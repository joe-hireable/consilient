"""AN - Gate A2 must be decidable while the log is being written.

Measured 24 Aug 2026: doctor compared the persisted projection against a replay of the
*live* log, so events landing between the two reads flipped A2 between FAIL ("canonical
state diverged"), UNKNOWN ("state covers N of M events") and PASS. Replay itself
reproduced; the read window was the defect.

These checks append *during* the A2 read, not before it. A quiet-log test would
reproduce the bug it is meant to catch. Two of them drive the race through a
monkeypatched ``projection.build`` or ``read_all``, each covering one of the two flips;
one drives it from a real writer thread, because a hook is not proof that a genuine
concurrent writer behaves the same way. The two checks that must still refuse are kept
here as well, for the same reason: pinning the prefix must not widen what counts as
identical, and an empty prefix must stay UNKNOWN rather than pass.

A2 is decided against a pinned prefix, not the live tail."""

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
import pytest
from consilient import projection
from consilient.events import (
    read_all,
)
from doctor_a2_helpers import (
    _a2,
    _append_judged,
    _doctor,
    _seeded,
)


def test_a2_is_pass_when_events_land_between_the_count_and_the_rebuild(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The FAIL race: log grows after the count and before the rebuild.

    cmd_replay used to read the live length, then rebuild from a later length.
    Matching counts made `stale` false, mismatched digests reported divergence.
    """
    log, db, path = _seeded(tmp_path)
    original_build = projection.build
    appended = {"n": 0}

    def racing_build(
        log_dir: Path, db_path: Path, *, workspace: Path | None = None
    ) -> sqlite3.Connection:
        if Path(log_dir).resolve() == log.resolve():
            _append_judged(path, f"race-rebuild-{appended['n']}", "t-race")
            appended["n"] += 1
        return original_build(log_dir, db_path, workspace=workspace)

    monkeypatch.setattr(projection, "build", racing_build)

    condition = _a2(_doctor(log, db, capsys))
    assert appended["n"] >= 1, (
        "the check never touched the live log; the race was not run"
    )
    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "diverged" not in reason


def test_a2_is_pass_when_events_land_between_the_projection_read_and_the_log_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The UNKNOWN race: log grows after the high-water mark is read.

    Matching that later length against the projection reported 'state covers N of M'
    and refused to decide. Events after the mark are outside the comparison.
    """
    from consilient import cli_replay

    log, db, path = _seeded(tmp_path)
    original_read_all = read_all
    appended = {"n": 0}

    def racing_read_all(directory: Path) -> object:
        if Path(directory).resolve() == log.resolve():
            _append_judged(path, f"race-read-{appended['n']}", "t-race")
            appended["n"] += 1
        return original_read_all(directory)

    # The A2 replay condition reads the log from cli_replay.py since the 28 August 2026
    # split, so it resolves `read_all` in that namespace. Patching the entry point left the
    # real reader in place and the race never ran -- the test said so, which is the right
    # failure: it asserts the race happened before asserting what it produced.
    monkeypatch.setattr(cli_replay, "read_all", racing_read_all)

    condition = _a2(_doctor(log, db, capsys))
    assert appended["n"] >= 1, "the live log was never re-read; the race was not run"
    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "covers" not in reason


def test_a2_still_fails_on_a_diverged_prefix_while_the_log_grows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pinning the prefix must not widen what counts as identical."""
    log, db, path = _seeded(tmp_path)
    drifted = sqlite3.connect(db)
    drifted.execute("UPDATE outcomes SET human_verdict = 'accept'")
    drifted.commit()
    drifted.close()

    original_build = projection.build

    def racing_build(
        log_dir: Path, db_path: Path, *, workspace: Path | None = None
    ) -> sqlite3.Connection:
        if Path(log_dir).resolve() == log.resolve():
            _append_judged(path, "race-drift", "t-race")
        return original_build(log_dir, db_path, workspace=workspace)

    monkeypatch.setattr(projection, "build", racing_build)

    condition = _a2(_doctor(log, db, capsys))
    assert condition["status"] == "fail", condition["reason"]
    assert "diverged" in str(condition["reason"])


def test_a2_stays_unknown_on_an_empty_prefix_while_the_log_grows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Do not reintroduce the tautological pass repaired on 20 Aug 2026.

    An empty prefix compared against later arrivals is not evidence that replay works.
    """
    log = tmp_path / "log"
    db = tmp_path / "state.db"
    log.mkdir()
    projection.build(log, db).close()
    path = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"

    original_build = projection.build

    def racing_build(
        log_dir: Path, db_path: Path, *, workspace: Path | None = None
    ) -> sqlite3.Connection:
        if Path(log_dir).resolve() == log.resolve():
            _append_judged(path, "race-empty", "t-empty")
        return original_build(log_dir, db_path, workspace=workspace)

    monkeypatch.setattr(projection, "build", racing_build)

    condition = _a2(_doctor(log, db, capsys))
    assert condition["status"] == "unknown", condition["reason"]
    assert "zero events" in str(condition["reason"])


def test_a2_verdict_is_stable_when_a_writer_thread_appends_during_the_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real concurrent writer, not only a hook: the check must still decide PASS."""
    log, db, path = _seeded(tmp_path)
    stop = threading.Event()
    entered = threading.Event()
    wrote = threading.Event()
    original_build = projection.build
    seq = {"n": 0}

    def writer() -> None:
        while not stop.is_set():
            if not entered.wait(timeout=5):
                return
            if stop.is_set():
                return
            _append_judged(path, f"thread-{seq['n']}", "t-thread")
            seq["n"] += 1
            wrote.set()
            if stop.wait(0.01):
                return

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()

    def racing_build(
        log_dir: Path, db_path: Path, *, workspace: Path | None = None
    ) -> sqlite3.Connection:
        if Path(log_dir).resolve() == log.resolve():
            entered.set()
            assert wrote.wait(5), "the writer did not append during the live rebuild"
        return original_build(log_dir, db_path, workspace=workspace)

    monkeypatch.setattr(projection, "build", racing_build)
    try:
        first = _a2(_doctor(log, db, capsys))
    finally:
        stop.set()
        entered.set()
        thread.join(timeout=5)

    assert seq["n"] >= 1, "the writer never appended while the check ran"
    original_build(log, db).close()
    second = _a2(_doctor(log, db, capsys))
    assert first["status"] == second["status"] == "pass", (
        first["reason"],
        second["reason"],
    )
    assert "identical" in str(first["reason"]) and "identical" in str(second["reason"])

"""AN — Gate A2 must be decidable while the log is being written.

Measured 24 Aug 2026: doctor compared the persisted projection against a replay of
the *live* log, so events landing between the two reads flipped A2 between FAIL
("canonical state diverged"), UNKNOWN ("state covers N of M events") and PASS.
Replay itself reproduced; the read window was the defect.

These checks append *during* the A2 read, not before it. A quiet-log test would
reproduce the bug it is meant to catch.

A2 is decided against a pinned prefix, not the live tail.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from consilient import projection
from consilient.cli import main
from consilient.events import (
    OUTCOME_KIND,
    SCHEMA_VERSION,
    VERDICT_KIND,
    append,
    read_all,
)

HUMAN = "joe-brown"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ev(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "v": SCHEMA_VERSION,
        "ts": _now(),
        "event": "test.event",
        "actor": "agent",
        "data": {},
    }
    base.update(over)
    return base


def _outcome(attempt_id: str, task: str, accept: bool) -> dict[str, object]:
    return _ev(
        event=OUTCOME_KIND,
        data={
            "attempt_id": attempt_id,
            "task": task,
            "verifier_accept": accept,
            "task_family": "repair",
            "verifier_version": "v1",
        },
    )


def _verdict(attempt_id: str, human_verdict: str) -> dict[str, object]:
    return _ev(
        actor=HUMAN,
        event=VERDICT_KIND,
        data={
            "attempt_id": attempt_id,
            "human_verdict": human_verdict,
            "principal": HUMAN,
            "via": "cli",
        },
    )


def _append_judged(path: Path, attempt_id: str, task: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    append(path, _outcome(attempt_id, task, True))
    append(path, _verdict(attempt_id, "reject"))


def _a2(payload: dict[str, Any]) -> dict[str, Any]:
    gates = payload["gates"]
    assert isinstance(gates, dict)
    conditions = gates["A"]["conditions"]
    assert isinstance(conditions, list)
    return next(c for c in conditions if c["id"] == "A2")


def _doctor(
    log: Path, db: Path, capsys: pytest.CaptureFixture[str]
) -> dict[str, Any]:
    code = main(["--log", str(log), "--db", str(db), "--json", "doctor"])
    captured = capsys.readouterr()
    assert captured.out, (
        f"doctor produced no stdout (exit {code}): {captured.err.strip() or '<empty stderr>'}"
    )
    parsed: object = json.loads(captured.out)
    assert isinstance(parsed, dict)
    return parsed


def _seeded(tmp_path: Path) -> tuple[Path, Path, Path]:
    log = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    _append_judged(path, "seed-0", "t0")
    projection.build(log, db).close()
    return log, db, path


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
    from consilient import cli as cli_mod

    log, db, path = _seeded(tmp_path)
    original_read_all = read_all
    appended = {"n": 0}

    def racing_read_all(directory: Path) -> object:
        if Path(directory).resolve() == log.resolve():
            _append_judged(path, f"race-read-{appended['n']}", "t-race")
            appended["n"] += 1
        return original_read_all(directory)

    monkeypatch.setattr(cli_mod, "read_all", racing_read_all)

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


def test_a2_canonicalises_rejection_paths_across_log_locations(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The same refused line has the same projected state wherever its log lives."""
    first_log = tmp_path / "first" / "log"
    second_log = tmp_path / "second" / "log"
    name = f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    first_path = first_log / name
    second_path = second_log / name
    first_path.parent.mkdir(parents=True)
    first_path.write_text("{not valid JSON}\n", encoding="utf-8")
    _append_judged(first_path, "rejected-path", "t-rejected-path")
    second_path.parent.mkdir(parents=True)
    second_path.write_text(first_path.read_text(encoding="utf-8"), encoding="utf-8")

    first_db = tmp_path / "first.db"
    second_db = tmp_path / "second.db"
    first = projection.build(first_log, first_db)
    second = projection.build(second_log, second_db)
    try:
        first_rejections = projection.rejections(first)
        assert first_rejections == projection.rejections(second)
        assert first_rejections[0]["path"] == name
        assert first_rejections[0]["line"] == 1
        assert str(first_rejections[0]["reason"]).startswith("not valid JSON:")
        assert projection.state_digest(first) == projection.state_digest(second)
    finally:
        first.close()
        second.close()

    first_a2 = _a2(_doctor(first_log, first_db, capsys))
    second_a2 = _a2(_doctor(second_log, second_db, capsys))
    assert first_a2["status"] == "pass", first_a2["reason"]
    assert second_a2["status"] == "pass", second_a2["reason"]
    for condition in (first_a2, second_a2):
        reason = str(condition["reason"])
        assert "identical" in reason
        assert "diverged" not in reason
        assert "Compared" in reason


def test_a2_is_unknown_when_pragma_projection_version_changes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The SQLite header version, not projection_meta, decides compatibility."""
    old, new = 1, 2
    assert projection.PROJECTION_VERSION == new
    log, db, _path = _seeded(tmp_path)
    existing = sqlite3.connect(db)
    existing.execute(f"PRAGMA user_version = {old}")
    existing.execute(
        "UPDATE projection_meta SET value = ? WHERE key = ?", ("999", "version")
    )
    existing.commit()
    existing.close()

    condition = _a2(_doctor(log, db, capsys))
    assert condition["status"] == "unknown", condition["reason"]
    assert condition["reason"] == "Projection version 1 rebuilt as 2; not compared."


def test_a2_does_not_prefix_digest_when_projection_version_differs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A version mismatch is unknown without comparing a prefix written by another projection."""
    from consilient import cli as cli_mod

    log, db, _path = _seeded(tmp_path)
    existing = sqlite3.connect(db)
    existing.execute("PRAGMA user_version = 1")
    existing.commit()
    existing.close()

    def forbidden(*_args: object, **_kwargs: object) -> str:
        raise AssertionError(
            "pinned-prefix rebuild must not run on a projection-version mismatch"
        )

    monkeypatch.setattr(cli_mod, "_digest_of_pinned_prefix", forbidden)
    condition = _a2(_doctor(log, db, capsys))
    assert condition["status"] == "unknown", condition["reason"]
    assert condition["reason"] == "Projection version 1 rebuilt as 2; not compared."


def test_a2_rejection_filename_still_changes_the_digest(tmp_path: Path) -> None:
    """Normalising the path must not drop it from the digest: a moved file still changes state."""
    first_log = tmp_path / "first" / "log"
    second_log = tmp_path / "second" / "log"
    first_log.mkdir(parents=True)
    second_log.mkdir(parents=True)
    (first_log / "one.jsonl").write_text("{not valid JSON}\n", encoding="utf-8")
    (second_log / "two.jsonl").write_text("{not valid JSON}\n", encoding="utf-8")
    first = projection.build(first_log, tmp_path / "first.db")
    second = projection.build(second_log, tmp_path / "second.db")
    try:
        assert first.execute("SELECT path FROM rejections").fetchone()[0] == "one.jsonl"
        assert second.execute("SELECT path FROM rejections").fetchone()[0] == "two.jsonl"
        assert projection.state_digest(first) != projection.state_digest(second)
    finally:
        first.close()
        second.close()


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


def test_a2_is_pass_when_a_refusal_lands_after_the_mark_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """MEASURED 26 August 2026: `_copy_event_prefix` copied the WHOLE current file
    whenever the accepted count was still within the mark, even if something had been
    appended since. A refused line added after the mark, with the accepted count
    unchanged, landed inside the reconstructed prefix anyway and read as divergence
    against a log that had not actually diverged within the pinned window.
    """
    log, db, path = _seeded(tmp_path)

    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")

    condition = _a2(_doctor(log, db, capsys))

    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "diverged" not in reason


def test_a2_is_pass_when_a_refusal_predates_events_added_after_the_mark(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """MEASURED 26 August 2026: cutting the prefix at the Nth accepted event's own line
    dropped a genuine refusal that predated the mark whenever later commits added MORE
    accepted events to the same file. The log is append-only, so anything before the
    FIRST accepted event beyond the mark is guaranteed to predate it, refusal or not.
    """
    log = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    _append_judged(path, "seed-0", "t0")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")
    projection.build(log, db).close()

    _append_judged(path, "grown-after-mark", "t-grown")

    condition = _a2(_doctor(log, db, capsys))

    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "diverged" not in reason

def test_a2_is_pass_on_a_quiet_trailing_refusal_inside_the_pin(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """MEASURED 26 August 2026: `_copy_event_prefix` pinned on accepted-event
    count only. When remaining==0 it cut at file_events[-1].line, dropping a
    trailing refusal that was already inside the projection. Quiet log of 2
    events + 1 refused line, built as (2, 1), doctor reported
    'Compared 2 events; canonical state diverged.'
    """
    log = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    _append_judged(path, "seed-0", "t0")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")
    conn = projection.build(log, db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM rejections").fetchone()[0] == 1
    finally:
        conn.close()

    condition = _a2(_doctor(log, db, capsys))

    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "diverged" not in reason


def test_a2_is_pass_when_a_refusal_then_events_land_after_the_mark(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """MEASURED 26 August 2026: seed 2/0, then one refused line then two accepted
    events. Cutting at the first accepted event beyond the mark pulled the
    post-mark refusal into the prefix. First doctor failed 'Compared 2 events;
    canonical state diverged.' The refusal is after the mark and is not evidence
    of divergence.
    """
    log, db, path = _seeded(tmp_path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")
    _append_judged(path, "grown-after-mark", "t-grown")

    condition = _a2(_doctor(log, db, capsys))

    assert condition["status"] == "pass", condition["reason"]
    reason = str(condition["reason"])
    assert "identical" in reason
    assert "diverged" not in reason


def test_a2_is_pass_on_a_trailing_refusal_inside_the_pin_while_the_log_grows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Trailing refusal at the pin, plus events landing during the check.

    The quiet case is the defect; this one keeps the unit's concurrent
    obligation: the log is being written while A2 decides.
    """
    log = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    _append_judged(path, "seed-0", "t0")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")
    projection.build(log, db).close()

    original_build = projection.build
    appended = {"n": 0}

    def racing_build(
        log_dir: Path, db_path: Path, *, workspace: Path | None = None
    ) -> sqlite3.Connection:
        if Path(log_dir).resolve() == log.resolve():
            _append_judged(path, f"race-trailing-{appended['n']}", "t-race")
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


def test_a2_still_fails_when_a_refusal_inside_the_pin_is_rewritten(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Including refusals in the pin must not widen what counts as identical."""
    log = tmp_path / "log"
    db = tmp_path / "state.db"
    path = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    _append_judged(path, "seed-0", "t0")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json\n")
    projection.build(log, db).close()

    drifted = sqlite3.connect(db)
    drifted.execute("UPDATE rejections SET reason = 'tampered'")
    drifted.commit()
    drifted.close()

    original_build = projection.build

    def racing_build(
        log_dir: Path, db_path: Path, *, workspace: Path | None = None
    ) -> sqlite3.Connection:
        if Path(log_dir).resolve() == log.resolve():
            _append_judged(path, "race-refusal-drift", "t-race")
        return original_build(log_dir, db_path, workspace=workspace)

    monkeypatch.setattr(projection, "build", racing_build)

    condition = _a2(_doctor(log, db, capsys))
    assert condition["status"] == "fail", condition["reason"]
    assert "diverged" in str(condition["reason"])
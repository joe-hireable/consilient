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

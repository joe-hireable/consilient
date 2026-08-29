"""Builders shared by the Gate A2 units: a judged attempt, a seeded log and projection,
and the JSON invocation of doctor.

Every A2 check needs a log with something in it and a way to read the A2 condition out
of ``consil doctor --json``, so those live here once rather than three times.
``_append_judged`` writes an outcome and a rejecting verdict as a pair, because A2 is
decided over judged attempts, not bare events. ``_seeded`` then builds the projection
from that pair so the pinned prefix is non-empty, and that matters: an empty prefix
compared against later arrivals is not evidence that replay works, and the tautological
pass that came of it was repaired on 20 August 2026.

Deliberately not named ``test_*.py``, so pytest does not collect it."""

import json
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


def _doctor(log: Path, db: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
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

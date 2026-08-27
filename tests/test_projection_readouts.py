"""AC — duplicate records quarantine, lag is not drift, rejection reasons surface.

The 24 August 2026 audit unit C (T7–T13). A unique-key collision during replay used to
raise IntegrityError and kill the projection; a one-event lag used to copy the whole
state file to `.stale-*`. Both are defects against ADR-0006 (the log is the record;
SQLite is a rebuildable projection) and against verdict-supply §5 (relational failures
become quarantine rows and replay continues).
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient import events
from consilient import projection
from consilient.cli import cmd_beta, cmd_replay, main


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _outcome(attempt_id: str) -> dict[str, object]:
    return {
        "v": events.SCHEMA_VERSION,
        "ts": _ts(),
        "event": events.OUTCOME_KIND,
        "actor": "agent",
        "data": {
            "attempt_id": attempt_id,
            "task": "t",
            "verifier_accept": True,
            "task_family": "repair",
            "verifier_version": "v1",
        },
    }


def _record_event(record_id: str, digest: str, payload: bytes) -> dict[str, object]:
    timestamp = _ts()
    return {
        "v": events.SCHEMA_VERSION,
        "ts": timestamp,
        "event": events.RECORD_CAPTURED_KIND,
        "actor": "projection-readouts-test",
        "event_id": events.new_event_id(),
        "data": {
            "record_id": record_id,
            "digest": digest,
            "byte_count": len(payload),
            "media_type": "application/octet-stream",
            "object_locator": f".harness/objects/sha256/{digest[:2]}/{digest[2:]}",
            "source": "inputs/source.bin",
            "consent_purpose": "task-evidence",
            "retention_class": "project",
            "valid_time": {"from": timestamp, "to": None},
            "supersedes": [],
            "invalidates": [],
        },
    }


def _stale_copies(db: Path) -> list[Path]:
    return sorted(db.parent.glob(db.name + ".stale-*"))


def test_duplicate_record_id_is_quarantined_and_build_succeeds(tmp_path: Path) -> None:
    """T9: a second record.captured with the same record_id must not raise.

    One accepted append used to kill replay permanently via IntegrityError on
    record_facts.record_id. The log already holds the line; the projection quarantines
    it and continues, matching the attempt_id / run_id pattern already in this module.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    log_dir.mkdir()
    payload = b"record bytes\n"
    digest = hashlib.sha256(payload).hexdigest()
    record_id = events.new_event_id()
    path = log_dir / f"{_ts()[:10]}.jsonl"
    events.append(path, _record_event(record_id, digest, payload))
    events.append(path, _record_event(record_id, digest, payload))

    conn = projection.build(log_dir, db)
    try:
        rows = projection.relational_quarantines(conn)
        facts = conn.execute("SELECT COUNT(*) FROM record_facts").fetchone()[0]
    finally:
        conn.close()

    assert facts == 1
    assert any("duplicate record_id" in str(row["reason"]) for row in rows)


def test_appending_a_declared_kind_twice_leaves_build_succeeding(
    tmp_path: Path,
) -> None:
    """Done criterion: appending a declared kind twice must not kill replay."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    log_dir.mkdir()
    path = log_dir / f"{_ts()[:10]}.jsonl"
    events.append(path, _outcome("attempt-dup"))
    events.append(path, _outcome("attempt-dup"))

    conn = projection.build(log_dir, db)
    try:
        quarantined = projection.relational_quarantines(conn)
        outcomes = conn.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
    finally:
        conn.close()

    assert outcomes == 1
    assert any("duplicate attempt_id" in str(row["reason"]) for row in quarantined)


def test_one_event_lag_writes_no_stale_copy(tmp_path: Path) -> None:
    """T7: lag is not drift. A one-event lag must produce zero `.stale-*` files."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    events.append(path, _outcome("attempt-0"))
    projection.build(log_dir, db).close()

    events.append(path, _outcome("attempt-1"))
    result = cmd_replay(argparse.Namespace(log=str(log_dir), db=str(db)))

    assert result["stale"] is True
    assert result["compared"] is False
    assert result["preserved_stale_state"] is None
    assert _stale_copies(db) == []


def test_lag_plus_drift_still_preserves_the_old_state(tmp_path: Path) -> None:
    """T7 copies only on genuine digest disagreement, not on every lag."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    events.append(path, _outcome("attempt-0"))
    projection.build(log_dir, db).close()

    drifted = sqlite3.connect(db)
    drifted.execute("UPDATE outcomes SET verifier_accept = 0")
    drifted.commit()
    drifted.close()

    events.append(path, _outcome("attempt-1"))
    result = cmd_replay(argparse.Namespace(log=str(log_dir), db=str(db)))

    assert result["stale"] is True
    assert result["preserved_stale_state"]
    assert Path(result["preserved_stale_state"]).exists()


def test_every_kind_constant_is_in_handlers_or_not_projected() -> None:
    """T11: a new `*_KIND` that is neither handled nor declared is a forgotten kind."""
    import inspect

    kinds = {
        value
        for name, value in vars(events).items()
        if name.endswith("_KIND") and isinstance(value, str)
    }
    missing = kinds - (projection.HANDLERS | projection.NOT_PROJECTED)
    assert missing == set(), f"undeclared kind constants: {sorted(missing)}"
    assert projection.HANDLERS.isdisjoint(projection.NOT_PROJECTED)
    assert projection.HANDLERS <= kinds
    apply_src = inspect.getsource(projection._apply)
    for name, value in vars(events).items():
        if (
            name.endswith("_KIND")
            and isinstance(value, str)
            and value in projection.HANDLERS
        ):
            assert name in apply_src, name


def test_beta_and_dashboard_surface_rejection_reasons(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T12: a parser refusal is a reason, not a pooled integer.

    Covers both quarantine classes the reviewer named: a parser-level refusal
    (malformed JSON line, via `rejection_reasons`) and a relational one (duplicate
    record_id, via `relational_quarantine`) -- `_rejection_reason_list` renders both
    from the same list, so both need a real reason present to prove the whole path,
    not just the parser half.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    events.append(path, _outcome("attempt-0"))
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{not json}\n")
    payload_bytes = b"record bytes\n"
    digest = hashlib.sha256(payload_bytes).hexdigest()
    record_id = events.new_event_id()
    events.append(path, _record_event(record_id, digest, payload_bytes))
    events.append(path, _record_event(record_id, digest, payload_bytes))

    assert main(["--log", str(log_dir), "--db", str(db), "beta", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["quarantined"] == 1
    reasons = payload["rejection_reasons"]
    assert reasons
    assert any("not valid JSON" in str(row["reason"]) for row in reasons)
    relational = payload["relational_quarantine"]
    assert relational
    assert any("duplicate record_id" in str(row["reason"]) for row in relational)
    all_reasons = reasons + relational

    out = tmp_path / "dash.html"
    assert (
        main(
            [
                "--log",
                str(log_dir),
                "--db",
                str(db),
                "--json",
                "dashboard",
                "--out",
                str(out),
            ]
        )
        == 0
    )
    capsys.readouterr()
    html_text = out.read_text(encoding="utf-8")
    assert all(
        html.escape(str(row["reason"]), quote=True) in html_text for row in all_reasons
    )


def test_relational_quarantine_count_helper_is_gone() -> None:
    """T12: the count-only helper pooled three forged approvals into a bare integer."""
    assert not hasattr(projection, "relational_quarantine_count")


def test_cmd_beta_closes_the_connection_when_from_connection_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """T13: try/finally, matching cmd_replay. An exception must not leak the handle."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    events.append(log_dir / "2026-08-20.jsonl", _outcome("attempt-0"))

    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("from_connection failed")

    monkeypatch.setattr("consilient.cli.beta_mod.from_connection", boom)
    with pytest.raises(RuntimeError, match="from_connection failed"):
        cmd_beta(
            argparse.Namespace(
                log=str(log_dir),
                db=str(db),
                task_family=None,
                verifier_version=None,
            )
        )
    # On Windows an open handle makes unlink/replace fail. This is the check.
    projection.build(log_dir, db).close()


def test_replay_reports_version_change_not_divergence(tmp_path: Path) -> None:
    """T10: a projection-version bump is a third replay state, not DIVERGED."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    events.append(log_dir / "2026-08-20.jsonl", _outcome("attempt-0"))
    projection.build(log_dir, db).close()

    conn = sqlite3.connect(db)
    # `projection_version()` reads PRAGMA user_version first and only falls back to the
    # projection_meta row when that pragma is unset (0) -- both must roll back to simulate
    # an old-version database, or the pragma (already stamped current by build()) wins.
    conn.execute("PRAGMA user_version = 0")
    conn.execute(
        "INSERT OR REPLACE INTO projection_meta (key, value) VALUES ('version', '0')"
    )
    conn.commit()
    conn.close()

    result = cmd_replay(argparse.Namespace(log=str(log_dir), db=str(db)))
    assert result["version_changed"] is True
    assert result["compared"] is False
    assert result["identical"] is None
    assert result["stale"] is False


def test_build_replaces_atomically_and_leaves_no_temp(tmp_path: Path) -> None:
    """T8: rebuild publishes via sibling temp + os.replace, not unlink-then-write."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    events.append(log_dir / "2026-08-20.jsonl", _outcome("attempt-0"))
    projection.build(log_dir, db).close()
    leftovers = [
        path
        for path in db.parent.iterdir()
        if path.name.startswith(".") and ".tmp" in path.name
    ]
    assert leftovers == []
    assert db.is_file()

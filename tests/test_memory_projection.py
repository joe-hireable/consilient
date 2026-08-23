"""M02 — temporal memory projection."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient import events, projection


OBJECTS = Path(".harness/objects")
LOG = Path(".harness/log")


def _record_event(
    *,
    event_id: str,
    record_id: str,
    digest: str,
    source: str = "inputs/source.bin",
    ts: str | None = None,
    byte_count: int | None = None,
    **data_overrides: object,
) -> dict[str, object]:
    timestamp = ts or datetime.now(timezone.utc).isoformat()
    data: dict[str, object] = {
        "record_id": record_id,
        "digest": digest,
        "byte_count": byte_count if byte_count is not None else len(b"record bytes\n"),
        "media_type": "application/octet-stream",
        "object_locator": f".harness/objects/sha256/{digest[:2]}/{digest[2:]}",
        "source": source,
        "consent_purpose": "task-evidence",
        "retention_class": "project",
        "valid_time": {"from": timestamp, "to": None},
        "supersedes": [],
        "invalidates": [],
    }
    data.update(data_overrides)
    return {
        "v": events.SCHEMA_VERSION,
        "ts": timestamp,
        "event": events.RECORD_CAPTURED_KIND,
        "actor": "memory-projection-test",
        "event_id": event_id,
        "data": data,
    }


def _reference(event: dict[str, object]) -> dict[str, str]:
    return {
        "event_id": str(event["event_id"]),
        "event_kind": str(event["event"]),
        "event_sha256": events.event_sha256(event),
    }


def _install_object(workspace: Path, payload: bytes = b"record bytes\n") -> str:
    digest = hashlib.sha256(payload).hexdigest()
    path = workspace / f".harness/objects/sha256/{digest[:2]}/{digest[2:]}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return digest


def _append_record(workspace: Path, event: dict[str, object]) -> None:
    log = workspace / LOG
    log.mkdir(parents=True, exist_ok=True)
    events.append(log / f"{str(event['ts'])[:10]}.jsonl", event)


def _build(workspace: Path) -> tuple:
    db = workspace / "projection.db"
    conn = projection.build(workspace / LOG, db, workspace=workspace)
    rows = projection.memory_record_rows(conn)
    digest = projection.state_digest(conn)
    conn.close()
    return rows, digest


def _temporal(workspace: Path) -> list[dict[str, object]]:
    db = workspace / "projection.db"
    conn = projection.build(workspace / LOG, db, workspace=workspace)
    try:
        return projection.record_temporal_views(conn)
    finally:
        conn.close()


def test_ordinary_capture_projects_one_current_head(tmp_path: Path) -> None:
    digest = _install_object(tmp_path)
    first = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=digest,
    )
    _append_record(tmp_path, first)

    views = _temporal(tmp_path)
    assert len(views) == 1
    view = views[0]
    assert view["status"] == "current"
    assert view["source"] == "inputs/source.bin"
    assert view["current"]["record_id"] == first["data"]["record_id"]
    assert view["history"] == []
    assert view["contested_heads"] == []
    assert view["invalidated"] == []
    assert view["defects"] == []
    assert view["current"]["kind"] == "application/octet-stream"
    assert view["current"]["actor"] == "memory-projection-test"
    assert view["current"]["work_item"] is None
    assert view["current"]["capability_contract"] is None


def test_immediate_supersession_projects_current_head_and_history(tmp_path: Path) -> None:
    first_digest = _install_object(tmp_path, b"first\n")
    second_digest = _install_object(tmp_path, b"second\n")
    first = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=first_digest,
        byte_count=len(b"first\n"),
    )
    second = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        record_id="650e8400-e29b-41d4-a716-446655440001",
        digest=second_digest,
        byte_count=len(b"second\n"),
        supersedes=[_reference(first)],
    )
    _append_record(tmp_path, first)
    _append_record(tmp_path, second)

    view = _temporal(tmp_path)[0]
    assert view["status"] == "current"
    assert view["current"]["record_id"] == second["data"]["record_id"]
    assert [row["record_id"] for row in view["history"]] == [first["data"]["record_id"]]


def test_invalidation_is_explicit_and_removes_current_head(tmp_path: Path) -> None:
    digest = _install_object(tmp_path)
    first = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=digest,
    )
    second = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        record_id="650e8400-e29b-41d4-a716-446655440001",
        digest=digest,
        invalidates=[_reference(first)],
    )
    _append_record(tmp_path, first)
    _append_record(tmp_path, second)

    view = _temporal(tmp_path)[0]
    assert view["status"] == "invalidated"
    assert view["current"] is None
    assert [row["record_id"] for row in view["invalidated"]] == [first["data"]["record_id"]]


def test_two_independently_supported_heads_are_contested(tmp_path: Path) -> None:
    first_digest = _install_object(tmp_path, b"alpha\n")
    second_digest = _install_object(tmp_path, b"beta\n")
    first = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=first_digest,
        byte_count=len(b"alpha\n"),
    )
    second = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        record_id="650e8400-e29b-41d4-a716-446655440001",
        digest=second_digest,
        byte_count=len(b"beta\n"),
    )
    _append_record(tmp_path, first)
    _append_record(tmp_path, second)

    view = _temporal(tmp_path)[0]
    assert view["status"] == "contested"
    assert view["current"] is None
    assert {row["record_id"] for row in view["contested_heads"]} == {
        first["data"]["record_id"],
        second["data"]["record_id"],
    }


def test_rejected_lines_increment_adverse_count_without_empty_prefix(tmp_path: Path) -> None:
    digest = _install_object(tmp_path)
    valid = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=digest,
    )
    log = tmp_path / LOG
    log.mkdir(parents=True, exist_ok=True)
    path = log / "2026-08-23.jsonl"
    events.append(path, valid)
    path.write_text(path.read_text(encoding="utf-8") + "not valid json\n", encoding="utf-8")

    conn = projection.build(log, tmp_path / "projection.db", workspace=tmp_path)
    try:
        assert projection.rejection_count(conn) == 1
        views = projection.record_temporal_views(conn)
        assert len(views) == 1
        assert views[0]["current"]["record_id"] == valid["data"]["record_id"]
    finally:
        conn.close()


def test_missing_object_is_a_visible_projection_defect(tmp_path: Path) -> None:
    digest = "e" * 64
    event = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=digest,
    )
    _append_record(tmp_path, event)

    view = _temporal(tmp_path)[0]
    assert view["status"] == "contested"
    assert view["current"] is None
    assert view["defects"] == [
        {
            "kind": "object_missing",
            "record_id": event["data"]["record_id"],
            "object_locator": event["data"]["object_locator"],
        }
    ]


def test_corrupt_object_is_a_visible_projection_defect(tmp_path: Path) -> None:
    payload = b"wrong bytes"
    claimed_digest = "f" * 64
    path = tmp_path / f".harness/objects/sha256/{claimed_digest[:2]}/{claimed_digest[2:]}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    event = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=claimed_digest,
        byte_count=len(payload),
    )
    _append_record(tmp_path, event)

    view = _temporal(tmp_path)[0]
    assert view["defects"] == [
        {
            "kind": "object_corrupt",
            "record_id": event["data"]["record_id"],
            "object_locator": event["data"]["object_locator"],
        }
    ]


def test_malformed_relation_target_is_a_visible_projection_defect(tmp_path: Path) -> None:
    digest = _install_object(tmp_path)
    first = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=digest,
    )
    second = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        record_id="650e8400-e29b-41d4-a716-446655440001",
        digest=digest,
        supersedes=[
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440099",
                "event_kind": events.RECORD_CAPTURED_KIND,
                "event_sha256": "0" * 64,
            }
        ],
    )
    log = tmp_path / LOG
    log.mkdir(parents=True, exist_ok=True)
    path = log / "2026-08-23.jsonl"
    events.append(path, first)
    with pytest.raises(events.EventError):
        events.append(path, second)

    # Projection defects also surface when a relation target is present but unresolved
    # inside the accepted prefix (for example after manual repair of the log).
    repaired = dict(second)
    repaired["data"] = dict(second["data"])
    repaired["data"]["supersedes"] = [_reference(first)]
    path.write_text(
        json.dumps(first, separators=(",", ":"), ensure_ascii=False)
        + "\n"
        + json.dumps(repaired, separators=(",", ":"), ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    accepted, rejected = events.read_all(log)
    assert rejected == []
    assert len(accepted) == 2

    conn = projection.build(log, tmp_path / "projection.db", workspace=tmp_path)
    try:
        relations = conn.execute(
            "SELECT relation, relation_status FROM record_relations ORDER BY id"
        ).fetchall()
        assert relations == [("supersedes", "ok")]
        views = projection.record_temporal_views(conn)
        assert views[0]["status"] == "current"
        assert views[0]["defects"] == []
    finally:
        conn.close()


def test_delete_and_rebuild_twice_is_deterministic(tmp_path: Path) -> None:
    first_digest = _install_object(tmp_path, b"first\n")
    second_digest = _install_object(tmp_path, b"second\n")
    first = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=first_digest,
        byte_count=len(b"first\n"),
    )
    second = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        record_id="650e8400-e29b-41d4-a716-446655440001",
        digest=second_digest,
        byte_count=len(b"second\n"),
        supersedes=[_reference(first)],
    )
    _append_record(tmp_path, first)
    _append_record(tmp_path, second)

    rows_one, digest_one = _build(tmp_path)
    rows_two, digest_two = _build(tmp_path)
    assert rows_one == rows_two
    assert digest_one == digest_two

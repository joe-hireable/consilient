"""M03 — auditable bounded recall receipts."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast

import pytest

from consilient import events
from consilient.events import SCHEMA_VERSION, VERDICT_KIND, Rejection, append
from consilient.recall import (
    RECEIPT_MARKER,
    pack,
    pack_events,
    parse_receipt,
)


def _ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def _event(**over):
    base = {
        "v": SCHEMA_VERSION,
        "ts": _ts(),
        "event": "test.event",
        "actor": "agent",
        "data": {},
    }
    base.update(over)
    return base


def _write(log_dir: Path, *raw_events) -> None:
    for event in raw_events:
        path = log_dir / f"{str(event['ts'])[:10]}.jsonl"
        append(path, event)


def _record_event(
    *,
    event_id: str,
    record_id: str,
    digest: str,
    retention_class: str = "project",
    supersedes: list[dict[str, str]] | None = None,
    ts: str | None = None,
) -> dict[str, object]:
    timestamp = ts or _ts()
    data: dict[str, object] = {
        "record_id": record_id,
        "digest": digest,
        "byte_count": 12,
        "media_type": "application/octet-stream",
        "object_locator": f".harness/objects/sha256/{digest[:2]}/{digest[2:]}",
        "source": "inputs/source.bin",
        "consent_purpose": "task-evidence",
        "retention_class": retention_class,
        "valid_time": {"from": timestamp, "to": None},
        "supersedes": supersedes or [],
        "invalidates": [],
    }
    return {
        "v": SCHEMA_VERSION,
        "ts": timestamp,
        "event": events.RECORD_CAPTURED_KIND,
        "actor": "recall-receipt-test",
        "event_id": event_id,
        "data": data,
    }


def _install_object(workspace: Path, payload: bytes = b"record bytes\n") -> str:
    digest = hashlib.sha256(payload).hexdigest()
    path = workspace / f".harness/objects/sha256/{digest[:2]}/{digest[2:]}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return digest


def _receipt(text: str) -> dict[str, object]:
    return parse_receipt(text)


def test_pack_appends_one_parseable_receipt(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write(
        log_dir,
        _event(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            event="note.recorded",
            data={"body": "alpha marker"},
        ),
    )
    text = pack(log_dir, query="alpha", limit_chars=5000)
    receipt = _receipt(text)
    assert RECEIPT_MARKER in text
    assert text.count(RECEIPT_MARKER) == 1
    assert receipt["semantic_status"] == "unknown"


def test_receipt_fields_are_exact_and_canonical(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    event = _event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        event="note.recorded",
        data={"body": "exact-query-token"},
    )
    _write(log_dir, event)
    text = pack(log_dir, query="exact-query-token", limit_chars=5000)
    receipt = _receipt(text)
    expected_keys = {
        "bytes_used",
        "candidate_ids",
        "context_complete",
        "continuation_cursor",
        "omitted",
        "prefix_digest",
        "query_digest",
        "scan_complete",
        "scanned_universe_count",
        "selected_ids",
        "semantic_status",
    }
    assert set(receipt) == expected_keys
    assert receipt["scanned_universe_count"] == 1
    assert receipt["candidate_ids"] == ["550e8400-e29b-41d4-a716-446655440000"]
    assert receipt["selected_ids"] == ["550e8400-e29b-41d4-a716-446655440000"]
    assert receipt["scan_complete"] is True
    assert receipt["context_complete"] is True


def test_irrelevant_events_are_named_in_receipt(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write(
        log_dir,
        _event(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            event="alpha.event",
            data={"topic": "alpha-only"},
        ),
        _event(
            event_id="550e8400-e29b-41d4-a716-446655440001",
            ts=_ts(1),
            event="beta.event",
            data={"topic": "beta-only"},
        ),
    )
    text = pack(log_dir, query="alpha-only", limit_chars=5000)
    receipt = _receipt(text)
    omitted = {entry["id"]: entry["reason"] for entry in receipt["omitted"]}
    assert omitted["550e8400-e29b-41d4-a716-446655440001"] == "irrelevant"


def test_context_bound_omission_and_continuation(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    ids: list[str] = []
    for index in range(6):
        event_id = f"550e8400-e29b-41d4-a716-44665544000{index}"
        ids.append(event_id)
        _write(
            log_dir,
            _event(
                event_id=event_id,
                ts=_ts(index),
                event="note.recorded",
                data={"n": index, "padding": "x" * 80},
            ),
        )
    first = pack(log_dir, query="note", limit_chars=2400)
    receipt = _receipt(first)
    assert receipt["context_complete"] is False
    assert receipt["continuation_cursor"] is not None
    context_bound = [
        entry for entry in receipt["omitted"] if entry["reason"] == "context_bound"
    ]
    assert context_bound
    second = pack(
        log_dir,
        query="note",
        limit_chars=2400,
        continuation_cursor=cast(str, receipt["continuation_cursor"]),
    )
    second_receipt = _receipt(second)
    assert second_receipt["selected_ids"]
    assert not set(second_receipt["selected_ids"]) & set(receipt["selected_ids"])


def test_continuation_rejects_prefix_drift(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    for index in range(4):
        _write(
            log_dir,
            _event(
                event_id=f"550e8400-e29b-41d4-a716-44665544000{index}",
                ts=_ts(index),
                event="note.recorded",
                data={"n": index, "padding": "y" * 60},
            ),
        )
    first = pack(log_dir, query="note", limit_chars=1500)
    receipt = _receipt(first)
    cursor = receipt["continuation_cursor"]
    assert cursor is not None
    _write(
        log_dir,
        _event(
            event_id="550e8400-e29b-41d4-a716-446655440099",
            ts=_ts(99),
            event="note.recorded",
            data={"body": "new"},
        ),
    )
    with pytest.raises(ValueError, match="continuation cursor"):
        pack(log_dir, query="note", limit_chars=1500, continuation_cursor=cast(str, cursor))


def test_superseded_record_is_omitted_with_reason(tmp_path: Path) -> None:
    workspace = tmp_path
    digest = _install_object(workspace)
    first = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=digest,
        ts=_ts(0),
    )
    second = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        record_id="650e8400-e29b-41d4-a716-446655440001",
        digest=digest,
        ts=_ts(1),
        supersedes=[
            {
                "event_id": str(first["event_id"]),
                "event_kind": str(first["event"]),
                "event_sha256": events.event_sha256(first),
            }
        ],
    )
    log_dir = workspace / "log"
    log_dir.mkdir()
    _write(log_dir, first, second)
    text = pack(log_dir, query="", limit_chars=8000)
    receipt = _receipt(text)
    omitted = {entry["id"]: entry["reason"] for entry in receipt["omitted"]}
    assert omitted["550e8400-e29b-41d4-a716-446655440000"] == "superseded"
    assert "550e8400-e29b-41d4-a716-446655440001" in receipt["selected_ids"]


def test_private_record_is_permission_omitted_without_content(tmp_path: Path) -> None:
    workspace = tmp_path
    digest = _install_object(workspace)
    private = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=digest,
        retention_class="private",
    )
    log_dir = workspace / "log"
    log_dir.mkdir()
    _write(log_dir, private)
    text = pack(log_dir, query="", limit_chars=8000)
    receipt = _receipt(text)
    assert receipt["omitted"] == [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "reason": "permission"}
    ]
    assert private["data"]["source"] not in text


def test_rejected_jsonl_is_corrupt_in_receipt(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    path = log_dir / "2026-08-23.jsonl"
    append(
        path,
        _event(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            event="note.recorded",
            data={"body": "valid"},
        ),
    )
    path.write_text(path.read_text(encoding="utf-8") + "not valid json\n", encoding="utf-8")
    text = pack(log_dir, query="valid", limit_chars=5000)
    receipt = _receipt(text)
    corrupt = [entry for entry in receipt["omitted"] if entry["reason"] == "corrupt"]
    assert len(corrupt) == 1
    assert corrupt[0]["id"].startswith("reject:")


def test_contested_records_stay_visible_in_candidates(tmp_path: Path) -> None:
    workspace = tmp_path
    digest = _install_object(workspace)
    first = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440000",
        record_id="650e8400-e29b-41d4-a716-446655440000",
        digest=digest,
        ts=_ts(0),
    )
    second = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        record_id="650e8400-e29b-41d4-a716-446655440001",
        digest=digest,
        ts=_ts(1),
    )
    log_dir = workspace / "log"
    log_dir.mkdir()
    _write(log_dir, first, second)
    text = pack(log_dir, query="", limit_chars=8000)
    receipt = _receipt(text)
    assert set(receipt["candidate_ids"]) >= {
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001",
    }


def test_parse_receipt_rejects_duplicate_blocks() -> None:
    block = (
        "<!-- consilient:recall-receipt:v1\n"
        '{"bytes_used":1,"candidate_ids":[],"context_complete":true,'
        '"continuation_cursor":null,"omitted":[],"prefix_digest":"a",'
        '"query_digest":"b","scan_complete":true,"scanned_universe_count":0,'
        '"selected_ids":[],"semantic_status":"unknown"}\n-->'
    )
    with pytest.raises(ValueError, match="duplicate"):
        parse_receipt(f"body\n{block}\n{block}")


def test_parse_receipt_rejects_unknown_omission_reason() -> None:
    block = (
        "<!-- consilient:recall-receipt:v1\n"
        '{"bytes_used":1,"candidate_ids":[],"context_complete":true,'
        '"continuation_cursor":null,"omitted":[{"id":"x","reason":"guess"}],'
        '"prefix_digest":"a","query_digest":"b","scan_complete":true,'
        '"scanned_universe_count":0,"selected_ids":[],"semantic_status":"unknown"}\n-->'
    )
    with pytest.raises(ValueError, match="omission reason"):
        parse_receipt(block)


def test_repeated_runs_are_byte_identical(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write(
        log_dir,
        _event(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            event="dispatch.refused",
            actor="consilient.dispatch",
            data={"reason": "pool exhausted", "supervised": False},
        ),
        _event(
            event_id="550e8400-e29b-41d4-a716-446655440001",
            ts=_ts(1),
            event="note.recorded",
            data={"topic": "dispatch"},
        ),
    )
    first = pack(log_dir, query="dispatch", limit_chars=5000)
    second = pack(log_dir, query="dispatch", limit_chars=5000)
    assert first == second


def test_human_verdict_priority_kind_still_selected(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write(
        log_dir,
        _event(
            actor="joe-brown",
            event=VERDICT_KIND,
            data={
                "attempt_id": "attempt-abc",
                "human_verdict": "reject",
                "principal": "joe-brown",
                "via": "cli",
            },
        ),
    )
    text = pack(log_dir, query="missing-keyword", limit_chars=5000)
    receipt = _receipt(text)
    assert receipt["selected_ids"]
    assert "attempt-abc" in text


def test_pack_events_accepts_explicit_rejections() -> None:
    event = events.Event(
        raw=_event(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            event="note.recorded",
            data={"body": "valid"},
        )
    )
    rejection = Rejection("log/2026-08-23.jsonl", 2, "invalid json", "deadbeef")
    text = pack_events([event], query="valid", limit_chars=5000, rejections=[rejection])
    receipt = _receipt(text)
    assert receipt["scanned_universe_count"] == 2
    assert any(entry["reason"] == "corrupt" for entry in receipt["omitted"])


def test_query_digest_is_normalised() -> None:
    from consilient.recall import _query_digest

    assert _query_digest("  Foo   BAR ") == _query_digest("foo bar")


def test_overflow_fixture_reports_honest_completion_flags(tmp_path: Path) -> None:
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    for index in range(5):
        _write(
            log_dir,
            _event(
                event_id=f"550e8400-e29b-41d4-a716-44665544000{index}",
                ts=_ts(index),
                event="note.recorded",
                data={"n": index, "padding": "z" * 100},
            ),
        )
    text = pack(log_dir, query="note", limit_chars=2400)
    receipt = _receipt(text)
    assert receipt["scan_complete"] is True
    assert receipt["context_complete"] is False
    assert receipt["continuation_cursor"] is not None
    selected = set(receipt["selected_ids"])
    omitted_ids = {entry["id"] for entry in receipt["omitted"] if entry["reason"] == "context_bound"}
    assert selected.isdisjoint(omitted_ids)


from typing import cast

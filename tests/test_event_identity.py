"""F03 — stable identities and exact references at the trajectory boundary."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

from consilient import events

SCHEMA_VERSION = events.SCHEMA_VERSION
EventError = events.EventError
append = events.append
append_transaction = events.append_transaction
read_all = events.read_all


def ev(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "test.identity",
        "actor": "identity-test",
        "data": {"marker": "source"},
    }
    base.update(over)
    return base


def _reference(event: dict[str, object]) -> dict[str, str]:
    return {
        "event_id": str(event["event_id"]),
        "event_kind": str(event["event"]),
        "event_sha256": events.event_sha256(event),
    }


def test_append_attaches_one_canonical_uuid4_and_reuses_it_on_retry(tmp_path) -> None:
    record = ev()
    log = tmp_path / "trajectory.jsonl"

    append(log, record)
    assigned = record["event_id"]
    assert isinstance(assigned, str)
    assert len(assigned) == 36
    assert assigned[8] == assigned[13] == assigned[18] == assigned[23] == "-"
    assert assigned[14] == "4"
    assert assigned == assigned.lower()

    with pytest.raises(EventError, match="duplicate event_id"):
        append(log, record)


@pytest.mark.parametrize(
    "event_id",
    (
        "550E8400-E29B-41D4-A716-446655440000",
        " 550e8400-e29b-41d4-a716-446655440000",
        "{550e8400-e29b-41d4-a716-446655440000}",
        "urn:uuid:550e8400-e29b-41d4-a716-446655440000",
        "550e8400e29b41d4a716446655440000",
        "550e8400-e29b-11d4-a716-446655440000",
    ),
)
def test_append_rejects_noncanonical_or_non_v4_ids(tmp_path, event_id: str) -> None:
    with pytest.raises(EventError, match="event_id"):
        append(tmp_path / "trajectory.jsonl", ev(event_id=event_id))


def test_transaction_rejects_duplicate_ids_inside_the_same_batch(tmp_path) -> None:
    event_id = "550e8400-e29b-41d4-a716-446655440000"
    with pytest.raises(EventError, match="duplicate event_id"):
        append_transaction(
            tmp_path,
            [ev(event_id=event_id), ev(event_id=event_id)],
            lambda _prefix, _rejections, _candidates: None,
        )


def test_read_all_reports_historical_duplicate_ids_across_daily_files(tmp_path) -> None:
    event_id = "550e8400-e29b-41d4-a716-446655440000"
    first = ev(event_id=event_id, ts="2026-08-22T12:00:00+00:00")
    second = ev(event_id=event_id, ts="2026-08-23T12:00:00+00:00")
    for day, record in (("2026-08-22", first), ("2026-08-23", second)):
        (tmp_path / f"{day}.jsonl").write_text(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    recorded, rejected = read_all(tmp_path)

    assert [event.raw for event in recorded] == [first, second]
    assert len(rejected) == 1
    assert "duplicate event_id" in rejected[0].reason


def test_event_sha256_binds_the_complete_canonical_event() -> None:
    record = ev(event_id="550e8400-e29b-41d4-a716-446655440000")
    expected = hashlib.sha256(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()

    assert events.event_sha256(record) == expected
    changed = {**record, "actor": "other-actor"}
    assert events.event_sha256(changed) != expected


def test_resolver_accepts_one_earlier_exact_reference_after_replay(tmp_path) -> None:
    source = ev(event_id="550e8400-e29b-41d4-a716-446655440000")
    consumer = ev(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        data={"marker": "consumer"},
    )
    log = tmp_path / f"{source['ts'][:10]}.jsonl"
    append(log, source)
    append(log, consumer)
    recorded, rejected = read_all(tmp_path)

    assert rejected == []
    assert events.resolve_reference(_reference(source), recorded, before=recorded[1]) == recorded[0]


def test_resolver_rejects_missing_late_kind_and_hash_mismatched_references() -> None:
    source = events.Event(ev(event_id="550e8400-e29b-41d4-a716-446655440000"))
    consumer = events.Event(ev(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        ts=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
    ))
    reference = _reference(source.raw)

    with pytest.raises(EventError, match="missing event_id"):
        events.resolve_reference(
            {"event_kind": source.kind, "event_sha256": events.event_sha256(source.raw)},
            [source],
        )
    with pytest.raises(EventError, match="not earlier"):
        events.resolve_reference(reference, [consumer, source], before=consumer)
    with pytest.raises(EventError, match="event_kind"):
        events.resolve_reference({**reference, "event_kind": "other.kind"}, [source])
    with pytest.raises(EventError, match="event_sha256"):
        events.resolve_reference({**reference, "event_sha256": "0" * 64}, [source])


def test_resolver_marks_only_a_matching_legacy_row_unmeasured() -> None:
    legacy = events.Event(ev())
    reference = {"event_kind": legacy.kind, "event_sha256": events.event_sha256(legacy.raw)}

    assert events.resolve_reference(reference, [legacy]) == "unmeasured"
    with pytest.raises(EventError, match="missing event_id"):
        events.resolve_reference({"event_kind": "test.identity", "event_sha256": "0" * 64}, [legacy])

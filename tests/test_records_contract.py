"""M01 — the ``record.captured`` schema, validated without capturing anything.

These tests build the event by hand and hand it straight to ``events.validate`` and
``events.append``, so they pin the contract the log enforces rather than the behaviour
of the module that writes it. The records implementation could be replaced wholesale and
every assertion here would still have to hold, which is why they are kept apart from the
capture tests. The refusals are non-canonical or escaping object locators, an absolute
source path, missing consent or retention metadata, and renamed fields or event-kind
aliases. The aliases matter more than they look: a reader keyed on ``record.captured``
silently ignores ``record.capture``, and an event that is silently ignored is
indistinguishable from one that was never written.

The relations test is the long one and carries the most weight. A reference resolves
only to an exact, earlier record event — never to itself, never forward to an event not
yet appended, and never through renamed reference keys — and after every refusal the log
still holds only the two events that were legitimately appended, so a rejected append
leaves no residue. As the fixture itself records: the frozen API accepts no validity
interval, so capture time is the measured lower bound and the unknown upper bound stays
explicit as ``None``."""

from datetime import datetime, timezone
from pathlib import Path
import pytest
from consilient import events


def _record_event(
    *,
    event_id: str = "550e8400-e29b-41d4-a716-446655440000",
    record_id: str = "650e8400-e29b-41d4-a716-446655440000",
    digest: str = "a" * 64,
    **data_overrides: object,
) -> dict[str, object]:
    ts = datetime.now(timezone.utc).isoformat()
    data: dict[str, object] = {
        "record_id": record_id,
        "digest": digest,
        "byte_count": 1,
        "media_type": "application/octet-stream",
        "object_locator": f".harness/objects/sha256/{digest[:2]}/{digest[2:]}",
        "source": "inputs/source.bin",
        "consent_purpose": "task-evidence",
        "retention_class": "project",
        # The frozen API accepts no validity interval. Capture time is therefore
        # the measured lower bound and an unknown upper bound stays explicit.
        "valid_time": {"from": ts, "to": None},
        "supersedes": [],
        "invalidates": [],
    }
    data.update(data_overrides)
    return {
        "v": events.SCHEMA_VERSION,
        "ts": ts,
        "event": "record.captured",
        "actor": "records-test",
        "event_id": event_id,
        "data": data,
    }


def _event_reference(event: dict[str, object]) -> dict[str, str]:
    return {
        "event_id": str(event["event_id"]),
        "event_kind": str(event["event"]),
        "event_sha256": events.event_sha256(event),
    }


@pytest.mark.parametrize(
    "locator",
    (
        "/absolute/object",
        "C:/absolute/object",
        ".harness/objects/../escape",
        ".harness/objects/sha256/aa/not-the-digest",
    ),
)
def test_record_contract_refuses_noncanonical_or_escaping_object_locators(
    tmp_path: Path, locator: str
) -> None:
    candidate = _record_event(object_locator=locator)
    with pytest.raises(events.EventError, match="object_locator"):
        events.append(tmp_path / "trajectory.jsonl", candidate)
    assert events.read(tmp_path / "trajectory.jsonl") == ([], [])


def test_record_contract_refuses_an_absolute_source_locator(tmp_path: Path) -> None:
    with pytest.raises(events.EventError, match="source"):
        events.append(
            tmp_path / "trajectory.jsonl",
            _record_event(source="C:/private/source.bin"),
        )
    assert events.read(tmp_path / "trajectory.jsonl") == ([], [])


@pytest.mark.parametrize("missing", ("consent_purpose", "retention_class"))
def test_record_contract_refuses_missing_consent_or_retention_metadata(
    missing: str,
) -> None:
    candidate = _record_event()
    del candidate["data"][missing]
    with pytest.raises(events.EventError, match=missing):
        events.validate(candidate)


def test_record_contract_refuses_field_and_event_kind_aliases() -> None:
    candidate = _record_event()
    candidate["data"]["consent"] = candidate["data"].pop("consent_purpose")
    with pytest.raises(events.EventError, match="consent|field"):
        events.validate(candidate)

    for alias in ("record.capture", "record_captured", "records.captured"):
        candidate = _record_event()
        candidate["event"] = alias
        with pytest.raises(events.EventError, match="alias|record.captured"):
            events.validate(candidate)


def test_record_relations_resolve_only_exact_earlier_record_references(
    tmp_path: Path,
) -> None:
    log = tmp_path / "trajectory.jsonl"
    first = _record_event()
    events.append(log, first)
    reference = _event_reference(first)

    second = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        record_id="650e8400-e29b-41d4-a716-446655440001",
        supersedes=[reference],
    )
    events.append(log, second)
    assert [event.raw for event in events.read(log)[0]] == [first, second]

    self_referencing = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440002",
        record_id="650e8400-e29b-41d4-a716-446655440002",
        invalidates=[
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440002",
                "event_kind": "record.captured",
                "event_sha256": "0" * 64,
            }
        ],
    )
    with pytest.raises(events.EventError, match="itself|self"):
        events.append(log, self_referencing)

    future = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440003",
        record_id="650e8400-e29b-41d4-a716-446655440003",
    )
    before_future = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440004",
        record_id="650e8400-e29b-41d4-a716-446655440004",
        supersedes=[_event_reference(future)],
    )
    with pytest.raises(events.EventError, match="earlier|future|missing"):
        events.append(log, before_future)

    alias_reference = {
        "id": reference["event_id"],
        "kind": reference["event_kind"],
        "sha256": reference["event_sha256"],
    }
    with pytest.raises(events.EventError, match="reference"):
        events.validate(
            _record_event(
                event_id="550e8400-e29b-41d4-a716-446655440005",
                record_id="650e8400-e29b-41d4-a716-446655440005",
                supersedes=[alias_reference],
            )
        )

    assert [event.raw for event in events.read(log)[0]] == [first, second]

"""M06 — an appended change replays with its whole lineage intact.

The refusal tests prove what cannot be written; these prove that what was written can be
read back and resolved, which is the only reason to record provenance at all. A
succeeded, a failed, a refused and a started change are appended over one seeded lineage
and then replayed from the log: nothing is rejected, they return in append order, and
for each of them the base-model reference resolves to a ``record.captured`` event and
the procedure reference to a ``capability.versioned`` event, with the dataset and
checkpoint digests matching the records they point at wherever those are present. The
failure text, the licence, the privacy class and the authoring run all survive the round
trip unchanged, so a reader reconstructing the change months later gets the same
disposition the writer recorded.

The second test covers the lineage that is legitimately short rather than broken: a non-
data-driven state change replays with no dataset and no dataset digest, and still
carries its checkpoint. That absence has to be readable as intended absence, not as a
missing field."""

from pathlib import Path
from consilient import events
from model_change_helpers import (
    CHECKPOINT_PAYLOAD,
    LOG,
    _append,
    _change_event,
    _digest,
    _event_data,
    _seed_lineage,
)


def test_success_failure_and_refusal_replay_with_complete_provenance(
    tmp_path: Path,
) -> None:
    seeded = _seed_lineage(tmp_path)
    success = _append(tmp_path, _change_event(seeded))
    failed = _append(
        tmp_path,
        _change_event(
            seeded,
            event_id="550e8400-e29b-41d4-a716-446655440021",
            change_id="750e8400-e29b-41d4-a716-446655440001",
            status="failed",
            failure="checkpoint write refused",
            checkpoint=None,
            checkpoint_digest=None,
        ),
    )
    refused = _append(
        tmp_path,
        _change_event(
            seeded,
            event_id="550e8400-e29b-41d4-a716-446655440022",
            change_id="750e8400-e29b-41d4-a716-446655440002",
            status="refused",
            failure="missing licence disposition",
            checkpoint=None,
            checkpoint_digest=None,
        ),
    )
    started = _append(
        tmp_path,
        _change_event(
            seeded,
            event_id="550e8400-e29b-41d4-a716-446655440023",
            change_id="750e8400-e29b-41d4-a716-446655440003",
            status="started",
            failure=None,
            checkpoint=None,
            checkpoint_digest=None,
        ),
    )

    accepted, rejected = events.read_all(tmp_path / LOG)
    assert rejected == []
    changes = [event for event in accepted if event.kind == events.MODEL_CHANGE_KIND]
    assert [event.raw["event_id"] for event in changes] == [
        success["event_id"],
        failed["event_id"],
        refused["event_id"],
        started["event_id"],
    ]
    prefix = tuple(accepted)
    for event in changes:
        data = event.data
        assert events.resolve_reference(data["base_model"], prefix).kind == (
            events.RECORD_CAPTURED_KIND
        )
        assert events.resolve_reference(data["procedure"], prefix).kind == (
            events.CAPABILITY_VERSIONED_KIND
        )
        if data["dataset"] is not None:
            dataset = events.resolve_reference(data["dataset"], prefix)
            assert dataset.kind == events.RECORD_CAPTURED_KIND
            assert dataset.data["digest"] == data["dataset_digest"]
        if data["checkpoint"] is not None:
            checkpoint = events.resolve_reference(data["checkpoint"], prefix)
            assert checkpoint.kind == events.RECORD_CAPTURED_KIND
            assert checkpoint.data["digest"] == data["checkpoint_digest"]
        assert data["licence"] == "MIT"
        assert data["privacy_class"] == "private"
        assert data["authoring_run"] == "20260825T022615-bd05853725"

    assert _event_data(success)["status"] == "succeeded"
    assert _event_data(success)["checkpoint_digest"] == _digest(CHECKPOINT_PAYLOAD)
    assert _event_data(failed)["failure"] == "checkpoint write refused"
    assert _event_data(refused)["failure"] == "missing licence disposition"
    assert _event_data(started)["status"] == "started"
    assert _event_data(started)["checkpoint"] is None


def test_non_data_driven_success_replays_without_a_dataset(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path, with_dataset=False)
    stored = _append(
        tmp_path,
        _change_event(
            seeded,
            mutation_class="non_data_driven_state_change",
            dataset=None,
            dataset_digest=None,
        ),
    )
    accepted, rejected = events.read_all(tmp_path / LOG)
    assert rejected == []
    change = next(
        event for event in accepted if event.raw["event_id"] == stored["event_id"]
    )
    assert change.data["mutation_class"] == "non_data_driven_state_change"
    assert change.data["dataset"] is None
    assert change.data["dataset_digest"] is None
    assert change.data["checkpoint_digest"] == _digest(CHECKPOINT_PAYLOAD)

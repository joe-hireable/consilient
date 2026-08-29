"""M06 — the change body's frozen shape, and every way validation refuses it.

Every attempted persistent model-state mutation is one validated ``model.change`` event,
and this file is where that sentence is enforced. The first test pins the field set and
both closed vocabularies verbatim, so adding a field, a mutation class or a status is a
deliberate edit here rather than a silent widening elsewhere. The rest exercise the
constraints that make the event provenance rather than a claim: aliases, missing fields
and unexpected extra fields are all refused; data-driven training must name a dataset
and a non-data-driven state change must not carry one; success requires a checkpoint and
forbids failure text, while failed and refused both require a visible reason — so no
status can be recorded without the evidence that status implies.

Licence and privacy class must be stated, with empty strings, ``unknown`` and
``unspecified`` each refused, because a derived artefact carrying no disposition is
precisely the one that later gets published by accident. References must resolve to
exact, earlier events of the right kind: a dangling reference, a reference to the
change's own event id, and a capability event offered where a record is required are
refused in turn, and a digest that does not match the record it points at is refused on
append rather than on read.

Preserved from before the 28 August 2026 split, which rewrote this docstring and carried
the paragraph below into no sibling. It is reproduced WHOLE. An earlier restoration took
only the individual lines a checker had reported missing, which spliced halves of two
different sentences together beneath a claim of being verbatim -- found by an outside
review on 29 August 2026.

    Every attempted persistent model-state mutation is one validated ``model.change``
    event. This unit records provenance; it does not train, promote or activate.
"""

from pathlib import Path
import pytest
from consilient import events
from model_change_helpers import (
    CHANGE_EVENT_ID,
    _append,
    _change_event,
    _event_data,
    _reference,
    _seed_lineage,
)


def test_model_change_body_fields_are_frozen() -> None:
    assert events.MODEL_CHANGE_KIND == "model.change"
    assert events.MODEL_CHANGE_FIELDS == {
        "change_id",
        "mutation_class",
        "base_model_digest",
        "dataset_digest",
        "procedure_digest",
        "authoring_run",
        "checkpoint_digest",
        "status",
        "failure",
        "licence",
        "privacy_class",
        "base_model",
        "dataset",
        "procedure",
        "checkpoint",
    }
    assert events.MODEL_CHANGE_MUTATION_CLASSES == {
        "data_driven_training",
        "non_data_driven_state_change",
    }
    assert events.MODEL_CHANGE_STATUSES == {
        "started",
        "succeeded",
        "failed",
        "refused",
    }


def test_aliases_and_missing_fields_are_refused(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    event = _change_event(seeded)
    alias = dict(event)
    alias["event"] = "model.changed"
    with pytest.raises(events.EventError, match="alias|model.change"):
        events.validate(alias)

    missing = dict(event)
    missing_data = dict(_event_data(event))
    missing["data"] = missing_data
    del missing_data["status"]
    with pytest.raises(events.EventError, match="missing"):
        events.validate(missing)

    extra = dict(event)
    extra_data = dict(_event_data(event))
    extra_data["weights"] = "mutated"
    extra["data"] = extra_data
    with pytest.raises(events.EventError, match="unexpected"):
        events.validate(extra)


def test_mutation_class_and_status_are_closed(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    with pytest.raises(events.EventError, match="mutation_class"):
        events.validate(_change_event(seeded, mutation_class="fine_tune"))
    with pytest.raises(events.EventError, match="status"):
        events.validate(_change_event(seeded, status="promoted"))


def test_data_driven_training_requires_a_dataset_record(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    with pytest.raises(events.EventError, match="dataset"):
        events.validate(
            _change_event(
                seeded,
                mutation_class="data_driven_training",
                dataset=None,
                dataset_digest=None,
            )
        )


def test_non_data_driven_change_forbids_a_dataset(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    with pytest.raises(events.EventError, match="dataset"):
        events.validate(
            _change_event(
                seeded,
                mutation_class="non_data_driven_state_change",
                status="succeeded",
                failure=None,
            )
        )


def test_success_requires_a_checkpoint_and_no_failure(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    with pytest.raises(events.EventError, match="checkpoint"):
        events.validate(
            _change_event(
                seeded,
                status="succeeded",
                checkpoint=None,
                checkpoint_digest=None,
            )
        )
    with pytest.raises(events.EventError, match="failure"):
        events.validate(
            _change_event(seeded, status="succeeded", failure="should-not-be-set")
        )


def test_failed_and_refused_require_a_visible_reason(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path, with_checkpoint=False)
    for status in ("failed", "refused"):
        with pytest.raises(events.EventError, match="failure"):
            events.validate(
                _change_event(
                    seeded,
                    status=status,
                    failure=None,
                    checkpoint=None,
                    checkpoint_digest=None,
                )
            )


def test_private_derived_output_requires_explicit_licence_and_privacy(
    tmp_path: Path,
) -> None:
    seeded = _seed_lineage(tmp_path)
    for field, value in (
        ("licence", ""),
        ("licence", "unknown"),
        ("privacy_class", "  "),
        ("privacy_class", "unspecified"),
    ):
        with pytest.raises(events.EventError, match="licence|privacy"):
            events.validate(_change_event(seeded, **{field: value}))


def test_references_must_be_exact_earlier_record_or_capability_events(
    tmp_path: Path,
) -> None:
    seeded = _seed_lineage(tmp_path)
    dangling = _change_event(
        seeded,
        base_model={
            "event_id": "550e8400-e29b-41d4-a716-446655440099",
            "event_kind": events.RECORD_CAPTURED_KIND,
            "event_sha256": "b" * 64,
        },
    )
    with pytest.raises(events.EventError, match="base_model"):
        _append(tmp_path, dangling)

    self_ref = _change_event(seeded, event_id=CHANGE_EVENT_ID)
    self_data = _event_data(self_ref)
    self_data["base_model"] = {
        "event_id": CHANGE_EVENT_ID,
        "event_kind": events.RECORD_CAPTURED_KIND,
        "event_sha256": "c" * 64,
    }
    with pytest.raises(events.EventError, match="self|base_model"):
        _append(tmp_path, self_ref)

    wrong_kind = _change_event(
        seeded,
        dataset=_reference(seeded["procedure"]),
        dataset_digest=_event_data(seeded["procedure"])["version_digest"],
    )
    with pytest.raises(events.EventError, match="dataset"):
        events.validate(wrong_kind)


def test_digest_must_match_the_referenced_record(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    with pytest.raises(events.EventError, match="digest"):
        _append(tmp_path, _change_event(seeded, base_model_digest="a" * 64))

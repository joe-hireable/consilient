"""Binding a record to the earlier events it claims.

A record that points backwards is worth exactly as much as the resolution of its
pointers, and these validators do that resolution against the accepted prefix while the
lock is held. A P01 planning record is bound to unique identities and to exact earlier
events, so it can name neither something absent nor itself. A model change is resolved
against the provenance it asserts, so the lineage of learned state is checked at the
moment it is written rather than reconstructed later from what happens to be lying
around.

The delivery-estimate contract sits with them because it is the same demand made of a
forecast instead of a fact. The body is fixed, and both directions of mismatch are
reported. Revision zero is its own original, carries no predecessor and no cause, and
cannot claim that notice preceded its upper bound; every later revision names the
estimate it revises, the original it descends from, and one of the declared causes for
having moved. An estimate free to be silently restated is not an estimate anyone can be
held to."""

from __future__ import annotations
from datetime import datetime
from typing import cast

from .events_vocabulary import (
    ESTIMATE_CAUSES,
    HUMAN_ONLY,
    _ESTIMATE_REQUIRED_FIELDS,
    estimate_digest,
)

from .events_digests import (
    _check_stream_bounds,
    _estimate_digest_field,
    _estimate_timestamp,
    decision_protocol_data,
)

from .events_durability import (
    Event,
    _planning_references,
)

from .events_fields import (
    _check_uuid4,
    _estimate_non_negative_int,
    _estimate_text,
)

from .events_kinds import (
    ACTION_PROPOSAL_KIND,
    CAPABILITY_VERSIONED_KIND,
    DELIVERY_ACTOR,
    DELIVERY_ESTIMATE_KIND,
    EventError,
    EventPayload,
    MODEL_CHANGE_KIND,
    RECORD_CAPTURED_KIND,
)

from .events_references import (
    Rejection,
    _check_estimate_analogue,
    _check_estimate_cohort,
    resolve_reference,
    version_digest,
)


__all__ = [
    "ACTION_PROPOSAL_KIND",
    "CAPABILITY_VERSIONED_KIND",
    "DELIVERY_ACTOR",
    "DELIVERY_ESTIMATE_KIND",
    "ESTIMATE_CAUSES",
    "Event",
    "EventError",
    "EventPayload",
    "HUMAN_ONLY",
    "MODEL_CHANGE_KIND",
    "RECORD_CAPTURED_KIND",
    "Rejection",
    "_ESTIMATE_REQUIRED_FIELDS",
    "_check_estimate_analogue",
    "_check_estimate_cohort",
    "_check_stream_bounds",
    "_check_uuid4",
    "_estimate_digest_field",
    "_estimate_non_negative_int",
    "_estimate_text",
    "_estimate_timestamp",
    "_planning_references",
    "decision_protocol_data",
    "estimate_digest",
    "resolve_reference",
    "version_digest",
]


def _validate_model_change_links(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    """Resolve model-change provenance against the locked accepted prefix."""
    for candidate in candidates:
        if candidate["event"] != MODEL_CHANGE_KIND:
            continue
        data = candidate["data"]
        if data["base_model"]["event_id"] == candidate["event_id"]:
            raise EventError(f"{MODEL_CHANGE_KIND} base_model cannot reference itself")
        try:
            base = resolve_reference(data["base_model"], prefix)
        except EventError as exc:
            raise EventError(
                f"{MODEL_CHANGE_KIND} base_model must reference an exact earlier "
                f"record.captured event: {exc}"
            ) from exc
        if not isinstance(base, Event) or base.kind != RECORD_CAPTURED_KIND:
            raise EventError(
                f"{MODEL_CHANGE_KIND} base_model must reference a record.captured event"
            )
        if base.data["digest"] != data["base_model_digest"]:
            raise EventError(
                f"{MODEL_CHANGE_KIND} base_model_digest does not match the referenced record"
            )

        try:
            procedure = resolve_reference(data["procedure"], prefix)
        except EventError as exc:
            raise EventError(
                f"{MODEL_CHANGE_KIND} procedure must reference an exact earlier "
                f"capability.versioned event: {exc}"
            ) from exc
        if (
            not isinstance(procedure, Event)
            or procedure.kind != CAPABILITY_VERSIONED_KIND
        ):
            raise EventError(
                f"{MODEL_CHANGE_KIND} procedure must reference a capability.versioned event"
            )
        if procedure.data["version_digest"] != data["procedure_digest"]:
            raise EventError(
                f"{MODEL_CHANGE_KIND} procedure_digest does not match the referenced capability"
            )

        dataset = data["dataset"]
        if dataset is not None:
            try:
                resolved_dataset = resolve_reference(dataset, prefix)
            except EventError as exc:
                raise EventError(
                    f"{MODEL_CHANGE_KIND} dataset must reference an exact earlier "
                    f"record.captured event: {exc}"
                ) from exc
            if (
                not isinstance(resolved_dataset, Event)
                or resolved_dataset.kind != RECORD_CAPTURED_KIND
            ):
                raise EventError(
                    f"{MODEL_CHANGE_KIND} dataset must reference a record.captured event"
                )
            if resolved_dataset.data["digest"] != data["dataset_digest"]:
                raise EventError(
                    f"{MODEL_CHANGE_KIND} dataset_digest does not match the referenced record"
                )

        checkpoint = data["checkpoint"]
        if checkpoint is not None:
            try:
                resolved_checkpoint = resolve_reference(checkpoint, prefix)
            except EventError as exc:
                raise EventError(
                    f"{MODEL_CHANGE_KIND} checkpoint must reference an exact earlier "
                    f"record.captured event: {exc}"
                ) from exc
            if (
                not isinstance(resolved_checkpoint, Event)
                or resolved_checkpoint.kind != RECORD_CAPTURED_KIND
            ):
                raise EventError(
                    f"{MODEL_CHANGE_KIND} checkpoint must reference a record.captured event"
                )
            if resolved_checkpoint.data["digest"] != data["checkpoint_digest"]:
                raise EventError(
                    f"{MODEL_CHANGE_KIND} checkpoint_digest does not match the referenced record"
                )


def _validate_decision_relations(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    """Bind each P01 record to unique identities and exact earlier events."""
    history = list(prefix)
    decision_ids: set[str] = set()
    operation_ids: set[str] = set()
    for prior in prefix:
        record = decision_protocol_data(prior)
        if record is None:
            continue
        decision_id = cast(str, record["decision_id"])
        operation_id = cast(str, record["operation_id"])
        if decision_id in decision_ids:
            raise EventError(f"historical duplicate decision_id {decision_id!r}")
        if operation_id in operation_ids:
            raise EventError(f"historical duplicate operation_id {operation_id!r}")
        decision_ids.add(decision_id)
        operation_ids.add(operation_id)

    for candidate in candidates:
        record = decision_protocol_data(candidate)
        if record is not None:
            decision_id = cast(str, record["decision_id"])
            operation_id = cast(str, record["operation_id"])
            if decision_id in decision_ids:
                raise EventError(f"duplicate decision_id {decision_id!r}")
            if operation_id in operation_ids:
                raise EventError(f"duplicate operation_id {operation_id!r}")

            resolved: dict[str, Event | str] = {}
            for field, reference in _planning_references(record):
                try:
                    resolved[field] = resolve_reference(reference, history)
                except EventError as exc:
                    raise EventError(
                        f"decision protocol {field} must reference an exact earlier event: {exc}"
                    ) from exc

            superseded = resolved.get("supersedes")
            if isinstance(superseded, Event):
                previous = decision_protocol_data(superseded)
                if (
                    previous is None
                    or superseded.kind != candidate["event"]
                    or previous["ticket"] != record["ticket"]
                ):
                    raise EventError(
                        "decision protocol supersedes must name an earlier planning record "
                        "of the same kind and ticket"
                    )

            if candidate["event"] == ACTION_PROPOSAL_KIND:
                proposal_id = cast(str, candidate["data"]["proposal_id"])
                binding = cast(EventPayload, record["binding"])
                authority_ref = binding.get("authority_ref")
                if authority_ref is not None:
                    try:
                        authority = resolve_reference(authority_ref, history)
                    except EventError as exc:
                        raise EventError(
                            "protected proposal authority must reference an exact earlier "
                            f"first-party event: {exc}"
                        ) from exc
                    if not isinstance(authority, Event):
                        raise EventError(
                            "protected proposal authority cannot be legacy/unmeasured"
                        )
                    authority_data = authority.data
                    if authority_data.get("human_decision") not in HUMAN_ONLY:
                        raise EventError(
                            "protected proposal authority must be a first-party human decision"
                        )
                    if authority_data.get("proposal_id") != proposal_id:
                        raise EventError(
                            "protected proposal authority proposal_id does not match"
                        )
                    if authority_data.get("decision_id") != decision_id:
                        raise EventError(
                            "protected proposal authority decision_id does not match"
                        )

            decision_ids.add(decision_id)
            operation_ids.add(operation_id)
        history.append(Event(candidate))


def _check_delivery_estimate_contract(event: EventPayload) -> None:
    if event["event"] != DELIVERY_ESTIMATE_KIND:
        return
    if event["actor"] != DELIVERY_ACTOR:
        raise EventError(
            f"{DELIVERY_ESTIMATE_KIND} must be attributed to declared writer {DELIVERY_ACTOR!r}"
        )
    data = event["data"]
    actual = set(data)
    if actual != _ESTIMATE_REQUIRED_FIELDS:
        missing = sorted(_ESTIMATE_REQUIRED_FIELDS - actual)
        unexpected = sorted(actual - _ESTIMATE_REQUIRED_FIELDS)
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if unexpected:
            detail.append(f"unexpected {unexpected}")
        raise EventError(
            f"{DELIVERY_ESTIMATE_KIND} body fields are fixed: {'; '.join(detail)}"
        )
    _estimate_text(data["delivery_id"], "delivery_id")
    _estimate_text(data["commitment_id"], "commitment_id")
    _estimate_digest_field(data["commitment_digest"], "commitment_digest")
    _estimate_digest_field(data["plan_digest"], "plan_digest")
    _check_uuid4(data["estimate_id"], "estimate_id")
    revision = data["revision"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise EventError("revision must be a non-negative integer")
    predecessor = data["predecessor_estimate_id"]
    original = data["original_estimate_id"]
    if revision == 0:
        if predecessor is not None:
            raise EventError("revision zero must not carry predecessor_estimate_id")
        if original != data["estimate_id"]:
            raise EventError(
                "revision zero original_estimate_id must equal estimate_id"
            )
        if data.get("cause") is not None:
            raise EventError("revision zero must not carry cause")
        if data["notice_preceded_upper_bound"] is not False:
            raise EventError("revision zero notice_preceded_upper_bound must be false")
    else:
        if not isinstance(predecessor, str):
            raise EventError("revisions after zero must carry predecessor_estimate_id")
        _check_uuid4(predecessor, "predecessor_estimate_id")
        _check_uuid4(original, "original_estimate_id")
        cause = data.get("cause")
        if cause not in ESTIMATE_CAUSES:
            raise EventError(
                f"revisions after zero must carry cause in {sorted(ESTIMATE_CAUSES)}"
            )
        notice = data["notice_preceded_upper_bound"]
        if not isinstance(notice, bool):
            raise EventError("notice_preceded_upper_bound must be a boolean")
    earliest = _estimate_timestamp(data["earliest_at"], "earliest_at")
    latest = _estimate_timestamp(data["latest_at"], "latest_at")
    if datetime.fromisoformat(latest) < datetime.fromisoformat(earliest):
        raise EventError("latest_at must be on or after earliest_at")
    _estimate_timestamp(data["issued_at"], "issued_at")
    _estimate_text(data["evidence_class"], "evidence_class")
    _check_estimate_analogue(data["analogue_ids"])
    sample_size = data["sample_size"]
    if (
        not isinstance(sample_size, int)
        or isinstance(sample_size, bool)
        or sample_size < 0
    ):
        raise EventError("sample_size must be a non-negative integer")
    _estimate_text(data["method"], "method")
    _check_stream_bounds(data["stream_bounds"])
    _estimate_digest_field(data["resource_snapshot_digest"], "resource_snapshot_digest")
    _estimate_non_negative_int(data["checkpoint_interval_s"], "checkpoint_interval_s")
    _estimate_non_negative_int(data["recovery_allowance_s"], "recovery_allowance_s")
    not_included = data["not_included"]
    if not isinstance(not_included, list):
        raise EventError("not_included must be an array")
    for index, item in enumerate(not_included):
        _estimate_text(item, f"not_included[{index}]")
    _check_estimate_cohort(data["cohort_key"])
    digest = data["estimate_digest"]
    if digest != estimate_digest(data):
        raise EventError("estimate_digest does not match the frozen estimate")

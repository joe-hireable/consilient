"""The decision protocol, and the transitions that keep an exposure honest.

Before an autonomous decision is allowed a consequence it must state its protocol and
its binding. The protocol is threshold-gated on three versioned inputs — whether
anything later relies on the decision, whether the question is open, whether being wrong
costs more than deciding slowly — each of them true, false or unknown, and its status
must agree with them: not_warranted requires at least one false input, and completed
permits none. A completed protocol also names the instructions, the bar, the search and
the killing check it rests on, each as an exact earlier event. The binding names the
admission class and then exactly the digests that class requires, no more and no fewer —
an effect manifest, sandbox and verifier policies, the receipt expected back, a recovery
proof for a recoverable mutation, an authority reference for anything touching a
protected class.

The rest are transitions read against the accepted prefix. A candidate exposed to a
reviewer must belong to the queue that is open, carry the next ordinal in sequence and
stay inside the declared stream cap, and its verification outcome must point back at the
exposure it came from and agree with it about which attempt it was. An exposure order
that can be reshuffled after the fact is not blind, and a review that is not blind
measures the reviewer rather than the artefact.

Capability lineage edges resolve to real earlier records — a source that is a captured
record, a duplicate or supersession that is a capability of the same kind and never
itself. `derive_delivery_estimate` computes a revision-zero estimate from plan inputs
and the durations of prior matching outcomes, including the censored ones, rather than
accepting a number somebody typed."""

from __future__ import annotations
import math
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import cast
from . import effects
from .events_vocabulary import (
    PROTECTED_DECISION_CLASSES,
    _AUTONOMOUS_ADMISSION_CLASSES,
    _cohort_matches,
    _outcome_duration_s,
    _outcome_is_censored,
    _schedule_stream_bounds,
    estimate_digest,
    new_event_id,
)

from .events_digests import (
    _decision_digest,
    _queue_opened,
)

from .events_durability import (
    Event,
)

from .events_fields import (
    DELIVERY_OUTCOME_KINDS,
    _decision_text,
    _nearest_rank_percentile,
    _outcome_is_completed,
)

from .events_kinds import (
    CANDIDATE_EXPOSED_KIND,
    CAPABILITY_VERSIONED_KIND,
    EventError,
    EventPayload,
    RECORD_CAPTURED_KIND,
    REVIEW_QUEUE_OPENED_KIND,
    VERIFICATION_OUTCOME_KIND,
    _PROTECTED_ADMISSION_CLASSES,
)

from .events_references import (
    Rejection,
    _check_exact_event_reference,
    _outcome_reference,
    resolve_reference,
)


__all__ = [
    "CANDIDATE_EXPOSED_KIND",
    "CAPABILITY_VERSIONED_KIND",
    "DELIVERY_OUTCOME_KINDS",
    "Event",
    "EventError",
    "EventPayload",
    "PROTECTED_DECISION_CLASSES",
    "RECORD_CAPTURED_KIND",
    "REVIEW_QUEUE_OPENED_KIND",
    "Rejection",
    "VERIFICATION_OUTCOME_KIND",
    "_AUTONOMOUS_ADMISSION_CLASSES",
    "_PROTECTED_ADMISSION_CLASSES",
    "_check_exact_event_reference",
    "_cohort_matches",
    "_decision_digest",
    "_decision_text",
    "_nearest_rank_percentile",
    "_outcome_duration_s",
    "_outcome_is_censored",
    "_outcome_is_completed",
    "_outcome_reference",
    "_queue_opened",
    "_schedule_stream_bounds",
    "derive_delivery_estimate",
    "estimate_digest",
    "new_event_id",
    "resolve_reference",
]


def _check_protocol(value: object) -> str:
    if not isinstance(value, dict):
        raise EventError("decision protocol protocol must be an object")
    status = value.get("status")
    base = {"status", "threshold"}
    completion = {
        "instructions_ref",
        "bar_ref",
        "search_ref",
        "killing_check_ref",
    }
    expected = base | completion if status == "completed" else base
    if set(value) != expected:
        missing = sorted(expected - set(value))
        unexpected = sorted(set(value) - expected)
        raise EventError(
            f"decision protocol {status!r} fields mismatch; missing {missing}, unexpected {unexpected}"
        )
    if status not in {"not_warranted", "completed"}:
        raise EventError("decision protocol status must be not_warranted or completed")
    threshold = value["threshold"]
    threshold_fields = {
        "version",
        "later_reliance",
        "question_open",
        "wrong_costs_more",
    }
    if not isinstance(threshold, dict) or set(threshold) != threshold_fields:
        raise EventError(
            "decision protocol threshold must carry its three versioned inputs"
        )
    _decision_text(threshold["version"], "protocol.threshold.version")
    tri_states = {"true", "false", "unknown"}
    states = []
    for field in ("later_reliance", "question_open", "wrong_costs_more"):
        state = threshold[field]
        if state not in tri_states:
            raise EventError(
                f"decision protocol threshold.{field} must be true, false or unknown"
            )
        states.append(state)
    if status == "not_warranted" and "false" not in states:
        raise EventError(
            "decision protocol not_warranted requires a false threshold input"
        )
    if status == "completed" and "false" in states:
        raise EventError(
            "decision protocol completed cannot carry a false threshold input"
        )
    for field in completion & set(value):
        _check_exact_event_reference(value[field], f"protocol.{field}")
    return cast(str, status)


def _check_binding(value: object, *, protected_proposal: bool) -> str:
    if not isinstance(value, dict):
        raise EventError("decision protocol binding must be an object")
    admission = value.get("kind")
    if not isinstance(admission, str) or admission not in effects.ADMISSION_CLASSES:
        raise EventError("decision protocol binding has an unknown admission class")
    admitted = (
        _PROTECTED_ADMISSION_CLASSES
        if protected_proposal
        else _AUTONOMOUS_ADMISSION_CLASSES
    )
    if admission not in admitted:
        label = "protected proposal" if protected_proposal else "autonomous decision"
        raise EventError(
            f"decision protocol admission {admission!r} is invalid for {label}"
        )

    execution_fields = {
        "kind",
        "effect_manifest_digest",
        "sandbox_policy_digest",
        "verifier_policy_digest",
        "expected_receipt_digest",
    }
    if admission == "material_choice":
        expected = {"kind"}
    elif admission in {"contained_execution", "proof_operation"}:
        expected = execution_fields
    elif admission == "recoverable_mutation":
        expected = execution_fields | {"recovery_proof_digest"}
    elif admission == "protected_covered":
        expected = {
            "kind",
            "protected_class",
            "effect_manifest_digest",
            "authority_ref",
        }
    else:
        expected = {"kind", "protected_class", "effect_manifest_digest"}
    if set(value) != expected:
        raise EventError(
            f"decision protocol binding for {admission} must contain exactly {sorted(expected)}"
        )
    for field in expected & {
        "effect_manifest_digest",
        "sandbox_policy_digest",
        "verifier_policy_digest",
        "expected_receipt_digest",
        "recovery_proof_digest",
    }:
        _decision_digest(value[field], f"binding.{field}")
    if "protected_class" in expected:
        protected_class = value["protected_class"]
        if protected_class not in PROTECTED_DECISION_CLASSES:
            raise EventError("decision protocol binding has an unknown protected class")
    if "authority_ref" in expected:
        _check_exact_event_reference(value["authority_ref"], "binding.authority_ref")
    return admission


def _validate_capability_versioned_links(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    """Resolve source and lineage edges against the locked accepted prefix.

    resolve_reference returns the string 'unmeasured' for a schema-v1 row identified
    only by kind and content hash. The reference schema already refuses a capability
    edge without an event_id, so that string cannot arrive here today; the isinstance
    guards below keep the refusal fail-closed if that schema is ever loosened.
    """
    for candidate in candidates:
        if candidate["event"] != CAPABILITY_VERSIONED_KIND:
            continue
        data = candidate["data"]
        try:
            resolved = resolve_reference(data["source_object"], prefix)
        except EventError as exc:
            raise EventError(
                f"{CAPABILITY_VERSIONED_KIND} source_object must reference an exact earlier "
                f"record.captured event: {exc}"
            ) from exc
        if not isinstance(resolved, Event) or resolved.kind != RECORD_CAPTURED_KIND:
            raise EventError(
                f"{CAPABILITY_VERSIONED_KIND} source_object must reference a record.captured event"
            )
        for relation in ("duplicate_of", "supersedes"):
            reference = data[relation]
            if reference is None:
                continue
            if reference["event_id"] == candidate["event_id"]:
                raise EventError(
                    f"{CAPABILITY_VERSIONED_KIND} {relation} cannot reference itself"
                )
            try:
                target = resolve_reference(reference, prefix)
            except EventError as exc:
                raise EventError(
                    f"{CAPABILITY_VERSIONED_KIND} {relation} must reference an exact earlier "
                    f"capability.versioned event: {exc}"
                ) from exc
            if (
                not isinstance(target, Event)
                or target.kind != CAPABILITY_VERSIONED_KIND
            ):
                raise EventError(
                    f"{CAPABILITY_VERSIONED_KIND} {relation} must reference capability.versioned"
                )


def derive_delivery_estimate(
    prefix: Sequence[Event],
    *,
    plan: Mapping[str, object],
    delivery_id: str,
    issued_at: datetime,
    cohort_key: Mapping[str, str],
    resource_snapshot_digest: str,
    checkpoint_interval_s: int,
    recovery_allowance_s: int,
    not_included: Sequence[str] | None = None,
) -> dict[str, object]:
    """Derive one revision-zero delivery estimate from plan inputs and prior outcomes."""
    matching: list[Event] = []
    completed_durations: list[float] = []
    censored_floors: list[float] = []
    for event in prefix:
        if event.kind not in DELIVERY_OUTCOME_KINDS:
            continue
        if not _cohort_matches(event.data, cohort_key):
            continue
        matching.append(event)
        duration = _outcome_duration_s(event.data)
        if duration is None:
            continue
        if _outcome_is_completed(event.data):
            completed_durations.append(duration)
        elif _outcome_is_censored(event.data):
            censored_floors.append(duration + recovery_allowance_s)

    analogue_ids = [_outcome_reference(event) for event in matching]
    estimate_inputs = cast(dict[str, object], plan["estimate_inputs"])
    cold_lower = cast(int, estimate_inputs["duration_lower_s"])
    cold_upper = cast(int, estimate_inputs["duration_upper_s"])

    if len(completed_durations) >= 5:
        lower_s = int(_nearest_rank_percentile(completed_durations, 0.10))
        upper_s = int(_nearest_rank_percentile(completed_durations, 0.90))
        evidence_class = "measured"
        method = "comparable_deliveries_percentile"
    else:
        lower_s = cold_lower
        upper_s = cold_upper
        evidence_class = "asserted: low evidence"
        method = "cold_start_slice_schedule"

    for floor in censored_floors:
        upper_s = max(upper_s, int(math.ceil(floor)))

    earliest_at = issued_at + timedelta(seconds=lower_s)
    latest_at = issued_at + timedelta(seconds=upper_s)
    estimate_id = new_event_id()
    payload: dict[str, object] = {
        "delivery_id": delivery_id,
        "commitment_id": cast(str, plan["commitment_id"]),
        "commitment_digest": cast(str, plan["commitment_digest"]),
        "plan_digest": cast(str, plan["plan_digest"]),
        "estimate_id": estimate_id,
        "revision": 0,
        "predecessor_estimate_id": None,
        "original_estimate_id": estimate_id,
        "earliest_at": earliest_at.isoformat(),
        "latest_at": latest_at.isoformat(),
        "issued_at": issued_at.isoformat(),
        "evidence_class": evidence_class,
        "analogue_ids": analogue_ids,
        "sample_size": len(completed_durations),
        "method": method,
        "stream_bounds": _schedule_stream_bounds(
            plan, lower_s=lower_s, upper_s=upper_s
        ),
        "resource_snapshot_digest": resource_snapshot_digest,
        "checkpoint_interval_s": checkpoint_interval_s,
        "recovery_allowance_s": recovery_allowance_s,
        "not_included": list(not_included or []),
        "cohort_key": dict(cohort_key),
        "cause": None,
        "notice_preceded_upper_bound": False,
    }
    payload["estimate_digest"] = estimate_digest(payload)
    return payload


def _validate_candidate_exposed_transition(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    queue = _queue_opened(prefix)
    if queue is None:
        raise EventError(
            f"{CANDIDATE_EXPOSED_KIND} requires a prior {REVIEW_QUEUE_OPENED_KIND} event"
        )
    queue_data = queue.data
    queue_id = cast(str, queue_data["queue_id"])
    prior = [
        event
        for event in prefix
        if event.kind == CANDIDATE_EXPOSED_KIND
        and event.data.get("queue_id") == queue_id
    ]
    next_ordinal = len(prior) + 1
    for candidate in candidates:
        if candidate["event"] != CANDIDATE_EXPOSED_KIND:
            continue
        data = candidate["data"]
        if data["queue_id"] != queue_id:
            raise EventError(
                f"{CANDIDATE_EXPOSED_KIND} queue_id must match the opened review queue"
            )
        if int(data["exposure_ordinal"]) != next_ordinal:
            raise EventError(
                f"{CANDIDATE_EXPOSED_KIND} exposure_ordinal must be sequential; "
                f"expected {next_ordinal}, got {data['exposure_ordinal']!r}"
            )
        if int(data["exposure_ordinal"]) > int(queue_data["stream_cap"]):
            raise EventError(
                f"{CANDIDATE_EXPOSED_KIND} exposure exceeds stream_cap "
                f"{queue_data['stream_cap']}"
            )
        for field in (
            "task_family",
            "protocol_id",
            "verifier_version",
            "verifier_contract_digest",
        ):
            if data[field] != queue_data[field]:
                raise EventError(
                    f"{CANDIDATE_EXPOSED_KIND} {field} must match the frozen review queue"
                )
        next_ordinal += 1


def _validate_verification_outcome_exposure_transition(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    queue = _queue_opened(prefix)
    if queue is None:
        return
    exposures_by_token = {
        cast(str, event.data["start_token"]): event
        for event in prefix
        if event.kind == CANDIDATE_EXPOSED_KIND
    }
    for candidate in candidates:
        if candidate["event"] != VERIFICATION_OUTCOME_KIND:
            continue
        data = candidate["data"]
        token = data.get("start_token")
        if not isinstance(token, str):
            raise EventError(
                f"{VERIFICATION_OUTCOME_KIND} requires start_token when a review queue is open"
            )
        exposure = exposures_by_token.get(token)
        if exposure is None:
            raise EventError(
                f"{VERIFICATION_OUTCOME_KIND} start_token must reference a prior "
                f"{CANDIDATE_EXPOSED_KIND} event"
            )
        if exposure.data["attempt_id"] != data["attempt_id"]:
            raise EventError(
                f"{VERIFICATION_OUTCOME_KIND} attempt_id must match the referenced exposure"
            )

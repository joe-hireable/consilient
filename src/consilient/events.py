"""Authoritative trajectory events.

The append-only JSONL log is the record; everything else is a projection of it
(ADR-0006).

Invariants enforced here, each with a test in the same commit:
  V0-01  every event is schema-versioned and append-only.
  V0-18  a human decision (approval, consent, gate lift, spend authorisation
         or verdict) is valid only when the human principal authored it.
  V0-22  every autonomous decision records a reversal path.
  V0-23  an autonomous decision cannot claim a class reserved to the user.
  V0-24  a recorded reversal has a machine-checkable executable shape.
  V0-26  multi-contributor events must declare a distinct evidence_class per contributor.
  V0-27  attempt outcomes and their later human verdicts share one stable identity.
  V0-28  a declared non-local channel cannot deliver a human decision.
  V0-30  a usage figure names its provenance; a provider that could not be read
         reports 'unavailable' and carries no number.
  V0-31  a knowledge retrieval names its source, licence and retrieval date; an
         unreachable source reports 'unavailable' and carries no invented content.
  V0-41  a capability gap names what was asked, what was tried and how it failed, and
         declares its closure; failure classes no retry can close must escalate.

The writers stay here — `append`, the batch `append_transaction`, and the two callers
that go through them, `record_escalation` and `record_intent`. The rest of the module
now stands beside it in files sharing this stem. `events_vocabulary` holds the closed
value sets and the leaf primitives; `events_kinds` the event-kind and actor names, the
schema constants and `EventError`; `events_evidence` the evidence-class, knowledge and
measurement contracts and the append lock; `events_durability` the `Event` row, the
lock, the whole-byte write, the fsyncs and the prefix digest; `events_fields` the typed
field coercions and `canonical`; `events_authority` human authority, budget and usage;
`events_supervision` consent, escalation, scheduler intent, promotion and `bypassed`;
`events_digests` the content addresses and event identities; `events_references`
`resolve_reference` and `Rejection`; `events_versioning` `CapabilityManifest` and the
model-change contract; `events_relations`, `events_protocol` and `events_records` the
decision protocol and the transition validators; `events_validation` `validate`, `read`
and the validator registry; and `events_transactions` `read_all` and the
compare-and-append transaction.
"""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from datetime import timedelta
from pathlib import Path
from . import effects

from .events_authority import (
    _check_budget_contract,
    _check_human_authority,
)

from .events_digests import (
    content_digest,
    decision_protocol_data,
    event_sha256,
    execution_contract_key,
)

from .events_durability import (
    _OPEN_FLAGS,
    _TRANSACTION_OPEN_FLAGS,
    Event,
    _budget_transaction,
    _fsync_directory,
    _lock_file,
    _unlock_file,
    parse_capability_identity,
    prefix_digest,
)

from .events_evidence import (
    _READ_BACKOFF,
    _appending,
    _check_evidence_class,
    _check_knowledge_contract,
    _retry_sleep,
)

from .events_fields import (
    CONSENT_KINDS,
    DELIVERY_OUTCOME_KINDS,
    ESCALATION_CLASSES,
    FEEDBACK_KINDS,
    PROMOTE_CONTRACT_KINDS,
    _hex64,
    canonical,
    mutation_class_for,
)

from .events_kinds import (
    ACQUISITION_SOURCE_STATUSES,
    ACQUISITION_STANCES,
    ACTION_PROPOSAL_KIND,
    ACTIVATION_REFUSED_KIND,
    ATTEMPT_REVIEWED_KIND,
    BUDGET_LOCK,
    BUDGET_RESERVATION_ACTOR,
    BUDGET_STATE_ACTOR,
    BUDGET_STATE_KIND,
    CANDIDATE_EXPOSED_KIND,
    CANONICAL_ON_OTHER,
    CAPABILITY_GAP_KIND,
    CAPABILITY_MANIFEST_KINDS,
    CAPABILITY_VERSIONED_KIND,
    CONSENT_GRANTED,
    CONSENT_WITHDRAWN,
    DECISION_KIND,
    DELIVERY_ACTOR,
    DELIVERY_ESTIMATE_KIND,
    DIGEST_RE,
    ESCALATION_ACTOR,
    ESCALATION_ATTEMPTED_KIND,
    ESCALATION_BUDGET,
    ESCALATION_PRECISION_FLOOR,
    ESCALATION_PRECISION_WINDOW,
    ESCALATION_WINDOW,
    EventError,
    EventPayload,
    FEEDBACK_ANSWERED_KIND,
    FEEDBACK_ASKED_KIND,
    FEEDBACK_DECLINED_KIND,
    GAP_CLOSURES,
    GAP_FAILURES,
    GOAL_ACHIEVED,
    IMPACT_CONTRACT_KIND,
    INTENT_REASONS,
    INTENT_REASON_PREFIXES,
    INTENT_RECORDED_FIELDS,
    INTENT_RECORDED_KIND,
    INTENT_STARVED_FIELDS,
    INTENT_STARVED_KIND,
    KNOWLEDGE_ACTOR,
    KNOWLEDGE_RETRIEVED_KIND,
    KNOWLEDGE_STATUSES,
    MAX_CLOCK_SKEW_S,
    MEASUREMENT_ACTOR,
    MEASUREMENT_REGISTERED_KIND,
    MEASUREMENT_RESULT_KIND,
    METERED_CURRENCY,
    METERED_PROVIDER,
    MODEL_CHANGE_KIND,
    MODEL_CHANGE_STATUSES,
    OUTCOME_KIND,
    PROMOTER_BETA_RECEIPT_KIND,
    PROMOTE_ACTOR,
    PROVENANCE,
    RECORD_CAPTURED_KIND,
    RECORD_KIND_ALIASES,
    REQUIRED,
    REVERSAL_KINDS,
    REVIEW_PRESENTATION_FROZEN_KIND,
    REVIEW_QUEUE_OPENED_KIND,
    SCHEDULER_ACTOR,
    SCHEMA_VERSION,
    SPEND_RESERVED_KIND,
    STARVATION_TICKS,
    STARVATION_WINDOW,
    TS,
    USAGE_ACTOR,
    USAGE_KIND,
    USAGE_STATUSES,
    VERDICT_CORRECTION_KIND,
    VERDICT_KIND,
    VERIFICATION_OUTCOME_KIND,
    VERIFICATION_STATUSES,
    VISIBILITY_CHANGE_KIND,
    VISIBILITY_DEFAULT,
    VISIBILITY_LEVELS,
    _BUDGET_LOCK_HELD,
    _READ_RETRIES,
    _TRANSACTION_LOCK_BYTE,
)

from .events_protocol import (
    _validate_candidate_exposed_transition,
    _validate_capability_versioned_links,
    _validate_verification_outcome_exposure_transition,
    derive_delivery_estimate,
)

from .events_records import (
    TransitionValidator,
    _check_record_contract,
    _validate_delivery_estimate_transition,
    _validate_effect_receipt_chain,
    _validate_record_relations,
    rejection_digest,
)

from .events_references import (
    Rejection,
    _escalation_disposition,
    resolve_reference,
    starvation,
    version_digest,
)

from .events_relations import (
    _validate_decision_relations,
    _validate_model_change_links,
)

from .events_supervision import (
    bypassed,
)

from .events_transactions import (
    _check_clock,
    _read_under_lock,
    _transaction,
    _write_validated,
    read_all,
)

from .events_validation import (
    _TRANSITION_VALIDATORS,
    _prepare_for_append,
    canonical_manifest,
    read,
    register_transition_validator,
    validate,
)

from .events_versioning import (
    CapabilityManifest,
)

from .events_vocabulary import (
    ACQUISITION_CHANNELS,
    BROWSER_RETAINED_EVIDENCE,
    CAPABILITY_KIND_ALIASES,
    CAPABILITY_MANIFEST_STATUSES,
    CAPABILITY_VERSIONED_FIELDS,
    CONSENT_PURPOSES,
    DISPATCH_STATUSES,
    ESCALATION_ATTEMPT_FIELDS,
    ESCALATION_REFUSAL_REASONS,
    ESTIMATE_CAUSES,
    FEEDBACK_COMPOSITE_FIELDS,
    HUMAN_ONLY,
    MODEL_CHANGE_FIELDS,
    MODEL_CHANGE_KIND_ALIASES,
    MODEL_CHANGE_MUTATION_CLASSES,
    PROTECTED_DECISION_CLASSES,
    RECORD_CAPTURED_FIELDS,
    RESPONSE_RATING_FIELDS,
    USER_ONLY,
    estimate_digest,
    jittered_sleep,
    new_event_id,
)

__all__ = [
    "_OPEN_FLAGS",
    "_TRANSACTION_OPEN_FLAGS",
    "ACQUISITION_CHANNELS",
    "ACQUISITION_SOURCE_STATUSES",
    "ACQUISITION_STANCES",
    "ACTION_PROPOSAL_KIND",
    "ACTIVATION_REFUSED_KIND",
    "ATTEMPT_REVIEWED_KIND",
    "BROWSER_RETAINED_EVIDENCE",
    "BUDGET_LOCK",
    "BUDGET_RESERVATION_ACTOR",
    "BUDGET_STATE_ACTOR",
    "BUDGET_STATE_KIND",
    "CANDIDATE_EXPOSED_KIND",
    "CANONICAL_ON_OTHER",
    "CAPABILITY_GAP_KIND",
    "CAPABILITY_KIND_ALIASES",
    "CAPABILITY_MANIFEST_KINDS",
    "CAPABILITY_MANIFEST_STATUSES",
    "CAPABILITY_VERSIONED_FIELDS",
    "CAPABILITY_VERSIONED_KIND",
    "CONSENT_GRANTED",
    "CONSENT_KINDS",
    "CONSENT_PURPOSES",
    "CONSENT_WITHDRAWN",
    "CapabilityManifest",
    "DECISION_KIND",
    "DELIVERY_ACTOR",
    "DELIVERY_ESTIMATE_KIND",
    "DELIVERY_OUTCOME_KINDS",
    "DIGEST_RE",
    "DISPATCH_STATUSES",
    "ESCALATION_ACTOR",
    "ESCALATION_ATTEMPTED_KIND",
    "ESCALATION_ATTEMPT_FIELDS",
    "ESCALATION_BUDGET",
    "ESCALATION_CLASSES",
    "ESCALATION_PRECISION_FLOOR",
    "ESCALATION_PRECISION_WINDOW",
    "ESCALATION_REFUSAL_REASONS",
    "ESCALATION_WINDOW",
    "ESTIMATE_CAUSES",
    "Event",
    "EventError",
    "EventPayload",
    "FEEDBACK_ANSWERED_KIND",
    "FEEDBACK_ASKED_KIND",
    "FEEDBACK_COMPOSITE_FIELDS",
    "FEEDBACK_DECLINED_KIND",
    "FEEDBACK_KINDS",
    "GAP_CLOSURES",
    "GAP_FAILURES",
    "GOAL_ACHIEVED",
    "HUMAN_ONLY",
    "IMPACT_CONTRACT_KIND",
    "INTENT_REASONS",
    "INTENT_REASON_PREFIXES",
    "INTENT_RECORDED_FIELDS",
    "INTENT_RECORDED_KIND",
    "INTENT_STARVED_FIELDS",
    "INTENT_STARVED_KIND",
    "KNOWLEDGE_ACTOR",
    "KNOWLEDGE_RETRIEVED_KIND",
    "KNOWLEDGE_STATUSES",
    "MAX_CLOCK_SKEW_S",
    "MEASUREMENT_ACTOR",
    "MEASUREMENT_REGISTERED_KIND",
    "MEASUREMENT_RESULT_KIND",
    "METERED_CURRENCY",
    "METERED_PROVIDER",
    "MODEL_CHANGE_FIELDS",
    "MODEL_CHANGE_KIND",
    "MODEL_CHANGE_KIND_ALIASES",
    "MODEL_CHANGE_MUTATION_CLASSES",
    "MODEL_CHANGE_STATUSES",
    "OUTCOME_KIND",
    "PROMOTER_BETA_RECEIPT_KIND",
    "PROMOTE_ACTOR",
    "PROMOTE_CONTRACT_KINDS",
    "PROTECTED_DECISION_CLASSES",
    "PROVENANCE",
    "RECORD_CAPTURED_FIELDS",
    "RECORD_CAPTURED_KIND",
    "RECORD_KIND_ALIASES",
    "REQUIRED",
    "RESPONSE_RATING_FIELDS",
    "REVERSAL_KINDS",
    "REVIEW_PRESENTATION_FROZEN_KIND",
    "REVIEW_QUEUE_OPENED_KIND",
    "Rejection",
    "SCHEDULER_ACTOR",
    "SCHEMA_VERSION",
    "SPEND_RESERVED_KIND",
    "STARVATION_TICKS",
    "STARVATION_WINDOW",
    "TS",
    "TransitionValidator",
    "USAGE_ACTOR",
    "USAGE_KIND",
    "USAGE_STATUSES",
    "USER_ONLY",
    "VERDICT_CORRECTION_KIND",
    "VERDICT_KIND",
    "VERIFICATION_OUTCOME_KIND",
    "VERIFICATION_STATUSES",
    "VISIBILITY_CHANGE_KIND",
    "VISIBILITY_DEFAULT",
    "VISIBILITY_LEVELS",
    "_BUDGET_LOCK_HELD",
    "_READ_BACKOFF",
    "_READ_RETRIES",
    "_TRANSACTION_LOCK_BYTE",
    "_TRANSITION_VALIDATORS",
    "_appending",
    "_budget_transaction",
    "_check_budget_contract",
    "_check_clock",
    "_check_evidence_class",
    "_check_human_authority",
    "_check_knowledge_contract",
    "_check_record_contract",
    "_escalation_disposition",
    "_fsync_directory",
    "_hex64",
    "_lock_file",
    "_prepare_for_append",
    "_read_under_lock",
    "_retry_sleep",
    "_transaction",
    "_unlock_file",
    "_validate_candidate_exposed_transition",
    "_validate_capability_versioned_links",
    "_validate_decision_relations",
    "_validate_delivery_estimate_transition",
    "_validate_effect_receipt_chain",
    "_validate_model_change_links",
    "_validate_record_relations",
    "_validate_verification_outcome_exposure_transition",
    "_write_validated",
    "append",
    "append_transaction",
    "bypassed",
    "canonical",
    "canonical_manifest",
    "content_digest",
    "decision_protocol_data",
    "derive_delivery_estimate",
    "estimate_digest",
    "event_sha256",
    "execution_contract_key",
    "jittered_sleep",
    "mutation_class_for",
    "new_event_id",
    "parse_capability_identity",
    "prefix_digest",
    "read",
    "read_all",
    "record_escalation",
    "record_intent",
    "register_transition_validator",
    "rejection_digest",
    "resolve_reference",
    "starvation",
    "validate",
    "version_digest",
]


def record_intent(
    path: Path,
    *,
    ts: str,
    tick: int,
    selected: Sequence[str] = (),
    not_selected: Mapping[str, str],
    actor: str = SCHEDULER_ACTOR,
    ticks: int = STARVATION_TICKS,
    window: timedelta = STARVATION_WINDOW,
) -> list[EventPayload]:
    """Write one tick of scheduler intent, then any starvation it has just established.

    Returns the appended events, the intent record first. Emitting at the same chokepoint
    that writes the record keeps `events.py` the single writer and means a scheduler
    cannot record a bench without also surfacing a bench that has gone on too long.
    """
    intent = append(
        path,
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": INTENT_RECORDED_KIND,
            "actor": actor,
            "data": {
                "tick": tick,
                "selected": list(selected),
                "not_selected": dict(not_selected),
            },
        },
    )
    written = [intent]
    events, _rejected = read_all(path.parent)
    for data in starvation(events, ticks=ticks, window=window):
        written.append(
            append(
                path,
                {
                    "v": SCHEMA_VERSION,
                    "ts": ts,
                    "event": INTENT_STARVED_KIND,
                    "actor": actor,
                    "data": data,
                },
            )
        )
    return written


def record_escalation(
    path: Path,
    *,
    ts: str,
    root_cause: str,
    escalation_class: str,
    what_stopped: str,
    what_it_is_holding: str,
    what_i_need: str,
    default_if_no_reply: Mapping[str, str],
    evidence: str,
    decision_changed: bool | None = None,
    actor: str = ESCALATION_ACTOR,
) -> EventPayload:
    """Append one delivered or refused escalation attempt through the single writer."""
    data: EventPayload = {
        "root_cause": root_cause,
        "escalation_class": escalation_class,
        "what_stopped": what_stopped,
        "what_it_is_holding": what_it_is_holding,
        "what_i_need": what_i_need,
        "default_if_no_reply": dict(default_if_no_reply),
        "evidence": evidence,
        "disposition": "delivered",
        "refusal_reason": None,
        "decision_changed": decision_changed,
    }
    attempt: EventPayload = {
        "v": SCHEMA_VERSION,
        "ts": ts,
        "event": ESCALATION_ATTEMPTED_KIND,
        "actor": actor,
        "data": data,
    }
    if escalation_class not in ESCALATION_CLASSES:
        data["disposition"] = "refused"
        data["refusal_reason"] = "out_of_set_class"
    validate(attempt)
    return append(path, attempt)


register_transition_validator((RECORD_CAPTURED_KIND,), _validate_record_relations)

register_transition_validator(
    (CAPABILITY_VERSIONED_KIND,), _validate_capability_versioned_links
)

register_transition_validator((MODEL_CHANGE_KIND,), _validate_model_change_links)

register_transition_validator(
    (effects.EFFECT_INTENT, effects.EFFECT_RECEIPT), _validate_effect_receipt_chain
)

register_transition_validator(
    (DECISION_KIND, ACTION_PROPOSAL_KIND), _validate_decision_relations
)


def append_transaction(
    log_dir: Path,
    candidates: list[EventPayload],
    transition_validator: TransitionValidator,
) -> list[EventPayload]:
    """Validate, compare and append one contiguous batch with one acknowledgement.

    Every candidate is validated before any byte is written; the accepted prefix
    and the rejections are then read while holding the per-log lock and handed
    to `transition_validator`, which refuses by raising EventError; only then is
    the batch written contiguously and fsynced. One transaction writes one log,
    so every candidate must carry the same `ts` date. The budget kinds keep
    their own serialised path through `append()` and are refused here.
    """
    if not candidates:
        raise EventError("a transaction must carry at least one candidate")
    checked = [_prepare_for_append(candidate) for candidate in candidates]
    budgeted = {candidate["event"] for candidate in checked} & {
        BUDGET_STATE_KIND,
        SPEND_RESERVED_KIND,
    }
    if budgeted:
        raise EventError(
            f"{sorted(budgeted)} keep the budget serialisation path through "
            "append(); a second governance path for them would be bypassable"
        )
    dates = {candidate["ts"][:10] for candidate in checked}
    if len(dates) != 1:
        raise EventError(
            f"one transaction writes one log; the candidates span dates {sorted(dates)}"
        )
    return _transaction(
        log_dir / f"{next(iter(dates))}.jsonl", checked, transition_validator
    )


def append(path: Path, event: EventPayload) -> EventPayload:
    """Validate and append. The only writer of the log."""
    event = _prepare_for_append(event)
    if event["event"] in (BUDGET_STATE_KIND, SPEND_RESERVED_KIND):
        lock = (path.parent / BUDGET_LOCK).resolve()
        if _BUDGET_LOCK_HELD.get() == lock:
            return _write_validated(path, event)
        try:
            with _budget_transaction(path.parent):
                return _write_validated(path, event)
        except FileExistsError as exc:
            raise EventError("the budget trajectory is busy") from exc
    if (
        event["event"] in _TRANSITION_VALIDATORS
        or event["event"] == ESCALATION_ATTEMPTED_KIND
    ):
        # A governed kind takes the same transaction as a batch, so the domain
        # rule runs against the locked prefix whichever door the caller took.
        return _transaction(path, [event], None)[0]
    return _write_validated(path, event)


register_transition_validator(
    (DELIVERY_ESTIMATE_KIND,), _validate_delivery_estimate_transition
)

register_transition_validator(
    (CANDIDATE_EXPOSED_KIND,), _validate_candidate_exposed_transition
)

register_transition_validator(
    (VERIFICATION_OUTCOME_KIND,), _validate_verification_outcome_exposure_transition
)

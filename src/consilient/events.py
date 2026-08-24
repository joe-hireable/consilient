"""Authoritative trajectory events.

The append-only JSONL log is the record; everything else is a projection of it (ADR-0006).

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
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, cast

from . import effects

# Event shapes vary by kind at this JSON boundary, so values cannot be narrowed further
# without changing the runtime validation contract. Every consumed value is checked below.
EventPayload = dict[str, Any]

SCHEMA_VERSION = 1

REQUIRED = ("v", "ts", "event", "actor", "data")

OUTCOME_KIND = "attempt.outcome"
VERIFICATION_OUTCOME_KIND = "verification.outcome"
REVIEW_QUEUE_OPENED_KIND = "review.queue.opened"
CANDIDATE_EXPOSED_KIND = "candidate.exposed"
ATTEMPT_REVIEWED_KIND = "attempt.reviewed"
REVIEW_PRESENTATION_FROZEN_KIND = "review.presentation.frozen"
VERDICT_KIND = "attempt.verdict"
VERDICT_CORRECTION_KIND = "attempt.verdict.correction"
DECISION_KIND = "decision.autonomous"
ACTION_PROPOSAL_KIND = "action.proposal"
REVERSAL_KINDS = frozenset({"revert", "command", "inverse"})
PROTECTED_DECISION_CLASSES = frozenset(
    {
        "money",
        "credential",
        "external_exposure",
        "unrecoverable_state_loss",
        "principal_authority",
        "preference",
    }
)
_AUTONOMOUS_ADMISSION_CLASSES = frozenset(
    {
        "contained_execution",
        "proof_operation",
        "material_choice",
        "recoverable_mutation",
    }
)
_PROTECTED_ADMISSION_CLASSES = frozenset(
    {"protected_covered", "protected_uncovered"}
)
_DECISION_PROTOCOL_MARKERS = frozenset(
    {
        "decision_id",
        "operation_id",
        "ticket",
        "owner",
        "record_level",
        "alternatives",
        "only_admissible",
        "evidence_refs",
        "acceptance_contract_digest",
        "protocol",
        "binding",
        "supersedes",
    }
)
# ADR-0033 section 2: these are the exhaustive classes only the user may decide.
USER_ONLY = frozenset(
    {
        "spend",  # Money leaving an account, or metered spend beyond an authorised cap | Not the harness's money
        "credential",  # A credential, permission or authentication only the user holds | The harness cannot obtain it
        "preference",  # A preferential question no fact settles | No experiment substitutes for a value judgement
        "outside_safety_floor",  # An action outside the safety floor | Reserved by construction
        "beta_verdict",  # The β verdict on an artefact | Human judgement is the ground truth being measured
        "external_exposure",  # Publishing, transmitting or exposing anything beyond the machine | Irreversible and outward-facing
        "gate_or_spec_approval",  # Lifting a gate, or approving a specification | Reserved to the principal
    }
)
BUDGET_STATE_KIND = "budget.state"
USAGE_KIND = "usage.observed"
SPEND_RESERVED_KIND = "spend.reserved"
METERED_PROVIDER = "openrouter"
METERED_CURRENCY = "USD"
BUDGET_STATE_ACTOR = "openrouter-probe"
BUDGET_RESERVATION_ACTOR = "consilient.budget"
USAGE_ACTOR = "consilient.usage"
KNOWLEDGE_RETRIEVED_KIND = "knowledge.retrieved"
KNOWLEDGE_ACTOR = "consilient.knowledge"
KNOWLEDGE_STATUSES = frozenset({"ok", "unavailable", "not_configured"})
VERIFICATION_STATUSES = frozenset(
    {"completed", "error", "timeout", "refused", "not_run"}
)
DISPATCH_STATUSES = frozenset(
    {"ok", "silent", "failed", "timeout", "refused", "killed", "error"}
)
ACQUISITION_CHANNELS = frozenset(
    {
        "artefact_execution",
        "browser_observation",
        "primary_source_retrieval",
        "novel_corpus_observation",
    }
)
_VERIFICATION_ACQUISITION_CHANNELS = frozenset(
    {"artefact_execution", "browser_observation"}
)
_KNOWLEDGE_ACQUISITION_CHANNELS = frozenset(
    {"primary_source_retrieval", "novel_corpus_observation"}
)
ACQUISITION_STANCES = frozenset({"supports", "opposes"})
ACQUISITION_SOURCE_STATUSES = frozenset({"FULL", "ABS"})
BROWSER_RETAINED_EVIDENCE = frozenset(
    {
        "screenshot",
        "accessibility_tree",
        "dom_runtime",
        "console_network",
        "interaction_receipt",
    }
)
RECORD_CAPTURED_KIND = "record.captured"
RECORD_CAPTURED_FIELDS = frozenset(
    {
        "record_id",
        "digest",
        "byte_count",
        "media_type",
        "object_locator",
        "source",
        "consent_purpose",
        "retention_class",
        "valid_time",
        "supersedes",
        "invalidates",
    }
)
RECORD_KIND_ALIASES = frozenset(
    {"record.capture", "record_captured", "records.captured"}
)
CAPABILITY_GAP_KIND = "capability.gap"
GAP_FAILURES = frozenset({"failed", "silent", "refused", "not_implemented"})
GAP_CLOSURES = frozenset({"retry", "escalate"})
INTENT_RECORDED_KIND = "intent.recorded"
INTENT_STARVED_KIND = "intent.starved"
SCHEDULER_ACTOR = "consilient.scheduler"
INTENT_RECORDED_FIELDS = frozenset({"tick", "selected", "not_selected"})
INTENT_STARVED_FIELDS = frozenset({"unit", "reason", "ticks", "since"})
# The four non-selection reasons of the supervision specification, section 2.1, and no
# fifth. A bench recorded under an unnamed reason is the failure the record exists to
# make visible.
INTENT_REASON_PREFIXES = ("blocked_on:", "quota_exhausted:", "breaker_open:")
INTENT_REASONS = frozenset({"no_capacity"})
# "6 ticks or 60 minutes, whichever is longer" - both floors, not either
# [asserted, preferential; supervision specification section 2.1].
STARVATION_TICKS = 6
STARVATION_WINDOW = timedelta(minutes=60)
# The project's evidence tags (AGENTS.md working principle 1). A usage figure that
# cannot name which of these it is has no business being displayed as a number.
PROVENANCE = frozenset({"measured", "cited", "asserted"})
USAGE_STATUSES = frozenset({"ok", "unavailable", "not_configured"})
BUDGET_LOCK = ".budget.lock"
_BUDGET_LOCK_HELD: ContextVar[Path | None] = ContextVar(
    "consilient_budget_lock", default=None
)

# RFC3339 with an explicit offset or Z. A naive timestamp is rejected: replay across machines
# must not depend on the reader's timezone.
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")

# Decisions that only a human principal may author (V0-18). Recording one under an agent
# actor is the failure EXP-16 measured: a fabricated human-participation claim.
HUMAN_ONLY = frozenset(
    {
        "approval",
        "consent",
        "feedback",
        "gate_lift",
        "spend_authorisation",
        "verdict",
    }
)

# ADR-0057: sharing is opt-in and purpose-specific. An existing grant never becomes
# authority for another purpose; commercial training is authorised one use at a time.
CONSENT_GRANTED = "consent.granted"
CONSENT_WITHDRAWN = "consent.withdrawn"
CONSENT_KINDS = frozenset({CONSENT_GRANTED, CONSENT_WITHDRAWN})
CONSENT_PURPOSES = frozenset(
    {"improve-consilient", "train-consilient", "commercial-training"}
)

# feedback-signals.md: the unit of feedback is the task, and the close surface is
# asked of the user, never the agent. Three durable kinds make a skip never re-asked:
# the ask and the decline are recorded, so "have we already asked about this task" is
# a query over the log, not a guess. The asked event carries the goal text verbatim
# from the pre-committed goal record — the surface renders the goal, nothing the
# agent wrote (anti-gaming rule 3).
FEEDBACK_ASKED_KIND = "feedback.asked"
FEEDBACK_DECLINED_KIND = "feedback.declined"
FEEDBACK_ANSWERED_KIND = "feedback.answered"
FEEDBACK_KINDS = frozenset(
    {FEEDBACK_ASKED_KIND, FEEDBACK_DECLINED_KIND, FEEDBACK_ANSWERED_KIND}
)
GOAL_ACHIEVED = frozenset({"fully", "partially", "no"})

# ADR-0076: immutable impact contracts and typed promoter-beta receipts (S01).
IMPACT_CONTRACT_KIND = "promote.impact_contract.registered"
PROMOTER_BETA_RECEIPT_KIND = "promote.promoter_beta.receipt"
ACTIVATION_REFUSED_KIND = "promote.activation.refused"
PROMOTE_CONTRACT_KINDS = frozenset(
    {IMPACT_CONTRACT_KIND, PROMOTER_BETA_RECEIPT_KIND, ACTIVATION_REFUSED_KIND}
)
CANONICAL_ON_OTHER = "no activation"
PROMOTE_ACTOR = "consilient.promote"
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

# feedback-signals.md rules 1–2: no approval-style signal is ever a training target,
# and none is collected at all — response rating is not built. The prohibition lives
# here in the schema, not in prose: validate() rejects these field names on any event.
RESPONSE_RATING_FIELDS = frozenset(
    {
        "rating",
        "response_rating",
        "thumbs",
        "thumbs_up",
        "thumbs_down",
        "satisfaction",
        "helpful",
        "unhelpful",
        "stars",
        "star_rating",
    }
)

# feedback-signals.md: achievement (asked) and efficiency (derived) are separate
# records, permanently. No default composite score exists anywhere, so the answered
# event refuses the fields that would build one — efficiency stays on
# dispatch.outcome, where it is measured, and any composite is an explicit user
# weighting, which is a preferential question the harness must not default.
FEEDBACK_COMPOSITE_FIELDS = frozenset(
    {"score", "composite", "overall", "efficiency", "cost", "duration_s"}
)

# ADR-0035: four levels, milestones by default; the dial changes what is displayed,
# never what is recorded. The change event exists so β can be stratified by the
# conditions the verdict was produced under — which is the only measurement that
# justifies the dial. The floor and its config-load validation are the CLI's half.
VISIBILITY_LEVELS = ("silent", "milestones", "decisions", "firehose")
VISIBILITY_DEFAULT = "milestones"
VISIBILITY_CHANGE_KIND = "visibility.change"

DELIVERY_ESTIMATE_KIND = "delivery.estimate"
MEASUREMENT_REGISTERED_KIND = "measurement.registered"
MEASUREMENT_RESULT_KIND = "measurement.result"
MEASUREMENT_ACTOR = "consilient.measurement"
DELIVERY_ACTOR = "consilient.delivery"
DELIVERY_OUTCOME_KINDS = frozenset(
    {"delivery.outcome", "dispatch.outcome", OUTCOME_KIND}
)
ESTIMATE_CAUSES = frozenset(
    {
        "scope_change",
        "route_change",
        "checkpoint_miss",
        "dependency_failure",
        "estimate_error",
    }
)
_ESTIMATE_REQUIRED_FIELDS = frozenset(
    {
        "delivery_id",
        "commitment_id",
        "commitment_digest",
        "plan_digest",
        "estimate_id",
        "revision",
        "predecessor_estimate_id",
        "original_estimate_id",
        "earliest_at",
        "latest_at",
        "issued_at",
        "evidence_class",
        "analogue_ids",
        "sample_size",
        "method",
        "stream_bounds",
        "resource_snapshot_digest",
        "checkpoint_interval_s",
        "recovery_allowance_s",
        "not_included",
        "cohort_key",
        "estimate_digest",
        "cause",
        "notice_preceded_upper_bound",
    }
)


class EventError(ValueError):
    """An event was rejected before it reached the log."""


@dataclass(frozen=True)
class Rejection:
    """A line the reader refused, kept so refusal is reported rather than fatal.

    The log is append-only, so a line that should never have been written cannot be
    removed. If the reader raises on it, one bad append destroys the readability of the
    whole record — the instrument's failure mode becomes "stop working" instead of "report
    the problem", and every downstream number disappears with it.

    This project had already worked that out and then walked into it anyway.
    `test_reading_a_historical_log_does_not_depend_on_when_it_is_read` says in as many
    words that if `validate` enforced clock skew "every log would become unreadable as it
    aged". The reasoning was applied to one rule and never generalised into a property of
    the reader, so when V0-18 was tightened at 03:52 on 20 August 2026 and three events
    were appended at 09:41-09:56 that it forbids, `replay` and `beta` both died on the
    real trajectory. [measured]

    A rejection is never silently dropped: it is excluded from the projection AND carried
    back to the caller, and every CLI command reports the count.
    """

    path: str
    line: int
    reason: str
    content_digest: str = ""


@dataclass(frozen=True)
class Event:
    raw: EventPayload
    path: str | None = None
    line: int | None = None

    @property
    def kind(self) -> str:
        return cast(str, self.raw["event"])

    @property
    def actor(self) -> str:
        return cast(str, self.raw["actor"])

    @property
    def data(self) -> EventPayload:
        return cast(EventPayload, self.raw["data"])


# A transition validator is pure: it receives the accepted prefix and the
# rejections exactly as they stand under the per-log lock, plus the validated
# candidates, and refuses by raising EventError. It performs no I/O of its own.
TransitionValidator = Callable[
    [tuple[Event, ...], tuple[Rejection, ...], tuple[EventPayload, ...]], None
]


def validate(event: object) -> EventPayload:
    """Reject anything that must never reach the log. Returns the event unchanged."""
    if not isinstance(event, dict):
        raise EventError("event must be an object")

    missing = [k for k in REQUIRED if k not in event]
    if missing:
        raise EventError(f"missing required field(s): {', '.join(missing)}")

    if event["v"] != SCHEMA_VERSION:
        raise EventError(
            f"unsupported schema version {event['v']!r}; this build writes v{SCHEMA_VERSION}"
        )

    if not isinstance(event["ts"], str) or not TS.match(event["ts"]):
        raise EventError(
            f"ts must be RFC3339 with an explicit offset, got {event['ts']!r}"
        )
    try:
        stamped = datetime.fromisoformat(event["ts"])
    except ValueError as exc:
        raise EventError(f"ts is not a valid calendar timestamp: {event['ts']!r}") from exc
    if stamped.tzinfo is None or stamped.utcoffset() is None:
        raise EventError(f"ts must carry an explicit offset, got {event['ts']!r}")
    try:
        stamped.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise EventError(f"ts cannot be normalised to UTC: {event['ts']!r}") from exc

    for field in ("event", "actor"):
        if not isinstance(event[field], str) or not event[field].strip():
            raise EventError(f"{field} must be a non-empty string")

    if not isinstance(event["data"], dict):
        raise EventError("data must be an object")

    if "event_id" in event:
        _check_event_id(event["event_id"])

    _check_record_contract(event)
    _check_budget_contract(event)
    _check_usage_contract(event)
    _check_knowledge_contract(event)
    _check_acquisition_contract(event)
    _check_capability_gap_contract(event)
    _check_intent_contract(event)
    _check_attempt_identity(event)
    _check_attempt_contract(event)
    _check_verification_outcome_contract(event)
    _check_review_queue_contract(event)
    _check_consent_contract(event)
    _check_decision_contract(event)
    _check_response_rating_ban(event)
    _check_feedback_contract(event)
    _check_visibility_contract(event)
    _check_human_authority(event)
    _check_evidence_class(event)
    _check_dispatch_contract(event)
    _check_delivery_estimate_contract(event)
    _check_measurement_contract(event)
    try:
        effects.validate_effect_event(event)
    except effects.EffectError as exc:
        raise EventError(str(exc)) from exc
    if event["event"].startswith(("conversation.", "work_item.", "organisation.")):
        from . import work_items

        work_items.check_event_contract(event)
    _check_promote_contract(event)
    return event


def _check_uuid4(value: object, field: str) -> None:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", value)
        is None
    ):
        raise EventError(f"{field} must be lower-case hyphenated UUIDv4 text")


def _check_event_id(value: object) -> None:
    """Accept one spelling of UUIDv4, so IDs cannot gain aliases in replay."""
    _check_uuid4(value, "event_id")


def new_event_id() -> str:
    """Return the one canonical identity spelling accepted by the trajectory."""
    raw = bytearray(os.urandom(16))
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    text = raw.hex()
    return f"{text[:8]}-{text[8:12]}-{text[12:16]}-{text[16:20]}-{text[20:]}"


def _prepare_for_append(event: EventPayload) -> EventPayload:
    """Attach one retry-stable identity before validating or attempting durability."""
    if "event_id" not in event:
        event["event_id"] = new_event_id()
    return validate(event)


def _check_record_contract(event: EventPayload) -> None:
    """M01: one exact, private, content-addressed capture event contract."""
    kind = event["event"]
    if kind != RECORD_CAPTURED_KIND:
        if kind in RECORD_KIND_ALIASES or kind.startswith("record."):
            raise EventError(
                f"record event kind must be {RECORD_CAPTURED_KIND!r}; aliases are not accepted"
            )
        return

    data = event["data"]
    actual = set(data)
    if actual != RECORD_CAPTURED_FIELDS:
        missing = sorted(RECORD_CAPTURED_FIELDS - actual)
        unexpected = sorted(actual - RECORD_CAPTURED_FIELDS)
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if unexpected:
            detail.append(f"unexpected {unexpected}")
        raise EventError(
            f"{RECORD_CAPTURED_KIND} body fields are fixed: {'; '.join(detail)}"
        )

    _check_uuid4(data["record_id"], "record.captured record_id")
    digest = data["digest"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} digest must be 64 lower-case hex characters"
        )
    byte_count = data["byte_count"]
    if (
        not isinstance(byte_count, int)
        or isinstance(byte_count, bool)
        or byte_count < 0
    ):
        raise EventError(f"{RECORD_CAPTURED_KIND} byte_count must be a non-negative integer")

    media_type = data["media_type"]
    if (
        not isinstance(media_type, str)
        or re.fullmatch(r"[^\s/]+/[^\s/]+", media_type) is None
    ):
        raise EventError(
            f"{RECORD_CAPTURED_KIND} media_type must be one canonical type/subtype string"
        )

    locator = data["object_locator"]
    expected_locator = (
        f".harness/objects/sha256/{digest[:2]}/{digest[2:]}"
    )
    if locator != expected_locator:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} object_locator must be the canonical repository-relative "
            f"SHA-256 locator {expected_locator!r}"
        )

    source = data["source"]
    if (
        not isinstance(source, str)
        or not source
        or source != source.strip()
        or source.startswith("/")
        or re.match(r"^[A-Za-z]:", source)
        or "\\" in source
        or any(part in {"", ".", ".."} for part in source.split("/"))
    ):
        raise EventError(
            f"{RECORD_CAPTURED_KIND} source must be one canonical repository-relative path"
        )

    for field in ("consent_purpose", "retention_class"):
        value = data[field]
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise EventError(
                f"{RECORD_CAPTURED_KIND} must carry canonical non-empty {field} metadata"
            )

    valid_time = data["valid_time"]
    if not isinstance(valid_time, dict) or set(valid_time) != {"from", "to"}:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} valid_time must contain exactly 'from' and 'to'"
        )
    valid_from = _record_timestamp(valid_time["from"], "valid_time.from")
    valid_to_raw = valid_time["to"]
    if valid_to_raw is not None:
        valid_to = _record_timestamp(valid_to_raw, "valid_time.to")
        if valid_to < valid_from:
            raise EventError(
                f"{RECORD_CAPTURED_KIND} valid_time.to cannot precede valid_time.from"
            )

    for relation in ("supersedes", "invalidates"):
        references = data[relation]
        if not isinstance(references, list):
            raise EventError(f"{RECORD_CAPTURED_KIND} {relation} must be a list")
        for reference in references:
            _check_record_reference(reference, relation)


def _record_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str) or TS.fullmatch(value) is None:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} {field} must be RFC3339 with an explicit offset"
        )
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} {field} cannot be normalised to UTC"
        ) from exc


def _check_record_reference(reference: object, relation: str) -> None:
    fields = {"event_id", "event_kind", "event_sha256"}
    if not isinstance(reference, dict) or set(reference) != fields:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} {relation} entries must be exact F03 event references"
        )
    _check_event_id(reference["event_id"])
    if reference["event_kind"] != RECORD_CAPTURED_KIND:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} {relation} may reference only record.captured events"
        )
    digest = reference["event_sha256"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise EventError(
            f"{RECORD_CAPTURED_KIND} {relation} event_sha256 must be 64 lower-case hex characters"
        )


def _decimal_field(
    kind: str, data: EventPayload, field: str, *, positive: bool
) -> None:
    value = data.get(field)
    if not isinstance(value, str):
        qualifier = "positive" if positive else "non-negative"
        raise EventError(f"{kind} must carry {field} as a finite {qualifier} Decimal string")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise EventError(f"{kind} carries invalid {field} {value!r}") from exc
    if not amount.is_finite():
        qualifier = "positive" if positive else "non-negative"
        raise EventError(f"{kind} must carry {field} as a finite {qualifier} Decimal string")
    valid_sign = amount > 0 if positive else amount >= 0
    if not valid_sign:
        qualifier = "positive" if positive else "non-negative"
        raise EventError(f"{kind} must carry {field} as a finite {qualifier} Decimal string")


def _check_budget_contract(event: EventPayload) -> None:
    """Budget state and reservations are valid before they reach the trajectory."""
    kind = event["event"]
    if kind not in (BUDGET_STATE_KIND, SPEND_RESERVED_KIND):
        return
    data = event["data"]
    if data.get("provider") != METERED_PROVIDER:
        raise EventError(f"{kind} must carry provider {METERED_PROVIDER!r}")
    if data.get("currency") != METERED_CURRENCY:
        raise EventError(f"{kind} must carry currency {METERED_CURRENCY!r}")

    if kind == BUDGET_STATE_KIND:
        if event["actor"] != BUDGET_STATE_ACTOR:
            raise EventError(
                f"{kind} must be attributed to declared writer {BUDGET_STATE_ACTOR!r}"
            )
        if datetime.fromisoformat(event["ts"]).utcoffset() != timedelta(0):
            raise EventError(f"{kind} ts must use UTC so trajectory order is unambiguous")
        _decimal_field(kind, data, "weekly_spent", positive=False)
        _decimal_field(kind, data, "monthly_spent", positive=False)
        observed_at = data.get("observed_at")
        if not isinstance(observed_at, str) or not TS.match(observed_at):
            raise EventError(
                f"{kind} must carry observed_at as RFC3339 with an explicit offset"
            )
        try:
            observed = datetime.fromisoformat(observed_at)
        except ValueError as exc:
            raise EventError(f"{kind} carries an invalid observed_at") from exc
        if observed.tzinfo is None or observed.utcoffset() is None:
            raise EventError(f"{kind} observed_at must carry an explicit offset")
        try:
            observed.astimezone(timezone.utc)
        except (OverflowError, ValueError) as exc:
            raise EventError(f"{kind} observed_at cannot be normalised to UTC") from exc
        digest = data.get("rejection_digest")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise EventError(
                f"{kind} must carry rejection_digest as a lowercase SHA-256 digest"
            )
        return

    if event["actor"] != BUDGET_RESERVATION_ACTOR:
        raise EventError(
            f"{kind} must be attributed to declared writer {BUDGET_RESERVATION_ACTOR!r}"
        )
    if datetime.fromisoformat(event["ts"]).utcoffset() != timedelta(0):
        raise EventError(f"{kind} ts must use UTC so trajectory order is unambiguous")
    state_observed_at = data.get("state_observed_at")
    if not isinstance(state_observed_at, str) or not TS.match(state_observed_at):
        raise EventError(
            f"{kind} must carry state_observed_at as RFC3339 with an explicit offset"
        )
    try:
        state_observed = datetime.fromisoformat(state_observed_at)
    except ValueError as exc:
        raise EventError(f"{kind} carries an invalid state_observed_at") from exc
    if state_observed.tzinfo is None or state_observed.utcoffset() is None:
        raise EventError(f"{kind} state_observed_at must carry an explicit offset")
    try:
        state_observed.astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise EventError(f"{kind} state_observed_at cannot be normalised to UTC") from exc
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        raise EventError(f"{kind} must carry a non-empty string run_id")
    _decimal_field(kind, data, "amount", positive=True)


def _check_usage_contract(event: EventPayload) -> None:
    """V0-30: a usage figure names its provenance, and no figure is invented.

    This is the failure this event kind exists to make impossible. A dashboard that shows
    "0%" for a provider it could not read is worse than one that shows nothing: it reports
    headroom that was never observed, and the reader cannot tell the two apart. It is the
    same shape as the 20 August 2026 OpenRouter reading, where the key-status counter read
    $0 immediately and $0.045138255 once billing settled -- the zero was real as a *counter
    value* and false as a *statement about spend*. [measured]

    So the rule is structural rather than advisory: a provider whose status is not `ok`
    may carry no figures at all, and every figure that does exist names which of the
    project's evidence tags it was obtained under. There is no code path that writes a
    number without one.

    Subscription quota and metered spend are kept apart on purpose (ADR-0044, and
    `backends.md` "Resource windows remain provider-native"). A quota has a window and a
    reset and no currency; spend has a currency and no window. Collapsing them into one
    "usage" number would lose the reset time, which is the field a human actually needs.
    """
    if event["event"] != USAGE_KIND:
        return
    if event["actor"] != USAGE_ACTOR:
        raise EventError(
            f"{USAGE_KIND} must be attributed to declared writer {USAGE_ACTOR!r}"
        )
    if datetime.fromisoformat(event["ts"]).utcoffset() != timedelta(0):
        raise EventError(f"{USAGE_KIND} ts must use UTC so trajectory order is unambiguous")

    data = event["data"]
    for field in ("provider", "detail"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EventError(f"{USAGE_KIND} must carry a non-empty string {field}")
    status = data.get("status")
    if status not in USAGE_STATUSES:
        raise EventError(
            f"{USAGE_KIND} status must be one of {sorted(USAGE_STATUSES)}, got {status!r}"
        )
    if data.get("kind") not in ("subscription", "metered"):
        raise EventError(
            f"{USAGE_KIND} must declare kind 'subscription' or 'metered'; a flat-fee "
            "window and a metered charge are not the same measurement"
        )
    quotas = data.get("quotas", [])
    spend = data.get("spend", [])
    if not isinstance(quotas, list) or not isinstance(spend, list):
        raise EventError(f"{USAGE_KIND} quotas and spend must be lists")

    if status != "ok":
        if quotas or spend:
            raise EventError(
                f"{USAGE_KIND} for {data['provider']!r} reports status {status!r} but "
                "carries a figure; a provider that could not be read reports no number "
                "(V0-30)"
            )
        return
    if not quotas and not spend:
        raise EventError(
            f"{USAGE_KIND} for {data['provider']!r} reports status 'ok' with no figure; "
            "say 'unavailable' rather than reporting an empty success (V0-30)"
        )

    for quota in quotas:
        if not isinstance(quota, dict):
            raise EventError(f"{USAGE_KIND} quota must be an object")
        window = quota.get("window")
        if not isinstance(window, str) or not window.strip():
            raise EventError(
                f"{USAGE_KIND} quota must name its provider-native window; a five-hour "
                "and a seven-day bucket are not one generic reset"
            )
        _decimal_field(f"{USAGE_KIND} quota", quota, "used_fraction", positive=False)
        if Decimal(quota["used_fraction"]) > 1:
            raise EventError(f"{USAGE_KIND} quota used_fraction must lie in [0, 1]")
        _check_reset(quota.get("resets_at"))
        _check_provenance(quota.get("provenance"), "quota")

    for item in spend:
        if not isinstance(item, dict):
            raise EventError(f"{USAGE_KIND} spend must be an object")
        _decimal_field(f"{USAGE_KIND} spend", item, "amount", positive=False)
        currency = item.get("currency")
        if not isinstance(currency, str) or not currency.strip():
            raise EventError(
                f"{USAGE_KIND} spend must name its currency; a metered figure without one "
                "cannot be compared with a ceiling"
            )
        if item.get("period") not in ("weekly", "monthly"):
            raise EventError(f"{USAGE_KIND} spend period must be 'weekly' or 'monthly'")
        _check_provenance(item.get("provenance"), "spend")


def _check_reset(value: object) -> None:
    """A window that has lost its reset time is not a window."""
    if value is None:
        return
    if not isinstance(value, str) or not TS.match(value):
        raise EventError(
            f"{USAGE_KIND} resets_at must be RFC3339 with an explicit offset, or absent"
        )
    try:
        datetime.fromisoformat(value).astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise EventError(f"{USAGE_KIND} resets_at cannot be normalised to UTC") from exc


def _check_provenance(value: object, where: str) -> None:
    if value not in PROVENANCE:
        raise EventError(
            f"{USAGE_KIND} {where} must tag its provenance with one of "
            f"{sorted(PROVENANCE)}, got {value!r}; an untagged number is presented as "
            "authoritative and this project does not have one to present (V0-30)"
        )


def _check_knowledge_contract(event: EventPayload) -> None:
    """V0-31: every retrieval carries source, licence and date; failures stay empty."""
    if event["event"] != KNOWLEDGE_RETRIEVED_KIND:
        return
    if event["actor"] != KNOWLEDGE_ACTOR:
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} must be attributed to {KNOWLEDGE_ACTOR!r}"
        )
    data = event["data"]
    for field in ("source_id", "source_url", "licence", "category", "retrieved_at", "status"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EventError(f"{KNOWLEDGE_RETRIEVED_KIND} must carry a non-empty string {field}")
    status = data["status"]
    if status not in KNOWLEDGE_STATUSES:
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} status must be one of {sorted(KNOWLEDGE_STATUSES)}, "
            f"got {status!r}"
        )
    retrieved_at = data["retrieved_at"]
    if not TS.match(retrieved_at):
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} retrieved_at must be RFC3339 with an explicit offset"
        )
    if status == "ok":
        if not isinstance(data.get("uri"), str) or not data["uri"].strip():
            raise EventError(f"{KNOWLEDGE_RETRIEVED_KIND} with status 'ok' must carry uri")
        digest = data.get("content_digest")
        if not isinstance(digest, str) or len(digest) != 64:
            raise EventError(
                f"{KNOWLEDGE_RETRIEVED_KIND} with status 'ok' must carry a 64-char "
                "content_digest"
            )
        if data.get("reason"):
            raise EventError(
                f"{KNOWLEDGE_RETRIEVED_KIND} with status 'ok' must not carry a failure reason"
            )
        return
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} with status {status!r} must carry a non-empty reason"
        )
    if data.get("content_digest"):
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} with status {status!r} must not carry content_digest"
        )


def _canonical_token(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise EventError(f"{field} must be canonical printable text")
    if not value.isprintable():
        raise EventError(f"{field} must be canonical printable text")
    return value


def _hex64(value: object, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise EventError(f"{field} must be 64 lowercase hex characters")
    return value


def _check_derivation_roots(value: object) -> None:
    if value == "unknown":
        return
    if (
        not isinstance(value, list)
        or not value
        or any(
            not isinstance(item, str) or not item.strip() or item != item.strip()
            for item in value
        )
    ):
        raise EventError(
            "acquisition.derivation_roots must be 'unknown' or a non-empty list "
            "of canonical strings"
        )


def _check_acquisition_contract(event: EventPayload) -> None:
    """ADR-0081: source-kind events may carry one validated acquisition channel."""
    kind = event["event"]
    if kind not in {VERIFICATION_OUTCOME_KIND, KNOWLEDGE_RETRIEVED_KIND}:
        return
    data = event["data"]
    if "acquisition" not in data:
        return
    acquisition = data["acquisition"]
    if not isinstance(acquisition, dict):
        raise EventError("acquisition must be an object")
    channel = acquisition.get("channel")
    if channel not in ACQUISITION_CHANNELS:
        raise EventError(
            "acquisition.channel must be one of "
            f"{sorted(ACQUISITION_CHANNELS)}, got {channel!r}"
        )
    if kind == VERIFICATION_OUTCOME_KIND and channel not in _VERIFICATION_ACQUISITION_CHANNELS:
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} cannot carry acquisition.channel {channel!r}"
        )
    if kind == KNOWLEDGE_RETRIEVED_KIND and channel not in _KNOWLEDGE_ACQUISITION_CHANNELS:
        raise EventError(
            f"{KNOWLEDGE_RETRIEVED_KIND} cannot carry acquisition.channel {channel!r}"
        )

    common = {
        "channel",
        "observation_anchor",
        "derivation_roots",
        "conclusion_id",
        "alternative",
        "acceptance_contract_digest",
    }
    if channel == "artefact_execution":
        expected = common | {"environment"}
    elif channel == "browser_observation":
        expected = common | {
            "browser",
            "browser_version",
            "retained_evidence",
            "retained_evidence_digest",
        }
    elif channel == "primary_source_retrieval":
        expected = common | {
            "proposition_id",
            "stance",
            "locator",
            "verification_status",
        }
    else:
        expected = common | {
            "proposition_id",
            "stance",
            "locator",
            "corpus_manifest_digest",
            "provenance",
            "selection_rule",
            "assembled_context_digest",
        }
    actual = set(acquisition)
    if actual != expected:
        raise EventError(
            f"acquisition fields for {channel} mismatch; "
            f"missing {sorted(expected - actual)}, unexpected {sorted(actual - expected)}"
        )

    _canonical_token(acquisition["observation_anchor"], "acquisition.observation_anchor")
    _canonical_token(acquisition["conclusion_id"], "acquisition.conclusion_id")
    _canonical_token(acquisition["alternative"], "acquisition.alternative")
    _hex64(
        acquisition["acceptance_contract_digest"],
        "acquisition.acceptance_contract_digest",
    )
    _check_derivation_roots(acquisition["derivation_roots"])

    if channel == "artefact_execution":
        _canonical_token(acquisition["environment"], "acquisition.environment")
        return
    if channel == "browser_observation":
        _canonical_token(acquisition["browser"], "acquisition.browser")
        _canonical_token(acquisition["browser_version"], "acquisition.browser_version")
        retained = acquisition["retained_evidence"]
        if retained not in BROWSER_RETAINED_EVIDENCE:
            raise EventError(
                "acquisition.retained_evidence must be one of "
                f"{sorted(BROWSER_RETAINED_EVIDENCE)}, got {retained!r}"
            )
        _hex64(
            acquisition["retained_evidence_digest"],
            "acquisition.retained_evidence_digest",
        )
        return

    _canonical_token(acquisition["proposition_id"], "acquisition.proposition_id")
    stance = acquisition["stance"]
    if stance not in ACQUISITION_STANCES:
        raise EventError(
            "acquisition.stance must be one of "
            f"{sorted(ACQUISITION_STANCES)}, got {stance!r}"
        )
    _canonical_token(acquisition["locator"], "acquisition.locator")
    if channel == "primary_source_retrieval":
        status = acquisition["verification_status"]
        if status not in ACQUISITION_SOURCE_STATUSES:
            raise EventError(
                "acquisition.verification_status must be one of "
                f"{sorted(ACQUISITION_SOURCE_STATUSES)}, got {status!r}"
            )
        return
    _hex64(
        acquisition["corpus_manifest_digest"],
        "acquisition.corpus_manifest_digest",
    )
    _canonical_token(acquisition["provenance"], "acquisition.provenance")
    _canonical_token(acquisition["selection_rule"], "acquisition.selection_rule")
    _hex64(
        acquisition["assembled_context_digest"],
        "acquisition.assembled_context_digest",
    )


def _check_capability_gap_contract(event: EventPayload) -> None:
    """V0-41: a capability gap is a first-class record, not a conversation that vanished."""
    if event["event"] != CAPABILITY_GAP_KIND:
        return
    data = event["data"]
    for field in ("asked", "attempted", "detail", "repair", "run_id", "source"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EventError(f"{CAPABILITY_GAP_KIND} must carry a non-empty string {field}")
    failure = data.get("failure")
    if failure not in GAP_FAILURES:
        raise EventError(
            f"{CAPABILITY_GAP_KIND} failure must be one of {sorted(GAP_FAILURES)}, "
            f"got {failure!r}"
        )
    closure = data.get("closure")
    if closure not in GAP_CLOSURES:
        raise EventError(
            f"{CAPABILITY_GAP_KIND} closure must be one of {sorted(GAP_CLOSURES)}, "
            f"got {closure!r}"
        )
    if failure in {"silent", "not_implemented"} and closure == "retry":
        raise EventError(
            f"{CAPABILITY_GAP_KIND} with failure {failure!r} must escalate, not retry"
        )


def _intent_timestamp(value: object, where: str) -> datetime:
    if not isinstance(value, str) or TS.fullmatch(value) is None:
        raise EventError(f"{where} must be RFC3339 with an explicit offset")
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def _check_intent_reason(value: object, where: str) -> None:
    if not isinstance(value, str) or value != value.strip() or not value:
        raise EventError(f"{where} reason must be a non-empty unpadded string")
    if value in INTENT_REASONS:
        return
    for prefix in INTENT_REASON_PREFIXES:
        if value.startswith(prefix) and value[len(prefix) :].strip():
            return
    raise EventError(
        f"{where} reason must be one of {sorted(INTENT_REASONS)} or "
        f"{list(INTENT_REASON_PREFIXES)} with a named subject, got {value!r}"
    )


def _check_intent_contract(event: EventPayload) -> None:
    """The scheduler's own record: what was ready, what ran, and why the rest did not.

    Every other supervision mechanism counts failures. F-08 produced no dispatch, no
    lease and no call, so it was invisible to all of them for two days [measured,
    `docs/00-context/orchestration-failure-modes-2026-08-23.md`]. Non-selection is only
    countable if the reason is written down at the tick, under a fixed vocabulary.
    """
    kind = event["event"]
    if kind not in (INTENT_RECORDED_KIND, INTENT_STARVED_KIND):
        return
    data = event["data"]
    expected = (
        INTENT_RECORDED_FIELDS
        if kind == INTENT_RECORDED_KIND
        else INTENT_STARVED_FIELDS
    )
    unexpected = sorted(set(data) - expected)
    if unexpected:
        raise EventError(f"{kind} carries unexpected field(s) {unexpected}")
    missing = sorted(expected - set(data))
    if missing:
        raise EventError(f"{kind} must carry {missing}")

    if kind == INTENT_STARVED_KIND:
        for field in ("unit", "since"):
            value = data[field]
            if not isinstance(value, str) or not value.strip():
                raise EventError(f"{kind} must carry a non-empty string {field}")
        _intent_timestamp(data["since"], f"{kind} since")
        _check_intent_reason(data["reason"], kind)
        ticks = data["ticks"]
        if not isinstance(ticks, int) or isinstance(ticks, bool):
            raise EventError(f"{kind} ticks must be an integer")
        if ticks < STARVATION_TICKS:
            raise EventError(
                f"{kind} claims a threshold that was not crossed: ticks {ticks} "
                f"is below {STARVATION_TICKS}"
            )
        return

    tick = data["tick"]
    if not isinstance(tick, int) or isinstance(tick, bool) or tick < 0:
        raise EventError(f"{kind} tick must be a non-negative integer")
    selected = data["selected"]
    if not isinstance(selected, list) or any(
        not isinstance(unit, str) or not unit.strip() for unit in selected
    ):
        raise EventError(f"{kind} selected must be a list of unit names")
    not_selected = data["not_selected"]
    if not isinstance(not_selected, dict):
        raise EventError(f"{kind} not_selected must be an object of unit to reason")
    for unit, reason in not_selected.items():
        if not isinstance(unit, str) or not unit.strip():
            raise EventError(f"{kind} not_selected must be keyed by unit name")
        _check_intent_reason(reason, f"{kind} {unit}")
    both = sorted(set(selected) & set(not_selected))
    if both:
        raise EventError(
            f"{kind} unit(s) {both} cannot be both selected and not selected"
        )


def _intent_runs(
    prefix: Sequence[Event],
) -> dict[str, tuple[str, datetime, datetime, int]]:
    """Per unit, the reason it is currently not being selected and how long that has run.

    Returns unit -> (reason, first_ts, last_ts, ticks). A unit that was selected, or that
    stopped being ready, or whose reason changed, starts a new run: only an unbroken
    repetition of one reason is starvation.
    """
    runs: dict[str, tuple[str, datetime, datetime, int]] = {}
    last_tick: int | None = None
    for event in prefix:
        if event.kind != INTENT_RECORDED_KIND:
            continue
        tick = cast(int, event.data["tick"])
        if last_tick is not None and tick <= last_tick:
            # A replayed or out-of-order tick is not a further tick of waiting.
            continue
        last_tick = tick
        ts = _intent_timestamp(event.raw["ts"], f"{INTENT_RECORDED_KIND} ts")
        not_selected = cast(Mapping[str, str], event.data["not_selected"])
        for unit in set(runs) - set(not_selected):
            del runs[unit]
        for unit, reason in not_selected.items():
            run = runs.get(unit)
            if run is None or run[0] != reason:
                runs[unit] = (reason, ts, ts, 1)
            else:
                runs[unit] = (reason, run[1], ts, run[3] + 1)
    return runs


def starvation(
    prefix: Sequence[Event],
    *,
    ticks: int = STARVATION_TICKS,
    window: timedelta = STARVATION_WINDOW,
) -> list[EventPayload]:
    """The units starved as of the end of `prefix`, each reported once per run.

    Both floors must be crossed - "6 ticks or 60 minutes, whichever is longer". Six ticks
    inside a minute is a busy scheduler, not a starved unit.
    """
    reported = {
        (event.data["unit"], event.data["reason"], event.data["since"])
        for event in prefix
        if event.kind == INTENT_STARVED_KIND
    }
    starved: list[EventPayload] = []
    for unit, (reason, first_ts, last_ts, count) in sorted(
        _intent_runs(prefix).items()
    ):
        if count < ticks or last_ts - first_ts < window:
            continue
        since = first_ts.isoformat()
        if (unit, reason, since) in reported:
            continue
        starved.append({"unit": unit, "reason": reason, "ticks": count, "since": since})
    return starved


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


def _check_evidence_class(event: EventPayload) -> None:
    """V0-26: multi-contributor events must declare a distinct evidence_class per contributor.

    ADR-0010 and CONSILIENCE.md clause 2: agreement between agents that share evidence
    is echo, not consilience. A multi-contributor event must name a different class of
    facts per contributor (Ao, Gao & Simchi-Levi 2026, arXiv:2603.26993).
    """
    data = event.get("data")
    if not isinstance(data, dict):
        return
    contributors = data.get("contributors")
    if contributors is None and "contributors" in event:
        contributors = event.get("contributors")
    if contributors is None:
        return

    if not isinstance(contributors, list):
        raise EventError("contributors must be a list")

    if len(contributors) <= 1:
        return

    seen_classes: set[str] = set()
    for contributor in contributors:
        if not isinstance(contributor, dict):
            raise EventError("contributor must be an object")
        ec = contributor.get("evidence_class")
        if not isinstance(ec, str) or not ec.strip():
            identity = (
                contributor.get("logical_identity")
                or contributor.get("runtime_identity")
                or "contributor"
            )
            raise EventError(
                f"multi-contributor event requires a non-empty evidence_class for {identity!r} (V0-26)"
            )
        normalized = ec.strip().casefold()
        if normalized in seen_classes:
            raise EventError(
                f"multi-contributor event must name distinct evidence classes; duplicate "
                f"evidence_class {ec.strip()!r} (V0-26)"
            )
        seen_classes.add(normalized)


def _check_dispatch_contract(event: EventPayload) -> None:
    """ADR-0039: every dispatch records whether it was supervised."""
    if event["event"].startswith("dispatch.") and not isinstance(
        event["data"].get("supervised"), bool
    ):
        raise EventError("dispatch events must record supervised as a boolean (ADR-0039)")
    status = event["data"].get("status")
    if event["event"] in ("dispatch.outcome", "dispatch.refused") and status is not None and (
        not isinstance(status, str) or status not in DISPATCH_STATUSES
    ):
        raise EventError(f"unknown dispatch status {status!r}")


def _check_measurement_contract(event: EventPayload) -> None:
    """BU1: pre-run registration and result rows join on run_id at replay."""
    kind = event["event"]
    if kind not in (MEASUREMENT_REGISTERED_KIND, MEASUREMENT_RESULT_KIND):
        return
    if event["actor"] != MEASUREMENT_ACTOR:
        raise EventError(
            f"{kind} must be attributed to declared writer {MEASUREMENT_ACTOR!r}"
        )
    data = event["data"]
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        raise EventError(f"{kind} must carry a non-empty string run_id")
    if kind == MEASUREMENT_REGISTERED_KIND:
        config_hash = data.get("config_hash")
        if not isinstance(config_hash, str) or DIGEST_RE.fullmatch(config_hash) is None:
            raise EventError(
                f"{MEASUREMENT_REGISTERED_KIND} config_hash must be 64 lower-case hex characters"
            )
        hardware_id = data.get("hardware_id")
        if not isinstance(hardware_id, str) or not hardware_id.strip():
            raise EventError(
                f"{MEASUREMENT_REGISTERED_KIND} must carry a non-empty string hardware_id"
            )
        return
    fixture = data.get("fixture")
    if not isinstance(fixture, str) or not fixture.strip():
        raise EventError(f"{MEASUREMENT_RESULT_KIND} must carry a non-empty string fixture")


def _check_promote_contract(event: EventPayload) -> None:
    """ADR-0076: registered impact contracts and promoter-beta receipts are typed."""
    kind = event["event"]
    if kind not in PROMOTE_CONTRACT_KINDS:
        return
    if event["actor"] != PROMOTE_ACTOR:
        raise EventError(
            f"{kind} must be attributed to declared writer {PROMOTE_ACTOR!r}"
        )
    data = event["data"]
    if kind == IMPACT_CONTRACT_KIND:
        experiment_id = data.get("experiment_id")
        if not isinstance(experiment_id, str) or not experiment_id.strip():
            raise EventError(f"{kind} must carry a non-empty experiment_id")
        digest_value = data.get("registration_digest")
        if not isinstance(digest_value, str) or DIGEST_RE.fullmatch(digest_value) is None:
            raise EventError(
                f"{kind} must carry registration_digest as a lowercase SHA-256 digest"
            )
        contract = data.get("contract")
        if not isinstance(contract, dict):
            raise EventError(f"{kind} must carry contract as an object")
        on_other = contract.get("on_other")
        if not isinstance(on_other, str) or on_other.strip().casefold() != CANONICAL_ON_OTHER:
            raise EventError(
                f"{kind} contract.on_other cannot be weakened; must be {CANONICAL_ON_OTHER!r}"
            )
        return
    if kind == PROMOTER_BETA_RECEIPT_KIND:
        if data.get("receipt_kind") != "promoter_beta":
            raise EventError(f"{kind} must carry receipt_kind promoter_beta")
        n_rejected = data.get("n_human_rejected")
        if not isinstance(n_rejected, int) or n_rejected < 30:
            raise EventError(
                f"{kind} must carry n_human_rejected as an integer >= 30"
            )
        for field in (
            "qualification_rule_digest",
            "decision_surface_digest",
            "instrument_digest",
            "generator_policy_digest",
            "sampling_frame_digest",
            "interval_rule_digest",
        ):
            value = data.get(field)
            if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None:
                raise EventError(
                    f"{kind} must carry {field} as a lowercase SHA-256 digest"
                )
        interval = data.get("wilson_interval")
        if (
            not isinstance(interval, list)
            or len(interval) != 2
            or not all(isinstance(item, (int, float)) for item in interval)
        ):
            raise EventError(f"{kind} must carry wilson_interval as a two-number list")
        return
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise EventError(f"{kind} must carry a non-empty refusal reason")


def _check_attempt_identity(event: EventPayload) -> None:
    """Attempt records carry the stable identity that later records reference."""
    if event["event"] not in (
        OUTCOME_KIND,
        VERDICT_KIND,
        VERDICT_CORRECTION_KIND,
    ):
        return
    attempt_id = event["data"].get("attempt_id")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise EventError(f"{event['event']} must carry a non-empty string attempt_id")


def _check_attempt_contract(event: EventPayload) -> None:
    """Keep verifier outcomes and human judgements on distinct event paths."""
    kind = event["event"]
    data = event["data"]
    if kind == OUTCOME_KIND and "human_verdict" in data:
        raise EventError(
            f"{OUTCOME_KIND} cannot carry human_verdict; append a separate "
            f"{VERDICT_KIND} event"
        )
    if "human_verdict" in data and kind not in (
        VERDICT_KIND,
        VERDICT_CORRECTION_KIND,
    ):
        raise EventError(
            f"human_verdict is valid only on {VERDICT_KIND} or "
            f"{VERDICT_CORRECTION_KIND}"
        )
    if kind in (VERDICT_KIND, VERDICT_CORRECTION_KIND) and "human_verdict" not in data:
        raise EventError(f"{kind} must carry human_verdict")
    if kind != VERDICT_CORRECTION_KIND:
        return

    previous = data.get("previous_verdict")
    if previous not in ("accept", "reject"):
        raise EventError(
            f"{VERDICT_CORRECTION_KIND} must carry previous_verdict 'accept' or "
            f"'reject', got {previous!r}"
        )
    if data["human_verdict"] == previous:
        raise EventError("a verdict correction must change the previous verdict")
    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise EventError(f"{VERDICT_CORRECTION_KIND} must carry a non-empty reason")


def _check_verification_outcome_contract(event: EventPayload) -> None:
    """Keep component outcomes pairable without treating missing work as rejection."""
    if event["event"] != VERIFICATION_OUTCOME_KIND:
        return

    data = event["data"]
    for field in (
        "verification_id",
        "attempt_id",
        "protocol_id",
        "verifier_id",
        "verifier_version",
        "evidence_class",
    ):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EventError(
                f"{VERIFICATION_OUTCOME_KIND} must carry a non-empty string {field}"
            )

    version = data["verifier_version"]
    if version != version.strip() or not version.isprintable():
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} verifier_version must be canonical printable text"
        )

    digest = data.get("artefact_sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} artefact_sha256 must be 64 lowercase hex characters"
        )

    status = data.get("status")
    if status not in VERIFICATION_STATUSES:
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} status must be one of "
            f"{sorted(VERIFICATION_STATUSES)}, got {status!r}"
        )

    if status == "completed":
        if not isinstance(data.get("verifier_accept"), bool):
            raise EventError(
                f"{VERIFICATION_OUTCOME_KIND} verifier_accept must be a boolean when completed"
            )
    elif "verifier_accept" in data:
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} verifier_accept is valid only when completed"
        )

    if "human_decision" in data:
        raise EventError(
            f"{VERIFICATION_OUTCOME_KIND} cannot carry human_decision; append a separate "
            f"{VERDICT_KIND} event"
        )

    token = data.get("start_token")
    if token is not None:
        if not isinstance(token, str) or re.fullmatch(r"[0-9a-f]{64}", token) is None:
            raise EventError(
                f"{VERIFICATION_OUTCOME_KIND} start_token must be 64 lowercase hex characters"
            )


def _check_review_queue_contract(event: EventPayload) -> None:
    kind = event["event"]
    if kind == REVIEW_QUEUE_OPENED_KIND:
        data = event["data"]
        required = {
            "queue_id",
            "stream_cap",
            "exp105_prefix_n",
            "rejection_target",
            "population",
            "task_family",
            "protocol_id",
            "verifier_version",
            "verifier_contract_digest",
            "start_position",
            "eligible_universe_digest",
            "selector",
            "order_rule",
        }
        actual = set(data)
        if actual != required:
            missing = sorted(required - actual)
            unexpected = sorted(actual - required)
            detail = []
            if missing:
                detail.append(f"missing {missing}")
            if unexpected:
                detail.append(f"unexpected {unexpected}")
            raise EventError(
                f"{REVIEW_QUEUE_OPENED_KIND} body fields are fixed: {'; '.join(detail)}"
            )
        if int(data["stream_cap"]) != 90:
            raise EventError(f"{REVIEW_QUEUE_OPENED_KIND} stream_cap is fixed at 90")
        if int(data["exp105_prefix_n"]) != 30:
            raise EventError(f"{REVIEW_QUEUE_OPENED_KIND} exp105_prefix_n is fixed at 30")
        if data["selector"] != "first_matching_trajectory_order":
            raise EventError(
                f"{REVIEW_QUEUE_OPENED_KIND} selector must be "
                "'first_matching_trajectory_order'"
            )
        for field in ("verifier_contract_digest", "eligible_universe_digest"):
            digest = data[field]
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise EventError(
                    f"{REVIEW_QUEUE_OPENED_KIND} {field} must be 64 lowercase hex characters"
                )
        for field in ("rejection_target", "start_position"):
            value = data[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise EventError(
                    f"{REVIEW_QUEUE_OPENED_KIND} {field} must be a non-negative integer"
                )
        from . import verification as verification_mod

        recomputed = verification_mod.eligible_universe_digest(
            task_family=cast(str, data["task_family"]),
            population=cast(str, data["population"]),
            protocol_id=cast(str, data["protocol_id"]),
            verifier_version=cast(str, data["verifier_version"]),
            verifier_contract_digest=cast(str, data["verifier_contract_digest"]),
            order_rule=cast(str, data["order_rule"]),
        )
        if data["eligible_universe_digest"] != recomputed:
            raise EventError(
                f"{REVIEW_QUEUE_OPENED_KIND} eligible_universe_digest does not match the "
                "frozen manifest"
            )
        return

    if kind == CANDIDATE_EXPOSED_KIND:
        data = event["data"]
        required = {
            "queue_id",
            "exposure_id",
            "attempt_id",
            "exposure_ordinal",
            "start_token",
            "artefact_sha256",
            "task_family",
            "protocol_id",
            "verifier_version",
            "verifier_contract_digest",
        }
        actual = set(data)
        if actual != required:
            missing = sorted(required - actual)
            unexpected = sorted(actual - required)
            detail = []
            if missing:
                detail.append(f"missing {missing}")
            if unexpected:
                detail.append(f"unexpected {unexpected}")
            raise EventError(
                f"{CANDIDATE_EXPOSED_KIND} body fields are fixed: {'; '.join(detail)}"
            )
        ordinal = data["exposure_ordinal"]
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal <= 0:
            raise EventError(
                f"{CANDIDATE_EXPOSED_KIND} exposure_ordinal must be a positive integer"
            )
        for field in ("start_token", "artefact_sha256", "verifier_contract_digest"):
            digest = data[field]
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise EventError(
                    f"{CANDIDATE_EXPOSED_KIND} {field} must be 64 lowercase hex characters"
                )
        return

    if kind == ATTEMPT_REVIEWED_KIND:
        data = event["data"]
        required = {"queue_id", "exposure_id", "attempt_id", "disposition"}
        if set(data) != required:
            raise EventError(f"{ATTEMPT_REVIEWED_KIND} body fields are fixed")
        if data["disposition"] not in ("unclear",):
            raise EventError(
                f"{ATTEMPT_REVIEWED_KIND} disposition must be 'unclear' until Q02 ingress"
            )
        return

    if kind == REVIEW_PRESENTATION_FROZEN_KIND:
        data = event["data"]
        required = {
            "queue_id",
            "exposure_id",
            "attempt_id",
            "contract_digest",
            "artefact_digest",
            "component_rollup_digest",
            "presentation_digest",
        }
        if set(data) != required:
            raise EventError(f"{REVIEW_PRESENTATION_FROZEN_KIND} body fields are fixed")
        for field in (
            "contract_digest",
            "artefact_digest",
            "component_rollup_digest",
            "presentation_digest",
        ):
            digest = data[field]
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise EventError(
                    f"{REVIEW_PRESENTATION_FROZEN_KIND} {field} must be 64 lowercase hex "
                    "characters"
                )


def _check_consent_contract(event: EventPayload) -> None:
    """Consent is purpose-specific; commercial grants authorise one named use.

    ADR-0057 forbids shipping sharing until consent, retention and a checkable use
    limit exist. The exporter is not in this commit. These two fields are the part
    of that bar that can be enforced on the record itself: a grant with no purpose
    or no retention is the gap the ADR named, and omitting `human_decision` must
    not dodge V0-18 the way omitting it once dodged a verdict.
    """
    kind = event["event"]
    if kind not in CONSENT_KINDS:
        return
    data = event["data"]
    purpose = data.get("purpose")
    if not isinstance(purpose, str) or purpose not in CONSENT_PURPOSES:
        raise EventError(
            f"{kind} must declare purpose as one of {sorted(CONSENT_PURPOSES)}; "
            "purposes are not bundled"
        )
    if kind != CONSENT_GRANTED:
        grant_fields = sorted({"per_use", "use_ref"} & set(data))
        if grant_fields:
            raise EventError(
                f"{kind} is a withdrawal and must not carry commercial grant "
                f"field(s) {grant_fields}"
            )
        return
    retention = data.get("retention_days")
    if not isinstance(retention, int) or isinstance(retention, bool) or retention <= 0:
        raise EventError(
            f"{kind} must carry retention_days as a positive integer; "
            "a grant with no stated retention is the gap ADR-0057 forbids shipping"
        )
    try:
        datetime.fromisoformat(event["ts"]) + timedelta(days=retention)
    except OverflowError as exc:
        raise EventError(
            f"{kind} retention_days must produce a representable granted-until "
            "timestamp"
        ) from exc
    if purpose != "commercial-training":
        return
    if data.get("per_use") is not True:
        raise EventError(
            f"{kind} for commercial-training must carry per_use: true; commercial "
            "gain requires fresh consent for each use"
        )
    use_ref = data.get("use_ref")
    if not isinstance(use_ref, str) or not use_ref.strip():
        raise EventError(
            f"{kind} for commercial-training must carry use_ref as a non-empty "
            "string naming the single authorised use"
        )


def _check_response_rating_ban(event: EventPayload) -> None:
    """R22: no response-level rating surface, enforced in the schema.

    Compliance cannot rest on nobody having written the code yet. Any event carrying
    an approval-style field is rejected before it reaches the log, so a rating widget
    added tomorrow fails here rather than accreting.
    """
    data = event["data"]
    hits = sorted(RESPONSE_RATING_FIELDS & set(data))
    if hits:
        raise EventError(
            f"{event['event']} carries approval-style field(s) {hits}; the unit of "
            "feedback is the task, and response-level rating is not built "
            "(feedback-signals.md rules 1–2)"
        )


def _check_feedback_contract(event: EventPayload) -> None:
    """R20/R23: task-close feedback — durable, skippable, and never composite."""
    kind = event["event"]
    if kind not in FEEDBACK_KINDS:
        return
    data = event["data"]
    task_id = data.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise EventError(
            f"{kind} must carry task_id as a non-empty string; the no-re-ask rule is "
            "a query over the log and task_id is its key"
        )
    if kind == FEEDBACK_ASKED_KIND:
        goal_text = data.get("goal_text")
        if not isinstance(goal_text, str) or not goal_text.strip():
            raise EventError(
                f"{kind} must carry goal_text verbatim from the pre-committed goal "
                "record; the close surface renders the goal, nothing the agent wrote"
            )
    if kind == FEEDBACK_ANSWERED_KIND:
        achieved = data.get("goal_achieved")
        if achieved not in GOAL_ACHIEVED:
            raise EventError(
                f"{kind} must carry goal_achieved as one of {sorted(GOAL_ACHIEVED)}, "
                f"got {achieved!r}"
            )
        for optional in ("missing", "better_approach"):
            value = data.get(optional)
            if value is not None and not isinstance(value, str):
                raise EventError(f"{kind}.{optional} must be a string when present")
        composite = sorted(FEEDBACK_COMPOSITE_FIELDS & set(data))
        if composite:
            raise EventError(
                f"{kind} carries composite/efficiency field(s) {composite}; "
                "achievement and efficiency are separate records permanently, and no "
                "default composite score exists (feedback-signals.md)"
            )


def _check_visibility_contract(event: EventPayload) -> None:
    """R31 / ADR-0035: the dial is recorded so β stratifies by display conditions."""
    data = event["data"]
    if event["event"] == VISIBILITY_CHANGE_KIND:
        level = data.get("level")
        if level not in VISIBILITY_LEVELS:
            raise EventError(
                f"{VISIBILITY_CHANGE_KIND} must carry level as one of "
                f"{VISIBILITY_LEVELS}, got {level!r}"
            )
        overrides = data.get("overrides")
        if overrides is not None:
            if not isinstance(overrides, dict):
                raise EventError(f"{VISIBILITY_CHANGE_KIND}.overrides must be an object")
            for kind_name, override_level in overrides.items():
                if not isinstance(kind_name, str) or not kind_name.strip():
                    raise EventError("override keys must be non-empty event kinds")
                if override_level not in VISIBILITY_LEVELS:
                    raise EventError(
                        f"override for {kind_name!r} must be one of "
                        f"{VISIBILITY_LEVELS}, got {override_level!r}"
                    )
    effective = data.get("effective_visibility")
    if effective is not None and effective not in VISIBILITY_LEVELS:
        raise EventError(
            f"effective_visibility must be one of {VISIBILITY_LEVELS}, "
            f"got {effective!r}"
        )


def _decision_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EventError(f"decision protocol {field} must be a non-empty string")
    return value


def _decision_digest(value: object, field: str) -> str:
    text = _decision_text(value, field)
    if re.fullmatch(r"[0-9a-f]{64}", text) is None:
        raise EventError(f"decision protocol {field} must be a lower-case SHA-256 digest")
    return text


def _check_exact_event_reference(reference: object, field: str) -> None:
    required = {"event_id", "event_kind", "event_sha256"}
    if not isinstance(reference, dict) or set(reference) != required:
        raise EventError(f"decision protocol {field} must be an exact F03 event reference")
    _check_event_id(reference["event_id"])
    _decision_text(reference["event_kind"], f"{field}.event_kind")
    _decision_digest(reference["event_sha256"], f"{field}.event_sha256")


def _check_decision_content(data: EventPayload) -> None:
    for field in ("decision", "reasoning", "falsifier"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EventError(
                f"{DECISION_KIND} must carry {field} as a non-empty string"
            )

    if "reversal" not in data:
        raise EventError(f"{DECISION_KIND} must carry reversal (V0-22)")
    reversal = data["reversal"]
    if not isinstance(reversal, dict):
        raise EventError("reversal must be an object carrying kind and value")
    kind = reversal.get("kind")
    if not isinstance(kind, str) or kind not in REVERSAL_KINDS:
        raise EventError(
            f"reversal kind must be one of {sorted(REVERSAL_KINDS)}, got {kind!r}"
        )
    if "value" not in reversal:
        raise EventError("reversal must carry value")

    value = reversal["value"]
    if kind == "revert":
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{7,40}", value) is None:
            raise EventError(
                "revert reversal value must be a 7-40 character commit sha"
            )
    elif kind == "command":
        if (
            not isinstance(value, list)
            or not value
            or any(not isinstance(token, str) or not token.strip() for token in value)
        ):
            raise EventError(
                "command reversal value must be a non-empty argv token list"
            )
    elif (
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+", value)
        is None
    ):
        raise EventError("inverse reversal value must be a dotted importable symbol")


def _check_alternatives(data: EventPayload) -> None:
    alternatives = data["alternatives"]
    if not isinstance(alternatives, list):
        raise EventError("decision protocol alternatives must be an array")
    for index, alternative in enumerate(alternatives):
        if not isinstance(alternative, dict) or set(alternative) != {
            "option",
            "rejected_because",
        }:
            raise EventError(
                f"decision protocol alternatives[{index}] must contain exactly option and rejected_because"
            )
        _decision_text(alternative["option"], f"alternatives[{index}].option")
        _decision_text(
            alternative["rejected_because"],
            f"alternatives[{index}].rejected_because",
        )

    only_admissible = data.get("only_admissible")
    if alternatives:
        if only_admissible is not None:
            raise EventError(
                "decision protocol only_admissible is permitted only when alternatives is empty"
            )
        return
    if not isinstance(only_admissible, dict) or set(only_admissible) != {"rule_refs"}:
        raise EventError(
            "decision protocol empty alternatives requires exact only_admissible.rule_refs"
        )
    rule_refs = only_admissible["rule_refs"]
    if not isinstance(rule_refs, list) or not rule_refs:
        raise EventError("decision protocol only_admissible.rule_refs must be non-empty")
    for index, rule_ref in enumerate(rule_refs):
        _decision_text(rule_ref, f"only_admissible.rule_refs[{index}]")


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
        raise EventError("decision protocol threshold must carry its three versioned inputs")
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
        raise EventError("decision protocol not_warranted requires a false threshold input")
    if status == "completed" and "false" in states:
        raise EventError("decision protocol completed cannot carry a false threshold input")
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
        raise EventError(f"decision protocol admission {admission!r} is invalid for {label}")

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


def _check_planning_record(
    data: EventPayload,
    *,
    actor: str,
    protected_proposal: bool,
) -> None:
    required = {
        "decision_id",
        "operation_id",
        "ticket",
        "owner",
        "actor",
        "record_level",
        "decision",
        "reasoning",
        "falsifier",
        "reversal",
        "alternatives",
        "evidence_refs",
        "acceptance_contract_digest",
        "protocol",
        "binding",
    }
    optional = {"only_admissible", "supersedes"}
    actual = set(data)
    if not required <= actual or not actual <= required | optional:
        raise EventError(
            "decision protocol planning fields mismatch; "
            f"missing {sorted(required - actual)}, unexpected {sorted(actual - required - optional)}"
        )
    for field in ("decision_id", "operation_id", "ticket", "owner", "actor"):
        _decision_text(data[field], field)
    if data["actor"] != actor:
        raise EventError("decision protocol actor must match the event actor")
    _check_decision_content(data)
    _check_alternatives(data)
    evidence_refs = data["evidence_refs"]
    if not isinstance(evidence_refs, list) or not evidence_refs:
        raise EventError("decision protocol evidence_refs must be a non-empty array")
    for index, evidence_ref in enumerate(evidence_refs):
        _check_exact_event_reference(evidence_ref, f"evidence_refs[{index}]")
    _decision_digest(
        data["acceptance_contract_digest"], "acceptance_contract_digest"
    )
    protocol_status = _check_protocol(data["protocol"])
    admission = _check_binding(
        data["binding"], protected_proposal=protected_proposal
    )
    expected_level = (
        "full"
        if admission in _PROTECTED_ADMISSION_CLASSES or protocol_status == "completed"
        else "minimal"
    )
    if data["record_level"] != expected_level:
        raise EventError(
            f"decision protocol record_level must be {expected_level!r} for {admission}/{protocol_status}"
        )
    if "supersedes" in data:
        _check_exact_event_reference(data["supersedes"], "supersedes")


def decision_protocol_data(event: object) -> EventPayload | None:
    """Return the strict nested P01 planning record, excluding legacy audit rows."""
    raw = event.raw if isinstance(event, Event) else event
    if not isinstance(raw, dict):
        return None
    data = raw.get("data")
    if not isinstance(data, dict):
        return None
    if raw.get("event") == ACTION_PROPOSAL_KIND:
        planning = data.get("planning")
        return planning if isinstance(planning, dict) else None
    if raw.get("event") == DECISION_KIND and _DECISION_PROTOCOL_MARKERS & set(data):
        return data
    return None


def _check_decision_contract(event: EventPayload) -> None:
    """V0-22/23/24 and P01: bind reversible decisions before consequence."""
    if event["event"] == ACTION_PROPOSAL_KIND:
        data = event["data"]
        if set(data) != {"proposal_id", "planning"}:
            raise EventError(
                f"{ACTION_PROPOSAL_KIND} must contain exactly proposal_id and planning"
            )
        _decision_text(data["proposal_id"], "proposal_id")
        planning = data["planning"]
        if not isinstance(planning, dict):
            raise EventError(f"{ACTION_PROPOSAL_KIND} planning must be an object")
        _check_planning_record(
            planning,
            actor=cast(str, event["actor"]),
            protected_proposal=True,
        )
        return
    if event["event"] != DECISION_KIND:
        return
    data = event["data"]
    _check_decision_content(data)

    decision_class = data.get("class")
    if isinstance(decision_class, str) and decision_class in USER_ONLY:
        raise EventError(
            f"decision class {decision_class!r} is reserved to the user (V0-23)"
        )
    if decision_class in PROTECTED_DECISION_CLASSES:
        raise EventError(
            f"decision class {decision_class!r} is protected and cannot be autonomous"
        )
    if _DECISION_PROTOCOL_MARKERS & set(data):
        _check_planning_record(
            data,
            actor=cast(str, event["actor"]),
            protected_proposal=False,
        )


def _check_human_authority(event: EventPayload) -> None:
    """V0-18: an agent may never author a human's decision.

    `principal` names whose authority is being exercised. It is not itself an authority
    grant, so it can never convert an agent-authored event into the human's decision.
    """
    decision = event["data"].get("human_decision")
    has_verdict = "human_verdict" in event["data"]
    verdict = event["data"].get("human_verdict")

    # A human verdict IS a human decision, and until 20 Aug 2026 it was the way round this
    # check. `_check_human_authority` returned early whenever `human_decision` was absent,
    # while `projection._apply_outcome` read `human_verdict` straight off an
    # `attempt.outcome` event and wrote it to the table beta is computed from. So an agent
    # could author the human verdict that beta is measured against, and V0-18 — the
    # invariant that exists to prevent exactly that — never fired. Found by Cursor
    # (Gemini 3.7 Flash) auditing code Claude wrote; a second path to a guarded state is
    # the `jobboard-v2` failure this project was founded on.
    if has_verdict:
        if verdict not in ("accept", "reject"):
            raise EventError(
                f"human_verdict must be 'accept' or 'reject', got {verdict!r}"
            )
        if decision is None:
            decision = "verdict"
        elif decision != "verdict":
            raise EventError(
                f"event carries a human_verdict but declares human_decision {decision!r}; "
                "a human verdict is a verdict and may not be filed as anything else (V0-18)"
            )

    # Same shape for consent. A `consent.granted` event *is* a human decision; if we
    # returned early whenever `human_decision` was absent, an agent could author a
    # share grant by omitting the field — the verdict hole, reproduced on the event
    # that would authorise data leaving the machine.
    if event["event"] in CONSENT_KINDS:
        if decision is None:
            decision = "consent"
        elif decision != "consent":
            raise EventError(
                f"event {event['event']} carries human_decision {decision!r}; "
                "a consent event is a consent and may not be filed as anything else "
                "(V0-18)"
            )

    # And the same shape again for feedback answers: the close questions go to the
    # user, never the agent — agent self-assessment is never an outcome signal
    # (feedback-signals.md rule 2; false self-reported completion is the measured
    # failure). An answered event without the human_decision discipline is an agent
    # grading its own homework.
    if event["event"] == FEEDBACK_ANSWERED_KIND:
        if decision is None:
            decision = "feedback"
        elif decision != "feedback":
            raise EventError(
                f"{FEEDBACK_ANSWERED_KIND} carries human_decision {decision!r}; "
                "a feedback answer is the user's and may not be filed as anything "
                "else (V0-18)"
            )

    if decision is None:
        return
    if decision not in HUMAN_ONLY:
        raise EventError(
            f"unknown human_decision {decision!r}; expected one of {sorted(HUMAN_ONLY)}"
        )

    principal = event["data"].get("principal")
    if principal is None:
        raise EventError("a human_decision event must name its principal")
    if event["actor"] != principal:
        raise EventError(
            f"human_decision {decision!r} is attributed to principal {principal!r} but was "
            f"authored by {event['actor']!r}; only the principal may author their own "
            f"decision (V0-18)"
        )
    via = event["data"].get("via")
    if not isinstance(via, str) or not via.strip():
        raise EventError(
            f"human_decision {decision!r} must record `via` as a non-empty string"
        )
    if via.strip().casefold() != "cli":
        # No signature verifier exists in the observe-only increment. A payload claiming
        # to carry a signature is not evidence that the signature was verified. This
        # checks declared provenance; trusted ingress must later establish authorship.
        raise EventError(
            f"human_decision {decision!r} declares non-local channel {via.strip()!r}; "
            "only local CLI is accepted because this build has no signature verifier "
            "(V0-28)"
        )
    # ADR-0078: caller-supplied actor/via metadata does not admit a capability gate.
    # Gate admission is derived only from inventory gate facts via effects.derive_admission().


def canonical(event: EventPayload) -> str:
    """One event, one line, stable key order so a replay hash is reproducible."""
    return json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


MAX_CLOCK_SKEW_S = 15 * 60


def _check_clock(event: EventPayload) -> None:
    """An appended event must be stamped from a clock, not from an author's belief.

    Added 20 Aug 2026 after the orchestrator wrote six consecutive trajectory events with
    invented timestamps, drifting to 2h15m ahead of the wall clock, while documenting
    instrument-integrity defects in other people's work. Nothing caught it: `validate`
    checked the *format* of `ts` and its offset, which were impeccable, and never asked
    whether the value was true.

    A format check on a timestamp is not a check on a timestamp.

    This runs at append only, never in `validate`, because reading a historical log must
    not depend on when it is read — which is the same reason `ts` requires an explicit
    offset in the first place.
    """
    stamped = datetime.fromisoformat(event["ts"])
    skew = abs((datetime.now(timezone.utc) - stamped).total_seconds())
    if skew > MAX_CLOCK_SKEW_S:
        raise EventError(
            f"event ts {event['ts']} is {skew / 60:.0f} minutes from the current clock, "
            f"beyond the {MAX_CLOCK_SKEW_S // 60}-minute tolerance. Stamp events from the "
            "clock rather than writing the time you believe it to be. To record something "
            "that happened earlier, put the occurrence time in `data` and let `ts` record "
            "when it was written."
        )


@contextmanager
def _budget_transaction(directory: Path) -> Iterator[None]:
    """Serialise every budget-state and reservation write in one directory."""
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / BUDGET_LOCK
    lock.touch(exist_ok=False)
    token = _BUDGET_LOCK_HELD.set(lock.resolve())
    try:
        yield
    finally:
        _BUDGET_LOCK_HELD.reset(token)
        lock.unlink(missing_ok=True)


# The durability path (F01). Until 22 Aug 2026 the append below was a buffered
# `path.open("a")` write: no serialisation across processes, so concurrent writers
# tore lines on the real trajectory, and no fsync, so an acknowledged event could
# still be lost with the process. [measured: the pinned torn-append incident in
# `tests/test_v0_invariants.py::test_no_new_event_may_bypass_append`; the `loop.py`
# ponytail] The contract now: `append` returns only after one complete UTF-8 line is
# written under a kernel-backed per-log lock and fsynced, and every failure raises —
# a partial line is never acknowledged, and is rolled back so it is never left
# behind either. The lock is the log's own descriptor: `fcntl.flock` on POSIX,
# `msvcrt.locking` on Windows, both released by the kernel when a holder dies, so a
# killed writer cannot strand the log the way a lock file does.

if sys.platform == "win32":
    # O_BINARY: without it the Windows CRT translates "\n" to "\r\n" on write.
    _OPEN_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_BINARY
    # The transaction reads the prefix through the descriptor that holds the
    # lock, so it needs read access; see _read_under_lock.
    _TRANSACTION_OPEN_FLAGS = os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_BINARY
else:
    _OPEN_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    _TRANSACTION_OPEN_FLAGS = os.O_RDWR | os.O_CREAT | os.O_APPEND


def _lock_file(fd: int) -> None:
    """Take the kernel-backed per-log lock; block until held. Death releases it."""
    if sys.platform == "win32":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        while True:
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                time.sleep(0.005)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_EX)


def _unlock_file(fd: int) -> None:
    """Best-effort: the descriptor is closed immediately after, which releases the
    lock regardless, so an unlock failure changes nothing."""
    if sys.platform == "win32":
        import msvcrt

        try:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        import fcntl

        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass


def _write_all(fd: int, data: bytes) -> None:
    """Write every byte or raise; a short write is retried, never acknowledged early."""
    view = memoryview(data)
    while len(view) > 0:
        try:
            written = os.write(fd, view)
        except OSError as exc:
            raise EventError(
                f"could not write the event line; the append is not acknowledged: {exc}"
            ) from exc
        if written <= 0:
            raise EventError(
                "a write made no progress; the append is not acknowledged"
            )
        view = view[written:]


def _fsync_file(fd: int) -> None:
    try:
        os.fsync(fd)
    except OSError as exc:
        raise EventError(
            f"could not fsync the event line; the append is not acknowledged: {exc}"
        ) from exc


def _fsync_directory(directory: Path) -> None:
    """Make a newly created log's directory entry durable where the platform exposes it.

    POSIX exposes directory fsync. The Windows standard library does not, so there
    this is a no-op and the first-file guarantee covers the file-content fsync and
    nothing broader.
    """
    if sys.platform == "win32":
        return
    else:
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _rollback(fd: int, offset: int) -> None:
    """Best-effort removal of a failed append's bytes. If the truncate itself fails,
    the torn bytes stay and `read()` quarantines them as a rejection — a partial
    line is still never acknowledged."""
    try:
        os.ftruncate(fd, offset)
    except OSError:
        pass


def _write_validated(path: Path, event: EventPayload) -> EventPayload:
    if event["event"] in (BUDGET_STATE_KIND, SPEND_RESERVED_KIND):
        expected = f"{event['ts'][:10]}.jsonl"
        if path.name != expected:
            raise EventError(
                f"{event['event']} must be written to its timestamped daily file "
                f"{expected!r}, not {path.name!r}"
            )
    _check_clock(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    created = not path.exists()
    line = (canonical(event) + "\n").encode("utf-8")
    fd = os.open(path, _TRANSACTION_OPEN_FLAGS)
    try:
        _lock_file(fd)
        try:
            prefix, _rejected = _read_under_lock(path, fd)
            _reject_duplicate_event_ids(tuple(prefix), (event,))
            offset = os.lseek(fd, 0, os.SEEK_END)
            try:
                _write_all(fd, line)
                # fsync inside the lock: an acknowledged prefix is always durable,
                # so a failed fsync rolls back before any later line can be
                # acknowledged over a non-durable earlier one.
                _fsync_file(fd)
            except EventError:
                _rollback(fd, offset)
                raise
        finally:
            _unlock_file(fd)
    finally:
        os.close(fd)
    if created:
        try:
            _fsync_directory(path.parent)
        except OSError as exc:
            raise EventError(
                f"the line is written and fsynced but the directory entry of "
                f"{path.name!r} could not be fsynced; the append is not "
                f"acknowledged: {exc}"
            ) from exc
    return event


# The compare-and-append transaction (F02). `append` checks a candidate against
# nothing but itself, so a rule that depends on the current state of the log —
# "this claim is still unheld", "this revision is still the tip" — had no honest
# place to run, and ADR-0070's evidence names the consequence: central
# `events.append()` called only `events.validate()`, so a helper's domain rule
# could be bypassed through the generic door. [measured: ADR-0070 evidence] The
# contract now: one per-log transaction validates every candidate before any
# byte is written, reads the accepted prefix and the rejections while holding
# the F01 lock, runs a pure transition validator against them, then writes the
# batch contiguously with one fsync. A rule registered here runs inside that
# transaction whichever door the caller takes, so `consil record` cannot bypass
# it. Any failure acknowledges nothing and rolls the whole batch back.

_TRANSITION_VALIDATORS: dict[str, TransitionValidator] = {}


def register_transition_validator(
    kinds: Iterable[str], validator: TransitionValidator
) -> None:
    """Bind a pure domain transition validator to event kinds.

    Once a kind is registered, every append of it — through the one-event front
    door `append()` or through `append_transaction()` — runs the validator
    against the accepted prefix and rejections while holding the per-log lock,
    so no caller bypasses the domain rule by choosing a different door. This is
    the universal boundary ADR-0070's enforcement section names; C01 registers
    `work_items.validate_transition()` here.

    The budget kinds are refused: budget.state and spend.reserved keep their own
    serialised path through `append()` (the budget lock), and a second
    governance path for them would be the bypass this boundary exists to close.
    Re-registering a kind is refused for the same reason: a rule that can be
    quietly replaced is not a rule.
    """
    kinds = tuple(kinds)
    if not kinds:
        raise EventError("register at least one event kind")
    for kind in kinds:
        if not isinstance(kind, str) or not kind.strip():
            raise EventError("registered kinds must be non-empty strings")
        if kind in (BUDGET_STATE_KIND, SPEND_RESERVED_KIND):
            raise EventError(
                f"{kind} keeps the budget serialisation path through append(); "
                "a second governance path for it would be bypassable"
            )
        if kind in _TRANSITION_VALIDATORS:
            raise EventError(
                f"{kind} already has a registered transition validator; a rule "
                "that can be quietly replaced is not a rule"
            )
    for kind in kinds:
        _TRANSITION_VALIDATORS[kind] = validator


def _validate_effect_receipt_chain(
    prefix: tuple[Event, ...],
    rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    try:
        effects.receipt_chain_validator(prefix, rejections, candidates)
    except effects.EffectError as exc:
        raise EventError(str(exc)) from exc


def _validate_record_relations(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    """Resolve correction edges against the locked, accepted earlier prefix."""
    for candidate in candidates:
        if candidate["event"] != RECORD_CAPTURED_KIND:
            continue
        data = candidate["data"]
        for relation in ("supersedes", "invalidates"):
            for reference in data[relation]:
                if reference["event_id"] == candidate["event_id"]:
                    raise EventError(
                        f"{RECORD_CAPTURED_KIND} {relation} cannot reference itself"
                    )
                try:
                    resolve_reference(reference, prefix)
                except EventError as exc:
                    raise EventError(
                        f"{RECORD_CAPTURED_KIND} {relation} must reference an exact earlier "
                        f"record.captured event: {exc}"
                    ) from exc


def _planning_references(record: EventPayload) -> Iterator[tuple[str, object]]:
    for index, reference in enumerate(cast(list[object], record["evidence_refs"])):
        yield f"evidence_refs[{index}]", reference
    protocol = cast(EventPayload, record["protocol"])
    for field in (
        "instructions_ref",
        "bar_ref",
        "search_ref",
        "killing_check_ref",
    ):
        if field in protocol:
            yield f"protocol.{field}", protocol[field]
    if "supersedes" in record:
        yield "supersedes", record["supersedes"]


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
                        raise EventError("protected proposal authority cannot be legacy/unmeasured")
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


register_transition_validator((RECORD_CAPTURED_KIND,), _validate_record_relations)
register_transition_validator(
    (effects.EFFECT_INTENT, effects.EFFECT_RECEIPT), _validate_effect_receipt_chain
)
register_transition_validator(
    (DECISION_KIND, ACTION_PROPOSAL_KIND), _validate_decision_relations
)


def _transaction(
    path: Path,
    candidates: list[EventPayload],
    validator: TransitionValidator | None,
) -> list[EventPayload]:
    """Compare-and-append under the per-log lock.

    Candidates arrive validated. The accepted prefix and the rejections are read
    while holding the F01 lock and handed to the caller's validator and to every
    registered rule governing a candidate's kind; only then is the batch written
    contiguously and fsynced. Any failure raises and rolls every byte of the
    batch back: a partial multi-event success is never returned.
    """
    for candidate in candidates:
        _check_clock(candidate)
    path.parent.mkdir(parents=True, exist_ok=True)
    created = not path.exists()
    fd = os.open(path, _TRANSACTION_OPEN_FLAGS)
    try:
        _lock_file(fd)
        try:
            try:
                accepted, rejected = _read_under_lock(path, fd)
            except (OSError, UnicodeDecodeError) as exc:
                raise EventError(
                    f"could not read the current prefix of {path.name!r}; the "
                    "transaction is not acknowledged rather than run against an "
                    f"assumed empty history: {exc}"
                ) from exc
            prefix = tuple(accepted)
            rejections = tuple(rejected)
            batch = tuple(candidates)
            _reject_duplicate_event_ids(prefix, batch)
            if validator is not None:
                validator(prefix, rejections, batch)
            for candidate in batch:
                registered = _TRANSITION_VALIDATORS.get(candidate["event"])
                if registered is not None:
                    registered(prefix, rejections, batch)
            _validate_delivery_claim_ordering(prefix, rejections, batch)
            offset = os.lseek(fd, 0, os.SEEK_END)
            try:
                for candidate in batch:
                    _write_all(fd, (canonical(candidate) + "\n").encode("utf-8"))
                # fsync inside the lock, exactly as the single-append path: an
                # acknowledged batch is always durably ordered behind every
                # earlier acknowledged line, and a failed fsync rolls back
                # before any later line can be acknowledged over it.
                _fsync_file(fd)
            except EventError:
                _rollback(fd, offset)
                raise
        finally:
            _unlock_file(fd)
    finally:
        os.close(fd)
    if created:
        try:
            _fsync_directory(path.parent)
        except OSError as exc:
            raise EventError(
                f"the batch is written and fsynced but the directory entry of "
                f"{path.name!r} could not be fsynced; the transaction is not "
                f"acknowledged: {exc}"
            ) from exc
    return list(candidates)


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
            "one transaction writes one log; the candidates span dates "
            f"{sorted(dates)}"
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
    if event["event"] in _TRANSITION_VALIDATORS:
        # A governed kind takes the same transaction as a batch, so the domain
        # rule runs against the locked prefix whichever door the caller took.
        return _transaction(path, [event], None)[0]
    return _write_validated(path, event)


# Six attempts with doubling backoff from 40ms spans roughly 2.5s, which is far longer than a
# file replace holds the path, and short enough that a genuinely stuck file fails the dispatch
# rather than hanging it.
_READ_RETRIES = 6
_READ_BACKOFF = 0.04


def _classify_lines(
    path_label: str, lines: Iterable[str]
) -> tuple[list[Event], list[Rejection]]:
    """Split raw lines into accepted events and rejections — the one classifier
    behind both `read()` and the transaction's locked read, so a line is judged
    identically through either path."""
    events: list[Event] = []
    rejected: list[Rejection] = []
    for number, line in enumerate(lines, start=1):
        content_digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            rejected.append(
                Rejection(path_label, number, f"not valid JSON: {exc}", content_digest)
            )
            continue
        try:
            validate(raw)
        except EventError as exc:
            rejected.append(Rejection(path_label, number, str(exc), content_digest))
            continue
        events.append(Event(raw, path_label, number))
    return events, rejected


def read(path: Path) -> tuple[list[Event], list[Rejection]]:
    """Every valid event in file order, and every line that was refused.

    A refused line is never silently skipped — it comes back in the second element, and
    the caller must decide what to say about it. The two-tuple is deliberate: it makes the
    quarantine impossible to ignore by accident, which a logged warning would not.
    """
    if not path.exists():
        return [], []
    # Windows denies a reader while a concurrent writer holds the file, and the trajectory is
    # written continuously while every dispatched harness reads it at startup. That collision
    # killed 6 of 6 failed dispatches on 23 August 2026 -- including the only Grok run -- with
    # PermissionError raised out of `instructions.assemble`, seconds after the scheduler had
    # already reported the work as dispatched. The harness never started, and a process-based
    # check would have called it healthy. [measured]
    #
    # The condition is transient by construction: the writer replaces the file and releases it.
    # Retry briefly, then fail loudly -- a reader that silently returned an empty trajectory
    # would be far worse, because every downstream decision would be made against no history.
    last: OSError | None = None
    for attempt in range(_READ_RETRIES):
        try:
            with path.open(encoding="utf-8") as fh:
                return _classify_lines(str(path), fh)
        except PermissionError as exc:
            last = exc
            time.sleep(_READ_BACKOFF * (2**attempt))
    raise EventError(
        f"{path} could not be read after {_READ_RETRIES} attempts: observed access denial "
        f"({last}); it may be held by another process. The trajectory is never partially "
        "reported -- refusing rather than "
        "continuing against an incomplete history."
    )


def _read_under_lock(path: Path, fd: int) -> tuple[list[Event], list[Rejection]]:
    """Read the log through the descriptor that holds the per-log lock.

    POSIX flock is advisory, but the Windows byte-range lock refuses a second
    handle reading the locked region at all, so under the lock the prefix cannot
    be read through a fresh open; the locking descriptor itself may read it. The
    bytes are decoded with the same universal-newline rule text mode applies, so
    a line classifies identically through either path.
    """
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        chunks.append(chunk)
    payload = b"".join(chunks)
    if payload and not payload.endswith(b"\n"):
        raise EventError(
            f"refusing append to {path.name!r}: torn line at byte offset {payload.rfind(b'\n') + 1}"
        )
    text = payload.decode("utf-8")
    normalised = text.replace("\r\n", "\n").replace("\r", "\n")
    return _classify_lines(str(path), normalised.splitlines(keepends=True))


def read_all(directory: Path) -> tuple[list[Event], list[Rejection]]:
    """Every event across every daily file, ordered by filename then position."""
    events: list[Event] = []
    rejected: list[Rejection] = []
    for path in sorted(directory.glob("*.jsonl")):
        if not path.is_file():
            continue
        file_events, file_rejected = read(path)
        events.extend(file_events)
        rejected.extend(file_rejected)
    seen_ids: dict[str, Event] = {}
    for event in events:
        event_id = event.raw.get("event_id")
        if not isinstance(event_id, str):
            continue
        first = seen_ids.get(event_id)
        if first is None:
            seen_ids[event_id] = event
            continue
        rejected.append(
            Rejection(
                event.path or "",
                event.line or 0,
                "duplicate event_id "
                f"{event_id!r}; first appeared at {first.path}:{first.line}",
                event_sha256(event.raw),
            )
        )
    return events, rejected


def _reject_duplicate_event_ids(
    prefix: tuple[Event, ...], candidates: tuple[EventPayload, ...]
) -> None:
    """Fail closed on a reused identity while the F01 lock protects the prefix."""
    seen: set[str] = set()
    for existing in prefix:
        event_id = existing.raw.get("event_id")
        if not isinstance(event_id, str):
            continue
        if event_id in seen:
            raise EventError(f"historical duplicate event_id {event_id!r}")
        seen.add(event_id)
    for candidate in candidates:
        event_id = cast(str, candidate["event_id"])
        if event_id in seen:
            raise EventError(f"duplicate event_id {event_id!r}")
        seen.add(event_id)


def event_sha256(event: EventPayload) -> str:
    """Digest the complete canonical event; identity and content remain distinct."""
    return hashlib.sha256(canonical(event).encode("utf-8")).hexdigest()


def resolve_reference(
    reference: object, events: Iterable[Event], *, before: Event | None = None
) -> Event | str:
    """Resolve one exact reference to an earlier event, or mark a real legacy row.

    A legacy reference may identify its stored schema-v1 event only by kind and
    complete-content hash; it is explicitly unmeasured because it lacks an ID.
    Any other missing or malformed modern reference fails closed.
    """
    if not isinstance(reference, dict):
        raise EventError("event reference must be an object")
    kind = reference.get("event_kind")
    digest = reference.get("event_sha256")
    if not isinstance(kind, str) or not kind:
        raise EventError("event reference must carry event_kind as a non-empty string")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise EventError("event reference must carry event_sha256 as 64 lower-case hex characters")

    ordered = tuple(events)
    event_id = reference.get("event_id")
    if event_id is None:
        legacy = [
            event
            for event in ordered
            if "event_id" not in event.raw
            and event.kind == kind
            and event_sha256(event.raw) == digest
        ]
        if len(legacy) == 1:
            return "unmeasured"
        raise EventError("event reference is missing event_id")
    _check_event_id(event_id)
    matching = [event for event in ordered if event.raw.get("event_id") == event_id]
    if not matching:
        raise EventError(f"event reference {event_id!r} is missing")
    if len(matching) != 1:
        raise EventError(f"event reference {event_id!r} is not unique")
    target = matching[0]
    if before is not None:
        try:
            before_index = next(index for index, event in enumerate(ordered) if event is before)
        except StopIteration as exc:
            raise EventError("reference consumer is absent from trajectory order") from exc
        target_index = next(index for index, event in enumerate(ordered) if event is target)
        if target_index >= before_index:
            raise EventError(f"event reference {event_id!r} is not earlier than its consumer")
    if target.kind != kind:
        raise EventError(f"event reference {event_id!r} has mismatched event_kind")
    if event_sha256(target.raw) != digest:
        raise EventError(f"event reference {event_id!r} has mismatched event_sha256")
    return target


def rejection_digest(rejected: list[Rejection]) -> str:
    """Fingerprint the exact quarantined lines without binding to an absolute clone path."""
    rows = (
        json.dumps(
            (Path(item.path).name, item.line, item.reason, item.content_digest),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        for item in rejected
    )
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def bypassed(directory: Path) -> list[tuple[str, int]]:
    """Lines that did not come through `append()`.

    `append` is documented as the only writer and is the only place `validate` runs. On
    20 August 2026, 92 of the 93 events in the real trajectory — 98.9% — had been written
    straight to the file by something else, which is how three events V0-18 forbids came
    to be in an authoritative record whose sole writer rejects them. [measured]

    That is `AGENTS.md` working principle 3 reproduced inside the artefact the principle
    was written about: a documented single boundary fragments into several access paths
    because no check bans the bypass.

    ponytail: canonical form is a proxy, not a boundary. It catches hand-written JSON,
    which is the failure that actually happened; it would not catch a writer that
    formatted its output correctly. The upgrade path if that ever matters is a per-event
    digest of the previous line, which cannot be applied retroactively to history.
    """
    out: list[tuple[str, int]] = []
    for path in sorted(directory.glob("*.jsonl")):
        # MEASURED 24 August 2026. Windows denies a reader while a writer holds the file, and
        # roughly twenty agents append here continuously, so this raised PermissionError and
        # failed the suite -- which then blocked retirement, merging and publication at once.
        # `read()` above already retries for exactly this reason; this path was written without
        # it. Same bound, same backoff, and the same refusal to report a partial trajectory:
        # after the last attempt it raises rather than returning a short list, because a
        # bypass check that silently sees fewer lines reports fewer bypasses.
        for attempt in range(_READ_RETRIES):
            try:
                with path.open(encoding="utf-8") as probe:
                    probe.read(0)
                break
            except PermissionError as exc:
                if attempt == _READ_RETRIES - 1:
                    raise EventError(
                        f"{path} could not be read after {_READ_RETRIES} attempts: observed "
                        f"access denial ({exc}); it may be held by another process. The "
                        "trajectory is never partially reported -- refusing rather than "
                        "continuing against an incomplete history."
                    ) from exc
                time.sleep(_READ_BACKOFF * (2**attempt))
        with path.open(encoding="utf-8") as fh:
            for number, line in enumerate(fh, start=1):
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                try:
                    if canonical(json.loads(line)) != line:
                        out.append((str(path), number))
                except json.JSONDecodeError:
                    out.append((str(path), number))
    return out


def prefix_digest(path: Path, count: int) -> str:
    """Digest of the first `count` lines — the append-only check.

    Appending must never change an earlier position. A test asserts the digest of the
    committed prefix survives an append and that an in-place edit is detected.
    """
    lines = []
    with path.open(encoding="utf-8") as fh:
        for number, line in enumerate(fh):
            if number >= count:
                break
            lines.append(line.rstrip("\n"))
    if len(lines) < count:
        raise EventError(
            f"{path} has {len(lines)} lines, cannot digest a prefix of {count}"
        )
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _estimate_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EventError(f"{field} must be a non-empty string")
    return value


def _estimate_digest_field(value: object, field: str) -> str:
    text = _estimate_text(value, field)
    if DIGEST_RE.fullmatch(text) is None:
        raise EventError(f"{field} must be a lowercase SHA-256 digest")
    return text


def _estimate_timestamp(value: object, field: str) -> str:
    text = _estimate_text(value, field)
    if not TS.match(text):
        raise EventError(f"{field} must be RFC3339 with an explicit offset")
    try:
        datetime.fromisoformat(text).astimezone(timezone.utc)
    except (OverflowError, ValueError) as exc:
        raise EventError(f"{field} is not a valid calendar timestamp") from exc
    return text


def _estimate_non_negative_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EventError(f"{field} must be a non-negative integer")
    return value


def _check_estimate_cohort(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise EventError("cohort_key must be an object")
    parsed: dict[str, str] = {}
    for field in (
        "artefact_kind",
        "verifier_contract_digest",
        "size_band",
        "route_capability_class",
    ):
        parsed[field] = _estimate_text(value.get(field), f"cohort_key.{field}")
        if field.endswith("_digest"):
            _estimate_digest_field(parsed[field], f"cohort_key.{field}")
    return parsed


def _check_estimate_analogue(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise EventError("analogue_ids must be an array")
    parsed: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise EventError(f"analogue_ids[{index}] must be an object")
        event_id = _estimate_text(item.get("event_id"), f"analogue_ids[{index}].event_id")
        _check_uuid4(event_id, f"analogue_ids[{index}].event_id")
        event_kind = _estimate_text(item.get("event_kind"), f"analogue_ids[{index}].event_kind")
        event_digest = _estimate_digest_field(
            item.get("event_sha256"), f"analogue_ids[{index}].event_sha256"
        )
        parsed.append(
            {
                "event_id": event_id,
                "event_kind": event_kind,
                "event_sha256": event_digest,
            }
        )
    return parsed


def _check_stream_bounds(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list) or not value:
        raise EventError("stream_bounds must be a non-empty array")
    parsed: list[dict[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise EventError(f"stream_bounds[{index}] must be an object")
        stream_id = _estimate_text(item.get("stream_id"), f"stream_bounds[{index}].stream_id")
        earliest_s = _estimate_non_negative_int(
            item.get("earliest_s"), f"stream_bounds[{index}].earliest_s"
        )
        latest_s = _estimate_non_negative_int(
            item.get("latest_s"), f"stream_bounds[{index}].latest_s"
        )
        if latest_s < earliest_s:
            raise EventError(
                f"stream_bounds[{index}].latest_s must be >= stream_bounds[{index}].earliest_s"
            )
        parsed.append(
            {"stream_id": stream_id, "earliest_s": earliest_s, "latest_s": latest_s}
        )
    return parsed


def estimate_digest(data: Mapping[str, object]) -> str:
    payload = {
        key: value
        for key, value in data.items()
        if key != "estimate_digest"
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
            raise EventError("revision zero original_estimate_id must equal estimate_id")
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
    if not isinstance(sample_size, int) or isinstance(sample_size, bool) or sample_size < 0:
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


def _cohort_matches(candidate: Mapping[str, object], cohort_key: Mapping[str, str]) -> bool:
    cohort = candidate.get("estimate_cohort")
    if not isinstance(cohort, dict):
        return False
    for field, expected in cohort_key.items():
        value = cohort.get(field)
        if value != expected:
            return False
    return True


def _outcome_reference(event: Event) -> dict[str, str]:
    return {
        "event_id": cast(str, event.raw["event_id"]),
        "event_kind": event.kind,
        "event_sha256": event_sha256(event.raw),
    }


def _outcome_duration_s(data: Mapping[str, object]) -> float | None:
    duration = data.get("duration_s")
    if isinstance(duration, (int, float)) and not isinstance(duration, bool):
        return float(duration)
    elapsed = data.get("elapsed_s")
    if isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool):
        return float(elapsed)
    return None


def _outcome_is_censored(data: Mapping[str, object]) -> bool:
    if data.get("timed_out") is True:
        return True
    status = data.get("status")
    return status in {"error", "refused", "timeout"}


def _outcome_is_completed(data: Mapping[str, object]) -> bool:
    if _outcome_is_censored(data):
        return False
    if data.get("verifier_accept") is False:
        return False
    status = data.get("status")
    if status is None:
        return True
    return status == "ok"


def _nearest_rank_percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise EventError("percentile requires at least one value")
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[index]


def _schedule_stream_bounds(
  plan: Mapping[str, object],
  *,
  lower_s: int,
  upper_s: int,
) -> list[dict[str, object]]:
    streams = cast(list[dict[str, object]], plan["streams"])
    return [
        {
            "stream_id": cast(str, stream["stream_id"]),
            "earliest_s": lower_s,
            "latest_s": upper_s,
        }
        for stream in streams
    ]


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
        "stream_bounds": _schedule_stream_bounds(plan, lower_s=lower_s, upper_s=upper_s),
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


def _delivery_estimates_by_id(prefix: Sequence[object]) -> dict[str, dict[str, object]]:
    tips: dict[str, dict[str, object]] = {}
    for item in prefix:
        if not isinstance(item, Event):
            if not isinstance(item, dict):
                continue
            kind = item.get("event")
            data = item.get("data")
        else:
            kind = item.kind
            data = item.data
        if kind != DELIVERY_ESTIMATE_KIND or not isinstance(data, dict):
            continue
        delivery_id = data.get("delivery_id")
        estimate_id = data.get("estimate_id")
        if isinstance(delivery_id, str) and isinstance(estimate_id, str):
            tips[delivery_id] = data
    return tips


def _plan_for_estimate(
    prefix: Sequence[Event], plan_digest: str
) -> Mapping[str, object] | None:
    for event in prefix:
        if event.kind != "organisation.plan.frozen":
            continue
        if event.data.get("plan_digest") == plan_digest:
            return event.data
    return None


def _validate_delivery_estimate_transition(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    tips = _delivery_estimates_by_id(prefix)
    rev0: dict[str, dict[str, object]] = {}
    for item in prefix:
        if item.kind != DELIVERY_ESTIMATE_KIND:
            continue
        data = item.data
        if data.get("revision") == 0:
            rev0[cast(str, data["delivery_id"])] = data

    for candidate in candidates:
        if candidate["event"] != DELIVERY_ESTIMATE_KIND:
            continue
        data = candidate["data"]
        delivery_id = cast(str, data["delivery_id"])
        revision = cast(int, data["revision"])
        plan_digest = cast(str, data["plan_digest"])
        plan = _plan_for_estimate(prefix, plan_digest)
        if plan is None:
            raise EventError(
                "delivery.estimate must reference a matching organisation.plan.frozen digest"
            )

        if revision == 0:
            if delivery_id in rev0:
                raise EventError("delivery.estimate revision zero is append-only")
            derived = derive_delivery_estimate(
                prefix,
                plan=plan,
                delivery_id=delivery_id,
                issued_at=datetime.fromisoformat(cast(str, data["issued_at"])),
                cohort_key=cast(dict[str, str], data["cohort_key"]),
                resource_snapshot_digest=cast(str, data["resource_snapshot_digest"]),
                checkpoint_interval_s=cast(int, data["checkpoint_interval_s"]),
                recovery_allowance_s=cast(int, data["recovery_allowance_s"]),
                not_included=cast(list[str], data["not_included"]),
            )
            if data["analogue_ids"] != derived["analogue_ids"]:
                raise EventError(
                    "outcome-aware cohort selection is refused; analogue_ids must list every "
                    "cohort-matching outcome"
                )
            continue

        predecessor_id = cast(str, data["predecessor_estimate_id"])
        tip = tips.get(delivery_id)
        original = rev0.get(delivery_id)
        if tip is None or original is None:
            raise EventError("delivery.estimate revision zero must exist before reforecast")
        if tip.get("estimate_id") != predecessor_id:
            raise EventError("predecessor_estimate_id must reference the latest estimate")
        if data.get("original_estimate_id") != original.get("estimate_id"):
            raise EventError("original_estimate_id must reference revision zero")

        prior_latest = datetime.fromisoformat(cast(str, tip["latest_at"]))
        issued = datetime.fromisoformat(cast(str, data["issued_at"]))
        if issued > prior_latest:
            raise EventError(
                "delivery.estimate reforecast must be pre-breach; issued_at exceeds prior latest_at"
            )
        new_latest = datetime.fromisoformat(cast(str, data["latest_at"]))
        if new_latest <= prior_latest:
            raise EventError("reforecast must widen or move the delivery window upward")
        tips[delivery_id] = data


def _validate_delivery_claim_ordering(
    prefix: tuple[Event, ...],
    _rejections: tuple[Rejection, ...],
    candidates: tuple[EventPayload, ...],
) -> None:
    rev0 = {
        cast(str, event.data["delivery_id"]): event.data
        for event in prefix
        if event.kind == DELIVERY_ESTIMATE_KIND and event.data.get("revision") == 0
    }
    for candidate in candidates:
        if candidate["event"] != "work_item.opened":
            continue
        data = candidate["data"]
        delivery_id = data.get("delivery_id")
        if not isinstance(delivery_id, str):
            continue
        estimate = rev0.get(delivery_id)
        if estimate is None:
            raise EventError(
                "delivery.estimate revision zero must be durable before a delivery claim"
            )
        for field in ("commitment_digest", "plan_digest"):
            if data.get(field) != estimate.get(field):
                raise EventError(
                    f"delivery claim {field} must match delivery.estimate revision zero"
                )


register_transition_validator(
    (DELIVERY_ESTIMATE_KIND,), _validate_delivery_estimate_transition
)


def _queue_opened(prefix: tuple[Event, ...]) -> Event | None:
    opened = [event for event in prefix if event.kind == REVIEW_QUEUE_OPENED_KIND]
    if not opened:
        return None
    if len(opened) > 1:
        raise EventError("only one review.queue.opened event is permitted per trajectory")
    return opened[0]


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
        if event.kind == CANDIDATE_EXPOSED_KIND and event.data.get("queue_id") == queue_id
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


register_transition_validator(
    (CANDIDATE_EXPOSED_KIND,), _validate_candidate_exposed_transition
)
register_transition_validator(
    (VERIFICATION_OUTCOME_KIND,), _validate_verification_outcome_exposure_transition
)

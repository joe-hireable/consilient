"""`validate` and `read` — the two doors every event passes through.

`validate` refuses anything that must never reach the log and returns the event
otherwise unchanged. It is the one place where the required keys, the schema version,
the timestamp, the actor, the kind-specific contract and the decision protocol are all
demanded at once, and returning the event unchanged is deliberate: validation that
quietly repairs its input is validation nobody can reason about. `_classify_lines` is
its counterpart on the way out — a single classifier splitting raw lines into accepted
events and rejections, so that a reader and a writer can never disagree about what a
given line is. `read` returns both halves for one file.

The decision contract is the heaviest check here and the reason for the ordering above
it. V0-22, V0-23 and V0-24 together require an autonomous decision to record a reversal
path, to give that path a machine-checkable executable shape, and never to claim a class
reserved to the user — all of it before the decision is permitted a consequence, because
a reversal invented afterwards is a story rather than a route back.

`register_transition_validator` binds a pure domain validator to the kinds it governs.
The registry is open on purpose, so a domain can add a rule without this module learning
what the rule is about, and typed on purpose, so nothing can be added that reaches
beyond the prefix it was handed."""

from __future__ import annotations
import hashlib
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from . import effects
from .events_vocabulary import (
    PROTECTED_DECISION_CLASSES,
    USER_ONLY,
    _DECISION_PROTOCOL_MARKERS,
    new_event_id,
)

from .events_authority import (
    _check_budget_contract,
    _check_human_authority,
    _check_usage_contract,
)

from .events_digests import (
    _check_alternatives,
    _check_event_id,
    _check_feedback_contract,
    _decision_digest,
    content_digest,
)

from .events_durability import (
    Event,
    _check_capability_gap_contract,
    _check_dispatch_contract,
    _check_response_rating_ban,
    _check_visibility_contract,
)

from .events_evidence import (
    _check_verification_outcome_contract,
    _check_attempt_contract,
    _check_decision_content,
    _check_evidence_class,
    _check_knowledge_contract,
    _check_measurement_contract,
    _retry_sleep,
)

from .events_fields import (
    _check_acquisition_contract,
    _check_attempt_identity,
    _decision_text,
)

from .events_kinds import (
    ACTION_PROPOSAL_KIND,
    BUDGET_STATE_KIND,
    DECISION_KIND,
    EventError,
    EventPayload,
    REQUIRED,
    SCHEMA_VERSION,
    SPEND_RESERVED_KIND,
    TS,
    _PROTECTED_ADMISSION_CLASSES,
    _READ_RETRIES,
    _canonical_json,
    _check_review_queue_contract,
)

from .events_protocol import (
    _check_binding,
    _check_protocol,
)

from .events_records import (
    TransitionValidator,
    _check_capability_versioned_contract,
    _check_record_contract,
)

from .events_references import (
    Rejection,
    _check_exact_event_reference,
)

from .events_relations import (
    _check_delivery_estimate_contract,
)

from .events_supervision import (
    _check_consent_contract,
    _check_escalation_contract,
    _check_intent_contract,
    _check_promote_contract,
)

from .events_versioning import (
    CapabilityManifest,
    _check_model_change_contract,
)


__all__ = [
    "ACTION_PROPOSAL_KIND",
    "BUDGET_STATE_KIND",
    "CapabilityManifest",
    "DECISION_KIND",
    "Event",
    "EventError",
    "EventPayload",
    "PROTECTED_DECISION_CLASSES",
    "REQUIRED",
    "Rejection",
    "SCHEMA_VERSION",
    "SPEND_RESERVED_KIND",
    "TS",
    "TransitionValidator",
    "USER_ONLY",
    "_DECISION_PROTOCOL_MARKERS",
    "_PROTECTED_ADMISSION_CLASSES",
    "_READ_RETRIES",
    "_canonical_json",
    "_check_acquisition_contract",
    "_check_alternatives",
    "_check_attempt_contract",
    "_check_attempt_identity",
    "_check_binding",
    "_check_budget_contract",
    "_check_capability_gap_contract",
    "_check_capability_versioned_contract",
    "_check_consent_contract",
    "_check_decision_content",
    "_check_delivery_estimate_contract",
    "_check_dispatch_contract",
    "_check_escalation_contract",
    "_check_event_id",
    "_check_evidence_class",
    "_check_exact_event_reference",
    "_check_feedback_contract",
    "_check_human_authority",
    "_check_intent_contract",
    "_check_knowledge_contract",
    "_check_measurement_contract",
    "_check_model_change_contract",
    "_check_promote_contract",
    "_check_protocol",
    "_check_record_contract",
    "_check_response_rating_ban",
    "_check_review_queue_contract",
    "_check_usage_contract",
    "_check_verification_outcome_contract",
    "_check_visibility_contract",
    "_decision_digest",
    "_decision_text",
    "_retry_sleep",
    "canonical_manifest",
    "content_digest",
    "new_event_id",
    "read",
    "register_transition_validator",
    "validate",
]


def canonical_manifest(manifest: CapabilityManifest) -> str:
    return _canonical_json(manifest.to_mapping())


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
        raise EventError(
            f"ts is not a valid calendar timestamp: {event['ts']!r}"
        ) from exc
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
    _check_capability_versioned_contract(event)
    _check_model_change_contract(event)
    _check_budget_contract(event)
    _check_usage_contract(event)
    _check_knowledge_contract(event)
    _check_acquisition_contract(event)
    _check_capability_gap_contract(event)
    _check_intent_contract(event)
    _check_escalation_contract(event)
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


def _prepare_for_append(event: EventPayload) -> EventPayload:
    """Attach one retry-stable identity before validating or attempting durability."""
    if "event_id" not in event:
        event["event_id"] = new_event_id()
    return validate(event)


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
    _decision_digest(data["acceptance_contract_digest"], "acceptance_contract_digest")
    protocol_status = _check_protocol(data["protocol"])
    admission = _check_binding(data["binding"], protected_proposal=protected_proposal)
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
            event_kind = raw.get("event") if isinstance(raw, dict) else None
            rejected.append(
                Rejection(path_label, number, str(exc), content_digest, event_kind)
            )
            continue
        events.append(Event(raw, path_label, number, content_digest))
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
            _retry_sleep(attempt)
    raise EventError(
        f"{path} could not be read after {_READ_RETRIES} attempts: observed access denial "
        f"({last}); it may be held by another process. The trajectory is never partially "
        "reported -- refusing rather than "
        "continuing against an incomplete history."
    )

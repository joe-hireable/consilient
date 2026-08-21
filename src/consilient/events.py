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
import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, cast

# Event shapes vary by kind at this JSON boundary, so values cannot be narrowed further
# without changing the runtime validation contract. Every consumed value is checked below.
EventPayload = dict[str, Any]

SCHEMA_VERSION = 1

REQUIRED = ("v", "ts", "event", "actor", "data")

OUTCOME_KIND = "attempt.outcome"
VERDICT_KIND = "attempt.verdict"
VERDICT_CORRECTION_KIND = "attempt.verdict.correction"
DECISION_KIND = "decision.autonomous"
REVERSAL_KINDS = frozenset({"revert", "command", "inverse"})
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
CAPABILITY_GAP_KIND = "capability.gap"
GAP_FAILURES = frozenset({"failed", "silent", "refused", "not_implemented"})
GAP_CLOSURES = frozenset({"retry", "escalate"})
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

# ADR-0057: sharing is opt-in, one purpose, private, used to improve Consilient only.
# Pinning the set makes bundling a failing test rather than a comment. Expanding it is
# an explicit decision; an existing grant does not become authority for a new purpose.
CONSENT_GRANTED = "consent.granted"
CONSENT_WITHDRAWN = "consent.withdrawn"
CONSENT_KINDS = frozenset({CONSENT_GRANTED, CONSENT_WITHDRAWN})
CONSENT_PURPOSES = frozenset({"improve-consilient"})

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

    _check_budget_contract(event)
    _check_usage_contract(event)
    _check_knowledge_contract(event)
    _check_capability_gap_contract(event)
    _check_attempt_identity(event)
    _check_attempt_contract(event)
    _check_consent_contract(event)
    _check_decision_contract(event)
    _check_response_rating_ban(event)
    _check_feedback_contract(event)
    _check_visibility_contract(event)
    _check_human_authority(event)
    _check_evidence_class(event)
    _check_dispatch_contract(event)
    return event


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


def _check_consent_contract(event: EventPayload) -> None:
    """A consent event names a permitted purpose; a grant states a retention period.

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
    if purpose not in CONSENT_PURPOSES:
        raise EventError(
            f"{kind} must declare purpose as one of {sorted(CONSENT_PURPOSES)}; "
            "ADR-0057 permits sharing only to improve Consilient, and purposes "
            "are not bundled"
        )
    if kind != CONSENT_GRANTED:
        return
    retention = data.get("retention_days")
    if not isinstance(retention, int) or isinstance(retention, bool) or retention <= 0:
        raise EventError(
            f"{kind} must carry retention_days as a positive integer; "
            "a grant with no stated retention is the gap ADR-0057 forbids shipping"
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


def _check_decision_contract(event: EventPayload) -> None:
    """V0-22/23/24: autonomous decisions are reversible and outside user-only classes."""
    if event["event"] != DECISION_KIND:
        return
    data = event["data"]
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

    decision_class = data.get("class")
    if isinstance(decision_class, str) and decision_class in USER_ONLY:
        raise EventError(
            f"decision class {decision_class!r} is reserved to the user (V0-23)"
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
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(canonical(event) + "\n")
    return event


def append(path: Path, event: EventPayload) -> EventPayload:
    """Validate and append. The only writer of the log."""
    validate(event)
    if event["event"] in (BUDGET_STATE_KIND, SPEND_RESERVED_KIND):
        lock = (path.parent / BUDGET_LOCK).resolve()
        if _BUDGET_LOCK_HELD.get() == lock:
            return _write_validated(path, event)
        try:
            with _budget_transaction(path.parent):
                return _write_validated(path, event)
        except FileExistsError as exc:
            raise EventError("the budget trajectory is busy") from exc
    return _write_validated(path, event)


def read(path: Path) -> tuple[list[Event], list[Rejection]]:
    """Every valid event in file order, and every line that was refused.

    A refused line is never silently skipped — it comes back in the second element, and
    the caller must decide what to say about it. The two-tuple is deliberate: it makes the
    quarantine impossible to ignore by accident, which a logged warning would not.
    """
    if not path.exists():
        return [], []
    events: list[Event] = []
    rejected: list[Rejection] = []
    with path.open(encoding="utf-8") as fh:
        for number, line in enumerate(fh, start=1):
            content_digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                rejected.append(
                    Rejection(
                        str(path), number, f"not valid JSON: {exc}", content_digest
                    )
                )
                continue
            try:
                validate(raw)
            except EventError as exc:
                rejected.append(Rejection(str(path), number, str(exc), content_digest))
                continue
            events.append(Event(raw, str(path), number))
    return events, rejected


def read_all(directory: Path) -> tuple[list[Event], list[Rejection]]:
    """Every event across every daily file, ordered by filename then position."""
    events: list[Event] = []
    rejected: list[Rejection] = []
    for path in sorted(directory.glob("*.jsonl")):
        file_events, file_rejected = read(path)
        events.extend(file_events)
        rejected.extend(file_rejected)
    return events, rejected


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

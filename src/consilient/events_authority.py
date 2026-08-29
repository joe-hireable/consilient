"""Who may authorise a thing, and what it is allowed to cost.

V0-18 is the rule this file exists for: an agent may never author a human's decision. An
approval, a consent, a gate lift, a spend authorisation or a β verdict is valid only
when the human principal authored it, and a declared non-local channel cannot deliver
one (V0-28). A human verdict is a verdict and may not be filed as anything else — filing
one under another kind is precisely how a fabricated human-participation claim reaches a
trajectory that then measures β against it. Caller-supplied actor and via metadata does
not admit a capability gate (ADR-0078); metadata is a claim, not an authority.

The money contracts sit with it because they are the same question asked about spend
rather than about judgement. Budget state and reservations are checked before they reach
the trajectory, not after something has been spent against them. A usage figure names
its provenance, and a provider that could not be read reports 'unavailable' and carries
no number, because an empty success reported as zero is worse than a gap that admits it
is one (V0-30). Subscription quota and metered spend are kept apart on purpose
(ADR-0044): they are different facts, and adding them produces a number that is true of
nothing."""

from __future__ import annotations
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from .events_vocabulary import (
    HUMAN_ONLY,
)

from .events_durability import (
    _check_reset,
    _decimal_field,
)

from .events_fields import (
    CONSENT_KINDS,
    _check_provenance,
)

from .events_kinds import (
    BUDGET_RESERVATION_ACTOR,
    BUDGET_STATE_ACTOR,
    BUDGET_STATE_KIND,
    EventError,
    EventPayload,
    FEEDBACK_ANSWERED_KIND,
    METERED_CURRENCY,
    METERED_PROVIDER,
    SPEND_RESERVED_KIND,
    TS,
    USAGE_ACTOR,
    USAGE_KIND,
    USAGE_STATUSES,
)


__all__ = [
    "BUDGET_RESERVATION_ACTOR",
    "BUDGET_STATE_ACTOR",
    "BUDGET_STATE_KIND",
    "CONSENT_KINDS",
    "EventError",
    "EventPayload",
    "FEEDBACK_ANSWERED_KIND",
    "HUMAN_ONLY",
    "METERED_CURRENCY",
    "METERED_PROVIDER",
    "SPEND_RESERVED_KIND",
    "TS",
    "USAGE_ACTOR",
    "USAGE_KIND",
    "USAGE_STATUSES",
    "_check_provenance",
    "_check_reset",
    "_decimal_field",
]


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
            raise EventError(
                f"{kind} ts must use UTC so trajectory order is unambiguous"
            )
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
        raise EventError(
            f"{kind} state_observed_at cannot be normalised to UTC"
        ) from exc
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
        raise EventError(
            f"{USAGE_KIND} ts must use UTC so trajectory order is unambiguous"
        )

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

"""Content addresses, and the identities that are not allowed to repeat.

An event's identity and its content are deliberately different things. `event_sha256`
digests the complete canonical event; `content_digest`, `execution_contract_key`,
`version_digest`'s companions and the decision and estimate digest fields address
particular payloads instead, so two records can be compared on what they say without
reference to when or by whom they were written. Event identity is one spelling of UUIDv4
and only one, so that an identity cannot acquire an alias between a write and its
replay, and a reused identity is refused while the F01 lock still protects the prefix it
would have collided with.

The readings derived from a prefix sit here because they are digests of history rather
than of a payload: how much of the escalation budget a window has already spent, how
long each unit has gone unselected and under which reason, which delivery estimates a
prefix holds and which of those were delivered inside the window they promised.

Task-close feedback is checked here as well — durable so a skip is never re-asked,
skippable so the ask is not coercive, and never collapsed into a composite score, since
achievement and efficiency are separate records and no default composite exists anywhere
(R20/R23)."""

from __future__ import annotations
import hashlib
import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import cast
from .events_vocabulary import (
    FEEDBACK_COMPOSITE_FIELDS,
    _DECISION_PROTOCOL_MARKERS,
    _content_payload,
)

from .events_durability import (
    Event,
    parse_capability_identity,
)

from .events_fields import (
    FEEDBACK_KINDS,
    _check_uuid4,
    _decision_text,
    _digest_json,
    _estimate_non_negative_int,
    _estimate_text,
    _intent_timestamp,
    _sha256_hex,
    canonical,
)

from .events_kinds import (
    ACTION_PROPOSAL_KIND,
    DECISION_KIND,
    DELIVERY_ESTIMATE_KIND,
    DIGEST_RE,
    ESCALATION_ATTEMPTED_KIND,
    ESCALATION_BUDGET,
    ESCALATION_PRECISION_FLOOR,
    ESCALATION_PRECISION_WINDOW,
    ESCALATION_WINDOW,
    EventError,
    EventPayload,
    FEEDBACK_ANSWERED_KIND,
    FEEDBACK_ASKED_KIND,
    GOAL_ACHIEVED,
    INTENT_RECORDED_KIND,
    REVIEW_QUEUE_OPENED_KIND,
    TS,
)


__all__ = [
    "ACTION_PROPOSAL_KIND",
    "DECISION_KIND",
    "DELIVERY_ESTIMATE_KIND",
    "DIGEST_RE",
    "ESCALATION_ATTEMPTED_KIND",
    "ESCALATION_BUDGET",
    "ESCALATION_PRECISION_FLOOR",
    "ESCALATION_PRECISION_WINDOW",
    "ESCALATION_WINDOW",
    "Event",
    "EventError",
    "EventPayload",
    "FEEDBACK_ANSWERED_KIND",
    "FEEDBACK_ASKED_KIND",
    "FEEDBACK_COMPOSITE_FIELDS",
    "FEEDBACK_KINDS",
    "GOAL_ACHIEVED",
    "INTENT_RECORDED_KIND",
    "REVIEW_QUEUE_OPENED_KIND",
    "TS",
    "_DECISION_PROTOCOL_MARKERS",
    "_check_uuid4",
    "_content_payload",
    "_decision_text",
    "_digest_json",
    "_estimate_non_negative_int",
    "_estimate_text",
    "_intent_timestamp",
    "_sha256_hex",
    "canonical",
    "content_digest",
    "decision_protocol_data",
    "event_sha256",
    "execution_contract_key",
    "parse_capability_identity",
]


def content_digest(fields: dict[str, object]) -> str:
    return _digest_json(_content_payload(fields))


def execution_contract_key(fields: dict[str, object]) -> str:
    kind, _name = parse_capability_identity(fields["identity"])
    return _digest_json(
        {
            "interface": fields["interface"],
            "kind": kind,
            "permission_boundary": fields["permission_boundary"],
            "purpose": fields["purpose"],
            "trust_boundary": fields["trust_boundary"],
            "verifier_semantics": fields["verifier_semantics"],
        }
    )


def _check_event_id(value: object) -> None:
    """Accept one spelling of UUIDv4, so IDs cannot gain aliases in replay."""
    _check_uuid4(value, "event_id")


def _nullable_sha256(kind: str, value: object, field: str) -> str | None:
    if value is None:
        return None
    return _sha256_hex(kind, value, field)


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


def _escalation_budget(history: Sequence[Event]) -> int:
    resolved = sorted(
        (
            event
            for event in history
            if event.kind == ESCALATION_ATTEMPTED_KIND
            and event.data["disposition"] == "delivered"
            and event.data["decision_changed"] is not None
        ),
        key=lambda event: _intent_timestamp(
            event.raw["ts"], f"{ESCALATION_ATTEMPTED_KIND} ts"
        ),
    )
    if len(resolved) < ESCALATION_PRECISION_WINDOW:
        return ESCALATION_BUDGET
    window = resolved[-ESCALATION_PRECISION_WINDOW:]
    precision = sum(event.data["decision_changed"] is True for event in window) / len(
        window
    )
    if precision < ESCALATION_PRECISION_FLOOR:
        return ESCALATION_BUDGET // 2
    return ESCALATION_BUDGET


def _delivered_in_window(
    history: Sequence[Event], occurred_at: datetime
) -> list[Event]:
    delivered: list[Event] = []
    for event in history:
        if (
            event.kind != ESCALATION_ATTEMPTED_KIND
            or event.data["disposition"] != "delivered"
        ):
            continue
        elapsed = occurred_at - _intent_timestamp(
            event.raw["ts"], f"{ESCALATION_ATTEMPTED_KIND} ts"
        )
        if timedelta(0) <= elapsed < ESCALATION_WINDOW:
            delivered.append(event)
    return delivered


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


def _decision_digest(value: object, field: str) -> str:
    text = _decision_text(value, field)
    if re.fullmatch(r"[0-9a-f]{64}", text) is None:
        raise EventError(
            f"decision protocol {field} must be a lower-case SHA-256 digest"
        )
    return text


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
        raise EventError(
            "decision protocol only_admissible.rule_refs must be non-empty"
        )
    for index, rule_ref in enumerate(rule_refs):
        _decision_text(rule_ref, f"only_admissible.rule_refs[{index}]")


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


def _check_stream_bounds(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list) or not value:
        raise EventError("stream_bounds must be a non-empty array")
    parsed: list[dict[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise EventError(f"stream_bounds[{index}] must be an object")
        stream_id = _estimate_text(
            item.get("stream_id"), f"stream_bounds[{index}].stream_id"
        )
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


def _queue_opened(prefix: tuple[Event, ...]) -> Event | None:
    opened = [event for event in prefix if event.kind == REVIEW_QUEUE_OPENED_KIND]
    if not opened:
        return None
    if len(opened) > 1:
        raise EventError(
            "only one review.queue.opened event is permitted per trajectory"
        )
    return opened[0]

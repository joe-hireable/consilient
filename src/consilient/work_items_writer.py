"""The only path by which a work-item event reaches the log.

`_event_payload` stamps the schema version, the timestamp and the actor; `validate` puts
the result through the general event schema and then the work-item contract check;
`_append` writes it into the day's file. Every writer in the family — a sealed
conversation turn, a comment, a state record, an opened item, an attempt, a pause, a
completion — goes through that one sequence, so there is no way to append a work-item
event that was never checked.

`check_event_contract` is the single-event gate. It dispatches on the event kind,
refuses a work-item event without a ticket, refuses `human_decision` or `human_verdict`
on any of them — a verdict is a person's to record, not a work item's to claim — and
requires a comment to declare the class of evidence it carries.

`_register_transition_validator` wires the transition rule into the event layer for the
eight kinds it governs, and it runs on import rather than being left to the caller. That
is deliberate: a validator which has to be connected by hand is a validator someone will
forget to connect."""

from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from . import events
from .work_items_vocabulary import (
    COMMENT,
    COMMITTED,
    COMPLETED,
    DEFAULT_ACTOR,
    DISPATCH_CLAIM_SCHEMA,
    INTAKE_ACTOR,
    NATIVE_ATTEMPTED,
    NATIVE_COMMITMENT_PAUSED,
    NATIVE_SCHEMA,
    OPENED,
    PLAN_FROZEN,
    STATE,
    TURN,
    WORK_MODEL_SCHEMA,
    _check_inform_score,
    _opened_schema,
    _string_list,
    _text,
)

from .work_items_contracts import (
    KINDS,
    _check_blocked_overlay,
    _check_native_attempt,
    _check_turn_contract,
    plan_digest,
)

from .work_items_integrity import (
    _check_commitment_contract,
    _check_native_pause,
    _check_work_state,
)

from .work_items_schemas import (
    _check_native_item,
    _check_plan_contract,
    _check_work_model_opened,
)

from .work_items_transition import (
    validate_transition,
)


__all__ = [
    "COMMENT",
    "COMMITTED",
    "COMPLETED",
    "DEFAULT_ACTOR",
    "DISPATCH_CLAIM_SCHEMA",
    "INTAKE_ACTOR",
    "KINDS",
    "NATIVE_ATTEMPTED",
    "NATIVE_COMMITMENT_PAUSED",
    "NATIVE_SCHEMA",
    "OPENED",
    "PLAN_FROZEN",
    "STATE",
    "TURN",
    "WORK_MODEL_SCHEMA",
    "_check_blocked_overlay",
    "_check_commitment_contract",
    "_check_inform_score",
    "_check_native_attempt",
    "_check_native_item",
    "_check_native_pause",
    "_check_plan_contract",
    "_check_turn_contract",
    "_check_work_model_opened",
    "_check_work_state",
    "_opened_schema",
    "_string_list",
    "_text",
    "check_event_contract",
    "comment",
    "complete_item",
    "open_item",
    "pause_native_item",
    "plan_digest",
    "record_native_attempt",
    "record_state",
    "seal_turn",
    "validate",
    "validate_transition",
]


def check_event_contract(event: events.EventPayload) -> None:
    kind = event["event"]
    data = cast(dict[str, Any], event["data"])
    if kind == TURN:
        _check_turn_contract(data)
        return
    if kind == COMMITTED:
        _check_commitment_contract(data)
        return
    if kind == PLAN_FROZEN:
        _check_plan_contract(data)
        return
    if kind == NATIVE_ATTEMPTED:
        _check_native_attempt(data)
        return
    if kind == NATIVE_COMMITMENT_PAUSED:
        _check_native_pause(data)
        return
    if kind not in KINDS:
        return
    ticket = data.get("ticket")
    if not isinstance(ticket, str) or not ticket.strip():
        raise events.EventError("work-item events must carry a non-empty string ticket")
    for field in ("human_decision", "human_verdict"):
        if field in data:
            raise events.EventError(f"work-item events cannot carry {field}")
    if kind == OPENED:
        accountable = data.get("accountable")
        if not isinstance(accountable, str) or not accountable.strip():
            raise events.EventError(
                "work_item.opened must carry a non-empty string accountable"
            )
        schema = _opened_schema(data)
        if schema == DISPATCH_CLAIM_SCHEMA:
            _text(data.get("run_id"), "dispatch claim run_id")
            _string_list(data.get("paths"), "dispatch claim paths")
            _text(data.get("cwd"), "dispatch claim cwd")
            _text(data.get("opened_at"), "dispatch claim opened_at")
            _text(data.get("expires_at"), "dispatch claim expires_at")
        elif schema == NATIVE_SCHEMA:
            _check_native_item(data)
        elif schema == WORK_MODEL_SCHEMA:
            _check_work_model_opened(data)
        elif schema is not None:
            raise events.EventError(f"unsupported item_schema {schema!r}")
    if kind == COMMENT:
        evidence_class = data.get("evidence_class")
        if not isinstance(evidence_class, str) or not evidence_class.strip():
            raise events.EventError(
                "work_item.comment must carry a non-empty evidence_class"
            )
    if kind == STATE:
        _check_work_state(data.get("state"), "state")
        _check_blocked_overlay(data)
    if kind == COMPLETED:
        inform_scores = data.get("inform_scores")
        if inform_scores is not None:
            if not isinstance(inform_scores, list):
                raise events.EventError("inform_scores must be an array when present")
            for index, item in enumerate(inform_scores):
                _check_inform_score(item, index)


def validate(event: object) -> events.EventPayload:
    checked = events.validate(event)
    check_event_contract(checked)
    return checked


def _event_payload(
    kind: str,
    actor: str,
    data: dict[str, Any],
    *,
    ts: str | None = None,
) -> events.EventPayload:
    now = ts or datetime.now(timezone.utc).isoformat()
    event = {
        "v": events.SCHEMA_VERSION,
        "ts": now,
        "event": kind,
        "actor": actor,
        "data": data,
    }
    validate(event)
    return event


def _append(
    log: Path,
    kind: str,
    actor: str,
    data: dict[str, Any],
    *,
    ts: str | None = None,
) -> events.EventPayload:
    event = _event_payload(kind, actor, data, ts=ts)
    return events.append(log / f"{event['ts'][:10]}.jsonl", event)


def seal_turn(
    log: Path,
    *,
    conversation_id: str,
    turn_id: str,
    root_request_turn_id: str,
    role: str,
    text: str,
    transport_authenticated: bool = True,
    transport_channel: str = "chat",
    reply_to_turn_id: str | None = None,
    redactions: list[dict[str, str]] | None = None,
    actor: str = INTAKE_ACTOR,
    ts: str | None = None,
) -> events.EventPayload:
    data: dict[str, Any] = {
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "root_request_turn_id": root_request_turn_id,
        "role": role,
        "text": text,
        "transport": {
            "authenticated": transport_authenticated,
            "channel": transport_channel,
        },
    }
    if reply_to_turn_id is not None:
        data["reply_to_turn_id"] = reply_to_turn_id
    if redactions:
        data["redactions"] = redactions
    return _append(log, TURN, actor, data, ts=ts)


def record_state(
    log: Path,
    *,
    ticket: str,
    state: str,
    actor: str = DEFAULT_ACTOR,
    is_blocked: bool | None = None,
    blocked_reason: str | None = None,
) -> events.EventPayload:
    data: dict[str, Any] = {"ticket": ticket, "state": state}
    if is_blocked is not None:
        data["is_blocked"] = is_blocked
    if blocked_reason is not None:
        data["blocked_reason"] = blocked_reason
    return _append(log, STATE, actor, data)


def open_item(
    log: Path,
    *,
    ticket: str,
    accountable: str,
    actor: str = DEFAULT_ACTOR,
    text: str | None = None,
    extra: dict[str, Any] | None = None,
) -> events.EventPayload:
    data: dict[str, Any] = {"ticket": ticket, "accountable": accountable}
    if text is not None:
        data["text"] = text
    if extra is not None:
        reserved = set(data) | {"human_decision", "human_verdict"}
        collision = reserved & set(extra)
        if collision:
            raise events.EventError(
                f"work_item.opened extra fields may not override {sorted(collision)}"
            )
        data.update(extra)
    return _append(log, OPENED, actor, data)


def record_native_attempt(
    log: Path,
    *,
    ticket: str,
    revision: int,
    plan_digest: str,
    attempt_id: str,
    run_id: str,
    claimed_paths: list[str],
    opened_at: str,
    expires_at: str,
    harness: str,
    model: str,
    family: str,
    pool: str,
    capability_context_digest: str,
    candidate_ordinal: int,
    exposure_state: str,
    predecessor_bindings: list[dict[str, object]],
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> events.EventPayload:
    return _append(
        log,
        NATIVE_ATTEMPTED,
        actor,
        {
            "ticket": ticket,
            "revision": revision,
            "plan_digest": plan_digest,
            "attempt_id": attempt_id,
            "run_id": run_id,
            "claimed_paths": claimed_paths,
            "opened_at": opened_at,
            "expires_at": expires_at,
            "harness": harness,
            "model": model,
            "family": family,
            "pool": pool,
            "capability_context_digest": capability_context_digest,
            "candidate_ordinal": candidate_ordinal,
            "exposure_state": exposure_state,
            "predecessor_bindings": predecessor_bindings,
        },
        ts=ts,
    )


def pause_native_item(
    log: Path,
    *,
    ticket: str,
    revision: int,
    plan_digest: str,
    cause: str,
    actor: str = DEFAULT_ACTOR,
    ts: str | None = None,
) -> events.EventPayload:
    return _append(
        log,
        NATIVE_COMMITMENT_PAUSED,
        actor,
        {
            "ticket": ticket,
            "revision": revision,
            "plan_digest": plan_digest,
            "cause": cause,
        },
        ts=ts,
    )


def comment(
    log: Path,
    *,
    ticket: str,
    text: str,
    evidence_class: str | None = None,
    actor: str = DEFAULT_ACTOR,
) -> events.EventPayload:
    data = {"ticket": ticket, "text": text}
    if evidence_class is not None:
        data["evidence_class"] = evidence_class
    return _append(
        log,
        COMMENT,
        actor,
        data,
    )


def complete_item(
    log: Path,
    *,
    ticket: str,
    actor: str = DEFAULT_ACTOR,
    extra: dict[str, Any] | None = None,
) -> events.EventPayload:
    data: dict[str, Any] = {"ticket": ticket}
    if extra is not None:
        reserved = set(data)
        collision = reserved & set(extra)
        if collision:
            raise events.EventError(
                f"work_item.completed extra fields may not override {sorted(collision)}"
            )
        data.update(extra)
    return _append(log, COMPLETED, actor, data)


def _register_transition_validator() -> None:
    events.register_transition_validator(
        (
            TURN,
            COMMITTED,
            PLAN_FROZEN,
            OPENED,
            STATE,
            COMPLETED,
            NATIVE_ATTEMPTED,
            NATIVE_COMMITMENT_PAUSED,
        ),
        validate_transition,
    )

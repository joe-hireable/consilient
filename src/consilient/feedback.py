"""R20/R23 task-close feedback events.

This increment records durable asks, declines and answers, and decides whether a task
may be asked once. The three-question close surface and the pre-committed goal record
are out of scope because no product surface exists to render them yet.

The explicit user-set weighting exception is also unbuilt: no weighting-record event
kind exists, so this module computes no composite of achievement and cost.
"""

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Literal

from . import events as event_schema
from .events import Event

_ACTOR = "consilient.feedback"


def should_ask(task_id: str, events: Iterable[Event]) -> bool:
    """Return whether this task has no durable feedback disposition."""
    return not any(
        event.kind in event_schema.FEEDBACK_KINDS
        and event.data.get("task_id") == task_id
        for event in events
    )


def _build(kind: str, actor: str, data: dict[str, object]) -> event_schema.EventPayload:
    payload: event_schema.EventPayload = {
        "v": event_schema.SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": kind,
        "actor": actor,
        "data": data,
    }
    return event_schema.validate(payload)


def record_ask(task_id: str, goal_text: str) -> event_schema.EventPayload:
    """Build and validate the durable record that a task was asked once."""
    return _build(
        event_schema.FEEDBACK_ASKED_KIND,
        _ACTOR,
        {"task_id": task_id, "goal_text": goal_text},
    )


def record_decline(task_id: str) -> event_schema.EventPayload:
    """Build and validate a consequence-free skip."""
    return _build(
        event_schema.FEEDBACK_DECLINED_KIND,
        _ACTOR,
        {"task_id": task_id},
    )


def record_answer(
    task_id: str,
    goal_achieved: Literal["fully", "partially", "no"],
    *,
    principal: str,
    missing: str | None = None,
    better_approach: str | None = None,
) -> event_schema.EventPayload:
    """Build and validate the principal's task-level outcome report."""
    data: dict[str, object] = {
        "task_id": task_id,
        "goal_achieved": goal_achieved,
        "principal": principal,
        "via": "cli",
    }
    if missing is not None:
        data["missing"] = missing
    if better_approach is not None:
        data["better_approach"] = better_approach
    return _build(event_schema.FEEDBACK_ANSWERED_KIND, principal, data)

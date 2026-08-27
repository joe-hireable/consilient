"""One ambient surface with a named element budget, and a demand record.

A generated surface answers the question actually asked. The ambient set is the
questions shown without being asked. Promotion into that set is earned only by
recorded `surface.request` events — never by recollection or by anticipating
which widgets will matter. See docs/20-design/surfaces-on-demand-2026-08-24.md.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .events import Event, EventError, EventPayload, SCHEMA_VERSION, append

REQUEST_KIND = "surface.request"
REPEATED_ASKS = 2

# The observe-only increment that already ships. Adding an identifier requires
# removing one, or renaming test_ambient_surface_element_budget_is_3.
AMBIENT_ELEMENTS: tuple[str, ...] = ("gates", "beta", "needs_you")


@dataclass(frozen=True)
class AmbientElement:
    """One ambient slot. Age is a running counter; this module cannot refresh."""

    id: str
    as_of: datetime
    age: str


def age_counter(as_of: datetime, now: datetime) -> str:
    """Elapsed age as a running counter. A timestamp or a 'stale' badge is not this."""
    if not isinstance(as_of, datetime) or not isinstance(now, datetime):
        raise ValueError("as_of and now must be datetimes")
    if as_of.tzinfo is None or now.tzinfo is None:
        raise ValueError("as_of and now must carry an explicit timezone")
    elapsed = int((now - as_of).total_seconds())
    if elapsed < 0:
        raise ValueError("as_of is after now")
    hours, rem = divmod(elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours}h {minutes}m {seconds}s"


def render_ambient(*, as_of: datetime, now: datetime) -> tuple[AmbientElement, ...]:
    """Render the ambient set. Every element carries age; nothing here is live."""
    age = age_counter(as_of, now)
    return tuple(
        AmbientElement(id=element_id, as_of=as_of, age=age)
        for element_id in AMBIENT_ELEMENTS
    )


def request_surface(
    log: Path,
    *,
    question: str,
    actor: str,
) -> EventPayload:
    """Record one surface request. The question, when, and who are the whole body.

    `ts` is the clock at append, not an author-supplied belief: events.py refuses
    a stamp more than fifteen minutes from now. The request happens when it is written.
    """
    asked = question.strip()
    if not asked:
        raise EventError("surface.request must carry a non-empty question")
    who = actor.strip()
    if not who:
        raise EventError("surface.request actor must be a non-empty string")
    event: EventPayload = {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": REQUEST_KIND,
        "actor": who,
        "data": {"question": asked},
    }
    return append(log, event)


def _trajectory_events(events: Iterable[object]) -> Iterable[Event]:
    for event in events:
        if not isinstance(event, Event):
            raise TypeError("promotion evidence must be a trajectory event")
        yield event


def demand_for(question: str, events: Iterable[object]) -> int:
    """Count recorded requests for this exact question. No other kind of row counts."""
    asked = question.strip()
    count = 0
    for event in _trajectory_events(events):
        if _is_recorded_request(event, asked):
            count += 1
    return count


def _is_recorded_request(event: Event, question: str) -> bool:
    """Exclude malformed hand-built rows; `read()` has already validated real rows."""
    try:
        kind = event.kind
        actor = event.actor
        recorded_question = event.data.get("question")
    except (AttributeError, KeyError, TypeError):
        return False
    return (
        kind == REQUEST_KIND
        and isinstance(actor, str)
        and actor == actor.strip()
        and bool(actor)
        and isinstance(recorded_question, str)
        and bool(recorded_question)
        and recorded_question == question
    )


def promotion_admissible(question: str, events: Iterable[object]) -> bool:
    """True only when the demand record shows the question asked repeatedly.

    Does not mutate AMBIENT_ELEMENTS. Recollection is not an argument this accepts.
    """
    return demand_for(question, events) >= REPEATED_ASKS

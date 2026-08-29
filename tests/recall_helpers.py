"""Event builders shared by the recall tests.

`_event` fills the schema fields every projector test needs and `_ts` keeps ordering
explicit, so each test states only the part of the payload it is actually about. The two
oversized builders are fixtures with a purpose rather than convenience wrappers: each
exceeds the 8,000-character pack budget on its own, which is precisely the condition
under which selection used to drop an event entirely instead of summarising it. They are
used both by the selection tests and by the assembly tests, so they live here rather
than in either."""

from datetime import datetime, timedelta, timezone
from consilient.events import Event, SCHEMA_VERSION


def _ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def _event(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "v": SCHEMA_VERSION,
        "ts": _ts(),
        "event": "test.event",
        "actor": "agent",
        "data": {},
    }
    base.update(over)
    return base


def _oversized_dispatch_outcome(
    *, event_id: str, padding: int = 9000, **data: object
) -> Event:
    payload: dict[str, object] = {
        "supervised": True,
        "unit": "Z07",
        "harness": "cursor-composer",
        "status": "failed",
        "reason": "START_FAILED -- no artefact within the start window",
        "task": "make the recall pack carry something",
        "padding": "x" * padding,
    }
    payload.update(data)
    return Event(
        _event(
            event_id=event_id,
            event="dispatch.outcome",
            actor="consilient.dispatch",
            data=payload,
        )
    )


def _oversized_capability_gap(*, event_id: str, padding: int = 9000) -> Event:
    return Event(
        _event(
            event_id=event_id,
            event="capability.gap",
            actor="consilient.dispatch",
            data={
                "asked": "assemble a brief",
                "attempted": "recall.pack_events",
                "failure": "not_implemented",
                "detail": "selection dropped every candidate",
                "repair": "project a summary when the full event does not fit",
                "run_id": "20260825T181844-f65a16fcf4",
                "source": "dispatch.outcome",
                "closure": "escalate",
                "padding": "y" * padding,
            },
        )
    )

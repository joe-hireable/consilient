"""Work-item events in the authoritative trajectory."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import events

DEFAULT_ACTOR = "consilient.work"
OPENED = "work_item.opened"
COMMENT = "work_item.comment"
COMPLETED = "work_item.completed"
KINDS = frozenset({OPENED, COMMENT, COMPLETED})


def validate(event: object) -> events.EventPayload:
    checked = events.validate(event)
    if checked["event"] in KINDS:
        ticket = checked["data"].get("ticket")
        if not isinstance(ticket, str) or not ticket.strip():
            raise events.EventError("work-item events must carry a non-empty string ticket")
        for field in ("human_decision", "human_verdict"):
            if field in checked["data"]:
                raise events.EventError(f"work-item events cannot carry {field}")
    if checked["event"] == OPENED:
        accountable = checked["data"].get("accountable")
        if not isinstance(accountable, str) or not accountable.strip():
            raise events.EventError(
                "work_item.opened must carry a non-empty string accountable"
            )
    if checked["event"] == COMMENT:
        evidence_class = checked["data"].get("evidence_class")
        if not isinstance(evidence_class, str) or not evidence_class.strip():
            raise events.EventError(
                "work_item.comment must carry a non-empty evidence_class"
            )
    return checked


def _append(
    log: Path, kind: str, actor: str, data: dict[str, Any]
) -> events.EventPayload:
    now = datetime.now(timezone.utc)
    event = {
        "v": events.SCHEMA_VERSION,
        "ts": now.isoformat(),
        "event": kind,
        "actor": actor,
        "data": data,
    }
    validate(event)
    return events.append(log / f"{now.date().isoformat()}.jsonl", event)


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
        # Extra fields extend an opened item (a dispatch claim's paths and expiry, for
        # instance); they may never restate the item's identity or smuggle in human
        # authority. validate() forbids the authority fields again below.
        reserved = set(data) | {"human_decision", "human_verdict"}
        collision = reserved & set(extra)
        if collision:
            raise events.EventError(
                f"work_item.opened extra fields may not override {sorted(collision)}"
            )
        data.update(extra)
    return _append(log, OPENED, actor, data)


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
    log: Path, *, ticket: str, actor: str = DEFAULT_ACTOR
) -> events.EventPayload:
    return _append(log, COMPLETED, actor, {"ticket": ticket})

"""Admit inbound transport payloads as untrusted proposals (ADR-0041).

Slack, Twilio, email, ClickUp and the rest are projections. An inbound message
becomes a `transport.proposal` or it is refused. It cannot become a human
verdict. Dedup is on the four-tuple (transport_name, channel_id, message_id, text).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .events import HUMAN_ONLY, SCHEMA_VERSION, EventPayload, read_all

PROPOSAL_KIND = "transport.proposal"
PROPOSAL_ACTOR = "consilient.transport"
REQUIRED = ("transport_name", "channel_id", "message_id", "text")
# Declared third-party channels. A payload from one of these that claims via=cli
# is the EXP-16 failure: an agent holding a shared token laundering itself as local.
UNTRUSTED_CHANNELS = frozenset(
    {"slack", "twilio", "email", "webhook", "clickup", "linear", "sms"}
)
_VERDICT_FIELDS = frozenset({"human_decision", "human_verdict", "principal"})
_VERDICT_KINDS = HUMAN_ONLY | frozenset(
    {"attempt.verdict", "approval", "gate_lift", "spend_authorisation", "verdict"}
)


class TransportAdmitError(ValueError):
    """A payload that must not enter the trajectory."""


def _as_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TransportAdmitError(f"{name} must be a non-empty string")
    return value.strip()


def looks_like_verdict(payload: Mapping[str, Any]) -> str | None:
    kind = payload.get("event")
    if isinstance(kind, str) and kind.strip().casefold() in {
        item.casefold() for item in _VERDICT_KINDS
    }:
        return kind.strip()
    nested = payload.get("data")
    if isinstance(nested, Mapping):
        decision = nested.get("human_decision")
        if isinstance(decision, str) and decision.strip().casefold() in {
            item.casefold() for item in HUMAN_ONLY
        }:
            return decision.strip()
        if "human_verdict" in nested:
            return "verdict"
    for field in _VERDICT_FIELDS:
        if field in payload:
            return field
    return None


def _dedup_key(payload: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        _as_text(payload["transport_name"], "transport_name"),
        _as_text(payload["channel_id"], "channel_id"),
        _as_text(payload["message_id"], "message_id"),
        _as_text(payload["text"], "text"),
    )


def already_recorded(log_dir: Path, key: tuple[str, str, str, str]) -> bool:
    if not log_dir.is_dir():
        return False
    events, _rejected = read_all(log_dir)
    for event in events:
        if event.raw.get("event") != PROPOSAL_KIND:
            continue
        data = event.raw.get("data")
        if not isinstance(data, dict):
            continue
        try:
            existing = (
                str(data["transport_name"]).strip(),
                str(data["channel_id"]).strip(),
                str(data["message_id"]).strip(),
                str(data["text"]).strip(),
            )
        except KeyError:
            continue
        if existing == key:
            return True
    return False


def admit(
    payload: Mapping[str, Any], *, log_dir: Path | None = None
) -> EventPayload | None:
    """Return a `transport.proposal` event, None if duplicate, or raise."""
    if not isinstance(payload, Mapping):
        raise TransportAdmitError("payload must be an object")
    missing = [name for name in REQUIRED if name not in payload]
    if missing:
        raise TransportAdmitError(f"payload missing {', '.join(missing)}")
    verdict = looks_like_verdict(payload)
    if verdict is not None:
        raise TransportAdmitError(
            f"refusing verdict-shaped payload ({verdict!r}): untrusted transports "
            "cannot deliver human decisions (ADR-0041, V0-18/V0-28)"
        )
    transport = _as_text(payload["transport_name"], "transport_name")
    via = payload.get("via")
    if isinstance(via, str) and via.strip().casefold() == "cli":
        if transport.casefold() in UNTRUSTED_CHANNELS:
            raise TransportAdmitError(
                f"via=cli on a {transport} payload is refused: that is how a shared "
                "token launders an agent as the principal (EXP-16)"
            )
        raise TransportAdmitError(
            "transport.proposal cannot declare via=cli; local CLI is not a transport"
        )
    key = _dedup_key(payload)
    if log_dir is not None and already_recorded(log_dir, key):
        return None
    now = datetime.now(timezone.utc).isoformat()
    event: EventPayload = {
        "v": SCHEMA_VERSION,
        "ts": now,
        "event": PROPOSAL_KIND,
        "actor": PROPOSAL_ACTOR,
        "data": {
            "transport_name": key[0],
            "channel_id": key[1],
            "message_id": key[2],
            "text": key[3],
            "via": transport.casefold(),
        },
    }
    return event

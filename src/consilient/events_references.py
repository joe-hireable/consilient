"""One event pointing at another, and what to do when the target is not there.

`resolve_reference` is the single route from a reference to the earlier event it names.
It returns that event, or it reports an honest legacy row — a schema-v1 line identified
only by kind and content hash, which cannot be resolved and must not be pretended into a
resolution. The exact-reference check is stricter: an event_id or nothing, so that a
newer edge cannot quietly inherit the looseness the old schema had to tolerate.

`Rejection` is the other half of the same idea. A line the reader refuses is kept as a
rejection rather than raising through the read, so a refusal is reported and countable
and a partly corrupt log stays inspectable instead of becoming a stack trace. Refusing
loudly and continuing is the behaviour that lets a trajectory be audited; refusing
fatally would mean the only logs that can be read are the ones with nothing wrong with
them.

The readings that need resolution sit alongside — the units starved as of the end of a
prefix, reported once per run rather than once per tick, and an escalation attempt's
disposition derived from authoritative event timestamps instead of from anybody's claim
about what happened."""

from __future__ import annotations
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import cast
from .events_vocabulary import (
    _content_payload,
)

from .events_digests import (
    _check_event_id,
    _decision_digest,
    _delivered_in_window,
    _escalation_budget,
    _estimate_digest_field,
    _intent_runs,
    content_digest,
    event_sha256,
    execution_contract_key,
)

from .events_durability import (
    Event,
)

from .events_fields import (
    ESCALATION_CLASSES,
    _check_uuid4,
    _decision_text,
    _digest_json,
    _estimate_text,
    _intent_timestamp,
)

from .events_kinds import (
    ESCALATION_ATTEMPTED_KIND,
    EventError,
    EventPayload,
    INTENT_STARVED_KIND,
    STARVATION_TICKS,
    STARVATION_WINDOW,
)


__all__ = [
    "ESCALATION_ATTEMPTED_KIND",
    "ESCALATION_CLASSES",
    "Event",
    "EventError",
    "EventPayload",
    "INTENT_STARVED_KIND",
    "Rejection",
    "STARVATION_TICKS",
    "STARVATION_WINDOW",
    "_check_event_id",
    "_check_uuid4",
    "_content_payload",
    "_decision_digest",
    "_decision_text",
    "_delivered_in_window",
    "_digest_json",
    "_escalation_budget",
    "_estimate_digest_field",
    "_estimate_text",
    "_intent_runs",
    "_intent_timestamp",
    "content_digest",
    "event_sha256",
    "execution_contract_key",
    "resolve_reference",
    "starvation",
    "version_digest",
]


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

    `event_kind` is the rejected line's own `"event"` field when it could be read at all
    (`None` for a line that was not even valid JSON, or that parsed to something with no
    such field). A01's review found `receipt_chain_validator` refusing to start a
    write-ahead intent in any log directory that already held one quarantined line of *any*
    kind -- a rejected `note.made` line blocked an unrelated `effect.intent`. `event_kind`
    lets that validator refuse only on a rejection that is actually part of its own chain.
    """

    path: str
    line: int
    reason: str
    content_digest: str = ""
    event_kind: str | None = None


def version_digest(fields: dict[str, object]) -> str:
    payload = _content_payload(fields)
    payload["content_digest"] = fields.get("content_digest") or content_digest(fields)
    payload["execution_contract_key"] = fields.get(
        "execution_contract_key"
    ) or execution_contract_key(fields)
    payload["status"] = fields["status"]
    return _digest_json(payload)


def _check_event_reference(
    reference: object, owner: str, relation: str, expected_kind: str
) -> dict[str, str]:
    fields = {"event_id", "event_kind", "event_sha256"}
    if not isinstance(reference, dict) or set(reference) != fields:
        raise EventError(f"{owner} {relation} must be an exact F03 event reference")
    _check_event_id(reference["event_id"])
    if reference["event_kind"] != expected_kind:
        raise EventError(f"{owner} {relation} must reference {expected_kind} events")
    digest = reference["event_sha256"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise EventError(
            f"{owner} {relation} event_sha256 must be 64 lower-case hex characters"
        )
    return {
        "event_id": reference["event_id"],
        "event_kind": reference["event_kind"],
        "event_sha256": digest,
    }


def starvation(
    prefix: Sequence[Event],
    *,
    ticks: int = STARVATION_TICKS,
    window: timedelta = STARVATION_WINDOW,
) -> list[EventPayload]:
    """The units starved as of the end of `prefix`, each reported once per run.

    Both floors must be crossed - "6 ticks or 60 minutes, whichever is longer". Six ticks
    inside a minute is a busy scheduler, not a starved unit.
    """
    reported = {
        (event.data["unit"], event.data["reason"], event.data["since"])
        for event in prefix
        if event.kind == INTENT_STARVED_KIND
    }
    starved: list[EventPayload] = []
    for unit, (reason, first_ts, last_ts, count) in sorted(
        _intent_runs(prefix).items()
    ):
        if count < ticks or last_ts - first_ts < window:
            continue
        since = first_ts.isoformat()
        if (unit, reason, since) in reported:
            continue
        starved.append({"unit": unit, "reason": reason, "ticks": count, "since": since})
    return starved


def _escalation_disposition(
    history: Sequence[Event], candidate: EventPayload
) -> tuple[str, str | None]:
    """Derive one attempt's disposition from authoritative event timestamps."""
    data = candidate["data"]
    escalation_class = data["escalation_class"]
    if escalation_class not in ESCALATION_CLASSES:
        return "refused", "out_of_set_class"
    occurred_at = _intent_timestamp(candidate["ts"], f"{ESCALATION_ATTEMPTED_KIND} ts")
    delivered = _delivered_in_window(history, occurred_at)
    if any(event.data["root_cause"] == data["root_cause"] for event in delivered):
        return "refused", "duplicate_root_cause"
    if len(delivered) >= _escalation_budget(history):
        return "refused", "budget_exhausted"
    return "delivered", None


def _check_exact_event_reference(reference: object, field: str) -> None:
    required = {"event_id", "event_kind", "event_sha256"}
    if not isinstance(reference, dict) or set(reference) != required:
        raise EventError(
            f"decision protocol {field} must be an exact F03 event reference"
        )
    _check_event_id(reference["event_id"])
    _decision_text(reference["event_kind"], f"{field}.event_kind")
    _decision_digest(reference["event_sha256"], f"{field}.event_sha256")


def resolve_reference(
    reference: object, events: Iterable[Event], *, before: Event | None = None
) -> Event | str:
    """Resolve one exact reference to an earlier event, or mark a real legacy row.

    A legacy reference may identify its stored schema-v1 event only by kind and
    complete-content hash; it is explicitly unmeasured because it lacks an ID.
    Any other missing or malformed modern reference fails closed.
    """
    if not isinstance(reference, dict):
        raise EventError("event reference must be an object")
    kind = reference.get("event_kind")
    digest = reference.get("event_sha256")
    if not isinstance(kind, str) or not kind:
        raise EventError("event reference must carry event_kind as a non-empty string")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise EventError(
            "event reference must carry event_sha256 as 64 lower-case hex characters"
        )

    ordered = tuple(events)
    event_id = reference.get("event_id")
    if event_id is None:
        legacy = [
            event
            for event in ordered
            if "event_id" not in event.raw
            and event.kind == kind
            and event_sha256(event.raw) == digest
        ]
        if len(legacy) == 1:
            return "unmeasured"
        raise EventError("event reference is missing event_id")
    _check_event_id(event_id)
    matching = [event for event in ordered if event.raw.get("event_id") == event_id]
    if not matching:
        raise EventError(f"event reference {event_id!r} is missing")
    if len(matching) != 1:
        raise EventError(f"event reference {event_id!r} is not unique")
    target = matching[0]
    if before is not None:
        try:
            before_index = next(
                index for index, event in enumerate(ordered) if event is before
            )
        except StopIteration as exc:
            raise EventError(
                "reference consumer is absent from trajectory order"
            ) from exc
        target_index = next(
            index for index, event in enumerate(ordered) if event is target
        )
        if target_index >= before_index:
            raise EventError(
                f"event reference {event_id!r} is not earlier than its consumer"
            )
    if target.kind != kind:
        raise EventError(f"event reference {event_id!r} has mismatched event_kind")
    if event_sha256(target.raw) != digest:
        raise EventError(f"event reference {event_id!r} has mismatched event_sha256")
    return target


def _check_estimate_cohort(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise EventError("cohort_key must be an object")
    parsed: dict[str, str] = {}
    for field in (
        "artefact_kind",
        "verifier_contract_digest",
        "size_band",
        "route_capability_class",
    ):
        parsed[field] = _estimate_text(value.get(field), f"cohort_key.{field}")
        if field.endswith("_digest"):
            _estimate_digest_field(parsed[field], f"cohort_key.{field}")
    return parsed


def _check_estimate_analogue(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise EventError("analogue_ids must be an array")
    parsed: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise EventError(f"analogue_ids[{index}] must be an object")
        event_id = _estimate_text(
            item.get("event_id"), f"analogue_ids[{index}].event_id"
        )
        _check_uuid4(event_id, f"analogue_ids[{index}].event_id")
        event_kind = _estimate_text(
            item.get("event_kind"), f"analogue_ids[{index}].event_kind"
        )
        event_digest = _estimate_digest_field(
            item.get("event_sha256"), f"analogue_ids[{index}].event_sha256"
        )
        parsed.append(
            {
                "event_id": event_id,
                "event_kind": event_kind,
                "event_sha256": event_digest,
            }
        )
    return parsed


def _outcome_reference(event: Event) -> dict[str, str]:
    return {
        "event_id": cast(str, event.raw["event_id"]),
        "event_kind": event.kind,
        "event_sha256": event_sha256(event.raw),
    }

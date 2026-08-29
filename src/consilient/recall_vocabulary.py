"""The names and fragments every recall pack is spelled with.

Holds the constant vocabulary of a pack — the receipt marker, the two projection forms,
the closed set of omission reasons, and the field names that mark an event as
qualification, sentinel or card-private — together with the per-event facts read
straight off a raw trajectory: a stable identifier, whether an event has been
superseded, whether its retention class denies permission to quote it, and the
protection rank that says how late in an eviction it may be dropped.

Protection is ranked rather than boolean because the commitment contract is not flat.
The current revision of a commitment outranks an older one, a turn linked to a
commitment outranks loose history, and a correction, a recorded dissent or an unresolved
principal authority outranks ordinary events. Nothing here decides what a pack contains:
these functions answer a question about one event at a time and hand the answer upward.

The markdown fragments — the header, the two omission footers, and the full and summary
renderings of a single event — and the continuation cursor payload live here for the
same reason. They are text, not policy. A fragment prints the numbers it is handed and
never chooses which events survive."""

from __future__ import annotations
import json
from collections.abc import Sequence
from dataclasses import dataclass
from .events import (
    CAPABILITY_GAP_KIND,
    DECISION_KIND,
    OUTCOME_KIND,
    RECORD_CAPTURED_KIND,
    VERIFICATION_OUTCOME_KIND,
    VERDICT_CORRECTION_KIND,
    VERDICT_KIND,
    Event,
    Rejection,
    canonical,
    event_sha256,
)
from . import promote
from .work_items import COMMITTED, TURN

RECEIPT_MARKER = "consilient:recall-receipt:v1"

RECEIPT_END = "\n-->"

FULL_FORM = "full"

SUMMARY_FORM = "summary"

OPTIONAL_RECEIPT_FIELDS = frozenset({"selected_forms"})

_EMPTY_WHILE_AVAILABLE = "empty_while_available"

# A summary that inlines an 8 KB field is not a summary. Live dispatch.outcome
# events have no `unit`; `task` is the whole brief (median 5,079 characters,
# 677 of 1,476 over the pack bound on 26 August 2026). [measured]
_SUMMARY_FIELD_CHARS = 240

OMISSION_REASONS = frozenset(
    {
        "irrelevant",
        "superseded",
        "permission",
        "context_bound",
        "corrupt",
        "qualification",
        "sentinel",
        "card_private",
    }
)

QUALIFICATION_FIELDS = promote.privileged_fields() | frozenset(
    {
        "qualification_batch_id",
        "qualification_rule_digest",
    }
)

SENTINEL_FIELDS = frozenset(
    {
        "sentinel_batch_id",
        "sentinel_score",
        "sentinel_items",
        "sentinel_digest",
        "drift_sentinel",
    }
)

CARD_PRIVATE_FIELDS = frozenset(
    {
        "owner_card",
        "proposal_card",
        "card_text",
        "card_sentences",
        "privileged_owner_projection",
        "before_behaviour",
        "after_behaviour",
    }
)

ALWAYS_INCLUDE_KINDS = frozenset(
    {
        "dispatch.outcome",
        "dispatch.refused",
        "dispatch.fanout",
        OUTCOME_KIND,
        VERIFICATION_OUTCOME_KIND,
        VERDICT_KIND,
        VERDICT_CORRECTION_KIND,
        DECISION_KIND,
        CAPABILITY_GAP_KIND,
        COMMITTED,
        "ticket.completed",
    }
)

_EMPTY_PACK = "# Recall pack\n\nNo events in log.\n"

_NO_MATCH_PACK = "# Recall pack\n\nNo events match query.\n"


@dataclass(frozen=True)
class _Omitted:
    id: str
    reason: str


@dataclass(frozen=True)
class Omission:
    event_id: str | None
    event_kind: str
    reason: str
    protected: bool


def _query_tokens(query: str) -> tuple[str, ...]:
    return tuple(token.lower() for token in query.split() if token)


def _normalise_query(query: str) -> str:
    return " ".join(query.lower().split())


def _prefix_digest(events: Sequence[Event]) -> str:
    return promote.digest("\n".join(canonical(event.raw) for event in events))


def _stable_id(event: Event) -> str:
    event_id = event.raw.get("event_id")
    if isinstance(event_id, str):
        return event_id
    if event.path is not None and event.line is not None:
        return f"line:{event.path}:{event.line}"
    return f"sha256:{event_sha256(event.raw)}"


def _rejection_id(rejection: Rejection) -> str:
    return f"reject:{rejection.path}:{rejection.line}"


def _searchable_text(event: Event) -> str:
    return json.dumps(event.raw, ensure_ascii=False, sort_keys=True)


def _permission_denied(event: Event) -> bool:
    if event.kind != RECORD_CAPTURED_KIND:
        return False
    return event.data.get("retention_class") == "private"


def _collect_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key))
            keys.update(_collect_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_collect_keys(item))
    return keys


def _superseded_event_ids(events: Sequence[Event]) -> frozenset[str]:
    superseded: set[str] = set()
    for event in events:
        if event.kind != RECORD_CAPTURED_KIND:
            continue
        supersedes = event.data.get("supersedes")
        if not isinstance(supersedes, list):
            continue
        for reference in supersedes:
            if isinstance(reference, dict) and isinstance(
                reference.get("event_id"), str
            ):
                superseded.add(reference["event_id"])
    return frozenset(superseded)


def _has_dissent(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            (str(key).casefold() == "dissent" and bool(item)) or _has_dissent(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_has_dissent(item) for item in value)
    return False


def _has_unresolved_authority(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    authority = value.get("authority_ref")
    if isinstance(authority, dict) and authority.get("kind") == "principal_required":
        return True
    return any(_has_unresolved_authority(item) for item in value.values())


def _linked_turns(events: Sequence[Event]) -> set[tuple[str, str]]:
    linked: set[tuple[str, str]] = set()
    for event in events:
        if event.kind != COMMITTED:
            continue
        conversation_id = event.data.get("conversation_id")
        turn_ids = event.data.get("source_turn_ids")
        if not isinstance(conversation_id, str) or not isinstance(turn_ids, list):
            continue
        linked.update(
            (conversation_id, turn_id)
            for turn_id in turn_ids
            if isinstance(turn_id, str)
        )
    return linked


def _active_commitments(events: Sequence[Event]) -> set[int]:
    active: dict[str, tuple[int, int]] = {}
    for index, event in enumerate(events):
        if event.kind != COMMITTED:
            continue
        commitment_id = event.data.get("commitment_id")
        revision = event.data.get("revision")
        if not isinstance(commitment_id, str) or not isinstance(revision, int):
            continue
        current = active.get(commitment_id)
        if current is None or revision > current[0]:
            active[commitment_id] = (revision, index)
    return {index for _, index in active.values()}


def _protection_ranks(events: Sequence[Event]) -> tuple[int, ...]:
    active = _active_commitments(events)
    linked = _linked_turns(events)
    ranks: list[int] = []
    for index, event in enumerate(events):
        data = event.data
        turn_key = (data.get("conversation_id"), data.get("turn_id"))
        if index in active:
            rank = 4
        elif event.kind == COMMITTED or (
            event.kind == TURN
            and isinstance(turn_key[0], str)
            and isinstance(turn_key[1], str)
            and turn_key in linked
        ):
            rank = 3
        elif (
            event.kind in ALWAYS_INCLUDE_KINDS
            or event.kind.endswith(".correction")
            or _has_dissent(data)
            or _has_unresolved_authority(data)
        ):
            rank = 2
        else:
            rank = 0
        ranks.append(rank)
    return tuple(ranks)


def _format_event(event: Event) -> str:
    raw = event.raw
    lines = [f"### `{raw['event']}` @ `{raw['ts']}`", ""]
    for key in ("v", "ts", "event", "event_id", "actor"):
        if key not in raw:
            continue
        value = raw[key]
        if isinstance(value, str):
            lines.append(f"- **{key}**: `{value}`")
        else:
            lines.append(
                f"- **{key}**: `{json.dumps(value, ensure_ascii=False, sort_keys=True)}`"
            )
    data = raw["data"]
    lines.extend(
        (
            "- **data**:",
            "```json",
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        )
    )
    return "\n".join(lines)


def _format_summary(event: Event, projection: dict[str, str]) -> str:
    raw = event.raw
    lines = [f"### `{raw['event']}` @ `{raw['ts']}` (summary)", ""]
    event_id = raw.get("event_id")
    if isinstance(event_id, str):
        lines.append(f"- **event_id**: `{event_id}`")
    lines.append("- **projection**: `summary`")
    for key, value in projection.items():
        lines.append(f"- **{key}**: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _header(query: str) -> str:
    return f"# Recall pack\n\nquery: `{query}`\n"


def _omitted_footer(omitted: int, limit_chars: int) -> str:
    return f"\n_{omitted} event(s) omitted to fit character limit of {limit_chars}._\n"


def _compact_omitted_footer(
    omitted: int, limit_chars: int, continuation_event_id: str | None
) -> str:
    continuation = (
        f" Direct continuation: event_id `{continuation_event_id}`."
        if continuation_event_id is not None
        else ""
    )
    return (
        f"\n_Context incomplete: {omitted} event(s) omitted to fit character limit "
        f"of {limit_chars}.{continuation}_\n"
    )


def _decode_cursor(cursor: str) -> dict[str, object]:
    try:
        payload = json.loads(cursor)
    except json.JSONDecodeError as exc:
        raise ValueError("continuation cursor is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("continuation cursor must be an object")
    return payload


def _encode_cursor(
    *,
    query_digest: str,
    prefix_digest: str,
    before_candidate_id: str,
    limit_chars: int,
    include_candidate: bool = False,
) -> str:
    payload = {
        "before_candidate_id": before_candidate_id,
        "include_candidate": include_candidate,
        "limit_chars": limit_chars,
        "prefix_digest": prefix_digest,
        "query_digest": query_digest,
        "v": 1,
    }
    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )


def _build_receipt(
    *,
    query_digest: str,
    prefix_digest: str,
    scanned_universe_count: int,
    candidate_ids: list[str],
    selected_ids: list[str],
    omitted: list[_Omitted],
    bytes_used: int,
    continuation_cursor: str | None,
    scan_complete: bool,
    context_complete: bool,
    selected_forms: list[str] | None = None,
    semantic_status: str = "unknown",
) -> dict[str, object]:
    receipt: dict[str, object] = {
        "bytes_used": bytes_used,
        "candidate_ids": candidate_ids,
        "context_complete": context_complete,
        "continuation_cursor": continuation_cursor,
        "omitted": [{"id": entry.id, "reason": entry.reason} for entry in omitted],
        "prefix_digest": prefix_digest,
        "query_digest": query_digest,
        "scan_complete": scan_complete,
        "scanned_universe_count": scanned_universe_count,
        "selected_ids": selected_ids,
        "semantic_status": semantic_status,
    }
    if selected_forms is not None:
        receipt["selected_forms"] = selected_forms
    return receipt

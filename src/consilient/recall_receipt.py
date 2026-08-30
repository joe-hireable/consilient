"""The canonical recall receipt, and the summary form it records.

Serialises, parses and validates the single JSON receipt that closes every pack, along
with the continuation cursor a caller uses to ask for the neighbouring page. Parsing is
deliberately strict: a receipt carrying a missing or unexpected field, a duplicated
receipt block, an unknown omission reason, or a `selected_forms` list that does not
align with `selected_ids` is refused rather than repaired, because a receipt is the
provenance of a context window and a tolerantly parsed one attests to nothing. A cursor
whose query digest, prefix digest or character limit disagrees with the current call is
refused for the same reason — it describes a different trajectory.

The extractive summary projection lives here too. When a single event exceeds the
character bound, an extractive summary of named fields is selected instead of dropping
it. That is not LLM condensation (EXP-45: condensation drops ~59%); the receipt records
the form so replay can tell a summary from the full event. A privileged field anywhere
on an event refuses the projection outright, so a summary can never become the path by
which a qualification, sentinel or card-private field reaches a pack.

`Selection` is the typed shape of what a receipt attests — the text, the selected
identifiers with their forms, the omissions and whether each was protected, and whether
the context is complete. `lookup_event` resolves a stable identifier back to its event,
or a commitment identifier to its current revision, which is what a caller needs in
order to follow a continuation."""

from __future__ import annotations
import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast
from .events import (
    CAPABILITY_GAP_KIND,
    Event,
    canonical,
)
from .work_items import COMMITTED
from .recall_vocabulary import (
    ALWAYS_INCLUDE_KINDS,
    CARD_PRIVATE_FIELDS,
    FULL_FORM,
    OMISSION_REASONS,
    OPTIONAL_RECEIPT_FIELDS,
    Omission,
    QUALIFICATION_FIELDS,
    RECEIPT_END,
    RECEIPT_MARKER,
    SENTINEL_FIELDS,
    SUMMARY_FORM,
    _SUMMARY_FIELD_CHARS,
    _clip_scalar_line,
    _collect_keys,
    _decode_cursor,
    _format_event,
    _format_summary,
    _normalise_query,
    _protection_ranks,
    _searchable_text,
    _stable_id,
)


__all__ = [
    "ALWAYS_INCLUDE_KINDS",
    "CARD_PRIVATE_FIELDS",
    "FULL_FORM",
    "OMISSION_REASONS",
    "OPTIONAL_RECEIPT_FIELDS",
    "Omission",
    "PRIVILEGED_FIELD_MARKERS",
    "PROJECTION_FORMS",
    "QUALIFICATION_FIELDS",
    "RECEIPT_BEGIN",
    "RECEIPT_END",
    "RECEIPT_MARKER",
    "SENTINEL_FIELDS",
    "SUMMARY_FORM",
    "Selection",
    "_SUMMARY_FIELD_CHARS",
    "_clip_scalar_line",
    "_collect_keys",
    "_decode_cursor",
    "_format_event",
    "_format_summary",
    "_normalise_query",
    "_protection_ranks",
    "_searchable_text",
    "_stable_id",
    "lookup_event",
    "parse_receipt",
    "privileged_omission_reason",
]

RECEIPT_BEGIN = f"<!-- {RECEIPT_MARKER}\n"

PROJECTION_FORMS = frozenset({FULL_FORM, SUMMARY_FORM})

PRIVILEGED_FIELD_MARKERS = QUALIFICATION_FIELDS | SENTINEL_FIELDS | CARD_PRIVATE_FIELDS


@dataclass(frozen=True)
class Selection:
    text: str
    selected_event_ids: tuple[str, ...]
    selected_digest: str
    omissions: tuple[Omission, ...]
    context_complete: bool
    continuation_event_id: str | None
    selected_forms: tuple[str, ...] = ()
    empty_while_available: bool = False


def _query_digest(query: str) -> str:
    return hashlib.sha256(_normalise_query(query).encode("utf-8")).hexdigest()


def _matches_query(event: Event, tokens: tuple[str, ...]) -> bool:
    if event.kind in ALWAYS_INCLUDE_KINDS:
        return True
    if not tokens:
        return True
    haystack = _searchable_text(event).lower()
    return any(token in haystack for token in tokens)


def privileged_omission_reason(event: Event) -> str | None:
    """Name the non-content reason, or None when the event may enter candidate context."""
    keys = _collect_keys(event.raw)
    if keys & CARD_PRIVATE_FIELDS:
        return "card_private"
    if keys & SENTINEL_FIELDS:
        return "sentinel"
    if keys & QUALIFICATION_FIELDS:
        return "qualification"
    return None


def _should_include(event: Event, tokens: tuple[str, ...]) -> bool:
    return _matches_query(event, tokens)


def _protected_event_indexes(events: Sequence[Event]) -> frozenset[int]:
    return frozenset(
        index for index, rank in enumerate(_protection_ranks(events)) if rank
    )


def _scalar_field(value: object, *, limit: int = _SUMMARY_FIELD_CHARS) -> str | None:
    """Extractive one-line clip so a summary cannot refill the pack budget."""
    if not isinstance(value, str):
        return None
    return _clip_scalar_line(value, limit=limit)


def _summary_projection(event: Event) -> dict[str, str] | None:
    """Named extractive fields, or None when this event cannot shrink.

    A privileged field anywhere on the event refuses the projection. The guard
    in instructions.py still inspects the full event; this keeps a summary from
    being the path that admits one.
    """
    if _collect_keys(event.raw) & PRIVILEGED_FIELD_MARKERS:
        return None
    data = event.data
    if event.kind == "dispatch.outcome":
        unit = (
            _scalar_field(data.get("unit"))
            or _scalar_field(data.get("task"))
            or _scalar_field(data.get("run_id"))
        )
        harness = _scalar_field(data.get("harness"))
        status = _scalar_field(data.get("status"))
        reason = _scalar_field(data.get("reason"))
        if unit is None or harness is None or status is None or reason is None:
            return None
        return {
            "unit": unit,
            "harness": harness,
            "status": status,
            "reason": reason,
        }
    if event.kind == CAPABILITY_GAP_KIND:
        capability = (
            _scalar_field(data.get("capability"))
            or _scalar_field(data.get("attempted"))
            or _scalar_field(data.get("asked"))
        )
        gap = (
            _scalar_field(data.get("gap"))
            or _scalar_field(data.get("detail"))
            or _scalar_field(data.get("failure"))
        )
        if capability is None or gap is None:
            return None
        return {"capability": capability, "gap": gap}
    if event.kind == "dispatch.refused":
        reason = _scalar_field(data.get("reason"))
        status = _scalar_field(data.get("status")) or "refused"
        if reason is None:
            return None
        return {"status": status, "reason": reason}
    return None


def _render_event(event: Event, form: str) -> str:
    if form == SUMMARY_FORM:
        projection = _summary_projection(event)
        if projection is not None:
            return _format_summary(event, projection)
    return _format_event(event)


def _selected_digest(
    events: Sequence[Event], forms: Sequence[str] | None = None
) -> str:
    pieces: list[str] = []
    for index, event in enumerate(events):
        form = FULL_FORM
        if forms is not None and index < len(forms):
            form = forms[index]
        if form == SUMMARY_FORM:
            projection = _summary_projection(event)
            if projection is not None:
                pieces.append("summary\n" + canonical(projection))
                continue
        pieces.append(canonical(event.raw))
    return hashlib.sha256("\n".join(pieces).encode("utf-8")).hexdigest()


def lookup_event(events: Sequence[Event], stable_id: str) -> Event | None:
    """Resolve a stable event ID, or the current revision of a commitment ID."""
    for event in events:
        if _stable_id(event) == stable_id:
            return event
    commitments = [
        event
        for event in events
        if event.kind == COMMITTED and event.data.get("commitment_id") == stable_id
    ]

    def revision(event: Event) -> int:
        value = event.data.get("revision")
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    return max(commitments, key=revision, default=None)


def _serialise_receipt(receipt: dict[str, object]) -> str:
    body = json.dumps(
        receipt, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    return f"{RECEIPT_BEGIN}{body}{RECEIPT_END}"


def _validate_cursor(
    cursor: str,
    *,
    query_digest: str,
    prefix_digest: str,
    limit_chars: int,
) -> tuple[str, bool]:
    payload = _decode_cursor(cursor)
    if payload.get("v") != 1:
        raise ValueError("continuation cursor has unsupported version")
    if payload.get("query_digest") != query_digest:
        raise ValueError("continuation cursor query_digest does not match")
    if payload.get("prefix_digest") != prefix_digest:
        raise ValueError(
            "continuation cursor prefix_digest does not match the current prefix"
        )
    if payload.get("limit_chars") != limit_chars:
        raise ValueError("continuation cursor limit_chars does not match")
    before_id = payload.get("before_candidate_id")
    if not isinstance(before_id, str) or not before_id:
        raise ValueError("continuation cursor before_candidate_id is missing")
    include_candidate = payload.get("include_candidate", False)
    if not isinstance(include_candidate, bool):
        raise ValueError("continuation cursor include_candidate must be a boolean")
    return before_id, include_candidate


def _fit_output(body: str, receipt: dict[str, object], limit_chars: int) -> str:
    text = body + _serialise_receipt(receipt) + "\n"
    if len(text) <= limit_chars:
        return text
    raise ValueError("limit_chars is too small for the recall receipt")


def parse_receipt(text: str) -> dict[str, object]:
    """Parse the single canonical recall receipt appended to a pack."""
    begin = text.find(RECEIPT_BEGIN)
    if begin == -1:
        raise ValueError("recall receipt block is missing")
    end = text.find(RECEIPT_END, begin + len(RECEIPT_BEGIN))
    if end == -1:
        raise ValueError("recall receipt block is not terminated")
    second = text.find(RECEIPT_BEGIN, begin + len(RECEIPT_BEGIN))
    if second != -1:
        raise ValueError("duplicate recall receipt blocks are not allowed")
    raw = text[begin + len(RECEIPT_BEGIN) : end]
    try:
        receipt = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("recall receipt is not valid JSON") from exc
    if not isinstance(receipt, dict):
        raise ValueError("recall receipt must be a JSON object")
    expected = {
        "bytes_used",
        "candidate_ids",
        "context_complete",
        "continuation_cursor",
        "omitted",
        "prefix_digest",
        "query_digest",
        "scan_complete",
        "scanned_universe_count",
        "selected_ids",
        "semantic_status",
    }
    actual = set(receipt)
    unexpected = actual - expected - OPTIONAL_RECEIPT_FIELDS
    missing = expected - actual
    if missing or unexpected:
        detail: list[str] = []
        if missing:
            detail.append(f"missing {', '.join(sorted(missing))}")
        if unexpected:
            detail.append(f"unexpected {', '.join(sorted(unexpected))}")
        raise ValueError(
            f"recall receipt fields are not canonical: {'; '.join(detail)}"
        )
    selected_forms = receipt.get("selected_forms")
    if selected_forms is not None:
        if not isinstance(selected_forms, list):
            raise ValueError("recall receipt selected_forms must be a list")
        if any(form not in PROJECTION_FORMS for form in selected_forms):
            raise ValueError("recall receipt selected_forms carries an unknown form")
        selected_ids = receipt.get("selected_ids")
        if not isinstance(selected_ids, list) or len(selected_forms) != len(
            selected_ids
        ):
            raise ValueError(
                "recall receipt selected_forms must align with selected_ids"
            )
    omitted = receipt["omitted"]
    if not isinstance(omitted, list):
        raise ValueError("recall receipt omitted must be a list")
    for entry in omitted:
        if not isinstance(entry, dict):
            raise ValueError("recall receipt omitted entries must be objects")
        reason = entry.get("reason")
        if reason not in OMISSION_REASONS:
            raise ValueError(f"unknown omission reason {reason!r}")
    return cast(dict[str, object], receipt)

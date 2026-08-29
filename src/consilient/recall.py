"""Portable verbatim recall projector for cross-harness memory.

Projects append-only trajectory events into a bounded markdown pack. Quotes event fields
literally when they fit. When a single event exceeds the character bound, an extractive
summary of named fields is selected instead of dropping it. That is not LLM condensation
(EXP-45: condensation drops ~59%); the receipt records the form so replay can tell a
summary from the full event.

Every pack ends with one canonical JSON recall receipt describing selection, omission
and completion state.

The projector is split across four siblings in this directory. `recall_vocabulary.py`
holds the constants, the per-event facts — identity, supersession, permission,
protection rank — and the markdown fragments. `recall_receipt.py` holds the receipt and
cursor codec, the strict receipt parser and the extractive summary projection.
`recall_body.py` assembles the pack body, reads a selection back out of a written pack,
and holds the compact selection used when the receipt itself will not fit.
`recall_budget.py` runs the budget loop that fits candidates to the character bound and
pages what does not. This file keeps the entry points: `pack`, `pack_events` and
`select_events`."""

from __future__ import annotations
from collections.abc import Sequence
from pathlib import Path
from .events import (
    Event,
    Rejection,
    read_all,
)
from .recall_vocabulary import (
    SUMMARY_FORM,
)

from .recall_body import (
    _compact_select_events,
    _selection_from_pack,
)

from .recall_budget import (
    _pack_with_receipt,
)

from .recall_receipt import (
    PRIVILEGED_FIELD_MARKERS,
    PROJECTION_FORMS,
    RECEIPT_BEGIN,
    Selection,
    _fit_output,
    _protected_event_indexes,
    _query_digest,
    _selected_digest,
    lookup_event,
    parse_receipt,
    privileged_omission_reason,
)

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
    _format_event,
    _protection_ranks,
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
    "_compact_select_events",
    "_fit_output",
    "_format_event",
    "_pack_with_receipt",
    "_protected_event_indexes",
    "_protection_ranks",
    "_query_digest",
    "_selected_digest",
    "_selection_from_pack",
    "_stable_id",
    "lookup_event",
    "pack",
    "pack_events",
    "parse_receipt",
    "privileged_omission_reason",
    "select_events",
]


def select_events(
    events: Sequence[Event],
    *,
    query: str,
    limit_chars: int,
    rejections: Sequence[Rejection] = (),
    continuation_cursor: str | None = None,
    scan_complete: bool = True,
    shrink_to_receipt: bool = False,
) -> Selection:
    """Select events and expose the bounded pack's exact provenance.

    Whole events are preferred. When a candidate cannot fit, a named extractive
    summary is selected and the receipt records `selected_forms`. The canonical
    receipt is retained whenever it fits without displacing context that the
    commitment contract protects. A smaller budget receives C02's compact,
    explicit stable-ID continuation instead of a fabricated complete receipt.
    """
    compact = (
        _compact_select_events(events, query=query, limit_chars=limit_chars)
        if continuation_cursor is None
        else None
    )
    try:
        text = _pack_with_receipt(
            events,
            query=query,
            limit_chars=limit_chars,
            rejections=rejections,
            continuation_cursor=continuation_cursor,
            scan_complete=scan_complete,
        )
    except ValueError:
        if compact is None:
            raise
        if not shrink_to_receipt:
            return compact
        try:
            _pack_with_receipt(
                (),
                query=query,
                limit_chars=limit_chars,
                scan_complete=scan_complete,
            )
        except ValueError:
            return compact
        raise

    selection = _selection_from_pack(events, text)
    if (
        compact is not None
        and not selection.selected_event_ids
        and compact.selected_event_ids
        and any(form == SUMMARY_FORM for form in compact.selected_forms)
    ):
        return compact
    if compact is not None:
        compact_protected = {
            omission.event_id for omission in compact.omissions if omission.protected
        }
        receipt_protected = {
            omission.event_id for omission in selection.omissions if omission.protected
        }
        if receipt_protected - compact_protected:
            if shrink_to_receipt:
                raise ValueError("the recall receipt displaces protected context")
            return compact
    return selection


def pack(
    log_dir: Path,
    *,
    query: str,
    limit_chars: int,
    continuation_cursor: str | None = None,
) -> str:
    """Build a bounded markdown pack from trajectory events."""
    if limit_chars < 1:
        raise ValueError("limit_chars must be at least 1")

    events, rejections = read_all(log_dir)
    return pack_events(
        events,
        query=query,
        limit_chars=limit_chars,
        rejections=rejections,
        continuation_cursor=continuation_cursor,
    )


def pack_events(
    events: Sequence[Event],
    *,
    query: str,
    limit_chars: int,
    rejections: Sequence[Rejection] = (),
    continuation_cursor: str | None = None,
    scan_complete: bool = True,
) -> str:
    """The pack over an already-read event list.

    `scan_complete=False` says the caller handed over a WINDOW of the trajectory rather than all
    of it. The receipt carries that through, because a bounded scan reported as complete is a
    claim about evidence the packer never saw. Callers that bound their window must say so.
    """
    return select_events(
        events,
        query=query,
        limit_chars=limit_chars,
        scan_complete=scan_complete,
        rejections=rejections,
        continuation_cursor=continuation_cursor,
    ).text

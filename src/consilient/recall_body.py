"""The visible body of a pack: assembled, read back, and shrunk when the receipt will
not fit.

Assembles the markdown half of a pack — a header, the selected events in trajectory
order rendered full or as summaries, and a footer counting what the character limit
displaced. It also reads that text back: given the events and a written pack, it
reconstructs the selection the receipt describes, so a caller holding only the markdown
can recover which events were quoted, in which form, and which were dropped under the
context bound.

The compact selection is the path taken when the budget is too small for the canonical
receipt to be written at all. It keeps protected context and states the loss in prose
rather than fabricating a complete receipt: an explicit stable-ID continuation names the
highest-ranked event that did not fit, and where even that will not fit the body
collapses to a single INCOMPLETE line naming it. A pack that has run out of room says
so. It never reports a partial context as whole."""

from __future__ import annotations
from collections.abc import Sequence
from .events import (
    Event,
)
from .recall_vocabulary import (
    FULL_FORM,
    Omission,
    SUMMARY_FORM,
    _EMPTY_PACK,
    _EMPTY_WHILE_AVAILABLE,
    _NO_MATCH_PACK,
    _compact_omitted_footer,
    _header,
    _omitted_footer,
    _permission_denied,
    _protection_ranks,
    _query_tokens,
    _stable_id,
    _superseded_event_ids,
)

from .recall_receipt import (
    PROJECTION_FORMS,
    Selection,
    _render_event,
    _selected_digest,
    _should_include,
    _summary_projection,
    parse_receipt,
    privileged_omission_reason,
)


__all__ = [
    "FULL_FORM",
    "Omission",
    "PROJECTION_FORMS",
    "SUMMARY_FORM",
    "Selection",
    "_EMPTY_PACK",
    "_EMPTY_WHILE_AVAILABLE",
    "_NO_MATCH_PACK",
    "_compact_omitted_footer",
    "_header",
    "_omitted_footer",
    "_permission_denied",
    "_protection_ranks",
    "_query_tokens",
    "_render_event",
    "_selected_digest",
    "_should_include",
    "_stable_id",
    "_summary_projection",
    "_superseded_event_ids",
    "parse_receipt",
    "privileged_omission_reason",
]


def _compact_select_events(
    events: Sequence[Event], *, query: str, limit_chars: int
) -> Selection:
    """Select protected context when even the canonical receipt cannot fit."""
    if limit_chars < 1:
        raise ValueError("limit_chars must be at least 1")
    if not events:
        return Selection(
            _EMPTY_PACK[:limit_chars], (), _selected_digest(()), (), True, None
        )

    tokens = _query_tokens(query)
    ranks = _protection_ranks(events)
    superseded_ids = _superseded_event_ids(events)
    privileged_omissions: list[Omission] = []
    candidates: list[tuple[int, Event, int]] = []
    for index, event in enumerate(events):
        if _stable_id(event) in superseded_ids or _permission_denied(event):
            continue
        reason = privileged_omission_reason(event)
        if reason is not None:
            privileged_omissions.append(
                Omission(_stable_id(event), event.kind, reason, False)
            )
            continue
        if ranks[index] or _should_include(event, tokens):
            candidates.append((index, event, ranks[index]))
    if not candidates:
        return Selection(
            _NO_MATCH_PACK[:limit_chars],
            (),
            _selected_digest(()),
            tuple(privileged_omissions),
            True,
            None,
        )

    kept: list[tuple[int, Event, int, str]] = [
        (index, event, rank, FULL_FORM) for index, event, rank in candidates
    ]
    removed: list[tuple[int, Event, int]] = []
    while kept:
        selected_events = [event for _, event, _, _ in kept]
        selected_forms = tuple(form for _, _, _, form in kept)
        continuation = (
            _stable_id(max(removed, key=lambda item: (item[2], item[0]))[1])
            if removed
            else None
        )
        parts = [_header(query)]
        parts.extend(_render_event(event, form) for _, event, _, form in kept)
        if removed:
            parts.append(
                _compact_omitted_footer(len(removed), limit_chars, continuation).lstrip(
                    "\n"
                )
            )
        text = "\n".join(parts)
        if not text.endswith("\n"):
            text += "\n"
        if len(text) <= limit_chars:
            omissions = tuple(privileged_omissions) + tuple(
                Omission(_stable_id(event), event.kind, "context_bound", rank > 0)
                for _, event, rank in sorted(removed, key=lambda item: item[0])
            )
            return Selection(
                text,
                tuple(_stable_id(event) for event in selected_events),
                _selected_digest(selected_events, selected_forms),
                omissions,
                not removed,
                continuation,
                selected_forms,
                False,
            )
        victim = None
        for position, (index, event, rank, form) in enumerate(kept):
            if form != FULL_FORM or _summary_projection(event) is None:
                continue
            if victim is None:
                victim = position
                continue
            current = kept[victim]
            if (rank, index) < (current[2], current[0]):
                victim = position
        if victim is not None:
            kept = [
                (
                    index,
                    event,
                    rank,
                    SUMMARY_FORM
                    if form == FULL_FORM and _summary_projection(event) is not None
                    else form,
                )
                for index, event, rank, form in kept
            ]
            continue
        victim = min(range(len(kept)), key=lambda item: (kept[item][2], kept[item][0]))
        dropped = kept.pop(victim)
        removed.append((dropped[0], dropped[1], dropped[2]))

    continuation = _stable_id(max(removed, key=lambda item: (item[2], item[0]))[1])
    omissions = tuple(privileged_omissions) + tuple(
        Omission(_stable_id(event), event.kind, "context_bound", rank > 0)
        for _, event, rank in sorted(removed, key=lambda item: item[0])
    )
    text = (
        "# Recall pack\n\n"
        f"{_EMPTY_WHILE_AVAILABLE}: candidates existed but none fitted, "
        "even as summaries.\n"
        + _compact_omitted_footer(len(removed), limit_chars, continuation).lstrip("\n")
    )
    if len(text) > limit_chars:
        text = f"INCOMPLETE event_id:{continuation}\n"
    return Selection(
        text[:limit_chars],
        (),
        _selected_digest(()),
        omissions,
        False,
        continuation,
        (),
        True,
    )


def _assemble_pack_body(
    *,
    query: str,
    selected: Sequence[Event],
    omitted_count: int,
    limit_chars: int,
    empty_text: str | None = None,
    forms: Sequence[str] | None = None,
) -> str:
    if empty_text is not None:
        return empty_text
    parts = [_header(query)]
    rendered = []
    for index, event in enumerate(selected):
        form = FULL_FORM
        if forms is not None and index < len(forms):
            form = forms[index]
        rendered.append(_render_event(event, form))
    parts.extend(rendered)
    if omitted_count:
        parts.append(_omitted_footer(omitted_count, limit_chars).lstrip("\n"))
    text = "\n".join(parts)
    return text if text.endswith("\n") else text + "\n"


def _selection_from_pack(events: Sequence[Event], text: str) -> Selection:
    receipt = parse_receipt(text)
    ranks = _protection_ranks(events)
    indexed = {
        _stable_id(event): (index, event, ranks[index])
        for index, event in enumerate(events)
    }
    raw_selected = receipt.get("selected_ids")
    selected_ids = (
        tuple(
            value
            for value in raw_selected
            if isinstance(value, str) and value in indexed
        )
        if isinstance(raw_selected, list)
        else ()
    )
    selected_events = [indexed[event_id][1] for event_id in selected_ids]
    raw_forms = receipt.get("selected_forms")
    if isinstance(raw_forms, list) and len(raw_forms) == len(selected_ids):
        selected_forms = tuple(
            form if form in PROJECTION_FORMS else FULL_FORM for form in raw_forms
        )
    else:
        selected_forms = tuple(FULL_FORM for _ in selected_ids)

    omissions: list[Omission] = []
    continuation_candidates: list[tuple[int, Event, int]] = []
    raw_omitted = receipt.get("omitted")
    if isinstance(raw_omitted, list):
        for entry in raw_omitted:
            if not isinstance(entry, dict):
                continue
            reason = entry.get("reason")
            event_id = entry.get("id")
            if not isinstance(event_id, str) or event_id not in indexed:
                continue
            index, event, rank = indexed[event_id]
            if reason == "context_bound":
                omissions.append(
                    Omission(event_id, event.kind, "context_bound", rank > 0)
                )
                continuation_candidates.append((index, event, rank))
            elif reason in {"qualification", "sentinel", "card_private"}:
                omissions.append(Omission(event_id, event.kind, reason, False))

    continuation = (
        _stable_id(max(continuation_candidates, key=lambda item: (item[2], item[0]))[1])
        if continuation_candidates
        else None
    )
    return Selection(
        text,
        selected_ids,
        _selected_digest(selected_events, selected_forms),
        tuple(omissions),
        receipt.get("context_complete") is True,
        continuation,
        selected_forms,
        receipt.get("semantic_status") == _EMPTY_WHILE_AVAILABLE,
    )

"""Portable verbatim recall projector for cross-harness memory.

Projects append-only trajectory events into a bounded markdown pack. Quotes event
fields literally — no condensation, no LLM summary (EXP-45: condensation drops ~59%).
"""

from __future__ import annotations

import json
from pathlib import Path

from .events import (
    VERDICT_CORRECTION_KIND,
    VERDICT_KIND,
    Event,
    read_all,
)

ALWAYS_INCLUDE_KINDS = frozenset(
    {
        "dispatch.outcome",
        "dispatch.refused",
        "dispatch.fanout",
        VERDICT_KIND,
        VERDICT_CORRECTION_KIND,
        "ticket.completed",
    }
)

_EMPTY_PACK = "# Recall pack\n\nNo events in log.\n"
_NO_MATCH_PACK = "# Recall pack\n\nNo events match query.\n"


def _query_tokens(query: str) -> tuple[str, ...]:
    return tuple(token.lower() for token in query.split() if token)


def _searchable_text(event: Event) -> str:
    return json.dumps(event.raw, ensure_ascii=False, sort_keys=True)


def _should_include(event: Event, tokens: tuple[str, ...]) -> bool:
    if event.kind in ALWAYS_INCLUDE_KINDS:
        return True
    if not tokens:
        return True
    haystack = _searchable_text(event).lower()
    return any(token in haystack for token in tokens)


def _format_event(event: Event) -> str:
    raw = event.raw
    lines = [f"### `{raw['event']}` @ `{raw['ts']}`", ""]
    for key in ("v", "ts", "event", "actor"):
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


def _header(query: str) -> str:
    return f"# Recall pack\n\nquery: `{query}`\n"


def _omitted_footer(omitted: int, limit_chars: int) -> str:
    return (
        f"\n_{omitted} event(s) omitted to fit character limit of {limit_chars}._\n"
    )


def pack(log_dir: Path, *, query: str, limit_chars: int) -> str:
    """Build a bounded markdown pack from trajectory events.

    Selects events matching ``query`` tokens plus always-include kinds (dispatch
    outcomes/refusals/fanouts, human verdicts, ticket.completed). Drops the oldest
    events first when the pack would exceed ``limit_chars``.
    """
    if limit_chars < 1:
        raise ValueError("limit_chars must be at least 1")

    events, _ = read_all(log_dir)
    if not events:
        return _EMPTY_PACK

    tokens = _query_tokens(query)
    selected = [event for event in events if _should_include(event, tokens)]
    if not selected:
        return _NO_MATCH_PACK

    omitted = 0
    while selected:
        parts = [_header(query)]
        parts.extend(_format_event(event) for event in selected)
        if omitted:
            parts.append(_omitted_footer(omitted, limit_chars).lstrip("\n"))
        text = "\n".join(parts)
        if len(text) <= limit_chars:
            return text if text.endswith("\n") else text + "\n"
        selected.pop(0)
        omitted += 1

    footer = _omitted_footer(omitted, limit_chars).strip()
    minimal = f"# Recall pack\n\n{footer}\n"
    if len(minimal) <= limit_chars:
        return minimal
    return _omitted_footer(omitted, limit_chars).lstrip("\n") + "\n"

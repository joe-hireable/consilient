"""Portable verbatim recall projector for cross-harness memory.

Projects append-only trajectory events into a bounded markdown pack. Quotes event
fields literally — no condensation, no LLM summary (EXP-45: condensation drops ~59%).

Every pack ends with one canonical JSON recall receipt describing selection, omission
and completion state.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from .events import (
    RECORD_CAPTURED_KIND,
    VERDICT_CORRECTION_KIND,
    VERDICT_KIND,
    Event,
    Rejection,
    canonical,
    event_sha256,
    read_all,
)
from . import promote

RECEIPT_MARKER = "consilient:recall-receipt:v1"
RECEIPT_BEGIN = f"<!-- {RECEIPT_MARKER}\n"
RECEIPT_END = "\n-->"

OMISSION_REASONS = frozenset(
    {"irrelevant", "superseded", "permission", "context_bound", "corrupt"}
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


@dataclass(frozen=True)
class _Omitted:
    id: str
    reason: str


def _query_tokens(query: str) -> tuple[str, ...]:
    return tuple(token.lower() for token in query.split() if token)


def _normalise_query(query: str) -> str:
    return " ".join(query.lower().split())


def _query_digest(query: str) -> str:
    return hashlib.sha256(_normalise_query(query).encode("utf-8")).hexdigest()


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


def _matches_query(event: Event, tokens: tuple[str, ...]) -> bool:
    if event.kind in ALWAYS_INCLUDE_KINDS:
        return True
    if not tokens:
        return True
    haystack = _searchable_text(event).lower()
    return any(token in haystack for token in tokens)


def _permission_denied(event: Event) -> bool:
    if event.kind != RECORD_CAPTURED_KIND:
        return False
    return event.data.get("retention_class") == "private"


def _superseded_event_ids(events: Sequence[Event]) -> frozenset[str]:
    superseded: set[str] = set()
    for event in events:
        if event.kind != RECORD_CAPTURED_KIND:
            continue
        supersedes = event.data.get("supersedes")
        if not isinstance(supersedes, list):
            continue
        for reference in supersedes:
            if isinstance(reference, dict) and isinstance(reference.get("event_id"), str):
                superseded.add(reference["event_id"])
    return frozenset(superseded)


def _should_include(event: Event, tokens: tuple[str, ...]) -> bool:
    return _matches_query(event, tokens)


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


def _serialise_receipt(receipt: dict[str, object]) -> str:
    body = json.dumps(receipt, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"{RECEIPT_BEGIN}{body}{RECEIPT_END}"


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
) -> str:
    payload = {
        "before_candidate_id": before_candidate_id,
        "limit_chars": limit_chars,
        "prefix_digest": prefix_digest,
        "query_digest": query_digest,
        "v": 1,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _validate_cursor(
    cursor: str,
    *,
    query_digest: str,
    prefix_digest: str,
    limit_chars: int,
) -> str:
    payload = _decode_cursor(cursor)
    if payload.get("v") != 1:
        raise ValueError("continuation cursor has unsupported version")
    if payload.get("query_digest") != query_digest:
        raise ValueError("continuation cursor query_digest does not match")
    if payload.get("prefix_digest") != prefix_digest:
        raise ValueError("continuation cursor prefix_digest does not match the current prefix")
    if payload.get("limit_chars") != limit_chars:
        raise ValueError("continuation cursor limit_chars does not match")
    before_id = payload.get("before_candidate_id")
    if not isinstance(before_id, str) or not before_id:
        raise ValueError("continuation cursor before_candidate_id is missing")
    return before_id


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
) -> dict[str, object]:
    return {
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
        "semantic_status": "unknown",
    }


def _assemble_pack_body(
    *,
    query: str,
    selected: Sequence[Event],
    omitted_count: int,
    limit_chars: int,
    empty_text: str | None = None,
) -> str:
    if empty_text is not None:
        return empty_text
    parts = [_header(query)]
    parts.extend(_format_event(event) for event in selected)
    if omitted_count:
        parts.append(_omitted_footer(omitted_count, limit_chars).lstrip("\n"))
    text = "\n".join(parts)
    return text if text.endswith("\n") else text + "\n"


def _pack_with_receipt(
    events: Sequence[Event],
    *,
    query: str,
    limit_chars: int,
    rejections: Sequence[Rejection] = (),
    continuation_cursor: str | None = None,
    scan_complete: bool = True,
) -> str:
    if limit_chars < 1:
        raise ValueError("limit_chars must be at least 1")

    query_digest = _query_digest(query)
    prefix = _prefix_digest(events)
    tokens = _query_tokens(query)
    superseded_ids = _superseded_event_ids(events)

    after_id: str | None = None
    if continuation_cursor is not None:
        after_id = _validate_cursor(
            continuation_cursor,
            query_digest=query_digest,
            prefix_digest=prefix,
            limit_chars=limit_chars,
        )

    scanned_universe_count = len(events) + len(rejections)
    omitted_entries: list[_Omitted] = [
        _Omitted(_rejection_id(rejection), "corrupt") for rejection in rejections
    ]

    if not events and not rejections:
        receipt = _build_receipt(
            query_digest=query_digest,
            prefix_digest=prefix,
            scanned_universe_count=0,
            candidate_ids=[],
            selected_ids=[],
            omitted=omitted_entries,
            bytes_used=len(_EMPTY_PACK),
            continuation_cursor=None,
            scan_complete=scan_complete,
            context_complete=True,
        )
        return _fit_output(_EMPTY_PACK, receipt, limit_chars)

    all_candidate_events: list[Event] = []
    for event in events:
        stable = _stable_id(event)
        if stable in superseded_ids:
            omitted_entries.append(_Omitted(stable, "superseded"))
            continue
        if _permission_denied(event):
            omitted_entries.append(_Omitted(stable, "permission"))
            continue
        if _should_include(event, tokens):
            all_candidate_events.append(event)
        else:
            omitted_entries.append(_Omitted(stable, "irrelevant"))

    if not all_candidate_events and not any(
        entry.reason in {"corrupt", "permission", "superseded"} for entry in omitted_entries
    ):
        receipt = _build_receipt(
            query_digest=query_digest,
            prefix_digest=prefix,
            scanned_universe_count=scanned_universe_count,
            candidate_ids=[],
            selected_ids=[],
            omitted=omitted_entries,
            bytes_used=len(_NO_MATCH_PACK),
            continuation_cursor=None,
            scan_complete=scan_complete,
            context_complete=True,
        )
        return _fit_output(_NO_MATCH_PACK, receipt, limit_chars)

    full_candidate_ids = [_stable_id(event) for event in all_candidate_events]
    if after_id is not None:
        if after_id not in full_candidate_ids:
            raise ValueError(
                "continuation cursor before_candidate_id is not a current candidate"
            )
        split = full_candidate_ids.index(after_id)
        page_candidates = all_candidate_events[:split]
    else:
        page_candidates = list(all_candidate_events)

    dropped_for_budget = 0
    selected: list[Event] = list(page_candidates)
    context_bound_ids: list[str] = []
    resume_suffix = after_id is None

    while True:
        if not selected:
            footer = _omitted_footer(dropped_for_budget, limit_chars).strip()
            minimal = f"# Recall pack\n\n{footer}\n"
            body = (
                minimal
                if len(minimal) <= limit_chars
                else _omitted_footer(dropped_for_budget, limit_chars).lstrip("\n") + "\n"
            )
        else:
            body = _assemble_pack_body(
                query=query,
                selected=selected,
                omitted_count=dropped_for_budget,
                limit_chars=limit_chars,
            )

        provisional_omitted = list(omitted_entries)
        provisional_omitted.extend(
            _Omitted(stable_id, "context_bound") for stable_id in context_bound_ids
        )
        continuation: str | None = None
        if resume_suffix and context_bound_ids and selected:
            continuation = _encode_cursor(
                query_digest=query_digest,
                prefix_digest=prefix,
                before_candidate_id=_stable_id(selected[0]),
                limit_chars=limit_chars,
            )
        elif resume_suffix and context_bound_ids and not selected:
            if len(context_bound_ids) < len(full_candidate_ids):
                continuation = _encode_cursor(
                    query_digest=query_digest,
                    prefix_digest=prefix,
                    before_candidate_id=full_candidate_ids[len(context_bound_ids)],
                    limit_chars=limit_chars,
                )

        receipt = _build_receipt(
            query_digest=query_digest,
            prefix_digest=prefix,
            scanned_universe_count=scanned_universe_count,
            candidate_ids=full_candidate_ids,
            selected_ids=[_stable_id(event) for event in selected],
            omitted=provisional_omitted,
            bytes_used=len(body),
            continuation_cursor=continuation,
            scan_complete=scan_complete,
            context_complete=continuation is None,
        )
        if len(body) + len(_serialise_receipt(receipt)) + 1 <= limit_chars:
            return _fit_output(body, receipt, limit_chars)

        if not selected:
            return _fit_output(body, receipt, limit_chars)
        removed = selected.pop(0)
        dropped_for_budget += 1
        removed_id = _stable_id(removed)
        if removed_id not in context_bound_ids:
            context_bound_ids.append(removed_id)


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
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        detail: list[str] = []
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        if extra:
            detail.append(f"unexpected {', '.join(extra)}")
        raise ValueError(f"recall receipt fields are not canonical: {'; '.join(detail)}")
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


def pack(log_dir: Path, *, query: str, limit_chars: int, continuation_cursor: str | None = None) -> str:
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
    return _pack_with_receipt(
        events,
        query=query,
        limit_chars=limit_chars,
        scan_complete=scan_complete,
        rejections=rejections,
        continuation_cursor=continuation_cursor,
    )

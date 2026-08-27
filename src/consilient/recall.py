"""Portable verbatim recall projector for cross-harness memory.

Projects append-only trajectory events into a bounded markdown pack. Quotes event
fields literally when they fit. When a single event exceeds the character bound, an
extractive summary of named fields is selected instead of dropping it. That is not
LLM condensation (EXP-45: condensation drops ~59%); the receipt records the form so
replay can tell a summary from the full event.

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
    read_all,
)
from . import promote
from .work_items import COMMITTED, TURN

RECEIPT_MARKER = "consilient:recall-receipt:v1"
RECEIPT_BEGIN = f"<!-- {RECEIPT_MARKER}\n"
RECEIPT_END = "\n-->"
FULL_FORM = "full"
SUMMARY_FORM = "summary"
PROJECTION_FORMS = frozenset({FULL_FORM, SUMMARY_FORM})
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
PRIVILEGED_FIELD_MARKERS = QUALIFICATION_FIELDS | SENTINEL_FIELDS | CARD_PRIVATE_FIELDS

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


def _protected_event_indexes(events: Sequence[Event]) -> frozenset[int]:
    return frozenset(
        index for index, rank in enumerate(_protection_ranks(events)) if rank
    )


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


def _scalar_field(value: object, *, limit: int = _SUMMARY_FIELD_CHARS) -> str | None:
    """Extractive one-line clip so a summary cannot refill the pack budget."""
    if not isinstance(value, str):
        return None
    line = ""
    for candidate in value.splitlines():
        stripped = candidate.strip()
        if stripped:
            line = stripped
            break
    if not line:
        return None
    if len(line) <= limit:
        return line
    if limit < 4:
        return line[:limit]
    return line[: limit - 3].rstrip() + "..."


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


def _render_event(event: Event, form: str) -> str:
    if form == SUMMARY_FORM:
        projection = _summary_projection(event)
        if projection is not None:
            return _format_summary(event, projection)
    return _format_event(event)


def _header(query: str) -> str:
    return f"# Recall pack\n\nquery: `{query}`\n"


def _omitted_footer(omitted: int, limit_chars: int) -> str:
    return (
        f"\n_{omitted} event(s) omitted to fit character limit of {limit_chars}._\n"
    )


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
        parts.extend(
            _render_event(event, form) for _, event, _, form in kept
        )
        if removed:
            parts.append(
                _compact_omitted_footer(
                    len(removed), limit_chars, continuation
                ).lstrip("\n")
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
        victim = min(
            range(len(kept)), key=lambda item: (kept[item][2], kept[item][0])
        )
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
        + _compact_omitted_footer(
            len(removed), limit_chars, continuation
        ).lstrip("\n")
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
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


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
        raise ValueError("continuation cursor prefix_digest does not match the current prefix")
    if payload.get("limit_chars") != limit_chars:
        raise ValueError("continuation cursor limit_chars does not match")
    before_id = payload.get("before_candidate_id")
    if not isinstance(before_id, str) or not before_id:
        raise ValueError("continuation cursor before_candidate_id is missing")
    include_candidate = payload.get("include_candidate", False)
    if not isinstance(include_candidate, bool):
        raise ValueError("continuation cursor include_candidate must be a boolean")
    return before_id, include_candidate


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
    ranks = _protection_ranks(events)

    after_id: str | None = None
    include_after = False
    if continuation_cursor is not None:
        after_id, include_after = _validate_cursor(
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

    all_candidates: list[tuple[int, Event, int]] = []
    for index, event in enumerate(events):
        stable = _stable_id(event)
        if stable in superseded_ids:
            omitted_entries.append(_Omitted(stable, "superseded"))
            continue
        if _permission_denied(event):
            omitted_entries.append(_Omitted(stable, "permission"))
            continue
        privileged = privileged_omission_reason(event)
        if privileged is not None:
            omitted_entries.append(_Omitted(stable, privileged))
            continue
        if ranks[index] or _should_include(event, tokens):
            all_candidates.append((index, event, ranks[index]))
        else:
            omitted_entries.append(_Omitted(stable, "irrelevant"))

    if not all_candidates and not any(
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

    # A continuation page must be a prefix of a stable ordering. Rank first so
    # ordinary history is evicted before commitments, corrections and authority;
    # render order remains the original trajectory order below.
    all_candidates.sort(key=lambda item: (item[2], item[0]))
    full_candidate_ids = [_stable_id(event) for _, event, _ in all_candidates]
    if after_id is not None:
        if after_id not in full_candidate_ids:
            raise ValueError(
                "continuation cursor before_candidate_id is not a current candidate"
            )
        split = full_candidate_ids.index(after_id) + int(include_after)
        page_candidates = all_candidates[:split]
    else:
        page_candidates = list(all_candidates)

    selected = list(page_candidates)
    forms: dict[str, str] = {
        _stable_id(event): FULL_FORM for _, event, _ in selected
    }
    context_bound: list[tuple[int, Event, int]] = []

    while True:
        dropped_for_budget = len(context_bound)
        selected_events = [
            event for _, event, _ in sorted(selected, key=lambda item: item[0])
        ]
        selected_form_list = [forms[_stable_id(event)] for event in selected_events]
        empty_while_available = not selected and bool(all_candidates)
        if not selected:
            footer = _omitted_footer(dropped_for_budget, limit_chars).strip()
            marker = (
                f"{_EMPTY_WHILE_AVAILABLE}: candidates existed but none fitted, "
                "even as summaries.\n"
            )
            minimal = f"# Recall pack\n\n{marker}{footer}\n"
            body = (
                minimal
                if len(minimal) <= limit_chars
                else marker
                + _omitted_footer(dropped_for_budget, limit_chars).lstrip("\n")
                + "\n"
            )
        else:
            body = _assemble_pack_body(
                query=query,
                selected=selected_events,
                omitted_count=dropped_for_budget,
                limit_chars=limit_chars,
                forms=selected_form_list,
            )

        provisional_omitted = list(omitted_entries)
        provisional_omitted.extend(
            _Omitted(_stable_id(event), "context_bound")
            for _, event, _ in context_bound
        )
        continuation: str | None = None
        if context_bound and selected:
            continuation = _encode_cursor(
                query_digest=query_digest,
                prefix_digest=prefix,
                before_candidate_id=_stable_id(selected[0][1]),
                limit_chars=limit_chars,
            )
        elif context_bound:
            direct = max(context_bound, key=lambda item: (item[2], item[0]))
            continuation = _encode_cursor(
                query_digest=query_digest,
                prefix_digest=prefix,
                before_candidate_id=_stable_id(direct[1]),
                limit_chars=limit_chars,
                include_candidate=True,
            )

        receipt = _build_receipt(
            query_digest=query_digest,
            prefix_digest=prefix,
            scanned_universe_count=scanned_universe_count,
            candidate_ids=full_candidate_ids,
            selected_ids=[_stable_id(event) for event in selected_events],
            omitted=provisional_omitted,
            bytes_used=len(body),
            continuation_cursor=continuation,
            scan_complete=scan_complete,
            context_complete=not context_bound,
            selected_forms=(
                selected_form_list if SUMMARY_FORM in selected_form_list else None
            ),
            semantic_status=(
                _EMPTY_WHILE_AVAILABLE if empty_while_available else "unknown"
            ),
        )
        if (
            len(body) + len(_serialise_receipt(receipt)) + 1 <= limit_chars
            and selected
        ):
            return _fit_output(body, receipt, limit_chars)
        if (
            len(body) + len(_serialise_receipt(receipt)) + 1 <= limit_chars
            and not selected
        ):
            reclaimed = False
            reclaimable = [
                item
                for item in context_bound
                if _summary_projection(item[1]) is not None
            ]
            reclaimable.sort(key=lambda item: (-item[2], -item[0]))
            for item in reclaimable:
                trial = selected + [item]
                trial_bound = [entry for entry in context_bound if entry is not item]
                trial_events = [
                    event for _, event, _ in sorted(trial, key=lambda row: row[0])
                ]
                trial_forms = [SUMMARY_FORM for _event in trial_events]
                trial_body = _assemble_pack_body(
                    query=query,
                    selected=trial_events,
                    omitted_count=len(trial_bound),
                    limit_chars=limit_chars,
                    forms=trial_forms,
                )
                trial_omitted = list(omitted_entries)
                trial_omitted.extend(
                    _Omitted(_stable_id(event), "context_bound")
                    for _, event, _ in trial_bound
                )
                trial_receipt = _build_receipt(
                    query_digest=query_digest,
                    prefix_digest=prefix,
                    scanned_universe_count=scanned_universe_count,
                    candidate_ids=full_candidate_ids,
                    selected_ids=[_stable_id(event) for event in trial_events],
                    omitted=trial_omitted,
                    bytes_used=len(trial_body),
                    continuation_cursor=_encode_cursor(
                        query_digest=query_digest,
                        prefix_digest=prefix,
                        before_candidate_id=_stable_id(trial[0][1]),
                        limit_chars=limit_chars,
                    )
                    if trial_bound
                    else None,
                    scan_complete=scan_complete,
                    context_complete=not trial_bound,
                    selected_forms=trial_forms,
                    semantic_status="unknown",
                )
                if (
                    len(trial_body) + len(_serialise_receipt(trial_receipt)) + 1
                    > limit_chars
                ):
                    break
                selected = trial
                context_bound = trial_bound
                forms[_stable_id(item[1])] = SUMMARY_FORM
                reclaimed = True
            if reclaimed:
                continue
            return _fit_output(body, receipt, limit_chars)

        if not selected:
            return _fit_output(body, receipt, limit_chars)
        demoted = None
        for position, (index, event, rank) in enumerate(selected):
            stable = _stable_id(event)
            if forms[stable] != FULL_FORM or _summary_projection(event) is None:
                continue
            if demoted is None:
                demoted = position
                continue
            current = selected[demoted]
            if (rank, index) < (current[2], current[0]):
                demoted = position
        if demoted is not None:
            for index, event, rank in selected:
                stable = _stable_id(event)
                if forms[stable] == FULL_FORM and _summary_projection(event) is not None:
                    forms[stable] = SUMMARY_FORM
            continue
        dropped = selected.pop(0)
        context_bound.append(dropped)
        forms.pop(_stable_id(dropped[1]), None)


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
        raise ValueError(f"recall receipt fields are not canonical: {'; '.join(detail)}")
    selected_forms = receipt.get("selected_forms")
    if selected_forms is not None:
        if not isinstance(selected_forms, list):
            raise ValueError("recall receipt selected_forms must be a list")
        if any(form not in PROJECTION_FORMS for form in selected_forms):
            raise ValueError("recall receipt selected_forms carries an unknown form")
        selected_ids = receipt.get("selected_ids")
        if not isinstance(selected_ids, list) or len(selected_forms) != len(selected_ids):
            raise ValueError("recall receipt selected_forms must align with selected_ids")
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


def _selection_from_pack(events: Sequence[Event], text: str) -> Selection:
    receipt = parse_receipt(text)
    ranks = _protection_ranks(events)
    indexed = {
        _stable_id(event): (index, event, ranks[index])
        for index, event in enumerate(events)
    }
    raw_selected = receipt.get("selected_ids")
    selected_ids = tuple(
        value
        for value in raw_selected
        if isinstance(value, str) and value in indexed
    ) if isinstance(raw_selected, list) else ()
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
                omissions.append(Omission(event_id, event.kind, "context_bound", rank > 0))
                continuation_candidates.append((index, event, rank))
            elif reason in {"qualification", "sentinel", "card_private"}:
                omissions.append(Omission(event_id, event.kind, reason, False))

    continuation = (
        _stable_id(
            max(continuation_candidates, key=lambda item: (item[2], item[0]))[1]
        )
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
    return select_events(
        events,
        query=query,
        limit_chars=limit_chars,
        scan_complete=scan_complete,
        rejections=rejections,
        continuation_cursor=continuation_cursor,
    ).text

"""Fitting the candidates into the character bound, and paging what will not fit.

Runs the budget loop that produces a pack together with its canonical receipt. Events
are classified before anything is measured — superseded, permission-denied and
privileged events are omitted with a named reason — and the survivors are ordered by
protection rank so that ordinary history is evicted before commitments, corrections and
unresolved authority. Ranking governs eviction only; render order stays the original
trajectory order.

When body and receipt together overrun the limit, full events are demoted to summaries
before any event is dropped, and an event dropped for the budget is recorded as
`context_bound` rather than quietly forgotten. Where nothing fits at all, the loop tries
once more to reclaim the highest-ranked droppable events as summaries, so a pack that is
empty while candidates existed is a stated outcome carried in the receipt rather than an
accident that looks like no matches.

Paging is by explicit cursor over a stable ordering. A continuation names the candidate
the next page must stop before, and is bound to the query digest, the prefix digest of
the events scanned and the character limit, so a cursor cannot be replayed against a
trajectory that has since changed."""

from __future__ import annotations
from collections.abc import Sequence
from .events import (
    Event,
    Rejection,
)
from .recall_vocabulary import (
    FULL_FORM,
    SUMMARY_FORM,
    _EMPTY_PACK,
    _EMPTY_WHILE_AVAILABLE,
    _NO_MATCH_PACK,
    _Omitted,
    _build_receipt,
    _encode_cursor,
    _omitted_footer,
    _permission_denied,
    _prefix_digest,
    _protection_ranks,
    _query_tokens,
    _rejection_id,
    _stable_id,
    _superseded_event_ids,
)

from .recall_body import (
    _assemble_pack_body,
)

from .recall_receipt import (
    _fit_output,
    _query_digest,
    _serialise_receipt,
    _should_include,
    _summary_projection,
    _validate_cursor,
    privileged_omission_reason,
)


__all__ = [
    "FULL_FORM",
    "SUMMARY_FORM",
    "_EMPTY_PACK",
    "_EMPTY_WHILE_AVAILABLE",
    "_NO_MATCH_PACK",
    "_Omitted",
    "_assemble_pack_body",
    "_build_receipt",
    "_encode_cursor",
    "_fit_output",
    "_omitted_footer",
    "_permission_denied",
    "_prefix_digest",
    "_protection_ranks",
    "_query_digest",
    "_query_tokens",
    "_rejection_id",
    "_serialise_receipt",
    "_should_include",
    "_stable_id",
    "_summary_projection",
    "_superseded_event_ids",
    "_validate_cursor",
    "privileged_omission_reason",
]


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
        entry.reason in {"corrupt", "permission", "superseded"}
        for entry in omitted_entries
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
    forms: dict[str, str] = {_stable_id(event): FULL_FORM for _, event, _ in selected}
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
        if len(body) + len(_serialise_receipt(receipt)) + 1 <= limit_chars and selected:
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
                if (
                    forms[stable] == FULL_FORM
                    and _summary_projection(event) is not None
                ):
                    forms[stable] = SUMMARY_FORM
            continue
        dropped = selected.pop(0)
        context_bound.append(dropped)
        forms.pop(_stable_id(dropped[1]), None)

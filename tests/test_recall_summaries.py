"""An event too large for the budget arrives as a summary, never as nothing at all.

A dropped event is worse than a shortened one: the pack goes out looking complete while
the outcome that mattered has vanished. So an oversized `dispatch.outcome` or
`capability.gap` is projected to a summary carrying the harness, unit, status, reason
and the capability that failed; the padding is clipped; and the receipt records the
summary form, so the selected digest cannot be mistaken for the digest of the full
event. A privileged event is refused rather than summarised, and an empty pack while
events were available is reported as its own semantic outcome instead of being passed
off as an empty log.

The live-shaped half of this file exists because the synthetic fixture in the first half
was wrong about the real schema. A live scan omitted 201 events. [measured] Measured 26
August 2026 over 1,476 outcomes: zero carry `unit`, `task` is the entire brief with a
median of 5,079 characters and a maximum of 16,923, and 677 exceed RECALL_LIMIT_CHARS --
so falling back to the full task makes the summary larger than the pack, and the shrink
loop drops every candidate exactly as before. [measured] The live-shaped tests pin that
shape, so a fixture that flatters the projector cannot be mistaken for evidence again."""

from consilient import recall
from consilient.events import Event
from consilient.recall import parse_receipt
from recall_helpers import (
    _event,
    _oversized_capability_gap,
    _oversized_dispatch_outcome,
)


def test_oversized_event_is_represented_by_a_summary_rather_than_dropped() -> None:
    event_id = "00000000-0000-4000-8000-000000000107"
    event = _oversized_dispatch_outcome(event_id=event_id)
    formatted = recall._format_event(event)
    assert len(formatted) > 8000

    selection = recall.select_events([event], query="", limit_chars=8000)

    assert event_id in selection.selected_event_ids
    assert selection.selected_forms == (recall.SUMMARY_FORM,)
    assert "cursor-composer" in selection.text
    assert "START_FAILED -- no artefact within the start window" in selection.text
    assert "Z07" in selection.text
    assert "(summary)" in selection.text
    assert ("x" * 200) not in selection.text
    receipt = parse_receipt(selection.text)
    assert receipt["selected_ids"] == [event_id]
    assert receipt["selected_forms"] == [recall.SUMMARY_FORM]
    full_digest = recall._selected_digest([event], (recall.FULL_FORM,))
    assert selection.selected_digest != full_digest
    assert selection.selected_digest == recall._selected_digest(
        [event], (recall.SUMMARY_FORM,)
    )


def test_capability_gap_summary_carries_capability_and_gap() -> None:
    event_id = "00000000-0000-4000-8000-000000000108"
    event = _oversized_capability_gap(event_id=event_id)
    selection = recall.select_events([event], query="", limit_chars=8000)
    assert event_id in selection.selected_event_ids
    assert selection.selected_forms == (recall.SUMMARY_FORM,)
    assert "recall.pack_events" in selection.text
    assert "selection dropped every candidate" in selection.text
    assert ("y" * 200) not in selection.text


def test_empty_pack_while_events_were_available_is_a_reported_outcome() -> None:
    event = Event(
        _event(
            event_id="00000000-0000-4000-8000-000000000109",
            event="note.recorded",
            data={"topic": "crowd", "padding": "z" * 9000},
        )
    )
    selection = recall.select_events([event], query="crowd", limit_chars=8000)
    assert selection.selected_event_ids == ()
    assert selection.empty_while_available is True
    assert "empty_while_available" in selection.text
    receipt = parse_receipt(selection.text)
    assert receipt["semantic_status"] == "empty_while_available"
    assert receipt["selected_ids"] == []


def test_privileged_event_is_not_admitted_as_a_summary() -> None:
    event = _oversized_dispatch_outcome(
        event_id="00000000-0000-4000-8000-000000000110",
        sentinel_score=1,
    )
    selection = recall.select_events([event], query="", limit_chars=8000)
    assert selection.selected_event_ids == ()
    assert all(omission.reason == "sentinel" for omission in selection.omissions)
    assert "(summary)" not in selection.text


def test_many_oversized_events_still_select_summaries() -> None:
    """A fat receipt must not evict every summary. [measured] live scan: 201 omitted."""
    crowd = [
        _oversized_dispatch_outcome(
            event_id=f"00000000-0000-4000-8000-{index:012d}",
            padding=9000,
        )
        for index in range(201)
    ]
    selection = recall.select_events(crowd, query="", limit_chars=8000)
    assert selection.selected_event_ids, (
        "an empty pack while 201 oversized outcomes were available is the defect"
    )
    assert recall.SUMMARY_FORM in selection.selected_forms
    assert "cursor-composer" in selection.text


def _live_shaped_dispatch_outcome(
    *, event_id: str, task: str, harness: str = "grok"
) -> Event:
    """Match the measured live schema: no `unit`, `task` is the whole brief."""
    return Event(
        _event(
            event_id=event_id,
            event="dispatch.outcome",
            actor="consilient.dispatch",
            data={
                "artefact_bytes": 0,
                "assembly_id": "assembly-live-shape",
                "command": ["grok", "--always-approve"],
                "cwd": ".",
                "diff_bytes": 0,
                "duration_s": 1.0,
                "exit_code": 0,
                "family": "grok",
                "harness": harness,
                "output_records": 0,
                "pool": "grok",
                "reason": "produced an artefact",
                "run_id": "20260826T195704-4516332bf0",
                "status": "ok",
                "supervised": True,
                "task": task,
                "timed_out": False,
            },
        )
    )


def test_summary_does_not_inline_a_task_field_larger_than_the_budget() -> None:
    """Live dispatch.outcome has no `unit`; `task` is the brief, often >8 KB.

    Measured 26 August 2026 over 1,476 outcomes: zero carry `unit`, task median
    5,079 characters / max 16,923, 677 exceed RECALL_LIMIT_CHARS. Falling back to
    the full task makes the 'summary' larger than the pack, so the shrink loop
    still drops every candidate. [measured]
    """
    title = "# Build Z07 exactly as the plan specifies. Test-first, one commit."
    body = "brief-body-padding " * 500
    event = _live_shaped_dispatch_outcome(
        event_id="00000000-0000-4000-8000-000000000201",
        task=f"{title}\n\n{body}",
    )
    assert len(event.data["task"]) > 8000

    selection = recall.select_events([event], query="", limit_chars=8000)

    assert event.raw["event_id"] in selection.selected_event_ids
    assert selection.selected_forms == (recall.SUMMARY_FORM,)
    assert "grok" in selection.text
    assert "produced an artefact" in selection.text
    assert title in selection.text
    assert "brief-body-padding " * 8 not in selection.text
    assert len(selection.text) <= 8000


def test_a_single_line_task_larger_than_the_budget_is_clipped_not_dropped() -> None:
    event = _live_shaped_dispatch_outcome(
        event_id="00000000-0000-4000-8000-000000000202",
        task="T" * 9000,
    )
    selection = recall.select_events([event], query="", limit_chars=8000)
    assert event.raw["event_id"] in selection.selected_event_ids
    assert selection.selected_forms == (recall.SUMMARY_FORM,)
    assert ("T" * 400) not in selection.text
    assert "T" * 40 in selection.text


def test_capability_gap_summary_clips_an_oversized_detail_field() -> None:
    event = Event(
        _event(
            event_id="00000000-0000-4000-8000-000000000203",
            event="capability.gap",
            actor="consilient.dispatch",
            data={
                "asked": "A" * 9000,
                "attempted": "recall.pack_events",
                "failure": "not_implemented",
                "detail": "selection dropped every candidate\n"
                + ("gap-detail-padding " * 500),
                "repair": "project a summary when the full event does not fit",
                "run_id": "20260826T195704-4516332bf0",
                "source": "dispatch.outcome",
                "closure": "escalate",
            },
        )
    )
    selection = recall.select_events([event], query="", limit_chars=8000)
    assert event.raw["event_id"] in selection.selected_event_ids
    assert selection.selected_forms == (recall.SUMMARY_FORM,)
    assert "recall.pack_events" in selection.text
    assert "gap-detail-padding " * 8 not in selection.text
    assert ("A" * 400) not in selection.text


def test_live_shaped_crowd_is_not_an_empty_pack() -> None:
    """The 201-omission live scan is this shape, not a short unit plus padding."""
    title = "# Build Z07 exactly as the plan specifies. Test-first, one commit."
    crowd = [
        _live_shaped_dispatch_outcome(
            event_id=f"00000000-0000-4000-8000-{index:012d}",
            task=f"{title}\n\n" + ("brief-body-padding " * 500),
        )
        for index in range(201)
    ]
    selection = recall.select_events(crowd, query="", limit_chars=8000)
    assert selection.selected_event_ids, (
        "an empty pack while 201 live-shaped outcomes were available is the defect"
    )
    assert recall.SUMMARY_FORM in selection.selected_forms
    assert title in selection.text
    assert "brief-body-padding " * 8 not in selection.text
    assert len(selection.selected_event_ids) > 1


def test_long_query_does_not_evict_summaries() -> None:
    """The pack header must not inline a task longer than RECALL_LIMIT_CHARS.

    instructions.assemble passes query=task unclipped; matching uses the full
    string while the displayed query line is clipped like scripts/dispatch.py.
    [measured] 261 of 601 live assemblies had empty selection and query length > 8000.
    """
    event_id = "00000000-0000-4000-8000-000000000116"
    event = _oversized_dispatch_outcome(event_id=event_id)
    selection = recall.select_events([event], query="Q" * 9000, limit_chars=8000)
    assert event_id in selection.selected_event_ids
    assert selection.selected_forms == (recall.SUMMARY_FORM,)
    assert not selection.empty_while_available
    assert ("Q" * 400) not in selection.text
    assert len(selection.text) <= 8000


def test_query_matching_uses_the_full_string_not_the_clipped_header() -> None:
    """Clipping the displayed query must not clip the matcher.

    A needle past character 240 of the task still has to select the event that
    carries it; otherwise the header clip would silently change retrieval.
    """
    event_id = "00000000-0000-4000-8000-000000000117"
    event = Event(
        _event(
            event_id=event_id,
            event="note.recorded",
            data={"body": "unique-needle-xyzzy"},
        )
    )
    selection = recall.select_events(
        [event],
        query=("P" * 9000) + " unique-needle-xyzzy",
        limit_chars=8000,
    )
    assert event_id in selection.selected_event_ids
    assert "unique-needle-xyzzy" in selection.text
    assert ("P" * 400) not in selection.text


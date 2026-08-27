"""Tests for the verbatim recall projector."""

from __future__ import annotations

import json

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import events, recall
from consilient.events import Event, SCHEMA_VERSION, VERDICT_KIND, append
from consilient.recall import ALWAYS_INCLUDE_KINDS, pack, parse_receipt


def _pack_body(text: str) -> str:
    marker = "<!-- consilient:recall-receipt:v1"
    index = text.find(marker)
    if index == -1:
        return text
    return text[:index]


def _ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def _event(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "v": SCHEMA_VERSION,
        "ts": _ts(),
        "event": "test.event",
        "actor": "agent",
        "data": {},
    }
    base.update(over)
    return base


def _write(log_dir: Path, *events) -> None:
    for event in events:
        path = log_dir / f"{event['ts'][:10]}.jsonl"
        append(path, event)


def test_empty_log_reports_no_events(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    text = pack(log_dir, query="", limit_chars=1000)
    assert _pack_body(text) == "# Recall pack\n\nNo events in log.\n"
    assert parse_receipt(text)["scanned_universe_count"] == 0


def test_verbatim_field_present_in_pack(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    marker = "unique-verbatim-marker-xyzzy"
    _write(
        log_dir,
        _event(
            event="note.recorded",
            data={"body": marker},
        ),
    )
    text = pack(log_dir, query=marker, limit_chars=5000)
    assert marker in text
    assert f'"body": "{marker}"' in text


def test_omitted_count_footer_when_over_budget(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    for index in range(6):
        _write(
            log_dir,
            _event(
                ts=_ts(index),
                event="note.recorded",
                data={"n": index, "padding": "x" * 80},
            ),
        )
    text = pack(log_dir, query="note", limit_chars=2400)
    assert "omitted to fit character limit" in text
    assert " event(s) omitted" in text


def test_query_filters_non_priority_events(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write(
        log_dir,
        _event(
            ts=_ts(0),
            event="alpha.event",
            data={"topic": "alpha-only"},
        ),
        _event(
            ts=_ts(1),
            event="beta.event",
            data={"topic": "beta-only"},
        ),
    )
    text = pack(log_dir, query="alpha-only", limit_chars=5000)
    assert "alpha-only" in text
    assert "beta-only" not in text


def test_always_include_kinds_ignore_query(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write(
        log_dir,
        _event(
            event="dispatch.refused",
            actor="consilient.dispatch",
            data={
                "reason": "pool exhausted",
                "supervised": False,
            },
        ),
    )
    text = pack(log_dir, query="totally-unrelated-token", limit_chars=5000)
    assert "dispatch.refused" in text
    assert "pool exhausted" in text


def test_human_verdict_kind_is_always_included(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write(
        log_dir,
        _event(
            actor="joe-brown",
            event=VERDICT_KIND,
            data={
                "attempt_id": "attempt-abc",
                "human_verdict": "reject",
                "principal": "joe-brown",
                "via": "cli",
            },
        ),
    )
    text = pack(log_dir, query="missing-keyword", limit_chars=5000)
    assert "attempt-abc" in text
    assert '"human_verdict": "reject"' in text


def test_character_bound_respected(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    for index in range(4):
        _write(
            log_dir,
            _event(
                ts=_ts(index),
                event="note.recorded",
                data={"n": index, "body": "word " * 20},
            ),
        )
    limit = 2400
    text = pack(log_dir, query="note", limit_chars=limit)
    assert len(text) <= limit


def test_always_include_kinds_cover_brief_list():
    assert "dispatch.outcome" in ALWAYS_INCLUDE_KINDS
    assert "dispatch.refused" in ALWAYS_INCLUDE_KINDS
    assert "dispatch.fanout" in ALWAYS_INCLUDE_KINDS
    assert VERDICT_KIND in ALWAYS_INCLUDE_KINDS
    assert "ticket.completed" in ALWAYS_INCLUDE_KINDS


def test_active_commitment_chain_and_source_turns_outlive_ordinary_history() -> None:
    events = [
        Event(
            _event(
                event_id="00000000-0000-4000-8000-000000000001",
                ts=_ts(0),
                event="conversation.turn",
                data={
                    "conversation_id": "conv-1",
                    "turn_id": "turn-1",
                    "text": "original user words verbatim",
                },
            )
        ),
        Event(
            _event(
                event_id="00000000-0000-4000-8000-000000000002",
                ts=_ts(1),
                event="work_item.committed",
                data={
                    "commitment_id": "commit-1",
                    "revision": 1,
                    "conversation_id": "conv-1",
                    "source_turn_ids": ["turn-1"],
                    "goal_text": "original committed goal verbatim",
                },
            )
        ),
        Event(
            _event(
                event_id="00000000-0000-4000-8000-000000000003",
                ts=_ts(2),
                event="conversation.turn",
                data={
                    "conversation_id": "conv-1",
                    "turn_id": "turn-2",
                    "text": "correct the goal verbatim",
                },
            )
        ),
        Event(
            _event(
                event_id="00000000-0000-4000-8000-000000000004",
                ts=_ts(3),
                event="work_item.committed",
                data={
                    "commitment_id": "commit-1",
                    "revision": 2,
                    "conversation_id": "conv-1",
                    "source_turn_ids": ["turn-1", "turn-2"],
                    "goal_text": "corrected active goal verbatim",
                    "authority_ref": {"kind": "principal_required"},
                },
            )
        ),
    ]
    events.extend(
        Event(
            _event(
                event_id=f"00000000-0000-4000-8000-{index:012d}",
                ts=_ts(index + 4),
                event="note.recorded",
                data={"topic": "crowd", "padding": "x" * 300},
            )
        )
        for index in range(10, 20)
    )

    text = recall.pack_events(events, query="crowd", limit_chars=2200)

    assert len(text) <= 2200
    assert "original user words verbatim" in text
    assert "original committed goal verbatim" in text
    assert "correct the goal verbatim" in text
    assert "corrected active goal verbatim" in text
    assert "principal_required" in text
    assert "00000000-0000-4000-8000-000000000004" in text
    active = recall.lookup_event(events, "commit-1")
    assert active is events[3]


def test_dissent_and_adverse_outcomes_are_protected_from_query_filtering() -> None:
    events = [
        Event(
            _event(
                event_id="00000000-0000-4000-8000-000000000021",
                event="review.recorded",
                data={"dissent": "the independent execution disagreed"},
            )
        ),
        Event(
            _event(
                event_id="00000000-0000-4000-8000-000000000022",
                event="attempt.outcome",
                data={"status": "failed", "reason": "verifier rejected artefact"},
            )
        ),
    ]

    text = recall.pack_events(events, query="unrelated-token", limit_chars=5000)

    assert "the independent execution disagreed" in text
    assert "verifier rejected artefact" in text


def test_oversize_active_commitment_reports_direct_stable_id_continuation() -> None:
    commitment = Event(
        _event(
            event_id="00000000-0000-4000-8000-000000000030",
            event="work_item.committed",
            data={
                "commitment_id": "commit-overflow",
                "revision": 1,
                "goal_text": "protected goal " + "x" * 2000,
            },
        )
    )

    assert hasattr(recall, "select_events")
    selection = recall.select_events(
        [commitment], query="unrelated-token", limit_chars=80
    )

    assert len(selection.text) <= 80
    assert not selection.context_complete
    assert selection.continuation_event_id == commitment.raw["event_id"]
    assert commitment.raw["event_id"] in selection.text
    assert selection.omissions[0].event_id == commitment.raw["event_id"]
    assert selection.omissions[0].reason == "context_bound"
    assert (
        recall.lookup_event([commitment], str(commitment.raw["event_id"])) is commitment
    )
    assert recall.lookup_event([commitment], "commit-overflow") is commitment


def test_limit_chars_must_be_positive(tmp_path):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    with pytest.raises(ValueError, match="limit_chars"):
        pack(log_dir, query="", limit_chars=0)


def test_assemble_shrinks_its_scan_window_rather_than_dying_on_a_long_trajectory(
    tmp_path,
):
    """A growing trajectory must not kill every dispatch at startup.

    The recall receipt carries one entry per omitted event, so it grows with the whole log.
    At 1,336 events against an 8,000-character budget it stopped fitting, `_fit_output` raised,
    and every dispatched harness died in `instructions.assemble` before it reached a model --
    six of six failed dispatches on 23 August 2026, including the only Grok run. The scheduler
    reported all of them as dispatched. [measured]

    A fixed window would only move the cliff, so the window halves until the pack fits, and the
    receipt reports `scan_complete` truthfully rather than claiming a scan nothing performed.
    """
    from consilient import instructions

    log = tmp_path / "log"
    log.mkdir()
    day = log / "2026-08-23.jsonl"
    lines = [
        json.dumps(
            {
                "v": events.SCHEMA_VERSION,
                "ts": "2026-08-23T11:59:59+00:00",
                "event": "review.recorded",
                "actor": "test",
                "data": {"dissent": "protected dissent survives the scan window"},
            }
        )
    ]
    for i in range(899):
        lines.append(
            json.dumps(
                {
                    "v": events.SCHEMA_VERSION,
                    "ts": "2026-08-23T12:00:00+00:00",
                    "event": "note.recorded",
                    "actor": "test",
                    "data": {"text": "padding " * 20, "n": i},
                }
            )
        )
    day.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")

    skills = tmp_path / "skills"
    skills.mkdir()
    assembly = instructions.assemble(
        skills, log, task="a task that needs recent history"
    )
    assert assembly is not None

    text = None
    for attr in ("recall", "recall_pack", "recall_text"):
        if hasattr(assembly, attr):
            text = getattr(assembly, attr)
            break
    assert text, "the assembly must carry a recall pack"
    assert "protected dissent survives the scan window" in text
    got = parse_receipt(text)
    assert got["scan_complete"] is False, (
        "a window smaller than the log must not be reported as a complete scan"
    )
    scanned_universe_count = got["scanned_universe_count"]
    assert isinstance(scanned_universe_count, int)
    assert 0 < scanned_universe_count < 900


def _skills_dir(root: Path) -> Path:
    skills = root / "skills"
    skills.mkdir()
    return skills


def _oversized_dispatch_outcome(
    *, event_id: str, padding: int = 9000, **data: object
) -> Event:
    payload: dict[str, object] = {
        "supervised": True,
        "unit": "Z07",
        "harness": "cursor-composer",
        "status": "failed",
        "reason": "START_FAILED -- no artefact within the start window",
        "task": "make the recall pack carry something",
        "padding": "x" * padding,
    }
    payload.update(data)
    return Event(
        _event(
            event_id=event_id,
            event="dispatch.outcome",
            actor="consilient.dispatch",
            data=payload,
        )
    )


def _oversized_capability_gap(*, event_id: str, padding: int = 9000) -> Event:
    return Event(
        _event(
            event_id=event_id,
            event="capability.gap",
            actor="consilient.dispatch",
            data={
                "asked": "assemble a brief",
                "attempted": "recall.pack_events",
                "failure": "not_implemented",
                "detail": "selection dropped every candidate",
                "repair": "project a summary when the full event does not fit",
                "run_id": "20260825T181844-f65a16fcf4",
                "source": "dispatch.outcome",
                "closure": "escalate",
                "padding": "y" * padding,
            },
        )
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


def test_assemble_returns_a_non_empty_pack_for_oversized_always_include_events(
    tmp_path: Path,
) -> None:
    from consilient import instructions

    log = tmp_path / "log"
    log.mkdir()
    events.append(
        log / "2026-08-25.jsonl",
        _oversized_dispatch_outcome(
            event_id="00000000-0000-4000-8000-000000000111"
        ).raw,
    )
    events.append(
        log / "2026-08-25.jsonl",
        _oversized_capability_gap(event_id="00000000-0000-4000-8000-000000000112").raw,
    )
    assembly = instructions.assemble(
        _skills_dir(tmp_path), log, task="carry a recall sentence"
    )
    assert assembly.recall_selection.selected_event_ids
    assert recall.SUMMARY_FORM in assembly.recall_selection.selected_forms
    assert "cursor-composer" in assembly.recall_pack
    assert len(assembly.recall_pack.strip()) > 160


def test_reconstruct_matches_a_full_event_and_a_summary_event(tmp_path: Path) -> None:
    """`instructions.verify` is not a symbol; reconstruct is the replay check."""
    from consilient import instructions

    log = tmp_path / "log"
    log.mkdir()
    skills = _skills_dir(tmp_path)
    events.append(
        log / "2026-08-25.jsonl",
        _event(
            event_id="00000000-0000-4000-8000-000000000113",
            event="note.recorded",
            data={"body": "small enough to travel as a full event"},
        ),
    )
    before = instructions.assemble(skills, log, task="small enough to travel")
    instructions.record_assembly(log, before, task="small enough to travel")
    replayed_before = instructions.reconstruct(log, skills, before.sha256)
    assert replayed_before.ok, [
        layer for layer in replayed_before.layers if not layer.ok
    ]
    assert before.recall_selection.selected_forms in ((), (recall.FULL_FORM,))

    events.append(
        log / "2026-08-25.jsonl",
        _oversized_dispatch_outcome(
            event_id="00000000-0000-4000-8000-000000000114"
        ).raw,
    )
    after = instructions.assemble(skills, log, task="small enough to travel")
    instructions.record_assembly(log, after, task="small enough to travel")
    replayed_after = instructions.reconstruct(log, skills, after.sha256)
    assert replayed_after.ok, [layer for layer in replayed_after.layers if not layer.ok]
    assert recall.SUMMARY_FORM in after.recall_selection.selected_forms


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

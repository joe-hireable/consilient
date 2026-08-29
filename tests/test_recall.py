"""The pack the projector produces: verbatim, bounded, and never silent about what it
left out.

Recall exists to carry the original words rather than a paraphrase of them, so these
tests assert the verbatim field survives into the pack, that the character limit is
honoured exactly, that a non-positive limit is refused, and that anything dropped is
counted rather than simply absent. An empty log says so and the receipt reports a
scanned universe of zero.

The query narrows ordinary history and nothing else. Dispatch outcomes, refusals and
fan-outs, human verdicts, recorded dissent, adverse attempt outcomes, and the active
commitment chain together with the conversation turns that produced it all ignore the
query, because a pack that filtered those out would look complete while having lost the
facts the reader needed most. Where a protected event cannot fit the budget at all, it
must still leave a stable identifier to continue from, so a truncated pack remains a
pointer rather than a dead end."""

from pathlib import Path
import pytest
from consilient import recall
from consilient.events import Event, VERDICT_KIND, append
from consilient.recall import ALWAYS_INCLUDE_KINDS, pack, parse_receipt
from recall_helpers import (
    _event,
    _ts,
)


def _pack_body(text: str) -> str:
    marker = "<!-- consilient:recall-receipt:v1"
    index = text.find(marker)
    if index == -1:
        return text
    return text[:index]


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

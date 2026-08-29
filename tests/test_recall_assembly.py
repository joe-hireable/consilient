"""What `instructions.assemble` actually hands a dispatched harness, and what replay can
reconstruct.

These tests are integration rather than projection, and they exist because the failure
they guard was fatal at startup and invisible above it. The recall receipt carries one
entry per omitted event, so it grows with the whole log; at 1,336 events against an
8,000-character budget it stopped fitting, `_fit_output` raised, and every dispatched
harness died in `instructions.assemble` before it reached a model -- six of six failed
dispatches on 23 August 2026, including the only Grok run, all of which the scheduler
reported as dispatched. [measured]

A fixed window would only move the cliff, so the window halves until the pack fits and
the receipt reports `scan_complete` truthfully rather than claiming a scan that nothing
performed. Protected dissent must survive that shrinking, an oversized always-include
event must still produce a non-empty pack rather than an assembly carrying nothing, and
`reconstruct` must match the recorded assembly for a full event and for a summarised one
alike -- `instructions.verify` is not a symbol, so reconstruct is the replay check."""

import json
from pathlib import Path
from consilient import events, recall
from consilient.recall import parse_receipt
from recall_helpers import (
    _event,
    _oversized_capability_gap,
    _oversized_dispatch_outcome,
)


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

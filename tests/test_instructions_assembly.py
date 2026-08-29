"""What `assemble` selects, how large it may become, and what the receipt records.

Selection is deterministic and bounded, an empty task is refused, and the assembled text
stays within the sum of its declared per-layer limits plus a fixed overhead.

V0-47 is the receipt: every assembly is recorded with the identity of every layer,
including the recall selection's digest and the omitted events' digest and count. The
count and digest — not the list — are the whole point. Inlining `omitted` beside the
digest is the compounding loop that took the trajectory to 40 MB; measured 24 Aug 2026,
454 omissions inlined to roughly 110 KB on a single written line, which is why one test
holds that line under 8 KB.

These tests pin the logged jsonl artefact rather than the helper that builds it, because
a mutant that re-spreads the omission list next to the digest still passes a test that
only inspects `_selection_receipt()`."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest
from consilient import instructions, promote
from consilient.events import append, canonical, read_all
from consilient.instructions import (
    ADAPTED_LIMIT_CHARS,
    ASSEMBLED,
    CORE_VERSION,
    INERT,
    RECALL_LIMIT_CHARS,
    SKILL_CHARS,
    AdaptedLayer,
    Assembly,
    assemble,
    reconstruct,
    record_assembly,
    select_skills,
)
from consilient.recall import Omission, Selection
from instructions_helpers import (
    note,
    now,
    record_event,
    skills_tree,
)


def test_every_assembly_is_recorded_with_the_identity_of_every_layer(tmp_path: Path):
    """V0-47."""
    selected = note(tmp_path, "beta work continued")
    note(tmp_path, "zanzibar quixotic")
    skills = skills_tree(tmp_path)
    assembly = assemble(skills, tmp_path, task="measure the beta verifier outcome")
    event = record_assembly(
        tmp_path, assembly, task="measure the beta verifier outcome"
    )

    assert event["event"] == ASSEMBLED
    data = event["data"]
    assert data["assembly_id"] == assembly.sha256
    assert data["core"]["version"] == instructions.CORE_VERSION
    assert len(data["core"]["sha256"]) == 64
    assert [skill["name"] for skill in data["skills"]] == ["alpha-skill"]
    assert data["skills"][0]["matched"] == ["beta", "verifier"]
    assert len(data["skills"][0]["sha256"]) == 64
    assert data["recall"]["source_events"] == 2
    assert len(data["recall"]["source_digest"]) == 64
    assert data["recall"]["sha256"] == promote.digest(assembly.recall_pack)
    assert data["recall"]["selected_event_ids"] == [selected["event_id"]]
    assert (
        data["recall"]["selected_digest"]
        == hashlib.sha256(canonical(selected).encode("utf-8")).hexdigest()
    )
    # The receipt records a digest and a count, not the omission list -- inlining the list is
    # what took the trajectory to 40 MB. Pin the LOGGED EVENT, not the helper: a mutant that
    # re-spreads `omitted` next to the digest still passes tests that only inspect
    # `_selection_receipt()`.
    assert "omitted" not in data["recall"]
    assert data["recall"]["omitted_count"] == 0
    assert data["recall"]["omitted_digest"] == instructions._omitted_digest([])
    assert data["recall"]["context_complete"] is True
    assert data["recall"]["continuation"] is None
    assert data["adapted"]["status"] == INERT

    events, rejected = read_all(tmp_path)
    assert not rejected
    assert events[-1].kind == ASSEMBLED


def test_overflow_metadata_points_to_omitted_protected_event_and_reconstructs(
    tmp_path: Path,
) -> None:
    protected = record_event(
        tmp_path,
        "review.recorded",
        {"dissent": "protected dissent", "padding": "x" * 2000},
    )
    for index in range(4):
        note(tmp_path, f"crowd {index} " + "y" * 200)
    skills = skills_tree(tmp_path)

    assembly = assemble(
        skills,
        tmp_path,
        task="crowd",
        recall_limit_chars=300,
    )
    repeated = assemble(
        skills,
        tmp_path,
        task="crowd",
        recall_limit_chars=300,
    )

    assert repeated.recall_pack == assembly.recall_pack
    assert repeated.sha256 == assembly.sha256
    event = record_assembly(tmp_path, assembly, task="crowd")
    recall_data = event["data"]["recall"]
    assert recall_data["context_complete"] is False
    assert recall_data["continuation"] == {"event_id": protected["event_id"]}
    # The compounding loop wrote `data.recall.omitted` onto instructions.assembled.
    # Pin that the logged event -- not the in-memory selection -- no longer carries it.
    assert "omitted" not in recall_data
    omitted_rows = instructions._omission_rows(assembly.recall_selection)
    assert {
        "event_id": protected["event_id"],
        "event_kind": "review.recorded",
        "reason": "context_bound",
        "protected": True,
    } in omitted_rows
    assert recall_data["omitted_digest"] == instructions._omitted_digest(omitted_rows)
    assert recall_data["omitted_count"] >= 1
    assert str(protected["event_id"]) in assembly.recall_pack

    result = reconstruct(tmp_path, skills, assembly.sha256)
    assert result.ok, [report for report in result.layers if not report.ok]
    repo = Path(__file__).parents[1]
    environment = os.environ | {"PYTHONPATH": str(repo / "src")}
    fresh = subprocess.run(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; "
            "from consilient.instructions import reconstruct; "
            "result = reconstruct(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]); "
            "raise SystemExit(0 if result.ok else 1)",
            str(tmp_path),
            str(skills),
            assembly.sha256,
        ],
        cwd=repo,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert fresh.returncode == 0, fresh.stderr

    event["data"]["recall"]["selected_digest"] = "0" * 64
    event.pop("event_id")
    event["ts"] = now()
    append(tmp_path / f"{event['ts'][:10]}.jsonl", event)
    drift = reconstruct(tmp_path, skills, assembly.sha256)
    assert not drift.ok
    assert "selection receipt" in next(
        report.detail for report in drift.layers if report.layer == "recall"
    )


def _selection_with_omissions(count: int) -> Selection:
    return Selection(
        text="# Recall pack\n\nNo events match query.\n",
        selected_event_ids=(),
        selected_digest="0" * 64,
        omissions=tuple(
            Omission(
                event_id=f"evt-{index:04d}",
                event_kind="conversation.turn",
                reason="budget",
                protected=False,
            )
            for index in range(count)
        ),
        context_complete=False,
        continuation_event_id=None,
    )


def _stub_assembly(selection: Selection) -> Assembly:
    pack = selection.text
    return Assembly(
        core_version=CORE_VERSION,
        skills=(),
        skills_omitted=0,
        recall_pack=pack,
        recall_selection=selection,
        recall_limit_chars=300,
        recall_source_events=0,
        recall_source_digest=promote.digest(""),
        adapted=AdaptedLayer(INERT, "", None),
        text="stub",
        sha256=promote.digest("stub"),
        capability_manifests=(),
        recall_receipt={"status": "ok", "digest": "0" * 64},
    )


def _logged_recall(tmp_path: Path, event: dict[str, object]) -> dict[str, object]:
    """The recall object as written to the jsonl artefact, not the in-memory return."""
    log_path = tmp_path / f"{str(event['ts'])[:10]}.jsonl"
    line = log_path.read_bytes().splitlines()[-1]
    recorded = json.loads(line.decode("utf-8"))
    recall_data = recorded["data"]["recall"]
    assert isinstance(recall_data, dict)
    return recall_data


def test_a_logged_assembled_event_does_not_inline_the_omission_list(
    tmp_path: Path,
) -> None:
    """Z01 artefact pin. The helper `_selection_receipt` was already slim; the event was not."""
    event = record_assembly(
        tmp_path, _stub_assembly(_selection_with_omissions(454)), task="crowd"
    )
    assert event["event"] == ASSEMBLED
    assert "omitted" not in event["data"]["recall"]
    logged = _logged_recall(tmp_path, event)
    assert "omitted" not in logged
    assert logged["omitted_count"] == 454
    assert isinstance(logged["omitted_digest"], str) and logged["omitted_digest"]


def test_a_logged_assembled_event_that_used_to_be_110kb_is_under_8kb(
    tmp_path: Path,
) -> None:
    """Measured 24 Aug 2026: 454 omissions inlined to ~110 KB. Hold the written line under 8 KB."""
    event = record_assembly(
        tmp_path, _stub_assembly(_selection_with_omissions(454)), task="crowd"
    )
    log_path = tmp_path / f"{str(event['ts'])[:10]}.jsonl"
    line = log_path.read_bytes().splitlines()[-1]
    assert len(line) < 8192, (
        f"instructions.assembled jsonl line is {len(line)} B; inlining omitted "
        "is the compounding loop that took the trajectory to 40 MB"
    )
    assert b'"omitted":' not in line


def test_select_skills_is_deterministic_bounded_and_records_why(tmp_path: Path):
    skills = skills_tree(tmp_path)
    task = "measure the beta verifier outcome"
    first, _ = select_skills(skills, task)
    second, _ = select_skills(skills, task)
    assert first == second
    assert [skill.name for skill in first] == ["alpha-skill"]
    assert first[0].matched == ("beta", "verifier")

    none, _ = select_skills(skills, "completely unrelated zanzibar quixotic")
    assert none == ()

    chosen, omitted = select_skills(skills, task, budget_chars=10)
    assert chosen == ()
    assert omitted == 1


def test_the_assembly_text_is_bounded(tmp_path: Path):
    for index in range(40):
        note(tmp_path, f"event {index} about beta and verifier outcomes " + "x" * 400)
    skills = skills_tree(tmp_path)
    assembly = assemble(skills, tmp_path, task="measure the beta verifier outcome")
    overhead = 2000
    bound = (
        len(assembly.text.split(instructions.SKILLS_HEADER)[0])
        + SKILL_CHARS
        + RECALL_LIMIT_CHARS
        + ADAPTED_LIMIT_CHARS
        + overhead
    )
    assert len(assembly.text) <= bound
    assert len(assembly.recall_pack) <= RECALL_LIMIT_CHARS


def test_an_empty_task_is_refused(tmp_path: Path):
    skills = skills_tree(tmp_path)
    with pytest.raises(ValueError, match="may not be empty"):
        assemble(skills, tmp_path, task="   ")

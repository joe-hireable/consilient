"""Replaying a recorded assembly out of the trajectory, and reporting honestly where it
no longer matches.

All four layers — core, skills, recall, adapted — are checked; drift in a skill body is
named in the report rather than swallowed; a missing event comes back as not found
rather than as a pass; and the adapted layer is replayed as of the assembly, not as of
now, so an assembly recorded before a promotion still reconstructs after it.

Two tests hold the omitted-digest change honest in both directions. An event recorded
before the change still carries the full omitted list and must still verify, because
events already in a trajectory cannot be rewritten. A digest-era event that also inlines
the list must not verify: that co-resident fat list is the mutant which previously still
passed."""

import copy
from pathlib import Path
from consilient import instructions
from consilient.events import append
from consilient.instructions import (
    ACTIVE,
    INERT,
    assemble,
    reconstruct,
    record_assembly,
)
from instructions_helpers import (
    note,
    now,
    promoted_layer,
    record_event,
    skills_tree,
)


def test_reconstruct_matches_an_event_recorded_after_the_digest_change(
    tmp_path: Path,
) -> None:
    note(tmp_path, "beta work continued")
    skills = skills_tree(tmp_path)
    assembly = assemble(skills, tmp_path, task="measure the beta verifier outcome")
    record_assembly(tmp_path, assembly, task="measure the beta verifier outcome")
    result = reconstruct(tmp_path, skills, assembly.sha256)
    assert result.ok, [report for report in result.layers if not report.ok]
    recall_layer = next(report for report in result.layers if report.layer == "recall")
    assert recall_layer.ok


def test_reconstruct_matches_an_event_recorded_with_the_old_fat_omitted_list(
    tmp_path: Path,
) -> None:
    """Back-compatibility. Events already in the trajectory carry the full list."""
    protected = record_event(
        tmp_path,
        "review.recorded",
        {"dissent": "protected dissent", "padding": "x" * 2000},
    )
    for index in range(4):
        note(tmp_path, f"crowd {index} " + "y" * 200)
    skills = skills_tree(tmp_path)
    assembly = assemble(skills, tmp_path, task="crowd", recall_limit_chars=300)
    recorded = record_assembly(tmp_path, assembly, task="crowd")
    legacy = copy.deepcopy(recorded)
    legacy.pop("event_id")
    legacy["ts"] = now()
    recall = legacy["data"]["recall"]
    recall.pop("omitted_digest")
    recall.pop("omitted_count")
    recall["omitted"] = instructions._omission_rows(assembly.recall_selection)
    append(tmp_path / f"{legacy['ts'][:10]}.jsonl", legacy)
    result = reconstruct(tmp_path, skills, assembly.sha256)
    assert result.ok, [report for report in result.layers if not report.ok]
    recall_layer = next(report for report in result.layers if report.layer == "recall")
    assert recall_layer.ok
    assert str(protected["event_id"]) in assembly.recall_pack


def test_reconstruct_rejects_a_digest_era_event_that_still_inlines_omitted(
    tmp_path: Path,
) -> None:
    """A co-resident fat list is the mutant that previously still verified."""
    note(tmp_path, "beta work continued")
    skills = skills_tree(tmp_path)
    assembly = assemble(skills, tmp_path, task="measure the beta verifier outcome")
    recorded = record_assembly(
        tmp_path, assembly, task="measure the beta verifier outcome"
    )
    bloated = copy.deepcopy(recorded)
    bloated.pop("event_id")
    bloated["ts"] = now()
    bloated["data"]["recall"]["omitted"] = instructions._omission_rows(
        assembly.recall_selection
    )
    append(tmp_path / f"{bloated['ts'][:10]}.jsonl", bloated)
    result = reconstruct(tmp_path, skills, assembly.sha256)
    assert not result.ok
    recall_layer = next(report for report in result.layers if report.layer == "recall")
    assert not recall_layer.ok
    assert "inlines omitted" in recall_layer.detail


def test_an_assembly_is_reconstructable_after_the_fact(tmp_path: Path):
    note(tmp_path, "first")
    skills = skills_tree(tmp_path)
    assembly = assemble(skills, tmp_path, task="measure the beta verifier outcome")
    record_assembly(tmp_path, assembly, task="measure the beta verifier outcome")
    note(tmp_path, "the log kept growing after the assembly")

    result = reconstruct(tmp_path, skills, assembly.sha256)
    assert result.found
    assert result.ok, [r for r in result.layers if not r.ok]
    assert {r.layer for r in result.layers} == {"core", "skills", "recall", "adapted"}


def test_reconstruction_reports_skill_drift(tmp_path: Path):
    skills = skills_tree(tmp_path)
    assembly = assemble(skills, tmp_path, task="measure the beta verifier outcome")
    record_assembly(tmp_path, assembly, task="measure the beta verifier outcome")

    (skills / "alpha-skill" / "SKILL.md").write_text("drifted\n", encoding="utf-8")
    result = reconstruct(tmp_path, skills, assembly.sha256)
    assert result.found
    assert not result.ok
    drift = {r.layer: r for r in result.layers}
    assert not drift["skills"].ok
    assert "drifted" in drift["skills"].detail
    assert drift["core"].ok
    assert drift["recall"].ok


def test_reconstruction_reports_a_missing_event(tmp_path: Path):
    result = reconstruct(tmp_path, tmp_path, "0" * 64)
    assert not result.found
    assert not result.ok


def test_reconstruction_replays_the_adapted_layer_as_of_the_assembly(tmp_path: Path):
    skills = skills_tree(tmp_path)
    before = assemble(skills, tmp_path, task="measure the beta verifier outcome")
    record_assembly(tmp_path, before, task="measure the beta verifier outcome")
    assert before.adapted.status == INERT

    promoted_layer(tmp_path)
    after = assemble(skills, tmp_path, task="measure the beta verifier outcome")
    assert after.adapted.status == ACTIVE

    earlier = reconstruct(tmp_path, skills, before.sha256)
    assert earlier.ok
    record_assembly(tmp_path, after, task="measure the beta verifier outcome")
    later = reconstruct(tmp_path, skills, after.sha256)
    assert later.ok

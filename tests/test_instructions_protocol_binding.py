"""Binding a fired threshold to evidence that can be reconstructed, and refusing every
route around it.

The existing selector does not choose the better-than-best skill for this task on
wording alone — that is what the first test establishes — so it is the firing threshold,
not the vocabulary, that puts the skill into the assembly. A non-firing threshold does
not force it in, and cannot be handed completion artefacts to fabricate a completion it
did not earn.

Everything else here is adversarial. A binding requires an earlier same-task assembly
already on the trajectory: not one recorded for a different task, not one that arrives
after the event prefix being bound. The recorded skill must reconstruct, so substituting
the skill digest, forging the assembly id, or drifting the skill body on disk each
refuse. What is finally bound is the reconstructed name, path, digest and body together
with the bar, search and killing-check references, so that a claim to have located the
bar carries the artefacts which would falsify it."""

from datetime import datetime, timezone
from pathlib import Path
import pytest
from consilient import promote
from consilient.events import SCHEMA_VERSION, append, event_sha256, read_all
from consilient.instructions import (
    ASSEMBLED,
    BETTER_THAN_BEST_NAME,
    InstructionError,
    ProtocolThreshold,
    assemble,
    bind_protocol,
    reconstruct,
    record_assembly,
    select_skills,
)
from instructions_helpers import (
    now,
    skills_tree,
)

BETTER_THAN_BEST_BODY = (
    "---\n"
    "name: better-than-best\n"
    "description: Use when a later decision turns on beating the best existing answer.\n"
    "---\n\n"
    "Locate the bar, then beat it. Name the killing check.\n"
)


def with_better_than_best(skills: Path) -> Path:
    folder = skills / BETTER_THAN_BEST_NAME
    folder.mkdir()
    (folder / "SKILL.md").write_text(BETTER_THAN_BEST_BODY, encoding="utf-8")
    return skills


def artefact(log_dir: Path, claim: str) -> dict[str, str]:
    raw = append(
        log_dir / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now(),
            "event": "evidence.observed",
            "actor": "test",
            "data": {"claim": claim},
        },
    )
    return {
        "event_id": str(raw["event_id"]),
        "event_kind": str(raw["event"]),
        "event_sha256": event_sha256(raw),
    }


def firing_threshold() -> ProtocolThreshold:
    return ProtocolThreshold("true", "true", "true")


def skipped_threshold() -> ProtocolThreshold:
    return ProtocolThreshold("false", "true", "true")


def test_existing_selector_lacks_the_three_condition_binding(tmp_path: Path) -> None:
    skills = with_better_than_best(skills_tree(tmp_path))
    task = "measure the beta verifier outcome"
    chosen, _ = select_skills(skills, task)
    assert BETTER_THAN_BEST_NAME not in [skill.name for skill in chosen]

    assembly = assemble(skills, tmp_path, task=task)
    assert BETTER_THAN_BEST_NAME not in [skill.name for skill in assembly.skills]


def test_a_firing_threshold_selects_the_existing_skill_for_the_same_task(
    tmp_path: Path,
) -> None:
    skills = with_better_than_best(skills_tree(tmp_path))
    task = "measure the beta verifier outcome"
    assembly = assemble(skills, tmp_path, task=task, threshold=firing_threshold())
    selected = [
        skill for skill in assembly.skills if skill.name == BETTER_THAN_BEST_NAME
    ]
    assert len(selected) == 1
    skill = selected[0]
    assert skill.path.endswith(f"{BETTER_THAN_BEST_NAME}/SKILL.md")
    assert skill.sha256 == promote.digest(BETTER_THAN_BEST_BODY)
    assert skill.body == BETTER_THAN_BEST_BODY

    event = record_assembly(tmp_path, assembly, task=task)
    recorded = event["data"]["skills"]
    assert any(
        entry["name"] == BETTER_THAN_BEST_NAME
        and entry["path"] == skill.path
        and entry["sha256"] == skill.sha256
        for entry in recorded
    )


def test_a_non_firing_threshold_does_not_force_the_skill(tmp_path: Path) -> None:
    skills = with_better_than_best(skills_tree(tmp_path))
    assembly = assemble(
        skills,
        tmp_path,
        task="measure the beta verifier outcome",
        threshold=skipped_threshold(),
    )
    assert BETTER_THAN_BEST_NAME not in [skill.name for skill in assembly.skills]


def test_a_firing_threshold_cannot_validate_without_the_earlier_same_task_assembly(
    tmp_path: Path,
) -> None:
    skills = with_better_than_best(skills_tree(tmp_path))
    bar = artefact(tmp_path, "bar")
    search = artefact(tmp_path, "search")
    killing = artefact(tmp_path, "killing-check")

    with pytest.raises(InstructionError, match="earlier same-task"):
        bind_protocol(
            tmp_path,
            skills,
            task="measure the beta verifier outcome",
            threshold=firing_threshold(),
            bar_ref=bar,
            search_ref=search,
            killing_check_ref=killing,
        )


def test_wrong_task_late_assembly_digest_substitution_and_body_mismatch_are_refused(
    tmp_path: Path,
) -> None:
    skills = with_better_than_best(skills_tree(tmp_path))
    bar = artefact(tmp_path, "bar")
    search = artefact(tmp_path, "search")
    killing = artefact(tmp_path, "killing-check")
    task = "measure the beta verifier outcome"

    other = assemble(
        skills,
        tmp_path,
        task="plant tulip bulbs in autumn",
        threshold=firing_threshold(),
    )
    record_assembly(tmp_path, other, task="plant tulip bulbs in autumn")
    with pytest.raises(InstructionError, match="same-task"):
        bind_protocol(
            tmp_path,
            skills,
            task=task,
            threshold=firing_threshold(),
            bar_ref=bar,
            search_ref=search,
            killing_check_ref=killing,
        )

    prefix, _ = read_all(tmp_path)
    later = assemble(skills, tmp_path, task=task, threshold=firing_threshold())
    recorded = record_assembly(tmp_path, later, task=task)
    with pytest.raises(InstructionError, match="earlier same-task"):
        bind_protocol(
            tmp_path,
            skills,
            task=task,
            threshold=firing_threshold(),
            bar_ref=bar,
            search_ref=search,
            killing_check_ref=killing,
            events=prefix,
        )

    substituted = dict(recorded)
    substituted.pop("event_id", None)
    substituted["ts"] = now()
    data = dict(substituted["data"])
    skills_payload = [dict(entry) for entry in data["skills"]]
    for entry in skills_payload:
        if entry["name"] == BETTER_THAN_BEST_NAME:
            entry["sha256"] = "0" * 64
    data["skills"] = skills_payload
    data["assembly_id"] = "1" * 64
    substituted["data"] = data
    append(tmp_path / f"{substituted['ts'][:10]}.jsonl", substituted)
    with pytest.raises(InstructionError, match="reconstruct|digest"):
        bind_protocol(
            tmp_path,
            skills,
            task=task,
            threshold=firing_threshold(),
            bar_ref=bar,
            search_ref=search,
            killing_check_ref=killing,
        )

    (skills / BETTER_THAN_BEST_NAME / "SKILL.md").write_text(
        BETTER_THAN_BEST_BODY + "drifted body\n", encoding="utf-8"
    )
    with pytest.raises(InstructionError, match="reconstruct"):
        bind_protocol(
            tmp_path,
            skills,
            task=task,
            threshold=firing_threshold(),
            bar_ref=bar,
            search_ref=search,
            killing_check_ref=killing,
        )


def test_a_firing_threshold_binds_reconstructed_name_path_digest_and_body(
    tmp_path: Path,
) -> None:
    skills = with_better_than_best(skills_tree(tmp_path))
    bar = artefact(tmp_path, "bar")
    search = artefact(tmp_path, "search")
    killing = artefact(tmp_path, "killing-check")
    task = "measure the beta verifier outcome"
    assembly = assemble(skills, tmp_path, task=task, threshold=firing_threshold())
    recorded = record_assembly(tmp_path, assembly, task=task)

    binding = bind_protocol(
        tmp_path,
        skills,
        task=task,
        threshold=firing_threshold(),
        bar_ref=bar,
        search_ref=search,
        killing_check_ref=killing,
    )
    assert binding.status == "completed"
    assert binding.instructions_ref == {
        "event_id": recorded["event_id"],
        "event_kind": ASSEMBLED,
        "event_sha256": event_sha256(recorded),
    }
    assert binding.bar_ref == bar
    assert binding.search_ref == search
    assert binding.killing_check_ref == killing

    result = reconstruct(tmp_path, skills, assembly.sha256)
    assert result.ok
    skill = next(item for item in assembly.skills if item.name == BETTER_THAN_BEST_NAME)
    replayed = (skills / BETTER_THAN_BEST_NAME / "SKILL.md").read_text(encoding="utf-8")
    assert replayed == skill.body
    assert promote.digest(replayed) == skill.sha256
    assert skill.path.endswith(f"{BETTER_THAN_BEST_NAME}/SKILL.md")


def test_a_non_firing_threshold_cannot_be_forced_to_fabricate_completion_artefacts(
    tmp_path: Path,
) -> None:
    skills = with_better_than_best(skills_tree(tmp_path))
    bar = artefact(tmp_path, "bar")
    search = artefact(tmp_path, "search")
    killing = artefact(tmp_path, "killing-check")
    task = "measure the beta verifier outcome"
    assembly = assemble(skills, tmp_path, task=task, threshold=firing_threshold())
    record_assembly(tmp_path, assembly, task=task)

    with pytest.raises(InstructionError, match="completion artefact"):
        bind_protocol(
            tmp_path,
            skills,
            task=task,
            threshold=skipped_threshold(),
            bar_ref=bar,
            search_ref=search,
            killing_check_ref=killing,
        )

    binding = bind_protocol(tmp_path, skills, task=task, threshold=skipped_threshold())
    assert binding.status == "not_warranted"
    assert binding.instructions_ref is None
    assert binding.bar_ref is None
    assert binding.search_ref is None
    assert binding.killing_check_ref is None
    assert binding.threshold.false_reasons == ("later_reliance",)

"""Checks for the EXP-08 known-bad critic corpus builder.

Regenerates the manifest from the seed and asserts it is byte-identical to the
committed artefact. Also asserts the pairing invariants: no bad arm fails a
composite check, no control carries a mutation, and every bad mutation sits
inside a path its unit claims.

    python -m pytest docs/10-research/experiments/exp08/test_build_corpus.py -q
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_corpus as B


def _source_document() -> dict:
    return json.loads(B.SOURCE_RESULTS.read_text(encoding="utf-8"))


def test_source_is_the_20_aug_record_not_the_22_aug_trap():
    """results-exp47.json is the empty 22 Aug re-run; the register's live record is dated."""
    document = _source_document()
    assert B.SOURCE_RESULTS.name == "results-exp47-2026-08-20.json"
    counts = B.verify_source_excludes_equivalents(document)
    assert counts["non_equivalent_survivors"] == 586
    assert counts["equivalent_mutants_excluded_by_exp47"] == 60
    assert document["timestamp"].startswith("2026-08-20")


def test_source_check_rejects_the_empty_trap_document():
    trap = json.loads(
        (B.ROOT / "docs/10-research/experiments/exp47/results-exp47.json").read_text(
            encoding="utf-8"
        )
    )
    assert trap["raw_counts"]["true_defects_survived"] == 0
    with pytest.raises(RuntimeError, match="empty|reconcile|trap|weakest_guards"):
        B.verify_source_excludes_equivalents(trap)

    doctored = copy.deepcopy(_source_document())
    doctored["raw_counts"]["equivalent_mutants"] = 0
    with pytest.raises(RuntimeError):
        B.verify_source_excludes_equivalents(doctored)

    truncated = copy.deepcopy(_source_document())
    truncated["weakest_guards"] = truncated["weakest_guards"][:-1]
    with pytest.raises(RuntimeError):
        B.verify_source_excludes_equivalents(truncated)


def test_locate_requires_a_unique_line():
    lines = ["a = 1", "b = 2", "a = 1", "c = 3"]
    assert B.locate("b = 2", lines) == 1
    assert B.locate("  b = 2  ", lines) == 1
    assert B.locate("a = 1", lines) is None
    assert B.locate("z = 9", lines) is None


def test_classify_records_exclusions_instead_of_dropping_silently():
    sources = {"src/consilient/beta.py": "x = 1\ny = 2\ny = 2\n"}
    guards = [
        {
            "id": 1,
            "file": "src/consilient/beta.py",
            "line": 1,
            "operator": "o",
            "orig_snippet": "x = 1",
            "mut_snippet": "x = 2",
        },
        {
            "id": 2,
            "file": "src/consilient/beta.py",
            "line": 2,
            "operator": "o",
            "orig_snippet": "y = 2",
            "mut_snippet": "y = 3",
        },
        {
            "id": 3,
            "file": "tests/test_beta.py",
            "line": 1,
            "operator": "o",
            "orig_snippet": "x = 1",
            "mut_snippet": "x = 2",
        },
        {
            "id": 4,
            "file": "src/consilient/beta.py",
            "line": 1,
            "operator": "o",
            "orig_snippet": "a\nb",
            "mut_snippet": "c",
        },
        {
            "id": 5,
            "file": "src/consilient/beta.py",
            "line": 1,
            "operator": "o",
            "orig_snippet": "q" * 120,
            "mut_snippet": "r",
        },
        {
            "id": 6,
            "file": "src/consilient/beta.py",
            "line": 1,
            "operator": "o",
            "orig_snippet": "x = 1",
            "mut_snippet": "x = 1",
        },
        {
            "id": 7,
            "file": "src/consilient/beta.py",
            "line": 1,
            "operator": "o",
            "orig_snippet": "nope",
            "mut_snippet": "n",
        },
    ]
    included, exclusions = B.classify_guards(guards, sources)
    assert [g["id"] for g in included] == [1]
    assert any(e["reason"] == "tests_path" for e in exclusions)
    assert any(e["reason"] == "multiline" for e in exclusions)
    assert any(e["reason"] == "truncated" for e in exclusions)
    assert any(e["reason"] == "equivalent_snippet" for e in exclusions)
    assert any(e["reason"] == "not_uniquely_locatable" for e in exclusions)
    assert len(included) + len(exclusions) == len(guards)


def test_refuses_to_mutate_tests_even_if_the_snippet_locates():
    sources = {"tests/test_beta.py": "assert True\n"}
    included, exclusions = B.classify_guards(
        [
            {
                "id": 9,
                "file": "tests/test_beta.py",
                "line": 1,
                "operator": "o",
                "orig_snippet": "assert True",
                "mut_snippet": "assert False",
            }
        ],
        sources,
    )
    assert included == []
    assert exclusions[0]["reason"] == "tests_path"


def test_canonical_dump_is_stable():
    payload = {"b": 2, "a": 1}
    first = B.canonical_dump(payload)
    second = B.canonical_dump(payload)
    assert first == second
    assert first.endswith("\n")
    assert first.startswith("{")


def test_manifest_regenerates_byte_identical_from_the_seed():
    regenerated = B.canonical_dump(B.build_manifest()).encode("utf-8")
    committed = B.CORPUS.read_bytes().replace(b"\r\n", b"\n")
    assert committed == regenerated


def test_at_least_120_verified_pairs():
    manifest = json.loads(B.CORPUS.read_text(encoding="utf-8"))
    assert manifest["seed"] == B.SEED
    assert len(manifest["pairs"]) >= 120
    assert manifest["n_pairs"] == len(manifest["pairs"])


def test_no_bad_item_fails_ruff_or_mypy():
    """[measured 26 August 2026] Both are genuinely invoked (control-baselined so
    pre-existing debt at SNAPSHOT_REV doesn't count) -- not a hardcoded label.
    pytest is honestly reported as not_verified: no unit-to-test mapping exists
    to scope a real per-pair run, and 240 full-suite runs is not a cost this
    builder can pay. A composite survivor is expected to pass both cleanly; a
    "fail" here means the mutation is not the kind EXP-08 wants and should be
    investigated, not silently accepted.
    """
    manifest = json.loads(B.CORPUS.read_text(encoding="utf-8"))
    for pair in manifest["pairs"]:
        checks = pair["bad"]["checks"]
        for name in ("mypy", "ruff"):
            assert checks[name] == "pass", (pair["pair_id"], name, checks[name])
        assert checks["pytest"] == "not_verified", (pair["pair_id"], checks["pytest"])


def test_no_control_carries_a_mutation():
    manifest = json.loads(B.CORPUS.read_text(encoding="utf-8"))
    for pair in manifest["pairs"]:
        control = pair["control"]
        assert control["mutated"] is False
        assert control["snapshot_digest"] != pair["bad"]["snapshot_digest"]
        assert pair["bad"]["mutated"] is True


def test_every_bad_mutation_lies_inside_a_path_its_unit_claims():
    manifest = json.loads(B.CORPUS.read_text(encoding="utf-8"))
    units = B.load_plan_units()
    for pair in manifest["pairs"]:
        claims = units[pair["unit_id"]]["claims"]
        assert pair["file"] in claims
        assert pair["file"].startswith("src/consilient/")
        assert not pair["file"].startswith("tests/")


def test_exclusions_are_recorded_with_reasons_and_counts():
    manifest = json.loads(B.CORPUS.read_text(encoding="utf-8"))
    assert manifest["exclusions"], "exclusion rate must be visible"
    counts = manifest["exclusion_counts"]
    assert counts == B.count_reasons(manifest["exclusions"])
    assert sum(counts.values()) == len(manifest["exclusions"])


def test_snapshot_is_the_exp47_20_aug_commit():
    manifest = json.loads(B.CORPUS.read_text(encoding="utf-8"))
    assert manifest["snapshot_rev"].startswith("d579bee")
    for pair in manifest["pairs"]:
        assert pair["base_commit"] == manifest["snapshot_rev"]
        assert pair["seed"] == manifest["seed"]
        assert pair["orig_snippet"].strip() != pair["mut_snippet"].strip()


def test_verify_arm_actually_invokes_ruff_and_mypy():
    """[measured 26 August 2026] build_corpus.py previously wrote a hardcoded
    {'pytest': 'pass', 'mypy': 'pass', 'ruff': 'pass'} without invoking any
    tool -- swapping it for all-fail values still left every corpus test
    green. verify_arm must genuinely run the tools: a real ruff violation and
    a real mypy --strict violation, introduced fresh (not present in the
    control baseline), must each report "fail".
    """
    scratch = B._scratch_worktree()
    try:
        rel_path = "src/consilient/__init__.py"
        pristine = B.git_show(B.SNAPSHOT_REV, rel_path)
        baseline = {
            "ruff": B._ruff_codes(scratch, rel_path),
            "mypy": B._mypy_codes(scratch, rel_path),
        }

        clean = B.verify_arm(scratch, rel_path, pristine, baseline)
        assert clean == {"ruff": "pass", "mypy": "pass", "pytest": "not_verified"}

        ruff_broken = pristine + "\nimport os\n"  # unused import: F401
        broken_checks = B.verify_arm(scratch, rel_path, ruff_broken, baseline)
        assert broken_checks["ruff"] == "fail"

        mypy_broken = (
            pristine + "\ndef _exp08_probe() -> int:\n    return 'not an int'\n"
        )
        broken_mypy = B.verify_arm(scratch, rel_path, mypy_broken, baseline)
        assert broken_mypy["mypy"] == "fail"
    finally:
        B._remove_scratch_worktree(scratch)

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXP56 = ROOT / "docs/10-research/experiments/exp56"
sys.path.insert(0, str(EXP56))

from run_exp56 import MODEL_IDS, REGISTRATION_COMMIT, audit_inputs  # noqa: E402


MODEL_LISTING = "auto - Auto (default)\n" + "\n".join(
    f"{model_id} - verified fixture" for model_id in MODEL_IDS
)


def complete_exp47():
    manifest = {}
    for path in ("src/consilient/beta.py", "tests/test_budget.py"):
        blob = subprocess.run(
            ["git", "show", f"{REGISTRATION_COMMIT}:{path}"],
            cwd=ROOT,
            capture_output=True,
            timeout=30,
            check=True,
        ).stdout
        manifest[path] = hashlib.sha256(blob).hexdigest()
    mutants = [
        {
            "id": index,
            "outcome": "killed",
            "classification": "non_equivalent",
            "source_region": "def f():\n    return 0\n",
            "covering_tests": ["def test_f():\n    assert f() == 0\n"],
        }
        for index in range(1285)
    ]
    mutants += [
        {
            "id": index,
            "outcome": "survived",
            "classification": "equivalent",
            "source_region": "def f():\n    return 0\n",
            "covering_tests": ["def test_f():\n    assert f() == 0\n"],
        }
        for index in range(1285, 1345)
    ]
    mutants += [
        {
            "id": index,
            "outcome": "survived",
            "classification": "non_equivalent",
            "source_region": "def f():\n    return 1\n",
            "covering_tests": ["def test_f():\n    assert f() == 0\n"],
        }
        for index in range(1345, 1931)
    ]
    return {
        "sample_size": 1931,
        "source_commit": REGISTRATION_COMMIT,
        "input_sha256": manifest,
        "raw_counts": {
            "total_mutants": 1931,
            "composite_survived": 646,
            "equivalent_mutants": 60,
            "true_defects_survived": 586,
        },
        "mutants": mutants,
        "weakest_guards": [{"id": index} for index in range(1345, 1931)],
    }


def test_exp56_rejects_the_committed_aggregate_only_corpus():
    exp47 = json.loads(
        (ROOT / "docs/10-research/experiments/exp47/results-exp47.json").read_text(
            encoding="utf-8"
        )
    )
    result = audit_inputs(exp47, "fixture", MODEL_LISTING)

    assert result["status"] == "stopped_before_scored_calls"
    assert result["scored_calls"] == 0
    assert result["corpus_audit"]["prompt_inputs_present_rows"] == 0


def test_count_correct_rows_still_need_verified_item_provenance():
    complete = complete_exp47()
    result = audit_inputs(complete, "fixture", MODEL_LISTING)

    assert result["status"] == "stopped_before_scored_calls"
    assert result["corpus_audit"]["shape_ready"] is True
    assert result["corpus_audit"]["item_provenance_verified"] is False
    assert result["corpus_audit"]["missing"] == [
        "item provenance from the pinned snapshot"
    ]

    mystery = complete_exp47()
    mystery["mutants"][-586:] = [
        {**row, "outcome": "mystery", "classification": "mystery"}
        for row in mystery["mutants"][-586:]
    ]
    empty = complete_exp47()
    empty["mutants"] = []
    invented_snapshot = complete_exp47()
    invented_snapshot["source_commit"] = "0" * 40
    wrong_blob_hash = complete_exp47()
    wrong_blob_hash["input_sha256"]["src/consilient/beta.py"] = "0" * 64

    for invalid in (mystery, empty, invented_snapshot, wrong_blob_hash):
        result = audit_inputs(invalid, "fixture", MODEL_LISTING)
        assert result["status"] == "stopped_before_scored_calls"


def test_item_identity_and_prompt_inputs_are_enforced():
    duplicate = complete_exp47()
    duplicate["mutants"] = [{**row, "id": 1} for row in duplicate["mutants"]]
    no_prompt_inputs = complete_exp47()
    no_prompt_inputs["mutants"] = [
        {
            key: value
            for key, value in row.items()
            if key not in {"source_region", "covering_tests"}
        }
        for row in no_prompt_inputs["mutants"]
    ]

    for invalid in (duplicate, no_prompt_inputs):
        result = audit_inputs(invalid, "fixture", MODEL_LISTING)
        assert result["status"] == "stopped_before_scored_calls"


def test_unreported_served_identity_is_counted_for_every_model_call():
    call = {
        "purpose": "identity_probe",
        "scored": False,
        "served_model": "unknown:not-reported-by-runtime",
        "served_identity_reported": False,
    }

    for record in (call, {}):
        result = audit_inputs({}, "fixture", MODEL_LISTING, [record])

        assert result["model_calls"] == 1
        assert result["scored_calls"] == 0
        assert result["unidentified_served_model_calls"] == 1
        assert result["call_records"] == [record]

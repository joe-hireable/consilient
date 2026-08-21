"""Invariant checks for the EXP-96 mutation-proxy instrument."""

import importlib.util
import os
from pathlib import Path
import sys
import time


RUNNER = Path("docs/10-research/experiments/exp96/run_exp96.py")
SPEC = importlib.util.spec_from_file_location("run_exp96", RUNNER)
assert SPEC and SPEC.loader
exp96 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exp96)


def mutant(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "file": "src/example.py",
        "docstring_only": False,
        "original_node": "if value == 1:",
        "mutated_node": "if value != 1:",
        "original_line": "if value == 1:",
        "mutated_line": "if value != 1:",
        "original_node_type": "ComparisonTarget",
        "mutated_node_type": "ComparisonTarget",
    }
    record.update(overrides)
    return record


def test_equivalence_classes_are_frozen_and_unknown_strings_remain_unclassifiable() -> (
    None
):
    assert exp96.FROZEN_EQUIVALENT_CLASSES == {
        "docstring_mutation",
        "sql_case_insensitive_mutation",
        "cli_help_metadata_string",
        "dataclass_default_caveat_string",
    }
    assert exp96.classify_mutant(mutant(docstring_only=True)) == (
        "equivalent",
        "docstring_mutation",
    )
    assert exp96.classify_mutant(
        mutant(
            file="src/consilient/cli.py",
            original_node='"JSON output"',
            mutated_node='"XXJSON outputXX"',
            original_line='parser.add_argument("--json", help="JSON output")',
            mutated_line='parser.add_argument("--json", help="XXJSON outputXX")',
            original_node_type="SimpleString",
            mutated_node_type="SimpleString",
        )
    ) == ("equivalent", "cli_help_metadata_string")
    assert exp96.classify_mutant(
        mutant(
            file="src/consilient/cli.py",
            original_node='"--event"',
            mutated_node='"XX--eventXX"',
            original_line='record.add_argument("--event", required=True, help="event")',
            mutated_line='record.add_argument("XX--eventXX", required=True, help="event")',
            original_node_type="SimpleString",
            mutated_node_type="SimpleString",
        )
    ) == (
        "unclassifiable",
        "presentation_or_metadata_without_contract_oracle",
    )
    assert exp96.classify_mutant(
        mutant(
            file="src/consilient/cli.py",
            original_line='record.add_argument("--event", required=True, help="event")',
            mutated_line='record.add_argument("--event", required=False, help="event")',
        )
    ) == ("true_defect", "seeded_non_presentation_operator")
    assert exp96.classify_mutant(
        mutant(original_node='"SELECT"', mutated_node='"select"')
    ) == ("equivalent", "sql_case_insensitive_mutation")
    assert exp96.classify_mutant(
        mutant(
            file="src/consilient/beta.py",
            original_node='"beta is conditional"',
            mutated_node='"BETA IS CONDITIONAL"',
            original_line='caveat: str = field(default="beta is conditional")',
            mutated_line='caveat: str = field(default="BETA IS CONDITIONAL")',
            original_node_type="SimpleString",
            mutated_node_type="SimpleString",
        )
    ) == ("equivalent", "dataclass_default_caveat_string")
    assert exp96.classify_mutant(
        mutant(
            original_node='"status"',
            mutated_node='"STATUS"',
            original_node_type="SimpleString",
            mutated_node_type="SimpleString",
        )
    ) == (
        "unclassifiable",
        "presentation_or_metadata_without_contract_oracle",
    )
    assert exp96.classify_mutant(mutant()) == (
        "true_defect",
        "seeded_non_presentation_operator",
    )


def test_summary_keeps_unclassifiable_out_of_the_point_estimate() -> None:
    rows = [
        *(
            {
                "composite_outcome": "rejected",
                "semantic_class": "true_defect",
                "checks": {},
            }
            for _ in range(60)
        ),
        *(
            {
                "composite_outcome": "accepted",
                "semantic_class": "true_defect",
                "checks": {},
            }
            for _ in range(30)
        ),
        *(
            {
                "composite_outcome": "accepted",
                "semantic_class": "equivalent",
                "checks": {},
            }
            for _ in range(3)
        ),
        *(
            {
                "composite_outcome": "rejected",
                "semantic_class": "equivalent",
                "checks": {},
            }
            for _ in range(2)
        ),
        *(
            {
                "composite_outcome": "accepted",
                "semantic_class": "unclassifiable",
                "checks": {},
            }
            for _ in range(4)
        ),
        {
            "composite_outcome": "rejected",
            "semantic_class": "unclassifiable",
            "checks": {},
        },
    ]
    summary = exp96.summarise_corpus(rows, 100, True, True)
    assert summary["census_identity_holds"] is True
    assert summary["classifiable_mutation_beta"] == 30 / 90
    assert summary["classifiable_n"] == 90
    assert summary["partial_identification"] == [30 / 91, 34 / 94]
    assert summary["contamination"]["known_equivalent_E_over_N"] == 0.05
    assert summary["contamination"]["unresolved_U_over_N"] == 0.05


def test_execution_error_makes_the_measurement_insufficient() -> None:
    rows = [
        {
            "composite_outcome": "rejected",
            "semantic_class": "true_defect",
            "checks": {},
        }
        for _ in range(50)
    ] + [
        {
            "composite_outcome": "execution_error",
            "semantic_class": "true_defect",
            "checks": {},
        }
    ]
    summary = exp96.summarise_corpus(rows, 51, True, True)
    assert summary["row_accounting_holds"] is True
    assert summary["census_identity_holds"] is False
    assert summary["measurement_complete"] is False
    assert summary["verdict"] == "insufficient_evidence"


def test_stopping_and_contamination_thresholds_are_strict() -> None:
    sufficient = [
        {
            "composite_outcome": "accepted" if index < 190 else "rejected",
            "semantic_class": "true_defect",
            "checks": {},
        }
        for index in range(381)
    ]
    summary = exp96.summarise_corpus(sufficient, 381, True, True)
    assert summary["measurement_complete"] is True
    assert summary["wilson_half_width"] <= 0.05

    boundary = [
        {
            "composite_outcome": "rejected",
            "semantic_class": "true_defect",
            "checks": {},
        }
        for _ in range(90)
    ] + [
        {
            "composite_outcome": "accepted",
            "semantic_class": "unclassifiable",
            "checks": {},
        }
        for _ in range(10)
    ]
    assert (
        exp96.summarise_corpus(boundary, 100, True, True)["contamination_reasons"] == []
    )
    over = [*boundary[1:], boundary[-1]]
    assert exp96.summarise_corpus(over, 100, True, True)["contamination_reasons"] == [
        "unclassifiable_rate_above_0.10",
        "identification_width_above_0.10",
    ]


def test_output_lock_refuses_a_concurrent_writer(tmp_path: Path) -> None:
    output = tmp_path / "results.json"
    lock, token = exp96.acquire_output_lock(output)
    try:
        try:
            exp96.acquire_output_lock(output)
        except RuntimeError:
            pass
        else:
            raise AssertionError("a second writer acquired the EXP-96 output lock")
    finally:
        exp96.release_output_lock(lock, token)
    assert not lock.exists()


def test_result_schema_cannot_pool_unlike_verifier_pairs() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert '"pooled":' not in source
    assert "pooled_rows" not in source


def test_windows_check_descendants_die_when_the_direct_process_exits(
    tmp_path: Path,
) -> None:
    if os.name != "nt":
        return
    marker = tmp_path / "escaped.txt"
    child = (
        "import pathlib,time;time.sleep(1);"
        f"pathlib.Path({str(marker)!r}).write_text('escaped')"
    )
    parent = (
        "import subprocess,sys,time;time.sleep(0.5);"
        f"subprocess.Popen([sys.executable,'-c',{child!r}])"
    )
    result = exp96.run_command(
        [sys.executable, "-c", parent],
        tmp_path,
        exp96.scrubbed_environment(),
        10,
        tmp_path / "receipt",
    )
    assert result["outcome"] == "accepted"
    time.sleep(1.5)
    assert not marker.exists()

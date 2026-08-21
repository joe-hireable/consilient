"""Unit tests for EXP-47 mutation testing analysis harness."""

import importlib.util
import math
from pathlib import Path

exp47_path = Path("docs/10-research/experiments/exp47/run_exp47.py")
spec = importlib.util.spec_from_file_location("run_exp47", exp47_path)
assert spec and spec.loader
run_exp47 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_exp47)

wilson_interval = run_exp47.wilson_interval
classify_equivalent_mutant = run_exp47.classify_equivalent_mutant
compute_statistics = run_exp47.compute_statistics
extract_mutant_diff_info = run_exp47.extract_mutant_diff_info


def test_wilson_interval_boundaries():
    # 0 successes
    low, high = wilson_interval(0, 100)
    assert 0.0 <= low <= high <= 1.0
    assert low == 0.0
    assert high > 0.0

    # All successes
    low, high = wilson_interval(100, 100)
    assert 0.0 <= low <= high <= 1.0
    assert low < 1.0
    assert math.isclose(high, 1.0, rel_tol=1e-7)

    # Known standard case
    low, high = wilson_interval(50, 100)
    assert 0.39 < low < 0.41
    assert 0.59 < high < 0.61


def test_extract_mutant_diff_info():
    orig = "def add(a, b):\n    return a + b\n"
    mut = "def add(a, b):\n    return a - b\n"
    info = extract_mutant_diff_info(orig, mut)
    assert info["line"] == 2
    assert "return a + b" in info["orig_snippet"]
    assert "return a - b" in info["mut_snippet"]
    assert info["operator_category"] == "arithmetic_binary_op"


def test_classify_equivalent_mutant():
    m_doc = {
        "file": "src/consilient/events.py",
        "line": 5,
        "orig_snippet": '"""Authoritative trajectory events."""',
        "mut_snippet": '"""XXAuthoritative trajectory events.XX"""',
    }
    is_eq, reason = classify_equivalent_mutant(m_doc)
    assert is_eq
    assert reason == "docstring_mutation"

    m_code = {
        "file": "src/consilient/events.py",
        "line": 100,
        "orig_snippet": "if event['v'] != SCHEMA_VERSION:",
        "mut_snippet": "if event['v'] == SCHEMA_VERSION:",
    }
    is_eq, reason = classify_equivalent_mutant(m_code)
    assert not is_eq
    assert "schema_version" in reason or "behavioural" in reason


def test_compute_statistics_synthetic():
    results = [
        {
            "id": 0,
            "file": "src/consilient/beta.py",
            "line": 10,
            "operator": "arithmetic_binary_op",
            "orig_snippet": "x + 1",
            "mut_snippet": "x - 1",
            "pytest_pass": False,
            "mypy_pass": False,
            "ruff_pass": True,
            "composite_pass": False,
            "elapsed": 0.1,
        },
        {
            "id": 1,
            "file": "src/consilient/beta.py",
            "line": 20,
            "operator": "constant_literal_mutation",
            "orig_snippet": "MIN_REJECTIONS = 30",
            "mut_snippet": "MIN_REJECTIONS = 31",
            "pytest_pass": True,
            "mypy_pass": True,
            "ruff_pass": True,
            "composite_pass": True,
            "elapsed": 0.1,
        },
        {
            "id": 2,
            "file": "src/consilient/cli.py",
            "line": 5,
            "operator": "constant_literal_mutation",
            "orig_snippet": '"""Module docstring"""',
            "mut_snippet": '"""Mutated docstring"""',
            "pytest_pass": True,
            "mypy_pass": True,
            "ruff_pass": True,
            "composite_pass": True,
            "elapsed": 0.1,
        },
    ]

    stats = compute_statistics(results, total_wall_clock=1.0)
    assert stats["sample_size"] == 3
    assert stats["raw_counts"]["composite_survived"] == 2
    assert stats["raw_counts"]["equivalent_mutants"] == 1
    assert stats["raw_counts"]["true_defects_survived"] == 1
    assert stats["beta_estimates"]["composite_corrected"]["survivors"] == 1
    assert stats["beta_estimates"]["composite_corrected"]["total"] == 2

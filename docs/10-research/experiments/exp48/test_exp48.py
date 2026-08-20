"""Unit tests for EXP-48 cross-reference analysis."""

from __future__ import annotations

import importlib.util
from pathlib import Path

exp48_path = Path(__file__).resolve().parent / "run_exp48.py"
spec = importlib.util.spec_from_file_location("run_exp48", exp48_path)
assert spec and spec.loader
run_exp48 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_exp48)

cluster_mutants = run_exp48.cluster_mutants
match_guard_to_mutants = run_exp48.match_guard_to_mutants
P2_CATALOGUE = run_exp48.P2_CATALOGUE


def test_cluster_mutants_synthetic():
    mutants = [
        {"file": "src/a.py", "line": 10, "operator": "op1"},
        {"file": "src/a.py", "line": 12, "operator": "op2"},
        {"file": "src/a.py", "line": 30, "operator": "op3"},
        {"file": "src/b.py", "line": 5, "operator": "op4"},
    ]
    clusters = cluster_mutants(mutants, max_gap=5)
    assert len(clusters) == 3
    
    # Cluster 1: a.py lines 10-12 (2 mutants)
    c1 = next(c for c in clusters if c["file"] == "src/a.py" and c["start_line"] == 10)
    assert c1["count"] == 2
    assert c1["end_line"] == 12
    assert set(c1["operators"]) == {"op1", "op2"}

    # Cluster 2: a.py line 30 (1 mutant)
    c2 = next(c for c in clusters if c["file"] == "src/a.py" and c["start_line"] == 30)
    assert c2["count"] == 1

    # Cluster 3: b.py line 5 (1 mutant)
    c3 = next(c for c in clusters if c["file"] == "src/b.py")
    assert c3["count"] == 1


def test_match_guard_to_mutants():
    guard = {
        "id": "A3",
        "layer": "code",
        "file": "src/consilient/events.py",
        "lines": (220, 275),
    }
    mutants = [
        {"file": "src/consilient/events.py", "line": 230, "operator": "op1"},
        {"file": "src/consilient/events.py", "line": 280, "operator": "op2"},
        {"file": "src/consilient/cli.py", "line": 230, "operator": "op3"},
    ]
    res = match_guard_to_mutants(guard, mutants)
    assert res["in_scope"] is True
    assert res["matched_mutants_count"] == 1
    assert res["matched_mutants"][0]["line"] == 230


def test_p2_catalogue_structure():
    assert len(P2_CATALOGUE) == 26  # 25 defects + 1 control
    code_resident = [g for g in P2_CATALOGUE if g["layer"] == "code"]
    assert len(code_resident) == 8
    non_code = [g for g in P2_CATALOGUE if g["layer"] != "code" and g["id"] != "C1"]
    assert len(non_code) == 17

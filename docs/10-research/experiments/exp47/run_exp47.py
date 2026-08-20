"""EXP-47: Direct Measurement of Verifier Beta via Mutation Testing.

Evaluates pytest, mypy, and ruff separately and in composite across all
syntactically valid first-order mutants generated on src/consilient/.
"""

from __future__ import annotations

import difflib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

try:
    import mutmut.mutation.file_mutation as fm
except ImportError:
    fm = None  # type: ignore[assignment]

WORKER_DIR: Path | None = None


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """Compute Wilson score interval."""
    if trials == 0:
        return 0.0, 0.0
    p = successes / trials
    denom = 1.0 + z * z / trials
    centre = (p + z * z / (2.0 * trials)) / denom
    spread = z * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)) / denom
    return max(0.0, centre - spread), min(1.0, centre + spread)


def init_worker(worker_id: int) -> None:
    """Initialise isolated scratch tree for worker process."""
    global WORKER_DIR
    tmp = tempfile.mkdtemp(prefix=f"exp47_worker_{os.getpid()}_{worker_id}_")
    WORKER_DIR = Path(tmp)
    shutil.copytree("src", WORKER_DIR / "src")
    shutil.copytree("tests", WORKER_DIR / "tests")
    shutil.copytree("docs", WORKER_DIR / "docs")
    if Path(".github").exists():
        shutil.copytree(".github", WORKER_DIR / ".github")
    shutil.copy("mypy.ini", WORKER_DIR / "mypy.ini")
    shutil.copy("pytest.ini", WORKER_DIR / "pytest.ini")


def cleanup_worker() -> None:
    """Clean up worker scratch tree."""
    global WORKER_DIR
    if WORKER_DIR and WORKER_DIR.exists():
        try:
            shutil.rmtree(WORKER_DIR, ignore_errors=True)
        except OSError:
            pass


def extract_mutant_diff_info(orig_code: str, mut_code: str) -> dict[str, Any]:
    """Extract line number, original snippet, and mutated snippet from unified diff."""
    diff = list(
        difflib.unified_diff(
            orig_code.splitlines(),
            mut_code.splitlines(),
            lineterm="",
        )
    )
    line_no = None
    cur_line = None
    orig_snippet = []
    mut_snippet = []
    hunk_re = re.compile(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    for line in diff:
        m = hunk_re.match(line)
        if m:
            cur_line = int(m.group(1))
        elif cur_line is not None:
            if line.startswith(" "):
                cur_line += 1
            elif line.startswith("-") and not line.startswith("---"):
                if line_no is None:
                    line_no = cur_line
                orig_snippet.append(line[1:])
                cur_line += 1
            elif line.startswith("+") and not line.startswith("+++"):
                mut_snippet.append(line[1:])

    orig_str = "\n".join(orig_snippet).strip()
    mut_str = "\n".join(mut_snippet).strip()

    # Operator category classification
    op_cat = "other"
    if any(op in mut_str or op in orig_str for op in ("==", "!=", "<=", ">=", "<", ">", " is ", " is not ", " in ", " not in ")):
        op_cat = "comparison_swap"
    elif any(kw in mut_str or kw in orig_str for kw in ("True", "False", " and ", " or ")):
        op_cat = "boolean_logical_swap"
    elif any(op in mut_str or op in orig_str for op in (" + ", " - ", " * ", " / ", " // ", " % ", " ** ", " & ", " | ", " ^ ")):
        op_cat = "arithmetic_binary_op"
    elif any(mut_str.startswith(u) or orig_str.startswith(u) for u in ("not ", "-", "~")):
        op_cat = "unary_inversion"
    elif "None" in mut_str or re.search(r"\b\d+\b", orig_str):
        op_cat = "constant_literal_mutation"
    elif "def " in orig_str or "class " in orig_str or "import " in orig_str:
        op_cat = "definition_or_import"
    elif "raise " in orig_str or "return " in orig_str or "break" in orig_str or "continue" in orig_str:
        op_cat = "control_flow_mutation"
    else:
        op_cat = "expression_mutation"

    return {
        "line": line_no or 1,
        "orig_snippet": orig_str[:120],
        "mut_snippet": mut_str[:120],
        "operator_category": op_cat,
    }


def run_single_mutant(task: tuple[int, str, str, dict[str, Any]]) -> dict[str, Any]:
    """Execute all three verifier checks against a single mutant in isolation."""
    global WORKER_DIR
    assert WORKER_DIR is not None

    mutant_id, file_rel, mutated_code, metadata = task
    target_path = WORKER_DIR / file_rel
    orig_code = Path(file_rel).read_text(encoding="utf-8")

    # Apply mutant
    target_path.write_text(mutated_code, encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(WORKER_DIR / "src")

    t0 = time.perf_counter()

    # 1. Pytest
    try:
        p_res = subprocess.run(
            ["python", "-m", "pytest", "tests", "-q"],
            cwd=WORKER_DIR,
            capture_output=True,
            text=True,
            env=env,
            timeout=20,
        )
        pytest_pass = (p_res.returncode == 0)
    except subprocess.TimeoutExpired:
        pytest_pass = False

    # 2. Mypy
    try:
        m_res = subprocess.run(
            ["python", "-m", "mypy", "src/consilient"],
            cwd=WORKER_DIR,
            capture_output=True,
            text=True,
            env=env,
            timeout=20,
        )
        mypy_pass = (m_res.returncode == 0)
    except subprocess.TimeoutExpired:
        mypy_pass = False

    # 3. Ruff
    try:
        r_res = subprocess.run(
            ["python", "-m", "ruff", "check", "src/", "tests/"],
            cwd=WORKER_DIR,
            capture_output=True,
            text=True,
            env=env,
            timeout=20,
        )
        ruff_pass = (r_res.returncode == 0)
    except subprocess.TimeoutExpired:
        ruff_pass = False

    elapsed = time.perf_counter() - t0

    # Restore unmutated file
    target_path.write_text(orig_code, encoding="utf-8")

    # Composite pass = all checks pass (mutant survived verifier)
    composite_pass = pytest_pass and mypy_pass and ruff_pass

    return {
        "id": mutant_id,
        "file": file_rel,
        "line": metadata["line"],
        "operator": metadata["operator_category"],
        "orig_snippet": metadata["orig_snippet"],
        "mut_snippet": metadata["mut_snippet"],
        "pytest_pass": pytest_pass,
        "mypy_pass": mypy_pass,
        "ruff_pass": ruff_pass,
        "composite_pass": composite_pass,
        "elapsed": elapsed,
    }


def is_sql_case_equivalent(orig: str, mut: str) -> bool:
    """Check if change is purely case/whitespace in SQL statement."""
    # Remove quotes and compare case-insensitively
    s_orig = orig.strip('\'"').casefold()
    s_mut = mut.strip('\'"').casefold()
    if s_orig == s_mut:
        sql_keywords = ("select", "insert", "update", "delete", "create", "table", "values", "from", "where", "count", "primary key", "unique")
        if any(kw in s_orig for kw in sql_keywords):
            return True
    return False


def classify_equivalent_mutant(mutant: dict[str, Any]) -> tuple[bool, str]:
    """Determine if a surviving mutant is equivalent (no-op / unobservable semantic change)."""
    orig = mutant["orig_snippet"]
    mut = mutant["mut_snippet"]
    file = mutant["file"]
    line = mutant["line"]

    # Docstring mutations
    if '"""' in orig or "'''" in orig:
        return True, "docstring_mutation"

    # SQL case changes (SQLite query syntax is case-insensitive)
    if is_sql_case_equivalent(orig, mut):
        return True, "sql_case_insensitive_mutation"

    # CLI argument help / epilog / description text
    if file == "src/consilient/cli.py":
        if "help=" in orig or "description=" in orig or "epilog=" in orig or "metavar=" in orig:
            return True, "cli_help_metadata_string"

    # Dataclass caveat default string
    if file == "src/consilient/beta.py":
        if "caveat: str = field" in orig or "default=\"beta is conditional" in orig:
            return True, "dataclass_default_caveat_string"

    # Default: behavioural / testable defect
    return False, "behavioural_or_uncovered"


def compute_statistics(results: list[dict[str, Any]], total_wall_clock: float) -> dict[str, Any]:
    """Compute comprehensive statistical metrics, intervals, independence tests, and rankings."""
    n_total = len(results)
    
    # Check counts
    pytest_survived = sum(1 for r in results if r["pytest_pass"])
    mypy_survived = sum(1 for r in results if r["mypy_pass"])
    ruff_survived = sum(1 for r in results if r["ruff_pass"])
    comp_survived = sum(1 for r in results if r["composite_pass"])

    # Wilson intervals for raw beta
    beta_pytest_raw = pytest_survived / n_total if n_total > 0 else 0.0
    beta_mypy_raw = mypy_survived / n_total if n_total > 0 else 0.0
    beta_ruff_raw = ruff_survived / n_total if n_total > 0 else 0.0
    beta_comp_raw = comp_survived / n_total if n_total > 0 else 0.0

    ci_pytest_raw = wilson_interval(pytest_survived, n_total)
    ci_mypy_raw = wilson_interval(mypy_survived, n_total)
    ci_ruff_raw = wilson_interval(ruff_survived, n_total)
    ci_comp_raw = wilson_interval(comp_survived, n_total)

    # Equivalent mutant analysis on composite survivors
    survivors = [r for r in results if r["composite_pass"]]
    classified_equiv = []
    true_defects = []

    for s in survivors:
        is_eq, reason = classify_equivalent_mutant(s)
        s["is_equivalent"] = is_eq
        s["equivalent_reason"] = reason
        if is_eq:
            classified_equiv.append(s)
        else:
            true_defects.append(s)

    n_equiv = len(classified_equiv)
    n_true_denom = n_total - n_equiv
    n_true_surv = len(true_defects)

    beta_comp_corrected = n_true_surv / n_true_denom if n_true_denom > 0 else 0.0
    ci_comp_corrected = wilson_interval(n_true_surv, n_true_denom)

    # Per-operator breakdown
    by_operator: dict[str, dict[str, Any]] = {}
    for r in results:
        op = r["operator"]
        if op not in by_operator:
            by_operator[op] = {"total": 0, "pytest_surv": 0, "mypy_surv": 0, "ruff_surv": 0, "comp_surv": 0}
        by_operator[op]["total"] += 1
        if r["pytest_pass"]:
            by_operator[op]["pytest_surv"] += 1
        if r["mypy_pass"]:
            by_operator[op]["mypy_surv"] += 1
        if r["ruff_pass"]:
            by_operator[op]["ruff_surv"] += 1
        if r["composite_pass"]:
            by_operator[op]["comp_surv"] += 1

    # Per-file breakdown
    by_file: dict[str, dict[str, Any]] = {}
    for r in results:
        f = r["file"]
        if f not in by_file:
            by_file[f] = {"total": 0, "pytest_surv": 0, "mypy_surv": 0, "ruff_surv": 0, "comp_surv": 0}
        by_file[f]["total"] += 1
        if r["pytest_pass"]:
            by_file[f]["pytest_surv"] += 1
        if r["mypy_pass"]:
            by_file[f]["mypy_surv"] += 1
        if r["ruff_pass"]:
            by_file[f]["ruff_surv"] += 1
        if r["composite_pass"]:
            by_file[f]["comp_surv"] += 1

    # Independence test: pytest vs mypy
    # 2x2 contingency table:
    #                 mypy_survived  mypy_killed
    # pytest_survived       n11          n10
    # pytest_killed         n01          n00
    n11 = sum(1 for r in results if r["pytest_pass"] and r["mypy_pass"])
    n10 = sum(1 for r in results if r["pytest_pass"] and not r["mypy_pass"])
    n01 = sum(1 for r in results if not r["pytest_pass"] and r["mypy_pass"])
    n00 = sum(1 for r in results if not r["pytest_pass"] and not r["mypy_pass"])

    # Expected under independence:
    e11 = (pytest_survived * mypy_survived) / n_total if n_total > 0 else 0
    e10 = (pytest_survived * (n_total - mypy_survived)) / n_total if n_total > 0 else 0
    e01 = ((n_total - pytest_survived) * mypy_survived) / n_total if n_total > 0 else 0
    e00 = ((n_total - pytest_survived) * (n_total - mypy_survived)) / n_total if n_total > 0 else 0

    chi2 = 0.0
    for obs, exp in [(n11, e11), (n10, e10), (n01, e01), (n00, e00)]:
        if exp > 0:
            chi2 += (obs - exp) ** 2 / exp

    independent_pytest_mypy = (chi2 <= 3.841)
    p_observed_joint = n11 / n_total if n_total > 0 else 0.0
    p_expected_joint = (pytest_survived / n_total) * (mypy_survived / n_total) if n_total > 0 else 0.0

    # Weakest guards ranking (all true surviving mutants)
    weak_guards = []
    for td in true_defects:
        weak_guards.append({
            "id": td["id"],
            "file": td["file"],
            "line": td["line"],
            "operator": td["operator"],
            "orig_snippet": td["orig_snippet"],
            "mut_snippet": td["mut_snippet"],
            "reason": td.get("equivalent_reason", "uncovered_logic"),
        })

    weak_guards.sort(key=lambda x: (x["file"], x["line"]))

    return {
        "experiment_id": "EXP-47",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine": "mutmut 3.7.0 (BSD-3-Clause) + libcst",
        "sample_size": n_total,
        "total_wall_clock_seconds": total_wall_clock,
        "seconds_per_mutant": total_wall_clock / n_total if n_total > 0 else 0.0,
        "raw_counts": {
            "total_mutants": n_total,
            "pytest_survived": pytest_survived,
            "mypy_survived": mypy_survived,
            "ruff_survived": ruff_survived,
            "composite_survived": comp_survived,
            "equivalent_mutants": n_equiv,
            "true_defects_survived": n_true_surv,
        },
        "beta_estimates": {
            "pytest": {
                "point": beta_pytest_raw,
                "interval_95": list(ci_pytest_raw),
                "survivors": pytest_survived,
                "total": n_total,
            },
            "mypy": {
                "point": beta_mypy_raw,
                "interval_95": list(ci_mypy_raw),
                "survivors": mypy_survived,
                "total": n_total,
            },
            "ruff": {
                "point": beta_ruff_raw,
                "interval_95": list(ci_ruff_raw),
                "survivors": ruff_survived,
                "total": n_total,
            },
            "composite_raw": {
                "point": beta_comp_raw,
                "interval_95": list(ci_comp_raw),
                "survivors": comp_survived,
                "total": n_total,
            },
            "composite_corrected": {
                "point": beta_comp_corrected,
                "interval_95": list(ci_comp_corrected),
                "survivors": n_true_surv,
                "total": n_true_denom,
                "equivalent_removed": n_equiv,
            },
        },
        "independence_analysis": {
            "contingency_table_pytest_mypy": {
                "pytest_surv_mypy_surv": n11,
                "pytest_surv_mypy_kill": n10,
                "pytest_kill_mypy_surv": n01,
                "pytest_kill_mypy_kill": n00,
            },
            "chi2_statistic": chi2,
            "df": 1,
            "p_value_less_than_0_05": not independent_pytest_mypy,
            "p_observed_joint": p_observed_joint,
            "p_expected_joint": p_expected_joint,
            "verdict": "dependent" if not independent_pytest_mypy else "independent",
        },
        "by_file": by_file,
        "by_operator": by_operator,
        "weakest_guards": weak_guards,
    }


def main() -> None:
    if fm is None:
        raise RuntimeError("EXP-47 requires mutmut: run with `uv run --with mutmut ...`")
    print("=== EXP-47: Mutation Testing for Direct Beta Measurement ===")
    src_dir = Path("src/consilient")
    src_files = sorted(src_dir.glob("*.py"))
    
    print(f"Scanning source files in {src_dir}...")
    tasks: list[tuple[int, str, str, dict[str, Any]]] = []
    mutant_id = 0

    for file_path in src_files:
        rel_path = str(file_path.as_posix())
        source = file_path.read_text(encoding="utf-8")
        module, mutations, _, _ = fm.create_mutations(rel_path, source)
        print(f"  {file_path.name}: {len(mutations)} mutants")
        
        for m in mutations:
            mut_tree = fm.deep_replace(module, m.original_node, m.mutated_node)
            mut_code = mut_tree.code
            diff_info = extract_mutant_diff_info(source, mut_code)
            tasks.append((mutant_id, rel_path, mut_code, diff_info))
            mutant_id += 1

    total_mutants = len(tasks)
    print(f"\nTotal mutant census across src/consilient/: {total_mutants}")
    print("Starting isolated multiprocessing worker pool (24 workers)...")

    t_start = time.perf_counter()
    results: list[dict[str, Any]] = []

    with ProcessPoolExecutor(max_workers=24, initializer=init_worker, initargs=(os.getpid(),)) as executor:
        futures = {executor.submit(run_single_mutant, task): task[0] for task in tasks}
        completed = 0
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 100 == 0 or completed == total_mutants:
                elapsed = time.perf_counter() - t_start
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"  Progress: {completed}/{total_mutants} ({completed/total_mutants*100:.1f}%) in {elapsed:.1f}s ({rate:.1f} mutants/s)")

    total_wall_clock = time.perf_counter() - t_start
    results.sort(key=lambda x: x["id"])

    print(f"\nExecution finished in {total_wall_clock:.2f}s (avg {total_wall_clock/total_mutants:.3f}s per mutant)")
    print("Computing statistical metrics and intervals...")

    stats = compute_statistics(results, total_wall_clock)

    out_json = Path("docs/10-research/experiments/exp47/results-exp47.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"Saved complete results JSON to {out_json}")

    print("\n=== HEADLINE METRICS ===")
    print(f"Census Total: {stats['sample_size']}")
    print(f"Pytest Beta: {stats['beta_estimates']['pytest']['point']:.4f} "
          f"[{stats['beta_estimates']['pytest']['interval_95'][0]:.4f}, {stats['beta_estimates']['pytest']['interval_95'][1]:.4f}] "
          f"({stats['raw_counts']['pytest_survived']}/{stats['sample_size']})")
    print(f"Mypy Beta: {stats['beta_estimates']['mypy']['point']:.4f} "
          f"[{stats['beta_estimates']['mypy']['interval_95'][0]:.4f}, {stats['beta_estimates']['mypy']['interval_95'][1]:.4f}] "
          f"({stats['raw_counts']['mypy_survived']}/{stats['sample_size']})")
    print(f"Ruff Beta: {stats['beta_estimates']['ruff']['point']:.4f} "
          f"[{stats['beta_estimates']['ruff']['interval_95'][0]:.4f}, {stats['beta_estimates']['ruff']['interval_95'][1]:.4f}] "
          f"({stats['raw_counts']['ruff_survived']}/{stats['sample_size']})")
    print(f"Composite Raw Beta: {stats['beta_estimates']['composite_raw']['point']:.4f} "
          f"[{stats['beta_estimates']['composite_raw']['interval_95'][0]:.4f}, {stats['beta_estimates']['composite_raw']['interval_95'][1]:.4f}] "
          f"({stats['raw_counts']['composite_survived']}/{stats['sample_size']})")
    print(f"Composite Corrected Beta: {stats['beta_estimates']['composite_corrected']['point']:.4f} "
          f"[{stats['beta_estimates']['composite_corrected']['interval_95'][0]:.4f}, {stats['beta_estimates']['composite_corrected']['interval_95'][1]:.4f}] "
          f"({stats['raw_counts']['true_defects_survived']}/{stats['raw_counts']['total_mutants'] - stats['raw_counts']['equivalent_mutants']})")
    print(f"Check Independence Chi2: {stats['independence_analysis']['chi2_statistic']:.2f} (p < 0.05: {stats['independence_analysis']['p_value_less_than_0_05']}) -> {stats['independence_analysis']['verdict']}")
    print(f"Weakest Guards Identified: {len(stats['weakest_guards'])} mutants")


if __name__ == "__main__":
    main()

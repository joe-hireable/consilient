"""EXP-43: Retro-verification of historical commits via forward test replay.

Evaluates whether running later test suites against historical commits (with
parent-commit control) provides an automated, human-free ground truth for
beta = P(verifier accepts | artefact is bad), or fails due to interface evolution
drift and survivorship bias.

Protocol pre-registered in docs/10-research/experiment-register.md § EXP-43.
Modelled on docs/10-research/experiments/exp31/run_exp31.py.
"""

from __future__ import annotations

import json
import math
import os
import signal
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results-exp43.json"
LOCK = HERE / "run.lock"

CORPUS_REPO = Path("/mnt/c/Users/jpbpr/Repositories/jobboard-v2")
SCRATCH_DIR = Path("/tmp/jobboard-scratch")

DEFAULT_TIMEOUT_S = 60
MAX_WALL_CLOCK_S = 3600
PILOT_SAMPLE_SIZE = 15

LIMITATIONS = [
    "The oracle is structurally blind to greenfield/additive defects where the interface did not exist at the parent commit (censored by parent-commit control).",
    "Survivorship bias: future test suites only contain regression tests for defects that were discovered and tested; latent unfound bugs remain unmeasured.",
    "Dependency and schema drift over long time horizons can induce false parent/child failures.",
    "Results apply to evaluated repository commits and unit test suites only.",
]


def kill_tree(pid: int) -> None:
    """Kill a process and every descendant to prevent hung pipe write-ends."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(pid)],
            capture_output=True,
            timeout=30,
        )
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def acquire_lock(run_id: str, cap_s: int) -> bool:
    """Refuse to start alongside a live run; atomically claim run.lock."""
    if LOCK.exists():
        try:
            held = json.loads(LOCK.read_text(encoding="utf-8"))
            age = time.time() - float(held.get("started_epoch", 0))
        except (ValueError, OSError):
            held, age = {}, cap_s + 1
        if age < cap_s:
            print(
                f"REFUSING TO START: {LOCK} is held by pid {held.get('pid')} "
                f"(run {held.get('run_id')}), started {age / 60:.1f} min ago. "
                "Wait, or delete the lock if that process is dead.",
                file=sys.stderr,
            )
            return False
        print(f"Stale lock ({age / 60:.1f} min old) — taking over", file=sys.stderr)
        LOCK.unlink(missing_ok=True)

    payload = json.dumps(
        {"pid": os.getpid(), "run_id": run_id, "started_epoch": time.time()}, indent=1
    )
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print(
            f"REFUSING TO START: {LOCK} was created concurrently by another runner.",
            file=sys.stderr,
        )
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(payload)
    return True


def release_lock() -> None:
    """Release lock only if held by this process."""
    try:
        held = json.loads(LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if held.get("pid") != os.getpid():
        return
    try:
        LOCK.unlink(missing_ok=True)
    except OSError:
        pass


def clean_env() -> dict[str, str]:
    """Return environment without GIT_DIR / GIT_WORK_TREE overrides."""
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def ensure_scratch_clone(source: Path, target: Path) -> bool:
    """Ensure an isolated scratch clone exists with working node_modules."""
    env = clean_env()
    if not (target / ".git").exists():
        print(f"Creating scratch clone at {target}...")
        res = subprocess.run(
            ["git", "clone", "--local", str(source), str(target)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if res.returncode != 0:
            print(f"Git clone failed: {res.stderr}", file=sys.stderr)
            return False

    # Check node_modules and linux bindings
    node_modules = target / "node_modules"
    if not node_modules.exists():
        src_nm = source / "node_modules"
        if src_nm.exists():
            try:
                os.symlink(src_nm, node_modules)
            except OSError:
                pass

    return True


def get_merge_commits(
    repo: Path, limit: int = 50, merges_only: bool = True
) -> list[dict[str, str]]:
    """Retrieve commit hash and first parent hash from repository."""
    env = clean_env()
    cmd = ["git", "-C", str(repo), "log"]
    if merges_only:
        cmd.append("--merges")
    cmd.extend(["--format=%H %P", f"-n{limit}", "main"])
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        env=env,
    )
    pairs = []
    for line in res.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            child = parts[0]
            parent = parts[1]
            pairs.append({"child": child, "parent": parent})
    return pairs


def run_commit_test(
    scratch_repo: Path,
    commit_hash: str,
    test_ref: str,
    test_target: str,
    timeout_s: int,
) -> dict:
    """Check out a commit, overlay tests from test_ref, and execute vitest."""
    env = clean_env()
    started = time.monotonic()

    # Step 1: Force checkout target commit
    r_co = subprocess.run(
        ["git", "-C", str(scratch_repo), "checkout", "-f", commit_hash],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=30,
    )
    if r_co.returncode != 0:
        return {
            "passed": False,
            "error": f"checkout_failed: {r_co.stderr.strip()[:200]}",
            "timed_out": False,
            "duration_s": round(time.monotonic() - started, 3),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
        }

    # Step 2: Overlay test files from future reference
    r_ov = subprocess.run(
        ["git", "-C", str(scratch_repo), "checkout", test_ref, "--", test_target],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=30,
    )
    if r_ov.returncode != 0:
        return {
            "passed": False,
            "error": f"test_overlay_failed: {r_ov.stderr.strip()[:200]}",
            "timed_out": False,
            "duration_s": round(time.monotonic() - started, 3),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
        }

    # Step 3: Execute vitest with JSON output
    out_json = scratch_repo / f"vitest-out-{os.getpid()}-{int(time.time()*1000)}.json"
    cmd = [
        "npx",
        "vitest",
        "run",
        test_target,
        "--reporter=json",
        f"--outputFile={out_json}",
        "--passWithNoTests",
        "--testTimeout=5000",
    ]

    test_started = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        cwd=str(scratch_repo),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        **({} if os.name == "nt" else {"start_new_session": True}),
    )

    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_tree(proc.pid)
        try:
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = "", ""

    test_duration = time.monotonic() - test_started
    total_duration = time.monotonic() - started

    if timed_out:
        if out_json.exists():
            out_json.unlink(missing_ok=True)
        return {
            "passed": False,
            "error": "vitest_timeout",
            "timed_out": True,
            "duration_s": round(total_duration, 3),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
        }

    # Parse JSON output
    passed = False
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    err_msg = None

    if out_json.exists():
        try:
            data = json.loads(out_json.read_text(encoding="utf-8"))
            total_tests = data.get("numTotalTests", 0)
            passed_tests = data.get("numPassedTests", 0)
            failed_tests = data.get("numFailedTests", 0)
            passed = bool(data.get("success", False)) and (failed_tests == 0)
        except Exception as exc:
            err_msg = f"json_parse_error: {exc}"
        finally:
            out_json.unlink(missing_ok=True)
    else:
        passed = (proc.returncode == 0)
        if proc.returncode != 0:
            err_msg = f"vitest_nonzero_exit: {proc.returncode}"

    return {
        "passed": passed,
        "error": err_msg,
        "timed_out": False,
        "duration_s": round(total_duration, 3),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "returncode": proc.returncode,
    }


def run_pair(
    scratch_repo: Path,
    child_hash: str,
    parent_hash: str,
    test_ref: str,
    test_target: str,
    timeout_s: int,
) -> dict:
    """Run retro-verification on parent and candidate child commit."""
    started = time.monotonic()

    parent_result = run_commit_test(
        scratch_repo, parent_hash, test_ref, test_target, timeout_s
    )
    child_result = run_commit_test(
        scratch_repo, child_hash, test_ref, test_target, timeout_s
    )

    pair_duration = round(time.monotonic() - started, 3)

    # Classification
    if parent_result["timed_out"] or child_result["timed_out"]:
        outcome = "timeout"
    elif parent_result.get("error") and ("checkout_failed" in str(parent_result.get("error")) or "test_overlay_failed" in str(parent_result.get("error"))):
        outcome = "execution_error"
    elif child_result.get("error") and ("checkout_failed" in str(child_result.get("error")) or "test_overlay_failed" in str(child_result.get("error"))):
        outcome = "execution_error"
    elif parent_result["passed"] and not child_result["passed"]:
        outcome = "defect"  # Parent passed later tests; child introduced regression
    elif parent_result["passed"] and child_result["passed"]:
        outcome = "clean"   # Both satisfy later tests
    elif not parent_result["passed"] and not child_result["passed"]:
        outcome = "drift"   # Both fail later tests (unattributable interface/dependency drift)
    elif not parent_result["passed"] and child_result["passed"]:
        outcome = "enhancement"  # Child added functionality asserted by later tests
    else:
        outcome = "unknown"

    return {
        "child_commit": child_hash,
        "parent_commit": parent_hash,
        "outcome": outcome,
        "pair_duration_s": pair_duration,
        "parent_result": parent_result,
        "child_result": child_result,
    }


def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate Wilson score confidence interval."""
    if n == 0:
        return 0.0, 1.0
    z = 1.959963984540054  # 95%
    p = k / n
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    spread = z * math.sqrt((p * (1 - p) / n + z**2 / (4 * n**2))) / denominator
    return round(max(0.0, center - spread), 4), round(min(1.0, center + spread), 4)


def summarise(records: list[dict]) -> dict:
    """Summarise retro-verification run outcomes and metrics."""
    total = len(records)
    outcomes = {}
    for r in records:
        outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1

    defects = outcomes.get("defect", 0)
    cleans = outcomes.get("clean", 0)
    drifts = outcomes.get("drift", 0)
    enhancements = outcomes.get("enhancement", 0)
    timeouts = outcomes.get("timeout", 0)
    errors = outcomes.get("execution_error", 0)

    evaluable_parent_passes = defects + cleans
    drift_rate = round(drifts / total, 4) if total > 0 else 0.0
    discrimination_rate = round((defects + enhancements) / total, 4) if total > 0 else 0.0

    durations = [r["pair_duration_s"] for r in records]
    median_pair_duration = round(float(statistics.median(durations)), 3) if durations else 0.0

    if evaluable_parent_passes > 0:
        beta_point = round(defects / evaluable_parent_passes, 4)
        beta_low, beta_high = wilson_score_interval(defects, evaluable_parent_passes)
        beta_interval = [beta_low, beta_high]
    else:
        beta_point = None
        beta_interval = None

    # Stopping rule evaluations
    if drift_rate > 0.80:
        stopping_verdict = "rejected_high_drift"
    elif evaluable_parent_passes < 10:
        stopping_verdict = "insufficient_evidence"
    elif discrimination_rate > 0 and drift_rate <= 0.80:
        stopping_verdict = "admitted_mechanical_oracle"
    else:
        stopping_verdict = "inconclusive"

    return {
        "total_pairs_evaluated": total,
        "outcomes": outcomes,
        "drift_rate": drift_rate,
        "discrimination_rate": discrimination_rate,
        "evaluable_parent_pass_count": evaluable_parent_passes,
        "beta_retro_point": beta_point,
        "beta_retro_95_interval": beta_interval,
        "median_pair_duration_s": median_pair_duration,
        "stopping_rule_verdict": stopping_verdict,
    }


def main() -> int:
    run_id = f"exp43-{time.strftime('%Y%m%dT%H%M%S')}-{os.getpid()}"
    if not acquire_lock(run_id, MAX_WALL_CLOCK_S):
        return 3

    print(f"EXP-43 retro-verifier run {run_id} starting...")
    if not ensure_scratch_clone(CORPUS_REPO, SCRATCH_DIR):
        print("Failed to initialize scratch clone.", file=sys.stderr)
        return 2

    # Get merge commit candidates
    all_pairs = get_merge_commits(SCRATCH_DIR, limit=50)
    if not all_pairs:
        print("No historical commits found in scratch clone.", file=sys.stderr)
        return 2

    # Primary evaluation: N = 50 on subsystem suite
    target_pairs = all_pairs[:50]
    test_ref = "HEAD"
    test_target = "tests/unit/services"

    started = time.monotonic()
    records: list[dict] = []
    stop_reason = None

    for idx, pair in enumerate(target_pairs, start=1):
        elapsed = time.monotonic() - started
        if elapsed > MAX_WALL_CLOCK_S:
            stop_reason = "wall_clock_cap"
            break

        print(
            f"Evaluating pair {idx}/{len(target_pairs)} (child {pair['child'][:8]} vs parent {pair['parent'][:8]})..."
        )
        rec = run_pair(
            SCRATCH_DIR,
            pair["child"],
            pair["parent"],
            test_ref,
            test_target,
            timeout_s=DEFAULT_TIMEOUT_S,
        )
        records.append(rec)
        print(f"  -> Outcome: {rec['outcome']} ({rec['pair_duration_s']}s)")

        # Write checkpoint with run_id
        checkpoint = {
            "run_id": run_id,
            "complete": False,
            "stop_reason": None,
            "records": records,
        }
        RESULTS.write_text(json.dumps(checkpoint, indent=1), encoding="utf-8")

    summary = summarise(records)
    final_payload = {
        "run_id": run_id,
        "protocol": {
            "sample_size": len(target_pairs),
            "test_ref": test_ref,
            "test_target": test_target,
            "timeout_s": DEFAULT_TIMEOUT_S,
        },
        "limitations": LIMITATIONS,
        "complete": stop_reason is None,
        "stop_reason": stop_reason,
        "elapsed_s": round(time.monotonic() - started, 3),
        "records": records,
        "summary": summary,
    }
    RESULTS.write_text(json.dumps(final_payload, indent=1), encoding="utf-8")
    print("\nEXP-43 Primary Summary:")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        release_lock()

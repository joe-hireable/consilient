import json
import subprocess

import pytest
import run_exp07
from headroom import admission_reason
from run_exp07 import (
    FIXTURES,
    GIT,
    LOCAL_ATTEMPTS,
    MIN_ATTEMPT_S,
    attempt_timeout,
    build_result,
    make_repo,
    summarise,
    verify,
    write_results,
)


@pytest.fixture(autouse=True)
def isolate_result_path(monkeypatch, tmp_path):
    """A test must never create, replace or delete the retained experiment result."""
    monkeypatch.setattr(run_exp07, "RESULTS", tmp_path / "results-exp07.json")

SOLUTION = """import re

def parse_duration(value):
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    order = {"d": 0, "h": 1, "m": 2, "s": 3}
    parts = value.strip().split()
    if not parts:
        raise ValueError(value)
    seen = set()
    prior = -1
    total = 0
    for part in parts:
        match = re.fullmatch(r"(0|[1-9]\\d*)([dhms])", part)
        if not match:
            raise ValueError(value)
        amount, unit = match.groups()
        if unit in seen or order[unit] <= prior:
            raise ValueError(value)
        seen.add(unit)
        prior = order[unit]
        total += int(amount) * units[unit]
    return total
"""


def row(fixture, condition, attempt, passed, seconds, censored=False):
    return {
        "fixture": fixture,
        "condition": condition,
        "attempt": attempt,
        "duration_s_including_verifier": seconds,
        "censored": censored,
        "verifier": {"passed": passed},
    }


def commit_all(repo, message):
    subprocess.run([GIT, "add", "-A"], cwd=repo, check=True)
    subprocess.run([GIT, "commit", "-qm", message], cwd=repo, check=True)


def test_admission_fails_closed_and_rejects_the_ninety_percent_boundary():
    good = {
        "plan_type": "pro",
        "used_percent": 89,
        "resets_at": 123,
        "rate_limit_reached_type": None,
        "spend_control_reached": False,
    }
    assert admission_reason(good, 90) is None
    assert (
        admission_reason({**good, "used_percent": 90}, 90)
        == "reserved headroom unavailable"
    )
    assert (
        admission_reason({**good, "used_percent": 91}, 90)
        == "reserved headroom unavailable"
    )
    assert admission_reason({**good, "used_percent": None}, 90) == "headroom unknown"
    assert (
        admission_reason({**good, "plan_type": "unknown"}, 90)
        == "subscription plan unavailable"
    )
    assert admission_reason(
        {**good, "rate_limit_reached_type": "rate_limit_reached"}, 90
    )


def test_summary_separates_single_and_five_attempt_cost():
    runs = []
    for fixture in FIXTURES:
        runs.append(row(fixture["id"], "frontier", 1, True, 10))
        for attempt in range(1, LOCAL_ATTEMPTS + 1):
            runs.append(row(fixture["id"], "local", attempt, False, 25))
    summary = summarise(runs)
    assert summary["single_attempt"]["median"] == 2.5
    assert summary["single_attempt"]["verdict"] == "replicates_2x_trigger"
    assert summary["best_of_five"]["median"] == 12.5
    assert summary["best_of_five"]["verdict"] == "replicates_2x_trigger"
    assert summary["single_attempt"]["eligible_pairs"] == 5
    assert summary["best_of_five"]["eligible_pairs"] == 5
    assert summary["interpretation"].startswith("single attempt crosses")


def test_summary_requires_three_eligible_pairs():
    runs = []
    for index, fixture in enumerate(FIXTURES):
        runs.append(row(fixture["id"], "frontier", 1, True, 10))
        for attempt in range(1, LOCAL_ATTEMPTS + 1):
            runs.append(row(fixture["id"], "local", attempt, index >= 2, 25))
    summary = summarise(runs)
    assert summary["single_attempt"]["eligible_pairs"] == 2
    assert summary["single_attempt"]["verdict"] == "insufficient_evidence"
    assert summary["best_of_five"]["eligible_pairs"] == 2
    assert summary["best_of_five"]["verdict"] == "insufficient_evidence"


def test_summary_tolerates_a_partial_run():
    runs = [row(FIXTURES[0]["id"], "frontier", 1, True, 10)]
    summary = summarise(runs)
    assert [pair["fixture"] for pair in summary["pairs"]] == [FIXTURES[0]["id"]]
    assert summary["single_attempt"]["verdict"] == "insufficient_evidence"


def test_censored_duration_is_never_an_exact_ratio_or_a_non_replication():
    runs = []
    for fixture in FIXTURES:
        runs.append(row(fixture["id"], "frontier", 1, True, 10))
        for attempt in range(1, LOCAL_ATTEMPTS + 1):
            runs.append(row(fixture["id"], "local", attempt, False, 3, censored=True))
    summary = summarise(runs)
    # Median lower bound is 0.3x: below 2, but a timeout cannot prove a non-crossing.
    assert summary["single_attempt"]["median"] == 0.3
    assert summary["single_attempt"]["censored_pairs"] == 5
    assert summary["single_attempt"]["median_is_lower_bound"] is True
    assert summary["single_attempt"]["verdict"] == "insufficient_evidence"
    assert summary["pairs"][0]["single_multiplier_is_lower_bound"] is True
    assert summary["interpretation"].startswith("no causal attribution")


def test_censored_median_at_or_above_two_still_replicates():
    runs = []
    for fixture in FIXTURES:
        runs.append(row(fixture["id"], "frontier", 1, True, 10))
        for attempt in range(1, LOCAL_ATTEMPTS + 1):
            runs.append(row(fixture["id"], "local", attempt, False, 30, censored=True))
    summary = summarise(runs)
    assert summary["single_attempt"]["median"] == 3.0
    assert summary["single_attempt"]["median_is_lower_bound"] is True
    assert summary["single_attempt"]["verdict"] == "replicates_2x_trigger"


def test_uncensored_shortfall_still_fails_to_replicate():
    runs = []
    for fixture in FIXTURES:
        runs.append(row(fixture["id"], "frontier", 1, True, 10))
        for attempt in range(1, LOCAL_ATTEMPTS + 1):
            runs.append(row(fixture["id"], "local", attempt, False, 3))
    summary = summarise(runs)
    assert summary["single_attempt"]["verdict"] == "does_not_replicate_2x_trigger"
    assert summary["single_attempt"]["median_is_lower_bound"] is False
    # Best-of-five keeps its full 5x serial cost and is judged separately.
    assert summary["best_of_five"]["median"] == 1.5
    assert summary["best_of_five"]["verdict"] == "does_not_replicate_2x_trigger"


def test_attempt_timeout_reduces_or_skips_against_the_outer_cap():
    assert attempt_timeout(1000, 240) == 240
    assert attempt_timeout(100, 240) == 100
    assert attempt_timeout(MIN_ATTEMPT_S, 240) == MIN_ATTEMPT_S
    assert attempt_timeout(MIN_ATTEMPT_S - 1, 240) is None
    assert attempt_timeout(-5, 240) is None


def test_verifier_accepts_a_committed_solution_and_rejects_committed_extras():
    repo, baseline = make_repo(FIXTURES[0])
    assert not verify(repo, baseline)["passed"]

    (repo / "solution.py").write_text(SOLUTION, encoding="utf-8")
    commit_all(repo, "solve")
    accepted = verify(repo, baseline)
    assert accepted["passed"], accepted
    assert accepted["changed_files"] == ["solution.py"]

    (repo / "test_runner.py").write_text("pass\n", encoding="utf-8")
    (repo / "unexpected.py").write_text("pass\n", encoding="utf-8")
    commit_all(repo, "tamper")
    rejected = verify(repo, baseline)
    assert not rejected["passed"]
    assert rejected["tests_passed"]
    assert rejected["changed_files"] == [
        "solution.py",
        "test_runner.py",
        "unexpected.py",
    ]


def test_verifier_rejects_uncommitted_extra_files():
    repo, baseline = make_repo(FIXTURES[0])
    (repo / "solution.py").write_text(SOLUTION, encoding="utf-8")
    (repo / "unexpected.py").write_text("pass\n", encoding="utf-8")
    rejected = verify(repo, baseline)
    assert not rejected["passed"]
    assert rejected["tests_passed"]
    assert rejected["changed_files"] == ["solution.py", "unexpected.py"]


def test_verifier_timeout_is_reported_rather_than_raised():
    repo, baseline = make_repo(FIXTURES[0])
    (repo / "solution.py").write_text(SOLUTION, encoding="utf-8")
    (repo / "test_runner.py").write_text(
        "import time\ntime.sleep(30)\n", encoding="utf-8"
    )
    result = verify(repo, baseline, timeout_s=1)
    assert result["timeout"] is True
    assert result["tests_passed"] is False
    assert result["passed"] is False


def test_verifier_fails_closed_when_scope_evidence_is_unavailable(monkeypatch):
    repo, baseline = make_repo(FIXTURES[0])
    (repo / "solution.py").write_text(SOLUTION, encoding="utf-8")

    def unavailable(*_args):
        raise subprocess.CalledProcessError(128, [GIT, "diff"])

    monkeypatch.setattr(run_exp07, "changed_since", unavailable)
    result = verify(repo, baseline)
    assert result["passed"] is False
    assert result["tests_passed"] is True
    assert result["scope_valid"] is False
    assert "CalledProcessError" in result["scope_error"]


def test_checkpoint_is_valid_and_retains_spent_attempts():
    runs = [row(FIXTURES[0]["id"], "frontier", 1, True, 10)]
    snapshots = [{"used_percent": 12}]
    write_results(build_result(runs, snapshots, 42.0, "headroom probe failed: boom"))
    from run_exp07 import RESULTS

    saved = json.loads(RESULTS.read_text(encoding="utf-8"))
    assert saved["complete"] is False
    assert saved["summary"] is None
    assert saved["stop_reason"] == "headroom probe failed: boom"
    assert len(saved["runs"]) == 1
    assert saved["headroom_snapshots"] == snapshots
    assert saved["limitations"][0].startswith("Reasoning modes are not matched")
    assert not RESULTS.with_suffix(".json.tmp").exists()
    RESULTS.unlink()


def test_main_reduces_then_skips_attempts_against_the_outer_cap(monkeypatch):
    import sys

    import run_exp07
    from run_exp07 import RESULTS

    calls = []

    def fake_headroom():
        return {
            "plan_type": "pro",
            "used_percent": 12,
            "resets_at": 1,
            "rate_limit_reached_type": None,
            "spend_control_reached": False,
        }

    def fake_attempt(fixture, condition, attempt, timeout_s, configured):
        calls.append(timeout_s)
        passed = condition == "frontier"
        return {
            "fixture": fixture["id"],
            "condition": condition,
            "attempt": attempt,
            "duration_s_including_verifier": 10.0 if passed else 25.0,
            "censored": False,
            "outcome": "passed" if passed else "rejected",
            "timeout_s_applied": timeout_s,
            "timeout_s_configured": configured,
            "verifier": {"passed": passed},
        }

    monkeypatch.setattr(run_exp07, "CODEX", run_exp07.CODEX or "codex-stub")
    monkeypatch.setattr(run_exp07, "read_codex_headroom", fake_headroom)
    monkeypatch.setattr(run_exp07, "run_attempt", fake_attempt)
    monkeypatch.setattr(sys, "argv", ["run_exp07.py"])

    # A cap tighter than the configured timeout reduces every attempt to fit.
    monkeypatch.setattr(run_exp07, "MAX_ELAPSED_S", 45)
    run_exp07.main()
    saved = json.loads(RESULTS.read_text(encoding="utf-8"))
    assert calls and all(MIN_ATTEMPT_S <= applied <= 45 for applied in calls), calls
    assert all(run["timeout_s_applied"] <= 45 for run in saved["runs"])
    assert all(run["timeout_s_configured"] == 240 for run in saved["runs"])

    # A cap below the minimum useful attempt skips it rather than overrunning.
    calls.clear()
    monkeypatch.setattr(run_exp07, "MAX_ELAPSED_S", MIN_ATTEMPT_S - 1)
    run_exp07.main()
    saved = json.loads(RESULTS.read_text(encoding="utf-8"))
    assert calls == []
    assert saved["complete"] is False
    assert saved["stop_reason"].startswith("wall-clock cap")
    assert saved["headroom_snapshots"], "the spent headroom probe must be retained"
    RESULTS.unlink()


def test_checkpoint_survives_a_transient_windows_lock(monkeypatch):
    import os

    import run_exp07
    from run_exp07 import RESULTS

    real_replace = os.replace
    attempts = []

    def flaky(src, dst):
        attempts.append(1)
        if len(attempts) == 1:
            raise PermissionError(5, "Access is denied")
        return real_replace(src, dst)

    monkeypatch.setattr(run_exp07.os, "replace", flaky)
    write_results(build_result([], [], 1.0, None))
    assert len(attempts) == 2
    assert json.loads(RESULTS.read_text(encoding="utf-8"))["complete"] is False
    assert not RESULTS.with_suffix(".json.tmp").exists()
    RESULTS.unlink()

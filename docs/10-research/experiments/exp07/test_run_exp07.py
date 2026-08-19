from headroom import admission_reason
from run_exp07 import FIXTURES, make_repo, summarise, verify


def row(fixture, condition, attempt, passed, seconds):
    return {
        "fixture": fixture,
        "condition": condition,
        "attempt": attempt,
        "duration_s_including_verifier": seconds,
        "verifier": {"passed": passed},
    }


def test_admission_fails_closed_and_reserves_headroom():
    good = {
        "plan_type": "pro",
        "used_percent": 90,
        "resets_at": 123,
        "rate_limit_reached_type": None,
        "spend_control_reached": False,
    }
    assert admission_reason(good, 90) is None
    assert admission_reason({**good, "used_percent": 91}, 90) == "reserved headroom unavailable"
    assert admission_reason({**good, "used_percent": None}, 90) == "headroom unknown"
    assert admission_reason({**good, "plan_type": "unknown"}, 90) == "subscription plan unavailable"
    assert admission_reason({**good, "rate_limit_reached_type": "rate_limit_reached"}, 90)


def test_summary_separates_single_and_five_attempt_cost():
    runs = []
    for fixture in FIXTURES:
        runs.append(row(fixture["id"], "frontier", 1, True, 10))
        for attempt in range(1, 6):
            runs.append(row(fixture["id"], "local", attempt, False, 25))
    summary = summarise(runs)
    assert summary["single_attempt"] == {
        "eligible_pairs": 5,
        "median": 2.5,
        "verdict": "replicates_2x_trigger",
    }
    assert summary["best_of_five"] == {
        "eligible_pairs": 5,
        "median": 12.5,
        "verdict": "replicates_2x_trigger",
    }
    assert summary["interpretation"].startswith("single attempt crosses")


def test_summary_requires_three_eligible_pairs():
    runs = []
    for index, fixture in enumerate(FIXTURES):
        runs.append(row(fixture["id"], "frontier", 1, True, 10))
        for attempt in range(1, 6):
            runs.append(row(fixture["id"], "local", attempt, index >= 2, 25))
    summary = summarise(runs)
    assert summary["single_attempt"]["eligible_pairs"] == 2
    assert summary["single_attempt"]["verdict"] == "insufficient_evidence"
    assert summary["best_of_five"]["eligible_pairs"] == 2
    assert summary["best_of_five"]["verdict"] == "insufficient_evidence"


def test_verifier_requires_functional_pass_and_exact_changed_file_scope():
    repo = make_repo(FIXTURES[0])
    assert not verify(repo)["passed"]
    (repo / "solution.py").write_text(
        """import re

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
""",
        encoding="utf-8",
    )
    accepted = verify(repo)
    assert accepted["passed"], accepted
    (repo / "unexpected.py").write_text("pass\n", encoding="utf-8")
    rejected = verify(repo)
    assert not rejected["passed"]
    assert rejected["tests_passed"]
    assert rejected["changed_files"] == ["solution.py", "unexpected.py"]

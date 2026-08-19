"""EXP-07: paired frontier/local wasted-work timing on frozen public fixtures."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from headroom import admission_reason, read_codex_headroom


CODEX = shutil.which("codex")
GIT = shutil.which("git")
PYTHON = sys.executable
HERE = Path(__file__).parent
RESULTS = HERE / "results-exp07.json"
MAX_ELAPSED_S = 90 * 60
LOCAL_ATTEMPTS = 5
MAX_FRONTIER_USED_PERCENT = 90
VERIFIER_TIMEOUT_S = 20
MIN_ATTEMPT_S = 30

LIMITATIONS = [
    "Reasoning modes are not matched: gpt-5.6-sol runs at explicit low reasoning effort "
    "while qwen3:8b runs at its Ollama default. Every multiplier compares two harness "
    "configurations as configured, not two models at matched reasoning effort.",
    "Timed-out attempts are right-censored: their durations are lower bounds, so a "
    "multiplier derived from one is a lower bound and can prove a crossing but can never "
    "prove a non-crossing.",
    "Synthetic fixtures can replicate the latency mechanism but cannot establish that a "
    "learned router improves real work.",
]


FIXTURES = [
    {
        "id": "duration-parser",
        "goal": (
            "Implement parse_duration in solution.py. Accept space-separated non-negative "
            "integer components using d, h, m, s in descending unit order, with each unit "
            "at most once. Return total seconds. Reject empty, malformed, duplicate or "
            "out-of-order input with ValueError. Edit only solution.py and run the tests."
        ),
        "stub": "def parse_duration(value):\n    raise NotImplementedError\n",
        "tests": r'''from solution import parse_duration

assert parse_duration("0s") == 0
assert parse_duration("1h 30m") == 5400
assert parse_duration("2d 4h 5s") == 187205
assert parse_duration(" 3m 2s ") == 182
for bad in ("", "1m 2h", "1h 2h", "1x", "-1h", "1 h", "1.5h"):
    try:
        parse_duration(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(bad)
''',
    },
    {
        "id": "event-replay",
        "goal": (
            "Implement replay in solution.py. Events are dictionaries with global seq, v, "
            "ticket and type. Global seq must start at 1 and be consecutive; v must be 1. "
            "created starts a ticket. claimed requires owner and an epoch strictly above the "
            "ticket's prior epoch. completed requires the current epoch and a claimed ticket. "
            "Reject invalid or stale transitions with ValueError. Return ticket states. Edit "
            "only solution.py and run the tests."
        ),
        "stub": "def replay(events):\n    raise NotImplementedError\n",
        "tests": r'''from solution import replay

events = [
    {"seq": 1, "v": 1, "ticket": "a", "type": "created"},
    {"seq": 2, "v": 1, "ticket": "a", "type": "claimed", "owner": "x", "epoch": 1},
    {"seq": 3, "v": 1, "ticket": "b", "type": "created"},
    {"seq": 4, "v": 1, "ticket": "a", "type": "completed", "epoch": 1},
]
state = replay(events)
assert state["a"] == {"state": "completed", "owner": "x", "epoch": 1}
assert state["b"] == {"state": "created", "owner": None, "epoch": 0}

bad_cases = [
    [{"seq": 2, "v": 1, "ticket": "a", "type": "created"}],
    [{"seq": 1, "v": 2, "ticket": "a", "type": "created"}],
    [{"seq": 1, "v": 1, "ticket": "a", "type": "claimed", "owner": "x", "epoch": 1}],
    [
        {"seq": 1, "v": 1, "ticket": "a", "type": "created"},
        {"seq": 2, "v": 1, "ticket": "a", "type": "claimed", "owner": "x", "epoch": 1},
        {"seq": 3, "v": 1, "ticket": "a", "type": "claimed", "owner": "y", "epoch": 1},
    ],
    [
        {"seq": 1, "v": 1, "ticket": "a", "type": "created"},
        {"seq": 2, "v": 1, "ticket": "a", "type": "claimed", "owner": "x", "epoch": 1},
        {"seq": 3, "v": 1, "ticket": "a", "type": "completed", "epoch": 2},
    ],
]
for bad in bad_cases:
    try:
        replay(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(bad)
''',
    },
    {
        "id": "windows-wsl-path",
        "goal": (
            "Implement windows_to_wsl in solution.py. Convert an absolute drive-letter "
            "Windows path to /mnt/<lowercase drive>/..., accepting slash or backslash and "
            "normalising dot segments. Reject relative paths, UNC paths, NUL, and any .. "
            "that would escape the drive root with ValueError. Edit only solution.py and run "
            "the tests."
        ),
        "stub": "def windows_to_wsl(value):\n    raise NotImplementedError\n",
        "tests": r'''from solution import windows_to_wsl

assert windows_to_wsl(r"C:\Users\Joe\repo") == "/mnt/c/Users/Joe/repo"
assert windows_to_wsl("D:/work/./repo/src") == "/mnt/d/work/repo/src"
assert windows_to_wsl(r"E:\work\child\..\repo") == "/mnt/e/work/repo"
assert windows_to_wsl("c:/") == "/mnt/c"
for bad in ("repo/file", r"\\server\share\x", "C:/../../x", "C:\\x\x00bad", "1:/x"):
    try:
        windows_to_wsl(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(repr(bad))
''',
    },
    {
        "id": "wilson-verdict",
        "goal": (
            "Implement wilson_interval and beta_verdict in solution.py. wilson_interval "
            "returns the 95% Wilson low/high interval for false_accepts out of bad_total and "
            "validates 0 <= false_accepts <= bad_total. beta_verdict returns estimate, low, "
            "high and status; status is insufficient_data for zero observations or interval "
            "half-width above max_half_width, otherwise measured. Edit only solution.py and "
            "run the tests."
        ),
        "stub": (
            "def wilson_interval(false_accepts, bad_total, z=1.96):\n"
            "    raise NotImplementedError\n\n"
            "def beta_verdict(false_accepts, bad_total, max_half_width=0.05):\n"
            "    raise NotImplementedError\n"
        ),
        "tests": r'''from math import isclose
from solution import beta_verdict, wilson_interval

low, high = wilson_interval(12, 100)
assert isclose(low, 0.069994, abs_tol=1e-5)
assert isclose(high, 0.198120, abs_tol=1e-5)
for args in ((-1, 10), (11, 10), (1, -1)):
    try:
        wilson_interval(*args)
    except ValueError:
        pass
    else:
        raise AssertionError(args)
empty = beta_verdict(0, 0)
assert empty["status"] == "insufficient_data"
assert empty["estimate"] is None and empty["low"] is None and empty["high"] is None
wide = beta_verdict(1, 10, max_half_width=0.05)
assert wide["status"] == "insufficient_data"
narrow = beta_verdict(120, 1000, max_half_width=0.05)
assert narrow["status"] == "measured" and isclose(narrow["estimate"], 0.12)
''',
    },
    {
        "id": "headroom-admission",
        "goal": (
            "Implement admit in solution.py. snapshot contains used_percent, observed_at, "
            "resets_at and stale_after_s; reservations contain amount and resets_at; request "
            "contains amount, now and resets_at. Return a dict with admitted, reason and "
            "remaining_percent. Fail closed for missing fields, stale snapshots, reset "
            "mismatch or invalid amounts. Count only reservations for the request reset and "
            "admit exactly at the 100% boundary. Edit only solution.py and run the tests."
        ),
        "stub": "def admit(snapshot, reservations, request):\n    raise NotImplementedError\n",
        "tests": r'''from solution import admit

snapshot = {"used_percent": 60, "observed_at": 1000, "resets_at": 2000, "stale_after_s": 300}
request = {"amount": 15, "now": 1100, "resets_at": 2000}
ok = admit(snapshot, [{"amount": 25, "resets_at": 2000}], request)
assert ok == {"admitted": True, "reason": None, "remaining_percent": 0}
old = admit(snapshot, [{"amount": 99, "resets_at": 1500}], request)
assert old == {"admitted": True, "reason": None, "remaining_percent": 25}
over = admit(snapshot, [{"amount": 26, "resets_at": 2000}], request)
assert over["admitted"] is False and over["reason"] == "insufficient_headroom"
stale = admit(snapshot, [], {**request, "now": 1301})
assert stale["admitted"] is False and stale["reason"] == "stale_snapshot"
mismatch = admit(snapshot, [], {**request, "resets_at": 3000})
assert mismatch["admitted"] is False and mismatch["reason"] == "reset_mismatch"
for bad_request in ({"amount": -1, "now": 1100, "resets_at": 2000}, {"now": 1100, "resets_at": 2000}):
    result = admit(snapshot, [], bad_request)
    assert result["admitted"] is False and result["reason"] == "invalid_or_unknown"
''',
    },
]


def make_repo(fixture):
    repo = Path(tempfile.mkdtemp(prefix=f"exp07-{fixture['id']}-"))
    subprocess.run([GIT, "init", "-q"], cwd=repo, check=True)
    subprocess.run([GIT, "config", "user.email", "exp07@local"], cwd=repo, check=True)
    subprocess.run([GIT, "config", "user.name", "EXP-07"], cwd=repo, check=True)
    (repo / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
    (repo / "solution.py").write_text(fixture["stub"], encoding="utf-8")
    (repo / "test_runner.py").write_text(fixture["tests"], encoding="utf-8")
    subprocess.run([GIT, "add", "."], cwd=repo, check=True)
    subprocess.run([GIT, "commit", "-qm", "fixture"], cwd=repo, check=True)
    baseline = subprocess.run(
        [GIT, "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip()
    return repo, baseline


def changed_since(repo, baseline):
    """Files differing from the immutable baseline commit, committed or not."""
    tracked = subprocess.run(
        [GIT, "diff", "--name-only", baseline],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.splitlines()
    untracked = subprocess.run(
        [GIT, "ls-files", "--others", "--exclude-standard"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.splitlines()
    return sorted({line.strip() for line in tracked + untracked if line.strip()})


def verify(repo, baseline, timeout_s=VERIFIER_TIMEOUT_S):
    started = time.monotonic()
    try:
        test = subprocess.run(
            [PYTHON, "test_runner.py"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        tests_passed = test.returncode == 0
        tail = (test.stderr or test.stdout)[-300:]
        timed_out = False
    except subprocess.TimeoutExpired:
        tests_passed = False
        tail = "verifier timeout"
        timed_out = True
    changed_files = changed_since(repo, baseline)
    return {
        "passed": tests_passed and changed_files == ["solution.py"],
        "tests_passed": tests_passed,
        "timeout": timed_out,
        "changed_files": changed_files,
        "duration_s": round(time.monotonic() - started, 3),
        "test_tail": tail,
    }


def usage_from_events(stdout):
    usage = {}
    for line in (stdout or "").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            usage = event.get("usage") or usage
    return usage


def attempt_timeout(remaining_s, configured_s):
    """Fit an attempt inside the outer cap; None means it cannot fit and must be skipped."""
    if remaining_s < MIN_ATTEMPT_S:
        return None
    return int(min(configured_s, remaining_s))


def run_attempt(fixture, condition, attempt, timeout_s, configured_timeout_s):
    repo, baseline = make_repo(fixture)
    command = [
        CODEX,
        "exec",
        fixture["goal"],
        "--json",
        "-C",
        str(repo),
        "--dangerously-bypass-approvals-and-sandbox",
        "--ephemeral",
        "--ignore-user-config",
    ]
    if condition == "frontier":
        command += ["-m", "gpt-5.6-sol", "-c", 'model_reasoning_effort="low"']
    else:
        command += ["--oss", "--local-provider", "ollama", "-m", "qwen3:8b"]
    started = time.monotonic()
    try:
        process = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        verifier = verify(repo, baseline)
        duration_s = time.monotonic() - started
        return_code = process.returncode
        usage = usage_from_events(process.stdout)
        if verifier["timeout"]:
            outcome, error = "verifier_timeout", "verifier timeout"
        elif verifier["passed"]:
            outcome, error = "passed", None
        else:
            outcome, error = "rejected", None
    except subprocess.TimeoutExpired:
        duration_s = time.monotonic() - started
        return_code = None
        usage = {}
        verifier = {
            "passed": False,
            "tests_passed": False,
            "timeout": True,
            "changed_files": [],
            "duration_s": 0,
            "test_tail": "agent timeout",
        }
        outcome, error = "agent_timeout", "agent timeout"
    return {
        "fixture": fixture["id"],
        "condition": condition,
        "attempt": attempt,
        "model": "gpt-5.6-sol" if condition == "frontier" else "qwen3:8b",
        "provider": "openai-subscription" if condition == "frontier" else "ollama",
        "reasoning_mode": "low" if condition == "frontier" else "ollama-default",
        "duration_s_including_verifier": round(duration_s, 3),
        # A timed-out attempt was cut short: its duration is a lower bound, not a measurement.
        "censored": outcome in ("agent_timeout", "verifier_timeout"),
        "outcome": outcome,
        "timeout_s_applied": timeout_s,
        "timeout_s_configured": configured_timeout_s,
        "return_code": return_code,
        "verifier": verifier,
        "usage": usage,
        "error": error,
    }


def summarise(runs):
    single_ratios = []
    five_ratios = []
    pairs = []
    for fixture in FIXTURES:
        name = fixture["id"]
        frontier = next(
            (
                row
                for row in runs
                if row["fixture"] == name and row["condition"] == "frontier"
            ),
            None,
        )
        if frontier is None:
            continue
        local = sorted(
            (
                row
                for row in runs
                if row["fixture"] == name and row["condition"] == "local"
            ),
            key=lambda row: row["attempt"],
        )
        pair = {
            "fixture": name,
            "frontier_passed": frontier["verifier"]["passed"],
            "local_passes": sum(row["verifier"]["passed"] for row in local),
            "local_censored": sum(bool(row.get("censored")) for row in local),
        }
        if (
            frontier["verifier"]["passed"]
            and local
            and not local[0]["verifier"]["passed"]
        ):
            ratio = (
                local[0]["duration_s_including_verifier"]
                / frontier["duration_s_including_verifier"]
            )
            censored = bool(local[0].get("censored"))
            pair["single_failed_multiplier"] = round(ratio, 3)
            pair["single_multiplier_is_lower_bound"] = censored
            single_ratios.append((ratio, censored))
        # Best-of-five stays a separate intervention and keeps its full serial cost.
        if (
            frontier["verifier"]["passed"]
            and len(local) == LOCAL_ATTEMPTS
            and not any(row["verifier"]["passed"] for row in local)
        ):
            ratio = (
                sum(row["duration_s_including_verifier"] for row in local)
                / frontier["duration_s_including_verifier"]
            )
            censored = any(bool(row.get("censored")) for row in local)
            pair["five_failed_multiplier"] = round(ratio, 3)
            pair["five_multiplier_is_lower_bound"] = censored
            five_ratios.append((ratio, censored))
        pairs.append(pair)

    def verdict(entries):
        censored_pairs = sum(1 for _, censored in entries if censored)
        base = {"eligible_pairs": len(entries), "censored_pairs": censored_pairs}
        if len(entries) < 3:
            return {
                **base,
                "median": None,
                "median_is_lower_bound": False,
                "verdict": "insufficient_evidence",
            }
        median = statistics.median(value for value, _ in entries)
        if median >= 2:
            # Censored values are lower bounds, so a median at or above 2 is still proven.
            outcome = "replicates_2x_trigger"
        elif censored_pairs:
            outcome = "insufficient_evidence"
        else:
            outcome = "does_not_replicate_2x_trigger"
        return {
            **base,
            "median": round(median, 3),
            "median_is_lower_bound": bool(censored_pairs),
            "verdict": outcome,
        }

    single = verdict(single_ratios)
    five = verdict(five_ratios)
    if single["verdict"] == "replicates_2x_trigger":
        interpretation = "single attempt crosses; best-of-five can only amplify it"
    elif five["verdict"] == "replicates_2x_trigger":
        interpretation = (
            "only best-of-five crosses; reasoning-layer cost causes the trigger"
        )
    else:
        interpretation = "no causal attribution; evidence is negative or insufficient"
    return {
        "pairs": pairs,
        "single_attempt": single,
        "best_of_five": five,
        "interpretation": interpretation,
    }


def build_result(runs, snapshots, elapsed_s, stop_reason):
    complete = len(runs) == len(FIXTURES) * (1 + LOCAL_ATTEMPTS)
    return {
        "protocol": {
            "fixtures": [fixture["id"] for fixture in FIXTURES],
            "frontier": "gpt-5.6-sol, low reasoning, Codex Pro subscription",
            "local": "qwen3:8b via Ollama, five serial attempts",
            "maximum_frontier_used_percent": MAX_FRONTIER_USED_PERCENT,
            "frontier_used_percent_boundary": "strictly below",
            "attempt_cap": 30,
            "wall_clock_cap_s": MAX_ELAPSED_S,
            "minimum_attempt_s": MIN_ATTEMPT_S,
            "verifier_timeout_s": VERIFIER_TIMEOUT_S,
        },
        "limitations": LIMITATIONS,
        "headroom_snapshots": snapshots,
        "complete": complete,
        "stop_reason": stop_reason,
        "elapsed_s": round(elapsed_s, 3),
        "runs": runs,
        "summary": summarise(runs) if complete else None,
    }


def write_results(payload):
    """Atomic so an interrupted or failed run always leaves a readable checkpoint."""
    tmp = RESULTS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Windows denies the rename while a watcher or scanner holds a transient handle;
    # retry briefly, then let a persistent failure surface.
    for delay in (0, 0.05, 0.2, 0.5, 1.0):
        time.sleep(delay)
        try:
            os.replace(tmp, RESULTS)
            return
        except PermissionError:
            continue
    os.replace(tmp, RESULTS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontier-timeout", type=int, default=240)
    parser.add_argument("--local-timeout", type=int, default=240)
    args = parser.parse_args()
    if CODEX is None or GIT is None:
        raise SystemExit("codex and git are required")
    started = time.monotonic()
    runs = []
    snapshots = []
    stop_reason = None

    def checkpoint():
        write_results(
            build_result(runs, snapshots, time.monotonic() - started, stop_reason)
        )

    def report():
        print(
            f"  outcome={runs[-1]['outcome']} "
            f"seconds={runs[-1]['duration_s_including_verifier']}"
            f"{'+' if runs[-1]['censored'] else ''}",
            flush=True,
        )

    try:
        for fixture in FIXTURES:
            try:
                snapshot = read_codex_headroom()
            except Exception as exc:
                stop_reason = f"headroom probe failed: {exc}"
                print(f"STOP {stop_reason}", flush=True)
                break
            snapshots.append(snapshot)
            checkpoint()
            reason = admission_reason(snapshot, MAX_FRONTIER_USED_PERCENT)
            if reason:
                stop_reason = f"frontier admission: {reason}"
                print(f"STOP {stop_reason}", flush=True)
                break
            timeout_s = attempt_timeout(
                MAX_ELAPSED_S - (time.monotonic() - started), args.frontier_timeout
            )
            if timeout_s is None:
                stop_reason = "wall-clock cap: no frontier attempt fits"
                print(f"STOP {stop_reason}", flush=True)
                break
            print(
                f"frontier {fixture['id']} headroom_used={snapshot['used_percent']}% "
                f"timeout={timeout_s}s",
                flush=True,
            )
            runs.append(
                run_attempt(fixture, "frontier", 1, timeout_s, args.frontier_timeout)
            )
            checkpoint()
            report()

        if len([row for row in runs if row["condition"] == "frontier"]) == len(
            FIXTURES
        ):
            for fixture in FIXTURES:
                for attempt in range(1, LOCAL_ATTEMPTS + 1):
                    timeout_s = attempt_timeout(
                        MAX_ELAPSED_S - (time.monotonic() - started), args.local_timeout
                    )
                    if timeout_s is None:
                        stop_reason = "wall-clock cap: no local attempt fits"
                        print(f"STOP {stop_reason}", flush=True)
                        break
                    print(
                        f"local {fixture['id']} attempt={attempt}/{LOCAL_ATTEMPTS} "
                        f"timeout={timeout_s}s",
                        flush=True,
                    )
                    runs.append(
                        run_attempt(
                            fixture, "local", attempt, timeout_s, args.local_timeout
                        )
                    )
                    checkpoint()
                    report()
                if stop_reason:
                    break
    except KeyboardInterrupt:
        stop_reason = "interrupted"
        print("STOP interrupted", flush=True)
    finally:
        result = build_result(runs, snapshots, time.monotonic() - started, stop_reason)
        write_results(result)

    print(f"result={RESULTS} complete={result['complete']}", flush=True)
    if result["complete"]:
        print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()

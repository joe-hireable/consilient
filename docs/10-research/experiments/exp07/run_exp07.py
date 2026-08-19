"""EXP-07: paired frontier/local wasted-work timing on frozen public fixtures."""

from __future__ import annotations

import argparse
import json
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
    return repo


def verify(repo):
    started = time.monotonic()
    test = subprocess.run(
        [PYTHON, "test_runner.py"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )
    changed = subprocess.run(
        [GIT, "status", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.splitlines()
    changed_files = sorted(line[3:].strip() for line in changed if len(line) >= 4)
    return {
        "passed": test.returncode == 0 and changed_files == ["solution.py"],
        "tests_passed": test.returncode == 0,
        "changed_files": changed_files,
        "duration_s": round(time.monotonic() - started, 3),
        "test_tail": (test.stderr or test.stdout)[-300:],
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


def run_attempt(fixture, condition, attempt, timeout_s):
    repo = make_repo(fixture)
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
        verifier = verify(repo)
        duration_s = time.monotonic() - started
        return_code = process.returncode
        usage = usage_from_events(process.stdout)
        error = None
    except subprocess.TimeoutExpired:
        duration_s = time.monotonic() - started
        return_code = None
        usage = {}
        verifier = {
            "passed": False,
            "tests_passed": False,
            "changed_files": [],
            "duration_s": 0,
            "test_tail": "attempt timeout",
        }
        error = "timeout"
    return {
        "fixture": fixture["id"],
        "condition": condition,
        "attempt": attempt,
        "model": "gpt-5.6-sol" if condition == "frontier" else "qwen3:8b",
        "provider": "openai-subscription" if condition == "frontier" else "ollama",
        "duration_s_including_verifier": round(duration_s, 3),
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
            row for row in runs if row["fixture"] == name and row["condition"] == "frontier"
        )
        local = sorted(
            (row for row in runs if row["fixture"] == name and row["condition"] == "local"),
            key=lambda row: row["attempt"],
        )
        pair = {
            "fixture": name,
            "frontier_passed": frontier["verifier"]["passed"],
            "local_passes": sum(row["verifier"]["passed"] for row in local),
        }
        if frontier["verifier"]["passed"] and local and not local[0]["verifier"]["passed"]:
            ratio = local[0]["duration_s_including_verifier"] / frontier[
                "duration_s_including_verifier"
            ]
            pair["single_failed_multiplier"] = round(ratio, 3)
            single_ratios.append(ratio)
        if frontier["verifier"]["passed"] and len(local) == 5 and not any(
            row["verifier"]["passed"] for row in local
        ):
            ratio = sum(row["duration_s_including_verifier"] for row in local) / frontier[
                "duration_s_including_verifier"
            ]
            pair["five_failed_multiplier"] = round(ratio, 3)
            five_ratios.append(ratio)
        pairs.append(pair)

    def verdict(values):
        if len(values) < 3:
            return {"eligible_pairs": len(values), "median": None, "verdict": "insufficient_evidence"}
        median = statistics.median(values)
        return {
            "eligible_pairs": len(values),
            "median": round(median, 3),
            "verdict": "replicates_2x_trigger" if median >= 2 else "does_not_replicate_2x_trigger",
        }

    single = verdict(single_ratios)
    five = verdict(five_ratios)
    if single["verdict"] == "replicates_2x_trigger":
        interpretation = "single attempt crosses; best-of-five can only amplify it"
    elif five["verdict"] == "replicates_2x_trigger":
        interpretation = "only best-of-five crosses; reasoning-layer cost causes the trigger"
    else:
        interpretation = "no causal attribution; evidence is negative or insufficient"
    return {"pairs": pairs, "single_attempt": single, "best_of_five": five, "interpretation": interpretation}


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

    for fixture in FIXTURES:
        snapshot = read_codex_headroom()
        reason = admission_reason(snapshot, MAX_FRONTIER_USED_PERCENT)
        snapshots.append(snapshot)
        if reason:
            print(f"STOP frontier admission: {reason}", flush=True)
            break
        print(f"frontier {fixture['id']} headroom_used={snapshot['used_percent']}%", flush=True)
        runs.append(run_attempt(fixture, "frontier", 1, args.frontier_timeout))
        print(
            f"  pass={runs[-1]['verifier']['passed']} "
            f"seconds={runs[-1]['duration_s_including_verifier']}",
            flush=True,
        )

    if len([row for row in runs if row["condition"] == "frontier"]) == len(FIXTURES):
        for fixture in FIXTURES:
            for attempt in range(1, LOCAL_ATTEMPTS + 1):
                if time.monotonic() - started >= MAX_ELAPSED_S:
                    print("STOP 90-minute wall-clock cap", flush=True)
                    break
                print(f"local {fixture['id']} attempt={attempt}/5", flush=True)
                runs.append(run_attempt(fixture, "local", attempt, args.local_timeout))
                print(
                    f"  pass={runs[-1]['verifier']['passed']} "
                    f"seconds={runs[-1]['duration_s_including_verifier']}",
                    flush=True,
                )
            if time.monotonic() - started >= MAX_ELAPSED_S:
                break

    complete = len(runs) == len(FIXTURES) * (1 + LOCAL_ATTEMPTS)
    result = {
        "protocol": {
            "fixtures": [fixture["id"] for fixture in FIXTURES],
            "frontier": "gpt-5.6-sol, low reasoning, Codex Pro subscription",
            "local": "qwen3:8b via Ollama, five serial attempts",
            "maximum_frontier_used_percent": MAX_FRONTIER_USED_PERCENT,
            "attempt_cap": 30,
            "wall_clock_cap_s": MAX_ELAPSED_S,
        },
        "headroom_snapshots": snapshots,
        "complete": complete,
        "elapsed_s": round(time.monotonic() - started, 3),
        "runs": runs,
        "summary": summarise(runs) if complete else None,
    }
    RESULTS.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"result={RESULTS} complete={complete}", flush=True)
    if complete:
        print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()

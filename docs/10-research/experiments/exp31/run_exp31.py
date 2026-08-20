"""EXP-31: does substituting the installed gemma4:31b for qwen3:8b change the local verdict?

Protocol frozen in experiment-register.md § EXP-31 before this ran. The estimand is model
SUBSTITUTION in one fixed composition, not a size effect: the two models differ in family,
training data, tokeniser, instruction tuning and quantisation, and no same-family sibling
pair is installed.

Reuses EXP-07's frozen fixtures, verifier and repository setup by import. run_exp07.py is
not modified: it is frozen, and its result has been published.

Hard gate from the registration: the GPU must be free. EXP-07 timed qwen3:8b on the same
card, and a concurrent load would have corrupted the durations that were its measurement.
"""

from __future__ import annotations

import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "exp07"))

from run_exp07 import (  # noqa: E402
    FIXTURES,
    attempt_timeout,
    make_repo,
    usage_from_events,
    verify,
)

CODEX = shutil.which("codex")
RESULTS = HERE / "results-exp31.json"

MODELS = ("qwen3:8b", "gemma4:31b")
ATTEMPTS = 5
ATTEMPT_TIMEOUT_S = 240
MAX_ELAPSED_S = 3 * 60 * 60  # registration: overall cap three hours
MIN_FREE_VRAM_MIB = 2048  # registration: >= 2 GB spare
OOM_STOP = 2  # registration: OOM in two attempts of one model stops

LIMITATIONS = [
    "The estimand is substitution of one installed model for another in a fixed "
    "composition. It is NOT a size effect: family, training data, tokeniser, instruction "
    "tuning and quantisation all differ, and no same-family sibling pair is installed.",
    "Reasoning modes are not matched; each model runs at its own Ollama default, inherited "
    "from EXP-07's limitation.",
    "The frontier side is a historical control reused from EXP-07 and carries unmeasured "
    "version drift. No new frontier or metered call is made here.",
    "beta is not measured: the fixture oracle's own false-accept rate is unknown, so a pass "
    "is verifier-accepted, not correct.",
    "Five synthetic fixtures cannot generalise to real repositories.",
]


def gpu_free_mib() -> int | None:
    try:
        out = (
            subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total,memory.used",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=True,
            )
            .stdout.strip()
            .splitlines()[0]
        )
        total, used = (int(x.strip()) for x in out.split(","))
        return total - used
    except Exception:
        return None


def served_identity(model: str) -> dict:
    """Read the served model back rather than trusting the request flag (EXP-05's lesson)."""
    try:
        out = subprocess.run(
            ["ollama", "show", model],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=True,
        ).stdout
        return {"requested": model, "show": out[:400]}
    except Exception as exc:
        return {"requested": model, "error": f"{type(exc).__name__}: {exc}"}


def feasibility_probe() -> dict:
    """Not scored. Establishes VRAM headroom and load behaviour before any attempt."""
    probe = {"free_mib_before": gpu_free_mib(), "models": {}}
    for model in MODELS:
        started = time.monotonic()
        try:
            r = subprocess.run(
                ["ollama", "run", model, "Reply with the single word: ready"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
            probe["models"][model] = {
                "load_and_reply_s": round(time.monotonic() - started, 2),
                "returncode": r.returncode,
                "reply_head": (r.stdout or r.stderr)[:120].strip(),
                "free_mib_while_loaded": gpu_free_mib(),
                "identity": served_identity(model),
            }
        except Exception as exc:
            probe["models"][model] = {"error": f"{type(exc).__name__}: {exc}"}
        subprocess.run(["ollama", "stop", model], capture_output=True, timeout=120)
    probe["free_mib_after"] = gpu_free_mib()
    return probe


LOCK = RESULTS.parent / "run.lock"


def kill_tree(pid: int) -> None:
    """Kill a process and every descendant.

    `subprocess.run(timeout=...)` kills only the direct child, and with `capture_output=True`
    it then blocks in `communicate()` because the surviving grandchildren still hold the pipe
    write-ends open. That is why a 240 s cap produced a 2,011 s attempt on 20 Aug 2026 — the
    `TimeoutExpired` is not raised until the descendants finally exit. EXP-07 measured the
    same defect at 10–269 s; two concurrent runners took it to 8.4x the cap.
    """
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(pid)],
            capture_output=True,
            timeout=30,
        )
    else:
        import signal

        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


def changed_files_now(repo, baseline) -> list:
    """What the working copy holds right now, relative to the fixture baseline.

    Used after a timeout kill, where the attempt produced no verdict but may well have
    produced an edit. Reuses EXP-07's frozen `verify` where it can, and falls back to a
    direct status read so an inspection failure never silently reads as "no edit".
    """
    try:
        return list(verify(repo, baseline).get("changed_files") or [])
    except Exception:
        out = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        return [ln[3:].strip() for ln in (out.stdout or "").splitlines() if ln.strip()]


def acquire_lock(run_id: str, cap_s: int) -> bool:
    """Refuse to start alongside a live run. Returns False if another run holds the lock.

    On 20 Aug 2026 this experiment was launched twice. Each runner held its results in
    memory and rewrote the whole file per checkpoint, so they silently destroyed each
    other's progress for three hours. It was detectable only because the VRAM probe happened
    to differ between the two processes — luck, not design.
    """
    if LOCK.exists():
        try:
            held = json.loads(LOCK.read_text(encoding="utf-8"))
            age = time.time() - float(held.get("started_epoch", 0))
        except (ValueError, OSError):
            held, age = {}, cap_s + 1
        if age < cap_s:
            print(
                f"REFUSING TO START: {LOCK} is held by pid {held.get('pid')} "
                f"(run {held.get('run_id')}), started {age / 60:.1f} min ago, within the "
                f"{cap_s / 60:.0f} min wall-clock cap. Two concurrent runners overwrite each "
                "other's results. Wait, or delete the lock if that process is gone.",
                file=sys.stderr,
            )
            return False
        print(f"stale lock ({age / 60:.1f} min old, past the cap) — taking over", file=sys.stderr)
        LOCK.unlink(missing_ok=True)

    # O_CREAT|O_EXCL is atomic on Windows and POSIX alike: of two simultaneous starts,
    # exactly one creates the file. The previous version did exists / read / write, so two
    # runners starting together could both observe no lock and both write one — the same
    # incident through a narrower window. Found by an external audit of this very repair,
    # which is the second defect that audit found in the fix rather than in the original.
    payload = json.dumps(
        {"pid": os.getpid(), "run_id": run_id, "started_epoch": time.time()}, indent=1
    )
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print(
            f"REFUSING TO START: {LOCK} was created by another runner between this "
            "process's check and its write — two runners started simultaneously.",
            file=sys.stderr,
        )
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(payload)
    return True


def release_lock() -> None:
    """Release the lock only if this process holds it.

    The first version unlinked unconditionally, and it was wrong within minutes of shipping.
    A second launch correctly *refused* to start, then ran this in its `finally` and deleted
    the lock held by the live runner — leaving a three-hour run unprotected by the very
    mechanism written to protect it. Found by reading the directory, not by the tests, which
    only ever exercised release from the holder.

    A release that does not check ownership is not a release; it is a free deletion.
    """
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


def run_attempt(fixture: dict, model: str, attempt: int, timeout_s: int) -> dict:
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
        "--oss",
        "--local-provider",
        "ollama",
        "-m",
        model,
    ]
    started = time.monotonic()
    # Popen rather than run(), so the whole process tree can be killed on timeout and the
    # pipes drained afterwards. See kill_tree() for why run(timeout=) does not bound anything.
    proc = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        **({} if os.name == "nt" else {"start_new_session": True}),
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_tree(proc.pid)
        try:
            stdout, stderr = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = "", ""
    if not timed_out:
        verifier = verify(repo, baseline)
        duration = time.monotonic() - started
        usage = usage_from_events(stdout)
        rc = proc.returncode
        oom = "out of memory" in (stderr or "").lower()
        if verifier["timeout"]:
            outcome = "verifier_timeout"
        elif not verifier["scope_valid"]:
            outcome = "verifier_error"
        elif verifier["passed"]:
            outcome = "passed"
        else:
            outcome = "rejected"
    else:
        duration, rc, usage, oom = time.monotonic() - started, None, {}, False
        # The tree is dead and the working copy is still on disk, so ask it what changed
        # rather than asserting nothing did. This block used to hard-code changed_files to
        # [], and `produced_an_edit` in summarise() counts exactly that field — so every
        # censored attempt was silently recorded as "no edit" without the repository ever
        # being inspected. Edit production was censored by the same mechanism the durations
        # were, which is precisely what I had claimed it was independent of. Found by an
        # external audit of my own findings.
        try:
            changed = changed_files_now(repo, baseline)
            scope_error = "agent timed out; working copy inspected after the kill"
        except Exception as exc:  # an inspection failure must not read as "no edit"
            changed = []
            scope_error = f"agent timed out; inspection failed: {exc}"
        verifier = {
            "passed": False,
            "tests_passed": False,
            "timeout": True,
            "scope_valid": False,
            "scope_error": scope_error,
            "changed_files": changed,
            "edit_observed_after_timeout": bool(changed),
            "duration_s": 0,
            "test_tail": "agent timeout",
        }
        outcome = "agent_timeout"
    return {
        "fixture": fixture["id"],
        "model": model,
        "attempt": attempt,
        "provider": "ollama",
        "reasoning_mode": "ollama-default",
        "duration_s_including_verifier": round(duration, 3),
        # EXP-07 measured the agent timeout overrunning by 10-269 s because descendants hold
        # the pipes. Recorded here so the same inflation is visible rather than assumed away.
        "timeout_s_applied": timeout_s,
        "timeout_overrun_s": round(max(0.0, duration - timeout_s), 3),
        "censored": outcome in ("agent_timeout", "verifier_timeout"),
        "outcome": outcome,
        "return_code": rc,
        "oom_suspected": oom,
        "verifier": verifier,
        "usage": usage,
    }


def summarise(runs: list[dict]) -> dict:
    out: dict = {"per_model": {}, "paired_first_attempt": [], "verdicts": {}}
    for model in MODELS:
        rows = [r for r in runs if r["model"] == model]
        first = [r for r in rows if r["attempt"] == 1]
        out["per_model"][model] = {
            "attempts": len(rows),
            "passes": sum(r["verifier"]["passed"] for r in rows),
            "first_attempt_passes": sum(r["verifier"]["passed"] for r in first),
            "censored": sum(bool(r["censored"]) for r in rows),
            "produced_an_edit": sum(bool(r["verifier"]["changed_files"]) for r in rows),
            "tests_pass_scope_fail": sum(
                1
                for r in rows
                if r["verifier"].get("tests_passed") and not r["verifier"]["passed"]
            ),
            "median_first_attempt_s": (
                statistics.median(r["duration_s_including_verifier"] for r in first)
                if first
                else None
            ),
        }

    ratios = []
    for fx in FIXTURES:
        a = next(
            (
                r
                for r in runs
                if r["fixture"] == fx["id"]
                and r["model"] == MODELS[0]
                and r["attempt"] == 1
            ),
            None,
        )
        b = next(
            (
                r
                for r in runs
                if r["fixture"] == fx["id"]
                and r["model"] == MODELS[1]
                and r["attempt"] == 1
            ),
            None,
        )
        if not a or not b:
            continue
        ratio = b["duration_s_including_verifier"] / a["duration_s_including_verifier"]
        censored = bool(a["censored"] or b["censored"])
        ratios.append((ratio, censored))
        out["paired_first_attempt"].append(
            {
                "fixture": fx["id"],
                "ratio_gemma_over_qwen": round(ratio, 3),
                "is_lower_bound": censored,
                "qwen_passed": a["verifier"]["passed"],
                "gemma_passed": b["verifier"]["passed"],
            }
        )

    # Registration: a pass-rate difference is claimed only at 5-0 or 4-1 in matched pairs.
    q = out["per_model"][MODELS[0]]["first_attempt_passes"]
    g = out["per_model"][MODELS[1]]["first_attempt_passes"]
    diff = abs(g - q)
    out["verdicts"]["pass_rate"] = (
        "difference_claimed" if diff >= 4 else "insufficient_evidence"
    )
    out["verdicts"]["pass_rate_detail"] = f"qwen {q}/5 vs gemma {g}/5"

    if ratios:
        signs = {r > 1 for r, _ in ratios}
        median = statistics.median(r for r, _ in ratios)
        out["verdicts"]["latency"] = (
            "materially_slower"
            if median >= 1.5 and len(signs) == 1
            else "insufficient_evidence"
        )
        out["verdicts"]["latency_detail"] = {
            "median_ratio": round(median, 3),
            "all_same_sign": len(signs) == 1,
            "censored_pairs": sum(1 for _, c in ratios if c),
        }
    return out


def main() -> int:
    if CODEX is None:
        print("codex not found", file=sys.stderr)
        return 2

    run_id = f"exp31-{time.strftime('%Y%m%dT%H%M%S')}-{os.getpid()}"
    if not acquire_lock(run_id, MAX_ELAPSED_S):
        return 3

    free = gpu_free_mib()
    print(f"GPU free before probe: {free} MiB")
    probe = feasibility_probe()
    print(json.dumps(probe, indent=1)[:1200])

    worst = (
        min(
            (m.get("free_mib_while_loaded") or 0)
            for m in probe["models"].values()
            if "error" not in m
        )
        if probe["models"]
        else 0
    )
    if worst < MIN_FREE_VRAM_MIB:
        payload = {
            "complete": False,
            "stop_reason": "infeasible_vram",
            "probe": probe,
            "limitations": LIMITATIONS,
            "runs": [],
        }
        payload["run_id"] = run_id
        RESULTS.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        print(f"INFEASIBLE: only {worst} MiB spare while loaded")
        return 1

    started = time.monotonic()
    runs: list[dict] = []
    stop_reason = None
    oom = {m: 0 for m in MODELS}

    # Counterbalanced order fixed before the run: alternate which model goes first per fixture.
    for index, fixture in enumerate(FIXTURES):
        order = MODELS if index % 2 == 0 else tuple(reversed(MODELS))
        for model in order:
            for attempt in range(1, ATTEMPTS + 1):
                remaining = MAX_ELAPSED_S - (time.monotonic() - started)
                budget = attempt_timeout(remaining, ATTEMPT_TIMEOUT_S)
                if budget is None:
                    stop_reason = "wall_clock_cap"
                    break
                row = run_attempt(fixture, model, attempt, budget)
                runs.append(row)
                if row["oom_suspected"]:
                    oom[model] += 1
                print(
                    f"  {fixture['id']:<20} {model:<12} att{attempt} "
                    f"{row['outcome']:<14} {row['duration_s_including_verifier']:7.1f}s "
                    f"edit={bool(row['verifier']['changed_files'])}",
                    flush=True,
                )
                RESULTS.write_text(
                    json.dumps(
                        {
                            # run_id on every checkpoint, not only on the final payload.
                            # The first version stamped it at the end, which is precisely when
                            # an interleaving is too late to see: the 20 Aug incident was only
                            # detectable because a VRAM probe happened to differ.
                            "run_id": run_id,
                            "complete": False,
                            "stop_reason": None,
                            "probe": probe,
                            "limitations": LIMITATIONS,
                            "runs": runs,
                        },
                        indent=1,
                    ),
                    encoding="utf-8",
                )
                if oom[model] >= OOM_STOP:
                    stop_reason = f"oom_{model}"
                    break
            if stop_reason:
                break
        if stop_reason:
            break
        subprocess.run(["ollama", "stop", MODELS[0]], capture_output=True, timeout=120)
        subprocess.run(["ollama", "stop", MODELS[1]], capture_output=True, timeout=120)

    payload = {
        "protocol": {
            "models": list(MODELS),
            "attempts_per_cell": ATTEMPTS,
            "attempt_timeout_s": ATTEMPT_TIMEOUT_S,
            "wall_clock_cap_s": MAX_ELAPSED_S,
            "fixtures": [f["id"] for f in FIXTURES],
            "estimand": "model substitution in a fixed composition, NOT a size effect",
        },
        "limitations": LIMITATIONS,
        "probe": probe,
        "complete": stop_reason is None,
        "stop_reason": stop_reason,
        "elapsed_s": round(time.monotonic() - started, 3),
        "runs": runs,
        "summary": summarise(runs),
    }
    payload["run_id"] = run_id
    RESULTS.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=1))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        release_lock()

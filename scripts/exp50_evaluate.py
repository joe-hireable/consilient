"""EXP-50 evaluation: does the composite verifier accept this injected fault?

One candidate at a time, in an isolated copy of the tree, against the same three checks EXP-47
used -- `pytest`, `mypy --strict`, `ruff check`. A candidate the verifier ACCEPTS is a survivor,
and survivors over adjudicated real defects are beta.

THE DEFECT THIS EXISTS NOT TO REPEAT. `docs/10-research/experiments/exp47/run_exp47.py` runs the
full suite per mutant under `timeout=20` and scores the timeout as `pytest_pass = False`, which
the composite reads as the mutant having been KILLED. That was sound in August when the suite
held 96 tests and ran in about a second. It is not sound now: the suite holds 2,169 tests and
takes about 180 s, so every mutant would time out, every mutant would be recorded killed, and the
harness would report a false-accept rate near ZERO with a Wilson interval and no error at all.

A false accept inside the false-accept meter is the exact failure this project exists to measure,
so two rules follow and both are enforced below:

  * The timeout is DERIVED from a measured clean run, not guessed, and carries generous headroom.
  * A timeout is its own outcome. It is never folded into pass or fail. A candidate whose checks
    did not finish is `inconclusive` and is excluded from the denominator with its count
    reported, exactly as an equivalent mutant is.

MEASURED PIN. The batch manifest records `src_consilient_sha256`. If the tree has moved since the
candidates were generated, the diffs describe a file that no longer exists in that form, and the
run is refused rather than producing a number about two different trees.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# scripts/ is not a package; this makes the sibling importable under both a direct run and
# an importlib load. See scripts/split_module.py for the measurement behind this pattern.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# The PIN COMES FROM THE GENERATOR, never from a second implementation here. A digest
# computed two ways is two digests: the first version of this file hashed the same tree by a
# slightly different rule and the pin check refused its own smoke batch. A tree hash is
# exactly the kind of thing that must have one definition.
from exp50_faults import tree_sha256  # noqa: E402

PRODUCT = "src/consilient"
CHECKS = ("pytest", "mypy", "ruff")
# Multiple of a measured clean run. Three is not a guess about this machine; it is the smallest
# factor that survives the load a parallel dispatch puts on it, and the run records what it used.
TIMEOUT_FACTOR = 3.0
MIN_TIMEOUT_S = 60.0


def _run(argv: list[str], cwd: Path, timeout: float) -> tuple[bool, bool]:
    """(passed, timed_out). A timeout is NEVER reported as a pass or a fail."""
    try:
        done = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return (False, True)
    return (done.returncode == 0, False)


def measure_clean(where: Path) -> tuple[dict[str, float], dict[str, bool]]:
    """Time each check on the unmodified tree, and record whether it PASSED.

    The timing derives the timeout. The pass/fail is the control: an instrument whose control
    fails has not measured anything, however confident its output looks.
    """
    timings: dict[str, float] = {}
    passed: dict[str, bool] = {}
    for name, argv in _commands().items():
        start = time.perf_counter()
        ok, _ = _run(argv, where, timeout=3600)
        timings[name] = time.perf_counter() - start
        passed[name] = ok
    return timings, passed


def _commands() -> dict[str, list[str]]:
    return {
        "pytest": [sys.executable, "-m", "pytest", "tests", "-q", "-x"],
        "mypy": [sys.executable, "-m", "mypy", "--strict", PRODUCT],
        "ruff": [sys.executable, "-m", "ruff", "check", PRODUCT],
    }


def tree_is_clean() -> bool:
    """No uncommitted change under the product tree."""
    done = subprocess.run(
        ["git", "status", "--porcelain", "--", PRODUCT],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return not done.stdout.strip()


def restore_tree() -> None:
    """Put the product tree back exactly as HEAD has it."""
    subprocess.run(
        ["git", "checkout", "--", PRODUCT],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )


def apply_candidate(where: Path, candidate: dict[str, object]) -> str | None:
    """Apply one candidate's diff at `where`. Returns a refusal reason, or None when applied."""
    files = candidate.get("files")
    if not isinstance(files, list) or not files:
        return "candidate names no files"
    for rel in files:
        if not isinstance(rel, str) or not rel.startswith(PRODUCT + "/"):
            return f"candidate touches {rel!r}, outside {PRODUCT}/"
    diff = candidate.get("diff")
    if not isinstance(diff, str) or not diff.strip():
        return "candidate carries no diff"
    patch = where / "candidate.diff"
    patch.write_text(
        diff if diff.endswith("\n") else diff + "\n", encoding="utf-8", newline="\n"
    )
    done = subprocess.run(
        ["git", "apply", "--unsafe-paths", "--directory", ".", str(patch)],
        cwd=str(where),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if done.returncode != 0:
        return "git apply failed: " + done.stderr.strip()[:160]
    return None


def evaluate_one(
    candidate: dict[str, object], timeouts: dict[str, float]
) -> dict[str, object]:
    """Apply one candidate IN PLACE, run the three checks, and always put the tree back.

    In place, not in a copy, because the composite verifier depends on the whole repository AND
    on untracked instance state. Four copy-based workers were built on 28 August 2026 and every
    one failed its own control -- a hand-picked subset, a `git archive`, an archive plus a fresh
    `git init`, and a full local clone -- each because the suite needed something the copy did
    not have: a checker loaded by path, `git ls-files`, repository history, and finally
    `.harness/knowledge/sources.json`, which is untracked by design.

    Guessing what the verifier needs is the failure mode. Running it where it actually runs
    removes the guess. The cost is that this is serial and destructive-in-the-moment, so the
    tree is restored in a finally block and the restoration is VERIFIED rather than assumed --
    an unrestored tree would silently contaminate every candidate after it.
    """
    if not tree_is_clean():
        return {
            "outcome": "unapplied",
            "reason": "product tree was dirty before applying",
        }
    try:
        refusal = apply_candidate(ROOT, candidate)
        if refusal is not None:
            return {"outcome": "unapplied", "reason": refusal}

        results: dict[str, object] = {}
        timed_out = False
        for name, argv in _commands().items():
            passed, expired = _run(argv, ROOT, timeout=timeouts[name])
            results[name + "_pass"] = passed
            results[name + "_timeout"] = expired
            timed_out = timed_out or expired

        if timed_out:
            # Never folded into pass or fail. This is the EXP-47 defect, refused.
            results["outcome"] = "inconclusive"
        else:
            accepted = all(bool(results[n + "_pass"]) for n in CHECKS)
            results["outcome"] = "accepted" if accepted else "rejected"
        return results
    finally:
        restore_tree()
        (ROOT / "candidate.diff").unlink(missing_ok=True)
        if not tree_is_clean():
            raise RuntimeError(
                "the product tree did not restore after a candidate; every later candidate "
                "would be measured against contaminated source. Stopping."
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch", required=True, help="directory holding candidates.jsonl"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="evaluate at most N candidates"
    )
    args = parser.parse_args(argv)

    batch = Path(args.batch)
    manifest = json.loads((batch / "manifest.json").read_text(encoding="utf-8"))
    pinned = manifest.get("src_consilient_sha256")
    actual = tree_sha256(ROOT / PRODUCT)
    if pinned != actual:
        print(
            json.dumps(
                {
                    "refused": "tree moved since generation",
                    "pinned": pinned,
                    "actual": actual,
                    "why": (
                        "the candidates describe a tree that is no longer on disk; evaluating "
                        "them would measure two different trees at once"
                    ),
                }
            )
        )
        return 1

    candidates = [
        json.loads(line)
        for line in (batch / "candidates.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    if args.limit:
        candidates = candidates[: args.limit]

    if not tree_is_clean():
        print(
            json.dumps(
                {
                    "refused": "the product tree has uncommitted changes",
                    "why": (
                        "candidates are applied in place and reverted with `git checkout`; an "
                        "already-dirty tree would be destroyed by that revert"
                    ),
                }
            )
        )
        return 1
    clean, clean_pass = measure_clean(ROOT)
    timeouts = {
        name: max(MIN_TIMEOUT_S, seconds * TIMEOUT_FACTOR)
        for name, seconds in clean.items()
    }

    # THE GUARD THAT MAKES A BROKEN HARNESS LOUD. If the composite verifier does not pass on the
    # UNMODIFIED tree, then every candidate will be scored `rejected` whatever it contains, and
    # beta comes out at zero -- a confident, specific, wrong number. That is precisely how this
    # file's own first version behaved, and how run_exp47.py behaves today. An instrument that
    # cannot pass its own control has not measured anything.
    if not all(clean_pass.values()):
        broken = sorted(name for name, ok in clean_pass.items() if not ok)
        print(
            json.dumps(
                {
                    "refused": "the composite verifier fails on the unmodified tree",
                    "failing": broken,
                    "clean_seconds": {k: round(v, 2) for k, v in clean.items()},
                    "why": (
                        "every candidate would score `rejected` regardless of its content and "
                        "beta would come out at zero; fix the harness before measuring"
                    ),
                }
            )
        )
        return 1

    rows: list[dict[str, object]] = []
    for index, candidate in enumerate(candidates, 1):
        row = evaluate_one(candidate, timeouts)
        row["index"] = index
        row["invariant"] = candidate.get("invariant")
        rows.append(row)
        print(json.dumps({"i": index, "outcome": row["outcome"]}), flush=True)

    counts: dict[str, int] = {}
    for row in rows:
        key = str(row["outcome"])
        counts[key] = counts.get(key, 0) + 1
    out = {
        "batch": str(batch),
        "arm": manifest.get("arm"),
        "family": manifest.get("family"),
        "src_consilient_sha256": actual,
        "clean_seconds": {k: round(v, 2) for k, v in clean.items()},
        "clean_pass": clean_pass,
        "timeouts_s": {k: round(v, 1) for k, v in timeouts.items()},
        "counts": counts,
        "note": (
            "`accepted` means the composite verifier did not catch the fault -- the beta "
            "numerator, before adjudication removes no-ops. `inconclusive` is a check that did "
            "not finish and is excluded from the denominator, never scored as caught."
        ),
        "rows": rows,
    }
    (batch / "evaluation.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"counts": counts, "wrote": str(batch / "evaluation.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

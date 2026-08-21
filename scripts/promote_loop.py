"""Execute a self-modification candidate and ask the native promoter.

Disabled by default. `--enable` turns the policy on; `--apply` would write the
candidate, and is refused unless the promoter returns promote. Today live β is
unmeasured, so promote never happens and apply never runs. That is the point.

    python scripts/promote_loop.py --source candidate.py --baseline baseline.py

No seventh `consil` command. No metered call. Does not import EXP-96's in-flight runner.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient import beta as beta_mod  # noqa: E402
from consilient.promote import (  # noqa: E402
    Candidate,
    ExecutionEvidence,
    decide,
    digest,
    record,
)

VERIFIER_VERSION = "exp78-training-v1"


def execute(source: str, cases: Sequence[tuple[str, str]]) -> tuple[bool, float]:
    """Run the candidate. This is the execution boundary; reflection is not one."""
    namespace: dict[str, object] = {}
    try:
        compiled = compile(source, "<candidate>", "exec")
        exec(compiled, namespace)  # noqa: S102 — fixture execution, not product code
        solve = namespace.get("solve")
        if not callable(solve):
            return False, 0.0
    except (SyntaxError, TypeError, ValueError):
        return False, 0.0
    if not cases:
        return True, 0.0
    hits = 0
    for prompt, expected in cases:
        try:
            if str(solve(prompt)) == expected:
                hits += 1
        except (TypeError, ValueError, ArithmeticError):
            continue
    return True, hits / len(cases)


def load_cases(path: Path) -> list[tuple[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [(str(row["prompt"]), str(row["expected"])) for row in payload]


def live_beta(log_dir: Path) -> beta_mod.Beta:
    return beta_mod.compute([])


def _cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Native promoter loop (disabled).")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--path", default=".agents/skills/exp78/SKILL.md")
    parser.add_argument("--id", default="candidate")
    parser.add_argument("--log", type=Path, default=ROOT / ".harness" / "log")
    parser.add_argument(
        "--enable",
        action="store_true",
        default=False,
        help="opt in to the promoter; default is refuse (V0-44)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="write the candidate; refused unless the promoter returns promote",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    source = args.source.read_text(encoding="utf-8")
    baseline = args.baseline.read_text(encoding="utf-8")
    cases = load_cases(args.tasks)
    ran_before, metric_before = execute(baseline, cases)
    ran_after, metric_after = execute(source, cases)
    evidence = ExecutionEvidence(
        ran=ran_before and ran_after,
        suite_passed=ran_after,
        metric_before=metric_before,
        metric_after=metric_after,
        verifier_version=VERIFIER_VERSION,
    )
    candidate = Candidate(
        identity=args.id,
        path=args.path,
        preimage_sha256=digest(baseline),
        postimage_sha256=digest(source),
        evidence=evidence,
    )
    measured = live_beta(args.log)
    decision = decide(candidate, measured, enabled=args.enable)
    recorded = record(args.log, decision)
    # Apply is a second lock. It is never taken while promoter β is unmeasured;
    # a write here would be a mutation, not a promotion (V0-43).
    applied = False
    apply_refused = bool(args.apply)
    print(
        json.dumps(
            {
                "action": decision.action,
                "reason": decision.reason,
                "enabled": decision.enabled,
                "applied": applied,
                "apply_refused": apply_refused,
                "metric_before": metric_before,
                "metric_after": metric_after,
                "event": recorded["event"],
            },
            sort_keys=True,
        )
    )
    return 0 if decision.action == "promote" else 2


if __name__ == "__main__":
    raise SystemExit(_cli())

"""Execute a self-modification candidate and ask the native promoter.

Disabled by default. `--enable` turns the policy on; `--apply` would write the
candidate, and is refused unless the promoter returns promote. Today live β is
unmeasured, so promote never happens and apply never runs. That is the point.

    python scripts/promote_loop.py --source candidate.py --baseline baseline.py

Sealed offline evaluation (S02) never commits, installs or swaps a pointer:

    python scripts/promote_loop.py --evaluate-only --sealed-manifest manifest.json \\
        --source candidate.py --baseline baseline.py --scratch-dir /tmp/scratch

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
    AdverseTable,
    Candidate,
    EvaluationRefusal,
    ExecutionEvidence,
    LineageRegistry,
    SealedManifest,
    candidate_visible,
    decide,
    digest,
    evaluate_sealed,
    record,
    record_evaluation,
    reserve_qualification_batch,
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


def scratch_digest(scratch_dir: Path) -> str:
    marker = scratch_dir / "state.txt"
    return digest(marker.read_text(encoding="utf-8"))


def scratch_forward(scratch_dir: Path, candidate_source: str) -> None:
    marker = scratch_dir / "state.txt"
    marker.write_text(digest(candidate_source), encoding="utf-8")


def scratch_reverse(scratch_dir: Path, preimage: str) -> None:
    marker = scratch_dir / "state.txt"
    marker.write_text(preimage, encoding="utf-8")


def evaluate_sealed_offline(
    *,
    manifest_path: Path,
    source: Path,
    baseline: Path,
    scratch_dir: Path,
    log_dir: Path,
    contained: bool,
) -> dict[str, object]:
    manifest = SealedManifest.from_mapping(
        json.loads(manifest_path.read_text(encoding="utf-8"))
    )
    marker = scratch_dir / "state.txt"
    if not marker.exists():
        marker.write_text("parent", encoding="utf-8")
    preimage = marker.read_text(encoding="utf-8")
    preimage_digest = digest(preimage)
    candidate_source = source.read_text(encoding="utf-8")
    baseline_source = baseline.read_text(encoding="utf-8")
    scratch_forward(scratch_dir, candidate_source)
    post_forward_digest = scratch_digest(scratch_dir)
    scratch_reverse(scratch_dir, preimage)
    post_reverse_digest = scratch_digest(scratch_dir)
    registry = LineageRegistry()
    result = evaluate_sealed(
        manifest,
        candidate_source=candidate_source,
        baseline_source=baseline_source,
        execute=execute,
        registry=registry,
        adverse=AdverseTable(0, 0, 0, 0, 0),
        contained=contained,
        scratch_preimage_digest=preimage_digest,
        scratch_postimage_digest=post_reverse_digest,
    )
    if isinstance(result, EvaluationRefusal):
        return {
            "action": "refused",
            "reason": result.reason,
            "detail": result.detail,
            "applied": False,
            "activated": False,
            "reversal_match": post_reverse_digest == preimage_digest,
            "scratch_forward_digest": post_forward_digest,
        }
    recorded = record_evaluation(log_dir, result)
    registry = reserve_qualification_batch(
        registry, manifest.lineage_id, manifest.qualification_batch_id
    )
    visible = candidate_visible(result)
    return {
        "action": "evaluated",
        "reason": "evaluated",
        **visible,
        "applied": False,
        "activated": False,
        "reversal_match": result.reversal_match,
        "event": recorded["event"],
        "scratch_forward_digest": post_forward_digest,
    }


def _cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Native promoter loop (disabled).")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--tasks", type=Path)
    parser.add_argument("--path", default=".agents/skills/exp78/SKILL.md")
    parser.add_argument("--id", default="candidate")
    parser.add_argument("--log", type=Path, default=ROOT / ".harness" / "log")
    parser.add_argument("--sealed-manifest", type=Path)
    parser.add_argument("--scratch-dir", type=Path)
    parser.add_argument(
        "--evaluate-only",
        action="store_true",
        default=False,
        help="run sealed offline evaluation without commit, install or pointer swap",
    )
    parser.add_argument(
        "--contained",
        action="store_true",
        default=True,
        help="fixture containment is assumed for offline evaluation",
    )
    parser.add_argument(
        "--uncontained",
        action="store_true",
        default=False,
        help="record candidate_unexecutable for non-fixture candidates",
    )
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

    if args.evaluate_only:
        if args.sealed_manifest is None or args.scratch_dir is None:
            parser.error("--evaluate-only requires --sealed-manifest and --scratch-dir")
        payload = evaluate_sealed_offline(
            manifest_path=args.sealed_manifest,
            source=args.source,
            baseline=args.baseline,
            scratch_dir=args.scratch_dir,
            log_dir=args.log,
            contained=not args.uncontained,
        )
        print(json.dumps(payload, sort_keys=True))
        return 0 if payload["action"] == "evaluated" else 2

    if args.tasks is None:
        parser.error("--tasks is required unless --evaluate-only is set")

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

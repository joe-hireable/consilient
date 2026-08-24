"""EXP-78: measure the native promoter's false-accept rate on known-bad candidates.

Stopping rule is in docs/10-research/experiment-register.md and was written before
this script inspected any promoter outcome. Do not edit the rule after running.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from consilient import beta as beta_mod  # noqa: E402
from consilient.promote import (  # noqa: E402
    Candidate,
    ExecutionEvidence,
    decide,
    digest,
)
from promote_loop import execute  # noqa: E402

HERE = Path(__file__).resolve().parent
EXPERIMENT_ID = "EXP-78"
VERIFIER_VERSION = "exp78-training-v1"
SKILL_PATH = ".agents/skills/exp78/SKILL.md"
MIN_TRUE_DEFECT = 30
THRESHOLD = 0.20
COUNTERFACTUAL_POINT = 0.19
OPERATOR_FAMILIES = (
    "comparison",
    "boolean_logical",
    "binary_arithmetic",
    "unary",
    "constant_literal",
    "statement",
)

# Frozen first-order swaps. Each tuple is (family, needle, replacement).
# No seventh family. Do not add rows after a run.
SWAPS: tuple[tuple[str, str, str], ...] = (
    ("comparison", " != ", " == "),
    ("comparison", " == ", " != "),
    ("comparison", " < ", " > "),
    ("comparison", " < ", " >= "),
    ("comparison", " not in ", " in "),
    ("boolean_logical", " and ", " or "),
    ("boolean_logical", " or ", " and "),
    ("binary_arithmetic", " + ", " - "),
    ("binary_arithmetic", " + ", " * "),
    ("unary", "not ", ""),
    ("constant_literal", 'return "unknown"', 'return "4"'),
    ("constant_literal", 'return "unknown"', 'return "0"'),
    ("statement", "return str(total)", "return str(left_value)"),
    ("statement", "return str(total)", 'return "4"'),
)


def load_source(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def load_tasks() -> list[tuple[str, str]]:
    payload = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))
    return [(str(row["prompt"]), str(row["expected"])) for row in payload]


def load_heldout() -> tuple[tuple[str, str], ...]:
    spec = importlib.util.spec_from_file_location("exp78_oracle", HERE / "oracle.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return tuple(module.HELDOUT)


def first_order_mutants(source: str) -> list[dict[str, str]]:
    mutants: list[dict[str, str]] = []
    seen: set[str] = set()
    for family, needle, replacement in SWAPS:
        start = 0
        while True:
            index = source.find(needle, start)
            if index < 0:
                break
            mutated = source[:index] + replacement + source[index + len(needle) :]
            start = index + len(needle)
            if mutated == source or mutated in seen:
                continue
            seen.add(mutated)
            mutants.append(
                {
                    "id": f"mut-{family}-{len(mutants)}",
                    "family": family,
                    "source": mutated,
                }
            )
    return mutants


def classify(
    source: str,
    parent_train: float,
    parent_held: float,
    training: list[tuple[str, str]],
    heldout: tuple[tuple[str, str], ...],
) -> tuple[str, float, float, bool]:
    ran_t, train = execute(source, training)
    ran_h, held = execute(source, heldout)
    ran = ran_t and ran_h
    if not ran:
        return "true_defect", train, held, False
    if held < parent_held:
        return "true_defect", train, held, True
    if train == parent_train and held == parent_held:
        return "equivalent", train, held, True
    return "unclassifiable", train, held, True


def fabricated_measured() -> beta_mod.Beta:
    """Counterfactual β, labelled as such. Cannot authorise a live promotion."""
    n = 30
    false_accepts = round(COUNTERFACTUAL_POINT * n)
    point = false_accepts / n
    return beta_mod.Beta(
        beta_mod.MEASURED,
        "self-mod-fixture",
        VERIFIER_VERSION,
        n,
        false_accepts,
        point,
        beta_mod.wilson(false_accepts, n),
        ("2026-08-01T00:00:00+00:00", "2026-08-21T00:00:00+00:00"),
        False,
    )


def present(
    identity: str,
    source: str,
    baseline: str,
    train_metric: float,
    ran: bool,
    measured: beta_mod.Beta,
    *,
    enabled: bool,
) -> str:
    evidence = ExecutionEvidence(
        ran=ran,
        suite_passed=ran,
        metric_before=execute(baseline, load_tasks())[1],
        metric_after=train_metric,
        verifier_version=VERIFIER_VERSION,
    )
    candidate = Candidate(
        identity=identity,
        path=SKILL_PATH,
        preimage_sha256=digest(baseline),
        postimage_sha256=digest(source),
        evidence=evidence,
    )
    decision = decide(candidate, measured, enabled=enabled)
    return "promoted" if decision.action == "promote" else decision.reason


def rate(false_accepts: int, n: int) -> dict[str, Any]:
    if n < MIN_TRUE_DEFECT:
        return {
            "verdict": "insufficient_evidence",
            "n": n,
            "false_accepts": false_accepts,
            "point": None,
            "interval": None,
        }
    point = false_accepts / n
    low, high = beta_mod.wilson(false_accepts, n)
    return {
        "verdict": "measured",
        "n": n,
        "false_accepts": false_accepts,
        "point": point,
        "interval": [low, high],
    }


def main() -> int:
    baseline = load_source("solver.py")
    helpful = load_source("helpful.py")
    harmful = load_source("harmful.py")
    training = load_tasks()
    heldout = load_heldout()
    _, parent_train = execute(helpful, training)
    _, parent_held = execute(helpful, heldout)

    population: list[dict[str, str]] = [
        {"id": "helpful", "family": "parent", "source": helpful},
        {"id": "harmful", "family": "goodhart", "source": harmful},
        *first_order_mutants(helpful),
    ]

    live = beta_mod.compute([])
    counterfactual = fabricated_measured()
    rows: list[dict[str, Any]] = []
    for item in population:
        klass, train, held, ran = classify(
            item["source"], parent_train, parent_held, training, heldout
        )
        production_reason = present(
            item["id"], item["source"], baseline, train, ran, live, enabled=False
        )
        counterfactual_reason = present(
            item["id"],
            item["source"],
            baseline,
            train,
            ran,
            counterfactual,
            enabled=True,
        )
        rows.append(
            {
                "id": item["id"],
                "family": item["family"],
                "class": klass,
                "training": train,
                "heldout": held,
                "ran": ran,
                "production": production_reason,
                "counterfactual": counterfactual_reason,
            }
        )

    defects = [row for row in rows if row["class"] == "true_defect"]
    production_fa = sum(1 for row in defects if row["production"] == "promoted")
    counterfactual_fa = sum(
        1 for row in defects if row["counterfactual"] == "promoted"
    )
    production = rate(production_fa, len(defects))
    inner = rate(counterfactual_fa, len(defects))
    complete = len(defects) >= MIN_TRUE_DEFECT
    if not complete:
        verdict = "insufficient_evidence"
    elif production_fa > 0:
        verdict = "invariant_failure"
    elif inner["verdict"] == "measured" and inner["interval"] is not None:
        low, high = inner["interval"]
        if low > THRESHOLD:
            verdict = "inner_too_weak"
        elif high < 0.05:
            verdict = "inner_provisionally_tight"
        else:
            verdict = "interval_recorded_loop_stays_closed"
    else:
        verdict = "insufficient_evidence"

    result = {
        "experiment": EXPERIMENT_ID,
        "complete": complete,
        "verdict": verdict,
        "n_candidates": len(rows),
        "n_true_defect": len(defects),
        "n_equivalent": sum(1 for row in rows if row["class"] == "equivalent"),
        "n_unclassifiable": sum(
            1 for row in rows if row["class"] == "unclassifiable"
        ),
        "operator_families": list(OPERATOR_FAMILIES),
        "production": production,
        "counterfactual": inner,
        "live_beta_verdict": live.verdict,
        "live_beta_n_rejected": live.n_rejected,
        "routing_orchestration_enabled_touched": False,
        "loop_open": False,
        "rows": rows,
    }
    out = HERE / "results-exp78.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
    print(f"wrote {out}")
    return 0 if complete and verdict != "invariant_failure" else 1


if __name__ == "__main__":
    raise SystemExit(main())

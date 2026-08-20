"""Determinism control for EXP-49: do two independent censuses agree mutant-for-mutant?

The census is executed by 24 concurrent workers against instruments that spawn subprocesses,
acquire locks and probe hardware. None of that is obviously deterministic, and a mutation
result that varies between runs is not a measurement.

Run 1 completed five of six targets; run 2 aborted after two (see findings-exp49.md, §5).
This compares the overlap, which is every mutant run 2 reached.

    python docs/10-research/experiments/exp49/compare_runs.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
RUN1 = HERE / "results-exp49.json"
RUN2 = HERE / "results-exp49-rerun-control.json"


def outcomes(path: Path) -> dict[str, str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return {mutant["id"]: mutant["outcome"] for mutant in document["mutants"]}


def main() -> int:
    first, second = outcomes(RUN1), outcomes(RUN2)
    shared = set(first) & set(second)
    disagreements = sorted(k for k in shared if first[k] != second[k])

    print(
        f"run 1: {len(first)} mutants   run 2: {len(second)}   overlap: {len(shared)}"
    )
    print(f"outcome disagreements across the overlap: {len(disagreements)}")
    for mutant_id in disagreements[:20]:
        print(f"  {mutant_id}: run1={first[mutant_id]} run2={second[mutant_id]}")

    return 1 if disagreements else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Determinism control for EXP-57: do two independent passes agree item-for-item?

Nothing about a sampled language model is deterministic, and the experiment compares
four arms whose differences may be a few percentage points wide. If the same item in
the same arm gets a different verdict on a second pass, the between-arm differences
cannot be read as anything, and *that* is the finding.

Run the control first, then this:

    python docs/10-research/experiments/exp57/run_exp57.py --control
    python docs/10-research/experiments/exp57/compare_runs.py

Exit status 1 on any disagreement, so a pipeline cannot mistake noise for agreement.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

HERE = Path(__file__).resolve().parent
RUN1 = HERE / "results-exp57.json"
RUN2 = HERE / "results-exp57-rerun-control.json"


def verdicts(path: Path) -> dict[tuple[str, str], str | None]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return {(r["arm"], r["item_id"]): r["verdict"] for r in document["records"]}


def main() -> int:
    first, second = verdicts(RUN1), verdicts(RUN2)
    shared = sorted(set(first) & set(second))
    disagreements = [key for key in shared if first[key] != second[key]]

    print(f"run 1: {len(first)} calls   run 2: {len(second)}   overlap: {len(shared)}")
    print(f"verdict disagreements across the overlap: {len(disagreements)}")
    if shared:
        print(f"agreement: {1 - len(disagreements) / len(shared):.4f}")
    by_arm = Counter(arm for arm, _ in disagreements)
    for arm, count in sorted(by_arm.items()):
        total = sum(1 for a, _ in shared if a == arm)
        print(f"  {arm}: {count}/{total} disagree")
    for key in disagreements[:20]:
        print(f"  {key[0]}/{key[1]}: run1={first[key]} run2={second[key]}")

    return 1 if disagreements else 0


if __name__ == "__main__":
    raise SystemExit(main())

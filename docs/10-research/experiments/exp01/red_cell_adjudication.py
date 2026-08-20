"""Is a "red" rollup a rejection? Mechanically, for a fifth of the cell, no.

`mine_beta.py` derives `_ci` from `statusCheckRollup` and calls anything not in
{SUCCESS, NEUTRAL, SKIPPED, None} "red". That set omits **CANCELLED**, so a run that was
superseded, aborted or cancelled counts as though the verifier had rejected the artefact.

It did not. A cancelled check produced no verdict at all. Treating it as a rejection puts a
PR in the denominator of a rate about verifier decisions when no decision was taken -- the
same error as counting a PR with no checks at all, which `mine_beta.py` was careful to
exclude via `_ci == "none"`.

This script re-derives alpha and beta with cancelled-only failures moved OUT of "red" and
into "no verdict", and reports both readings side by side. It does NOT amend `mine_beta.py`
or its recorded outputs -- EXP-01 is under a live audit and its results must not be
retrofitted. It reads a gitignored evidence file gathered separately and prints aggregates
only, per the privacy rule. Check names are private-corpus content and are never printed:
only counts, and a coarse class per check.

Run: python red_cell_adjudication.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATA = Path(
    r"C:\Users\jpbpr\Repositories\consilience\docs\10-research\experiments\exp01\data"
)

# The cells `mine_beta.py` measured, from `two_by_two.py`, jobboard-v2.
BAD_GREEN, BAD_RED = 128, 75
GOOD_GREEN, GOOD_RED = 74, 23

NO_VERDICT = {"CANCELLED", "SKIPPED", "STALE", "TIMED_OUT", None}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * ((ph * (1 - ph) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def show(label: str, k: int, n: int) -> None:
    lo, hi = wilson(k, n)
    print(f"  {label:34} {k:>3}/{n:<4} = {k / n:.4f}  Wilson95 [{lo:.4f}, {hi:.4f}]")


def main() -> None:
    records = json.loads((DATA / "red-cells-evidence.json").read_text(encoding="utf-8"))

    counts = {}
    for cell in ("bad-and-red", "good-and-red"):
        rows = [r for r in records if r["cell"] == cell]
        cancelled_only = 0
        informational_only = 0
        for r in rows:
            failing = [
                c
                for c in r["checks"]
                if c["conclusion"] not in ("SUCCESS", "NEUTRAL", "SKIPPED", None)
            ]
            if failing and all(c["conclusion"] in NO_VERDICT for c in failing):
                cancelled_only += 1
            elif failing and all("informational" in c["name"].lower() for c in failing):
                informational_only += 1
        counts[cell] = (len(rows), cancelled_only, informational_only)
        print(
            f"{cell:14} n={len(rows):<4} cancelled-only={cancelled_only:<4} "
            f"informational-only={informational_only}"
        )

    bad_cancel = counts["bad-and-red"][1]
    good_cancel = counts["good-and-red"][1]

    print("\nAs recorded — cancelled runs counted as rejections:")
    show("beta  = P(green | bad)", BAD_GREEN, BAD_GREEN + BAD_RED)
    show("alpha = P(red | good)", GOOD_RED, GOOD_GREEN + GOOD_RED)

    print("\nCancelled runs moved out of 'red' — no verdict was taken:")
    show("beta", BAD_GREEN, BAD_GREEN + BAD_RED - bad_cancel)
    show("alpha", GOOD_RED - good_cancel, GOOD_GREEN + GOOD_RED - good_cancel)

    print(
        "\nBoth move, and in opposite directions. beta rises: the checks accepted a larger\n"
        "share of the bad artefacts they actually ruled on. alpha falls: fewer of the good\n"
        "artefacts were genuinely rejected. The optimistic reading of the verifier gets worse\n"
        "and its flakiness gets better, from one corrected classification.\n"
        "\n"
        "This is mechanical, not adjudicated. It settles only the cancelled runs. Whether a\n"
        "FAILURE on any given suite means the artefact was bad still needs per-PR judgement,\n"
        "and one suite in this corpus is explicitly labelled informational while reporting\n"
        "FAILURE, which is a non-blocking check being counted as a rejection."
    )


if __name__ == "__main__":
    main()

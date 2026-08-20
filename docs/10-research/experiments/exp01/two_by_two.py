"""EXP-01 addendum: emit the full 2x2 so a conditional is read off a table, not a memory.

Both alpha and beta are off-diagonal cells of one contingency table over the SAME mined
records. `mine_beta.py` printed one marginal-conditioned figure and the project then argued
for a day about which conditional it was. The fix is structural: print the table.

    alpha = P(verifier rejects | artefact good) = good & red / good
    beta  = P(verifier accepts | artefact bad)  = bad  & green / bad
    (and P(bad | green), which is the transpose beta was confused with)

`_ci == "none"` means no checks were recorded: the verifier did not run, so the PR is
neither an accept nor a reject. Those rows are excluded from every conditional and the
excluded count is printed, because an unrun verifier silently counted as an accept would
bias beta downwards.

Reads the gitignored per-PR records; prints aggregates only (AGENTS.md privacy rule).

Run: python two_by_two.py <dir containing data/*-prs.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * ((ph * (1 - ph) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def rate(k: int, n: int) -> str:
    if n == 0:
        return f"{k}/{n} = undefined (no denominator)"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k / n:.4f}  Wilson95 [{lo:.4f}, {hi:.4f}]"


def table(prs: list[dict]) -> dict[str, int]:
    cells = {"bad_green": 0, "bad_red": 0, "good_green": 0, "good_red": 0, "no_ci": 0}
    for p in prs:
        ci = p["_ci"]
        if ci == "none":
            cells["no_ci"] += 1
            continue
        cells[("bad_" if p["_bad"] else "good_") + ci] += 1
    return cells


def report(name: str, prs: list[dict]) -> dict[str, object]:
    c = table(prs)
    bad = c["bad_green"] + c["bad_red"]
    good = c["good_green"] + c["good_red"]
    green = c["bad_green"] + c["good_green"]
    red = c["bad_red"] + c["good_red"]

    print(f"\n=== {name} — {len(prs)} merged PRs analysed ===")
    print(f"  {'':10}{'CI green':>12}{'CI red':>10}{'total':>10}")
    print(f"  {'bad':10}{c['bad_green']:>12}{c['bad_red']:>10}{bad:>10}")
    print(f"  {'good':10}{c['good_green']:>12}{c['good_red']:>10}{good:>10}")
    print(f"  {'total':10}{green:>12}{red:>10}{bad + good:>10}")
    print(f"  excluded, verifier never ran (_ci == none): {c['no_ci']}")
    print()
    print(f"  alpha = P(red | good)   {rate(c['good_red'], good)}")
    print(f"  beta  = P(green | bad)  {rate(c['bad_green'], bad)}")
    print(f"  transpose P(bad | green){rate(c['bad_green'], green)}")
    print(f"  base rate P(bad)        {rate(bad, bad + good)}")
    return {"repo": name, "cells": c, "bad": bad, "good": good, "green": green, "red": red}


def main(root: Path) -> None:
    files = sorted((root / "data").glob("*-prs.json"))
    if not files:
        raise SystemExit(f"no data/*-prs.json under {root}")
    for f in files:
        report(f.stem.removesuffix("-prs"), json.loads(f.read_text(encoding="utf-8")))
    print("\n  Aggregates only. Per-PR records stay gitignored (AGENTS.md privacy rule).")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))

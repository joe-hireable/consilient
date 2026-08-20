"""Is the `_bad` proxy the same instrument in every cell of the table?

`mine_beta.py` labels a merged PR bad if it was REVERTED, or if it was HOT-FIXED: a later
PR merged within 14 days whose title matches fix-ish words and whose changed files overlap.

Those are not equally strong. A revert is a direct statement that the change was wrong. A
hotfix match is circumstantial, and its false-positive rate rises with the number of files
the PR touched, because overlap gets easier the more files you have. A 100-file PR overlaps
almost any later commit.

If the two mechanisms are distributed unevenly across the table, then beta and alpha are not
being measured with one instrument — the cells carry different label noise, and a correction
audited in one cell cannot be propagated to another. That is exactly what the published
beta corrections did.

Run: python proxy_diagnostics.py <dir containing data/*-prs.json>
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def cell(p: dict) -> str:
    return ("bad" if p["_bad"] else "good") + "-and-" + p["_ci"]


def summarise(name: str, prs: list[dict]) -> None:
    print(f"\n=== {name} ===")
    cells: dict[str, list[dict]] = {}
    for p in prs:
        cells.setdefault(cell(p), []).append(p)

    print(
        f"  {'cell':18}{'n':>5}{'reverted':>10}{'hotfixed':>10}{'files: med':>12}{'mean':>8}{'max':>6}"
    )
    for key in sorted(cells):
        rows = cells[key]
        sizes = sorted(len(r["_files"]) for r in rows)
        rev = sum(1 for r in rows if r["_why"] == "reverted")
        hot = sum(1 for r in rows if r["_why"] == "hotfixed")
        print(
            f"  {key:18}{len(rows):>5}{rev:>10}{hot:>10}"
            f"{statistics.median(sizes):>12.0f}{statistics.mean(sizes):>8.1f}{sizes[-1]:>6}"
        )

    bad_red = cells.get("bad-and-red", [])
    bad_green = cells.get("bad-and-green", [])
    if bad_red and bad_green:
        mr = statistics.median(sorted(len(r["_files"]) for r in bad_red))
        mg = statistics.median(sorted(len(r["_files"]) for r in bad_green))
        print(
            f"\n  bad-and-red median size {mr:.0f} files vs bad-and-green {mg:.0f}."
            f"  ratio {mr / mg:.2f}"
            if mg
            else ""
        )
        rev_red = sum(1 for r in bad_red if r["_why"] == "reverted") / len(bad_red)
        rev_green = sum(1 for r in bad_green if r["_why"] == "reverted") / len(
            bad_green
        )
        print(
            f"  share labelled by REVERT (the strong signal): "
            f"bad-and-red {rev_red:.1%}, bad-and-green {rev_green:.1%}"
        )
        print(
            "  If those two shares differ, the cells were not labelled by the same\n"
            "  instrument, and a label correction measured in one does not transfer."
        )


def main(root: Path) -> None:
    for f in sorted((root / "data").glob("*-prs.json")):
        summarise(
            f.stem.removesuffix("-prs"), json.loads(f.read_text(encoding="utf-8"))
        )
    print(
        "\n  Aggregates only. Per-PR records stay gitignored (AGENTS.md privacy rule)."
    )


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))

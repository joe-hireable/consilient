"""Refuse duplicate record identifiers in the experiment register and the decision directory.

R15 in `docs/20-design/dispatch-layer-requirements-2026-08-20.md` recorded the incident and
specified this check: six agents dispatched from clones cut at the same commit each read the
register, took the next free number, and **five of them chose EXP-58**. Resolving the merge with
"keep both sides" then duplicated EXP-56 and EXP-57 as stale copies of experiments that had
already run. R15's stated remedy was two checks; the second belongs to a dispatch layer that does
not exist yet, and this is the first. [measured]

R15 also closes by claiming all fifteen requirements "now have a check". That was not true of
this one, and the duplicates it names were still present when this file was written -- which is
the argument for the check rather than against it. Working principle 3: a documented boundary
with nothing banning bypass is not a boundary.

Scope is deliberately narrow: a duplicated identifier, and nothing else.

C3 in `docs/00-context/corrections-2026-08-21.md` also reports "duplicate rows for 0002 and 0027"
in `docs/decisions/index.md`. Checked 21 August 2026: each appears once in the curated
"load-bearing four" section and once in its topical table, which is ordinary index cross-listing
rather than an identifier collision. 0010 and 0018 sit in the highlight section only, so the
pattern is inconsistent -- but inconsistent is not colliding. **C3 is partial on that point, and
a check that flagged it would be reporting a false positive.** [measured] What is scanned here
instead is duplicate ADR *filenames*, which is the real invariant: two decisions cannot share a
number.

Usage:
  python .github/scripts/check_record_numbers.py
  python .github/scripts/check_record_numbers.py --self-test
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs" / "10-research" / "experiment-register.md"
DECISION_DIR = ROOT / "docs" / "decisions"

# A register entry is a level-2 or level-3 heading naming its experiment.
EXP_HEADING = re.compile(r"^#{2,3} *(EXP-[0-9]+)", re.MULTILINE)


def duplicates(names: list[str]) -> list[str]:
    return sorted(name for name, count in Counter(names).items() if count > 1)


def check(register: str, adr_numbers: list[str]) -> list[str]:
    """Return one failure line per duplicated identifier. Empty means the invariant holds."""
    failures = []
    for label, found in (
        (
            "docs/10-research/experiment-register.md headings",
            duplicates(EXP_HEADING.findall(register)),
        ),
        ("docs/decisions/ ADR numbers", duplicates(adr_numbers)),
    ):
        if found:
            failures.append(f"- {label}: {', '.join(found)}")
    return failures


def self_test() -> None:
    """The detector must fire on a synthetic collision, or it proves nothing when it passes."""
    assert check("### EXP-58 a\n### EXP-58 b\n", []) == [
        "- docs/10-research/experiment-register.md headings: EXP-58"
    ]
    assert check("### EXP-01 a\n", ["0027", "0027", "0028"]) == [
        "- docs/decisions/ ADR numbers: 0027"
    ]
    assert check("### EXP-01 a\n### EXP-02 b\n", ["0027", "0028"]) == []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()

    adr_numbers = sorted(
        p.name[:4] for p in DECISION_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")
    )
    failures = check(REGISTER.read_text(encoding="utf-8"), adr_numbers)
    if failures:
        print("Duplicate record identifiers (R15):")
        print("\n".join(failures))
        print(
            "\nAllocate identifiers in the dispatch brief, not by reading the current maximum.\n"
            "Where two versions of one record collide, supersede by key -- never keep both sides."
        )
        return 1
    print("record-numbers invariant passes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

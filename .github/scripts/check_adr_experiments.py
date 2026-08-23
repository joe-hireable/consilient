"""Refuse a PROVISIONAL ADR whose nominated experiment is not in the register.

Working principle 11 requires a PROVISIONAL decision to name the experiment that would
settle it. `tests/test_v0_invariants.py` already enforces that — but only when someone runs
the suite, which is not the agent that wrote the ADR.

That gap has a measured cost. Three times in two days an ADR landed naming an experiment it
never registered: ADR-0056 and ADR-0060 (EXP-94, EXP-95), ADR-0090 (EXP-133, EXP-134) and
ADR-0097 (EXP-140). Each time the suite went red afterwards, and because a green suite gates
whether the build driver may retire a finished unit, **one unregistered experiment held four
completed units and produced a stall that read as inactivity**. Recorded as F-06 in
`docs/00-context/orchestration-failure-modes-2026-08-23.md`.

The repair is to move the check to where the defect is created. As a pre-commit hook this
refuses the author's commit, so the person who nominated the experiment is the person who
registers it. A check that fires for somebody else later is a report, not a chokepoint —
working principle 3.

Exit 0 when clean, 1 when an ADR nominates a missing experiment. `--staged` limits the scan
to staged ADRs, which is what the hook wants; the default scans the whole directory.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# GIT_DIR overrides cwd. A git subprocess that inherits it from a hook reads the wrong
# repository — so every gate script here scrubs the git environment before shelling out.
# This one did not, and `test_gate_scripts_scrub_the_git_environment` refused it on the first
# run. That invariant exists because the failure is silent: the check would pass or fail
# against a repository nobody intended to inspect.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
DECISIONS = ROOT / "docs" / "decisions"
REGISTER = ROOT / "docs" / "10-research" / "experiment-register.md"

ADR_FILE = re.compile(r"^\d{4}-.+\.md$")
EXP_REF = re.compile(r"\bEXP-(\d{1,4})\b")
# A register entry is a heading, not a passing mention. An ADR citing EXP-99 in prose does
# not register it; only `### EXP-99 · ...` does. This is the same rule the suite applies.
REGISTER_HEADING = re.compile(r"^#{2,4}\s*EXP-(\d{1,4})\b", re.M)
# Only a PROVISIONAL decision owes an experiment. ACCEPTED rests on evidence already in
# hand; PROPOSED has not been accepted at all.
STATUS = re.compile(r"^\s*-?\s*\*\*Status:?\*\*:?\s*(.+)$", re.IGNORECASE | re.M)


def registered() -> set[str]:
    if not REGISTER.exists():
        return set()
    text = REGISTER.read_text(encoding="utf-8", errors="replace")
    return {m.group(1).lstrip("0") or "0" for m in REGISTER_HEADING.finditer(text)}


def staged_adrs() -> list[Path]:
    run = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=GIT_ENV,
    )
    out = []
    for line in (run.stdout or "").splitlines():
        p = ROOT / line.strip()
        if p.parent == DECISIONS and ADR_FILE.match(p.name) and p.exists():
            out.append(p)
    return out


def violations(paths: list[Path], have: set[str]) -> list[str]:
    found = []
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8", errors="replace")
        status = STATUS.search(text)
        if not status or "provisional" not in status.group(1).casefold():
            continue
        # Read only the status line's own nominations. An ADR discussing EXP-07 in its
        # Context does not owe that experiment; the one it names as its killer is the claim.
        nominated = {m.lstrip("0") or "0" for m in EXP_REF.findall(status.group(1))}
        missing = sorted(nominated - have, key=int)
        if missing:
            names = ", ".join(f"EXP-{m}" for m in missing)
            found.append(
                f"{path.name}: nominates {names}, absent from register headings"
            )
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--staged", action="store_true", help="scan staged ADRs only")
    args = ap.parse_args()

    paths = (
        staged_adrs()
        if args.staged
        else [p for p in DECISIONS.glob("*.md") if ADR_FILE.match(p.name)]
    )
    if not paths:
        print("adr-experiment invariant passes: no ADR in scope")
        return 0

    found = violations(paths, registered())
    if found:
        print("PROVISIONAL ADRs nominating unregistered experiments:", file=sys.stderr)
        for line in found:
            print(f"  {line}", file=sys.stderr)
        print(
            "\nWrite the register entry — a real question with a stopping rule fixed in "
            "advance — before committing the ADR. A placeholder that registers nothing is "
            "worse than a missing entry, because it looks discharged.",
            file=sys.stderr,
        )
        return 1
    print(f"adr-experiment invariant passes: {len(paths)} ADR(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

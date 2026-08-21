"""V0-39 — no code path in this repository may escalate spend.

ADR-0056 clause D5: On-Demand Spending stays Disabled and only the principal may change that.
It is the single control by which this system could spend real money, so it gets a lint rule
rather than a convention. A boundary with no rule banning bypass is not a boundary.

The two Cursor RPC method names below are not guesses: they were read out of the installed
`cursor-agent` bundle on 21 Aug 2026, on the same `aiserver.v1.DashboardService` that EXP-94
must call read-only. That adjacency is the whole reason this ships before the experiment.

Occurrences are permitted only under `ALLOWED_PREFIXES` -- documentation that has to name what
it bans. Adding a new occurrence anywhere else means editing that list in the same diff, which
is the reviewable event.

Usage:
  python .github/scripts/check_no_spend_escalation.py --check
  python .github/scripts/check_no_spend_escalation.py --self-test
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Each token is split so this file never matches its own checker and needs no allowlist entry
# of its own -- the same convention check_secrets.py uses, for the same reason.
BANNED: tuple[str, ...] = (
    "Set" + "HardLimit",
    "set_" + "hard_limit",
    "Set" + "UsageBasedPremiumRequests",
    "set_" + "usage_based_premium_requests",
    "enable_" + "on_demand_spending",
    "enable" + "OnDemandSpending",
)

# Documentation that must be able to name the controls it forbids. Paths, not patterns:
# a prefix list is auditable at a glance and cannot quietly widen.
ALLOWED_PREFIXES: tuple[str, ...] = (
    "docs/decisions/0056-schedule-work-across-prepaid-quota-pools-and-never-shed-to-spend.md",
    "docs/20-design/quota-pools-and-routes-2026-08-21.md",
)


def is_allowed(path: str) -> bool:
    return path.startswith(ALLOWED_PREFIXES)


def scan_text(path: str, text: str) -> list[tuple[str, int, str]]:
    """Return (path, 1-indexed line, token) for every banned token outside the allowlist."""
    if is_allowed(path):
        return []
    return [
        (path, number, token)
        for number, line in enumerate(text.splitlines(), start=1)
        for token in BANNED
        if token in line
    ]


def tracked_files(root: Path) -> list[str]:
    # ponytail: tracked files only. check_secrets.py owns the untracked/history sweep; a spend
    # call cannot reach CI without being tracked. Add --untracked here only if that changes.
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def violations(root: Path) -> list[tuple[str, int, str]]:
    found: list[tuple[str, int, str]] = []
    for path in tracked_files(root):
        try:
            text = (root / path).read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeError):
            continue
        found.extend(scan_text(path, text))
    return found


def self_test() -> None:
    call = "client." + "Set" + "HardLimit(9999)"
    assert scan_text("src/consilient/router.py", call), "a spend call must be caught"
    assert not scan_text(ALLOWED_PREFIXES[0], call), "the ADR may name what it bans"
    assert not scan_text(
        "src/consilient/budget.py", "check_budget(log_dir, ceilings, request)"
    )
    assert not scan_text(
        "src/consilient/usage.py", "Get" + "FilteredUsageEvents(request)"
    ), "the read-only usage oracle EXP-94 needs must not be blocked"
    assert scan_text("s.py", call)[0][1] == 1, "the reported line is 1-indexed"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("self-test: ok")
        if not args.check:
            return 0

    found = violations(Path(__file__).resolve().parents[2])
    for path, number, token in found:
        print(
            f"{path}:{number}: spend escalation is forbidden (V0-39, ADR-0056 D5): {token}"
        )
    if found:
        print(
            f"V0-39 FAILED: {len(found)} occurrence(s). Only the principal may change spend."
        )
        return 1
    print("V0-39 ok: no spend-escalation call outside the declared allowlist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""R06: the friction log is the v0 backlog, so it may not silently go stale.

Joe, 21 Aug 2026: "Keep docs/00-context/friction-log.md updated as you go — every manual
step you have to do that Consilience should automate. That log is the v0 backlog." The log
exists and is well kept by hand; what was missing is a check that fails when attention moves
elsewhere — the documented-rule-with-no-check pattern this repository catalogues.

The comparison is against the newest **commit date**, never wall-clock today: a commit-free
weekend must not fail the check, because the rule is "as you go", not "daily". A tree that
is being committed to without its friction being logged is the defect; a quiet tree is not.
[asserted: the 1-day grace is a judgement call — same-day commits may legitimately precede
their log row]
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "docs" / "00-context" / "friction-log.md"
ROW_DATE = re.compile(r"^\|\s*(\d{4})-(\d{2})-(\d{2})\s*\|", re.MULTILINE)
MAX_LAG_DAYS = 1


def _newest_row_date(text: str) -> date | None:
    found = ROW_DATE.findall(text)
    if not found:
        return None
    return max(date(int(y), int(m), int(d)) for y, m, d in found)


def _newest_commit_date() -> date | None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    # A hook's inherited GIT_DIR once redirected a repository check at another
    # repository; the scrub above is the same pattern check_private_corpus.py uses.
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    try:
        return date.fromisoformat(out.stdout.strip())
    except ValueError:
        return None


def test_friction_log_is_not_stale() -> None:
    commit_day = _newest_commit_date()
    if commit_day is None:
        pytest.skip("git unavailable — cannot date the newest commit")
    text = LOG.read_text(encoding="utf-8")
    row_day = _newest_row_date(text)
    assert row_day is not None, "friction-log.md carries no dated rows"
    lag = (commit_day - row_day).days
    assert lag <= MAX_LAG_DAYS, (
        f"friction-log.md is stale: newest row {row_day}, newest commit {commit_day} "
        f"({lag} days). Every manual step the harness should automate goes in the log "
        "as you go — the log is the v0 backlog (R06)."
    )


def test_the_staleness_check_can_fail() -> None:
    """Mutation check: a week-stale fixture log must be caught; a fresh one passes."""
    assert _newest_row_date("| 2026-08-14 | old friction | once | automate it |\n") == date(
        2026, 8, 14
    )
    stale_lag = (date(2026, 8, 21) - date(2026, 8, 14)).days
    assert stale_lag > MAX_LAG_DAYS
    fresh_lag = (date(2026, 8, 21) - date(2026, 8, 21)).days
    assert fresh_lag <= MAX_LAG_DAYS
    assert _newest_row_date("no rows here\n") is None

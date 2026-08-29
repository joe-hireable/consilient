"""A plan silently rolled back to an older, smaller one must be caught. Deletion already is.

WHY BOTH HALVES ARE NEEDED. `.harness/plan-units.json` was tracked until d01394a on 25 August
2026, and 262 of 838 local branches still carry it at their tip. Replaying any of those commits
into the main worktree stages the path into an index whose HEAD has no version of it: the live
file is OVERWRITTEN with the commit's copy, and only the abort that follows a conflict deletes it.

`ensure_plan` already handled the deletion -- it is loud, and the newest backup restores it. The
overwrite is the half nothing could see. Measured 29 August 2026: the live plan holds 147 units
and the commit's copy holds 117, so a rollback destroys 30 queued units and leaves behind a file
that parses, validates and looks entirely correct. The driver's own plan-shrink refusal needs a
25% loss before it fires; 147 to 117 is 20%, and passes it silently.

The threshold is deliberately not zero. An operator pruning a unit or two is doing their job, and
a guard that fights a legitimate edit is the failure this repository has already shipped once --
see the name gate whose self-test blocked the repair of the file it was protecting.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".harness"))

import build_loop_housekeeping as HOUSEKEEPING  # noqa: E402


def _plan(path: Path, units: int) -> Path:
    path.write_text(
        json.dumps({"units": [{"id": f"U{i:03d}"} for i in range(units)]}),
        encoding="utf-8",
    )
    return path


def test_a_large_rollback_is_detected(tmp_path: Path) -> None:
    """The measured case: 147 units replaced by 117."""
    backups = tmp_path / "plan-backups"
    backups.mkdir()
    _plan(backups / "plan-units-20260829T180000.json", 147)
    plan = _plan(tmp_path / "plan-units.json", 117)

    result = HOUSEKEEPING._plan_rolled_back(plan, backups)
    assert result is not None, (
        "a 147 -> 117 rollback went undetected, which is exactly the silent failure this guard "
        "exists for; the driver's own 25% refusal does not fire at 20% either"
    )
    live, known, source = result
    assert (live, known) == (117, 147)
    assert source.name == "plan-units-20260829T180000.json"


def test_a_healthy_plan_is_left_alone(tmp_path: Path) -> None:
    backups = tmp_path / "plan-backups"
    backups.mkdir()
    _plan(backups / "plan-units-20260829T180000.json", 147)
    plan = _plan(tmp_path / "plan-units.json", 147)
    assert HOUSEKEEPING._plan_rolled_back(plan, backups) is None


def test_a_growing_plan_is_left_alone(tmp_path: Path) -> None:
    """Units are added constantly; growth must never be mistaken for corruption."""
    backups = tmp_path / "plan-backups"
    backups.mkdir()
    _plan(backups / "plan-units-20260829T180000.json", 147)
    plan = _plan(tmp_path / "plan-units.json", 160)
    assert HOUSEKEEPING._plan_rolled_back(plan, backups) is None


def test_a_small_deliberate_prune_is_not_fought(tmp_path: Path) -> None:
    """Removing a unit or two is legitimate work, and a guard must not undo it every tick."""
    backups = tmp_path / "plan-backups"
    backups.mkdir()
    _plan(backups / "plan-units-20260829T180000.json", 147)
    plan = _plan(tmp_path / "plan-units.json", 144)
    assert HOUSEKEEPING._plan_rolled_back(plan, backups) is None, (
        "a three-unit prune was treated as corruption; the guard would restore it on every "
        "tick and the operator could never remove a unit"
    )


def test_no_backup_means_no_verdict(tmp_path: Path) -> None:
    """With nothing to compare against, silence is the only honest answer."""
    backups = tmp_path / "plan-backups"
    backups.mkdir()
    plan = _plan(tmp_path / "plan-units.json", 10)
    assert HOUSEKEEPING._plan_rolled_back(plan, backups) is None


def test_an_unreadable_plan_is_not_guessed_at(tmp_path: Path) -> None:
    backups = tmp_path / "plan-backups"
    backups.mkdir()
    _plan(backups / "plan-units-20260829T180000.json", 147)
    plan = tmp_path / "plan-units.json"
    plan.write_text("{ not json", encoding="utf-8")
    assert HOUSEKEEPING._plan_rolled_back(plan, backups) is None

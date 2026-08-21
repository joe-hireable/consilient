"""R03: the ADR trail checker — supersede, never silently edit.

The pure classification core is pinned on synthetic blobs; the git leg is exercised against
the real repository but must skip cleanly where git is unavailable.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "check_adr_trail.py"
SPEC = importlib.util.spec_from_file_location("check_adr_trail", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def test_silent_edit_of_settled_adr_is_a_violation() -> None:
    assert CHECKER.classify_edit("ACCEPTED", ["new body"], ["old body"]) == "violation"
    assert CHECKER.classify_edit("SUPERSEDED by 0002", ["x"], ["y"]) == "violation"


def test_supersession_pointer_or_dated_correction_legitimises_the_edit() -> None:
    assert (
        CHECKER.classify_edit("ACCEPTED", ["Superseded by 0067"], ["old body"])
        == "ok-settled-with-marker"
    )
    assert (
        CHECKER.classify_edit("ACCEPTED", ["Update 21 Aug 2026: corrected"], ["old"])
        == "ok-settled-with-marker"
    )


def test_unsettled_adr_and_pure_additions_are_fine() -> None:
    assert CHECKER.classify_edit("PROPOSED", ["anything"], ["old body"]) == "ok"
    assert CHECKER.classify_edit("ACCEPTED", ["reworded"], []) == "ok"


def test_trail_integrity_runs_on_the_real_tree() -> None:
    """Leg 1 must execute; violations are reported in the message, not hidden."""
    problems = CHECKER.check_trail_integrity()
    assert isinstance(problems, list)
    if problems:
        pytest.fail("ADR trail integrity violations:\n" + "\n".join(problems))


def test_history_leg_runs_and_reports_without_failing_prepin() -> None:
    reported, failed = CHECKER.check_history()
    assert failed == [], "post-pin silent edits of settled ADRs:\n" + "\n".join(failed)
    assert isinstance(reported, list)


def test_self_test_passes() -> None:
    run = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-test"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert run.returncode == 0, run.stderr

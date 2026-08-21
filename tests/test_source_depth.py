"""R05: the citation-depth checker fails on [SNIP]/[2ND] and can itself fail.

Joe: "Never cite a [SNIP] or [2ND] source publicly." The checker lives at
`.github/scripts/check_source_depth.py`; these tests pin its contract so the gate cannot
quietly rot into one that always passes.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "check_source_depth.py"
SPEC = importlib.util.spec_from_file_location("check_source_depth", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def test_snip_and_2nd_citations_fail() -> None:
    findings = CHECKER.findings_in_text(
        "Neyman & Pearson, 1933) [SNIP]:\nand a blog-only claim [2ND].\n"
    )
    assert findings == [(1, "[SNIP]"), (2, "[2ND]")]


def test_full_and_abs_citations_pass() -> None:
    assert CHECKER.findings_in_text("read in full [FULL].\nabstract only [ABS].\n") == []


def test_backticked_meta_references_pass() -> None:
    """README documents the markers themselves; discussing a flag is not citing with it."""
    assert CHECKER.findings_in_text("Most are `[SNIP]` — snippet-only, unread.\n") == []


def test_the_checker_fails_the_current_drafts() -> None:
    """The drafts carry [SNIP] citations today [measured]; the gate must say so.

    This is the honest state: P1/P2/P3 are not submittable while snippet-only sources
    remain. If this test starts failing because the drafts were verified and upgraded,
    the publications have become releasable — invert the assertion with that evidence.
    """
    drafts = sorted((ROOT / "docs" / "50-publications").glob("P*.md"))
    assert drafts, "publication drafts missing"
    assert CHECKER.scan(drafts), "the drafts carry [SNIP]/[2ND] markers; the gate must fail"


def test_self_test_passes_and_script_exits_clean_on_clean_input(tmp_path: Path) -> None:
    clean = tmp_path / "clean.md"
    clean.write_text("verified [FULL].\n", encoding="utf-8")
    self_test = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-test"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert self_test.returncode == 0, self_test.stderr
    run = subprocess.run(
        [sys.executable, str(SCRIPT), str(clean)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert run.returncode == 0, run.stderr


def test_script_exits_1_on_a_snip_file(tmp_path: Path) -> None:
    dirty = tmp_path / "dirty.md"
    dirty.write_text("snippet-only [SNIP].\n", encoding="utf-8")
    run = subprocess.run(
        [sys.executable, str(SCRIPT), str(dirty)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert run.returncode == 1
    assert "[SNIP]" in run.stderr

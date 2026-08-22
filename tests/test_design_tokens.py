"""Tests for .github/scripts/check_design_tokens.py."""

from __future__ import annotations

import sys
from pathlib import Path

# Add .github/scripts to path for import
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / ".github" / "scripts"))

import check_design_tokens  # noqa: E402


def test_declared_hexes_extraction() -> None:
    design_md = REPO_ROOT / "docs" / "20-design" / "DESIGN.md"
    declared = check_design_tokens.extract_declared_hexes(design_md)
    assert len(declared) >= 20
    assert "#0C0E12" in declared
    assert "#E2B340" in declared
    assert "#2E9E66" in declared


def test_governed_files_are_clean() -> None:
    report = check_design_tokens.check_tokens(REPO_ROOT)
    assert report["clean"] is True, f"Undeclared tokens detected: {report['violations']}"
    assert report["total_violations"] == 0


def test_catches_undeclared_in_style_and_svg(tmp_path: Path) -> None:
    sample_html = tmp_path / "sample.html"
    sample_html.write_text(
        """
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            .card { background-color: #0C0E12; border: 1px solid #999999; }
          </style>
        </head>
        <body>
          <svg width="10" height="10">
            <rect fill="#123456" stroke="#ABCDEF" />
          </svg>
          <div style="color: #FEDCBA;">Task #142 in body prose should be ignored</div>
        </body>
        </html>
        """,
        encoding="utf-8",
    )

    found = check_design_tokens.extract_governed_hexes(sample_html)
    assert "#0C0E12" in found
    assert "#999999" in found
    assert "#123456" in found
    assert "#ABCDEF" in found
    assert "#FEDCBA" in found
    assert "#142" not in found  # Prose task ID not matched as hex

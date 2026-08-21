"""Verify that CSS / UI source files use only hex colours declared in docs/20-design/DESIGN.md.

Enforces the token lockdown contract (ADR-0060, using-open-design skill):
"Tokens are non-negotiable once locked. An agent generating artefacts under a
locked DESIGN.md must not invent hex values outside the declared palette."

Usage:
  python .github/scripts/check_design_tokens.py
  python .github/scripts/check_design_tokens.py --check
  python .github/scripts/check_design_tokens.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")

# SVG/CSS presentation attributes in HTML that can carry color hexes
STYLE_ATTRS_RE = re.compile(
    r'(?:style|fill|stroke|stop-color|flood-color|lighting-color|color)=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

# Files governed by the official DESIGN.md
GOVERNED_FILES = [
    Path("src/consilient/dashboard.py"),
    Path("docs/20-design/prototypes/web-workspace.html"),
    Path("docs/20-design/prototypes/mobile-verdict.html"),
]


def extract_declared_hexes(design_md_path: Path) -> set[str]:
    """Extract all hex color tokens declared in DESIGN.md §2."""
    if not design_md_path.exists():
        raise FileNotFoundError(f"DESIGN.md not found at {design_md_path}")

    text = design_md_path.read_text(encoding="utf-8")
    hexes = {h.upper() for h in HEX_RE.findall(text)}
    return hexes


def extract_governed_hexes(file_path: Path) -> set[str]:
    """Extract all hex color codes used in CSS / SVG / styling of a governed file."""
    if not file_path.exists():
        return set()
    text = file_path.read_text(encoding="utf-8")

    if file_path.suffix == ".html":
        # Extract <style> blocks
        style_blocks = re.findall(r"<style[^>]*>(.*?)</style>", text, re.DOTALL | re.IGNORECASE)
        # Extract <script> blocks
        script_blocks = re.findall(r"<script[^>]*>(.*?)</script>", text, re.DOTALL | re.IGNORECASE)
        # Extract style and SVG presentation attributes (fill, stroke, stop-color, etc.)
        attr_values = STYLE_ATTRS_RE.findall(text)

        combined_styling = " ".join(style_blocks + script_blocks + attr_values)
        return {h.upper() for h in HEX_RE.findall(combined_styling)}

    return {h.upper() for h in HEX_RE.findall(text)}


def check_tokens(repo_root: Path) -> dict[str, object]:
    design_md = repo_root / "docs" / "20-design" / "DESIGN.md"
    declared = extract_declared_hexes(design_md)

    results: dict[str, object] = {
        "declared_tokens_count": len(declared),
        "declared_tokens": sorted(declared),
        "governed_files": {},
        "violations": {},
        "clean": True,
    }

    total_violations = 0

    for rel_path in GOVERNED_FILES:
        full_path = repo_root / rel_path
        if not full_path.exists():
            continue
        used = extract_governed_hexes(full_path)
        undeclared = used - declared
        results["governed_files"][str(rel_path)] = {
            "used_count": len(used),
            "used_tokens": sorted(used),
            "undeclared_count": len(undeclared),
            "undeclared_tokens": sorted(undeclared),
        }
        if undeclared:
            results["violations"][str(rel_path)] = sorted(undeclared)
            total_violations += len(undeclared)
            results["clean"] = False

    results["total_violations"] = total_violations
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 if undeclared tokens found")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    report = check_tokens(repo_root)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        declared_count = report["declared_tokens_count"]
        print(f"DESIGN.md declared tokens: {declared_count}")
        clean = report["clean"]
        if clean:
            print("OK: All governed files use strictly declared DESIGN.md color tokens.")
        else:
            print("FAILED: Undeclared color tokens detected in governed files:")
            for file_name, undeclared in report["violations"].items():
                print(f"  {file_name}: {', '.join(undeclared)}")

    if args.check and not report["clean"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

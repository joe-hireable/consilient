"""Publication-facing documents cite only verified sources — the executable half of R05.

Joe's rule: "Never cite a [SNIP] or [2ND] source publicly." Until this script the rule was
a prose instruction in four documents and a PowerShell-only line in RELEASE-PLAN.md pointing
at a placeholder path — the catalogued failure shape of a gate that cannot run. The depth
markers themselves are defined in `.agents/skills/citing-sources/SKILL.md`:

    [FULL]  paper or page fetched and read            — citable
    [ABS]   abstract or listing read directly         — citable for what the abstract states
    [SNIP]  seen only in a search-result snippet      — never citable publicly
    [2ND]   known only via blog/aggregator/vendor     — never citable publicly

Usage:

    python .github/scripts/check_source_depth.py [paths or globs ...]
    python .github/scripts/check_source_depth.py --self-test

With no arguments the publication set is scanned: `docs/50-publications/*.md` and
`README.md`. Exit 1, one `file: line` per finding, when a citation carries [SNIP] or [2ND].
A backticked marker (`` `[SNIP]` ``) discusses the flag system rather than citing with it
and is ignored — README.md documents the markers themselves. [asserted: the checker cannot
judge whether an [ABS] citation claims only what its abstract states; that half of the rule
stays with the reviewer.]

Standard library only. Exit 0 clean, 1 on any finding, 2 on misuse.
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_PATTERNS = ("docs/50-publications/*.md", "README.md")

# A citation marker is an unbackticked [SNIP] or [2ND]. Backticks mean the text is about
# the flag, not a citation carrying it.
FORBIDDEN = re.compile(r"(?<!`)\[(SNIP|2ND)\](?!`)")

SELFTEST_FAIL = "Trautsch & Ledel, EMSE 2019) [SNIP].\n"
SELFTEST_PASS = "Trautsch & Ledel, EMSE 2019) [FULL].\n"
SELFTEST_META = "Most are `[SNIP]` — snippet-only, unread.\n"


def findings_in_text(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in FORBIDDEN.finditer(line):
            found.append((lineno, match.group(0)))
    return found


def scan(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            findings.append(f"{path}: unreadable ({error})")
            continue
        for lineno, marker in findings_in_text(text):
            findings.append(f"{path}:{lineno}: {marker} cited in a publication-facing file")
    return findings


def _self_test() -> int:
    if findings_in_text(SELFTEST_FAIL) != [(1, "[SNIP]")]:
        print("self-test FAILED: [SNIP] citation not caught", file=sys.stderr)
        return 1
    if findings_in_text(SELFTEST_PASS):
        print("self-test FAILED: [FULL] citation flagged", file=sys.stderr)
        return 1
    if findings_in_text(SELFTEST_META):
        print("self-test FAILED: backticked meta-reference flagged", file=sys.stderr)
        return 1
    print("self-test passed: [SNIP] caught, [FULL] clean, backticked meta-reference ignored")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_source_depth",
        description="Fail when a publication-facing document cites a [SNIP] or [2ND] source.",
    )
    parser.add_argument("paths", nargs="*", help="markdown files or globs to scan")
    parser.add_argument(
        "--self-test", action="store_true", help="prove the checker can fail, then exit"
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()

    patterns = args.paths or list(DEFAULT_PATTERNS)
    paths: list[Path] = []
    for pattern in patterns:
        matched = sorted(glob.glob(str(ROOT / pattern), recursive=True))
        paths.extend(Path(p) for p in matched)
        if not matched and Path(pattern).is_file():
            paths.append(Path(pattern))
    if not paths:
        print("no publication-facing files matched; nothing scanned", file=sys.stderr)
        return 2

    findings = scan(paths)
    if findings:
        print("source-depth invariant FAILED:", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        print(
            f"{len(findings)} unverified citation(s) in {len(paths)} publication-facing "
            "file(s). Verify the source and upgrade the marker to [FULL]/[ABS], or remove "
            "the claim it carries. Joe's rule: never cite a [SNIP] or [2ND] source publicly.",
            file=sys.stderr,
        )
        return 1
    print(f"source-depth invariant passes: {len(paths)} publication-facing file(s) clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

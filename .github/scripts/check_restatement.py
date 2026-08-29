"""Refuse hand-written restatements of generated project facts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FACTS = Path("docs/project-facts.md")

# A generated region is exempt only when its marker names a REGISTERED generator. An arbitrary
# marker must not buy an exemption. Widened 28 August 2026: the set named only the facts spine,
# so the two inline blocks that scripts/build_counts.py maintains in CLAUDE.md and README.md were
# unrecognised, and the generator's own output was reported as a hand-written restatement of
# itself -- "CLAUDE.md:14 restates a generated fact '108 ADRs'", on a line no human wrote.
REGISTERED_REGIONS = frozenset(
    {
        FACTS.as_posix(),
        "scripts/build_counts.py#inventory",
        "scripts/build_counts.py#experiments",
    }
)
TOP_LEVEL_WRITTEN = ("README.md", "AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md")
FACT_HEADING = re.compile(r"^##\s+(\w+)\s*$", re.MULTILINE)
DOCUMENT_CLASS = re.compile(r"(?:Document\s+)?class:\s*\**\s*W(?:/g)?\b", re.IGNORECASE)
GENERATED_MARKER = re.compile(
    r"<!--\s*(BEGIN|END) GENERATED:\s*([^\s>]+)\s*-->", re.IGNORECASE
)
COUNT_PATTERNS = {
    "adr_count": re.compile(r"(?<![\w,])\d[\d,]*\s+ADRs?\b", re.IGNORECASE),
    "experiment_count": re.compile(
        r"(?<![\w,])\d[\d,]*\s+registered\s+experiments?\b", re.IGNORECASE
    ),
    "spec_count": re.compile(
        r"(?<![\w,])\d[\d,]*\s+(?:specifications?|specs?)\b", re.IGNORECASE
    ),
    "version": re.compile(
        r"\bConsilient\s+(?:version\s+)?v?\d+(?:\.\d+){1,3}(?:[-+][\w.-]+)?\b",
        re.IGNORECASE,
    ),
}
REQUIRED_FACTS = frozenset(COUNT_PATTERNS)


def fact_keys(root: Path) -> set[str]:
    path = root / FACTS
    if not path.is_file():
        raise ValueError(f"{FACTS.as_posix()} is missing")
    keys = set(FACT_HEADING.findall(path.read_text(encoding="utf-8")))
    if missing := REQUIRED_FACTS - keys:
        raise ValueError(
            f"{FACTS.as_posix()} is missing facts: {', '.join(sorted(missing))}"
        )
    return keys


def written_documents(root: Path) -> list[Path]:
    paths = [root / name for name in TOP_LEVEL_WRITTEN if (root / name).is_file()]
    docs = root / "docs"
    if docs.is_dir():
        for path in docs.rglob("*.md"):
            header = "\n".join(path.read_text(encoding="utf-8").splitlines()[:20])
            if DOCUMENT_CLASS.search(header):
                paths.append(path)
    return sorted(set(paths))


def written_lines(path: Path) -> list[tuple[int, str]]:
    """The HAND-WRITTEN lines of a document: everything outside a generated region.

    MEASURED 28 August 2026. REGISTERED_REGIONS held only `docs/project-facts.md`, so
    `docs/project-facts.md`, so the two live generated blocks in CLAUDE.md and README.md --
    both emitted by `scripts/build_counts.py` -- were invisible to it. Their BEGIN markers were
    treated as ordinary prose, the region never opened, and the generator's own output was then
    reported as a hand-written restatement of itself: "CLAUDE.md:14 restates a generated fact
    '108 ADRs'", on a line no human wrote and that `build_counts.py --check` keeps current.

    The registration requirement itself is deliberate and stays: an arbitrary hand-written
    BEGIN GENERATED marker must NOT buy an exemption, or the check could be silenced by wrapping
    prose in a fake marker. tests/test_restatement.py pins that, and it caught the first attempt
    at this fix, which had dropped the requirement entirely. The defect was only that the
    registered set named one generator when the tree has two.

    Regions are also now tracked per source, because two generators may interleave in one file
    and a single boolean cannot tell whose END it has just read.
    """
    visible: list[tuple[int, str]] = []
    open_sources: set[str] = set()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        marker = GENERATED_MARKER.search(line)
        if marker is None or marker.group(2) not in REGISTERED_REGIONS:
            if not open_sources:
                visible.append((line_no, line))
            continue
        source = marker.group(2)
        if marker.group(1).upper() == "BEGIN":
            if source in open_sources:
                raise ValueError(f"nested generated region for {source}")
            open_sources.add(source)
        else:
            if source not in open_sources:
                raise ValueError(
                    f"generated region for {source} ends without a beginning"
                )
            open_sources.discard(source)
    if open_sources:
        raise ValueError(f"unclosed generated region: {sorted(open_sources)}")
    return visible


def check(root: Path) -> tuple[list[tuple[Path, int, str]], int]:
    keys = fact_keys(root)
    findings: list[tuple[Path, int, str]] = []
    paths = written_documents(root)
    for path in paths:
        relative = path.relative_to(root)
        try:
            lines = written_lines(path)
        except ValueError as error:
            findings.append((relative, 0, str(error)))
            continue
        for line_no, line in lines:
            for key, pattern in COUNT_PATTERNS.items():
                if key in keys and (match := pattern.search(line)):
                    findings.append((relative, line_no, match.group(0)))
    return findings, len(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check written documents")
    args = parser.parse_args()
    if not args.check:
        print("FAIL --check is required", file=sys.stderr)
        return 2
    try:
        findings, checked = check(ROOT)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    for path, line_no, text in findings:
        if line_no:
            print(f'{path.as_posix()}:{line_no} restates a generated fact "{text}"')
        else:
            print(f"{path.as_posix()}: {text}")
    print(f"checked={checked} adverse={len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

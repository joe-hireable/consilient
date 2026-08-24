"""Refuse hand-written restatements of generated project facts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FACTS = Path("docs/project-facts.md")
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
    visible: list[tuple[int, str]] = []
    in_generated = False
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        marker = GENERATED_MARKER.search(line)
        if marker is None or marker.group(2) != FACTS.as_posix():
            if not in_generated:
                visible.append((line_no, line))
            continue
        if marker.group(1).upper() == "BEGIN":
            if in_generated:
                raise ValueError("nested generated region")
            in_generated = True
        else:
            if not in_generated:
                raise ValueError("generated region ends without a beginning")
            in_generated = False
    if in_generated:
        raise ValueError("unclosed generated region")
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

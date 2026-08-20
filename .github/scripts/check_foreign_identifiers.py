"""Refuse tracked content that carries identifiers belonging to another repository.

`check_private_corpus.py` matches FILE PATHS from the private corpora. On 21 August 2026 an
independent pre-publication audit found what that cannot see: `results-exp43.json` carries **71
forty-character commit SHAs**, and none of them resolves in this repository. They are commit
identifiers from a private commercial repository, mined by EXP-43.

`AGENTS.md` permits the corpora's names and **aggregate measured metrics**. A list of specific
commits is neither. It is a list of incidents, and it is exactly what a path-matcher and a
secret-regex both miss.

    python .github/scripts/check_foreign_identifiers.py            # tracked tree
    python .github/scripts/check_foreign_identifiers.py --staged   # pre-commit / pre-push
    python .github/scripts/check_foreign_identifiers.py --self-test

The check never prints a foreign identifier in full. It reports the file, the count and a
truncated prefix, which is enough to find it and not enough to republish it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Forty hex characters, delimited so ordinary hex blobs and digests do not match by accident.
SHA_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])")

# Paths whose whole purpose is to record identifiers of THIS repository, or to document the rule.
EXEMPT_PREFIXES = (
    ".harness/log/",  # the trajectory records this repository's own state digests
)

# A blob/tree digest is also 40 hex characters. Resolve as a commit specifically.
MAX_BYTES = 40_000_000


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )


def tracked_paths(staged: bool) -> list[str]:
    command = (
        ["diff", "--cached", "--name-only", "--diff-filter=ACMR"]
        if staged
        else ["ls-files"]
    )
    completed = git(*command)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "cannot enumerate files")
    return [line for line in completed.stdout.splitlines() if line]


def resolves_here(sha: str) -> bool:
    """Is this a commit that exists in this repository?"""
    return git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def scan(paths: list[str]) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    cache: dict[str, bool] = {}
    for relative in paths:
        if relative.startswith(EXEMPT_PREFIXES):
            continue
        path = Path(relative)
        try:
            if not path.is_file() or path.stat().st_size > MAX_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        foreign = set()
        for sha in set(SHA_RE.findall(text)):
            if sha not in cache:
                cache[sha] = resolves_here(sha)
            if not cache[sha]:
                foreign.add(sha)
        if foreign:
            findings.append((relative, len(foreign), sorted(foreign)[0][:7]))
    return findings


def self_test() -> None:
    """The check must detect a foreign SHA and must not flag one of our own."""
    assert SHA_RE.search("a" * 40), "a bare 40-hex string must match"
    assert not SHA_RE.search("a" * 39), "39 characters is not a commit id"
    assert not SHA_RE.search("b" * 41), "41 characters is not a commit id"
    head = git("rev-parse", "HEAD").stdout.strip()
    if head:
        assert resolves_here(head), "HEAD must resolve in its own repository"
    assert not resolves_here("0" * 40), "an all-zero id must not resolve"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--staged",
        action="store_true",
        help="scan staged content instead of the tracked tree",
    )
    parser.add_argument(
        "--self-test", action="store_true", help="prove the detector still detects"
    )
    args = parser.parse_args()

    if args.self_test:
        self_test()

    findings = scan(tracked_paths(args.staged))
    if findings:
        print(
            "Foreign commit identifiers in tracked content — values are deliberately truncated:"
        )
        for relative, count, prefix in findings:
            print(
                f"- {relative}: {count} identifier(s) that do not resolve here, e.g. {prefix}…"
            )
        print()
        print(
            "AGENTS.md permits the private corpora's names and AGGREGATE metrics. A list of"
        )
        print("specific commits is neither. Aggregate them, or remove them.")
        return 1

    print(
        "foreign-identifier invariant passes: no unresolvable commit ids in tracked content"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

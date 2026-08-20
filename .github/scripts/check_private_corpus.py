"""Refuse tracked content that reconstructs a private corpus.

`AGENTS.md` declares the rule:

    Publish anything from `../hireable-3.0` or `../jobboard-v2` -- never. Their names and
    aggregate measured metrics may appear in docs; their code, file contents, excerpts and
    detailed file paths may never be committed here.

Until 20 August 2026 that rule had no check, and working principle 3 says plainly what
happens then: a documented boundary with nothing banning bypass is not a boundary. It had
been violated since the initial commit -- detailed internal paths, function and script
identifiers, hook filenames and a verbatim quotation from a private assessment document,
sitting in two tracked files. [measured]

It was found by a paid cross-family audit, not by this repository. The orchestrator's own
sweep searched for paths PREFIXED with a repository name -- `<repo>/src/...` -- and the leak
was the same path written bare, with no prefix to search for. That angle could not have
found it however carefully it was run. This script encodes the angle that worked: take the
paths that actually exist in the private repositories and look for them here.

It also caught itself on first run: the docstring below originally used a real private path
as its example of a distinctive one. That is the correct behaviour and it is left recorded
rather than tidied away.

WHY THIS IS NOT A CI JOB. The private repositories are not present on a CI runner, so this
cannot run there, and a check that silently no-ops is worse than none. It is a local
pre-publication gate. `--require-corpora` makes a missing corpus a failure rather than a
skip, which is what a release step should pass.

    python .github/scripts/check_private_corpus.py --require-corpora

Exit 0 clean, 1 on any finding. Never prints the matched private path in full -- it prints
where the leak is in THIS repository and enough of the needle to find it, because a script
that dumps private paths to a build log has become the leak.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CORPORA = [
    Path(r"C:\Users\jpbpr\Repositories\jobboard-v2"),
    Path(r"C:\Users\jpbpr\Repositories\hireable-3.0"),
]

# A path segment has to be distinctive to be evidence. `src/index.ts` appears in half the
# repositories on earth; a deeply nested product path does not. Require depth and length, and skip
# anything this repository would legitimately contain.
MIN_DEPTH = 3
MIN_LEN = 12
GENERIC = re.compile(
    r"^(src/index|src/main|docs?/|test/|tests/|\.github/|node_modules/|dist/)", re.I
)

# Files that are allowed to discuss the corpora, because their entire purpose is to record
# what was learned from them. They are still checked; they are simply where a finding is
# most expected.
EXPECTED = {"docs/30-source-material/prior-repo-assets.md"}


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return [line for line in out.stdout.splitlines() if line.strip()]


def corpus_paths(repo: Path) -> set[str]:
    """Every path in the corpus's HEAD tree, as forward-slash strings."""
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return {
        line.strip().replace("\\", "/")
        for line in out.stdout.splitlines()
        if line.strip()
    }


def needles(paths: set[str]) -> set[str]:
    """Distinctive path prefixes worth searching for, including directory prefixes.

    A leak often names a directory (a nested directory) rather than a file, so every
    ancestor of a real file is a needle too.
    """
    found: set[str] = set()
    for path in paths:
        parts = path.split("/")
        for depth in range(MIN_DEPTH, len(parts) + 1):
            candidate = "/".join(parts[:depth])
            if len(candidate) >= MIN_LEN and not GENERIC.match(candidate):
                found.add(candidate)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-corpora", action="store_true")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    present = [c for c in CORPORA if (c / ".git").exists()]
    missing = [c.name for c in CORPORA if c not in present]

    if missing:
        message = (
            f"private corpora not present, cannot check against: {', '.join(missing)}"
        )
        if args.require_corpora:
            print(f"FAIL {message}")
            return 1
        print(f"SKIP {message}")

    if not present:
        return 0

    all_needles: set[str] = set()
    for repo in present:
        all_needles |= needles(corpus_paths(repo))
    print(
        f"checking against {len(all_needles)} distinctive paths from {len(present)} corpora"
    )

    findings: list[tuple[str, int, str]] = []
    for rel in tracked_files(root):
        path = root / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            for needle in all_needles:
                if needle in line:
                    findings.append((rel, number, needle))

    if not findings:
        print(
            "private-corpus invariant passes: no corpus path appears in tracked content"
        )
        return 0

    print(
        f"\nFAIL {len(findings)} private-corpus path reference(s) in tracked content:\n"
    )
    for rel, number, needle in sorted(findings):
        tail = needle.rsplit("/", 1)[-1]
        expected = "  (expected location)" if rel in EXPECTED else ""
        print(
            f"  {rel}:{number}  references a private path ending '.../{tail}'{expected}"
        )
    print(
        "\nAGENTS.md: detailed file paths from the private corpora may never be committed.\n"
        "Aggregate measured metrics and the repository names are permitted; paths are not."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

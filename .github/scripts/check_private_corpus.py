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

THE 21 AUGUST 2026 REPAIR. This gate was unsound in both directions and the cause was an
inherited environment. Git exports `GIT_DIR`, `GIT_INDEX_FILE` and `GIT_WORK_TREE` when it
invokes a hook, and **`GIT_DIR` overrides `cwd`**. Measured that day: run standalone the
script enumerated 2854 distinctive needles from the two corpora and passed; run from the
`pre-push` hook it enumerated **17**, because both `git ls-files` calls read the repository
the hook came from rather than the corpus they were pointed at, and reported 2123 findings
that were this repository's files matching themselves. [measured]

The false-PASS direction is the serious one. `--require-corpora` tested only that
`<corpus>/.git` existed; it never established that the enumeration came from the corpus. On a
tree where those 17 wrong needles happened not to match, **the sole gate protecting private
commercial code would have reported PASS having read neither corpus.** [measured]

Two things now prevent it. Every git subprocess runs with `GIT_ENV`, from which every `GIT_*`
variable has been removed. And `ls_files()` will not return a listing until
`git rev-parse --show-toplevel`, run from the same directory, resolves to that same directory
-- so an enumeration is bound to its source, and `--require-corpora` means "I read those
corpora" rather than "those directories exist".
"""

from __future__ import annotations

import argparse
import os
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


class BindingError(RuntimeError):
    """An enumeration could not be proved to have come from the directory it names."""


# Git exports GIT_DIR, GIT_INDEX_FILE and GIT_WORK_TREE into every hook it runs, and GIT_DIR
# overrides cwd. A git subprocess that inherits them reads whatever repository the hook came
# from. Scrubbing them is half the repair; ls_files() below is the other half.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def ls_files(repo: Path) -> list[str]:
    """Tracked paths of `repo`, or raise unless the listing provably came from `repo`.

    The binding check is the load-bearing part. `cwd=` is a request; `git rev-parse
    --show-toplevel` is the answer, and only when the answer is `repo` itself is the listing
    evidence about `repo`. An empty listing is also refused: a corpus that yields no paths
    yields no needles, and a gate that checks nothing must never report PASS.
    """
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=repo,
        env=GIT_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout.strip()
    if not top or Path(top).resolve() != repo.resolve():
        raise BindingError(
            f"enumeration of '{repo.name}' resolved to a different repository; refusing to "
            "report on a tree that was never read"
        )
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=repo,
        env=GIT_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    files = [line.strip() for line in out.stdout.splitlines() if line.strip()]
    if not files:
        raise BindingError(f"'{repo.name}' enumerated to zero tracked files")
    return files


def tracked_files(root: Path) -> list[str]:
    return ls_files(root)


def corpus_paths(repo: Path) -> set[str]:
    """Every path in the corpus's HEAD tree, as forward-slash strings."""
    return {line.replace("\\", "/") for line in ls_files(repo)}


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
    try:
        for repo in present:
            all_needles |= needles(corpus_paths(repo))
        checked = tracked_files(root)
    except BindingError as error:
        print(f"FAIL {error}")
        return 1
    print(
        f"checking against {len(all_needles)} distinctive paths from {len(present)} corpora"
    )

    findings: list[tuple[str, int, str]] = []
    for rel in checked:
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

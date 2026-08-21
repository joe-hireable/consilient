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

CONTENT FINGERPRINTS close the remaining excerpt gap. Each UTF-8 line is normalised to
case-folded words; lines with at least 12 words and 80 characters become whole-line
shingles, represented only by their SHA-256 digest. To keep the local gate bounded, it
retains the deterministic lowest 25,000 digests per corpus: at most 50,000 content needles,
not millions. A copied multi-line passage survives a one-line edit through its neighbouring
shingles; an edited isolated line is below this detector's guarantee.

It also caught itself on first run: the docstring below originally used a real private path
as its example of a distinctive one. That is the correct behaviour and it is left recorded
rather than tidied away.

WHY THIS IS NOT A CI JOB. The private repositories are not present on a CI runner, so this
cannot run there, and a check that silently no-ops is worse than none. It is a local
pre-publication gate. `--require-corpora` makes a missing corpus a failure rather than a
skip, which is what a release step should pass.

    python .github/scripts/check_private_corpus.py --require-corpora
    python .github/scripts/check_private_corpus.py --self-test

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
import hashlib
import heapq
import os
import re
import subprocess
import sys
import unicodedata
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

# Whole-line shingles make line-number reporting exact. Bottom-hash sampling is stable across
# file order and bounds each private corpus to tens of thousands of hash-only needles.
MIN_CONTENT_WORDS = 12
MIN_CONTENT_CHARS = 80
MAX_CONTENT_NEEDLES = 25_000
WORD_RE = re.compile(r"\w+", re.UNICODE)

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


def content_digest(line: str) -> str | None:
    """Hash one distinctive normalised line, or ignore short/generic text."""
    words = WORD_RE.findall(unicodedata.normalize("NFKC", line).casefold())
    normalised = " ".join(words)
    if len(words) < MIN_CONTENT_WORDS or len(normalised) < MIN_CONTENT_CHARS:
        return None
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def content_needles(root: Path, paths: set[str] | list[str]) -> set[str]:
    """Return a bounded deterministic sample of hash-only content shingles."""
    selected: set[str] = set()
    heap: list[tuple[int, str]] = []
    for rel in paths:
        path = root / rel
        if not path.exists():
            raise BindingError(
                f"tracked content is missing from '{root.name}'; refusing a partial scan"
            )
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        except OSError as error:
            raise BindingError(
                f"tracked content in '{root.name}' could not be read; refusing a partial scan"
            ) from error
        for line in lines:
            digest = content_digest(line)
            if digest is None or digest in selected:
                continue
            item = (-int(digest, 16), digest)
            if len(heap) < MAX_CONTENT_NEEDLES:
                heapq.heappush(heap, item)
                selected.add(digest)
            elif item > heap[0]:
                _, removed = heapq.heapreplace(heap, item)
                selected.remove(removed)
                selected.add(digest)
    if not selected:
        raise BindingError(
            f"'{root.name}' produced zero distinctive content fingerprints"
        )
    return selected


def scan_content(
    root: Path, paths: list[str], needle_hashes: set[str]
) -> list[tuple[str, int, str]]:
    """Find public lines matching corpus hashes without retaining or returning their text."""
    findings: list[tuple[str, int, str]] = []
    for rel in paths:
        try:
            lines = (root / rel).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, start=1):
            digest = content_digest(line)
            if digest is not None and digest in needle_hashes:
                findings.append((rel, number, digest))
    return findings


def self_test() -> None:
    """The content detector must normalise harmless formatting and reject an edit."""
    line = (
        "A synthetic private passage contains enough deliberately unusual words to prove "
        "that the content fingerprint recognises copied material without storing its text."
    )
    digest = content_digest(line)
    assert digest is not None, "a long distinctive line must produce a fingerprint"
    assert digest == content_digest(f"  {line.upper()}  "), (
        "case and surrounding whitespace must be normalised"
    )
    assert digest != content_digest(line.replace("unusual", "specific")), (
        "an edited line must not retain the verbatim fingerprint"
    )
    assert content_digest("too short") is None, "short boilerplate is not distinctive"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-corpora", action="store_true")
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--self-test", action="store_true", help="prove the detector still detects"
    )
    args = parser.parse_args()

    if args.self_test:
        self_test()

    root = Path(args.root).resolve()
    # The corpus locations above are absolute paths on the principal's Windows machine, so
    # this gate can only be RUN there. `CONSILIENT_CORPORA` (os.pathsep-separated) lets the
    # same person run it from a second machine, or from Linux, without editing this file
    # and without those paths entering the repository. Unset, behaviour is unchanged.
    override = os.environ.get("CONSILIENT_CORPORA", "").strip()
    corpora = (
        [Path(p) for p in override.split(os.pathsep) if p.strip()]
        if override
        else CORPORA
    )
    present = [c for c in corpora if (c / ".git").exists()]
    missing = [c.name for c in corpora if c not in present]

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
    all_content_needles: set[str] = set()
    try:
        for repo in present:
            paths = corpus_paths(repo)
            all_needles |= needles(paths)
            all_content_needles |= content_needles(repo, paths)
        checked = tracked_files(root)
    except BindingError as error:
        print(f"FAIL {error}")
        return 1
    print(
        f"checking against {len(all_needles)} distinctive paths from {len(present)} corpora"
    )
    print(
        f"checking against {len(all_content_needles)} hashed content shingles from "
        f"{len(present)} corpora"
    )

    path_findings: list[tuple[str, int, str]] = []
    for rel in checked:
        path = root / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            for needle in all_needles:
                if needle in line:
                    path_findings.append((rel, number, needle))

    content_findings = scan_content(root, checked, all_content_needles)

    if not path_findings and not content_findings:
        print(
            "private-corpus invariant passes: no corpus path or content excerpt appears "
            "in tracked content"
        )
        return 0

    if path_findings:
        print(
            f"\nFAIL {len(path_findings)} private-corpus path reference(s) in tracked "
            "content:\n"
        )
        for rel, number, needle in sorted(path_findings):
            tail = needle.rsplit("/", 1)[-1]
            expected = "  (expected location)" if rel in EXPECTED else ""
            print(
                f"  {rel}:{number}  references a private path ending "
                f"'.../{tail}'{expected}"
            )

    if content_findings:
        print(
            f"\nFAIL {len(content_findings)} private-corpus content fingerprint(s) in "
            "tracked content:\n"
        )
        for rel, number, digest in sorted(content_findings):
            print(f"  {rel}:{number}  matches private content hash {digest[:12]}")

    print(
        "\nAGENTS.md: detailed paths and content excerpts from the private corpora may never "
        "be committed.\nAggregate measured metrics and the repository names are permitted; "
        "paths and excerpts are not."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

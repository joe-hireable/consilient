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

A GATE, NOT A WALL. Until 21 August 2026 this exited non-zero on fourteen occurrences that had
already been examined and cleared, and the `pre-push` hook refuses on any non-zero exit -- so
the gate could never pass. That is the defect catalogued in
`docs/00-context/four-of-seven-gate-conditions-cannot-pass-2026-08-20.md`: a condition that can
never pass teaches people to bypass it. `ALLOWLIST` below records the cleared identifiers with
a justification each; anything outside it still fails, immediately.

Each allowlisted identifier is stored as the SHA-256 DIGEST of the identifier, never the
identifier. That is not ceremony. It keeps the truncation discipline unbroken in the one file
that would otherwise have to write twelve of them out in full, and it stops this file tripping
its own detector. A 64-hex digest cannot match a 40-hex delimited pattern, and `self_test()`
asserts that rather than assuming it. To add an entry:

    python -c "import hashlib,sys; print(hashlib.sha256(sys.argv[1].encode()).hexdigest())" SHA
"""

from __future__ import annotations

import argparse
import hashlib
import os
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

ROOT = Path(__file__).resolve().parents[2]

# Git exports GIT_DIR, GIT_INDEX_FILE and GIT_WORK_TREE into every hook it runs, and GIT_DIR
# overrides cwd -- GIT_INDEX_FILE would also redirect `--staged` onto another repository's
# index. Every git subprocess in .github/scripts now runs with these removed; the measurement
# that forced it is recorded in check_private_corpus.py.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

# SHA-256 digests of commit-shaped identifiers that appear in tracked content and have been
# examined. On 21 August 2026 each of the twelve was tested with `git cat-file -e SHA^{commit}`
# against BOTH private corpora with a scrubbed environment: none resolved in either. [measured]
# Removing an entry is always permitted. Adding one means a human re-ran that test and wrote
# down the answer.
ALLOWLIST = {
    # Two upstream permalinks cited by the triggered-recall research as prior art, 23 Aug
    # 2026: a pinned NousResearch/hermes-agent revision and a ruvnet/ruflo revision. Both
    # were resolved against BOTH private corpora and neither appears in either; the Hermes
    # URL was additionally fetched and resolves. This class of entry now recurs with every
    # research stream that cites upstream by permalink, which is a growth the ratchet cannot
    # absorb indefinitely — the structural answer is to distinguish a bare identifier, which
    # is how the original leak looked, from one embedded in a public forge URL that names its
    # own repository. That is queued as a unit rather than decided here.
    "55b67004d7a43bf42a2ebcce2a45c95f8a5d86db1d6687f70dbe01584e50f1aa": "bibliography.md - pinned NousResearch/hermes-agent revision cited as memory prior art. "
    "Resolved against both private corpora: present in neither. Public URL fetched 23 Aug 2026 "
    "and resolves.",
    "296e0896c9844b0308aa780d4133cd0fabe3b3c033db8cf0f46d6da052b450fb": "bibliography.md and triggered-recall spec - ruvnet/ruflo automatic-intelligence path, "
    "pinned. Resolved against both private corpora: present in neither. Same repository as the "
    "already-cleared entries below.",
    "f0c3152ae865438726f4697dabc5dcf3f696bed2b9ffe349ab52f92afe0f32f9": "gap-register-2026-08-22.md - the head of a public GitHub compare link showing "
    "same-day drift in ruvnet/ruflo against the base revision allowlisted below. Cleared "
    "22 Aug 2026 by positive public provenance: the compare URL was fetched and both "
    "revisions resolve, five commits apart, covering Windows CI fixes and dependency "
    "bumps. The private corpora were NOT scanned for this entry; they were, separately, "
    "searched for every identifier in that file and none resolved in either.",
    "0110386da5278d960f2cca97c1ac2620f872b89de22e00f820a36ad8f71d23ee": "bibliography.md - a public GitHub permalink pinning the inspected revision of "
    "ruvnet/ruflo, cited as prior art. Cleared 22 Aug 2026 by a different route from the "
    "entries below: rather than failing to find it in the private corpora, the public URL "
    "was fetched and resolves, showing the commit inside that repository's public history. "
    "Positive public provenance is stronger evidence than absence from the corpora, and a "
    "collision between a public SHA-1 and a private one is not a case worth designing for. "
    "The private corpora were NOT scanned for this entry.",
    "74423b39119b3990866f184beca8b4a8e355f0bc89c0970b0aa9e62f44d75fe7": "experiment-register.md - EXP-96 pins Pallets `itsdangerous` 2.2.0 by commit as its "
    "second corpus. Pinning the exact revision measured is what makes the result "
    "reproducible, so removing it would weaken the experiment. Tested 21 Aug 2026 with a "
    "scrubbed environment against both private corpora: resolves in neither.",
    "8dd61cadb9e983d128ad8bc9d8da9a7aa51fb3142d191f74532e14124f22bcb2": ".agents/skills/using-open-design/references/critique-upstream.md - a public GitHub "
    "permalink pinning a blob in nexu-io/open-design for provenance, the same class as the "
    "julep-ai and mlflow permalinks below. Tested 21 Aug 2026 with a scrubbed environment "
    "against both private corpora: resolves in neither.",
    "6183c59c0dbd5b519c06f17710365b66bedde9455398c7db3be6e01ed7d4ec81": "exp05/backend-comparison.json:126 - an OpenCode session snapshot digest inside a "
    "captured raw transcript tail, not a git commit at all.",
    "a835ca7063a2cde8547e189f9f2bfffbb95f2366898a8cfc547c52b42986d9bb": "exp49 results x2 and run_exp49.py - EXP-49's own pre-registration commit, orphaned "
    "by this repository's history rewrite.",
    "70b0ce5be10eb485e98b2e39e4cd3a1ca5d29cf701abf750366644b54ae76fae": "orchestration-dependencies-2026-08-20.md:72 - public permalink into "
    "github.com/julep-ai/julep. [cited]",
    "f6aaacce682ae394128c72423412cb89f018ae8a8d43020750a6d6cf8b6c8687": "orchestration-dependencies-2026-08-20.md:74 - public permalink into "
    "github.com/mlflow/mlflow. [cited]",
    "cb91183a60800eedca949eaeaa355811a46e7c0770ab054c6dc667c0f0403cc6": "orchestration-dependencies-2026-08-20.md:75 - public permalink into "
    "github.com/gptme/gptme. [cited]",
    "f272fc7d6bfeca2f17765d37ec1489c662e95837ab3a8d1f1b7582f4589d9ed3": "orchestration-dependencies-2026-08-20.md:79 - public permalink into "
    "github.com/tavily-ai/tavily-chat. [cited]",
    "b8bd517a78280c6e34b2f84d9548dd151686c52150504b0d1a9565724dc2f4ed": "orchestration-dependencies-2026-08-20.md:80 - public permalink into "
    "github.com/dataforgoodfr/13_odis. [cited]",
    "615ea7a905bcb09be96187ff87d3a8ad1324400e6cc77a4cb04be3d9c5339141": "orchestration-dependencies-2026-08-20.md:81 - public permalink into "
    "github.com/coleam00/MongoDB-RAG-Agent. [cited]",
    "7dceea271dafc608ef71740b09b1828949fe7bb1d37ea8597dc363cc03651a35": "orchestration-dependencies-2026-08-20.md:85 - public permalink into "
    "github.com/Zen7-Labs/Zen7-Payment-Agent. [cited]",
    "b43ec99390cfed6070c28517df5719b3aa5955fd12044adf6b7c490b320c9292": "orchestration-dependencies-2026-08-20.md:86 - public permalink into "
    "github.com/heaversm/crew-llamafile. [cited]",
    "fbeeb8070d3d6e5b76c64b724ca192bc31128dd5dab9ce69fa74d1ed3378959f": "orchestration-dependencies-2026-08-20.md:87 - public permalink into "
    "github.com/chrisammon3000/dspy-neo4j-knowledge-graph. [cited]",
    "71335227b801d5ce6c47d50529803a2b8ed5ecefbd998d173d89fcdf734a8bc0": "orchestration-dependencies-2026-08-20.md:90 - public permalink into "
    "github.com/traceloop/opentelemetry-mcp-server. [cited]",
}


def allowlisted(sha: str) -> bool:
    return hashlib.sha256(sha.encode("ascii")).hexdigest() in ALLOWLIST


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        env=GIT_ENV,
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


def scan(paths: list[str]) -> list[tuple[str, set[str]]]:
    """Per file, the ids that do not resolve as a commit here. Read from ROOT, which is the
    tree `tracked_paths` enumerated -- reading a different tree than the one enumerated is the
    same defect class as enumerating a different tree than the one requested."""
    findings: list[tuple[str, set[str]]] = []
    cache: dict[str, bool] = {}
    for relative in paths:
        if relative.startswith(EXEMPT_PREFIXES):
            continue
        path = ROOT / relative
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
            findings.append((relative, foreign))
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
    assert not allowlisted("0" * 40), "an unexamined id must not be allowlisted"
    # The allowlist stores digests precisely so this file cannot trip its own detector.
    for digest in ALLOWLIST:
        assert not SHA_RE.search(digest), "a stored digest must not read as a commit id"
        assert ALLOWLIST[digest].strip(), (
            "every allowlist entry carries a justification"
        )


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
    new = {sha for _, foreign in findings for sha in foreign if not allowlisted(sha)}

    # One line per offending file on BOTH paths, so the total is visible when the gate passes
    # and the ratchet in tests/test_v0_invariants.py reads the true count rather than the
    # remainder. Values stay truncated either way: a script that dumps identifiers into a
    # build log has itself become the leak.
    if findings:
        print(
            f"Foreign commit identifiers in tracked content — {len(new)} not allowlisted"
            " — values are deliberately truncated:"
        )
        for relative, foreign in findings:
            unknown = sum(1 for sha in foreign if not allowlisted(sha))
            mark = f"{unknown} NOT allowlisted" if unknown else "allowlisted"
            print(
                f"- {relative}: {len(foreign)} identifier(s) that do not resolve here,"
                f" {mark}, e.g. {sorted(foreign)[0][:7]}…"
            )
        print()

    if new:
        print(
            "AGENTS.md permits the private corpora's names and AGGREGATE metrics. A list of"
        )
        print("specific commits is neither. Aggregate them, or remove them.")
        print(
            "If one is genuinely benign, test it against both corpora with a scrubbed"
            " environment and add its SHA-256 digest to ALLOWLIST with a reason."
        )
        return 1

    print(
        f"foreign-identifier invariant passes: {len(ALLOWLIST)} allowlisted identifier(s),"
        " 0 unexamined"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""ADR supersession trail: integrity of the tree, and a ratchet on silent edits.

Joe's rule: "Supersede ADRs, never silently edit them. The trail of reversals is the point."
Until this script the rule was documented twice (docs/decisions/README.md,
.agents/skills/writing-adrs/SKILL.md) and enforced by nothing executable.

Two legs:

1. **Trail integrity** (tree, strict): every full supersession pointer resolves to an
   existing ADR; the superseding ADR names the one it supersedes back; every ADR file has a
   row in `index.md`. `SUPERSEDED IN PART` pointers must resolve but need no back-reference
   (the original still stands in part). Duplicate index rows are tolerated — 0002 and 0027
   appear twice by design (highlight section plus their own row). Number collisions are
   already owned by `check_record_numbers.py` and are not re-checked here.

2. **History ratchet** (git): for commits *after* the pin below that touch
   `docs/decisions/NNNN-*.md`, if the parent blob's Status was ACCEPTED or SUPERSEDED and
   the whitespace-insensitive diff deletes or modifies body lines without adding a
   supersession pointer or a dated correction/update marker, the commit fails. Candidates
   at or before the pin are reported, not failed — an ad-hoc scan on 21 Aug 2026 found nine
   candidate commits in existing history, and retroactive punishment is not the rule's point.

    python .github/scripts/check_adr_trail.py            # both legs
    python .github/scripts/check_adr_trail.py --self-test

Standard library only. Exit 0 clean, 1 on a violation, 2 on misuse. Git IO scrubs GIT_* so
a hook's inherited GIT_DIR cannot redirect the history leg at another repository (the same
pattern check_private_corpus.py uses).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DECISIONS = ROOT / "docs" / "decisions"
INDEX = DECISIONS / "index.md"

# The ratchet pin: violations in history at or before this commit are reported, not failed.
# Pinned 21 Aug 2026 when this check landed; the nine known candidates are at or before it.
# GIT_DIR overrides cwd. A git subprocess that inherits it from a hook reads the wrong repo.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

HISTORY_PIN = "1db009b"

ADR_FILE = re.compile(r"^(\d{4})-.+\.md$")
STATUS_LINE = re.compile(r"^\s*-?\s*\*\*Status:?\*\*:?\s*(.+)$", re.IGNORECASE)
SUPERSEDED_FULL = re.compile(r"SUPERSEDED\s+by\s+\[?(\d{4})", re.IGNORECASE)
SUPERSEDED_PART = re.compile(r"SUPERSEDED\s+IN\s+PART\s+by\s+\[?(\d{4})", re.IGNORECASE)
# What legitimises an edit to a settled ADR: a new supersession pointer, or a dated
# correction/update marker quoting the prior text. Heuristic [asserted]: the vocabulary
# below is what this repository's own corrections use.
EDIT_MARKERS = re.compile(r"supersed|update:|corrected|erratum", re.IGNORECASE)


def _adr_files() -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in sorted(DECISIONS.glob("*.md")):
        match = ADR_FILE.match(path.name)
        if match:
            found[match.group(1)] = path
    return found


def _status_of(text: str) -> str:
    for line in text.splitlines()[:10]:
        match = STATUS_LINE.match(line)
        if match:
            return match.group(1)
    return ""


def check_trail_integrity() -> list[str]:
    """Strict tree checks; every violation is one string, file:line where known."""
    problems: list[str] = []
    files = _adr_files()
    index_text = INDEX.read_text(encoding="utf-8") if INDEX.is_file() else ""
    for number, path in files.items():
        text = path.read_text(encoding="utf-8")
        status = _status_of(text)
        target = None
        full = SUPERSEDED_FULL.search(status)
        part = SUPERSEDED_PART.search(status)
        if full:
            target = full.group(1)
            if target not in files:
                problems.append(
                    f"{path.name}: SUPERSEDED by {target}, but no {target}-*.md exists"
                )
            else:
                target_text = files[target].read_text(encoding="utf-8")
                if number not in target_text:
                    problems.append(
                        f"{path.name}: superseded by {target}, but {files[target].name} "
                        f"never names {number} back — the trail is one-way"
                    )
        elif part:
            target = part.group(1)
            if target not in files:
                problems.append(
                    f"{path.name}: SUPERSEDED IN PART by {target}, but no {target}-*.md exists"
                )
        if number not in index_text:
            problems.append(f"{path.name}: no row in index.md — the index has drifted before")
    return problems


def classify_edit(parent_status: str, added: list[str], removed: list[str]) -> str:
    """Pure core of the history leg. 'ok', 'ok-settled-with-marker', or 'violation'.

    A settled ADR (ACCEPTED/SUPERSEDED) whose body lines change is legitimate only when the
    same edit adds a supersession pointer or a dated correction marker.
    """
    settled = bool(re.search(r"ACCEPTED|SUPERSEDED", parent_status, re.IGNORECASE))
    if not settled or not removed:
        return "ok"
    marker_added = any(EDIT_MARKERS.search(line) for line in added)
    return "ok-settled-with-marker" if marker_added else "violation"


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        env=GIT_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )


def check_history() -> tuple[list[str], list[str]]:
    """(reported, failed). Post-pin silent edits of settled ADRs fail; the rest report."""
    log = _git(["log", "--format=%H", "--name-only", "--", "docs/decisions/"])
    if log.returncode != 0:
        return [], [f"git log failed: {log.stderr.strip()[:200]}"]
    pinned = _git(["merge-base", "--is-ancestor", HISTORY_PIN, "HEAD"])
    pin_known = pinned.returncode == 0

    reported: list[str] = []
    failed: list[str] = []
    commits: list[tuple[str, list[str]]] = []
    current: str | None = None
    for line in log.stdout.splitlines():
        if re.fullmatch(r"[0-9a-f]{40}", line):
            current = line
            commits.append((current, []))
        elif line.strip() and current is not None:
            commits[-1][1].append(line.strip())

    for sha, touched in commits:
        adr_paths = [p for p in touched if ADR_FILE.match(Path(p).name)]
        if not adr_paths:
            continue
        for rel in adr_paths:
            parent = _git(["show", f"{sha}^:{rel}"])
            child = _git(["show", f"{sha}:{rel}"])
            if parent.returncode != 0 or child.returncode != 0:
                continue  # added or deleted in this commit; not an edit
            diff = _git(["diff", "--ignore-all-space", f"{sha}^", sha, "--", rel])
            added = [l[1:] for l in diff.stdout.splitlines() if l.startswith("+") and not l.startswith("+++")]
            removed = [l[1:] for l in diff.stdout.splitlines() if l.startswith("-") and not l.startswith("---")]
            verdict = classify_edit(_status_of(parent.stdout), added, removed)
            if verdict != "violation":
                continue
            message = f"{sha[:9]} silently edits settled ADR {rel}"
            ancestor = _git(["merge-base", "--is-ancestor", sha, HISTORY_PIN])
            if pin_known and ancestor.returncode == 0:
                reported.append(message + " (at/before pin — reported)")
            else:
                failed.append(message)
    return reported, failed


def _self_test() -> int:
    ok = True
    cases = [
        ("ACCEPTED", ["body"], ["old body"], "violation"),
        ("ACCEPTED", ["Superseded by 0067"], ["old body"], "ok-settled-with-marker"),
        ("ACCEPTED", ["Update 21 Aug 2026: corrected"], ["old body"], "ok-settled-with-marker"),
        ("PROPOSED", ["anything"], ["old body"], "ok"),
        ("ACCEPTED", ["reworded"], [], "ok"),
    ]
    for status, added, removed, expected in cases:
        got = classify_edit(status, added, removed)
        if got != expected:
            print(f"self-test FAILED: {status}/{added}/{removed} -> {got}, want {expected}",
                  file=sys.stderr)
            ok = False
    print("self-test " + ("passed" if ok else "FAILED"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_adr_trail")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()

    problems = check_trail_integrity()
    reported, failed = check_history()
    for message in reported:
        print(f"reported: {message}")
    for problem in problems:
        print(f"trail: {problem}", file=sys.stderr)
    for message in failed:
        print(f"history: {message}", file=sys.stderr)
    if problems or failed:
        print(
            f"ADR trail invariant FAILED: {len(problems)} trail, {len(failed)} history "
            f"({len(reported)} pre-pin candidates reported)",
            file=sys.stderr,
        )
        return 1
    print(
        f"ADR trail invariant passes ({len(reported)} pre-pin candidate(s) reported, "
        "not failed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

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

2. **History ratchet** (git): accepted/superseded ADRs, settled experiment entries, and
   correction records are protected from silent history edits. Candidates
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

# Advanced from 1db009b to d1c7e9fd by ADR-0110, over exactly one commit.
# d1c7e9fda rewrote ADR-0105 in place, withdrawing a 24 August acceptance claim that
# named no trajectory event. The substance was right -- V0-18 requires the principal as
# author of an event, and there was none -- but it declared nothing, so this checker
# could not tell a correction from a quiet rewrite and refused, correctly.
# The pin means "reviewed and acknowledged", and ADR-0110 is that review.
HISTORY_PIN = "d1c7e9fd"
SETTLED_RECORD_PIN = "27d67a2"

# Commits imported from the public repository's own history on 23 Aug 2026. That repository
# was built as a series of curated tree snapshots — "Publish the verified tree, ..." — and
# shares no ancestor with this one, so `git merge` needed `--allow-unrelated-histories` and
# no such commit can ever be an ancestor of HISTORY_PIN above. A snapshot commit rewrites
# every ADR file wholesale, which this checker correctly reads as a settled-ADR edit.
#
# These are reported, never failed, and the exemption is a fixed list rather than a moved
# pin: moving the pin would silently excuse unrelated commits, whereas naming one sha
# excuses exactly the imported history and nothing else. Adding to this list requires the
# same reasoning recorded beside it.
IMPORTED_PUBLIC_HISTORY = frozenset({"b2e75e7"})

ADR_FILE = re.compile(r"^(\d{4})-.+\.md$")
STATUS_LINE = re.compile(r"^\s*-?\s*\*\*Status:?\*\*:?\s*(.+)$", re.IGNORECASE)
SUPERSEDED_FULL = re.compile(r"SUPERSEDED\s+by\s+\[?(\d{4})", re.IGNORECASE)
SUPERSEDED_PART = re.compile(r"SUPERSEDED\s+IN\s+PART\s+by\s+\[?(\d{4})", re.IGNORECASE)
EXPERIMENT_REGISTER = "docs/10-research/experiment-register.md"
CORRECTION_RECORD = re.compile(r"^docs/00-context/corrections-[^/]+\.md$")
EXPERIMENT_HEADING = re.compile(r"^###\s+(EXP-[A-Za-z0-9_-]+)\b.*$", re.MULTILINE)
SECTION_HEADING = re.compile(r"^#{1,3}(?:\s+|$)", re.MULTILINE)
OUTCOME_MARKER = re.compile(
    r"\b(?:DONE|PASS(?:ED)?|FAIL(?:ED)?|STOPPED|COMPROMISED|FIRED|"
    r"INSUFFICIENT[\s_-]*EVIDENCE|ACCEPTED|REJECTED)\b",
    re.IGNORECASE,
)
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
            problems.append(
                f"{path.name}: no row in index.md — the index has drifted before"
            )
    return problems


def classify_edit(parent_status: str, added: list[str], removed: list[str]) -> str:
    """Pure core of the ADR history leg: 'ok' or 'violation'."""
    settled = bool(re.search(r"ACCEPTED|SUPERSEDED", parent_status, re.IGNORECASE))
    if not settled or not any(line.strip() for line in removed):
        return "ok"
    return "violation"


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


class _BlobResult:
    def __init__(self, returncode: int, stdout: str) -> None:
        self.returncode = returncode
        self.stdout = stdout


def _blob(sha: str, rel: str) -> _BlobResult:
    """Like `_git(["show", ...])`, but for file content a settled-record comparison reads.

    Passing `text=True` to `subprocess.run` always applies universal-newline translation
    with no way to opt out (unlike `open()`, `Popen` takes no `newline` argument) -- so
    \\r\\n silently becomes \\n before this checker ever sees it, making a CRLF-to-LF-only
    mutation of a settled record invisible to every content comparison below. Capturing raw
    bytes and decoding by hand keeps the exact line endings a blob actually carries. Scoped
    to blob reads only: git's own log/diff STRUCTURE (SHAs, name lists, diff headers) is
    parsed elsewhere by `_git` and depends on universal-newline splitting behaving as before.
    [measured 26 August 2026]
    """
    result = subprocess.run(
        ["git", "show", f"{sha}:{rel}"],
        cwd=ROOT,
        env=GIT_ENV,
        capture_output=True,
        timeout=60,
        check=False,
    )
    return _BlobResult(result.returncode, result.stdout.decode("utf-8", errors="replace"))


def _experiment_entries(text: str) -> list[tuple[str, int, str, bool]]:
    """Return (id, ordinal, exact section, settled) for ordered EXP headings."""
    starts = list(EXPERIMENT_HEADING.finditer(text))
    boundaries = [match.start() for match in SECTION_HEADING.finditer(text)]
    ordinals: dict[str, int] = {}
    entries: list[tuple[str, int, str, bool]] = []
    for start in starts:
        end = next((point for point in boundaries if point > start.start()), len(text))
        experiment_id = start.group(1)
        ordinals[experiment_id] = ordinals.get(experiment_id, 0) + 1
        statuses = re.findall(r"`([^`]+)`", start.group(0))
        entries.append(
            (
                experiment_id,
                ordinals[experiment_id],
                text[start.start() : end],
                bool(statuses and OUTCOME_MARKER.search(statuses[-1])),
            )
        )
    return entries


def _settled_experiment_violation(parent: str, child: str) -> str | None:
    """A settled entry is identified by (id, ordinal) -- the Nth heading with that id --
    never by its raw position in the file. Matching by file position let a prior entry
    with the same id inserted ahead of a settled one silently take over that position,
    while the untouched settled text merely shifted down: exactly the "replace via a
    prior entry" laundering this check exists to catch. [measured 25 August 2026]
    """
    parent_entries = _experiment_entries(parent)
    child_by_key = {
        (experiment_id, ordinal): entry
        for experiment_id, ordinal, entry, _ in _experiment_entries(child)
    }
    for experiment_id, ordinal, entry, settled in parent_entries:
        if not settled:
            continue
        child_entry = child_by_key.get((experiment_id, ordinal))
        if child_entry is None or not child_entry.startswith(entry):
            return f"{experiment_id}#{ordinal}"
    return None


def _correction_line(parent: str, child: str) -> int:
    # keepends=True: a bare .splitlines() discards \r\n/\n entirely, so a CRLF-to-LF-only
    # mutation compares as identical line-for-line and this reports EOF (past the last real
    # line) instead of the true first differing line. [measured 26 August 2026]
    parent_lines = parent.splitlines(keepends=True)
    child_lines = child.splitlines(keepends=True)
    for index, line in enumerate(parent_lines):
        if index >= len(child_lines) or child_lines[index] != line:
            return index + 1
    return len(parent_lines) + 1


def _record_kind(rel: str) -> str | None:
    if rel == EXPERIMENT_REGISTER:
        return "experiment"
    if CORRECTION_RECORD.fullmatch(rel):
        return "correction"
    if rel.startswith("docs/decisions/") and ADR_FILE.match(Path(rel).name):
        return "adr"
    return None


def _at_or_before(sha: str, pin: str, pin_known: bool) -> bool:
    return pin_known and _git(["merge-base", "--is-ancestor", sha, pin]).returncode == 0


def check_history() -> tuple[list[str], list[str]]:
    """(reported, failed). Post-pin silent edits of protected records fail."""
    log = _git(
        [
            "log",
            "--format=%H",
            "--name-only",
            "--",
            "docs/decisions/",
            EXPERIMENT_REGISTER,
            ":(glob)docs/00-context/corrections-*.md",
        ]
    )
    if log.returncode != 0:
        return [], [f"git log failed: {log.stderr.strip()[:200]}"]
    pinned = _git(["merge-base", "--is-ancestor", HISTORY_PIN, "HEAD"])
    pin_known = pinned.returncode == 0
    settled_pinned = _git(
        ["merge-base", "--is-ancestor", SETTLED_RECORD_PIN, "HEAD"]
    )
    settled_pin_known = settled_pinned.returncode == 0

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
        adr_paths = [
            p
            for p in touched
            if _record_kind(p) is not None or p.startswith("docs/decisions/")
        ]
        if not adr_paths:
            continue
        for rel in adr_paths:
            kind = _record_kind(rel)
            parent = _blob(f"{sha}^", rel)
            child = _blob(sha, rel)
            if kind == "experiment":
                if parent.returncode == 0:
                    locator = _settled_experiment_violation(
                        parent.stdout, child.stdout if child.returncode == 0 else ""
                    )
                    if locator is not None:
                        message = f"{sha} silently edits settled experiment {rel} {locator}"
                        if _at_or_before(
                            sha, SETTLED_RECORD_PIN, settled_pin_known
                        ):
                            reported.append(message + " (at/before pin — reported)")
                        else:
                            failed.append(message)
                continue
            if kind == "correction":
                child_text = child.stdout if child.returncode == 0 else ""
                if parent.returncode == 0 and not child_text.startswith(parent.stdout):
                    locator = f"correction line {_correction_line(parent.stdout, child_text)}"
                    message = f"{sha} silently edits correction record {rel} {locator}"
                    if _at_or_before(sha, SETTLED_RECORD_PIN, settled_pin_known):
                        reported.append(message + " (at/before pin — reported)")
                    else:
                        failed.append(message)
                continue
            if (
                parent.returncode != 0
                and child.returncode == 0
                and (kind == "adr" or rel.startswith("docs/decisions/"))
            ):
                names = _git(["diff-tree", "--no-commit-id", "-r", "--name-status", "-M", sha])
                for line in names.stdout.splitlines():
                    status, *paths = line.split("\t")
                    if status.startswith("R") and len(paths) == 2 and paths[1] == rel:
                        old_rel = paths[0]
                        if _record_kind(old_rel) == "adr":
                            kind = "adr"
                            rel = old_rel
                            parent = _blob(f"{sha}^", rel)
                            child = _blob(sha, rel)
                        break
            if kind is None:
                continue
            if parent.returncode != 0:
                continue  # a new ADR has no prior text to protect
            if child.returncode != 0:
                added = []
                removed = ["deleted"]
            else:
                diff = _git(["diff", "--ignore-all-space", f"{sha}^", sha, "--", rel])
                added = [
                    ln[1:]
                    for ln in diff.stdout.splitlines()
                    if ln.startswith("+") and not ln.startswith("+++")
                ]
                removed = [
                    ln[1:]
                    for ln in diff.stdout.splitlines()
                    if ln.startswith("-") and not ln.startswith("---")
                ]
            marker_added = any(EDIT_MARKERS.search(line) for line in added)
            verdict = classify_edit(_status_of(parent.stdout), added, removed)
            if verdict != "violation":
                continue
            message = f"{sha[:9]} silently edits settled ADR {rel}"
            pin = SETTLED_RECORD_PIN if marker_added else HISTORY_PIN
            known = settled_pin_known if marker_added else pin_known
            ancestor = _git(["merge-base", "--is-ancestor", sha, pin])
            if any(sha.startswith(known) for known in IMPORTED_PUBLIC_HISTORY):
                reported.append(message + " (imported public snapshot — reported)")
            elif known and ancestor.returncode == 0:
                reported.append(message + " (at/before pin — reported)")
            else:
                failed.append(message)
    return reported, failed


def _self_test() -> int:
    ok = True
    cases = [
        ("ACCEPTED", ["body"], ["old body"], "violation"),
        ("ACCEPTED", ["Superseded by 0067"], ["old body"], "violation"),
        (
            "ACCEPTED",
            ["Update 21 Aug 2026: corrected"],
            ["old body"],
            "violation",
        ),
        ("PROPOSED", ["anything"], ["old body"], "ok"),
        ("ACCEPTED", ["reworded"], [], "ok"),
    ]
    for status, added, removed, expected in cases:
        got = classify_edit(status, added, removed)
        if got != expected:
            print(
                f"self-test FAILED: {status}/{added}/{removed} -> {got}, want {expected}",
                file=sys.stderr,
            )
            ok = False
    record_cases = [
        (
            "### EXP-1 — test `DONE`\n\nresult\n",
            "### EXP-1 — test `DONE`\n\nresult\n\n### EXP-2 — next `READY`\n",
            None,
        ),
        (
            "### EXP-1 — test `DONE`\n\nresult\n",
            "### EXP-1 — test `DONE`\n\nrewrite\n",
            "EXP-1#1",
        ),
        (
            "### EXP-1 — test `READY`\n\ndraft\n",
            "### EXP-1 — test `READY`\n\nrevised\n",
            None,
        ),
    ]
    for parent, child, expected in record_cases:
        got = _settled_experiment_violation(parent, child)
        if got != expected:
            print(f"self-test FAILED: experiment -> {got}, want {expected}", file=sys.stderr)
            ok = False
    if _correction_line("first\nsecond\n", "first\nrewrite\n") != 2:
        print("self-test FAILED: correction locator", file=sys.stderr)
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

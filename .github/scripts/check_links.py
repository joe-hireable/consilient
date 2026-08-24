"""C4 — refuse a relative markdown link that resolves to nothing.

`docs/20-design/documentation-and-surfaces-plan-2026-08-23.md` §"The anti-drift
mechanism" specifies this check and its order: it ships **before** the file
migration, not after, so the migration is performed against a gate that can see
what it breaks. The audit that specified it measured the live 404 at the end of
the contributor path -- `docs/00-context/ways-to-contribute.md` -> `../CONTRIBUTING.md`
-> `docs/CONTRIBUTING.md`, absent. [measured]

Measured on this tree, 24 August 2026: 337 tracked markdown files, 304 relative
links, of which **6 occurrences do not resolve** -- 3 to a missing file (two of
them the same target cited twice) and 3 to a heading that has since been
reworded, so 5 distinct source/target pairs. Every one is in a file this unit
does not own, so they are listed in `KNOWN_BROKEN` with the reason. [measured]

**The allowlist may only shrink, and it is checked in both directions.** A new
broken link fails, and an allowlisted link that has been fixed *also* fails, with
"remove it". A one-way allowlist (the `.class-backfill` shape this plan uses for
C2) permits a fixed entry to sit there forever, and a stale exemption is
indistinguishable from an unfixed defect at the point where someone reads it.

What is checked, and why that is the bar
----------------------------------------
The incumbents are `lycheeverse/lychee` (Rust, HTTP + filesystem + fragments) and
`tcort/markdown-link-check` (npm, HTTP + filesystem + fragments), both retrieved
24 August 2026. [cited] Either would do this job. Neither is used, for reasons
that are about this repository and not about their quality: both are new
dependencies -- one Rust binary or one npm tree in a Python project whose
`pyproject.toml` declares zero runtime dependencies and whose AGENTS.md makes
adding one an ask -- and both are network-capable, so their headline feature is
the one thing a gate here must not do. This file is offline by construction: it
cannot check an `http(s)` target because it never opens a socket, and it says so
rather than implying coverage it does not have.

So: **equal to the incumbents on relative links and heading fragments, narrower
on HTTP (deliberately), and ahead of both on two classes** -- a `#L12-L34` range
extending past the end of its target, and a target that exists on this disk but
is not tracked by git. Both resolve on the author's machine and 404 for every
reader: `.harness/` is gitignored here, and Windows resolves a wrong-case name to
the right file while GitHub does not. Neither lychee nor markdown-link-check
consults the tracked set. [cited, retrieved 24 August 2026]

Measured on this tree: 0 occurrences of either today, so this is a ratchet
against a class that has not yet fired, not a repair. [measured] A correct
standard answer would have been to vendor lychee; the delta that justifies not
doing so is the dependency and the socket, not cleverness.

Re-check the bar when: a dependency is admitted for another reason, or link rot
appears in a class this cannot see (see "What this does not check").

What this does not check
------------------------
- **`http(s)` targets.** No network, by design. Nothing here reports on them, so
  nothing here should be read as evidence about them.
- **A line range that still resolves but now points at different code.** Only a
  range extending past the end of the file is detectable without hashing the
  cited text, and hashing it would make every edit above it a failure.
- **Anchor generation exactly as GitHub does it.** The slug rule below is the
  documented lowercase/strip/space-to-hyphen behaviour and matches all 7 heading
  fragments on this tree; it does not implement duplicate-heading `-1` suffixes.
  A heading fragment that fails only because of that is a false positive, and
  should be fixed here rather than allowlisted.

Usage:
  python .github/scripts/check_links.py
  python .github/scripts/check_links.py --self-test
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]

# Git exports GIT_DIR, GIT_INDEX_FILE and GIT_WORK_TREE into every hook it runs, and GIT_DIR
# overrides cwd. Measured 21 August 2026 in check_private_corpus.py: an unscrubbed
# `git ls-files` read the hook's repository instead of the tree it was pointed at, and the
# gate reported on a tree it had never opened. Every git subprocess here runs without them.
GIT_ENV = {
    key: value for key, value in os.environ.items() if not key.startswith("GIT_")
}

# Inline links only: this corpus has no reference-style definitions and no images
# with relative targets [measured, 24 August 2026]. `(?<!!)` drops image syntax.
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(\s*<?([^)>\s]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
# A scheme (http:, mailto:, and a bare Windows drive letter) is not ours to resolve.
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
LINE_RANGE = re.compile(r"^L([0-9]+)(?:-L([0-9]+))?$")

# Broken on this tree, each in a file W07 does not own. May only shrink; a fixed
# entry left here fails just as loudly as a new break.
KNOWN_BROKEN: dict[tuple[str, str], str] = {
    (
        "docs/00-context/ways-to-contribute.md",
        "../CONTRIBUTING.md",
    ): "the measured contributor 404; the plan's unit 7 migration fixes it when it moves this file to docs/05-guide/",
    (
        "docs/decisions/0064-add-training-providers-and-supersede-openrouter-as-sole-metered-vendor.md",
        "0044-openrouter-is-the-only-metered-vendor.md",
    ): "ADR-0044 was renamed to 0044-openrouter-is-the-only-metered-vendor-and-budgets-are-a-capability.md; two links in the superseding ADR still carry the old name",
    (
        "docs/superpowers/specs/2026-08-23-effort-allocation.md",
        "../../10-research/experiment-register.md#exp-133--does-an-8020-decision-first-budget-beat-threshold-triggered-allocation-the-inverse-and-superpowers-at-equal-total-budget-blocked",
    ): "EXP-133's heading was reworded after the spec cited it",
    (
        "docs/superpowers/specs/2026-08-23-effort-allocation.md",
        "../../10-research/experiment-register.md#exp-134--does-frontier-supervision-of-weaker-execution-match-frontier-direct-quality-at-lower-frontier-cost-blocked",
    ): "EXP-134's heading was reworded after the spec cited it",
    (
        "docs/superpowers/specs/2026-08-23-orchestration-liveness.md",
        "../../10-research/experiment-register.md#exp-138--does-evidence-consuming-supervision-reduce-actionable-stall-exposure-and-avoidable-silence",
    ): "EXP-138's heading was reworded after the spec cited it",
}


def link_targets(text: str) -> list[str]:
    """Every relative link target in one document, in order. Pure."""
    return [
        target
        for target in LINK.findall(text)
        if target and not target.startswith(("#", "//")) and not SCHEME.match(target)
    ]


def slug(heading: str) -> str:
    """GitHub's anchor for a heading line: lowercase, strip punctuation, spaces to hyphens."""
    text = heading.lstrip("#").strip().lower()
    return re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).replace(" ", "-")


def anchors(text: str) -> set[str]:
    return {slug(line) for line in text.splitlines() if line.startswith("#")}


def failure(
    source: Path, target: str, *, root: Path, tracked: frozenset[str]
) -> str | None:
    """Why this link does not resolve, or None if it does. `source` is the linking file."""
    path_part, _, fragment = target.partition("#")
    destination = (
        (source.parent / unquote(path_part)).resolve() if path_part else source
    )
    if not destination.exists():
        return "no such file"
    if not destination.is_dir():
        # Existing on this disk is not existing in the repository. `.harness/` is
        # gitignored here, and Windows resolves a wrong-case name to the right file,
        # so both classes pass a filesystem check and 404 for every reader. Neither
        # lychee nor markdown-link-check looks at the tracked set. [cited, 24 Aug 2026]
        try:
            relative = destination.relative_to(root).as_posix()
        except ValueError:
            return "outside the repository"
        if relative not in tracked:
            return "not tracked by git (resolves on this disk, 404 in the repository)"
    if not fragment or destination.is_dir():
        return None
    line_range = LINE_RANGE.match(fragment)
    body = destination.read_text(encoding="utf-8", errors="replace")
    if line_range:
        last = int(line_range.group(2) or line_range.group(1))
        length = len(body.splitlines())
        return (
            None if last <= length else f"line {last} past end of file ({length} lines)"
        )
    if destination.suffix != ".md":
        return None
    return None if unquote(fragment) in anchors(body) else "no such heading"


def scan(
    paths: list[str], root: Path, tracked: frozenset[str] | None = None
) -> list[tuple[str, str, str]]:
    """(source, target, reason) for every relative link that does not resolve.

    `tracked` is the repository's tracked set; it defaults to `paths`, which is
    what the self-test wants and never what the real run wants.
    """
    known = frozenset(paths) if tracked is None else tracked
    found = []
    for relative in paths:
        source = root / relative
        try:
            text = source.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            # Not `continue`: a tracked file this gate cannot open is a file it did
            # not check, and a gate that silently no-ops is worse than no gate.
            found.append((relative.replace("\\", "/"), "", f"unreadable: {error}"))
            continue
        for target in link_targets(text):
            reason = failure(source, target, root=root, tracked=known)
            if reason is not None:
                found.append((relative.replace("\\", "/"), target, reason))
    return found


def self_test() -> None:
    """The detector must fire on a synthetic tree, or a green run proves nothing."""
    assert link_targets(
        "[a](b.md) [x](http://e) [y](#h) ![i](p.png) [z](mailto:a@b)"
    ) == ["b.md"]
    assert slug("### EXP-133 · Does it? `BLOCKED: x`") == "exp-133--does-it-blocked-x"
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "b.md").write_text("# A Head\nsecond\n", encoding="utf-8")
        (root / "untracked.md").write_text("# on disk only\n", encoding="utf-8")
        (root / "a.md").write_text(
            "[ok](b.md)\n[gone](nope.md)\n[head](b.md#a-head)\n"
            "[wrong](b.md#no-head)\n[range](b.md#L2)\n[over](b.md#L9)\n"
            "[ignored](untracked.md)\n",
            encoding="utf-8",
        )
        expected = [
            ("a.md", "nope.md", "no such file"),
            ("a.md", "b.md#no-head", "no such heading"),
            ("a.md", "b.md#L9", "line 9 past end of file (2 lines)"),
            (
                "a.md",
                "untracked.md",
                "not tracked by git (resolves on this disk, 404 in the repository)",
            ),
        ]
        found = scan(["a.md"], root, frozenset({"a.md", "b.md"}))
        assert found == expected, found
        assert scan(["b.md"], root, frozenset({"a.md", "b.md"})) == []


def tracked(*pattern: str) -> list[str]:
    """Tracked paths, repository-relative. Empty pattern means all.

    `-z` because `git ls-files` otherwise C-quotes any path with a non-ASCII
    character, and a quoted path does not open -- which would have been a file
    skipped rather than a file checked.
    """
    completed = subprocess.run(
        ["git", "ls-files", "-z", *pattern],
        cwd=ROOT,
        env=GIT_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "cannot enumerate tracked files")
    return [entry for entry in completed.stdout.split("\0") if entry]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="C4: relative markdown links resolve")
    parser.add_argument(
        "--self-test", action="store_true", help="prove the detector still detects"
    )
    args = parser.parse_args()
    if args.self_test:
        self_test()

    paths = tracked("*.md")
    found = scan(paths, ROOT, frozenset(tracked()))
    broken = {(source, target): reason for source, target, reason in found}
    new = {key: reason for key, reason in broken.items() if key not in KNOWN_BROKEN}
    stale = [key for key in KNOWN_BROKEN if key not in broken]

    if new:
        print(
            f"Relative markdown links that do not resolve — {len(new)} not allowlisted:"
        )
        for (source, target), reason in sorted(new.items()):
            print(f"- {source}: {target} — {reason}")
        print(
            "\nFix the link, or -- if the target is genuinely still to be moved -- add it to\n"
            "KNOWN_BROKEN in this file with the reason and who owns the fix."
        )
    if stale:
        print(f"KNOWN_BROKEN lists {len(stale)} link(s) that now resolve:")
        for source, target in sorted(stale):
            print(f"- {source}: {target}")
        print(
            "\nRemove them. The list may only shrink; an exemption for a defect that is\n"
            "fixed reads as an unfixed defect to the next person who opens this file."
        )
    if new or stale:
        return 1

    print(
        f"link invariant passes: {len(paths)} tracked markdown file(s), "
        f"{len(KNOWN_BROKEN)} allowlisted broken link(s), 0 unexamined. "
        "http(s) targets are not checked: this gate opens no socket."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Z04 — mutable harness state and nested source copies stay off the index.

MEASURED 24 August 2026: `git ls-files .harness` returned `driver-state.json`
(the authoritative scheduling record), `plan-units.json`, a lock file,
`build-loop.*`, and two complete extra copies of `src/consilient/` — so it
returned three `consilient/events.py`. A checkout silently restored an older
`plan-units.json` and dropped a queued unit. `.harness/log/` was already
gitignored and never suffered this.

The files stay on disk. The index must not carry them. A chokepoint without
the check that enforces it is not a chokepoint (working principle 3); this
is that check, following the ADR-0057 `git ls-files` ratchet.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Names that decide what the driver dispatches, or that a checkout must never
# restore. The unit names these exactly. STOP-LOOP, board-snapshot.json and
# gate-specs.json are the same class: a checkout that restores them asserts a
# machine-local fact about a different moment.
FORBIDDEN_BASENAMES = frozenset(
    {
        "driver-state.json",
        "plan-units.json",
        "STOP-LOOP",
        "board-snapshot.json",
        "gate-specs.json",
    }
)

# Source and documentation the unit says must stay tracked. A blanket
# `.harness/` ignore would drop these; that is the MUST NOT.
REQUIRED_HARNESS_SOURCE = (
    ".harness/HANDOFF.md",
    ".harness/build_driver.py",
    ".harness/build_loop.py",
    ".harness/board_snapshot.py",
)

# DONE WHEN: `git ls-files .harness` returns only source and documentation.
# The named denylist is not enough — it left generated scratch and a JSONL
# log tracked after the first Z04 commit. An allowlist is the ADR-0057 shape.
ALLOWED_HARNESS_TRACKED = frozenset(
    {
        ".harness/HANDOFF.md",
        ".harness/STOP-PUBLISH.lifted-20260824-joe-authorised",
        ".harness/STOP-PUBLISH.lifted-20260829-joe-authorised",
        ".harness/allowed-cwds.example.json",
        ".harness/board_snapshot.py",
        ".harness/build_board.py",
        ".harness/build_driver.py",
        ".harness/build_loop.py",
        ".harness/build_loop_git.py",
        ".harness/build_loop_housekeeping.py",
        ".harness/integrate_when_quiet.sh",
        ".harness/limits.example.json",
        ".harness/permissions.example.json",
        ".harness/publish_when_integrated.sh",
        ".harness/resume_loop.py",
    }
)

# Tracked when it exists, and absent the rest of the time. The live publication hold is a
# governance record like the lifted marker beside it -- an orchestrator re-imposed one on
# 29 August 2026 and it belongs in the history -- but a hold is LIFTED by renaming it to
# `STOP-PUBLISH.lifted-<date>-<who>`, so requiring it to be tracked would make lifting it fail
# this test. Allowed, never required. Tracking it is also the fail-safe direction: an old
# checkout that restores the hold blocks a publish, where restoring only a lifted marker
# permits one.
OPTIONAL_HARNESS_TRACKED = frozenset({".harness/STOP-PUBLISH"})

BLANKET_HARNESS_IGNORES = frozenset(
    {
        ".harness",
        ".harness/",
        ".harness/*",
        ".harness/**",
    }
)

# Patterns the plan named, plus the same-class lines already in .gitignore.
# Deleting any of them makes an ordinary `git add` able to re-track the path.
REQUIRED_GITIGNORE = (
    ".harness/driver-state.json",
    ".harness/plan-units.json",
    ".harness/driver-tick.lock",
    ".harness/*.lock",
    ".harness/build-loop.out",
    ".harness/build-loop.err",
    ".harness/build-loop.*",
    ".harness/**/src/consilient/",
    ".harness/STOP-LOOP",
    ".harness/board-snapshot.json",
    ".harness/build-board.html",
    ".harness/exp79-scratch/",
    ".harness/exp130-out.txt",
    ".harness/exp130-scratch/",
    ".harness/fallback-result.json",
    ".harness/stray-debris-*/",
    ".harness/gate-specs.json",
    # The two trees that actually held extra copies of src/consilient/,
    # plus the orch- prefix measured beside them. **/src/consilient/
    # covers future copies; these cover the measured locations.
    ".harness/exp-s02-audit-*/",
    ".harness/orch-*/",
    ".harness/s02-mut-*/",
)

# Paths the unit said `git ls-files .harness` must never return. Used for
# `git check-ignore --no-index` so the probe works even when the file is
# absent from this worktree.
READD_PROBES = (
    ".harness/driver-state.json",
    ".harness/plan-units.json",
    ".harness/driver-tick.lock",
    ".harness/build-loop.out",
    ".harness/build-loop.err",
    ".harness/exp-s02-audit-probe/src/consilient/events.py",
    ".harness/s02-mut-probe/src/consilient/events.py",
)


def _posix_git_dir(raw: str) -> str:
    """Resolve a worktree `gitdir:` pointer on this runtime.

    Linked worktrees created on Windows store `gitdir: C:/...`. WSL git then
    treats that as a relative path and looks under the worktree for `C:/...`
    [measured in this worktree]. Translate only when the Windows spelling is
    not already a directory here and the `/mnt/<drive>/` form is.
    """
    if Path(raw).is_dir():
        return raw
    if len(raw) >= 3 and raw[1] == ":" and raw[0].isalpha():
        translated = Path(f"/mnt/{raw[0].lower()}{raw[2:].replace('\\', '/')}")
        if translated.is_dir():
            return str(translated)
    return raw


def _git_env() -> dict[str, str]:
    # A hook's inherited GIT_DIR once redirected a repository check at another
    # repository; the scrub is the same pattern check_private_corpus.py uses.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    pointer = ROOT / ".git"
    if pointer.is_file():
        for line in pointer.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("gitdir:"):
                env["GIT_DIR"] = _posix_git_dir(line.split(":", 1)[1].strip())
                env["GIT_WORK_TREE"] = str(ROOT)
                break
    return env


def _git(
    *args: str,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env or _git_env(),
        check=check,
    )


def _tracked_harness(env: dict[str, str] | None = None) -> list[str]:
    result = _git("ls-files", "-z", "--", ".harness", env=env)
    return [path for path in result.stdout.split("\0") if path]


def _is_forbidden(path: str) -> bool:
    name = Path(path).name
    if name in FORBIDDEN_BASENAMES:
        return True
    if name.endswith(".lock"):
        return True
    if name.startswith("build-loop."):
        return True
    parts = Path(path).parts
    try:
        src_at = parts.index("src")
    except ValueError:
        return False
    return src_at + 1 < len(parts) and parts[src_at + 1] == "consilient"


def _is_lifted_publication_hold(path: str) -> bool:
    """A lift renames STOP-PUBLISH; the new name is still a governance record.

    Listing each lift in ALLOWED_HARNESS_TRACKED made the next lift fail CI,
    which is the same trap OPTIONAL_HARNESS_TRACKED exists to avoid for the
    unlifted hold. Known lifts stay in the allowlist so they remain required;
    a future lift is allowed, never required.
    """
    return Path(path).name.startswith("STOP-PUBLISH.lifted-")


def _gitignore_patterns() -> list[str]:
    patterns: list[str] = []
    for raw in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return patterns


def test_mutable_harness_state_is_not_tracked() -> None:
    """`git ls-files .harness` must not return driver state, locks, loop I/O, or nested source."""
    tracked = _tracked_harness()
    leaked = [path for path in tracked if _is_forbidden(path)]
    assert leaked == [], (
        "mutable harness state is tracked and a checkout can restore an older "
        f"copy: {leaked}. `git rm --cached` the path; do not delete it from disk."
    )


def test_harness_source_stays_tracked() -> None:
    """HANDOFF and the driver scripts are source, not instance data."""
    tracked = set(_tracked_harness())
    missing = [path for path in REQUIRED_HARNESS_SOURCE if path not in tracked]
    assert missing == [], (
        "a blanket .harness/ ignore (or an over-broad untrack) dropped source "
        f"that must stay tracked: {missing}"
    )


def test_harness_index_is_source_and_documentation_only() -> None:
    """`git ls-files .harness` must return only source and documentation."""
    tracked = set(_tracked_harness())
    unexpected = sorted(
        path
        for path in tracked
        if path not in ALLOWED_HARNESS_TRACKED
        and path not in OPTIONAL_HARNESS_TRACKED
        and not _is_lifted_publication_hold(path)
    )
    assert unexpected == [], (
        "git ls-files .harness returned instance data; a checkout can restore "
        f"it: {unexpected}. `git rm --cached` the path; do not delete it from disk."
    )
    missing = sorted(ALLOWED_HARNESS_TRACKED - tracked)
    assert missing == [], (
        "a blanket .harness/ ignore (or an over-broad untrack) dropped source "
        f"that must stay tracked: {missing}"
    )


def test_an_optional_tracked_path_is_never_also_required() -> None:
    """The point of OPTIONAL_HARNESS_TRACKED is that its absence is legal.

    A path listed in both sets would be required by the `missing` half of the check above, which
    is exactly the trap this set exists to avoid: the publication hold is lifted by renaming it,
    so a rule requiring it to be tracked would make lifting the hold fail CI, and the obvious
    way out of that would be to leave the hold in place. A guard that punishes the correct
    action is worse than no guard.
    """
    both = sorted(ALLOWED_HARNESS_TRACKED & OPTIONAL_HARNESS_TRACKED)
    assert both == [], (
        f"{both} is listed as both required and optional, so removing it fails the "
        "index check even though the whole point of the optional set is that it may go"
    )


def test_gitignore_names_the_mutable_paths_and_is_not_a_blanket() -> None:
    patterns = _gitignore_patterns()
    missing = [pattern for pattern in REQUIRED_GITIGNORE if pattern not in patterns]
    assert missing == [], (
        "gitignore is missing the Z04 ignore that stops the path being "
        f"re-added by an ordinary git add: {missing}"
    )
    blanket = [pattern for pattern in patterns if pattern in BLANKET_HARNESS_IGNORES]
    assert blanket == [], (
        "gitignore blanket-ignores .harness/; HANDOFF.md and the driver "
        f"scripts would drop out of the index: {blanket}"
    )


def test_gitignore_blocks_readding_the_named_mutable_paths() -> None:
    """An ordinary `git add` of a named instance path must be a no-op.

    `git check-ignore --no-index` is the probe that works whether or not the
    file is on disk in this worktree. Exit 0 means ignored.
    """
    missed = []
    for probe in READD_PROBES:
        result = _git("check-ignore", "-q", "--no-index", "--", probe, check=False)
        if result.returncode != 0:
            missed.append(probe)
    assert missed == [], (
        "gitignore does not ignore these paths; an ordinary git add would "
        f"re-track them and a checkout could restore an older copy: {missed}"
    )


def test_readding_a_forbidden_path_fails_the_index_check(tmp_path: Path) -> None:
    """DONE WHEN: the new test fails when any untracked path is re-added.

    Uses a throwaway index so the real index is never touched. An ordinary
    add must not stage the path; a force-add must then be caught by the
    denylist that `test_mutable_harness_state_is_not_tracked` runs.
    """
    probe = ".harness/plan-units.json"
    if not (ROOT / probe).is_file():
        pytest.skip(
            "no on-disk instance copy to force-add; "
            "test_gitignore_blocks_readding_the_named_mutable_paths covers the gitignore half"
        )
    env = _git_env()
    env["GIT_INDEX_FILE"] = str(tmp_path / "index")
    _git("read-tree", "HEAD", env=env)
    ordinary = _git("add", "--", probe, env=env, check=False)
    assert ordinary.returncode != 0, (
        f"ordinary git add of {probe} succeeded; gitignore is not blocking re-add"
    )
    assert probe not in _tracked_harness(env), (
        f"ordinary git add re-tracked {probe}; gitignore is not blocking re-add"
    )
    _git("add", "-f", "--", probe, env=env)
    leaked = [path for path in _tracked_harness(env) if _is_forbidden(path)]
    assert probe in leaked, (
        f"force-adding {probe} did not fire the denylist; the ls-files "
        "ratchet would stay green after a re-add"
    )

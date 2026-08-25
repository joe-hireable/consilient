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

ROOT = Path(__file__).resolve().parent.parent

# Names that decide what the driver dispatches, or that a checkout must never
# restore. The unit names these exactly.
FORBIDDEN_BASENAMES = frozenset(
    {
        "driver-state.json",
        "plan-units.json",
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

BLANKET_HARNESS_IGNORES = frozenset(
    {
        ".harness",
        ".harness/",
        ".harness/*",
        ".harness/**",
    }
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


def _tracked_harness() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", ".harness"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_git_env(),
        check=True,
    )
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


def test_gitignore_names_the_mutable_paths_and_is_not_a_blanket() -> None:
    patterns = _gitignore_patterns()
    required = (
        ".harness/driver-state.json",
        ".harness/plan-units.json",
        ".harness/*.lock",
        ".harness/build-loop.out",
        ".harness/build-loop.err",
        ".harness/**/src/consilient/",
    )
    missing = [pattern for pattern in required if pattern not in patterns]
    assert missing == [], (
        "gitignore is missing the Z04 ignore that stops the path being "
        f"re-added by an ordinary git add: {missing}"
    )
    blanket = [pattern for pattern in patterns if pattern in BLANKET_HARNESS_IGNORES]
    assert blanket == [], (
        "gitignore blanket-ignores .harness/; HANDOFF.md and the driver "
        f"scripts would drop out of the index: {blanket}"
    )

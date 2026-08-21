"""Pre-commit execution for the commit-attribution gate. This is what git runs.

Policy lives in `consilient.commit_gate` (AST-locked: no subprocess, no
environment reads). This script does the IO: enumerate the staged set, read the
trajectory logs of this repository's worktrees, take the committer identity
from the environment, and refuse by exit code. Wired in by the tracked
`.githooks/pre-commit`; installed per clone by `scripts/install_hooks.py`.

    CONSILIENT_RUN_ID=<run id or name> git commit ...
    CONSILIENT_RUN_ID=<run id> CONSILIENT_COMMIT_PATHS=a.py,b.py git commit ...

A refusal is the mechanism working, not an error: unstage what is not yours,
or name yourself. `--no-verify` remains the escape hatch, as with the secrets
stage.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient import coordination  # noqa: E402
from consilient.commit_gate import (  # noqa: E402
    PATHS_ENV,
    RUN_ID_ENV,
    Refusal,
    check_commit,
)
from consilient.events import read_all  # noqa: E402

GIT_TIMEOUT_S = 30


def _git(cwd: Path, *args: str) -> str | None:
    """Run git and return stdout, or None if git cannot answer."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout or ""


def _worktree_root(cwd: Path) -> Path:
    top = _git(cwd, "rev-parse", "--show-toplevel")
    if top is None or not top.strip():
        return cwd.resolve()
    return Path(top.strip()).resolve()


def _staged(root: Path) -> list[str] | None:
    """The staged set, NUL-separated so quoting never lies. None means git failed."""
    out = _git(root, "diff", "--cached", "--name-only", "-z")
    if out is None:
        return None
    return [entry for entry in out.split("\0") if entry.strip()]


def _worktree_roots(root: Path) -> list[Path]:
    """Every worktree of this repository, so claims recorded by a dispatcher
    running in a different checkout of the same repository are still seen.
    Best-effort: if git cannot list them, this worktree alone is checked."""
    roots = [root]
    listing = _git(root, "worktree", "list", "--porcelain")
    if listing is None:
        return roots
    for line in listing.splitlines():
        if not line.startswith("worktree "):
            continue
        candidate = Path(line[len("worktree ") :].strip())
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_dir() and resolved not in roots:
            roots.append(resolved)
    return roots


def main() -> int:
    root = _worktree_root(Path(os.getcwd()))
    staged = _staged(root)
    if staged is None:
        # A gate that cannot see the staged set cannot check attribution. Fail
        # closed: a missing checker counted as a pass is the ADR-0065 lesson.
        print(
            "pre-commit: REFUSED — could not enumerate the staged set "
            "(git diff --cached failed). Nothing was committed.",
            file=sys.stderr,
        )
        return 1
    events = []
    for base in _worktree_roots(root):
        log = base / ".harness" / "log"
        if log.is_dir():
            found, _rejected = read_all(log)
            events.extend(found)
    live = coordination.live_claims(events, now=datetime.now(timezone.utc))
    raw_paths = os.environ.get(PATHS_ENV)
    declared = (
        [entry for entry in raw_paths.split(",") if entry.strip()]
        if raw_paths is not None
        else None
    )
    decision = check_commit(
        staged=staged,
        live=live,
        worktree=root,
        run_id=os.environ.get(RUN_ID_ENV),
        declared=declared,
    )
    if isinstance(decision, Refusal):
        print(f"pre-commit: REFUSED — {decision.reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Repair the repository's git state, and dispose of the worktrees that hold nothing.

Two jobs that look unrelated and are not: both act on git's own bookkeeping rather than
on the build. `self_heal` clears the faults that blind every git command at once -- a
WSL path written into the shared config, a vanished worktree administrative directory, a
stale index.lock that no live process holds, long-path support missing from the global
config. `prune_spent_workspaces` removes dispatch worktree registrations and their
branches once accumulation begins to break provisioning. Both were repaired by hand
often enough to prove they recur unattended, and an orchestrator that needs a person to
clear its own blockers is not unattended.

What they refuse is the same instinct pointed in two directions. `self_heal` will not
guess a branch for a worktree whose admin directory has gone, because a wrong HEAD looks
repaired and a missing one does not, and it will not lift a lock while a git process is
running. The pruner will not remove a worktree that is dirty or that carries a commit
HEAD does not already have, because a cleanup that discards a commit is worse than no
cleanup; it touches only a dispatch workspace, never a unit worktree, never the main
tree, never the orchestrator's own.

Also here: `ROOT`, and the constants the loop and its housekeeping are tuned by -- the
tick interval, the worktree count above which pruning is worth paying for, the plan
backup period and depth, and the age below which a dispatch workspace is presumed still
live. `_force_writable` is the rmtree handler that clears the Windows read-only bit,
which git sets on pack files and loose objects and which on Windows blocks deletion
outright rather than merely advising against it."""

import os
import pathlib
import subprocess
import sys
import time
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent

INTERVAL_S = 45

# Above this many registered worktrees, housekeeping runs. Below it an ordinary tick pays
# nothing.
PRUNE_CEILING = 180

PLAN_BACKUP_EVERY_S = 1800

PLAN_BACKUPS_KEPT = 24


def _force_writable(func, path, exc):
    """rmtree onexc handler: clear the read-only bit and retry once.

    MEASURED 27 August 2026: a first sweep removed 985 workspaces and FAILED on 721 -- a 42%
    failure rate -- every one of them PermissionError [WinError 5] inside `isolated_git_env`.
    The cause is not permissions in any interesting sense: git marks pack files and loose objects
    READ-ONLY, and on Windows the read-only attribute blocks deletion outright rather than being
    a mere hint as it is on POSIX.

    So the self-cleaning shipped an hour earlier would have silently failed on nearly half of
    what it was written to remove, and the disk would have kept filling while a green test said
    the mechanism was in place. A cleanup that reports success on work it did not do is worse
    than no cleanup.
    """
    import stat as _stat

    try:
        os.chmod(path, _stat.S_IWRITE)
        func(path)
    except OSError:
        pass


SPENT_WORKSPACE_AGE_S = 6 * 3600


def prune_spent_workspaces(log) -> None:
    """Remove dispatch worktrees that hold nothing, before accumulation breaks provisioning.

    MEASURED 25 August 2026, and it took the whole harness down once already. 547 worktrees and
    673 stale `consilient-ws-*` branches had accumulated with nothing pruning them, `.git` had
    reached 136 MB, and provisioning a workspace began to fail -- which sent every dispatch to a
    fallback form whose commits cannot be harvested. Eleven commits of finished work were
    stranded and one unit was built twice.

    Joe, 25 August 2026: "that's not sustainable - we need to be autonomously cleaning up
    worktrees and branches."

    Nothing here is clever, deliberately. It removes only a DISPATCH workspace -- never a unit
    worktree, never the main tree, never the orchestrator's own -- and only when that workspace
    holds nothing at all: its directory is gone, or it is clean apart from the provisioning
    probe marker AND carries no commit that HEAD does not already have.

    A cleanup that discards a commit is worse than no cleanup, so anything failing either test
    is left alone. It lives in the loop rather than in the driver because it is housekeeping and
    because a destructive git sweep has no business running inside the driver's unit tests.

    Unit BN is the full lifecycle -- create, use, release, prune, and refuse concurrent
    duplicate-subsystem units. This is the floor that stops the failure recurring until BN
    lands; BN was itself stranded by the workspace bug, so it has already been written once and
    lost.
    """

    def git(*args, cwd=None, timeout=600):
        return subprocess.run(
            ["git", "-C", str(cwd or ROOT), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

    try:
        listing = git("worktree", "list", "--porcelain", timeout=900).stdout
    except Exception:
        return
    entries = []
    current = {}
    for line in listing.splitlines():
        if line.startswith("worktree "):
            if current:
                entries.append(current)
            current = {"path": line.split(" ", 1)[1].strip()}
        elif line.startswith("HEAD "):
            current["head"] = line.split(" ", 1)[1].strip()
        elif line.startswith("branch "):
            current["branch"] = line.split(" ", 1)[1].strip()
    if current:
        entries.append(current)
    if len(entries) <= PRUNE_CEILING:
        return

    head = git("rev-parse", "HEAD").stdout.strip()
    removed = 0
    kept_with_work = 0
    for entry in entries:
        path = entry.get("path", "")
        if "/.harness/dispatch/" not in path.replace(chr(92), "/").lower():
            continue
        try:
            if not pathlib.Path(path).exists():
                git("worktree", "remove", "--force", path)
                removed += 1
                continue
            dirty = [
                ln
                for ln in git("status", "--porcelain", cwd=path).stdout.splitlines()
                if ln.strip() and ".consilient-workspace-probe-" not in ln
            ]
            if dirty:
                continue
            wt_head = entry.get("head", "")
            if wt_head and head:
                ahead = git("rev-list", "--count", head + ".." + wt_head).stdout.strip()
                if ahead not in ("", "0"):
                    kept_with_work += 1
                    continue
            if git("worktree", "remove", "--force", path).returncode == 0:
                removed += 1
                branch = entry.get("branch", "")
                if branch.startswith("refs/heads/consilient-ws-"):
                    git("branch", "-D", branch.split("refs/heads/", 1)[1], timeout=300)
        except Exception:
            continue
    if removed:
        git("worktree", "prune", timeout=900)
        log.write(
            "loop: pruned "
            + str(removed)
            + " spent dispatch worktree(s) from "
            + str(len(entries))
            + "; kept "
            + str(kept_with_work)
            + " carrying work"
            + chr(10)
        )


def self_heal(log) -> None:
    """Repair the two faults that stop everything and that nothing else notices.

    Both were fixed by hand repeatedly on 24 August 2026, which means both would recur
    unattended. An orchestrator that needs a human to clear its own blockers is not unattended.

    ONE -- a WSL-launched agent writing `core.worktree` into the SHARED .git/config, pointing at
    a /mnt/c path. That single line makes EVERY git command in the main repository fail, so no
    merge, no publish and no status works. It recurred THREE times within one hour. `git config
    --unset` cannot repair it, because git cannot read the config far enough to act -- the line
    must be deleted textually. The repository already scrubs GIT_* environment variables for
    exactly this hazard; writing the config file bypasses that entirely.

    TWO -- a stale index.lock left by a killed git process. Held with NO live git process, it
    blocks every write indefinitely. The liveness test matters: removing a lock a live process
    holds would corrupt that operation, so this only acts when no git is running at all, and
    only when the lock has been untouched for two minutes.
    """
    # FOUR -- the worktree's OWN administrative directory is gone.
    #
    # MEASURED 28 August 2026, twice in one night. `.git/worktrees/consilience-cto/`
    # disappeared and every git call from the driver failed with 'fatal: not a git
    # repository'. That is the worst shape a fault can take here, because the driver does
    # not stop: it keeps ticking and writes state computed from failed git calls -- a
    # retired count derived from `rev-parse` returning nothing looks exactly like real
    # regression. Both times it was repaired by hand.
    #
    # The cause is still unknown, and this deliberately does not wait to find out. A fault
    # that blinds the orchestrator and recurs unattended has to be survivable before it is
    # understood; the alternative is another night of hand-repair.
    #
    # Three files are the minimum git needs, and the index is the fourth thing: without it
    # `git status` reports EVERY tracked file as deleted, so a commit taken in that state
    # would record the deletion of the whole tree. `git reset` (MIXED, never --hard)
    # rebuilds the index from HEAD and never touches the working tree.
    try:
        admin = ROOT.parent.parent.parent / ".git" / "worktrees" / ROOT.name
        pointer = ROOT / ".git"
        if pointer.is_file() and not admin.is_dir():
            branch = "worktree-" + ROOT.name
            ref = ROOT.parent.parent.parent / ".git" / "refs" / "heads" / branch
            packed = ROOT.parent.parent.parent / ".git" / "packed-refs"
            known = ref.is_file() or (
                packed.is_file()
                and ("refs/heads/" + branch)
                in packed.read_text(encoding="utf-8", errors="replace")
            )
            if not known:
                # Never guess which branch this worktree was on. A wrong HEAD is worse
                # than a missing one, because it looks repaired.
                log.write(
                    "loop: the worktree admin dir is GONE and the branch could not be "
                    "identified -- REFUSING to guess. git is blind until a person "
                    "repairs it." + chr(10)
                )
                log.flush()
            else:
                admin.mkdir(parents=True, exist_ok=True)
                (admin / "HEAD").write_text(
                    "ref: refs/heads/" + branch + chr(10), encoding="utf-8"
                )
                (admin / "commondir").write_text("../.." + chr(10), encoding="utf-8")
                (admin / "gitdir").write_text(
                    str(pointer).replace(chr(92), "/") + chr(10), encoding="utf-8"
                )
                subprocess.run(
                    ["git", "-C", str(ROOT), "reset"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=600,
                )
                log.write(
                    "loop: REBUILT the worktree admin dir (" + branch + "); every git "
                    "call had been failing and the driver was writing state computed "
                    "from those failures" + chr(10)
                )
                log.flush()
    except OSError:
        pass

    main_config = ROOT.parent.parent.parent / ".git" / "config"
    try:
        text = main_config.read_text(encoding="utf-8")
        if "/mnt/c" in text:
            kept = [ln for ln in text.split(chr(10)) if "/mnt/c" not in ln]
            main_config.write_text(chr(10).join(kept), encoding="utf-8")
            log.write(
                "loop: repaired .git/config -- a WSL path had broken every git command"
                + chr(10)
            )
    except OSError:
        pass

    # THREE -- git long-path support. MEASURED 24 August 2026 and it silently stopped ALL
    # verification. A review dispatch builds its isolated workspace by full-cloning into
    # .harness/dispatch/<run-id>/workspace/full_clone/<run-id>/, and that prefix plus this
    # repository's descriptive ADR filenames exceeds Windows MAX_PATH of 260 characters. The
    # clone SUCCEEDS and the checkout FAILS -- "unable to create file ... Filename too long",
    # then "fatal: unable to checkout working tree" -- so every review died at setup with an
    # empty stdout and status=failed. Verified sat at 3 while 64 reviews were in flight, and
    # nothing reported a cause, because from the driver's side a review that never started and
    # a review that found nothing look identical.
    #
    # `core.longpaths` is inherited by fresh clones only from the GLOBAL config, which is why it
    # is set there rather than in the repository. Proved by reproducing the exact failing path
    # shape: with it set, the clone completes and the long-named ADR checks out.
    try:
        current = subprocess.run(
            ["git", "config", "--global", "--get", "core.longpaths"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        ).stdout.strip()
        if current.lower() != "true":
            subprocess.run(
                ["git", "config", "--global", "core.longpaths", "true"],
                capture_output=True,
                timeout=60,
            )
            log.write(
                "loop: set git core.longpaths -- long paths were breaking every review clone"
                + chr(10)
            )
    except Exception:
        pass

    for lock in (ROOT.parent.parent.parent / ".git" / "worktrees").glob("*/index.lock"):
        try:
            if time.time() - lock.stat().st_mtime < 120:
                continue
        except OSError:
            continue
        try:
            alive = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-Process git -ErrorAction SilentlyContinue | Measure-Object).Count",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            ).stdout.strip()
        except Exception:
            continue
        if alive not in ("", "0"):
            continue
        try:
            lock.unlink()
            log.write(
                f"loop: removed a stale {lock.name} -- no git process was holding it"
                + chr(10)
            )
        except OSError:
            pass

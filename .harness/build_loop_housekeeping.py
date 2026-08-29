"""Housekeeping that runs before the driver on every tick, and the paths the loop runs
on.

Four sweeps, each of which exists because something stopped the build dead.
`ensure_plan` keeps `.harness/plan-units.json` alive -- restoring the newest backup when
something deletes it, and otherwise keeping a backup fresh enough to be worth restoring.
`normalise_wsl_gitdirs` rewrites WSL-form git pointers back to Windows form before any
disposal path runs, because a worktree Windows git cannot read looks empty to both
`worktree remove --force` and `worktree prune`. `ensure_unit_knowledge` places the
gitignored knowledge source declaration into unit worktrees, which can never inherit it
by merging. `prune_spent_workspace_dirs` reclaims the scratch half of a finished
dispatch, which the registration pruner can never see, because only one of the three
workspace forms is a worktree and the other two are clones.

All four sit in the loop rather than the driver deliberately: this is housekeeping, it
must run before the driver starts, and destructive-adjacent file operations have no
business inside the driver's unit tests. None of them may touch a dispatch RECORD -- the
brief, the stdout, the stderr and the result are small and are the audit trail this
project runs on. Each reports what it did to the log rather than working silently, since
a sweep that reports a clean pass over work it did not do is the failure these were
written to end.

`hold_loop_lock` is here as well, with the three paths the loop is defined by: the log
it appends to, the `STOP-LOOP` marker that is the only thing that ends it, and the lock
file that makes it safe for the scheduler to fire as often as it likes -- a second loop
exits immediately, and a dead one is replaced within a single scheduling interval."""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_loop_git import (
    PLAN_BACKUPS_KEPT,
    PLAN_BACKUP_EVERY_S,
    ROOT,
    SPENT_WORKSPACE_AGE_S,
    _force_writable,
    prune_spent_workspaces,
    self_heal,
)


__all__ = [
    "LOG",
    "LOOP_LOCK",
    "PLAN_BACKUPS_KEPT",
    "PLAN_BACKUP_EVERY_S",
    "ROOT",
    "SPENT_WORKSPACE_AGE_S",
    "STOP",
    "_force_writable",
    "ensure_plan",
    "ensure_unit_knowledge",
    "hold_loop_lock",
    "normalise_wsl_gitdirs",
    "prune_spent_workspace_dirs",
    "prune_spent_workspaces",
    "self_heal",
]

STOP = ROOT / ".harness" / "STOP-LOOP"

LOG = ROOT / ".harness" / "build-loop.log"

LOOP_LOCK = ROOT / ".harness" / "build-loop.lock"


def hold_loop_lock():
    """One loop at a time, so the scheduler may retry as often as it likes.

    MEASURED 24 August 2026: the loop died twice without writing an exception -- 41 ticks, then
    the process simply ended, with an empty stderr and the per-tick handler never firing. It was
    killed or died outside the guarded region, and both times the build stopped dead until
    somebody noticed. A loop whose liveness depends on nothing ever killing it is not resilient;
    it is lucky.

    The scheduled task now fires every few minutes instead of once. This lock makes that safe:
    if a loop is already running the new invocation exits immediately, and if the previous one
    died the new one takes over within one scheduling interval. That is crash-only recovery --
    the restart path is the ONLY path, so it is exercised constantly and cannot rot.

    Returns the held handle, or None when another loop owns it.
    """
    handle = LOOP_LOCK.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


# A shrink smaller than this is left alone: an operator pruning a unit or two is doing their job,
# and a guard that fights a legitimate edit is worse than no guard. The measured failure was a
# rollback of 147 units to 117 -- 20% -- so the threshold sits well below it and well above
# ordinary editing.
PLAN_ROLLBACK_FRACTION = 0.05


def _plan_units(path: Path) -> int | None:
    """How many units a plan file declares, or None if it cannot be read as one."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    units = data if isinstance(data, list) else data.get("units", data)
    return len(units) if isinstance(units, (list, dict)) else None


def _plan_rolled_back(plan: Path, backups: Path) -> tuple[int, int, Path] | None:
    """Has the live plan been silently replaced by an OLDER, smaller one?

    MEASURED 29 August 2026, and this is the half of the failure that `ensure_plan` could not
    see. The plan was tracked until d01394a on 25 August, and 262 of 838 local branches still
    carry it at their tip. Replaying any of those commits into the main worktree stages the path
    into an index whose HEAD has no version of it: the live file is OVERWRITTEN with the commit's
    copy, and only the abort that follows deletes it.

    A deleted plan is loud and the branch above restores it. A plan quietly rolled back four days
    -- 147 units to 117 -- looks entirely valid, and the driver then builds from it. The driver's
    own plan-shrink refusal needs a 25% loss to fire, so a 20% rollback passes it silently.

    Compares against the newest backup rather than a remembered number, because the backup is at
    most PLAN_BACKUP_EVERY_S old and is the only record of what the plan looked like before.
    """
    live = _plan_units(plan)
    if live is None:
        return None
    newest = max(
        backups.glob("plan-units-*.json"),
        key=lambda p: p.stat().st_mtime,
        default=None,
    )
    if newest is None:
        return None
    known = _plan_units(newest)
    if known is None or known == 0:
        return None
    if live >= known - max(1, int(known * PLAN_ROLLBACK_FRACTION)):
        return None
    return live, known, newest


def ensure_plan(log) -> str:
    """Keep `.harness/plan-units.json` alive. Returns what happened, for the log.

    MEASURED 27 August 2026: the plan was DELETED four times in under three hours. It is
    untracked and gitignored, so git cannot restore it, and it is the one file the driver cannot
    work without -- every tick that ran without it either crashed on `units[uid]` or refused.

    SOLVED 29 August 2026, by reproduction after two investigations failed by reading code.
    NOTHING deletes it. GIT does, and the paragraph that used to stand here said "what deletes it
    is still unknown ... neither the loop nor the driver removes it ... `git clean -nd` lists
    nothing ... a watcher polling twice a second caught the context but not the culprit."

    Every one of those observations was true and none of them pointed at the cause. The file was
    TRACKED until d01394a on 25 August, and 262 of 838 local branches still carry it at their tip.
    `build_driver` replays unit commits with `git cherry-pick` in the MAIN worktree; picking a
    commit from before that boundary stages the path into an index whose HEAD has no version of
    it, so the live file is overwritten with the commit's copy, and the `--abort`, `--skip` or
    `reset --hard` that follows a conflict then removes it. Git does that to ignored files without
    complaint. There is no unlink to find, `git clean` really is innocent, and the abort is one
    atomic index rewrite, so no poller could ever win the race. Measured: 776 such aborts in the
    log, across ten units, all replaying one commit.

    `build_driver.replays_over_instance_state` now refuses those replays. This stays, because a
    hand-run `git checkout` or `rebase` across the same boundary does the same thing and no guard
    in the driver can cover an operator's shell.

    So this still does not diagnose. It makes the question stop mattering: if the plan is gone, restore
    the newest backup and say so loudly; if it is present, keep a backup fresh enough to be worth
    restoring. The first restore of the day had to fall back to a copy from 25 August because
    nothing had refreshed it in two days, and six units lost their retirement because their
    claims had moved on since. A backup nobody refreshes is a backup that costs you something to
    use.

    Deliberately in the loop rather than the driver: it is housekeeping, it must run BEFORE the
    driver starts, and a destructive-adjacent file operation has no business inside the driver's
    unit tests.
    """
    plan = ROOT / ".harness" / "plan-units.json"
    backups = ROOT / ".harness" / "plan-backups"
    backups.mkdir(parents=True, exist_ok=True)

    if not plan.exists():
        candidates = sorted(
            backups.glob("plan-units-*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            log.write(
                "loop: plan-units.json is MISSING and there is no backup to restore\n"
            )
            log.flush()
            return "missing-no-backup"
        newest = candidates[0]
        try:
            shutil.copy2(newest, plan)
        except OSError as exc:
            log.write(f"loop: plan-units.json restore FAILED: {exc}\n")
            log.flush()
            return "restore-failed"
        age_min = (time.time() - newest.stat().st_mtime) / 60
        log.write(
            "loop: plan-units.json was MISSING and has been restored from "
            f"{newest.name} ({age_min:.0f} min old). Something is deleting it; this is the "
            "fourth time today and the cause is not yet known.\n"
        )
        log.flush()
        return "restored"

    rolled_back = _plan_rolled_back(plan, backups)
    if rolled_back is not None:
        live_units, backup_units, source = rolled_back
        try:
            shutil.copy2(source, plan)
        except OSError as exc:
            log.write(f"loop: plan-units.json rollback repair FAILED: {exc}" + chr(10))
            log.flush()
            return "rollback-repair-failed"
        log.write(
            f"loop: plan-units.json had SHRUNK from {backup_units} units to {live_units} and "
            f"has been restored from {source.name}. A cherry-pick of a commit predating "
            "d01394a -- when this file was still tracked -- silently overwrites it with that "
            "commit's older copy. Deletion is loud; this is not." + chr(10)
        )
        log.flush()
        return "rolled-back"

    # Present. Keep a backup fresh enough that restoring it costs nothing.
    try:
        newest = max(
            backups.glob("plan-units-*.json"),
            key=lambda p: p.stat().st_mtime,
            default=None,
        )
        if newest is None or time.time() - newest.stat().st_mtime > PLAN_BACKUP_EVERY_S:
            stamp = time.strftime("%Y%m%dT%H%M%S")
            fresh = backups / f"plan-units-{stamp}.json"
            shutil.copy2(plan, fresh)
            # copy2 PRESERVES mtime, so the backup inherited the plan's and the freshness test
            # above measured how old the PLAN was, never how old the BACKUP was. A restore then
            # copies a backup onto the plan, so the plan inherits the stale stamp too and the
            # pair never ages out of it. MEASURED 27 August 2026: two backups existed, the
            # newest 139 minutes old, against a 30-minute interval -- and the restore that
            # mattered fell back to a copy from two days earlier. Stamp it with now.
            os.utime(fresh, None)
            keep = sorted(
                backups.glob("plan-units-*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for old in keep[PLAN_BACKUPS_KEPT:]:
                try:
                    old.unlink()
                except OSError:
                    pass
            log.write(f"loop: plan-units.json backed up to {fresh.name}" + chr(10))
            log.flush()
            return "backed-up"
    except OSError:
        pass
    return "present"


def normalise_wsl_gitdirs(log) -> int:
    """Rewrite WSL-form git pointers back to Windows form before anything prunes them.

    MEASURED 27 August 2026, and this is the mechanism that destroyed 37 unit worktrees.

    cursor-agent runs under WSL, so a dispatch into a unit worktree runs LINUX git, which
    rewrites that worktree's `.git` file and its admin `gitdir` to `/mnt/c/...`. Windows git
    cannot resolve that path, so the worktree reports NO HEAD -- and both disposal paths in
    this file read that as "nothing of value here":

      * `git worktree remove --force` skips its own has-work guard, because that guard asks
        whether the worktree is ahead of HEAD and an unreadable worktree is ahead of nothing;
      * `git worktree prune` treats the registration as stale and deletes the admin dir.

    Either way the unit loses its git metadata permanently. It can never be merged again, and
    every review of it returns DEFECTIVE against content that was never its own. 37 of the 41
    built-and-unmerged units were in exactly that state when this was found; three more were
    carrying WSL paths at that moment and were one prune away from joining them.

    The repair is one line of text per file and it is lossless -- only the spelling of the
    path changes. It runs BEFORE any disposal, so a WSL round-trip becomes a no-op instead of
    a deletion. This is the guard, not a cleanup: the cleanup would be running it afterwards,
    by which time the admin directory is already gone.
    """
    candidates = [ROOT / ".git"]
    units = ROOT / ".harness" / "unit-worktrees"
    if units.is_dir():
        for d in units.iterdir():
            if d.is_dir():
                candidates.append(d / ".git")
    common = ROOT.parent.parent.parent / ".git" / "worktrees"
    if common.is_dir():
        for d in common.iterdir():
            if d.is_dir():
                candidates.append(d / "gitdir")

    fixed: list[str] = []
    unwritable: list[str] = []
    for f in candidates:
        try:
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "/mnt/" not in text:
            continue
        out = re.sub(r"/mnt/([a-zA-Z])/", lambda m: m.group(1).upper() + ":/", text)
        try:
            # MODE 'r+', NEVER 'w'. git marks a worktree's .git pointer HIDDEN on
            # Windows, and open(mode='w') uses CREATE_ALWAYS, which the OS refuses on a
            # hidden file with PermissionError [Errno 13]. Every file this guard exists
            # to repair is hidden, so the first version could never repair a single one.
            # 'r+' opens the existing file instead of recreating it, and truncate()
            # drops the tail when the Windows path is shorter than the WSL one.
            with open(f, "r+", encoding="utf-8", newline="") as fh:
                fh.seek(0)
                fh.write(out)
                fh.truncate()
            fixed.append(str(f))
        except OSError as exc:
            # NEVER silent. The first version swallowed this with a bare `continue`, so
            # it reported a clean sweep while repairing nothing. A pointer that cannot be
            # repaired is one prune away from costing a unit its git metadata for good.
            unwritable.append(str(f) + " (" + type(exc).__name__ + ")")

    if fixed:
        log.write(
            "loop: normalised "
            + str(len(fixed))
            + " WSL-form git pointer(s) before prune; "
            "a WSL dispatch had made them unreadable to Windows git, which is how worktrees "
            "were being destroyed" + chr(10)
        )
        log.flush()
    if unwritable:
        log.write(
            "loop: COULD NOT repair " + str(len(unwritable)) + " WSL-form git "
            "pointer(s) -- each is one prune away from losing its worktree: "
            + ", ".join(unwritable)
            + chr(10)
        )
        log.flush()
    return len(fixed)


def ensure_unit_knowledge(log) -> int:
    """Give every unit worktree the knowledge source declaration it cannot inherit.

    MEASURED 28 August 2026, and this was the whole pipeline stall.

    `.harness/knowledge/sources.json` is instance data under ADR-0065 and is gitignored, so
    a unit worktree can never receive it by merging -- git does not carry ignored files.
    129 of 132 unit worktrees did not have it. `tests/test_knowledge.py` reads the real
    declaration, so SIX tests failed in every one of those worktrees, the merge gate refused
    on a red suite, and the conflict stayed. 217 resolve dispatches ran and not one could
    succeed: A01's resolver finished its merge, fixed its own mypy, and reported the six
    knowledge failures as 'not this merge' -- correctly, and it still could not pass.

    Five consecutive ticks reported an identical 31/147 done, 8 ready, 53 blocked.

    The file holds NO credential -- it names connectors, licences and the ENV VAR NAMES a
    connector would read, and says so in its own header. Copying it into a worktree
    therefore moves no secret, which is the only reason this is safe to automate.

    Deliberately additive: an existing file is never overwritten, because a unit may be
    editing the declaration as its actual deliverable.
    """
    source = ROOT / ".harness" / "knowledge" / "sources.json"
    if not source.is_file():
        return 0
    units = ROOT / ".harness" / "unit-worktrees"
    if not units.is_dir():
        return 0
    placed = 0
    for d in sorted(units.iterdir()):
        if not d.is_dir():
            continue
        dest = d / ".harness" / "knowledge" / "sources.json"
        if dest.is_file():
            continue
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            placed += 1
        except OSError:
            continue
    if placed:
        log.write(
            "loop: placed the knowledge declaration in "
            + str(placed)
            + " unit worktree(s); "
            "without it six tests fail there and every merge gate refuses on a red suite"
            + chr(10)
        )
        log.flush()
    return placed


def prune_spent_workspace_dirs(log) -> int:
    """Delete the scratch half of a finished dispatch. Returns how many were removed.

    `prune_spent_workspaces` below removes git WORKTREE REGISTRATIONS, and that is all it can
    ever remove, because it enumerates `git worktree list`. But dispatch.py provisions one of
    THREE forms -- `WORKSPACE_FORMS = ("linked_worktree", "isolated_git_env", "full_clone")` --
    and only the first is a worktree. A clone never appears in that listing, so two forms out of
    three have never been prunable by anything.

    MEASURED 27 August 2026: 58 registered worktrees against 1,819 workspace directories on disk
    at ~326MB each. Roughly 580GB of scratch, dating back to 21 August, on a machine where git
    operations were timing out and a tick was spending minutes in prune. Joe: "We need to
    thoroughly clean up all of those worktrees that's ridiculous", and "worktrees should be
    self-cleaning and the consilient product should enforce that".

    A dispatch directory has two halves and only one is scratch. The RECORD -- brief, stdout,
    stderr, result json -- is small and is the audit trail this project runs on, so it is never
    touched. The WORKSPACE is the clone, and once the run is over nothing can read it again.

    Three guards, in order of how badly each would hurt if it were missing:

    1. Never touch a directory with a registered worktree inside it. Deleting a worktree's files
       without unregistering leaves git a dangling admin directory -- which is precisely what
       took the driver's own worktree out earlier the same day.
    2. Never touch anything under `unit-worktrees/`. That is unmerged unit work and its only
       copy; thirty-nine units were in conflict when this was written.
    3. Never touch a young directory. The age floor is well above the 3600s leash, so a live
       dispatch cannot be caught by it.
    """
    dispatch = ROOT / ".harness" / "dispatch"
    if not dispatch.is_dir():
        return 0
    try:
        listing = subprocess.run(
            ["git", "-C", str(ROOT), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=900,
        ).stdout
    except Exception:
        return 0
    registered = set()
    for line in listing.splitlines():
        if line.startswith("worktree "):
            raw = line[len("worktree ") :].strip().replace(chr(92), "/").lower()
            if raw.startswith("/mnt/c/"):
                raw = "c:/" + raw[len("/mnt/c/") :]
            registered.add(raw.rstrip("/"))

    now = time.time()
    removed = 0
    for entry in dispatch.iterdir():
        if not entry.is_dir() or not entry.name.startswith("2026"):
            continue
        workspace = entry / "workspace"
        if not workspace.is_dir():
            continue
        try:
            if now - entry.stat().st_mtime < SPENT_WORKSPACE_AGE_S:
                continue
        except OSError:
            continue
        prefix = str(workspace).replace(chr(92), "/").lower()
        if any(r.startswith(prefix) for r in registered):
            continue  # a worktree lives in here; the registration pruner owns it
        try:
            shutil.rmtree(workspace, onexc=_force_writable)
            removed += 1
        except OSError:
            continue
    if removed:
        log.write(
            f"loop: reclaimed {removed} spent dispatch workspace(s); their records are kept"
            + chr(10)
        )
        log.flush()
    return removed

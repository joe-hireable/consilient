"""Tick the driver forever. Survives the orchestrator; stops only when told to.

The build sat idle from 12:32 on 24 August 2026 because the agent holding the loop died and
nothing restarted it. Fourteen units had finished and none were retired, which blocked every
dependent. A loop that depends on an agent staying alive is not a loop.

Stop it by creating .harness/STOP-LOOP. Nothing else stops it, and it never runs two ticks at
once because build_driver takes its own exclusive lock.

HOW IT IS STARTED, and why it is not a plain background process. MEASURED 24 August 2026: the
loop was launched with PowerShell Start-Process from an orchestrating session, and when that
session exited the loop AND every dispatch it had started died with it -- the whole process tree
went, despite being nominally detached. The build had been running unattended for exactly as long
as the chat window was open, which is the opposite of the intent.

It now runs as a Windows scheduled task:

    schtasks /Create /TN ConsilientBuildLoop /TR "<python> -u <this file>" /SC ONCE /ST 00:00 /F
    schtasks /Run    /TN ConsilientBuildLoop

To stop it for good, and this is the undo:

    schtasks /End    /TN ConsilientBuildLoop
    schtasks /Delete /TN ConsilientBuildLoop /F

Creating .harness/STOP-LOOP still stops it cleanly after the current tick, which is the gentler
option and the one to prefer -- a tick killed mid-suite leaves a worktree half-judged.
"""

import os
import pathlib
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = ROOT / ".harness" / "STOP-LOOP"
LOG = ROOT / ".harness" / "build-loop.log"
INTERVAL_S = 45


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


# Above this many registered worktrees, housekeeping runs. Below it an ordinary tick pays
# nothing.
PRUNE_CEILING = 180


PLAN_BACKUP_EVERY_S = 1800
PLAN_BACKUPS_KEPT = 24


def ensure_plan(log) -> str:
    """Keep `.harness/plan-units.json` alive. Returns what happened, for the log.

    MEASURED 27 August 2026: the plan was DELETED four times in under three hours. It is
    untracked and gitignored, so git cannot restore it, and it is the one file the driver cannot
    work without -- every tick that ran without it either crashed on `units[uid]` or refused.

    What deletes it is still unknown, and that is precisely why this exists. The obvious suspects
    were read and cleared: neither the loop nor the driver removes it, `self_heal` only repairs
    git config, and `git clean` cannot be it because `git clean -nd` lists nothing. A watcher
    polling twice a second caught the context but not the culprit -- an unlink completes far
    faster than any poll, and two Claude Code sessions were live on this machine at the time.

    So this does not diagnose. It makes the question stop mattering: if the plan is gone, restore
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
            backups.glob("plan-units-*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not candidates:
            log.write("loop: plan-units.json is MISSING and there is no backup to restore\n")
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

    # Present. Keep a backup fresh enough that restoring it costs nothing.
    try:
        newest = max(
            backups.glob("plan-units-*.json"), key=lambda p: p.stat().st_mtime, default=None
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
                backups.glob("plan-units-*.json"), key=lambda p: p.stat().st_mtime, reverse=True
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
            "loop: normalised " + str(len(fixed)) + " WSL-form git pointer(s) before prune; "
            "a WSL dispatch had made them unreadable to Windows git, which is how worktrees "
            "were being destroyed" + chr(10)
        )
        log.flush()
    if unwritable:
        log.write(
            "loop: COULD NOT repair " + str(len(unwritable)) + " WSL-form git "
            "pointer(s) -- each is one prune away from losing its worktree: "
            + ", ".join(unwritable) + chr(10)
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
            "loop: placed the knowledge declaration in " + str(placed) + " unit worktree(s); "
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
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900,
        ).stdout
    except Exception:
        return 0
    registered = set()
    for line in listing.splitlines():
        if line.startswith("worktree "):
            raw = line[len("worktree "):].strip().replace(chr(92), "/").lower()
            if raw.startswith("/mnt/c/"):
                raw = "c:/" + raw[len("/mnt/c/"):]
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
            f"loop: reclaimed {removed} spent dispatch workspace(s); their records are kept" + chr(10)
        )
        log.flush()
    return removed


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
            ref = (
                ROOT.parent.parent.parent / ".git" / "refs" / "heads" / branch
            )
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


class _NullLog:
    """self_heal writes its repairs somewhere; the watchdog opens the log per repair rather
    than holding the handle the tick is writing to."""

    def write(self, text: str) -> None:
        try:
            with LOG.open("a", encoding="utf-8") as handle:
                handle.write(text)
        except OSError:
            pass


def _healing_watchdog() -> None:
    """Repair the shared config on a clock, not on a tick boundary.

    MEASURED 25 August 2026, from the monitors, four times in one afternoon:

        WSL-CONFIG: /mnt/c in .git/config and no tick for 34m - self_heal is not clearing it

    `self_heal` was correct and correctly wired; it simply could not run. It executes at the
    top of a tick, and a tick can occupy the loop for the full 3000-second deadline, so a
    corruption written by a dispatched agent at minute one is not repaired until minute fifty.
    Meanwhile EVERY git command in the repository fails, and the damage is not confined to
    merging and publishing: `artefact_identity` shells out to `git rev-parse HEAD:<path>` per
    claimed file and returns None when git fails, `retired_units` requires a non-None identity,
    and the retirement count therefore fell from 10 to 0 while no work had been lost at all.
    A broken config silently reports the build as having completed nothing.

    A repair whose period is set by the thing it repairs is not a repair. Sixty seconds, on its
    own thread, daemon so it never keeps the process alive, and every failure swallowed -- a
    watchdog that can raise is one more thing to go wrong.
    """
    while not STOP.exists():
        try:
            self_heal(_NullLog())
        except Exception:  # a watchdog that dies is worse than one that skips a beat
            pass
        time.sleep(60)


def main() -> int:
    tick = 0
    threading.Thread(target=_healing_watchdog, daemon=True).start()
    while not STOP.exists():
        tick += 1
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with LOG.open("a", encoding="utf-8") as handle:
            handle.write(f"\n===== tick {tick} at {stamp} =====\n")
            handle.flush()
            # BEFORE the tick, every tick. `self_heal` was written on 24 August 2026 and NEVER
            # CALLED -- defined, documented, dead. MEASURED 25 August 2026: a WSL agent had
            # written `core.worktree = /mnt/c/...` into the shared .git/config at 22:57 on the
            # 24th and it was still there THIRTEEN HOURS LATER, because the repair that exists
            # for exactly that line had no call site.
            #
            # What it cost: `git worktree add` fails while that line is present, so every
            # dispatch fell through to the isolated_git_env workspace form, which clones with
            # --separate-git-dir. Agent commits then landed in a DIFFERENT object store, invisible
            # to the driver, and eleven commits of finished work -- about 3,300 insertions --
            # were stranded. One unit was built twice because the first result could not be seen.
            #
            # Per tick rather than per loop start, because the corruption is written DURING
            # operation by a dispatched agent. A repair that only runs at startup cannot fix a
            # fault that appears after startup, which is precisely what happened here.
            # Before anything else: the driver cannot do useful work without a plan, and
            # something has been deleting it. See `ensure_plan`.
            ensure_plan(handle)
            # BEFORE any disposal path runs. A WSL-form pointer makes a live worktree look
            # empty, and both `worktree remove --force` and `worktree prune` then delete it.
            normalise_wsl_gitdirs(handle)
            # A unit worktree cannot inherit gitignored instance data by merging, and
            # without this file six tests fail there and the merge gate refuses.
            ensure_unit_knowledge(handle)
            handle.flush()
            self_heal(handle)
            handle.flush()
            prune_spent_workspaces(handle)
            handle.flush()
            # Registrations are only one of the three workspace forms; the other two are
            # clones and have never been prunable by anything. See the docstring.
            prune_spent_workspace_dirs(handle)
            handle.flush()
            try:
                subprocess.run(
                    [sys.executable, "-u", str(ROOT / ".harness" / "build_driver.py")],
                    cwd=str(ROOT),
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    timeout=3000,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                handle.write(
                    "loop: tick exceeded 50 minutes; abandoning it and starting the next\n"
                )
            except Exception as exc:  # a loop that dies on one bad tick is not a loop
                handle.write(f"loop: tick raised {type(exc).__name__}: {exc}\n")
        if STOP.exists():
            break
        time.sleep(INTERVAL_S)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\nloop: STOP-LOOP present, exiting cleanly after {tick} tick(s)\n"
        )
    return 0


if __name__ == "__main__":
    _lock = hold_loop_lock()
    if _lock is None:
        raise SystemExit(0)
    try:
        raise SystemExit(main())
    finally:
        _lock.close()

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
            self_heal(handle)
            handle.flush()
            prune_spent_workspaces(handle)
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

"""Tick the driver forever. Survives the orchestrator; stops only when told to.

The build sat idle from 12:32 on 24 August 2026 because the agent holding the loop died
and nothing restarted it. Fourteen units had finished and none were retired, which
blocked every dependent. A loop that depends on an agent staying alive is not a loop.

Stop it by creating .harness/STOP-LOOP. Nothing else stops it, and it never runs two
ticks at once because build_driver takes its own exclusive lock.

HOW IT IS STARTED, and why it is not a plain background process. MEASURED 24 August
2026: the loop was launched with PowerShell Start-Process from an orchestrating session,
and when that session exited the loop AND every dispatch it had started died with it --
the whole process tree went, despite being nominally detached. The build had been
running unattended for exactly as long as the chat window was open, which is the
opposite of the intent.

It now runs as a Windows scheduled task:

    schtasks /Create /TN ConsilientBuildLoop /TR "<python> -u <this file>" /SC ONCE /ST 00:00 /F
    schtasks /Run    /TN ConsilientBuildLoop

To stop it for good, and this is the undo:

    schtasks /End    /TN ConsilientBuildLoop
    schtasks /Delete /TN ConsilientBuildLoop /F

Creating .harness/STOP-LOOP still stops it cleanly after the current tick, which is the
gentler option and the one to prefer -- a tick killed mid-suite leaves a worktree
half-judged.

Two siblings now hold what a tick calls into. `build_loop_git.py` holds `ROOT`, the
loop's constants, `self_heal` and `prune_spent_workspaces` -- repairing git's own
bookkeeping and disposing of worktree registrations that hold nothing.
`build_loop_housekeeping.py` holds `LOG`, `STOP`, `LOOP_LOCK`, `hold_loop_lock`, and the
four pre-driver sweeps: `ensure_plan`, `normalise_wsl_gitdirs`, `ensure_unit_knowledge`
and `prune_spent_workspace_dirs`. This file keeps the tick itself, the healing watchdog
and the log shim it writes through."""

import subprocess
import sys
import threading
import time
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_loop_git import (
    INTERVAL_S,
    ROOT,
    prune_spent_workspaces,
    self_heal,
)

from build_loop_git import (
    PLAN_BACKUPS_KEPT,
    PLAN_BACKUP_EVERY_S,
    PRUNE_CEILING,
    SPENT_WORKSPACE_AGE_S,
    _force_writable,
)

from build_loop_housekeeping import (
    LOG,
    LOOP_LOCK,
    STOP,
    ensure_plan,
    ensure_unit_knowledge,
    hold_loop_lock,
    normalise_wsl_gitdirs,
    prune_spent_workspace_dirs,
)

__all__ = [
    "INTERVAL_S",
    "LOG",
    "LOOP_LOCK",
    "PLAN_BACKUPS_KEPT",
    "PLAN_BACKUP_EVERY_S",
    "PRUNE_CEILING",
    "ROOT",
    "SPENT_WORKSPACE_AGE_S",
    "STOP",
    "_force_writable",
    "ensure_plan",
    "ensure_unit_knowledge",
    "hold_loop_lock",
    "main",
    "normalise_wsl_gitdirs",
    "prune_spent_workspace_dirs",
    "prune_spent_workspaces",
    "self_heal",
]


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

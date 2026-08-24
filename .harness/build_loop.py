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

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = ROOT / ".harness" / "STOP-LOOP"
LOG = ROOT / ".harness" / "build-loop.log"
INTERVAL_S = 45


def main() -> int:
    tick = 0
    while not STOP.exists():
        tick += 1
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with LOG.open("a", encoding="utf-8") as handle:
            handle.write(f"\n===== tick {tick} at {stamp} =====\n")
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
                handle.write("loop: tick exceeded 50 minutes; abandoning it and starting the next\n")
            except Exception as exc:  # a loop that dies on one bad tick is not a loop
                handle.write(f"loop: tick raised {type(exc).__name__}: {exc}\n")
        if STOP.exists():
            break
        time.sleep(INTERVAL_S)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"\nloop: STOP-LOOP present, exiting cleanly after {tick} tick(s)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

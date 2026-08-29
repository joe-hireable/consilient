"""Wait for the running tick to finish, apply the pending state repairs, restart the loop.

Editing driver-state.json while a tick is running loses the edit: the driver read the file at
tick start and rewrites it wholesale at the end, so a concurrent write is a lost update. T01 was
retired three times and un-retired three times that way on 24 August 2026. This waits for the
window instead of fighting for it.

THIS IS NOT THE RESTART COMMAND, AND IT REFUSES TO RUN WITHOUT --APPLY.

It reads like one. It is the only script in the tree whose name suggests resuming the loop, and
nothing else documents a restart -- so on 29 August 2026 an audit found it sitting here as the
obvious thing to run, and it is the wrong thing to run.

`FORCE_DONE` below is a hard-coded list of eleven unit ids frozen on 24 August 2026. `main()`
merges it into the driver's `force_done`, appends every id to `done`, drops them from
`conflicts`, `in_flight` and `resolve_dispatched`, and THEN deletes STOP-LOOP and starts the
loop. Running it today retires eleven named units on five-day-old reasoning, in the same breath
as the restart, with no separate confirmation of either half.

TO RESTART THE LOOP, when the preconditions are met, the whole procedure is:

    rm .harness/STOP-LOOP

The ConsilientBuildLoop scheduled task fires every five minutes and has been firing throughout
the pause -- each fire appending one "STOP-LOOP present, exiting cleanly after 0 tick(s)" line
to .harness/build-loop.log. Deleting the token is the entire restart. Confirm it took with
`tail .harness/build-loop.log`.

There is also a second reason not to reach for this script: it restarts the loop with
`subprocess.Popen`, and build_loop.py's own docstring records that a Popen-launched loop died
together with the session that spawned it on 24 August 2026, which is why the scheduled task
exists. The task is the supported path; this is not.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / ".harness" / "driver-state.json"
STOP = ROOT / ".harness" / "STOP-LOOP"
LOG = ROOT / ".harness" / "resume-loop.log"
FORCE_DONE = ["T01", "AM", "A03", "AD", "AH", "G01", "K01", "N00", "Q01", "X05", "Y02"]


def loop_alive() -> bool:
    out = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            # MEASURED 24 Aug 2026: this matched 'build_driver' ANYWHERE in a command line, and a
            # unit dispatch that CLAIMS .harness/build_driver.py contains that string. The handover
            # therefore waited on a process that was not the loop, for ever. Verifying by process
            # identity is the failure this repository keeps measuring; match the script the loop
            # actually runs, and exclude dispatch workers explicitly.
            "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            r"Where-Object { $_.CommandLine -match 'build_loop\.py' -and "
            r"$_.CommandLine -notmatch 'dispatch\.py' } | "
            "Measure-Object).Count",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return (out.stdout or "0").strip() not in ("", "0")


def save(state: dict) -> None:
    tmp = STATE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(state, indent=1))
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, STATE)


def main() -> int:
    # The refusal. Added 29 August 2026 because this script is what a reader reaches for when
    # they want to restart the loop, and it does two unrelated things at once -- one of them a
    # five-day-old retirement list. Requiring the flag makes running it a decision rather than
    # a guess, and costs the one person who genuinely wants it a single word.
    if "--apply" not in sys.argv:
        print(__doc__)
        print(
            "REFUSING: this would force-retire "
            + str(len(FORCE_DONE))
            + " unit(s) -- "
            + ", ".join(FORCE_DONE)
            + " -- on 24 August 2026 reasoning, then delete STOP-LOOP and start the loop."
        )
        print("Re-run with --apply if that is genuinely what you want.")
        return 2

    with LOG.open("a", encoding="utf-8") as log:
        deadline = time.time() + 3600
        while loop_alive() and time.time() < deadline:
            time.sleep(20)
        log.write(f"{time.strftime('%H:%M:%S')} loop quiet; applying repairs\n")

        state = json.loads(STATE.read_text(encoding="utf-8"))
        state["force_done"] = sorted(set(state.get("force_done", [])) | set(FORCE_DONE))
        for uid in state["force_done"]:
            if uid not in state["done"]:
                state["done"].append(uid)
            state.get("conflicts", {}).pop(uid, None)
            state.get("in_flight", {}).pop(uid, None)
            if uid in state.get("resolve_dispatched", []):
                state["resolve_dispatched"].remove(uid)
        state.setdefault("note", []).append(
            "24 Aug 2026: force_done set for hand-merged units. A unit merged by hand cannot be "
            "retired by commit match -- the merge sha is not the one the plan recorded -- so the "
            "driver re-tried the original, conflicted, and re-opened work already in the tree."
        )
        save(state)
        log.write(
            f"{time.strftime('%H:%M:%S')} force_done={state['force_done']} "
            f"done={len(state['done'])} conflicts={sorted(state.get('conflicts', {}))}\n"
        )

        STOP.unlink(missing_ok=True)
        subprocess.Popen(
            [sys.executable, "-u", str(ROOT / ".harness" / "build_loop.py")],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        log.write(f"{time.strftime('%H:%M:%S')} loop restarted\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

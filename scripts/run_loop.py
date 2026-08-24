"""Supervise one always-on loop. Every tick lands in the trajectory.

    python scripts/run_loop.py                       # run the default capture loop
    python scripts/run_loop.py --status --json       # what has it produced?
    python scripts/run_loop.py --stop                # the kill switch
    python scripts/run_loop.py --interval 60 -- python scripts/capture_health.py

The policy — what is recorded, where a tick may run, when the budget refuses one, what
"working" means — is `consilient.loop`, which has no execution capability by design. This
file holds the parts that must touch the operating system, and each of them exists because
something on this machine failed without it:

* **Output goes to a file, never a pipe.** `subprocess` timeouts do not kill grandchildren,
  and overruns of 10-269 seconds past the deadline were measured here because descendants
  held the pipes open. With no pipes there is nothing to hold, and `wait()` cannot block on
  one. It also means no text-mode decoding of the child's output, so cp1252 never gets a
  chance; the one text-mode subprocess in this file is `taskkill`, and it sets
  `encoding="utf-8", errors="replace"` as the rule requires.
* **The kill is a tree kill, by identity.** `taskkill /F /T` on Windows, the process group
  on POSIX, both against the PID we started. Never a name pattern: a `pkill -f` here once
  matched nothing while two unrelated agents ran, and a blind kill would have destroyed
  correct work (R11).
* **The stop file is checked inside the tick**, not only between ticks, so it works while
  the loop is wedged.
* **One instance at a time**, held with an OS lock that the kernel releases when the
  process dies. A lock file that outlived a crash would leave the loop unable to restart,
  which is the opposite of what an always-on loop needs.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient import loop as loop_mod  # noqa: E402
from consilient.budget import Ceiling  # noqa: E402
from consilient.loop import Loop, LoopError  # noqa: E402

POLL_S = 0.2
KILL_TIMEOUT_S = 30


def kill_tree(process: subprocess.Popen[bytes]) -> None:
    """Kill the process and every descendant of it. A timeout alone does not."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=KILL_TIMEOUT_S,
            check=False,
        )
    else:
        import signal

        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except OSError:
            pass
    try:
        process.kill()
    except OSError:
        pass


@contextmanager
def single_instance(loop: Loop) -> Iterator[None]:
    """An OS lock the kernel drops when this process dies, however it dies."""
    loop.lock_file.parent.mkdir(parents=True, exist_ok=True)
    handle = loop.lock_file.open("a+b")
    try:
        handle.seek(0)
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        handle.close()
        raise LoopError(
            f"another {loop.name!r} loop already holds {loop.lock_file}"
        ) from exc
    try:
        yield
    finally:
        handle.close()


def execute(loop: Loop, tick: int) -> dict[str, Any]:
    """Run one tick and report what it produced, not whether it exited."""
    loop.transcript.parent.mkdir(parents=True, exist_ok=True)
    before = loop.transcript.stat().st_size if loop.transcript.exists() else 0
    began = time.monotonic()
    interrupted = ""
    extra: dict[str, Any] = {} if os.name == "nt" else {"start_new_session": True}
    with loop.transcript.open("ab") as sink:
        try:
            process = subprocess.Popen(
                list(loop.command),
                cwd=str(loop.root),
                stdin=subprocess.DEVNULL,
                stdout=sink,
                stderr=subprocess.STDOUT,
                **extra,
            )
        except OSError as exc:
            # A command that will not start will not start on the next tick either. R12:
            # a refusal is a repairable dispatch fault, not a bad result, and it is not
            # the same thing as a failure.
            return {
                "outcome": "refused",
                "exit_code": None,
                "produced_bytes": 0,
                "seconds": 0.0,
                "detail": str(exc),
            }
        deadline = began + loop.timeout_s
        while process.poll() is None:
            if time.monotonic() >= deadline:
                interrupted = "timeout"
            elif loop.stop_file.exists():
                interrupted = "killed"
            if interrupted:
                kill_tree(process)
                break
            time.sleep(POLL_S)
        try:
            code = process.wait(timeout=KILL_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            kill_tree(process)
            code, interrupted = -1, interrupted or "timeout"
    produced = loop.transcript.stat().st_size - before
    if interrupted:
        outcome = interrupted
    elif code != 0:
        outcome = "failed"
    elif produced <= 0:
        # Exit 0 and not one byte. Two dispatches on this machine "succeeded" this way
        # having never started at all, so it is reported as its own outcome (R1, R13).
        outcome = "silent"
    else:
        outcome = "completed"
    return {
        "outcome": outcome,
        "exit_code": code,
        "produced_bytes": produced,
        "seconds": round(time.monotonic() - began, 3),
        "transcript": loop.transcript.name,
    }


def _stop(loop: Loop, tick: int, reason: str) -> dict[str, Any]:
    loop_mod.record(loop, loop_mod.LOOP_STOPPED, tick, {"reason": reason})
    return loop_mod.status(loop)


def _wait(loop: Loop) -> bool:
    """Sleep the interval in slices. False if a stop was requested while waiting."""
    until = time.monotonic() + loop.interval_s
    while time.monotonic() < until:
        if loop.stop_file.exists():
            return False
        time.sleep(min(POLL_S, loop.interval_s))
    return not loop.stop_file.exists()


def run(loop: Loop) -> dict[str, Any]:
    """Tick until stopped, refused or capped. Returns the loop's status."""
    refused = loop_mod.refusal(loop)
    if refused is not None:
        raise LoopError(refused)
    # A kill switch a scheduled restart can clear is not a kill switch. The stop stands
    # until someone lifts it with `--resume`.
    if loop.stop_file.exists():
        raise LoopError(
            f"a stop is in force at {loop.stop_file}; lift it with --resume"
        )
    with single_instance(loop):
        tick = loop_mod.resume(loop)
        silent_ticks = 0
        while True:
            if loop.stop_file.exists():
                return _stop(loop, tick, "a stop was requested")
            if loop.max_ticks is not None and tick > loop.max_ticks:
                return _stop(loop, tick, "the tick ceiling was reached")
            denied = loop_mod.reserve(loop, tick)
            if denied is not None:
                return _stop(loop, tick, f"the budget refused this tick: {denied}")
            loop_mod.record(
                loop,
                loop_mod.TICK_STARTED,
                tick,
                {
                    "command": list(loop.command),
                    "transcript_bytes": (
                        loop.transcript.stat().st_size
                        if loop.transcript.exists()
                        else 0
                    ),
                },
            )
            result = execute(loop, tick)
            loop_mod.record(loop, loop_mod.TICK_FINISHED, tick, result)
            if result["outcome"] == "silent":
                silent_ticks += 1
                if silent_ticks >= loop_mod.STALE_CYCLES:
                    return _stop(
                        loop,
                        tick,
                        f"{silent_ticks} consecutive silent ticks produced no bytes",
                    )
            else:
                silent_ticks = 0
            if result["outcome"] == "killed":
                return _stop(loop, tick, "a stop was requested mid-tick")
            if result["outcome"] == "refused":
                return _stop(
                    loop, tick, f"the command will not start: {result['detail']}"
                )
            tick += 1
            if not _wait(loop):
                return _stop(loop, tick, "a stop was requested")


def build(args: argparse.Namespace) -> Loop:
    root = Path(args.root).resolve()
    ceilings = []
    for period, amount in (("weekly", args.weekly), ("monthly", args.monthly)):
        if amount is not None:
            ceilings.append(Ceiling(period, Decimal(amount), "USD"))
    return Loop(
        name=args.name,
        root=root,
        log_dir=Path(args.log).resolve(),
        command=tuple(args.command) or (sys.executable, "scripts/capture_health.py"),
        interval_s=args.interval,
        timeout_s=args.timeout,
        cost_per_tick=Decimal(args.cost),
        ceilings=tuple(ceilings),
        max_ticks=args.max_ticks,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Supervise one always-on loop.")
    parser.add_argument("--name", default="capture")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--log", default=str(ROOT / ".harness" / "log"))
    parser.add_argument("--interval", type=float, default=3600.0)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--max-ticks", type=int, default=None)
    parser.add_argument("--cost", default="0", help="USD per tick; 0 spends nothing")
    parser.add_argument("--weekly", default=None, help="USD weekly ceiling")
    parser.add_argument("--monthly", default=None, help="USD monthly ceiling")
    parser.add_argument("--status", action="store_true", help="report what it produced")
    parser.add_argument("--stop", action="store_true", help="the kill switch")
    parser.add_argument("--resume", action="store_true", help="lift a standing stop")
    parser.add_argument("--json", action="store_true")
    # The brief is delivered by reference and the command after `--` is never interpolated
    # into a shell, because a brief containing backticks was once partly executed on its
    # way to an agent (R8).
    parser.add_argument("command", nargs="*", help="the tick command, after `--`")
    return parser


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        loop = build(args)
    except (ArithmeticError, InvalidOperation, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        if args.stop:
            loop.stop_file.parent.mkdir(parents=True, exist_ok=True)
            loop.stop_file.write_text("stop\n", encoding="utf-8")
            result = loop_mod.status(loop)
        elif args.resume:
            loop.stop_file.unlink(missing_ok=True)
            result = loop_mod.status(loop)
        elif args.status:
            result = loop_mod.status(loop)
        else:
            result = run(loop)
    except LoopError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"{result['loop']}: {'working' if result['working'] else 'not working'} — "
            f"{result['reason']}"
        )
        print(
            f"  ticks started={result['ticks_started']} finished={result['ticks_finished']}"
            f" abandoned={result['ticks_abandoned']} silent={result['ticks_silent']},"
            f" {result['bytes_produced']} byte(s) produced"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Watch a child harness, bound it, and report what it did.

Two cursor-agent processes race ~/.cursor/cli-config.json [measured], and the exclusive
file lock here is the check that forbids that overlap; a dry run must never enter it.
The process-tree kill sits beside it because a subprocess deadline does not reach
grandchildren, and the chunked stream drain records when the first chunk and the first
non-empty chunk arrived, so a run that produced nothing is distinguishable from one that
produced something late.

Two records name the ways a dispatch fails without dying. A start failure never produced
a first artefact inside its window; a stall notified start and then went quiet, because
the started line answers "did it start?", not "is it healthy?". ADR-0034 §6 requires a
stall decision to record the signal, the threshold, the observed value and the action
taken, so an operator can dispute it from the record alone — and the action is never
termination, because killing is the irreversible half and the expensive production
failure is a watchdog that acts on live work. Neither record consumes a work attempt: an
infrastructure death is not evidence about the work (F-05 / F-13).

The rest is reporting — the human rendering of a dispatch payload, and the outcome event
appended to the trajectory with the gap classification a non-ok status implies. Nothing
here decides anything. It holds, kills, drains, records and prints, and refuses to turn
any of that into a verdict."""

from __future__ import annotations
import os
import shlex
import signal
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Any

# Self-contained on purpose: every destination of a split needs this line, and a sibling below
# the layer that defines ROOT cannot import it. The expression is what ROOT is, and every file
# of the family sits in this same directory, so it computes the same path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient.events import (
    SCHEMA_VERSION,
    append,
)
from consilient.harness import (
    Harness,
    DISPATCH_ACTOR,
    DISPATCH_OUTCOME_KIND,
    classify_gap,
    record_gap,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class ExclusiveFileLock:
    """Process-exclusive lock. Two cursor-agent processes race ~/.cursor/cli-config.json
    [measured]; this is the check that forbids that overlap. Dry-run must not enter it.
    """

    def __init__(self, path: Path, *, timeout_s: float) -> None:
        self.path = path
        self.timeout_s = timeout_s
        self._fh: Any = None

    def __enter__(self) -> ExclusiveFileLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self.path, "a+b")
        self._fh = handle
        deadline = time.monotonic() + max(0.0, self.timeout_s)
        while True:
            try:
                self._lock_nonblocking()
                return self
            except OSError:
                if time.monotonic() >= deadline:
                    handle.close()
                    self._fh = None
                    raise TimeoutError(
                        f"cursor-agent lock held: could not acquire {self.path} "
                        f"within {self.timeout_s}s"
                    ) from None
                time.sleep(0.05)

    def _lock_nonblocking(self) -> None:
        handle = self._fh
        if handle is None:
            raise OSError("lock file is not open")
        handle.seek(0)
        if handle.read(1) == b"":
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def __exit__(self, *_exc: object) -> None:
        handle = self._fh
        if handle is None:
            return
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()
            self._fh = None


def kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass
    if process.poll() is None:
        try:
            process.kill()
        except (ProcessLookupError, PermissionError, OSError):
            pass


def _pipe_bytes_available(fd: int) -> int:
    """How many bytes can be read without blocking. 0 means wait for the next write."""
    if os.name == "nt":
        import ctypes
        import msvcrt

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        peek = kernel32.PeekNamedPipe
        peek.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong),
        ]
        peek.restype = ctypes.c_int
        try:
            handle = msvcrt.get_osfhandle(fd)
        except OSError:
            return 0
        avail = ctypes.c_ulong(0)
        if not peek(handle, None, 0, None, ctypes.byref(avail), None):
            return 0
        return int(avail.value)
    import select

    ready, _, _ = select.select([fd], [], [], 0)
    return 65536 if ready else 0


def _stamp_from_mono(
    origin_wall: datetime, origin_mono: float, event_mono: float
) -> str:
    elapsed = max(0.0, event_mono - origin_mono)
    return (origin_wall + timedelta(seconds=elapsed)).isoformat()


def _drain_stream(
    pipe: Any,
    out_path: Path,
    *,
    origin_wall: datetime,
    origin_mono: float,
) -> tuple[int, str | None, str | None]:
    """Observe provider flushes, not a buffered EOF.

    ``BufferedReader.read(n)`` on Windows waits for n bytes or close, so two
    flushed writes 1.2s apart collapse into one chunk timestamped at EOF.
    AIPerf stamps each non-empty content response with a monotonic clock
    (``content_responses[0].perf_ns - request.start_perf_ns``); we do the
    same at the pipe: block for the first byte, drain what is already
    available as one chunk, repeat.
    """
    try:
        raw = pipe.detach()
    except (AttributeError, ValueError):
        raw = pipe
    fd = raw.fileno()
    n_chunks = 0
    t_first: str | None = None
    t_first_nonempty: str | None = None
    with out_path.open("wb") as handle:
        while True:
            try:
                first = os.read(fd, 1)
            except OSError:
                break
            if not first:
                break
            event_mono = time.perf_counter()
            extra = bytearray()
            while True:
                avail = _pipe_bytes_available(fd)
                if avail <= 0:
                    break
                piece = os.read(fd, avail)
                if not piece:
                    break
                extra.extend(piece)
            chunk = first + bytes(extra)
            stamp = _stamp_from_mono(origin_wall, origin_mono, event_mono)
            n_chunks += 1
            if t_first is None:
                t_first = stamp
            if t_first_nonempty is None and chunk.strip():
                t_first_nonempty = stamp
            handle.write(chunk)
            handle.flush()
    return n_chunks, t_first, t_first_nonempty


@dataclass(frozen=True)
class StartFailure:
    """One open dispatch that never produced a first artefact.

    ADR-0034 §6: a stall decision records the signal, the threshold, the observed
    value and the action taken, so an operator can dispute it from the record alone.
    The action is never termination — §3 defaults to diagnosis, because killing is the
    irreversible half and the expensive production failure is a watchdog that acts on
    live work.

    A start failure does not consume a work attempt: an infrastructure death is
    not evidence about the work (F-05 / F-13).
    """

    run_id: str
    harness: str | None
    signal: str
    threshold_s: int
    observed_s: float
    observed_bytes: int
    action: str
    consumes_attempt: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "harness": self.harness,
            "signal": self.signal,
            "threshold_s": self.threshold_s,
            "observed_s": self.observed_s,
            "observed_bytes": self.observed_bytes,
            "action": self.action,
            "consumes_attempt": self.consumes_attempt,
        }


@dataclass(frozen=True)
class Stall:
    """A dispatch that declared start and then produced no further progress.

    The started line is s6's notification, not a health signal. Treating it as
    healthy is startsecs by another name. [cited, skarnet.org/software/s6]
    """

    run_id: str
    harness: str | None
    signal: str
    threshold_s: int
    observed_s: float
    action: str

    def as_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "harness": self.harness,
            "signal": self.signal,
            "threshold_s": self.threshold_s,
            "observed_s": self.observed_s,
            "action": self.action,
        }


def _print_human(payload: dict[str, object]) -> None:
    status = str(payload.get("status", ""))
    print(f"status: {status}")
    if "reason" in payload:
        print(f"reason: {payload['reason']}")
    if "harness" in payload:
        print(
            f"harness: {payload['harness']} ({payload.get('family')}, {payload.get('pool')})"
        )
    if "selected" in payload:
        print(f"selected: {payload['selected']}")
    if "first" in payload and isinstance(payload["first"], dict):
        first = payload["first"]
        second = payload.get("second")
        print(
            f"first: {first.get('harness')} {first.get('status')} "
            f"({first.get('artefact_bytes')} bytes)"
        )
        if isinstance(second, dict):
            print(
                f"second: {second.get('harness')} {second.get('status')} "
                f"({second.get('artefact_bytes')} bytes)"
            )
        print(f"verdict: {payload.get('verdict')}")
        for label in ("first", "second"):
            row = payload.get(label)
            if isinstance(row, dict):
                tail = row.get("stdout_tail")
                if isinstance(tail, str) and tail.strip():
                    print(f"--- {row.get('harness')} ---")
                    print(tail.strip())
    if "artefact_bytes" in payload:
        print(f"artefact: {payload['artefact_bytes']} bytes")
    if "open_dispatches" in payload:
        print(f"open dispatches: {payload['open_dispatches']}")
    started_never = payload.get("start_failed")
    if isinstance(started_never, list):
        print(f"start_failed: {len(started_never)}")
        for row in started_never:
            if not isinstance(row, dict):
                continue
            print(
                f"  {row.get('run_id')} ({row.get('harness')}): {row.get('signal')}; "
                f"threshold {row.get('threshold_s')}s, observed "
                f"{row.get('observed_s')}s and {row.get('observed_bytes')} bytes; "
                f"action {row.get('action')}"
            )
    stalled = payload.get("stalled")
    if isinstance(stalled, list):
        print(f"stalled: {len(stalled)}")
        for row in stalled:
            if not isinstance(row, dict):
                continue
            print(
                f"  {row.get('run_id')} ({row.get('harness')}): {row.get('signal')}; "
                f"threshold {row.get('threshold_s')}s, observed "
                f"{row.get('observed_s')}s; action {row.get('action')}"
            )
    command = payload.get("command")
    if isinstance(command, list) and command:
        print("command: " + shlex.join(str(part) for part in command))
    if "recorded" in payload:
        print(f"recorded: {payload['recorded']}")
    stdout_tail = payload.get("stdout_tail")
    if isinstance(stdout_tail, str) and stdout_tail.strip():
        print("--- stdout ---")
        print(stdout_tail.strip())
    rows = payload.get("harnesses")
    if isinstance(rows, list):
        print(
            f"{'id':<18} {'family':<10} {'pool':<16} {'installed':<10} {'used':<8} note"
        )
        for row in rows:
            if not isinstance(row, dict):
                continue
            used = row.get("used_percent")
            used_s = "unknown" if used is None else f"{used:g}%"
            installed = "yes" if row.get("installed") else "no"
            print(
                f"{str(row.get('id')):<18} {str(row.get('family')):<10} "
                f"{str(row.get('pool')):<16} {installed:<10} {used_s:<8} "
                f"{row.get('note') or ''}"
            )
            print(f"  probe: {row.get('probe')}")


def _record_dispatch_outcome(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    task: str,
    cwd: str,
    harness: Harness,
    status: str,
    reason: str,
    exit_code: int | None,
    artefact_bytes: int,
    diff_bytes: int,
    timed_out: bool,
    duration_s: float,
    command: Sequence[str],
    assembly_id: str | None = None,
    output_records: Mapping[str, object] | None = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "run_id": run_id,
        "task": task,
        "cwd": cwd,
        "harness": harness.id,
        "family": harness.family,
        "pool": harness.pool,
        "status": status,
        "reason": reason,
        "exit_code": exit_code,
        "artefact_bytes": artefact_bytes,
        "diff_bytes": diff_bytes,
        "timed_out": timed_out,
        "duration_s": duration_s,
        "command": list(command),
        "supervised": True,
    }
    if assembly_id is not None:
        data["assembly_id"] = assembly_id
    if output_records is not None:
        data["output_records"] = dict(output_records)
    recorded = append(
        log_dir / f"{ts[:10]}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": DISPATCH_OUTCOME_KIND,
            "actor": DISPATCH_ACTOR,
            "data": data,
        },
    )
    gap = classify_gap(status, reason)
    if gap is not None:
        failure, closure, repair = gap
        record_gap(
            log_dir,
            ts=ts,
            run_id=run_id,
            task=task,
            cwd=cwd,
            attempted=harness.id,
            failure=failure,
            detail=reason,
            closure=closure,
            repair=repair,
            source=DISPATCH_OUTCOME_KIND,
        )
    return recorded

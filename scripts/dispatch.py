"""Probe subscription harnesses, select by headroom, run, and record the result."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.dispatch import (  # noqa: E402
    DispatchRefused,
    Harness,
    REGISTRY,
    select_harnesses,
)
from consilient.events import EventPayload, append  # noqa: E402

LOG_DIR = ROOT / ".harness" / "log"
OUTPUT_ROOT = ROOT / ".harness" / "dispatch"
SILENT_MARKERS = ("workspace trust required",)
METERED_KEYS = {
    "claude": ("ANTHROPIC_API_KEY",),
    "cursor-composer": ("CURSOR_API_KEY",),
    "grok": ("XAI_API_KEY", "GROK_CODE_XAI_API_KEY", "GROK_API_KEY"),
    "codex": ("OPENAI_API_KEY", "CODEX_API_KEY"),
}
SAFE_ENVIRONMENT_NAMES = frozenset(
    {
        "ALLUSERSPROFILE",
        "APPDATA",
        "COMMONPROGRAMFILES",
        "COMMONPROGRAMFILES(X86)",
        "COMMONPROGRAMW6432",
        "COMSPEC",
        "DRIVERDATA",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "LANG",
        "LC_ALL",
        "LOCALAPPDATA",
        "LOGNAME",
        "NUMBER_OF_PROCESSORS",
        "OS",
        "PATH",
        "PATHEXT",
        "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_IDENTIFIER",
        "PROCESSOR_LEVEL",
        "PROCESSOR_REVISION",
        "PROGRAMDATA",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMW6432",
        "PUBLIC",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TERM",
        "TMP",
        "USER",
        "USERDOMAIN",
        "USERNAME",
        "USERPROFILE",
        "WINDIR",
    }
)
WINDOWS_CREATE_SUSPENDED = 0x00000004
# ponytail: process-local lock; add a file lock if concurrent dispatcher processes matter.
APPEND_LOCK = threading.Lock()


@dataclass(frozen=True)
class Probe:
    harness: Harness
    installed: bool
    executable: str | None
    detail: str


def is_direct_executable(path: Path) -> bool:
    return os.name != "nt" or path.suffix.casefold() in {".exe", ".com"}


def _native_executable(name: str) -> str | None:
    command = {"claude": "claude", "grok": "grok", "codex": "codex"}[name]
    if name == "grok" and os.name == "nt":
        candidate = Path.home() / ".grok" / "bin" / "grok.exe"
        if candidate.is_file() and is_direct_executable(candidate):
            return str(candidate)
    found = shutil.which(command)
    if name == "codex" and found is not None and os.name == "nt":
        package = Path(found).parent / "node_modules" / "@openai" / "codex"
        for relative in (
            Path("node_modules/@openai/codex-win32-x64/vendor")
            / "x86_64-pc-windows-msvc/bin/codex.exe",
            Path("node_modules/@openai/codex-win32-arm64/vendor")
            / "aarch64-pc-windows-msvc/bin/codex.exe",
        ):
            candidate = package / relative
            if candidate.is_file() and is_direct_executable(candidate):
                return str(candidate)
    return found if found is not None and is_direct_executable(Path(found)) else None


def probe_harness(harness: Harness) -> Probe:
    """Resolve an executable without making a model or metered call."""
    if harness.name != "cursor-composer":
        executable = _native_executable(harness.name)
        return Probe(
            harness,
            executable is not None,
            executable,
            "direct executable resolved"
            if executable
            else "safe direct executable not found",
        )

    wsl = shutil.which("wsl")
    if wsl is None:
        return Probe(harness, False, None, "wsl executable not found")
    try:
        completed = subprocess.run(
            [
                wsl,
                "-e",
                "bash",
                "-lc",
                'test -x "$HOME/.local/bin/cursor-agent"',
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=sanitise_environment(os.environ),
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Probe(harness, False, None, f"WSL probe failed: {type(exc).__name__}")
    return Probe(
        harness,
        completed.returncode == 0,
        wsl if completed.returncode == 0 else None,
        "cursor-agent reachable through WSL"
        if completed.returncode == 0
        else "cursor-agent not found in WSL",
    )


def probe_registry() -> tuple[Probe, ...]:
    return tuple(probe_harness(harness) for harness in REGISTRY)


def to_wsl_path(path: Path) -> str:
    absolute = str(path.resolve()).replace("\\", "/")
    if len(absolute) < 3 or absolute[1:3] != ":/":
        raise DispatchRefused(f"Cursor requires a Windows drive path, got {absolute!r}")
    return f"/mnt/{absolute[0].lower()}/{absolute[3:]}"


def build_command(probe: Probe, brief_path: Path, cwd: Path) -> list[str]:
    """Fill structured argv; untrusted values never enter Cursor's shell program."""
    if not probe.installed or probe.executable is None:
        raise DispatchRefused(f"{probe.harness.name} is not installed")
    harness = probe.harness
    if harness.name == "cursor-composer":
        brief_prompt = f"Read and follow the task in {to_wsl_path(brief_path)}"
        return [
            probe.executable,
            *harness.invocation[1:-2],
            to_wsl_path(cwd),
            brief_prompt,
        ]
    brief_prompt = f"Read and follow the task in {brief_path.resolve()}"
    return [
        probe.executable,
        *(
            brief_prompt
            if part == "{brief}"
            else str(cwd.resolve())
            if part == "{cwd}"
            else part
            for part in harness.invocation[1:]
        ),
    ]


def refuse_metered_environment(
    harness: Harness, environ: Mapping[str, str]
) -> None:
    """Fail closed on credential presence without reading or printing its value."""
    for key in METERED_KEYS.get(harness.name, ()):
        if key in environ:
            raise DispatchRefused(
                f"{harness.name} refused because {key} could select metered API billing"
            )


def sanitise_environment(environ: Mapping[str, str]) -> dict[str, str]:
    """Copy the small runtime allow-list without retrieving excluded values."""
    return {
        key: environ[key]
        for key in environ
        if key.upper() in SAFE_ENVIRONMENT_NAMES
    }


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def record_event(log_dir: Path, event: EventPayload) -> None:
    stamp = event["ts"]
    if not isinstance(stamp, str):
        raise ValueError("event timestamp must be a string")
    with APPEND_LOCK:
        append(log_dir / f"{stamp[:10]}.jsonl", event)


class _WindowsJob:
    """Own a Windows process tree and kill every member when closed."""

    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimits),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        ntdll = ctypes.WinDLL("ntdll")
        ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        ntdll.NtResumeProcess.restype = wintypes.LONG
        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x00002000
        assigned = kernel32.SetInformationJobObject(
            handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ) and kernel32.AssignProcessToJobObject(
            handle, wintypes.HANDLE(getattr(process, "_handle"))
        )
        if not assigned:
            error = ctypes.get_last_error()
            kernel32.CloseHandle(handle)
            raise ctypes.WinError(error)
        self._kernel32 = kernel32
        self._handle = handle
        self._ntdll = ntdll
        self._process_handle = wintypes.HANDLE(getattr(process, "_handle"))

    def resume(self) -> None:
        status = self._ntdll.NtResumeProcess(self._process_handle)
        if status != 0:
            raise OSError(f"NtResumeProcess failed with NTSTATUS {status:#x}")

    def close(self) -> None:
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None


def _kill_process_tree(
    process: subprocess.Popen[bytes], job: _WindowsJob | None = None
) -> None:
    if job is not None:
        job.close()
    if os.name != "nt":
        try:
            killpg = getattr(os, "killpg")
            sigkill = getattr(signal, "SIGKILL")
            killpg(process.pid, sigkill)
        except (ProcessLookupError, PermissionError):
            pass
    if process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def _dispatch_event(kind: str, data: dict[str, object]) -> EventPayload:
    return {
        "v": 1,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": kind,
        "actor": "consilient.dispatch",
        "data": {**data, "supervised": True},
    }


def run_harness(
    harness: Harness,
    command: list[str],
    *,
    task: str,
    cwd: Path,
    log_dir: Path,
    output_root: Path,
    timeout_s: float,
    run_id: str,
) -> dict[str, object]:
    """Run one harness with file-backed output and a hard process-tree deadline."""
    attempt_id = f"{run_id}:{harness.name}"
    common: dict[str, object] = {
        "run_id": run_id,
        "attempt_id": attempt_id,
        "task": task,
        "cwd": str(cwd.resolve()),
        "harness": harness.name,
        "model_family": harness.family,
        "pool": harness.pool,
        "used_percent": harness.used_percent,
        "headroom_percent": harness.headroom_percent,
        "headroom_state": harness.headroom_state,
        "headroom_source": harness.headroom_source,
        "command": command,
    }
    record_event(log_dir, _dispatch_event("dispatch.started", common))

    output_dir = output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = output_dir / f"{harness.name}.stdout.txt"
    stderr_path = output_dir / f"{harness.name}.stderr.txt"
    started = time.monotonic()
    process: subprocess.Popen[bytes] | None = None
    job: _WindowsJob | None = None
    tree_closed = False
    timed_out = False
    error: str | None = None

    process_options: dict[str, Any] = {}
    if os.name == "nt":
        process_options["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | WINDOWS_CREATE_SUSPENDED
        )
    else:
        process_options["start_new_session"] = True

    with (
        stdout_path.open("wb") as stdout_file,
        stderr_path.open("wb") as stderr_file,
    ):
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                env=sanitise_environment(os.environ),
                **process_options,
            )
            if os.name == "nt":
                try:
                    job = _WindowsJob(process)
                    job.resume()
                except OSError:
                    _kill_process_tree(process, job)
                    tree_closed = True
                    raise
            try:
                process.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
                _kill_process_tree(process, job)
                tree_closed = True
        except OSError as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            if process is not None and not tree_closed:
                if job is not None:
                    job.close()
                elif os.name != "nt":
                    _kill_process_tree(process)

    stdout_bytes = stdout_path.read_bytes()
    stderr_bytes = stderr_path.read_bytes()
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    stdout_bytes = stdout.encode("utf-8")
    stderr_bytes = stderr.encode("utf-8")
    stdout_path.write_bytes(stdout_bytes)
    stderr_path.write_bytes(stderr_bytes)
    combined = f"{stdout}\n{stderr}".casefold()
    marker = next((item for item in SILENT_MARKERS if item in combined), None)
    exit_code = process.returncode if process is not None else None
    if timed_out:
        status = "timeout"
    elif error is not None:
        status = "unavailable"
    elif marker is not None:
        status = "silent"
    elif exit_code != 0:
        status = "error"
    elif not stdout.strip():
        status = "silent"
    else:
        status = "produced"

    artefact_present = marker is None and bool(stdout.strip())

    result: dict[str, object] = {
        "run_id": run_id,
        "attempt_id": attempt_id,
        "harness": harness.name,
        "model_family": harness.family,
        "pool": harness.pool,
        "headroom_percent": harness.headroom_percent,
        "status": status,
        "artefact_present": artefact_present,
        "verified": False,
        "exit_code": exit_code,
        "duration_s": round(time.monotonic() - started, 3),
        "stdout_path": str(stdout_path.resolve()),
        "stderr_path": str(stderr_path.resolve()),
        "output_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
        "output": stdout.rstrip(),
    }
    completed = {
        **common,
        **{key: value for key, value in result.items() if key != "output"},
        "timed_out": timed_out,
        "silent_reason": marker or (
            "empty stdout" if status == "silent" and not stdout.strip() else None
        ),
        "error": error,
    }
    record_event(log_dir, _dispatch_event("dispatch.completed", completed))
    return result


def _probe_rows(probes: Sequence[Probe]) -> list[dict[str, object]]:
    return [
        {
            "harness": probe.harness.name,
            "model_family": probe.harness.family,
            "pool": probe.harness.pool,
            "installed": probe.installed,
            "used_percent": probe.harness.used_percent,
            "headroom_percent": probe.harness.headroom_percent,
            "headroom_state": probe.harness.headroom_state,
            "headroom_source": probe.harness.headroom_source,
            "invocation": list(probe.harness.invocation),
            "probe": probe.detail,
        }
        for probe in probes
    ]


def _print_probe(probes: Sequence[Probe], *, as_json: bool) -> None:
    rows = _probe_rows(probes)
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, sort_keys=True))
        return
    for row in rows:
        headroom = (
            f"{row['headroom_percent']}%"
            if row["headroom_percent"] is not None
            else row["headroom_state"]
        )
        reachable = "yes" if row["installed"] else "no"
        print(
            f"{row['harness']}: reachable={reachable} pool={row['pool']} "
            f"headroom={headroom} ({row['headroom_source']}); {row['probe']}"
        )


def _record_refusal(task: str, cwd: Path, reason: str) -> None:
    record_event(
        LOG_DIR,
        _dispatch_event(
            "dispatch.refused",
            {"run_id": uuid4().hex, "task": task, "cwd": str(cwd), "reason": reason},
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="?", help="task sent to the selected harness")
    parser.add_argument("--cwd", type=Path, help="absolute or relative working directory")
    parser.add_argument("--harness", choices=[item.name for item in REGISTRY])
    parser.add_argument("--fan-out", action="store_true", help="run two model families")
    parser.add_argument("--supervised", action="store_true", help="confirm a human can stop this run")
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--probe", action="store_true", help="show registry and reachability")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.probe:
        probes = probe_registry()
        _print_probe(probes, as_json=args.json)
        return 0
    if args.task is None or not args.task.strip() or args.cwd is None:
        parser.error("a non-empty task and --cwd are required")
    if not args.supervised:
        parser.error("--supervised is required while Gate B is closed")
    if args.fan_out and args.harness is not None:
        parser.error("--fan-out and --harness cannot be combined")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")

    cwd = args.cwd.resolve()
    if not cwd.is_dir():
        parser.error(f"working directory does not exist: {cwd}")
    probes = probe_registry()
    installed = {probe.harness.name: probe.installed for probe in probes}
    try:
        selected = select_harnesses(
            installed,
            count=2 if args.fan_out else 1,
            requested=args.harness,
        )
        by_name = {probe.harness.name: probe for probe in probes}
        for harness in selected:
            refuse_metered_environment(harness, os.environ)
    except DispatchRefused as exc:
        _record_refusal(args.task, cwd, str(exc))
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    brief_dir = (OUTPUT_ROOT / run_id).resolve()
    brief_dir.mkdir(parents=True, exist_ok=True)
    brief_path = brief_dir / "brief.txt"
    brief_path.write_text(args.task, encoding="utf-8", errors="strict")
    commands = [
        build_command(by_name[harness.name], brief_path, cwd)
        for harness in selected
    ]
    work = list(zip(selected, commands, strict=True))

    def execute(item: tuple[Harness, list[str]]) -> dict[str, object]:
        harness, command = item
        return run_harness(
            harness,
            command,
            task=args.task,
            cwd=cwd,
            log_dir=LOG_DIR,
            output_root=OUTPUT_ROOT,
            timeout_s=args.timeout,
            run_id=run_id,
        )

    results = [execute(item) for item in work]

    if args.json:
        print(
            json.dumps(
                {"run_id": run_id, "results": results},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    else:
        print(f"run_id: {run_id}")
        for result in results:
            print(
                f"[{result['harness']}] status={result['status']} "
                f"exit={result['exit_code']} pool={result['pool']} "
                f"headroom={result['headroom_percent']}%"
            )
            if result["output"]:
                print(result["output"])
            print(f"artefact: {result['stdout_path']}")
    return 0 if all(result["status"] == "produced" for result in results) else 1


if __name__ == "__main__":
    configure_console()
    raise SystemExit(main())

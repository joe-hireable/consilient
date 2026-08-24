"""Kill a process and every descendant, atomically enough that none escapes.

MEASURED 24 August 2026. `taskkill /T /F` is not atomic with the deadline. `wait()` expires,
then taskkill spends roughly 0.9 s enumerating and killing, and every descendant keeps running
for the whole of that interval. Reproduced with a one-second timeout: the runner returned at
1.91 s and a grandchild writing its file at 1.5 s escaped on every attempt. The same defect was
found independently in `memory_refresh.py` and `promote_loop.py`, which is why the fix lives
here rather than in either of them -- two copies of a broken kill is how a third gets written.

On Windows the primitive that closes the window is a Job Object: descendants inherit membership
at creation, and `TerminateJobObject` kills the whole tree in a single call. Assignment races
only the few microseconds between `CreateProcess` returning and the child spawning anything,
which is far tighter than the interval it replaces. `taskkill` and `killpg` remain the fallback
for when the job cannot be created.
"""

from __future__ import annotations

import os
import signal
import subprocess

KILL_TIMEOUT_S = 10.0
_KILL_ON_JOB_CLOSE = 0x2000
_EXTENDED_LIMIT_INFORMATION = 9
_Popen = subprocess.Popen[str] | subprocess.Popen[bytes]


def assign_job(process: _Popen) -> object | None:
    """Put `process` in a kill-on-close job so its whole tree dies in one call."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)

        class _Basic(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.POINTER(ctypes.c_ulong)),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class _Io(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class _Extended(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", _Basic),
                ("IoInfo", _Io),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        job: object = k32.CreateJobObjectW(None, None)
        if not job:
            return None
        info = _Extended()
        info.BasicLimitInformation.LimitFlags = _KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(
            job, _EXTENDED_LIMIT_INFORMATION, ctypes.byref(info), ctypes.sizeof(info)
        ):
            k32.CloseHandle(job)
            return None
        if not k32.AssignProcessToJobObject(job, int(getattr(process, "_handle"))):
            k32.CloseHandle(job)
            return None
        return job
    except Exception:
        return None


def terminate_job(job: object | None) -> bool:
    """Kill every process in `job` at once. True only if the call actually succeeded."""
    if job is None or os.name != "nt":
        return False
    try:
        import ctypes

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        ok = bool(k32.TerminateJobObject(job, 1))
        k32.CloseHandle(job)
        return ok
    except Exception:
        return False


def kill_tree(process: _Popen, job: object | None = None) -> None:
    """Kill the process and all descendants by the identity we started."""
    if process.poll() is not None:
        terminate_job(job)
        return
    if terminate_job(job):
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=KILL_TIMEOUT_S,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            getattr(os, "killpg")(process.pid, getattr(signal, "SIGKILL", 9))
        except (OSError, PermissionError, ProcessLookupError):
            pass
    if process.poll() is None:
        try:
            process.kill()
        except (OSError, PermissionError, ProcessLookupError):
            pass

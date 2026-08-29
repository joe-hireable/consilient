"""What this machine can actually be asked, and the synthetic load put through it.

Split out of ``bench_overhead.py`` on 28 August 2026. Two kinds of thing live here and
they share one property: each is where the measurement meets the operating system, and
each has already been wrong in a way that read as a result.

``process_rss_kb`` returned 0.0 kB on Windows for three runs at every N, because
``GetCurrentProcess`` hands back a pseudo-handle that ctypes' default ``c_int`` restype
truncates; the call then fails and the untouched struct yields a plausible-looking zero.
``cpu_clock_granularity_ms`` exists because ``time.get_clock_info("process_time")``
advertises 1e-07 s on Windows while ``GetProcessTimes`` in fact advances on the ~15.6 ms
scheduler tick, so a cell whose whole routed CPU total lands under one step reports 0.0
with zero variance — which reads as a measurement and is not one.

``default_admit`` reuses ``consilient.routing`` rather than inventing a ceiling, so an
unmeasured β refuses here exactly as it refuses in the product. The synthetic arms do no
I/O and reach no provider: no credential, no spend, nothing off-machine."""

import hashlib
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from overhead_stats import (
    ROOT,
    added_ttft_p99,
    rss_fixed_cost_dominates,
)

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from overhead_stats import (
    ROOT,
)

__all__ = [
    "DEFAULT_TOKENS",
    "Hooks",
    "PREFIX",
    "ROOT",
    "StreamSample",
    "added_ttft_p99",
    "cpu_clock_granularity_ms",
    "default_admit",
    "default_hooks",
    "process_rss_kb",
    "rss_fixed_cost_dominates",
]

DEFAULT_TOKENS = 32

PREFIX = b"consilient-overhead-prefix" * 128


@dataclass(frozen=True)
class StreamSample:
    ttft_ms: float
    tokens: int
    cpu_ms: float
    rss_kb: float


@dataclass
class Hooks:
    direct: Callable[[int], StreamSample]
    routed: Callable[[int], StreamSample]
    stall_ms: Callable[[], float] | None = None
    clear_caches: Callable[[], None] | None = None
    rss_kb: Callable[[], float] | None = None
    cpu_ms: Callable[[], float] | None = None
    admit: Callable[[], str] | None = None


def cpu_clock_granularity_ms(samples: int = 5) -> float:
    """Smallest step ``time.process_time`` can actually resolve, measured.

    ``time.get_clock_info("process_time").resolution`` reports 1e-07 on Windows
    while ``GetProcessTimes`` in fact advances on the ~15.6 ms scheduler tick, so
    the advertised figure is not usable. A cell whose whole routed CPU total lands
    under one step reports 0.0 with zero variance, which reads as a measurement and
    is not one.
    """
    steps: list[float] = []
    for _ in range(samples):
        start = time.process_time()
        while True:
            now = time.process_time()
            if now > start:
                steps.append((now - start) * 1000.0)
                break
    return min(steps)


def default_admit() -> str:
    """Reuse routing.py: unmeasured β is a refusal, never a fabricated ceiling."""
    from consilient.beta import INSUFFICIENT, Beta
    from consilient.routing import RoutingRefusal, candidates_ceiling

    estimate = Beta(
        verdict=INSUFFICIENT,
        task_family=None,
        verifier_version=None,
        n_rejected=0,
        n_false_accept=0,
        point=None,
        interval=None,
        window=None,
    )
    result = candidates_ceiling(estimate, 0.40)
    return "refused" if isinstance(result, RoutingRefusal) else "admitted"


def process_rss_kb() -> float:
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        # HANDLE restypes are not optional: the default c_int truncates the
        # GetCurrentProcess pseudo-handle, the call fails, and the struct is
        # returned untouched — i.e. a silent 0 kB.
        get_current = ctypes.windll.kernel32.GetCurrentProcess
        get_current.argtypes = []
        get_current.restype = wintypes.HANDLE
        get_info = ctypes.windll.psapi.GetProcessMemoryInfo
        get_info.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
            wintypes.DWORD,
        ]
        get_info.restype = wintypes.BOOL

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        if not get_info(get_current(), ctypes.byref(counters), counters.cb):
            raise OSError(f"GetProcessMemoryInfo failed: {ctypes.GetLastError()}")
        return float(counters.WorkingSetSize) / 1024.0
    meminfo = Path("/proc/self/status")
    if meminfo.is_file():
        for line in meminfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("VmRSS:"):
                return float(line.split()[1])
    import resource

    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return float(usage) / 1024.0
    return float(usage)


def _work(n_tokens: int) -> None:
    acc = 0
    for i in range(n_tokens):
        acc ^= (i * 2654435761) & 0xFFFFFFFF
    if acc == -1:
        raise RuntimeError("unreachable")


_POOL: list[object] = [object()]


def _timed_stream(*, routed: bool, index: int) -> StreamSample:
    started = time.perf_counter()
    cpu0 = time.process_time()
    if routed:
        hashlib.sha256(PREFIX + bytes((index % 256,))).digest()
        _ = _POOL[0]
    _work(DEFAULT_TOKENS)
    cpu_ms = (time.process_time() - cpu0) * 1000.0
    ttft_ms = (time.perf_counter() - started) * 1000.0
    return StreamSample(
        ttft_ms=ttft_ms,
        tokens=DEFAULT_TOKENS,
        cpu_ms=cpu_ms,
        rss_kb=process_rss_kb(),
    )


def default_hooks() -> Hooks:
    return Hooks(
        direct=lambda i: _timed_stream(routed=False, index=i),
        routed=lambda i: _timed_stream(routed=True, index=i),
        stall_ms=None,
        clear_caches=_clear_caches,
        rss_kb=process_rss_kb,
        cpu_ms=lambda: time.process_time() * 1000.0,
        admit=default_admit,
    )


def _clear_caches() -> None:
    sys.intern("consilient-overhead-cache-bust")
    hashlib.sha256(PREFIX).digest()

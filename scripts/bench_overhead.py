"""Orchestrator overhead meter: paired direct versus routed at N in {1, 10, 100}.

Client-owned numbers only — cpu_ms_per_1k_tokens, rss_kb_per_stream, added_ttft_p99,
ui_thread_max_stall_ms. Three consecutive runs; variance is a first-class field, not a
mean that swallowed it. Load is open-loop. No provider, no credential, no spend.

    python scripts/bench_overhead.py
    python scripts/bench_overhead.py --out overhead.json

The bar, recorded so it can be re-checked (working principle 9)
---------------------------------------------------------------
`docs/20-design/measurement-and-efficiency-2026-08-23.md` line 80 claims "no published
harness measures the client". **That claim is too strong and this module does not rest
on it.** LlamaStash's benchmark Suite C measures exactly a paired direct-versus-proxy
first-token delta on loopback, alternating one for one, and reports "zero measurable
proxy cost" — a genuine client-side overhead meter, published, with a method very close
to this one. [cited: github.com/llamastash/llamastash docs/benchmarks.md; deepu.tech
"How fast is LlamaStash?"; retrieved 23 August 2026] Commercial routers publish the same
figure: OpenRouter is reported 70 ms *ahead* of OpenAI direct on TTFT, ClawRouters 18 ms
behind. [cited: opper.ai LLM Router Latency Benchmark 2026; clawrouters.com; retrieved
23 August 2026]

Where this instrument is ahead of that bar, and the measurement that shows it: Suite C
reports one metric (TTFT delta) at one concurrency, summarised as "inside run-to-run
noise". This reports four, sweeps N in {1, 10, 100}, takes the **p99 of paired
differences** rather than a mean or a difference of percentiles, and emits every run
with its standard deviation so a "within noise" verdict is checkable rather than
asserted. Re-measure by running both and comparing what each can say at N=100.

Where it is behind: Suite C measures a real proxy carrying real requests. This is a
synthetic in-process workload with no provider on the other end, so it bounds the
harness's own cost and says nothing about a live routed path. That gap closes at BU5,
not here. [asserted]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import statistics
import sys
import threading
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DIRECT = "direct"
ROUTED = "routed"
CONCURRENCIES: tuple[int, ...] = (1, 10, 100)
N_RUNS = 3
REQUIRED_METRICS: tuple[str, ...] = (
    "cpu_ms_per_1k_tokens",
    "rss_kb_per_stream",
    "added_ttft_p99",
    "ui_thread_max_stall_ms",
)
MIN_SAMPLES_FOR_P99 = 100
DEFAULT_TOKENS = 32
PREFIX = b"consilient-overhead-prefix" * 128

T = TypeVar("T")


class HiddenVariance(ValueError):
    """A mean without its runs. The unit exists to stop this."""


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


@dataclass(frozen=True)
class CellResult:
    n: int
    run: int
    cpu_ms_per_1k_tokens: float
    rss_kb_per_stream: float
    added_ttft_p99: float
    ui_thread_max_stall_ms: float
    caches_cleared: bool
    cpu_below_clock_resolution: bool


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


def nearest_rank_percentile(values: Sequence[float], p: float) -> float:
    """Nearest-rank percentile, p in [0, 100]. Same rule as events.py."""
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0.0 <= p <= 100.0:
        raise ValueError(f"percentile p must lie in [0, 100]; got {p!r}")
    ordered = sorted(float(v) for v in values)
    index = max(0, min(len(ordered) - 1, math.ceil(p / 100.0 * len(ordered)) - 1))
    return ordered[index]


def added_ttft_p99(direct: Sequence[float], routed: Sequence[float]) -> float:
    if len(direct) != len(routed):
        raise ValueError("paired A/B requires equal-length direct and routed samples")
    diffs = [r - d for r, d in zip(routed, direct, strict=True)]
    return nearest_rank_percentile(diffs, 99)


def metric_summary(runs: Sequence[float]) -> dict[str, Any]:
    if len(runs) < 2:
        raise HiddenVariance(
            "variance requires at least two runs; a single number hides it"
        )
    values = [float(x) for x in runs]
    return {
        "runs": values,
        "mean": float(statistics.mean(values)),
        "stdev": float(statistics.stdev(values)),
        "min": float(min(values)),
        "max": float(max(values)),
    }


def arm_order(index: int, run: int) -> tuple[str, str]:
    if (index + run) % 2 == 0:
        return (DIRECT, ROUTED)
    return (ROUTED, DIRECT)


async def open_loop(
    n: int, interval_s: float, handle: Callable[[int], Awaitable[T]]
) -> list[T]:
    """Schedule n arrivals without waiting for completion. Closed-loop is the defect."""

    async def scheduled(i: int) -> T:
        delay = i * interval_s
        if delay > 0:
            await asyncio.sleep(delay)
        return await handle(i)

    tasks = [asyncio.create_task(scheduled(i)) for i in range(n)]
    return list(await asyncio.gather(*tasks))


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


def _watchdog(
    stop: threading.Event, holder: list[float], interval_s: float = 0.001
) -> None:
    last = time.perf_counter()
    max_stall = 0.0
    while not stop.wait(interval_s):
        now = time.perf_counter()
        stall = now - last - interval_s
        if stall > max_stall:
            max_stall = stall
        last = now
    holder[0] = max_stall * 1000.0


def measure_cell(
    n: int,
    run: int,
    *,
    min_samples: int,
    interval_s: float,
    hooks: Hooks,
    cpu_granularity_ms: float = 0.0,
) -> CellResult:
    if n <= 0:
        raise ValueError(f"concurrency N must be positive; got {n!r}")
    if hooks.clear_caches is not None:
        hooks.clear_caches()
    # Marginal, not total: whole-process RSS divided by N is the interpreter
    # baseline shrinking as 1/N, which is not what "per stream" means and cannot
    # be read against a 96 kB target.
    baseline_rss = float(hooks.rss_kb()) if hooks.rss_kb is not None else 0.0
    waves = max(1, math.ceil(min_samples / n))
    direct_ttft: list[float] = []
    routed_ttft: list[float] = []
    routed_cpu_ms = 0.0
    routed_tokens = 0
    peak_rss = 0.0
    admit = hooks.admit if hooks.admit is not None else default_admit

    stop = threading.Event()
    holder = [0.0]
    started_watchdog = hooks.stall_ms is None
    watcher: threading.Thread | None = None
    if started_watchdog:
        watcher = threading.Thread(
            target=_watchdog, args=(stop, holder), name="overhead-stall", daemon=True
        )
        watcher.start()

    async def slot(index: int) -> dict[str, StreamSample]:
        out: dict[str, StreamSample] = {}
        for arm in arm_order(index, run):
            if arm == DIRECT:
                out[DIRECT] = hooks.direct(index)
            else:
                admit()
                out[ROUTED] = hooks.routed(index)
        return out

    try:
        for wave in range(waves):

            async def wave_body(
                current_wave: int = wave,
            ) -> list[dict[str, StreamSample]]:
                async def handle(slot_i: int) -> dict[str, StreamSample]:
                    return await slot(current_wave * n + slot_i)

                return await open_loop(n, interval_s, handle)

            pairs = asyncio.run(wave_body())
            for pair in pairs:
                direct_ttft.append(pair[DIRECT].ttft_ms)
                routed_ttft.append(pair[ROUTED].ttft_ms)
                routed_cpu_ms += pair[ROUTED].cpu_ms
                routed_tokens += pair[ROUTED].tokens
                peak_rss = max(peak_rss, pair[DIRECT].rss_kb, pair[ROUTED].rss_kb)
    finally:
        if watcher is not None:
            stop.set()
            watcher.join(timeout=1.0)

    if hooks.rss_kb is not None:
        peak_rss = max(peak_rss, float(hooks.rss_kb()))
    if routed_tokens <= 0:
        raise ValueError("cpu_ms_per_1k_tokens needs a positive token count")
    stall = float(hooks.stall_ms()) if hooks.stall_ms is not None else holder[0]
    return CellResult(
        n=n,
        run=run,
        cpu_ms_per_1k_tokens=routed_cpu_ms * 1000.0 / routed_tokens,
        rss_kb_per_stream=max(0.0, peak_rss - baseline_rss) / n,
        added_ttft_p99=added_ttft_p99(direct_ttft, routed_ttft),
        ui_thread_max_stall_ms=stall,
        caches_cleared=True,
        cpu_below_clock_resolution=routed_cpu_ms < cpu_granularity_ms,
    )


def run_meter(
    *,
    concurrencies: Sequence[int] = CONCURRENCIES,
    n_runs: int = N_RUNS,
    min_samples: int = MIN_SAMPLES_FOR_P99,
    interval_s: float = 0.0,
    hooks: Hooks | None = None,
) -> dict[str, Any]:
    if n_runs < 2:
        raise HiddenVariance(
            "three consecutive runs are the default; fewer than two hides variance"
        )
    used = hooks if hooks is not None else default_hooks()
    granularity = cpu_clock_granularity_ms()
    cells: dict[int, list[CellResult]] = {int(n): [] for n in concurrencies}
    for run in range(n_runs):
        for n in cells:
            cells[n].append(
                measure_cell(
                    n,
                    run,
                    min_samples=min_samples,
                    interval_s=interval_s,
                    hooks=used,
                    cpu_granularity_ms=granularity,
                )
            )
    return _summarise(cells, n_runs, granularity)


def _summarise(
    cells: dict[int, list[CellResult]], n_runs: int, cpu_granularity_ms: float
) -> dict[str, Any]:
    by_concurrency: dict[str, dict[str, Any]] = {}
    caches_cleared = True
    for n, runs in cells.items():
        if len(runs) != n_runs:
            raise HiddenVariance(f"expected {n_runs} runs at N={n}, got {len(runs)}")
        caches_cleared = caches_cleared and all(cell.caches_cleared for cell in runs)
        cell_summary: dict[str, Any] = {
            name: metric_summary([float(getattr(cell, name)) for cell in runs])
            for name in REQUIRED_METRICS
        }
        cell_summary["cpu_below_clock_resolution"] = any(
            cell.cpu_below_clock_resolution for cell in runs
        )
        by_concurrency[str(n)] = cell_summary
    return {
        "instrument": "orchestrator-overhead-meter",
        "n_runs": n_runs,
        "concurrencies": [int(n) for n in cells],
        "load": "open_loop",
        "pairing": "counterbalanced",
        "caches_cleared": caches_cleared,
        "cpu_clock_granularity_ms": cpu_granularity_ms,
        # Derived from the payload, not asserted over it. A hard-coded False is a
        # claim with no check behind it, which is the shape of defect this repo
        # keeps paying for.
        "variance_hidden": any(
            len(cell[name]["runs"]) < 2
            for cell in by_concurrency.values()
            for name in REQUIRED_METRICS
        ),
        "by_concurrency": by_concurrency,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--min-samples", type=int, default=MIN_SAMPLES_FOR_P99)
    parser.add_argument("--runs", type=int, default=N_RUNS)
    args = parser.parse_args(argv)
    report = run_meter(min_samples=args.min_samples, n_runs=args.runs)
    text = json.dumps(report, indent=2)
    print(text)
    if args.out is not None:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

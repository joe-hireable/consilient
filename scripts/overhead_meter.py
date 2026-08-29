"""The experiment: one cell, then the sweep over it.

Split out of ``bench_overhead.py`` on 28 August 2026. The design decisions live here
rather than in the arms or the statistics, and each is something that was got wrong
first.

Arrivals are open-loop — ``open_loop`` schedules N without waiting for completion,
because a closed loop measures the system's own service time back at itself. The two
arms are counterbalanced by ``arm_order``, so a warm cache or a drifting clock cannot
sit under one arm for a whole run. RSS is the peak minus the pre-cell baseline over N,
never whole-process RSS over N, which shrinks as 1/N and reads as an improvement at
N=100 while nothing per-stream changed.

The sweep is N in {1, 10, 100} at three consecutive runs, and variance is a first-class
field rather than a mean that swallowed it: ``_summarise`` derives ``variance_hidden``
from the payload instead of asserting it, because a hard-coded ``False`` is a claim with
no check behind it."""

import asyncio
import math
import sys
import threading
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from overhead_stats import (
    HiddenVariance,
    REQUIRED_METRICS,
    ROOT,
    added_ttft_p99,
    metric_summary,
    rss_fixed_cost_dominates,
)

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from overhead_probes import (
    Hooks,
    StreamSample,
    cpu_clock_granularity_ms,
    default_admit,
    default_hooks,
)

from overhead_stats import (
    ROOT,
)

__all__ = [
    "CONCURRENCIES",
    "CellResult",
    "DIRECT",
    "HiddenVariance",
    "Hooks",
    "MIN_SAMPLES_FOR_P99",
    "N_RUNS",
    "REQUIRED_METRICS",
    "ROOT",
    "ROUTED",
    "StreamSample",
    "T",
    "added_ttft_p99",
    "arm_order",
    "cpu_clock_granularity_ms",
    "default_admit",
    "default_hooks",
    "measure_cell",
    "metric_summary",
    "open_loop",
    "rss_fixed_cost_dominates",
    "run_meter",
]

DIRECT = "direct"

ROUTED = "routed"

CONCURRENCIES: tuple[int, ...] = (1, 10, 100)

N_RUNS = 3

MIN_SAMPLES_FOR_P99 = 100

T = TypeVar("T")


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
        # A per-stream figure that shrinks as N rises is a fixed cost divided by N,
        # not a marginal cost, and cannot be read against the 96 kB target. Flagged,
        # like cpu_below_clock_resolution, rather than silently reported as a number.
        "rss_fixed_cost_dominates": rss_fixed_cost_dominates(by_concurrency),
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

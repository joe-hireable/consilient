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
on it.** LlamaStash — a terminal-native local-LLM runtime manager that fronts
`llama-server` as an OpenAI-compatible proxy — publishes a benchmark Suite C measuring
exactly a paired direct-versus-proxy first-token delta, reported as TTFT p50 +0.45 ms
with decode unchanged. That is a genuine client-side overhead meter, published, with a
method very close to this one.
[cited: FULL; github.com/llamastash/llamastash, README benchmark section; retrieved 24
August 2026]

Commercial routers publish the same shape of figure. Opper's 2026 router latency
benchmark put OpenRouter 70 ms *ahead* of OpenAI direct on time to first token — 0.640 s
against 0.712 s over 200 calls to GPT-4.1, with the scripts and seeds published.
[cited: FULL; opper.ai/blog/llm-router-latency-benchmark-2026; retrieved 24 August 2026]

**Correction, 24 August 2026.** This docstring previously added "ClawRouters 18 ms
behind", attributed jointly to that Opper benchmark and to clawrouters.com. **Neither
source states it.** The Opper benchmark does not mention ClawRouters at all, and
clawrouters.com publishes a 10 ms *per-call routing decision*, which is a routing-analysis
cost and not a time-to-first-token delta against a direct call. The figure is withdrawn.
[measured: both pages fetched, 24 August 2026] The ratchet is
`tests/test_bench_overhead.py::test_every_citation_carries_a_verification_flag_and_a_retrieval_date`:
a citation here declares its `citing-sources` flag and its retrieval date, so a figure
cannot be attributed without the fetch that would have caught this one.

Where this instrument is ahead of that bar, and the measurement that shows it: Suite C
reports one metric (TTFT delta) at one concurrency. This reports four, sweeps N in
{1, 10, 100}, takes the **p99 of paired differences** rather than a mean or a difference
of percentiles, and emits every run with its standard deviation so a "within noise"
verdict is checkable rather than asserted. Re-measure by running both and comparing what
each can say at N=100.

Where it is behind: Suite C measures a real proxy carrying real requests. This is a
synthetic in-process workload with no provider on the other end, so it bounds the
harness's own cost and says nothing about a live routed path. That gap closes at BU5,
not here. [asserted]

Where one of the four numbers is still not readable, flagged rather than left to mislead:
on the default in-process hooks `rss_kb_per_stream` falls roughly as 1/N — 2,147 kB at
N=1, 154 kB at N=10, 16.5 kB at N=100, three runs, one machine — because the marginal
numerator is dominated by per-cell fixed cost (one asyncio loop, the task set, the sample
lists) rather than by anything a stream owns. Read against the 96 kB per-stream target it
would pass at N=100 and fail 22× at N=1 while measuring the same thing.
`rss_fixed_cost_dominates` is true in the report whenever the per-stream figure at the
largest swept N is less than half the figure at the smallest, which is the tell.
[measured, three runs, 24 August 2026]

This file is the command line and the re-export facade. The measurement now sits in three
siblings: `overhead_probes.py` for what this machine can be asked and the synthetic load put
through it, `overhead_meter.py` for the single cell and the sweep over it, and
`overhead_stats.py` for `ROOT` and what a number from the meter is allowed to claim. Every
name importable from here before the split still is; `__all__` says which.
"""

import argparse
import json
import sys
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

from overhead_meter import (
    CONCURRENCIES,
    CellResult,
    DIRECT,
    MIN_SAMPLES_FOR_P99,
    N_RUNS,
    ROUTED,
    T,
    _summarise,
    _watchdog,
    arm_order,
    measure_cell,
    open_loop,
    run_meter,
)

from overhead_probes import (
    DEFAULT_TOKENS,
    Hooks,
    PREFIX,
    StreamSample,
    _POOL,
    _clear_caches,
    _timed_stream,
    _work,
    cpu_clock_granularity_ms,
    default_admit,
    default_hooks,
    process_rss_kb,
)

from overhead_stats import (
    HiddenVariance,
    REQUIRED_METRICS,
    ROOT,
    metric_summary,
    nearest_rank_percentile,
)

__all__ = [
    "CONCURRENCIES",
    "CellResult",
    "DEFAULT_TOKENS",
    "DIRECT",
    "HiddenVariance",
    "Hooks",
    "MIN_SAMPLES_FOR_P99",
    "N_RUNS",
    "PREFIX",
    "REQUIRED_METRICS",
    "ROOT",
    "ROUTED",
    "StreamSample",
    "T",
    "_POOL",
    "_clear_caches",
    "_summarise",
    "_timed_stream",
    "_watchdog",
    "_work",
    "added_ttft_p99",
    "arm_order",
    "cpu_clock_granularity_ms",
    "default_admit",
    "default_hooks",
    "main",
    "measure_cell",
    "metric_summary",
    "nearest_rank_percentile",
    "open_loop",
    "process_rss_kb",
    "rss_fixed_cost_dominates",
    "run_meter",
]


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

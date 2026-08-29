"""ROOT, and what a number from the overhead meter is allowed to claim.

ROOT sits here rather than in the entry point because the module-level sys.path
bootstrap that uses it is copied into every destination, and a sibling importing it from
the entry point would be a cycle -- the entry point already imports the siblings.
Resolving `parent.parent` from any file in scripts/ gives the same directory, so nothing
moves by moving it.

What a number from the overhead meter is allowed to say.

Split out of ``bench_overhead.py`` on 28 August 2026; that file keeps the instrument's
prose and its recorded bar. These are the honesty rules the meter rests on, and each has
a test in ``tests/test_bench_overhead.py``: a percentile is nearest-rank rather than
interpolated, the added-TTFT figure is the p99 of *paired* differences rather than a
mean or a difference of percentiles, and a summary that cannot show its runs raises
rather than reporting a mean that swallowed the variance.

``rss_fixed_cost_dominates`` exists because of a measurement. On the default in-process
hooks ``rss_kb_per_stream`` fell roughly as 1/N — 2,147 kB at N=1, 154 kB at N=10, 16.5
kB at N=100, three runs, one machine — because the marginal numerator is dominated by
per-cell fixed cost rather than by anything a stream owns. Read against the 96 kB per-
stream target, the same instrument would pass at N=100 and fail 22× at N=1 while
measuring the same thing. [measured, three runs, 24 August 2026]"""

import math
import statistics
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REQUIRED_METRICS: tuple[str, ...] = (
    "cpu_ms_per_1k_tokens",
    "rss_kb_per_stream",
    "added_ttft_p99",
    "ui_thread_max_stall_ms",
)


class HiddenVariance(ValueError):
    """A mean without its runs. The unit exists to stop this."""


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


def rss_fixed_cost_dominates(by_concurrency: dict[str, dict[str, Any]]) -> bool:
    """True when ``rss_kb_per_stream`` at the largest N is under half the smallest N's.

    Per-stream cost should be roughly flat in N. When it halves or worse across the
    sweep, the numerator is per-cell setup and the quotient is arithmetic, not memory.
    """
    means = sorted(
        (int(n), float(cell["rss_kb_per_stream"]["mean"]))
        for n, cell in by_concurrency.items()
    )
    if len(means) < 2:
        return False
    return means[-1][1] * 2.0 < means[0][1]

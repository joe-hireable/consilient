"""X04 — orchestrator overhead meter.

The instrument, not a live ranking: paired direct-versus-routed at N in {1, 10, 100},
three consecutive runs, variance visible, p99 not the mean. A deleted metric, a
mean-only summary, a closed-loop scheduler or a missing concurrency must fail here.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "bench_overhead.py"

REQUIRED_METRICS = (
    "cpu_ms_per_1k_tokens",
    "rss_kb_per_stream",
    "added_ttft_p99",
    "ui_thread_max_stall_ms",
)


def _load():
    spec = importlib.util.spec_from_file_location("bench_overhead", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["bench_overhead"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bench():
    assert SCRIPT.is_file(), "scripts/bench_overhead.py is the X04 deliverable"
    return _load()


def _sample(
    *,
    ttft_ms: float,
    tokens: int = 1000,
    cpu_ms: float = 1.0,
    rss_kb: float = 80.0,
) -> Any:
    bench = sys.modules["bench_overhead"]
    return bench.StreamSample(
        ttft_ms=ttft_ms, tokens=tokens, cpu_ms=cpu_ms, rss_kb=rss_kb
    )


def _hooks(
    bench: Any,
    *,
    direct_ttft: Callable[[int], float] | None = None,
    routed_ttft: Callable[[int], float] | None = None,
    stall_ms: float = 0.5,
    rss_kb: float = 80.0,
    baseline_rss_kb: float = 0.0,
    cpu_ms: float = 2.0,
    tokens: int = 1000,
    order: list[str] | None = None,
) -> Any:
    seen_order = order if order is not None else []

    def direct(i: int) -> Any:
        seen_order.append("direct")
        ttft = 1.0 if direct_ttft is None else direct_ttft(i)
        return _sample(ttft_ms=ttft, tokens=tokens, cpu_ms=cpu_ms, rss_kb=rss_kb)

    def routed(i: int) -> Any:
        seen_order.append("routed")
        ttft = 2.0 if routed_ttft is None else routed_ttft(i)
        return _sample(ttft_ms=ttft, tokens=tokens, cpu_ms=cpu_ms * 1.5, rss_kb=rss_kb)

    return bench.Hooks(
        direct=direct,
        routed=routed,
        stall_ms=lambda: stall_ms,
        clear_caches=lambda: None,
        rss_kb=lambda: baseline_rss_kb,
        cpu_ms=lambda: 0.0,
        admit=lambda: "refused",
    )


def test_script_exists():
    assert SCRIPT.is_file()


def test_concurrencies_are_one_ten_and_a_hundred(bench):
    assert tuple(bench.CONCURRENCIES) == (1, 10, 100)


def test_default_is_three_consecutive_runs(bench):
    assert bench.N_RUNS == 3


def test_required_metrics_are_the_four_client_owned_names(bench):
    assert tuple(bench.REQUIRED_METRICS) == REQUIRED_METRICS


def test_p99_sample_floor_is_at_least_one_hundred(bench):
    """p99 of one sample is a max, not a percentile. MLPerf would not accept it."""
    assert bench.MIN_SAMPLES_FOR_P99 >= 100


def test_nearest_rank_percentile(bench):
    values = [float(i) for i in range(1, 101)]
    assert bench.nearest_rank_percentile(values, 100) == 100.0
    assert bench.nearest_rank_percentile(values, 99) == 99.0
    assert bench.nearest_rank_percentile([7.0], 99) == 7.0
    with pytest.raises(ValueError, match="at least one"):
        bench.nearest_rank_percentile([], 99)


def test_added_ttft_is_p99_of_paired_diffs_not_the_mean(bench):
    # Crossed pairing: mean of diffs is 0, unpaired p99-p99 is 0, paired p99 is 100.
    direct = [0.0] * 50 + [100.0] * 50
    routed = [100.0] * 50 + [0.0] * 50
    added = bench.added_ttft_p99(direct, routed)
    assert added == 100.0
    mean_diff = statistics.mean(r - d for r, d in zip(routed, direct, strict=True))
    assert added != pytest.approx(mean_diff)
    unpaired = bench.nearest_rank_percentile(
        routed, 99
    ) - bench.nearest_rank_percentile(direct, 99)
    assert added != pytest.approx(unpaired)


def test_added_ttft_refuses_unpaired_lengths(bench):
    with pytest.raises(ValueError, match="paired"):
        bench.added_ttft_p99([1.0, 2.0], [1.0])


def test_metric_summary_refuses_a_lone_mean(bench):
    with pytest.raises(bench.HiddenVariance, match="hides"):
        bench.metric_summary([4.2])
    summary = bench.metric_summary([1.0, 3.0, 5.0])
    assert summary["runs"] == [1.0, 3.0, 5.0]
    assert summary["mean"] == pytest.approx(3.0)
    assert summary["stdev"] == pytest.approx(statistics.stdev([1.0, 3.0, 5.0]))
    assert summary["min"] == 1.0
    assert summary["max"] == 5.0


def test_arm_order_is_counterbalanced(bench):
    first = [bench.arm_order(i, run=0)[0] for i in range(10)]
    assert first.count("direct") == 5
    assert first.count("routed") == 5
    flipped = [bench.arm_order(i, run=1)[0] for i in range(10)]
    assert flipped == ["routed" if arm == "direct" else "direct" for arm in first]


def test_open_loop_keeps_n_in_flight(bench):
    inflight = 0
    peak = 0

    async def handle(i: int) -> int:
        nonlocal inflight, peak
        inflight += 1
        peak = max(peak, inflight)
        await asyncio.sleep(0.02)
        inflight -= 1
        return i

    got = asyncio.run(bench.open_loop(10, 0.0, handle))
    assert got == list(range(10))
    assert peak == 10


def test_meter_emits_four_metrics_for_each_n_across_three_runs(bench):
    report = bench.run_meter(
        hooks=_hooks(bench),
        min_samples=1,
        n_runs=3,
        concurrencies=(1, 10, 100),
    )
    assert report["n_runs"] == 3
    assert report["load"] == "open_loop"
    assert report["pairing"] == "counterbalanced"
    assert report["caches_cleared"] is True
    assert report["variance_hidden"] is False
    for n in (1, 10, 100):
        cell = report["by_concurrency"][str(n)]
        for name in REQUIRED_METRICS:
            metric = cell[name]
            assert metric["runs"] == pytest.approx(metric["runs"])
            assert len(metric["runs"]) == 3
            assert "stdev" in metric
            assert "min" in metric
            assert "max" in metric
            assert "mean" in metric


def test_added_ttft_from_injected_arms(bench):
    def direct_ttft(i: int) -> float:
        return 10.0

    def routed_ttft(i: int) -> float:
        return 25.0 if i == 0 else 12.0

    report = bench.run_meter(
        hooks=_hooks(bench, direct_ttft=direct_ttft, routed_ttft=routed_ttft),
        min_samples=1,
        n_runs=3,
        concurrencies=(1,),
    )
    added_runs = report["by_concurrency"]["1"]["added_ttft_p99"]["runs"]
    # N=1, one pair per run: routed 25, direct 10 → added 15.
    assert added_runs == [15.0, 15.0, 15.0]


def test_cpu_ms_per_1k_tokens_is_cpu_over_tokens(bench):
    report = bench.run_meter(
        hooks=_hooks(bench, cpu_ms=4.0, tokens=2000),
        min_samples=1,
        n_runs=3,
        concurrencies=(1,),
    )
    # routed cpu_ms=6.0 (1.5×), tokens=2000 → 6.0 * 1000 / 2000 = 3.0
    runs = report["by_concurrency"]["1"]["cpu_ms_per_1k_tokens"]["runs"]
    assert runs == pytest.approx([3.0, 3.0, 3.0])


def test_rss_is_the_marginal_cost_per_in_flight_stream(bench):
    """Peak minus the pre-cell baseline, over N.

    Reporting whole-process RSS over N makes the figure shrink as 1/N — it reads
    as an improvement at N=100 while nothing per-stream changed, and it cannot be
    compared to the 96 kB per-stream target.
    """
    report = bench.run_meter(
        hooks=_hooks(bench, rss_kb=900.0, baseline_rss_kb=100.0),
        min_samples=1,
        n_runs=3,
        concurrencies=(10,),
    )
    runs = report["by_concurrency"]["10"]["rss_kb_per_stream"]["runs"]
    assert runs == pytest.approx([80.0, 80.0, 80.0])

    flat = bench.run_meter(
        hooks=_hooks(bench, rss_kb=500.0, baseline_rss_kb=500.0),
        min_samples=1,
        n_runs=3,
        concurrencies=(10,),
    )
    assert flat["by_concurrency"]["10"]["rss_kb_per_stream"]["runs"] == [0.0] * 3


def test_ui_stall_is_the_watchdog_reading_not_a_mean_ttft(bench):
    report = bench.run_meter(
        hooks=_hooks(bench, stall_ms=7.5),
        min_samples=1,
        n_runs=3,
        concurrencies=(1,),
    )
    runs = report["by_concurrency"]["1"]["ui_thread_max_stall_ms"]["runs"]
    assert runs == pytest.approx([7.5, 7.5, 7.5])


def test_caches_are_cleared_between_cells_and_recorded(bench):
    cleared: list[int] = []

    hooks = _hooks(bench)
    hooks = bench.Hooks(
        direct=hooks.direct,
        routed=hooks.routed,
        stall_ms=hooks.stall_ms,
        clear_caches=lambda: cleared.append(1),
        rss_kb=hooks.rss_kb,
        cpu_ms=hooks.cpu_ms,
        admit=hooks.admit,
    )
    report = bench.run_meter(
        hooks=hooks, min_samples=1, n_runs=3, concurrencies=(1, 10, 100)
    )
    assert report["caches_cleared"] is True
    assert len(cleared) == 9  # 3 runs × 3 concurrencies


def test_routed_path_runs_admission(bench):
    admitted: list[str] = []

    hooks = _hooks(bench)

    def admit() -> str:
        admitted.append("hit")
        return "refused"

    hooks = bench.Hooks(
        direct=hooks.direct,
        routed=hooks.routed,
        stall_ms=hooks.stall_ms,
        clear_caches=hooks.clear_caches,
        rss_kb=hooks.rss_kb,
        cpu_ms=hooks.cpu_ms,
        admit=admit,
    )
    bench.run_meter(hooks=hooks, min_samples=1, n_runs=3, concurrencies=(1,))
    assert admitted
    assert all(item == "hit" for item in admitted)


def test_default_admission_reuses_routing_and_refuses_unmeasured_beta(bench):
    verdict = bench.default_admit()
    assert verdict == "refused"


LOOPBACK = frozenset({"127.0.0.1", "::1", "localhost"})


def test_default_in_process_meter_makes_no_off_machine_connection(bench, monkeypatch):
    """No provider, no credential, no spend.

    Loopback is allowed and must be: asyncio's Windows event loop builds its own
    wake-up self-pipe from a 127.0.0.1 socketpair, so a blanket ``connect`` ban
    fails on the runtime rather than on the meter.
    """
    import socket

    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def _check(address: object) -> None:
        host = address[0] if isinstance(address, tuple) and address else address
        if host not in LOOPBACK:
            raise AssertionError(
                f"overhead meter must not connect off-machine; got {address!r}"
            )

    def guarded_connect(self: Any, address: Any) -> Any:
        _check(address)
        return real_connect(self, address)

    def guarded_connect_ex(self: Any, address: Any) -> Any:
        _check(address)
        return real_connect_ex(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    report = bench.run_meter(min_samples=1, n_runs=3, concurrencies=(1, 10, 100))
    assert report["n_runs"] == 3
    for n in (1, 10, 100):
        for name in REQUIRED_METRICS:
            assert len(report["by_concurrency"][str(n)][name]["runs"]) == 3


def test_cli_writes_json(bench, tmp_path, capsys):
    out = tmp_path / "overhead.json"
    code = bench.main(["--out", str(out), "--min-samples", "1", "--runs", "3"])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert payload["n_runs"] == 3
    assert printed["variance_hidden"] is False
    for n in (1, 10, 100):
        for name in REQUIRED_METRICS:
            assert name in payload["by_concurrency"][str(n)]


def test_process_rss_reads_a_real_working_set_not_a_silent_zero(bench):
    """The first cut returned 0.0 kB on Windows for three runs at every N.

    ``GetCurrentProcess`` returns a pseudo-handle; with ctypes' default ``c_int``
    restype it is truncated, ``GetProcessMemoryInfo`` fails, and the untouched
    struct yields 0 with no error. A zero here is not a small process.
    """
    reading = bench.process_rss_kb()
    assert reading > 1024.0, f"implausible RSS reading: {reading} kB"


def test_cpu_clock_granularity_is_measured_not_advertised(bench):
    """``get_clock_info`` advertises 1e-07 s; the scheduler tick is ~15.6 ms."""
    granularity = bench.cpu_clock_granularity_ms()
    assert granularity > 0.0
    advertised_ms = (
        __import__("time").get_clock_info("process_time").resolution * 1000.0
    )
    assert granularity > advertised_ms


def test_cpu_below_clock_resolution_is_flagged_not_reported_as_zero(bench):
    """A cell whose whole routed CPU total is under one tick must say so."""
    report = bench.run_meter(
        hooks=_hooks(bench, cpu_ms=0.0),
        min_samples=1,
        n_runs=3,
        concurrencies=(1,),
    )
    cell = report["by_concurrency"]["1"]
    assert cell["cpu_ms_per_1k_tokens"]["runs"] == [0.0, 0.0, 0.0]
    assert cell["cpu_below_clock_resolution"] is True
    assert report["cpu_clock_granularity_ms"] > 0.0

    honest = bench.run_meter(
        hooks=_hooks(bench, cpu_ms=1000.0),
        min_samples=1,
        n_runs=3,
        concurrencies=(1,),
    )
    assert honest["by_concurrency"]["1"]["cpu_below_clock_resolution"] is False


# --- The two defects found on 24 August 2026, each with the check that stops it ---
#
# 1. `rss_kb_per_stream` still falls as ~1/N on the default in-process hooks, because
#    the marginal numerator is per-cell fixed cost. A per-stream figure that shrinks
#    when N rises is a fixed cost divided by N, and cannot be read against the 96 kB
#    target. It is now flagged in the payload rather than left to be misread.
# 2. The module docstring carried a figure ("ClawRouters 18 ms behind") that neither
#    named source states. Every citation in this module now declares its verification
#    flag and its retrieval date, so a figure cannot be attributed without a fetch.

CITATION_FLAGS = ("FULL", "ABS", "SNIP", "2ND")


def test_rss_fixed_cost_over_n_is_flagged_not_silently_divided(bench: Any) -> None:
    """Constant cell growth over a swept N is fixed cost, and must say so."""
    report = bench.run_meter(
        hooks=_hooks(bench, rss_kb=1600.0, baseline_rss_kb=0.0),
        min_samples=1,
        n_runs=3,
        concurrencies=(1, 10, 100),
    )
    means = {
        n: cell["rss_kb_per_stream"]["mean"]
        for n, cell in report["by_concurrency"].items()
    }
    assert means["100"] * 2.0 < means["1"], means
    assert report["rss_fixed_cost_dominates"] is True


def test_rss_flag_is_false_when_the_cost_is_genuinely_per_stream(bench: Any) -> None:
    """A cell whose growth scales with N reports a flat per-stream figure, no flag."""
    per_stream = {str(n): {"rss_kb_per_stream": {"mean": 80.0}} for n in (1, 10, 100)}
    assert bench.rss_fixed_cost_dominates(per_stream) is False

    fixed = {str(n): {"rss_kb_per_stream": {"mean": 1600.0 / n}} for n in (1, 10, 100)}
    assert bench.rss_fixed_cost_dominates(fixed) is True

    # One concurrency cannot show a slope, so it cannot claim one either.
    assert (
        bench.rss_fixed_cost_dominates({"1": {"rss_kb_per_stream": {"mean": 9.0}}})
        is False
    )


def test_default_meter_reports_the_rss_flag(bench: Any) -> None:
    """The flag is derived from the payload on every run, not only under injection."""
    report = bench.run_meter(min_samples=1, n_runs=2, concurrencies=(1, 10))
    assert isinstance(report["rss_fixed_cost_dominates"], bool)


def test_every_citation_carries_a_verification_flag_and_a_retrieval_date(
    bench: Any,
) -> None:
    """`citing-sources`: a source is fetched and dated, or it is not `[cited]` here.

    The defect this replaces attributed "ClawRouters 18 ms behind" to two sources,
    neither of which states it. A flag forces the fetch that would have caught it.
    """
    doc = bench.__doc__ or ""
    citations = [
        line for line in doc.splitlines() if "[cited:" in line or "[cited," in line
    ]
    assert citations, "the bar is recorded in the docstring or it is not recorded"
    for line in citations:
        tail = doc[doc.index(line) :]
        window = tail[: tail.index("]") + 1] if "]" in tail else tail
        assert any(flag in window for flag in CITATION_FLAGS), (
            f"citation without a verification flag: {window!r}"
        )
        assert "retrieved" in window.lower(), (
            f"citation without a retrieval date: {window!r}"
        )


def test_withdrawn_figure_is_not_reintroduced(bench: Any) -> None:
    """The specific unsupported number, named so its return is a test failure."""
    doc = bench.__doc__ or ""
    assert "18 ms" not in doc or "withdrawn" in doc.lower()

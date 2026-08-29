"""Comparing two runs of one frozen set: a signed paired difference with a cluster-
robust interval.

Two runs of the same hash produce a signed paired difference with a cluster-robust
interval; one run stays insufficient_data. That refusal is the point — a single run has
nothing to be a difference from, and reporting a bare pass rate as though it were drift
is the failure this module exists to avoid.

The interval resamples clusters, not tasks, so tasks drawn from one family or one
repository do not count as independent evidence. A run whose declared
``anchor_set_hash`` differs from the set refuses outright: the set changed, so whatever
moved is not drift. A run that omits a task, or names one outside the set, refuses on
the same reasoning."""

import math
import random
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from anchor_set_tasks import (
    AnchorSetError,
    _text_field,
)


__all__ = [
    "AnchorSetError",
    "_text_field",
    "cluster_bootstrap_mean",
    "drift_report",
]


def _unpack_run(run: object) -> tuple[str | None, list[Mapping[str, Any]]]:
    if isinstance(run, Mapping) and "outcomes" in run:
        outcomes = run["outcomes"]
        digest = run.get("anchor_set_hash")
        if not isinstance(outcomes, list):
            raise AnchorSetError("run outcomes must be a list")
        if digest is not None and not isinstance(digest, str):
            raise AnchorSetError("anchor_set_hash must be a string")
        return digest, outcomes
    if isinstance(run, list):
        return None, run
    raise AnchorSetError("a run must be a list of outcomes or an object with outcomes")


def _index_outcomes(
    outcomes: Sequence[Mapping[str, Any]],
    *,
    expected: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str], bool]:
    indexed: dict[tuple[str, str], bool] = {}
    for raw in outcomes:
        if not isinstance(raw, Mapping):
            raise AnchorSetError("each outcome must be an object")
        family = _text_field(raw, "family")
        task_id = _text_field(raw, "id")
        passed = raw.get("passed")
        if not isinstance(passed, bool):
            raise AnchorSetError("outcome passed must be a boolean")
        key = (family, task_id)
        if key in indexed:
            raise AnchorSetError(f"duplicate outcome for {family}/{task_id}")
        indexed[key] = passed
    expected_keys = {(str(t["family"]), str(t["id"])) for t in expected}
    missing = expected_keys - set(indexed)
    extra = set(indexed) - expected_keys
    if missing or extra:
        raise AnchorSetError(
            "run is incomplete or names a task outside the set "
            f"(missing={len(missing)} extra={len(extra)})"
        )
    return indexed


def _nearest_rank(values: Sequence[float], p: float) -> float:
    if not values:
        raise AnchorSetError("percentile requires at least one value")
    if not 0.0 <= p <= 100.0:
        raise AnchorSetError(f"percentile p must lie in [0, 100]; got {p!r}")
    ordered = sorted(float(v) for v in values)
    index = max(0, min(len(ordered) - 1, math.ceil(p / 100.0 * len(ordered)) - 1))
    return ordered[index]


def cluster_bootstrap_mean(
    values: Sequence[float],
    clusters: Sequence[str],
    *,
    n_boot: int,
    seed: int,
    lo_bound: float,
    hi_bound: float,
) -> tuple[float, tuple[float, float]]:
    if len(values) != len(clusters):
        raise AnchorSetError("values and clusters must be paired")
    if len(values) == 0:
        raise AnchorSetError("bootstrap requires at least one value")
    if n_boot < 1:
        raise AnchorSetError("n_boot must be at least 1")
    groups: dict[str, list[int]] = defaultdict(list)
    for i, cluster in enumerate(clusters):
        groups[cluster].append(i)
    cluster_ids = sorted(groups)
    if len(cluster_ids) < 2:
        raise AnchorSetError(
            "a cluster-robust interval needs at least 2 clusters; "
            "leave cluster unset to treat each task as its own cluster"
        )
    rng = random.Random(seed)
    n_c = len(cluster_ids)
    means: list[float] = []
    for _ in range(n_boot):
        drawn = [cluster_ids[rng.randrange(n_c)] for _ in range(n_c)]
        sample: list[float] = []
        for cluster in drawn:
            sample.extend(values[i] for i in groups[cluster])
        means.append(sum(sample) / len(sample))
    point = sum(values) / len(values)
    low = max(lo_bound, _nearest_rank(means, 2.5))
    high = min(hi_bound, _nearest_rank(means, 97.5))
    if high < low:
        low, high = high, low
    return point, (low, high)


def _insufficient(
    *,
    n: int,
    n_clusters: int,
    anchor_set_hash: str,
    measured_at: str | None,
) -> dict[str, Any]:
    return {
        "verdict": "insufficient_data",
        "point": None,
        "interval": None,
        "n": n,
        "n_clusters": n_clusters,
        "anchor_set_hash": anchor_set_hash,
        "measured_at": measured_at,
        "drift": None,
        "drift_interval": None,
    }


def drift_report(
    anchor: Mapping[str, Any],
    runs: Sequence[object],
    *,
    measured_at: str | None = None,
    n_boot: int = 2000,
) -> dict[str, Any]:
    tasks = list(anchor["tasks"])
    digest = str(anchor["hash"])
    n_clusters = len({str(task["cluster"]) for task in tasks})
    n = len(tasks)
    if len(runs) < 2:
        return _insufficient(
            n=n,
            n_clusters=n_clusters,
            anchor_set_hash=digest,
            measured_at=measured_at,
        )
    earlier_hash, earlier_rows = _unpack_run(runs[0])
    later_hash, later_rows = _unpack_run(runs[1] if len(runs) == 2 else runs[-1])
    for named in (earlier_hash, later_hash):
        if named is not None and named != digest:
            raise AnchorSetError(
                "run hash does not match the frozen anchor set; "
                "the set changed, so this is not drift"
            )
    earlier = _index_outcomes(earlier_rows, expected=tasks)
    later = _index_outcomes(later_rows, expected=tasks)
    later_bits: list[float] = []
    diffs: list[float] = []
    clusters: list[str] = []
    for task in tasks:
        key = (str(task["family"]), str(task["id"]))
        later_val = 1.0 if later[key] else 0.0
        earlier_val = 1.0 if earlier[key] else 0.0
        later_bits.append(later_val)
        diffs.append(later_val - earlier_val)
        clusters.append(str(task["cluster"]))
    boot_seed = int(digest[:8], 16)
    point, interval = cluster_bootstrap_mean(
        later_bits,
        clusters,
        n_boot=n_boot,
        seed=boot_seed,
        lo_bound=0.0,
        hi_bound=1.0,
    )
    drift, drift_interval = cluster_bootstrap_mean(
        diffs,
        clusters,
        n_boot=n_boot,
        seed=boot_seed + 1,
        lo_bound=-1.0,
        hi_bound=1.0,
    )
    return {
        "verdict": "measured",
        "point": point,
        "interval": [interval[0], interval[1]],
        "n": n,
        "n_clusters": n_clusters,
        "anchor_set_hash": digest,
        "measured_at": measured_at,
        "drift": drift,
        "drift_interval": [drift_interval[0], drift_interval[1]],
    }

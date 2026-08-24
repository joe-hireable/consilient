"""Hashed anchor set: 100 tasks per family, never committed readable.

A frozen hold-out for drift detection. The JSON is the set; its SHA-256 is the
public identifier. Bodies never enter a path git would commit. Two runs of the
same hash produce a signed paired difference with a cluster-robust interval;
one run stays insufficient_data.

    python scripts/build_anchor_set.py --bank bank.json --out set.json
    python scripts/build_anchor_set.py --set set.json --earlier run1.json --later run2.json

The bar, recorded so it can be re-checked (working principle 9)
---------------------------------------------------------------
Incumbent: a frozen unpublished item set, re-run every period, with a hash as
integrity — the shape the measurement design already chose, after LiveCodeBench
(date-held-out) and SWE-bench-Live (monthly held-out). The design cites
arXiv:2604.12843 for that shape; that identifier could not be retrieved from
this runtime (search, 24 August 2026) so it is not re-cited here.
[asserted: design already decided; retrieval of 2604.12843 unavailable]

Where this is ahead of seeded ``random.sample`` (the obvious stdlib answer):
membership is hash-ranked by ``sha256(seed, family, id)``, so growing the bank
does not reshuffle the sitting 100, and the written set stores ``content_sha256``
rather than the body, so a leaked file is composition plus a digest, not the
prompts. A tracked dest is refused. Re-measure: add a high-hash id to a 100-item
family and check membership is unchanged; ``git check-ignore`` on the dest.

Where it is not: this does not download or run a live eval. ADR-0013 keeps
public benchmarks out of β, and the claim list is the builder plus its tests.
The operator supplies the bank. [asserted]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import subprocess
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TASKS_PER_FAMILY = 100
SEED = "consilient-anchor-set-v1"
DEFAULT_DEST = ROOT / ".harness" / "objects" / "anchor-set" / "set.json"
SCHEMA_VERSION = 1
EMPTY_CONTENT_SHA256 = hashlib.sha256(b"").hexdigest()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class AnchorSetError(ValueError):
    """The set cannot be built, written or compared."""


def canonical_dumps(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def selection_key(family: str, task_id: str, seed: str = SEED) -> str:
    return sha256_hex(f"{seed}\n{family}\n{task_id}")


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _git_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def assert_uncommitted_readable(dest: Path, *, root: Path = ROOT) -> Path:
    """Refuse a dest git would commit as readable JSON."""
    dest = dest.resolve()
    root = root.resolve()
    if not _is_inside(dest, root):
        return dest
    rel = dest.relative_to(root).as_posix()
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", rel],
        cwd=root,
        env=_git_env(),
        check=False,
    )
    if ignored.returncode != 0:
        raise AnchorSetError(
            f"refusing dest {rel}: git would commit a readable anchor set; "
            "write outside the repository or under a gitignored path"
        )
    tracked = subprocess.run(
        ["git", "ls-files", "--", rel],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_git_env(),
        check=True,
    )
    if tracked.stdout.split():
        raise AnchorSetError(
            f"refusing dest {rel}: the path is already tracked, so git would "
            "publish a readable anchor set"
        )
    return dest


def _text_field(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AnchorSetError(f"task {key} must be a non-empty string")
    return value.strip()


def _optional_text(row: Mapping[str, Any], key: str) -> str | None:
    if key not in row or row[key] is None:
        return None
    value = row[key]
    if not isinstance(value, str):
        raise AnchorSetError(f"task {key} must be a string")
    return value


def _hex64(value: str, *, label: str) -> str:
    text = value.strip().lower()
    if len(text) != 64:
        raise AnchorSetError(f"{label} must be 64 lowercase hex characters")
    int(text, 16)
    return text


def _content_sha256(row: Mapping[str, Any]) -> str:
    content = _optional_text(row, "content")
    declared = _optional_text(row, "content_sha256")
    digest = (
        hashlib.sha256(content.encode("utf-8")).hexdigest()
        if content is not None
        else None
    )
    if digest is not None and declared is not None:
        declared = _hex64(declared, label="content_sha256")
        if digest != declared:
            raise AnchorSetError(
                "content_sha256 does not match the supplied content"
            )
        return digest
    if digest is not None:
        return digest
    if declared is not None:
        return _hex64(declared, label="content_sha256")
    return EMPTY_CONTENT_SHA256


def _canonical_task(row: Mapping[str, Any]) -> dict[str, str]:
    family = _text_field(row, "family")
    task_id = _text_field(row, "id")
    cluster = _optional_text(row, "cluster")
    return {
        "cluster": cluster.strip() if cluster else task_id,
        "content_sha256": _content_sha256(row),
        "family": family,
        "id": task_id,
    }


def _load_tasks(bank: object) -> list[Mapping[str, Any]]:
    if isinstance(bank, Mapping) and "tasks" in bank:
        bank = bank["tasks"]
    if not isinstance(bank, list):
        raise AnchorSetError("bank must be a list of tasks or an object with tasks")
    return bank


def select_anchor_set(
    bank: object,
    *,
    tasks_per_family: int = TASKS_PER_FAMILY,
    seed: str = SEED,
) -> dict[str, Any]:
    if tasks_per_family < 1:
        raise AnchorSetError("tasks_per_family must be at least 1")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for raw in _load_tasks(bank):
        if not isinstance(raw, Mapping):
            raise AnchorSetError("each task must be an object")
        task = _canonical_task(raw)
        key = (task["family"], task["id"])
        if key in seen:
            raise AnchorSetError(
                f"duplicate id {task['id']!r} in family {task['family']!r}"
            )
        seen.add(key)
        grouped[task["family"]].append(task)
    if not grouped:
        raise AnchorSetError("bank is empty")
    selected: list[dict[str, str]] = []
    for family in sorted(grouped):
        rows = grouped[family]
        if len(rows) < tasks_per_family:
            raise AnchorSetError(
                f"family {family!r} has {len(rows)} tasks; need {tasks_per_family}"
            )
        ranked = sorted(
            rows,
            key=lambda task: (selection_key(task["family"], task["id"], seed), task["id"]),
        )
        selected.extend(ranked[:tasks_per_family])
    selected.sort(key=lambda task: (task["family"], task["id"]))
    families = sorted({task["family"] for task in selected})
    anchor = {
        "v": SCHEMA_VERSION,
        "seed": seed,
        "tasks_per_family": tasks_per_family,
        "families": families,
        "tasks": selected,
    }
    anchor["hash"] = hash_anchor_set(anchor)
    return anchor


def hash_anchor_set(anchor: Mapping[str, Any]) -> str:
    tasks = anchor.get("tasks")
    if not isinstance(tasks, list):
        raise AnchorSetError("anchor set must carry tasks")
    payload = {
        "families": sorted(str(f) for f in list(anchor.get("families") or [])),
        "seed": str(anchor.get("seed") or SEED),
        "tasks": [
            _canonical_task(task) if isinstance(task, Mapping) else task
            for task in sorted(
                tasks,
                key=lambda task: (str(task["family"]), str(task["id"])),
            )
        ],
        "tasks_per_family": int(anchor.get("tasks_per_family") or TASKS_PER_FAMILY),
        "v": int(anchor.get("v") or SCHEMA_VERSION),
    }
    return sha256_hex(canonical_dumps(payload))


def write_anchor_set(anchor: Mapping[str, Any], dest: Path, *, root: Path = ROOT) -> Path:
    dest = assert_uncommitted_readable(dest, root=root)
    payload = {
        "v": int(anchor.get("v") or SCHEMA_VERSION),
        "seed": str(anchor.get("seed") or SEED),
        "tasks_per_family": int(anchor["tasks_per_family"]),
        "families": list(anchor["families"]),
        "hash": str(anchor["hash"]),
        "tasks": list(anchor["tasks"]),
    }
    if hash_anchor_set(payload) != payload["hash"]:
        raise AnchorSetError("anchor hash does not match its tasks")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(canonical_dumps(payload) + "\n", encoding="utf-8")
    return dest


def load_anchor_set(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AnchorSetError("anchor set file must be an object")
    recomputed = hash_anchor_set(payload)
    stored = payload.get("hash")
    if stored != recomputed:
        raise AnchorSetError("anchor hash does not match its tasks")
    return payload


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


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--set", type=Path, dest="set_path")
    parser.add_argument("--earlier", type=Path)
    parser.add_argument("--later", type=Path)
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--measured-at")
    args = parser.parse_args(argv)
    if args.bank is not None:
        dest = args.out if args.out is not None else DEFAULT_DEST
        built = select_anchor_set(_read_json(args.bank))
        write_anchor_set(built, dest)
        print(built["hash"])
        return 0
    if args.set_path is not None and args.earlier is not None and args.later is not None:
        anchor = load_anchor_set(args.set_path)
        report = drift_report(
            anchor,
            [_read_json(args.earlier), _read_json(args.later)],
            measured_at=args.measured_at,
            n_boot=args.n_boot,
        )
        print(canonical_dumps(report))
        return 0
    raise AnchorSetError(
        "need --bank [--out DEST] to build, or --set with --earlier and --later to compare"
    )


if __name__ == "__main__":
    raise SystemExit(main())

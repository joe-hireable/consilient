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

This file keeps the build and the command line. `anchor_set_tasks.py` holds the task row both
halves read and its digest, and `anchor_set_drift.py` the paired comparison of two runs of the
frozen set. Every name importable from here before the split still is; `__all__` says which.
"""

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from anchor_set_tasks import (
    AnchorSetError,
    _canonical_task,
    canonical_dumps,
    sha256_hex,
)

from anchor_set_drift import (
    _index_outcomes,
    _insufficient,
    _nearest_rank,
    _unpack_run,
    cluster_bootstrap_mean,
    drift_report,
)

from anchor_set_tasks import (
    EMPTY_CONTENT_SHA256,
    _content_sha256,
    _hex64,
    _optional_text,
    _text_field,
)

__all__ = [
    "AnchorSetError",
    "DEFAULT_DEST",
    "EMPTY_CONTENT_SHA256",
    "ROOT",
    "SCHEMA_VERSION",
    "SEED",
    "TASKS_PER_FAMILY",
    "_canonical_task",
    "_content_sha256",
    "_hex64",
    "_index_outcomes",
    "_insufficient",
    "_nearest_rank",
    "_optional_text",
    "_text_field",
    "_unpack_run",
    "assert_uncommitted_readable",
    "canonical_dumps",
    "cluster_bootstrap_mean",
    "drift_report",
    "hash_anchor_set",
    "load_anchor_set",
    "main",
    "select_anchor_set",
    "selection_key",
    "sha256_hex",
    "write_anchor_set",
]

ROOT = Path(__file__).resolve().parent.parent

TASKS_PER_FAMILY = 100

SEED = "consilient-anchor-set-v1"

DEFAULT_DEST = ROOT / ".harness" / "objects" / "anchor-set" / "set.json"

SCHEMA_VERSION = 1

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


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
            key=lambda task: (
                selection_key(task["family"], task["id"], seed),
                task["id"],
            ),
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


def write_anchor_set(
    anchor: Mapping[str, Any], dest: Path, *, root: Path = ROOT
) -> Path:
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
    if (
        args.set_path is not None
        and args.earlier is not None
        and args.later is not None
    ):
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

"""EXP-50 arm-B fault generator — instrument and smoke batch, not a verdict.

Arm B: the proposer sees `src/consilient/` and the v0 spec / invariant comments,
never `tests/`. This module refuses test-file contents as generator input.

Does not apply diffs. Does not adjudicate. Does not write `docs/10-research/`.
Adjudication is a different family (ADR-0010). EXP-50 is not declared DONE here.

    python scripts/exp50_faults.py
    python scripts/exp50_faults.py --out .harness/rsi/exp50 --n 10

The generator is split in two. This file keeps the corpus, the tree pin and the command line;
`exp50_arm_b.py` holds what the proposer may be shown and what a candidate must be -- the
isolation rule above is enforced there. Every name importable from here before the split
still is; `__all__` says which.
"""

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from exp50_arm_b import (
    ARM,
    CandidateError,
    InsufficientEvidence,
    ROOT,
    _now_ts,
    apply_once,
    load_arm_b_context,
    reject_test_contents,
    tree_sha256,
    unified_diff,
    validate_candidate,
)

from exp50_arm_b import (
    DIFF_PATH,
    PRODUCT_PREFIX,
    REQUIRED_FIELDS,
    SPEC_KEY,
    TS,
    is_product_path,
    is_test_path,
    parse_diff_paths,
    posix_rel,
)

__all__ = [
    "ARM",
    "CandidateError",
    "DEFAULT_MODEL_ID",
    "DEFAULT_N",
    "DEFAULT_OUT",
    "DEFAULT_SPEC",
    "DEFAULT_SRC",
    "DIFF_PATH",
    "FAMILY",
    "InsufficientEvidence",
    "PRODUCT_PREFIX",
    "Proposer",
    "REQUIRED_FIELDS",
    "ROOT",
    "SMOKE_FAULTS",
    "SPEC_KEY",
    "TS",
    "_now_ts",
    "apply_once",
    "build_parser",
    "generate_candidates",
    "is_product_path",
    "is_test_path",
    "load_arm_b_context",
    "main",
    "parse_diff_paths",
    "posix_rel",
    "reject_test_contents",
    "smoke_proposer",
    "tree_sha256",
    "unified_diff",
    "validate_candidate",
    "write_batch",
]

DEFAULT_SRC = ROOT / "src" / "consilient"

DEFAULT_SPEC = ROOT / "docs" / "40-spec" / "v0-draft.md"

DEFAULT_OUT = ROOT / ".harness" / "rsi" / "exp50"

FAMILY = "xai"

DEFAULT_MODEL_ID = "grok-4.6"

DEFAULT_N = 10

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

Proposer = Callable[[Mapping[str, str]], Sequence[Mapping[str, Any]]]

# Polarity inversions of documented guards. Each names the invariant it claims
# to violate. Generated from source + spec context, not from tests/.
SMOKE_FAULTS: tuple[dict[str, str], ...] = (
    {
        "file": "src/consilient/events.py",
        "old": '    if event["actor"] != principal:',
        "new": '    if event["actor"] == principal:',
        "invariant": (
            "V0-18: a human decision is valid only when the human principal "
            "authored it; an agent actor must not be able to author it"
        ),
    },
    {
        "file": "src/consilient/events.py",
        "old": '    if via.strip().casefold() != "cli":',
        "new": '    if via.strip().casefold() == "cli":',
        "invariant": (
            "V0-28: a declared non-local channel cannot deliver a human "
            "decision; only local CLI is accepted"
        ),
    },
    {
        "file": "src/consilient/events.py",
        "old": '    if status != "ok":',
        "new": '    if status == "ok":',
        "invariant": (
            "V0-30: a provider whose status is not ok may carry no figures; "
            "a provider that could not be read reports unavailable and no number"
        ),
    },
    {
        "file": "src/consilient/events.py",
        "old": "        if normalized in seen_classes:",
        "new": "        if normalized not in seen_classes:",
        "invariant": (
            "V0-26: multi-contributor events must declare a distinct "
            "evidence_class per contributor"
        ),
    },
    {
        "file": "src/consilient/events.py",
        "old": '    if event["v"] != SCHEMA_VERSION:',
        "new": '    if event["v"] == SCHEMA_VERSION:',
        "invariant": (
            "V0-01: every event is schema-versioned; unsupported versions "
            "must not reach the log"
        ),
    },
    {
        "file": "src/consilient/beta.py",
        "old": "    if min_rejections < MIN_REJECTIONS:",
        "new": "    if min_rejections > MIN_REJECTIONS:",
        "invariant": (
            "min_rejections may only raise the evidence floor, never lower it; "
            "a knob that can lower the floor is a bypass around it"
        ),
    },
    {
        "file": "src/consilient/beta.py",
        "old": (
            "        if self.verdict == MEASURED and self.n_rejected < MIN_REJECTIONS:"
        ),
        "new": (
            "        if self.verdict == MEASURED and self.n_rejected >= MIN_REJECTIONS:"
        ),
        "invariant": (
            "a measured beta needs at least MIN_REJECTIONS rejections behind "
            "it; an underpowered number presented as measured is the failure "
            "this project exists to catch"
        ),
    },
    {
        # `_is_exhausted` moved here when src/consilient/harness.py was split on
        # 28 August 2026. The instrument refused rather than guessing -- it reported
        # "expected the invariant site to occur once, found 0" -- which is the right
        # behaviour and the reason this was a one-line repair rather than a silent
        # arm-B batch generated against a site that no longer exists.
        "file": "src/consilient/harness_headroom.py",
        "old": (
            "def _is_exhausted(pool: PoolState) -> bool:\n"
            "    if pool.exhausted:\n"
            "        return True\n"
        ),
        "new": (
            "def _is_exhausted(pool: PoolState) -> bool:\n"
            "    if pool.exhausted:\n"
            "        return False\n"
        ),
        "invariant": (
            "selection never silently spends an exhausted pool; refusing with "
            "a reason is the success path when the scarce resource is the "
            "only thing left"
        ),
    },
    {
        "file": "src/consilient/loop.py",
        "old": "    if not (root / MARKER).is_file():",
        "new": "    if (root / MARKER).is_file():",
        "invariant": (
            "V0-30: a loop runs only inside a Consilient checkout; Gate B "
            "forbids pointing the harness at another repository"
        ),
    },
    {
        "file": "src/consilient/budget.py",
        "old": "        if ceiling.amount > cap.amount:",
        "new": "        if ceiling.amount <= cap.amount:",
        "invariant": (
            "V0-31: a configured ceiling may not exceed the declared account "
            "cap; the check refuses rather than clamps"
        ),
    },
)


def generate_candidates(
    context: Mapping[str, str],
    proposer: Proposer,
    *,
    arm: str = ARM,
    family: str = FAMILY,
    n: int = DEFAULT_N,
    ts: str | None = None,
) -> list[dict[str, Any]]:
    """Ask `proposer` for faults. `context` must not contain test files."""
    if arm != ARM:
        raise CandidateError(
            f"Arm {arm!r} is not generated here; arm B cannot be shown tests/"
        )
    reject_test_contents(context)
    proposed = proposer(context)
    stamp = ts or _now_ts()
    out: list[dict[str, Any]] = []
    for raw in proposed:
        record = dict(raw)
        record.setdefault("arm", arm)
        record.setdefault("family", family)
        record.setdefault("ts", stamp)
        out.append(validate_candidate(record))
        if len(out) >= n:
            break
    if len(out) < n:
        raise InsufficientEvidence(
            f"proposer produced {len(out)} valid named-invariant diffs; need {n}"
        )
    return out[:n]


def smoke_proposer(context: Mapping[str, str]) -> list[dict[str, Any]]:
    """Ten arm-B faults from this generating family. Does not read tests/."""
    reject_test_contents(context)
    records: list[dict[str, Any]] = []
    for fault in SMOKE_FAULTS:
        path = fault["file"]
        if path not in context:
            raise InsufficientEvidence(
                f"smoke proposer was not shown {path}; refusing to invent a no-op"
            )
        mutated = apply_once(context[path], fault["old"], fault["new"], where=path)
        if mutated == context[path]:
            raise InsufficientEvidence(f"{path}: replacement was a no-op")
        diff = unified_diff(path, context[path], mutated)
        if not diff.strip():
            raise InsufficientEvidence(f"{path}: empty diff")
        records.append(
            {
                "invariant": fault["invariant"],
                "diff": diff,
                "files": [path],
            }
        )
    return records


def write_batch(
    candidates: Sequence[Mapping[str, Any]],
    out_dir: Path,
    *,
    src_dir: Path,
    model_id: str,
    tests_shown: bool,
) -> dict[str, Any]:
    """Write candidates.jsonl and manifest.json. Does not touch src/."""
    if tests_shown:
        raise CandidateError("Arm B batch cannot record tests_shown=true")
    out_dir.mkdir(parents=True, exist_ok=True)
    validated = [validate_candidate(item) for item in candidates]
    jsonl = out_dir / "candidates.jsonl"
    with jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for record in validated:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    manifest = {
        "experiment": "EXP-50",
        "arm": ARM,
        "family": FAMILY,
        "n": len(validated),
        "src_consilient_sha256": tree_sha256(src_dir),
        "model_id": model_id,
        "tests_shown": False,
        "adjudication": "pending",
        "status": "smoke",
        "generated_at": _now_ts(),
        "tree_hash_algorithm": (
            "sha256 over posix-relative paths then file bytes, "
            "excluding __pycache__ and .pyc, files sorted by path"
        ),
        "note": (
            "Smoke batch. Not a verdict. Adjudication by a different family "
            "is pending (ADR-0010). Diffs are proposed, not applied."
        ),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--family", default=FAMILY)
    return parser


def main(
    argv: list[str] | None = None,
    proposer: Proposer | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    context = load_arm_b_context(args.src, args.spec)
    try:
        candidates = generate_candidates(
            context,
            proposer or smoke_proposer,
            arm=ARM,
            family=args.family,
            n=args.n,
        )
    except InsufficientEvidence as exc:
        print(f"insufficient_evidence: {exc}", file=sys.stderr)
        return 2
    write_batch(
        candidates,
        args.out,
        src_dir=args.src,
        model_id=args.model_id,
        tests_shown=False,
    )
    print(
        json.dumps(
            {"wrote": args.n, "out": str(args.out), "adjudication": "pending"},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

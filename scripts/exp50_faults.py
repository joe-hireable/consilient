"""EXP-50 arm-B fault generator — instrument and smoke batch, not a verdict.

Arm B: the proposer sees `src/consilient/` and the v0 spec / invariant comments,
never `tests/`. This module refuses test-file contents as generator input.

Does not apply diffs. Does not adjudicate. Does not write `docs/10-research/`.
Adjudication is a different family (ADR-0010). EXP-50 is not declared DONE here.

    python scripts/exp50_faults.py
    python scripts/exp50_faults.py --out .harness/rsi/exp50 --n 10
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = ROOT / "src" / "consilient"
DEFAULT_SPEC = ROOT / "docs" / "40-spec" / "v0-draft.md"
DEFAULT_OUT = ROOT / ".harness" / "rsi" / "exp50"
PRODUCT_PREFIX = "src/consilient/"
SPEC_KEY = "docs/40-spec/v0-draft.md"
FAMILY = "xai"
ARM = "B"
DEFAULT_MODEL_ID = "grok-4.6"
DEFAULT_N = 10
REQUIRED_FIELDS = ("arm", "family", "invariant", "diff", "files", "ts")
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
DIFF_PATH = re.compile(r"^(?:---|\+\+\+)\s+(\S+)")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class CandidateError(ValueError):
    """A proposed candidate is not a legal EXP-50 arm-B record."""


class InsufficientEvidence(RuntimeError):
    """The smoke batch could not produce n diffs that name a real invariant."""


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
            "        if self.verdict == MEASURED and "
            "self.n_rejected < MIN_REJECTIONS:"
        ),
        "new": (
            "        if self.verdict == MEASURED and "
            "self.n_rejected >= MIN_REJECTIONS:"
        ),
        "invariant": (
            "a measured beta needs at least MIN_REJECTIONS rejections behind "
            "it; an underpowered number presented as measured is the failure "
            "this project exists to catch"
        ),
    },
    {
        "file": "src/consilient/harness.py",
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


def posix_rel(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def is_test_path(path: str) -> bool:
    """True if `path` is, or would resolve into, a tests/ tree."""
    parts = [part for part in posix_rel(path).split("/") if part not in ("", ".")]
    collapsed: list[str] = []
    for part in parts:
        if part == "..":
            if collapsed:
                collapsed.pop()
            continue
        collapsed.append(part)
    return "tests" in collapsed


def is_product_path(path: str) -> bool:
    parts = [part for part in posix_rel(path).split("/") if part not in ("", ".")]
    collapsed: list[str] = []
    for part in parts:
        if part == "..":
            if collapsed:
                collapsed.pop()
            continue
        collapsed.append(part)
    normalised = "/".join(collapsed)
    return normalised.startswith(PRODUCT_PREFIX) and normalised != PRODUCT_PREFIX.rstrip(
        "/"
    )


def reject_test_contents(context: Mapping[str, str]) -> None:
    """Arm B: the generator function must not be passed test file contents."""
    bad = sorted(path for path in context if is_test_path(path))
    if bad:
        raise CandidateError(
            "Arm B generator must not be passed test file contents; "
            f"got {bad}"
        )


def tree_sha256(src_dir: Path) -> str:
    """SHA-256 of the `src/consilient/` tree, excluding bytecode.

    Paths are hashed in POSIX order, then file bytes, so the digest is
    independent of the walker's native separators.
    """
    digest = hashlib.sha256()
    files = [
        path
        for path in src_dir.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    ]
    for path in sorted(files, key=lambda item: item.relative_to(src_dir).as_posix()):
        rel = path.relative_to(src_dir).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_arm_b_context(
    src_dir: Path,
    spec_path: Path | None = None,
    extra: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Load product source and the v0 spec. Refuses anything under tests/."""
    src_dir = src_dir.resolve()
    context: dict[str, str] = {}
    for path in sorted(src_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            rel = path.relative_to(ROOT).as_posix()
        except ValueError as exc:
            raise CandidateError(
                f"source file {path} is outside the repository root"
            ) from exc
        if is_test_path(rel):
            raise CandidateError(
                f"Arm B context refused test path {rel}"
            )
        context[rel] = path.read_text(encoding="utf-8")
    if spec_path is not None and spec_path.is_file():
        spec_rel = spec_path.resolve().relative_to(ROOT).as_posix()
        if is_test_path(spec_rel):
            raise CandidateError(f"Arm B context refused test path {spec_rel}")
        context[spec_rel] = spec_path.read_text(encoding="utf-8")
    if extra:
        for key, value in extra.items():
            if is_test_path(key):
                raise CandidateError(f"Arm B context refused test path {key}")
            context[key] = value
    reject_test_contents(context)
    return context


def parse_diff_paths(diff: str) -> list[str]:
    """Paths named by a unified diff's --- / +++ headers, minus /dev/null."""
    found: list[str] = []
    seen: set[str] = set()
    for line in diff.splitlines():
        match = DIFF_PATH.match(line)
        if match is None:
            continue
        raw = match.group(1)
        if raw in {"/dev/null", "nul", "NUL"}:
            continue
        stripped = posix_rel(raw)
        if stripped.startswith("a/") or stripped.startswith("b/"):
            stripped = stripped[2:]
        if "\t" in stripped:
            stripped = stripped.split("\t", 1)[0]
        if stripped not in seen:
            seen.add(stripped)
            found.append(stripped)
    return found


def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def unified_diff(path: str, original: str, mutated: str) -> str:
    if not original.endswith("\n"):
        original += "\n"
    if not mutated.endswith("\n"):
        mutated += "\n"
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            mutated.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def apply_once(source: str, old: str, new: str, *, where: str) -> str:
    count = source.count(old)
    if count != 1:
        raise InsufficientEvidence(
            f"{where}: expected the invariant site to occur once, found {count}"
        )
    return source.replace(old, new, 1)


def validate_candidate(record: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        raise CandidateError(f"missing required field(s): {', '.join(missing)}")
    arm = record["arm"]
    family = record["family"]
    invariant = record["invariant"]
    diff = record["diff"]
    files = record["files"]
    ts = record["ts"]
    if arm != ARM:
        raise CandidateError(f"this instrument emits arm {ARM!r} only, got {arm!r}")
    if not isinstance(family, str) or not family.strip():
        raise CandidateError("family must be a non-empty string")
    if not isinstance(invariant, str) or not invariant.strip():
        raise CandidateError("invariant must name the behaviour the diff claims to violate")
    if not isinstance(diff, str) or not diff.strip():
        raise CandidateError("diff must be a non-empty unified diff")
    if "---" not in diff or "+++" not in diff or "@@" not in diff:
        raise CandidateError("diff must be a single self-contained unified diff")
    if not isinstance(files, list) or not files or not all(isinstance(item, str) for item in files):
        raise CandidateError("files must be a non-empty list of strings")
    if not isinstance(ts, str) or not TS.match(ts):
        raise CandidateError(
            f"ts must be RFC3339 with an explicit offset, got {ts!r}"
        )

    declared = [posix_rel(item) for item in files]
    parsed = parse_diff_paths(diff)
    if not parsed:
        raise CandidateError("diff names no files")
    for path in (*declared, *parsed):
        if is_test_path(path) or not is_product_path(path):
            raise CandidateError(
                f"candidate whose diff touches {path!r} is rejected; "
                f"arm B may change only {PRODUCT_PREFIX} paths"
            )
    if set(declared) != set(parsed):
        raise CandidateError(
            f"files {declared} does not match diff paths {parsed}"
        )
    return {
        "arm": arm,
        "family": family,
        "invariant": invariant.strip(),
        "diff": diff if diff.endswith("\n") else diff + "\n",
        "files": declared,
        "ts": ts,
    }


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

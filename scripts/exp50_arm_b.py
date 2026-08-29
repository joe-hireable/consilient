"""EXP-50 arm B: what the proposer may be shown, and what a candidate must be.

This is the experimental control, split out from the instrument that uses it so that the
control can be read on its own. Arm B sees `src/consilient/` and the v0 spec and never
`tests/` — `is_test_path` collapses `..` segments before deciding, so a path that
escapes into a tests tree by traversal is refused as firmly as a literal `tests/`
prefix, and `reject_test_contents` is called on every context that reaches the
generator. `is_product_path` is the other half: a candidate may name only paths under
`src/consilient/`, so a diff that wanders outside the product tree is rejected before
anything downstream sees it.

The record contract lives here too, because it is the same boundary seen from the other
side. `validate_candidate` is the only thing that decides whether a proposal is a legal
arm-B record: it requires the six fields, an RFC3339 timestamp with an explicit offset,
a single self-contained unified diff, and — the load-bearing check — that the declared
`files` set is exactly the set of paths the diff's own headers name. Declaring one file
and touching another is the shape a batch would take if it were quietly editing
something it should not.

`tree_sha256` hashes the product tree in POSIX path order before file bytes, so the
digest is independent of the walker's native separators. The generator records it before
and the suite compares it after; that is how "this instrument does not touch `src/`" is
checked rather than promised.

Nothing here imports `exp50_faults`. The dependency runs one way — the instrument
imports the boundary — so the facade in `scripts/exp50_faults.py` cannot form a cycle."""

import difflib
import hashlib
import re
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent

PRODUCT_PREFIX = "src/consilient/"

SPEC_KEY = "docs/40-spec/v0-draft.md"

ARM = "B"

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
    return normalised.startswith(
        PRODUCT_PREFIX
    ) and normalised != PRODUCT_PREFIX.rstrip("/")


def reject_test_contents(context: Mapping[str, str]) -> None:
    """Arm B: the generator function must not be passed test file contents."""
    bad = sorted(path for path in context if is_test_path(path))
    if bad:
        raise CandidateError(
            f"Arm B generator must not be passed test file contents; got {bad}"
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
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
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
            raise CandidateError(f"Arm B context refused test path {rel}")
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
        raise CandidateError(
            "invariant must name the behaviour the diff claims to violate"
        )
    if not isinstance(diff, str) or not diff.strip():
        raise CandidateError("diff must be a non-empty unified diff")
    if "---" not in diff or "+++" not in diff or "@@" not in diff:
        raise CandidateError("diff must be a single self-contained unified diff")
    if (
        not isinstance(files, list)
        or not files
        or not all(isinstance(item, str) for item in files)
    ):
        raise CandidateError("files must be a non-empty list of strings")
    if not isinstance(ts, str) or not TS.match(ts):
        raise CandidateError(f"ts must be RFC3339 with an explicit offset, got {ts!r}")

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
        raise CandidateError(f"files {declared} does not match diff paths {parsed}")
    return {
        "arm": arm,
        "family": family,
        "invariant": invariant.strip(),
        "diff": diff if diff.endswith("\n") else diff + "\n",
        "files": declared,
        "ts": ts,
    }

"""Refuse reachable held-out contracts and void measurements that leak them.

ADR-0103's enforcement is the boundary: a build whose brief, worktree or claims can
reach the contract is refused before child launch. A post-build audit voids a
measurement that leaked the path, digest or a fingerprinted line. The residual is
recorded on the checker: a child that reads the contract and neither echoes its path nor reproduces its assertions is not detected. [asserted]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from consilient.coordination import canonical_path, paths_overlap  # noqa: E402


def _private_corpus_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "check_private_corpus", ROOT / ".github" / "scripts" / "check_private_corpus.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("private-corpus fingerprinter is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


content_digest = cast(
    Callable[[str], str | None], _private_corpus_module().content_digest
)


def refusal_reason(
    contract: str,
    *,
    brief: str = "",
    worktree: str = "",
    claims: tuple[str, ...] = (),
) -> str | None:
    """Return a boundary reason without printing private context."""
    if not contract.strip():
        return "held-out contract input is invalid; refusing before child launch"
    contract_path = canonical_path(contract)
    if worktree and paths_overlap(contract_path, canonical_path(worktree)):
        return "held-out contract is reachable from the worktree; refusing before child launch"
    brief_folded = brief.casefold()
    if contract.casefold() in brief_folded or Path(contract).name.casefold() in brief_folded:
        return "held-out contract is named in the brief; refusing before child launch"
    try:
        quoted = Path(contract).read_text(encoding="utf-8")
    except OSError:
        return "held-out contract input is invalid; refusing before child launch"
    if any(line.strip() and line.strip() in brief for line in quoted.splitlines()):
        return "held-out contract is quoted in the brief; refusing before child launch"
    for claim in claims:
        if claim.strip() and paths_overlap(contract_path, canonical_path(claim, cwd=Path(worktree))):
            return "held-out contract is covered by a claim; refusing before child launch"
    return None


def audit_reason(
    contract: str, *, runs_dir: str, uid: str, diff: str
) -> str | None:
    """Return a leak/invalid-input reason, never contract content or its path."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", uid):
        return "held-out audit input is invalid; measurement VOID"
    try:
        contract_path = Path(contract).resolve(strict=True)
        root = Path(runs_dir).resolve(strict=True)
        if not contract_path.is_file() or not root.is_dir():
            return "held-out audit input is invalid; measurement VOID"
        stdout = (root / f"{uid}.out").resolve(strict=True)
        stderr = (root / f"{uid}.err").resolve(strict=True)
        diff_path = Path(diff).resolve(strict=True)
        for path in (stdout, stderr):
            path.relative_to(root)
            if not path.is_file():
                return "held-out audit input is invalid; measurement VOID"
        if not diff_path.is_file():
            return "held-out audit input is invalid; measurement VOID"
        contract_bytes = contract_path.read_bytes()
        transcripts = [
            stdout.read_text(encoding="utf-8", errors="replace"),
            stderr.read_text(encoding="utf-8", errors="replace"),
            diff_path.read_text(encoding="utf-8", errors="replace"),
        ]
    except (OSError, ValueError):
        return "held-out audit input is invalid; measurement VOID"
    paths = (str(contract), str(contract_path))
    fingerprinted = {
        digest
        for line in contract_bytes.decode("utf-8", errors="replace").splitlines()
        if (digest := content_digest(line)) is not None
    }
    digest = hashlib.sha256(contract_bytes).hexdigest()
    for transcript in transcripts:
        if any(path in transcript for path in paths) or digest in transcript:
            return "held-out contract LEAKED; measurement VOID"
        if any(content_digest(line) in fingerprinted for line in transcript.splitlines()):
            return "held-out contract LEAKED; measurement VOID"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--heldout-contract", required=True)
    parser.add_argument("--brief", default="")
    parser.add_argument("--worktree", default="")
    parser.add_argument("--claim", action="append", default=[])
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--runs-dir")
    parser.add_argument("--uid")
    parser.add_argument("--diff")
    args = parser.parse_args(argv)
    if args.audit:
        if not args.runs_dir or not args.uid or not args.diff:
            print("held-out audit input is invalid; measurement VOID")
            return 2
        reason = audit_reason(
            args.heldout_contract, runs_dir=args.runs_dir, uid=args.uid, diff=args.diff
        )
        print(reason or "held-out audit CLEAN")
        return 2 if reason else 0
    reason = refusal_reason(
        args.heldout_contract,
        brief=args.brief,
        worktree=args.worktree,
        claims=tuple(args.claim),
    )
    print(reason or "held-out isolation checked: brief, worktree and claims")
    return 2 if reason else 0


if __name__ == "__main__":
    raise SystemExit(main())

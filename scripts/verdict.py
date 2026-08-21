"""Record one reviewed attempt: what the checks said, and what you said.

Beta is P(verifier_accept | human_reject), so its denominator is human *rejections*
alone — thirty of them before `consil beta` reports a number, and realistically more
before the interval decides anything. Thirty hand-written JSON blobs is thirty chances
to typo, and one typo is permanent: an `attempt.verdict` naming an attempt that has no
recorded outcome passes `validate()`, appends happily, and then refuses to project
forever. The log is append-only, so there is no taking it back.

This writes both events in one call, in the required order, sharing one generated
attempt_id, through `events.append()` — the only writer. No path here can orphan a
verdict.

    python scripts/verdict.py reject "fix pagination off-by-one" --checks pass
    python scripts/verdict.py accept "tighten the retry backoff"  --checks fail

Shorten it once and you will do it thirty times:
    PowerShell   function verdict { python <repo>/scripts/verdict.py @args }
    bash         alias verdict='python <repo>/scripts/verdict.py'

`--checks` is required on purpose. If you only ever review artefacts whose checks
already passed, every rejected row carries verifier_accept=true and beta is 1.000 by
construction rather than by measurement (see `src/consilient/beta.py`). Recording
attempts whose checks FAILED is what makes the number mean anything.

The pair is hand-recorded. It says what you observed; it is not evidence that a
verifier ran.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from consilient.events import OUTCOME_KIND, SCHEMA_VERSION, VERDICT_KIND, append  # noqa: E402


def record(
    log: Path,
    verdict: str,
    task: str,
    checks: str,
    principal: str,
    family: str | None = None,
    verifier: str | None = None,
) -> tuple[str, Path]:
    """Append the outcome and its verdict as one pair. Returns (attempt_id, file)."""
    attempt_id = f"attempt-{uuid.uuid4().hex[:12]}"
    # One timestamp for both: they were written in the same breath, and it keeps the pair
    # in one daily file even when the clock crosses midnight between two append() calls.
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path = log / f"{ts[:10]}.jsonl"

    outcome: dict[str, Any] = {
        "attempt_id": attempt_id,
        "task": task,
        "verifier_accept": checks == "pass",
    }
    if family:
        outcome["task_family"] = family
    if verifier:
        outcome["verifier_version"] = verifier

    base = {"v": SCHEMA_VERSION, "ts": ts, "actor": principal}
    append(path, {**base, "event": OUTCOME_KIND, "data": outcome})
    append(
        path,
        {
            **base,
            "event": VERDICT_KIND,
            # V0-18: only the principal may author their own verdict, and V0-28 accepts
            # no channel but the local CLI, so both are fixed by who ran this script.
            "data": {
                "attempt_id": attempt_id,
                "human_verdict": verdict,
                "principal": principal,
                "via": "cli",
            },
        },
    )
    return attempt_id, path


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        prog="verdict.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("verdict", choices=("accept", "reject"), help="your judgement")
    parser.add_argument("task", help="what the attempt was, in a few words")
    parser.add_argument(
        "--checks",
        required=True,
        choices=("pass", "fail"),
        help="what the automated checks said. Record failures too, or beta is 1.000 by "
        "construction",
    )
    parser.add_argument(
        "--log",
        default=os.environ.get("CONSILIENT_LOG", ".harness/log"),
        help="trajectory directory (default $CONSILIENT_LOG, else .harness/log). One log "
        "across every repository you review is what gets you to thirty rejections",
    )
    parser.add_argument(
        "--principal",
        default=os.environ.get("CONSILIENT_PRINCIPAL", getpass.getuser()),
        help="whose judgement this is (default $CONSILIENT_PRINCIPAL, else your username)",
    )
    parser.add_argument("--family", help="task family, for `consil beta --task-family`")
    parser.add_argument(
        "--verifier", help="verifier version, for `consil beta --verifier-version`"
    )
    args = parser.parse_args(argv)

    attempt_id, path = record(
        Path(args.log),
        args.verdict,
        args.task,
        args.checks,
        args.principal,
        args.family,
        args.verifier,
    )
    print(f"{attempt_id}  checks: {args.checks}  you: {args.verdict}  -> {path}")
    print(f"next: consil beta --log {args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

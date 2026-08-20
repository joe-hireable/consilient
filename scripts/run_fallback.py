"""Exercise the bare-agent fallback and record the result. Gate B condition 3.

The condition asks one question: **if the harness vanished, could you still work?** It is
answered by running one documented command against a fixed task with no harness involved, and
writing down what happened.

This runs wherever a credential legitimately lives — the principal's machine, a private
runner — and never in this repository's CI, because `AGENTS.md` forbids a secret anywhere a
public repository can reach (Joe, 20 Aug 2026). See ADR-0046 for why the gate reads the result
rather than a schedule trigger.

    python scripts/run_fallback.py                 # run it and write the result
    python scripts/run_fallback.py --dry-run       # show what would run, touch nothing

The result is committed. `consil doctor` reads it, fails if it is absent, malformed, undated,
older than 14 days, or records anything but a pass, and never reports `unknown`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULT = ROOT / ".harness" / "fallback-result.json"

# One command, fixed, documented, and deliberately dull. The task must be small enough that a
# failure means the fallback is broken rather than that the task was hard.
COMMAND = [
    "claude",
    "-p",
    "Read src/consilient/beta.py and reply with the exact name of the function that "
    "computes the Wilson score interval. Reply with the name alone and nothing else.",
]
EXPECTED = "wilson"
TIMEOUT_S = 300


def run() -> tuple[str, str]:
    """Return (outcome, detail). Any failure to run IS a failed fallback, not an error."""
    try:
        completed = subprocess.run(
            COMMAND,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_S,
        )
    except FileNotFoundError:
        return "fail", "the `claude` executable is not on PATH"
    except subprocess.TimeoutExpired:
        return "fail", f"no answer within {TIMEOUT_S}s"

    if completed.returncode != 0:
        return "fail", f"exit {completed.returncode}"
    answer = completed.stdout.strip().lower()
    if EXPECTED not in answer:
        # The transcript is not recorded: it is a model's prose about this repository, and the
        # result file is committed. The verdict and its length are enough to diagnose from.
        return (
            "fail",
            f"answer did not name `{EXPECTED}` ({len(answer)} chars returned)",
        )
    return "pass", f"answered in {len(answer)} chars"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the command and exit without running it or writing anything",
    )
    args = parser.parse_args()

    if args.dry_run:
        print(" ".join(COMMAND))
        return 0

    outcome, detail = run()
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(
        json.dumps(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "command": " ".join(COMMAND),
                "outcome": outcome,
                "detail": detail,
                "run": "local",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"{outcome}: {detail}")
    print(f"written to {RESULT.relative_to(ROOT).as_posix()}")
    # Exit 0 either way. A failed fallback is a recorded measurement, not a broken script, and
    # a non-zero exit here would make a scheduler treat evidence as an error.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

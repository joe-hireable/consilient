#!/usr/bin/env python
"""No source file may exceed 500 lines, and the count of offenders may only fall.

WHY THIS EXISTS. On 28 August 2026 the principal found `.harness/build_driver.py` at 4,101
lines and asked how it had been allowed to happen when every unit is adversarially reviewed by
a different model family. The answer was structural, and it is worth writing down here because
this file is the repair:

  * Nothing measured file size. Not a test, not a hook, not ruff -- `pyproject.toml` selected
    only RUF100, so no C901, no PLR0915, no max-lines.
  * The review brief says "a finding is a failing check or a reproduction, never an opinion.
    If you cannot express a concern as something that fails, do not file it." With no check to
    fail, a reviewer who noticed was *instructed to stay silent*.
  * The same brief says "anything touched outside your claimed paths is a finding" -- so
    splitting the file you are editing counted AGAINST you. Cleanup was penalised.

Fifty-nine files passed 500 lines with every gate green. That is not a reviewer failure; it is
the absence of an enforcement rule, which AGENTS.md principle 3 says is no rule at all.

WHERE THE NUMBER COMES FROM, and it is not where it came from at first. The original cap of 500
was calibrated against ONE unnamed reference codebase (median 94, 90th percentile 261, 1.7% of
files over 500). Working principle 9 requires the bar be recorded so it can be RE-CHECKED, and
an unnamed reference cannot be re-checked by anyone. ADR-0111, accepted by the principal on
29 August 2026, replaced it with named, permissively-licensed corpora that anyone can re-measure:

                                     files   median   90th pct   >500     >1000
    CPython 3.13.11 stdlib             564      252      1,184   27.3%    12.2%
    12 mature libraries, pooled        616      208      1,144   28.4%    13.0%
    the old unnamed reference            -       94        261    1.7%        -

Tests, generated tables and vendored trees excluded from both. Under a 500 cap the Python
standard library would post 154 offenders; `typing.py` is 3,831 lines and `tarfile.py` 3,070.
The published bar agrees: pylint's `max-module-lines` defaults to 1000 and is on by default,
SonarQube's python:S104 is 1000, Checkstyle is 2000, and ESLint's 300 ships disabled. Thirteen
tools and style guides were searched and NONE names 500.

WHAT THIS CAP CANNOT DO, said plainly so nobody claims otherwise. The empirical literature does
not support "smaller files have fewer defects" -- Hatton (1997) finds a U-shaped curve with the
optimum near 200-400 LOC, and Koru et al. (2008) find smaller modules proportionally MORE defect
prone. This is a review-cognition guard, which is what Sonar's own `brain-overload` tag says it
is. It is not a defect-reduction measure and must never be described as one. The per-function
limits in pyproject.toml are where the published weight of practice actually sits, and they are
the half that catches a 777-line `main` inside an otherwise ordinary file.

THE STANDARD IS A CAP, NOT A RATIO. A percentage lets one 4,000-line file hide inside a large
denominator. A cap cannot be gamed by growing the repo.

HOW THE RATCHET WORKS, AND HOW IT STAYS REVERSIBLE. CEILING is the number of offending files
allowed, and it may only ever be lowered -- but only AT A GIVEN LIMIT, which is what
CEILING_AT_LIMIT records. That pairing is not decoration; it is the repair for a trap ADR-0111
found before walking into it. This check fails in BOTH directions, so raising LIMIT forces
CEILING down in the same commit; and if "never raise CEILING" were then read absolutely, LOWERING
the limit again would be forbidden for ever, because fewer lines means more offenders. The cap
would have been a one-way door held shut by its own anti-loosening rule.

So the rule is: at an unchanged LIMIT, CEILING may only fall. When LIMIT changes, CEILING is
re-derived and CEILING_AT_LIMIT moves with it, and that pair of edits needs an ADR --
`tests/test_file_length_cap.py` fails if LIMIT moves without one.

EXEMPT: docs/10-research/experiments/. Those are frozen evidence whose reproducibility is their
value, AGENTS.md makes docs/10-research/ ask-first, and splitting them would trade the evidence
base for a percentage point.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
LIMIT = 1000
EXEMPT_PREFIXES = ("docs/10-research/experiments/",)

# The ratchet. Lower it with every split; never raise it AT THIS LIMIT. Measured 29 August 2026:
# one offender at 1,000 lines, `.harness/build_driver.py` at 4,101, which no split fixes because
# it is a single 777-line `main` and needs helpers extracted instead.
CEILING = 1

# The limit CEILING was counted against. Changing LIMIT without moving this is what makes the cap
# irreversible, so the two move together or tests/test_file_length_cap.py fails. See the ratchet
# paragraph in the module docstring: this pair is ADR-0111's reversibility repair, not bookkeeping.
CEILING_AT_LIMIT = 1000

# The decision that set LIMIT. Working principle 3: a chokepoint without an enforcement rule is
# not a chokepoint, and the first version of this cap had none -- no ADR established 500 and no
# test asserted it, so any agent could have moved it silently. Now moving it fails a test that
# names this constant.
LIMIT_ADR = "0111"

# git exports GIT_DIR and GIT_INDEX_FILE into every hook it runs, and GIT_DIR overrides
# cwd -- so a gate script inheriting them lists a DIFFERENT repository than the one it was
# pointed at, and reports a clean ratchet for a tree it never looked at.
GIT_ENV = {
    key: value for key, value in os.environ.items() if not key.startswith("GIT_")
}


def _tracked_python() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=str(ROOT),
        env=GIT_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return [p for p in out.stdout.split() if p]


def offenders(paths: list[str] | None = None) -> list[tuple[int, str]]:
    """Every tracked, non-exempt .py file over LIMIT lines, largest first."""
    found: list[tuple[int, str]] = []
    for rel in paths if paths is not None else _tracked_python():
        if rel.startswith(EXEMPT_PREFIXES):
            continue
        path = ROOT / rel
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                n = sum(1 for _ in handle)
        except OSError:
            continue
        if n > LIMIT:
            found.append((n, rel))
    found.sort(reverse=True)
    return found


def _self_test() -> int:
    """The checker must redden on a file that is too long, or it guards nothing."""
    with tempfile.TemporaryDirectory() as scratch:
        planted = pathlib.Path(scratch) / "too_long.py"
        planted.write_text("# line\n" * (LIMIT + 1), encoding="utf-8")
        # counted directly rather than through git, so the probe needs no index
        with planted.open("r", encoding="utf-8") as handle:
            n = sum(1 for _ in handle)
        if n <= LIMIT:
            print(
                "check_file_length self-test FAILED: planted file was not over the limit"
            )
            return 1

    exempt = offenders(["docs/10-research/experiments/run_exp96.py"])
    if exempt:
        print("check_file_length self-test FAILED: the exemption did not apply")
        return 1

    caught = offenders([".harness/build_driver.py"])
    if not caught:
        print(
            "check_file_length self-test FAILED: a known oversized file was not reported. "
            "If build_driver.py is now under the limit, pick another and update this probe."
        )
        return 1
    print("check_file_length self-test: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()

    if CEILING_AT_LIMIT != LIMIT:
        print(
            f"FAIL the ratchet holds {CEILING} counted at {CEILING_AT_LIMIT} lines, but LIMIT "
            f"is {LIMIT}.\n  A ceiling means nothing without the limit it was counted against. "
            f"Re-derive both: set CEILING to the offender count at {LIMIT} and CEILING_AT_LIMIT "
            f"to {LIMIT}, in one commit, citing the ADR that moved the limit."
        )
        return 1

    found = offenders()
    count = len(found)
    total = sum(n for n, _ in found)

    if count > CEILING:
        print(
            f"FAIL {count} file(s) over {LIMIT} lines; the ratchet allows {CEILING}.\n"
            f"  Split something, or say plainly why this file is the exception."
        )
        for n, rel in found[:15]:
            print(f"  {n:6,}  {rel}")
        return 1

    if count < CEILING:
        print(
            f"FAIL the ratchet is stale: {count} file(s) over {LIMIT} lines but CEILING is "
            f"{CEILING}.\n  Lower CEILING to {count} in this same commit -- a ratchet that "
            f"is not tightened when the work is done stops meaning anything."
        )
        return 1

    print(
        f"file length: {count} file(s) over {LIMIT} lines ({total:,} lines), "
        f"at the ratchet. Target is 0."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

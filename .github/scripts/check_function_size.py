#!/usr/bin/env python
"""No function may grow past 50 statements or complexity 10, and the counts may only fall.

WHY THIS EXISTS, and why the file-length cap is not enough on its own. ADR-0111 established that
the published weight of practice caps FUNCTIONS, not files: Google's Python guide suggests ~40
lines, the Linux kernel says "one or two screenfuls", Checkstyle's MethodLength is 150, ESLint's
max-lines-per-function is 50, and pylint's max-statements -- which this implements via ruff's
PLR0915 -- is 50. A per-file cap is the uncommon rule; a per-function cap is the common one.

The distinction is not academic here. It is the whole diagnosis:

  * `.harness/build_driver.py` is 4,101 lines because of a single 777-line `main`. No file cap
    under 4,000 catches it, and splitting the file does not fix it -- any file holding that
    function lands near 820. It needs helpers EXTRACTED, which is a code change, not a move.
  * A facade split satisfies a per-file cap WITHOUT IMPROVING A SINGLE FUNCTION. That is what
    happened across 28-29 August 2026: ten modules became sixty files and not one function got
    shorter. The cap was met and nothing was made more readable.

So this is the half of the rule that measures the thing a reader actually has to hold in their
head at once.

WHY IT IS A SEPARATE GATE AND NOT `extend-select` IN pyproject.toml. Adding PLR0915 and C901 there
would make plain `ruff check` fail across the tree, and every dispatched unit runs `ruff check`.
The loop would reject correct work for pre-existing violations it did not cause and was never
briefed about. A ratchet reports the count; a linter rejects the file. The count is what can fall
gradually, so the count is what is enforced.

THE RATCHET. Both ceilings may only ever be lowered, and this fails in BOTH directions: too many
is a regression, too few is a stale ratchet that stopped meaning anything. Measured 29 August 2026
against the tracked tree, exempting frozen experiments for the reason check_file_length.py gives.

EXEMPT: docs/10-research/experiments/ -- frozen evidence whose reproducibility is its value.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXEMPT_PREFIXES = ("docs/10-research/experiments/",)
RULES = ("PLR0915", "C901")

# The ratchet, per rule. Lower with every extraction; never raise. Measured 29 August 2026.
CEILINGS = {"PLR0915": 38, "C901": 123}

# ADR-0111 decided that a per-function limit is where the published bar sits.
RULES_ADR = "0111"

# git exports GIT_DIR into every hook it runs, and GIT_DIR overrides cwd -- so a gate script
# inheriting it lists a DIFFERENT repository than the one it was pointed at. Same hazard, same
# repair, as check_file_length.py.
GIT_ENV = {
    key: value for key, value in os.environ.items() if not key.startswith("GIT_")
}


def tracked_python() -> list[str]:
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
    return [p for p in out.stdout.split() if p and not p.startswith(EXEMPT_PREFIXES)]


def violations(paths: list[str] | None = None) -> list[dict[str, object]]:
    """Every PLR0915 / C901 hit in the tracked tree, as ruff reports them.

    The file list goes in through a file, not the command line. 445 tracked paths exceeded the
    Windows command-line limit and ruff was never run at all -- it reported "The command line is
    too long" and a naive caller would have read that as zero violations.
    """
    files = paths if paths is not None else tracked_python()
    if not files:
        return []
    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    ) as handle:
        handle.write("\n".join(files))
        listing = handle.name
    try:
        out = subprocess.run(
            [
                "python",
                "-m",
                "ruff",
                "check",
                "--select",
                ",".join(RULES),
                "--output-format",
                "json",
                "--no-cache",
                # .harness is excluded in pyproject.toml, but its tracked driver scripts are the
                # very files this rule exists for. --no-force-exclude honours an explicit path.
                "--no-force-exclude",
                f"@{listing}",
            ],
            cwd=str(ROOT),
            env=GIT_ENV,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        if not out.stdout.strip():
            raise SystemExit(
                "check_function_size: ruff produced no output; it did not run.\n"
                + out.stderr
            )
        return list(json.loads(out.stdout))
    finally:
        pathlib.Path(listing).unlink(missing_ok=True)


def by_rule(found: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    out: dict[str, list[dict[str, object]]] = {rule: [] for rule in RULES}
    for item in found:
        code = str(item.get("code") or "")
        if code in out:
            out[code].append(item)
    return out


def _self_test() -> int:
    """The checker must redden on a function that is too long, or it guards nothing."""
    with tempfile.TemporaryDirectory() as scratch:
        planted = pathlib.Path(scratch) / "too_many.py"
        body = "\n".join(f"    x{i} = {i}" for i in range(80))
        planted.write_text(f"def f() -> None:\n{body}\n", encoding="utf-8")
        hits = violations([str(planted)])
        if not any(str(h.get("code")) == "PLR0915" for h in hits):
            print(
                "check_function_size self-test FAILED: a 80-statement function was not caught"
            )
            return 1
    print("check_function_size self-test: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()

    grouped = by_rule(violations())
    failed = False
    for rule in RULES:
        hits = grouped[rule]
        count = len(hits)
        ceiling = CEILINGS[rule]
        if count > ceiling:
            failed = True
            print(f"FAIL {count} {rule} violation(s); the ratchet allows {ceiling}.")
            worst = sorted(hits, key=lambda h: str(h.get("filename")))[:10]
            for hit in worst:
                name = pathlib.Path(str(hit.get("filename"))).name
                location = hit.get("location")
                row = location.get("row") if isinstance(location, dict) else "?"
                print(f"  {name}:{row}  {hit.get('message')}")
        elif count < ceiling:
            failed = True
            print(
                f"FAIL the {rule} ratchet is stale: {count} violation(s) but the ceiling is "
                f"{ceiling}.\n  Lower it to {count} in this same commit -- a ratchet that is not "
                f"tightened when the work is done stops meaning anything."
            )
        else:
            print(
                f"function size: {count} {rule} violation(s), at the ratchet. Target is 0."
            )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

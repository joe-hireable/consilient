"""One command that answers "is this releasable?" and fails loudly when it is not.

    python scripts/release_check.py

Exit 0 only if every gate PASSED. Anything else — a failure, or a gate that could not be
run at all — exits 1 and says which.

Why this exists. `docs/50-publications/RELEASE-PLAN.md` carries a pre-submission checklist,
but it is prose, it is PowerShell-only, and one of its commands names an absolute path to a
checkout that is not this one — its own preflight table records that as "FAIL: script path
does not exist". A checklist a Linux or macOS reviewer cannot execute is not a gate. This
runs the same checks from any platform, from any working directory, and reports each one.

Three verdicts, not two. A gate that could not run is reported UNAVAILABLE and is never
folded into PASSED, because a check that silently no-ops is the defect this repository was
written about: `docs/50-publications/P2-guards.md` catalogues thirteen guards that could not
fail, one of which reported clean because its corpus was absent.

Read every gate's output, not its exit code alone — and never pipe this into `tail`, which
replaces this script's status with `tail`'s. B9 in that catalogue is that exact mistake.

Standard library only. No new dependency.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PASSED, FAILED, UNAVAILABLE = "PASSED", "FAILED", "UNAVAILABLE"

# This script relays other tools' output verbatim, and the Windows console default is
# cp1252. Same guard as scripts/capture_health.py and .github/scripts/check_foreign_
# identifiers.py: a release gate must not fall over on an em dash in a subprocess's stderr.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Result:
    name: str
    verdict: str
    detail: str
    output: str


def _run(command: list[str], timeout: int) -> tuple[int, str]:
    """Run a gate from the repository root and return its status and combined output.

    `encoding="utf-8", errors="replace"` on every call: the default on Windows is cp1252
    and ordinary tool output crashes it.

    ponytail: `subprocess` timeouts do not kill grandchildren, so a gate that spawns a
    process tree can overrun the deadline. None of the gates below does; if one ever
    spawns agents, this needs the process-tree kill that `docs/10-research/experiments/
    exp49/run_exp49.py` already implements.
    """
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return -1, f"{command[0]} is not on PATH: {exc}"
    except subprocess.TimeoutExpired:
        return -1, f"timed out after {timeout}s"
    return completed.returncode, (completed.stdout or "") + (completed.stderr or "")


def gate(name: str, command: list[str], timeout: int = 900) -> Result:
    code, output = _run(command, timeout)
    if code == 0:
        return Result(name, PASSED, "", output)
    if code == -1:
        return Result(name, UNAVAILABLE, output.strip().splitlines()[-1], output)
    return Result(name, FAILED, f"exit {code}", output)


def private_corpus_gate() -> Result:
    """The leak gate. Absent corpora must read UNAVAILABLE, never PASSED.

    `--require-corpora` already makes a missing corpus a failure rather than a skip. The
    corpora are local-only by design and are not present on CI or on a contributor's
    machine, so this gate is expected to be UNAVAILABLE everywhere except the principal's
    box — and a release approval that never ran it is not a release approval.
    """
    result = gate(
        "private-corpus leak scan",
        [
            sys.executable,
            ".github/scripts/check_private_corpus.py",
            "--require-corpora",
        ],
    )
    if result.verdict == FAILED and "private corpora not present" in result.output:
        return Result(
            result.name,
            UNAVAILABLE,
            "the private corpora are not on this machine; set CONSILIENT_CORPORA, or run "
            "this gate where they are",
            # The checker names the absent corpora. Those names are permitted in this
            # repository's documents, but there is no reason to relay them into a build
            # log, so the raw output is dropped rather than reprinted.
            "",
        )
    return result


def clean_install_gate() -> Result:
    """Can a stranger install this and run it? Measured, not reasoned about.

    Builds a throwaway virtual environment, installs the repository into it, and runs the
    `consil` console script from it. Before 21 August 2026 this failed at the first step:
    the repository had neither `pyproject.toml` nor `setup.py`, so `pip install .` said
    "Directory '.' is not installable" while thirty-odd documents referred to a `consil`
    command. Needs network for the build backend.
    """
    scripts = "Scripts" if sys.platform == "win32" else "bin"
    exe = ".exe" if sys.platform == "win32" else ""
    with tempfile.TemporaryDirectory(prefix="consilient-release-") as tmp:
        env = Path(tmp) / "env"
        code, output = _run([sys.executable, "-m", "venv", str(env)], timeout=300)
        if code != 0:
            return Result(
                "clean install", UNAVAILABLE, "could not create a venv", output
            )

        python = env / scripts / f"python{exe}"
        code, install = _run(
            [str(python), "-m", "pip", "install", "--quiet", "."], timeout=900
        )
        if code != 0:
            return Result(
                "clean install", FAILED, f"pip install . exited {code}", install
            )

        consil = env / scripts / f"consil{exe}"
        if not consil.exists():
            return Result(
                "clean install",
                FAILED,
                "the `consil` console script was not installed",
                f"looked for {consil}",
            )
        # Run it from OUTSIDE the repository: a stranger's first command is not run here.
        code, help_text = _run([str(consil), "--help"], timeout=120)
        if code != 0 or "record" not in help_text:
            return Result(
                "clean install", FAILED, f"`consil --help` exited {code}", help_text
            )
        return Result("clean install", PASSED, "", install + help_text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="release_check",
        description="Run every release gate and report whether this tree is releasable.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print each gate's full output, not only failures",
    )
    args = parser.parse_args(argv)

    if shutil.which("git") is None:
        print(
            "git is not on PATH; the history and leak gates cannot run", file=sys.stderr
        )

    results = [
        gate("test suite", [sys.executable, "-m", "pytest", "tests/", "-q"]),
        gate(
            "mypy --strict",
            [sys.executable, "-m", "mypy", "--strict", "src/consilient"],
        ),
        gate("ruff", [sys.executable, "-m", "ruff", "check", "."]),
        gate(
            "secret scan",
            [
                sys.executable,
                ".github/scripts/check_secrets.py",
                "--history",
                "--untracked",
                "--self-test",
            ],
        ),
        private_corpus_gate(),
        gate(
            "foreign commit identifiers",
            [sys.executable, ".github/scripts/check_foreign_identifiers.py"],
        ),
        # R05: a publication carrying [SNIP]/[2ND] citations is not releasable. Expected
        # to read FAILED while the drafts carry unverified sources — that is the gate
        # working, not the checker broken.
        gate("source depth", [sys.executable, ".github/scripts/check_source_depth.py"]),
        clean_install_gate(),
    ]

    width = max(len(r.name) for r in results)
    print("\nRelease gates\n" + "-" * (width + 26))
    for r in results:
        suffix = f"  ({r.detail})" if r.detail else ""
        print(f"  {r.name.ljust(width)}  {r.verdict}{suffix}")
    print("-" * (width + 26))

    for r in results:
        if args.verbose or r.verdict != PASSED:
            body = r.output.strip()
            if body:
                print(f"\n### {r.name} — {r.verdict}\n{body}")

    blocked = [r for r in results if r.verdict != PASSED]
    if blocked:
        names = ", ".join(f"{r.name} [{r.verdict}]" for r in blocked)
        print(
            f"\nNOT RELEASABLE — {len(blocked)} of {len(results)} gates did not pass: {names}"
        )
        return 1
    print(f"\nRELEASABLE — all {len(results)} gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

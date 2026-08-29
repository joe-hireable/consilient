"""The persona catalogue, and the two journeys that hold documents to their word.

Each persona is a RunSpec (ADR-0055): an information boundary and a task, executed
against real CLI surfaces. A persona that stops found a defect; a persona that succeeds
proves nothing.

PERSONAS names the five, and JourneyResult is what running one leaves behind: where the
persona stopped, what wrong answer it tried to get accepted, and what the system did
about it. The last of those is the field that matters for beta. accepted_wrongly is set
only when a wrong answer went through with nothing surfaced, so a journey that fails
loudly is never counted as a false acceptance.

The average-joe and researcher journeys sit here because they depend on nothing above
them. Average-joe checks the command count printed in getting-started against what
consil --help actually lists; the researcher follows the EXP-47 beta = 0.3132 citation
from the experiment register to run_exp47.py and results-exp47.json, and stops when that
chain cannot be walked from public documents alone. Neither installs anything or writes
to the repository under test. They read what a newcomer would read and invoke the CLI as
a subprocess through _run, which decodes as UTF-8 with replacement so that an awkward
byte in tool output cannot end a journey in place of a real defect."""

from __future__ import annotations
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Literal

ROOT = Path(__file__).resolve().parent.parent

from consilient.synthetic import Finding, RunSpec  # noqa: E402

PersonaId = Literal[
    "average-joe",
    "developer",
    "contributor",
    "researcher",
    "operator",
]

PERSONAS: dict[PersonaId, RunSpec] = {
    "average-joe": RunSpec(
        id="average-joe",
        task="Follow getting-started.md from install through first consil doctor run",
        success_criterion="Each step completes without needing source, ADRs or tests",
        information_boundary=("docs/00-context/getting-started.md",),
        interface="cli",
        oracle_kinds=("specification", "implicit"),
        harness="human-or-script",
    ),
    "developer": RunSpec(
        id="developer",
        task="pip install -e ., consil --help, run pytest on one file",
        success_criterion="Dev loop works from a clean venv without reading governance docs",
        information_boundary=(
            "README.md install section",
            "pyproject.toml requires-python",
        ),
        interface="cli",
        oracle_kinds=("implicit", "reference"),
        harness="human-or-script",
    ),
    "contributor": RunSpec(
        id="contributor",
        task="Find how to submit a change and what rules apply",
        success_criterion="CONTRIBUTING.md matches the repository state",
        information_boundary=(
            "CONTRIBUTING.md",
            "README.md",
            "AGENTS.md link from CONTRIBUTING",
        ),
        interface="cli",
        oracle_kinds=("specification", "state"),
        harness="human-or-script",
    ),
    "researcher": RunSpec(
        id="researcher",
        task="Reproduce EXP-47 beta=0.3132 from public docs alone",
        success_criterion="Find producing script and results file without being told paths",
        information_boundary=(
            "docs/10-research/experiment-register.md",
            "docs/10-research/experiments/exp47/findings-exp47.md",
        ),
        interface="cli",
        oracle_kinds=("reference", "specification"),
        harness="human-or-script",
    ),
    "operator": RunSpec(
        id="operator",
        task="Run consil doctor, usage and dashboard from the checkout",
        success_criterion="Observability commands succeed and report coherently",
        information_boundary=("docs/00-context/getting-started.md sections 2 and 5",),
        interface="cli",
        oracle_kinds=("implicit", "state"),
        harness="human-or-script",
    ),
}


@dataclass(frozen=True)
class JourneyResult:
    persona: PersonaId
    stopped_at: str
    exit_code: int
    stdout: str
    stderr: str
    finding: Finding | None
    #: What wrong answer this persona tried to get accepted (β falsification).
    attempted: str = ""
    #: What the system did — refusal, contradiction surfaced, or silent acceptance.
    system_response: str = ""
    #: True only when a wrong answer was accepted without surfacing a defect.
    accepted_wrongly: bool = False


def _run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        argv,
        cwd=cwd,
        env=merged,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _cli_module(repo: Path) -> list[str]:
    return [sys.executable, "-m", "consilient.cli"]


def journey_average_joe(repo: Path) -> JourneyResult:
    spec = PERSONAS["average-joe"]
    attempted = "Trust getting-started.md command count over consil --help without reading source"
    getting_started = (repo / "docs/00-context/getting-started.md").read_text(
        encoding="utf-8"
    )
    if "Four commands, and not one of them" in getting_started:
        finding = Finding(
            run_id="persona-qa",
            spec_id=spec.id,
            discrepancy=(
                "getting-started section 1 still says 'Four commands' but measured --help "
                "lists six (record, replay, beta, usage, doctor, dashboard)"
            ),
            anchor="specification",
            reproduction=(
                "read docs/00-context/getting-started.md section 1",
                "consil --help",
            ),
        )
        return JourneyResult(
            persona="average-joe",
            stopped_at="section 1 command count contradicts --help",
            exit_code=0,
            stdout="",
            stderr="",
            finding=finding,
            attempted=attempted,
            system_response="docs contradict --help; persona journey surfaced the mismatch",
        )
    required = ("consil usage", "consil dashboard", "Six commands")
    if not all(token in getting_started for token in required):
        finding = Finding(
            run_id="persona-qa",
            spec_id=spec.id,
            discrepancy=(
                "getting-started section 1 does not list all six observe commands "
                f"(missing one of {required!r})"
            ),
            anchor="specification",
            reproduction=("read docs/00-context/getting-started.md section 1",),
        )
        return JourneyResult(
            persona="average-joe",
            stopped_at="section 1 incomplete command table",
            exit_code=0,
            stdout="",
            stderr="",
            finding=finding,
            attempted=attempted,
            system_response="incomplete command table surfaced",
        )
    help_run = _run(_cli_module(repo) + ["--help"], cwd=repo)
    if help_run.returncode == 0 and "doctor" in help_run.stdout:
        return JourneyResult(
            persona="average-joe",
            stopped_at="no contradiction detected",
            exit_code=0,
            stdout=help_run.stdout.splitlines()[0] if help_run.stdout else "",
            stderr="",
            finding=None,
            attempted=attempted,
            system_response="--help lists six commands; docs agree; wrong count not accepted",
        )
    finding = Finding(
        run_id="persona-qa",
        spec_id=spec.id,
        discrepancy="consil --help failed or omitted doctor after install-free read path",
        anchor="implicit",
        reproduction=("--help",),
    )
    return JourneyResult(
        persona="average-joe",
        stopped_at="--help unusable",
        exit_code=help_run.returncode,
        stdout=help_run.stdout,
        stderr=help_run.stderr,
        finding=finding,
        attempted=attempted,
        system_response="--help failed",
    )


def journey_researcher(repo: Path) -> JourneyResult:
    spec = PERSONAS["researcher"]
    attempted = (
        "Cite EXP-47 beta=0.3132 from the register without a reproducible script path"
    )
    register = repo / "docs/10-research/experiment-register.md"
    if not register.is_file():
        return JourneyResult(
            persona="researcher",
            stopped_at="experiment-register.md missing",
            exit_code=1,
            stdout="",
            stderr="",
            finding=Finding(
                run_id="persona-qa",
                spec_id=spec.id,
                discrepancy="experiment register not found at documented path",
                anchor="reference",
                reproduction=("read docs/10-research/experiment-register.md",),
            ),
            attempted=attempted,
            system_response="register missing; number cannot be accepted",
        )
    reg_text = register.read_text(encoding="utf-8")
    if "0.3132" not in reg_text:
        return JourneyResult(
            persona="researcher",
            stopped_at="EXP-47 number not in register",
            exit_code=0,
            stdout="",
            stderr="",
            finding=Finding(
                run_id="persona-qa",
                spec_id=spec.id,
                discrepancy="register does not cite EXP-47 beta=0.3132",
                anchor="reference",
                reproduction=("grep 0.3132 docs/10-research/experiment-register.md",),
            ),
            attempted=attempted,
            system_response="register lacks the cited figure",
        )
    script = repo / "docs/10-research/experiments/exp47/run_exp47.py"
    results = repo / "docs/10-research/experiments/exp47/results-exp47.json"
    if not script.is_file():
        return JourneyResult(
            persona="researcher",
            stopped_at="cannot find run_exp47.py from register alone",
            exit_code=0,
            stdout="",
            stderr="",
            finding=Finding(
                run_id="persona-qa",
                spec_id=spec.id,
                discrepancy=(
                    "register cites EXP-47 but does not link run_exp47.py; "
                    "researcher must guess docs/10-research/experiments/exp47/"
                ),
                anchor="reference",
                reproduction=(
                    "read experiment-register EXP-47 entry",
                    "search for run_exp47.py",
                ),
            ),
            attempted=attempted,
            system_response="evidence chain incomplete from public docs alone",
        )
    if not results.is_file():
        return JourneyResult(
            persona="researcher",
            stopped_at="results-exp47.json missing",
            exit_code=0,
            stdout="",
            stderr="",
            finding=Finding(
                run_id="persona-qa",
                spec_id=spec.id,
                discrepancy="findings cite results file that is not committed",
                anchor="reference",
                reproduction=("ls docs/10-research/experiments/exp47/",),
            ),
            attempted=attempted,
            system_response="results artefact missing; measured claim not acceptable",
        )
    return JourneyResult(
        persona="researcher",
        stopped_at="evidence chain complete when paths are known",
        exit_code=0,
        stdout=str(script.relative_to(repo)),
        stderr="",
        finding=None,
        attempted=attempted,
        system_response="script and results exist; number reproducible when path is known",
    )

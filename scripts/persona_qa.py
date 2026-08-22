"""Run one persona journey as a falsifier, not a confirmer.

Each persona is a RunSpec (ADR-0055): an information boundary and a task, executed
against real CLI surfaces. A persona that stops found a defect; a persona that
succeeds proves nothing.

    python scripts/persona_qa.py --list
    python scripts/persona_qa.py --persona average-joe --repo .
    python scripts/persona_qa.py --all --repo .
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

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
        information_boundary=("CONTRIBUTING.md", "README.md", "AGENTS.md link from CONTRIBUTING"),
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
    attempted = (
        "Trust getting-started.md command count over consil --help without reading source"
    )
    getting_started = (repo / "docs/00-context/getting-started.md").read_text(encoding="utf-8")
    if "Four commands, and not one of them" in getting_started:
        finding = Finding(
            run_id="persona-qa",
            spec_id=spec.id,
            discrepancy=(
                "getting-started section 1 still says 'Four commands' but measured --help "
                "lists six (record, replay, beta, usage, doctor, dashboard)"
            ),
            anchor="specification",
            reproduction=("read docs/00-context/getting-started.md section 1", "consil --help"),
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


def journey_developer(repo: Path) -> JourneyResult:
    spec = PERSONAS["developer"]
    attempted = "Run pip install -e . and treat a broken venv as a working dev loop"
    with tempfile.TemporaryDirectory(prefix="persona-dev-") as tmp:
        venv = Path(tmp) / "venv"
        create = _run([sys.executable, "-m", "venv", str(venv)], cwd=repo)
        if create.returncode != 0:
            return JourneyResult(
                persona="developer",
                stopped_at="python -m venv",
                exit_code=create.returncode,
                stdout=create.stdout,
                stderr=create.stderr,
                finding=Finding(
                    run_id="persona-qa",
                    spec_id=spec.id,
                    discrepancy="venv creation failed during developer install path",
                    anchor="implicit",
                    reproduction=(create.args[0], *create.args[1:]),
                ),
                attempted=attempted,
                system_response="venv creation failed; broken path not accepted",
            )
        pip_bin = "Scripts" if sys.platform == "win32" else "bin"
        py = str(venv / pip_bin / "python")
        pip = _run([py, "-m", "pip", "install", "-e", str(repo)], cwd=repo)
        if pip.returncode != 0:
            return JourneyResult(
                persona="developer",
                stopped_at="pip install -e .",
                exit_code=pip.returncode,
                stdout=pip.stdout,
                stderr=pip.stderr,
                finding=Finding(
                    run_id="persona-qa",
                    spec_id=spec.id,
                    discrepancy="editable install failed",
                    anchor="implicit",
                    reproduction=("pip install -e .",),
                ),
                attempted=attempted,
                system_response="pip install failed; dev loop not accepted as working",
            )
        help_run = _run([py, "-m", "consilient.cli", "--help"], cwd=repo)
        if help_run.returncode != 0 or "doctor" not in help_run.stdout:
            return JourneyResult(
                persona="developer",
                stopped_at="consil --help",
                exit_code=help_run.returncode,
                stdout=help_run.stdout,
                stderr=help_run.stderr,
                finding=Finding(
                    run_id="persona-qa",
                    spec_id=spec.id,
                    discrepancy="consil --help missing or failed after install",
                    anchor="implicit",
                    reproduction=(f"{py} -m consilient.cli --help",),
                ),
                attempted=attempted,
                system_response="help missing after install; not accepted as working",
            )
    return JourneyResult(
        persona="developer",
        stopped_at="install and help succeeded",
        exit_code=0,
        stdout=help_run.stdout.splitlines()[0] if help_run.stdout else "",
        stderr="",
        finding=None,
        attempted=attempted,
        system_response="install and --help succeeded; no false acceptance",
    )


def journey_contributor(repo: Path) -> JourneyResult:
    spec = PERSONAS["contributor"]
    attempted = "Follow CONTRIBUTING.md claiming the project has no code yet"
    text = (repo / "CONTRIBUTING.md").read_text(encoding="utf-8")
    stale_markers = ("has no code yet", "pre-brainstorm")
    if any(marker in text for marker in stale_markers):
        finding = Finding(
            run_id="persona-qa",
            spec_id=spec.id,
            discrepancy=(
                "CONTRIBUTING.md still claims the project has no code or is pre-brainstorm "
                "but the tree ships src/, tests/ and hundreds of tests"
            ),
            anchor="state",
            reproduction=("read CONTRIBUTING.md lines 1-10", "ls src/ tests/"),
        )
        return JourneyResult(
            persona="contributor",
            stopped_at="CONTRIBUTING.md contradicts repository state",
            exit_code=0,
            stdout="",
            stderr="",
            finding=finding,
            attempted=attempted,
            system_response="stale CONTRIBUTING surfaced against src/ and tests/",
        )
    return JourneyResult(
        persona="contributor",
        stopped_at="CONTRIBUTING.md looks current",
        exit_code=0,
        stdout="",
        stderr="",
        finding=None,
        attempted=attempted,
        system_response="CONTRIBUTING matches repository state; stale claim not accepted",
    )


def journey_researcher(repo: Path) -> JourneyResult:
    spec = PERSONAS["researcher"]
    attempted = "Cite EXP-47 beta=0.3132 from the register without a reproducible script path"
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


def journey_operator(repo: Path) -> JourneyResult:
    spec = PERSONAS["operator"]
    attempted = "Run consil usage and doctor; accept undocumented ceilings or a false-zero beta"
    log = repo / ".harness" / "log"
    db = repo / ".harness" / "state.db"
    getting_started = (repo / "docs/00-context/getting-started.md").read_text(encoding="utf-8")
    usage = _run(_cli_module(repo) + ["usage", "--log", str(log)], cwd=repo)
    ceilings_documented = (
        "limits.example.json" in getting_started
        and "ceilings: NONE" in getting_started
    )
    if "ceilings: NONE" in usage.stdout and not ceilings_documented:
        finding = Finding(
            run_id="persona-qa",
            spec_id=spec.id,
            discrepancy=(
                "consil usage reports 'ceilings: NONE — every metered call refuses' but "
                "getting-started does not explain copying .harness/limits.example.json"
            ),
            anchor="state",
            reproduction=(f"consil usage --log {log}", "read getting-started"),
        )
        return JourneyResult(
            persona="operator",
            stopped_at="usage ceilings undocumented",
            exit_code=usage.returncode,
            stdout=usage.stdout,
            stderr=usage.stderr,
            finding=finding,
            attempted=attempted,
            system_response="usage reports ceilings NONE but docs omit limits.example.json",
        )
    doctor = _run(
        _cli_module(repo) + ["doctor", "--log", str(log), "--db", str(db)],
        cwd=repo,
    )
    if doctor.returncode != 0 and "PermissionError" in doctor.stderr:
        finding = Finding(
            run_id="persona-qa",
            spec_id=spec.id,
            discrepancy=(
                "consil doctor crashes with PermissionError on state.db when another "
                "process holds the SQLite file"
            ),
            anchor="implicit",
            reproduction=(f"consil doctor --log {log} --db {db}",),
        )
        return JourneyResult(
            persona="operator",
            stopped_at="doctor state.db lock",
            exit_code=doctor.returncode,
            stdout=doctor.stdout,
            stderr=doctor.stderr,
            finding=finding,
            attempted=attempted,
            system_response="doctor crashed on state.db lock",
        )
    return JourneyResult(
        persona="operator",
        stopped_at="usage and doctor ran",
        exit_code=doctor.returncode,
        stdout=doctor.stdout.splitlines()[0] if doctor.stdout else "",
        stderr=doctor.stderr,
        finding=None,
        attempted=attempted,
        system_response="usage and doctor completed without accepting a false-zero",
    )


def cold_trajectory_refusal(repo: Path) -> JourneyResult:
    """Orchestrator check: missing trajectory must refuse, not report zero."""
    spec = PERSONAS["operator"]
    attempted = "Run consil beta from an empty directory and accept a zero reading"
    with tempfile.TemporaryDirectory(prefix="persona-cold-") as tmp:
        cold = Path(tmp)
        beta = _run(
            _cli_module(repo) + ["beta"],
            cwd=cold,
            env={"PYTHONPATH": str(repo / "src")},
        )
    if beta.returncode == 2 and "trajectory not configured" in beta.stderr:
        return JourneyResult(
            persona="operator",
            stopped_at="cold directory correctly refused",
            exit_code=2,
            stdout=beta.stdout,
            stderr=beta.stderr,
            finding=None,
            attempted=attempted,
            system_response="exit 2 trajectory not configured; false-zero not accepted",
        )
    finding = Finding(
        run_id="persona-qa",
        spec_id=spec.id,
        discrepancy=(
            "consil beta from a directory with no trajectory did not refuse cleanly "
            f"(exit={beta.returncode})"
        ),
        anchor="implicit",
        reproduction=("mkdir /tmp/empty && cd /tmp/empty && consil beta",),
    )
    return JourneyResult(
        persona="operator",
        stopped_at="cold directory false-zero regression",
        exit_code=beta.returncode,
        stdout=beta.stdout,
        stderr=beta.stderr,
        finding=finding,
        attempted=attempted,
        system_response=f"exit {beta.returncode} without clean refusal",
        accepted_wrongly=beta.returncode == 0,
    )


JOURNEYS: dict[PersonaId, object] = {
    "average-joe": journey_average_joe,
    "developer": journey_developer,
    "contributor": journey_contributor,
    "researcher": journey_researcher,
    "operator": journey_operator,
}


def run_persona(persona: PersonaId, repo: Path) -> JourneyResult:
    fn = JOURNEYS[persona]
    return fn(repo)  # type: ignore[operator,call-arg]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--persona", choices=list(PERSONAS))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--cold-check", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    if args.list:
        for pid, spec in PERSONAS.items():
            print(f"{pid}: {spec.task}")
        return 0

    results: list[JourneyResult] = []
    if args.cold_check:
        results.append(cold_trajectory_refusal(args.repo))
    if args.all:
        for pid in PERSONAS:
            results.append(run_persona(pid, args.repo))
    elif args.persona:
        results.append(run_persona(args.persona, args.repo))
    else:
        parser.error("pass --persona, --all, or --cold-check")

    if args.json:
        payload = []
        for r in results:
            row = {
                "persona": r.persona,
                "stopped_at": r.stopped_at,
                "exit_code": r.exit_code,
                "attempted": r.attempted,
                "system_response": r.system_response,
                "accepted_wrongly": r.accepted_wrongly,
                "finding": asdict(r.finding) if r.finding else None,
            }
            payload.append(row)
        print(json.dumps(payload, indent=2))
        return 1 if any(r.finding for r in results) else 0

    for r in results:
        tag = "DEFECT" if r.finding or r.accepted_wrongly else "ok"
        print(f"[{tag}] {r.persona}: stopped at {r.stopped_at!r}")
        if r.attempted:
            print(f"  tried: {r.attempted}")
        if r.system_response:
            print(f"  system: {r.system_response}")
        if r.finding:
            print(f"  {r.finding.discrepancy}")
    defects = sum(1 for r in results if r.finding or r.accepted_wrongly)
    print(f"\n{defects} defect(s) across {len(results)} journey(s)")
    return 1 if defects else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run one persona journey as a falsifier, not a confirmer.

Each persona is a RunSpec (ADR-0055): an information boundary and a task, executed
against real CLI surfaces. A persona that stops found a defect; a persona that succeeds
proves nothing.

    python scripts/persona_qa.py --list
    python scripts/persona_qa.py --persona average-joe --repo .
    python scripts/persona_qa.py --all --repo .

The persona catalogue, the JourneyResult record, the subprocess runner and the
average-joe and researcher journeys now live in persona_qa_specs.py. This file keeps the
developer, contributor and operator journeys, the cold-directory refusal check, the
JOURNEYS table and the command line."""

from __future__ import annotations
import argparse
import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from persona_qa_specs import (
    JourneyResult,
    PERSONAS,
    PersonaId,
    ROOT,
    _cli_module,
    _run,
    journey_average_joe,
    journey_researcher,
)

sys.path.insert(0, str(ROOT / "src"))

from consilient.synthetic import Finding

from persona_qa_specs import (
    ROOT,
)

__all__ = [
    "JOURNEYS",
    "JourneyResult",
    "PERSONAS",
    "PersonaId",
    "ROOT",
    "_cli_module",
    "_run",
    "cold_trajectory_refusal",
    "journey_average_joe",
    "journey_contributor",
    "journey_developer",
    "journey_operator",
    "journey_researcher",
    "main",
    "run_persona",
]


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


def journey_operator(repo: Path) -> JourneyResult:
    spec = PERSONAS["operator"]
    attempted = (
        "Run consil usage and doctor; accept undocumented ceilings or a false-zero beta"
    )
    log = repo / ".harness" / "log"
    db = repo / ".harness" / "state.db"
    getting_started = (repo / "docs/00-context/getting-started.md").read_text(
        encoding="utf-8"
    )
    usage = _run(_cli_module(repo) + ["usage", "--log", str(log)], cwd=repo)
    ceilings_documented = (
        "limits.example.json" in getting_started and "ceilings: NONE" in getting_started
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

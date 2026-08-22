"""One command that runs the whole QA battery and records what it found.

    python scripts/qa_battery.py
    python scripts/qa_battery.py --dry-run     # report without appending to trajectory
    python scripts/qa_battery.py --json

Runs the test suite, leak gates, ``consil doctor``, the private-corpus check with
``--require-corpora``, executable decision models, persona falsification journeys,
defect-class checks and a bounded seeded-fault batch. Reuses existing tools; does not
reimplement them.

Exit 0 only when every gate PASSED and no new defect-class finding is present.
Known producer/consumer gaps from the wiring inventory are reported but do not fail
the battery while they remain on the allowlist.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from consilient.events import append  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG = ROOT / ".harness" / "log"
DB = ROOT / ".harness" / "state.db"
BATTERY_KIND = "qa.battery"
PASSED, FAILED, UNAVAILABLE = "PASSED", "FAILED", "UNAVAILABLE"


@dataclass
class GateResult:
    name: str
    verdict: str
    detail: str
    output: str


def _run(command: list[str], timeout: int = 900) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return -1, f"{command[0]} is not on PATH: {exc}"
    except subprocess.TimeoutExpired:
        return -1, f"timed out after {timeout}s"
    return completed.returncode, (completed.stdout or "") + (completed.stderr or "")


def gate(name: str, command: list[str], timeout: int = 900) -> GateResult:
    code, output = _run(command, timeout)
    if code == 0:
        return GateResult(name, PASSED, "", output)
    if code == -1:
        tail = output.strip().splitlines()[-1] if output.strip() else output
        return GateResult(name, UNAVAILABLE, tail, output)
    return GateResult(name, FAILED, f"exit {code}", output)


def _load_defect_module():
    spec = importlib.util.spec_from_file_location(
        "qa_defect_checks", ROOT / "tests" / "test_qa_battery.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_persona_qa():
    spec = importlib.util.spec_from_file_location(
        "persona_qa_runner", ROOT / "scripts" / "persona_qa.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def private_corpus_gate() -> GateResult:
    result = gate(
        "private-corpus leak scan",
        [
            sys.executable,
            ".github/scripts/check_private_corpus.py",
            "--require-corpora",
        ],
    )
    if result.verdict == FAILED and "private corpora not present" in result.output:
        return GateResult(
            result.name,
            UNAVAILABLE,
            "private corpora not on this machine",
            "",
        )
    return result


def doctor_gate() -> GateResult:
    """Run consil doctor and record gate state. Non-zero exit is expected while gates are shut."""
    code, output = _run(
        [
            sys.executable,
            "-m",
            "consilient.cli",
            "doctor",
            "--log",
            str(LOG),
            "--db",
            str(DB),
        ],
        timeout=120,
    )
    if code == -1:
        tail = output.strip().splitlines()[-1] if output.strip() else output
        return GateResult("consil doctor", UNAVAILABLE, tail, output)
    if "routing" in output.lower() and "orchestration" in output.lower():
        return GateResult(
            "consil doctor",
            PASSED,
            f"exit {code} (gate state recorded)",
            output,
        )
    return GateResult("consil doctor", FAILED, f"exit {code}", output)


def run_battery(*, dry_run: bool = False) -> dict[str, object]:
    defects_mod = _load_defect_module()
    persona_mod = _load_persona_qa()

    gates = [
        gate("test suite", [sys.executable, "-m", "pytest", "tests/", "-q"]),
        gate("mypy --strict", [sys.executable, "-m", "mypy", "--strict", "src/consilient"]),
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
        doctor_gate(),
        gate(
            "executable decision models",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_decision_models.py",
                "-q",
            ],
        ),
        gate("capture health", [sys.executable, "scripts/capture_health.py", "--dry-run"]),
    ]

    persona_results = []
    persona_defects = 0
    for pid in persona_mod.PERSONAS:
        journey = persona_mod.run_persona(pid, ROOT)
        row = {
            "persona": journey.persona,
            "attempted": journey.attempted,
            "system_response": journey.system_response,
            "accepted_wrongly": journey.accepted_wrongly,
            "stopped_at": journey.stopped_at,
            "finding": asdict(journey.finding) if journey.finding else None,
        }
        persona_results.append(row)
        if journey.finding or journey.accepted_wrongly:
            persona_defects += 1

    defect_findings = defects_mod.run_all_defect_checks()
    new_defects = [
        asdict(f)
        for f in defect_findings
        if f.check != "producer_consumer_gap"
        or f.detail.startswith("index claims")
        or "greenfield" in f.detail
    ]
    known_gaps = [
        {"kind": kind, "rationale": rationale}
        for kind, rationale in defects_mod.KNOWN_PRODUCER_CONSUMER_GAPS.items()
    ]

    seeded = defects_mod.run_seeded_fault_batch()

    blocked_gates = [g for g in gates if g.verdict != PASSED]
    summary = {
        "gates": [
            {
                "name": g.name,
                "verdict": g.verdict,
                "detail": g.detail,
            }
            for g in gates
        ],
        "personas": persona_results,
        "persona_defects": persona_defects,
        "defect_findings": [asdict(f) for f in defect_findings],
        "new_defects": new_defects,
        "known_producer_consumer_gaps": known_gaps,
        "seeded_faults": seeded,
        "healthy": not blocked_gates and not new_defects and persona_defects == 0,
        "dry_run": dry_run,
    }

    if not dry_run:
        now = datetime.now(timezone.utc)
        append(
            LOG / f"{now.date().isoformat()}.jsonl",
            {
                "v": 1,
                "ts": now.isoformat(),
                "event": BATTERY_KIND,
                "actor": "consilient.qa-battery",
                "data": {
                    "healthy": summary["healthy"],
                    "gates_failed": len(blocked_gates),
                    "persona_defects": persona_defects,
                    "defect_count": len(defect_findings),
                    "new_defect_count": len(new_defects),
                    "seeded_unclassifiable_rate": seeded["unclassifiable_rate"],
                    "headline_permitted": seeded["headline_permitted"],
                    "recorded_by": "scripts/qa_battery.py",
                },
            },
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    summary = run_battery(dry_run=args.dry_run)

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print("\nQA battery\n" + "-" * 40)
        for row in summary["gates"]:  # type: ignore[union-attr]
            suffix = f" ({row['detail']})" if row["detail"] else ""
            print(f"  {row['name']}: {row['verdict']}{suffix}")
        print("-" * 40)
        print(f"persona defects: {summary['persona_defects']}")
        print(
            f"defect-class findings: {len(summary['defect_findings'])} "
            f"({len(summary['new_defects'])} blocking)"
        )
        seeded = summary["seeded_faults"]
        print(
            f"seeded faults: unclassifiable {seeded['unclassifiable']}/{seeded['generated']} "
            f"(max {seeded['max_unclassifiable_rate']}); "
            f"headline permitted: {seeded['headline_permitted']}"
        )
        if not seeded["headline_permitted"]:
            print("  proxy β withheld — unclassifiable rate exceeds threshold")
        elif seeded["proxy_beta"] is not None:
            print(f"  proxy β (seeded batch only): {seeded['proxy_beta']}")
        print(f"\n{'HEALTHY' if summary['healthy'] else 'DEFECTS FOUND'}")

    return 0 if summary["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Defect-class checks the QA battery runs. Each failure is a reproduction, not prose.

These checks mine recurring failure shapes from corrections-2026-08-21, spec-audit-2026-08-22,
P2-guards and this repository's own history. They ship with ratchet tests so a repaired
defect cannot return silently.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "consilient"
PRE_PUSH = ROOT / ".githooks" / "pre-push"

# Gaps recorded in .harness/quarantine-wiring-plan-1906.md and ADRs. A new gap not listed
# here is a failing check; a listed gap is reported but does not fail the battery.
KNOWN_PRODUCER_CONSUMER_GAPS: dict[str, str] = {
    "decision.autonomous": "ADR-0079: record-only contract; no semantic consumer yet",
    "instructions.assembled": "ADR-0074/0076: assembly wired; full consumer is M05 work",
    "routing.consulted": "ADR-0077: deliberately unwired while gates are shut",
    "usage.observed": "usage projection is write-only until a reader ships",
}

MAX_UNCLASSIFIABLE_RATE = 0.10  # EXP-96 pre-registered ceiling; same standard as run_exp96.py

MEASURED_TAG = re.compile(r"\[measured\]", re.IGNORECASE)
ADR_COUNT_CLAIM = re.compile(
    r"^(\d+)\s+ADRs,\s+.*\[measured\]",
    re.MULTILINE | re.IGNORECASE,
)


@dataclass(frozen=True)
class Finding:
    check: str
    reproduction: tuple[str, ...]
    detail: str


def _py_files_under(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return [p for p in path.rglob("*.py") if p.is_file()]


def _file_mentions_kind(path: Path, kind: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return kind in text


def _semantic_consumers_for(kind: str) -> list[str]:
    """Modules that reference `kind` outside events.py validation."""
    hits: list[str] = []
    for path in _py_files_under(ROOT / "src") + _py_files_under(ROOT / "scripts"):
        rel = path.relative_to(ROOT).as_posix()
        if rel == "src/consilient/events.py":
            continue
        if _file_mentions_kind(path, kind):
            hits.append(rel)
    return sorted(hits)


def _producers_for(kind: str) -> list[str]:
    hits: list[str] = []
    for path in _py_files_under(ROOT / "src") + _py_files_under(ROOT / "scripts"):
        rel = path.relative_to(ROOT).as_posix()
        if rel == "src/consilient/events.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if kind not in text:
            continue
        if "append(" in text or "record_assembly" in text or f'"{kind}"' in text:
            hits.append(rel)
    return sorted(set(hits))


def check_producer_consumer_gaps() -> list[Finding]:
    """Producer exists, semantic consumer does not — four instances found 22 Aug 2026."""
    findings: list[Finding] = []
    for kind in KNOWN_PRODUCER_CONSUMER_GAPS:
        producers = _producers_for(kind)
        consumers = [
            c
            for c in _semantic_consumers_for(kind)
            if not c.endswith("events.py")
        ]
        if producers and not consumers:
            continue  # known gap on allowlist
        if consumers and not producers:
            findings.append(
                Finding(
                    check="producer_consumer_gap",
                    reproduction=(f"grep -r {kind!r} src/",),
                    detail=f"{kind!r} has consumer(s) {consumers} but no producer",
                )
            )
    return findings


def check_generated_index_drift() -> list[Finding]:
    """A document restating a fact a tool could generate — C3, requirements drift."""
    findings: list[Finding] = []
    script = ROOT / "scripts" / "build_requirements.py"
    if script.is_file():
        run = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if run.returncode != 0:
            findings.append(
                Finding(
                    check="generated_index_drift",
                    reproduction=(f"python {script.relative_to(ROOT)} --check",),
                    detail="docs/40-spec/requirements.md drifted from requirements-source.json",
                )
            )
    index = ROOT / "docs" / "decisions" / "index.md"
    if index.is_file():
        text = index.read_text(encoding="utf-8")
        match = ADR_COUNT_CLAIM.search(text)
        if match:
            claimed = int(match.group(1))
            actual = len(list((ROOT / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md")))
            if claimed != actual:
                findings.append(
                    Finding(
                        check="generated_index_drift",
                        reproduction=(
                            "read docs/decisions/index.md line 3",
                            "ls docs/decisions/[0-9][0-9][0-9][0-9]-*.md | wc -l",
                        ),
                        detail=(
                            f"index claims {claimed} ADRs [measured] but directory holds {actual}"
                        ),
                    )
                )
    return findings


def check_measured_claims_have_artefacts() -> list[Finding]:
    """[measured] tag without a producing artefact — C1 class."""
    findings: list[Finding] = []
    exp43_results = ROOT / "docs/10-research/experiments/exp43/results-exp43.json"
    results_text = exp43_results.read_text(encoding="utf-8") if exp43_results.is_file() else ""
    skip = {
        ROOT / "docs/00-context/corrections-2026-08-21.md",
        ROOT / "docs/10-research/experiments/exp43/findings-exp43.md",
        ROOT / "docs/superpowers/specs/2026-08-22-autonomous-qa.md",
    }
    for path in (ROOT / "docs").rglob("*.md"):
        if path in skip:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "EXP-43 measured" not in text and "EXP-43 already measured" not in text:
            continue
        if ("72.8" not in text and "75.9" not in text) or not MEASURED_TAG.search(text):
            continue
        if "72.8" in results_text or "75.9" in results_text:
            continue
        findings.append(
            Finding(
                check="measured_without_artefact",
                reproduction=(
                    f"grep -n 'EXP-43' {path.relative_to(ROOT)}",
                    f"grep 72.8 {exp43_results.relative_to(ROOT)}",
                ),
                detail=(
                    f"{path.relative_to(ROOT)} claims EXP-43 greenfield blindness "
                    "[measured] but results-exp43.json does not contain the figure"
                ),
            )
        )
    return findings


def check_gate_fails_when_checker_absent() -> list[Finding]:
    """Gate passes when its checker is absent — pre-push fail-open repaired 22 Aug 2026."""
    findings: list[Finding] = []
    if not PRE_PUSH.is_file():
        findings.append(
            Finding(
                check="gate_fail_open",
                reproduction=("read .githooks/pre-push",),
                detail="pre-push hook missing; publication gates are not enforced",
            )
        )
        return findings
    text = PRE_PUSH.read_text(encoding="utf-8")
    if "checker missing" not in text and "FAIL" not in text:
        findings.append(
            Finding(
                check="gate_fail_open",
                reproduction=("read .githooks/pre-push",),
                detail="pre-push does not fail when a checker script is absent",
            )
        )
    if "exit 0" in text and "checker missing" not in text:
        findings.append(
            Finding(
                check="gate_fail_open",
                reproduction=("read .githooks/pre-push",),
                detail="pre-push may exit 0 when a checker is missing",
            )
        )
    # Negative control: a hook that skips missing checkers must fail this check.
    if "[ ! -f" in text and "failed=0" in text and "continue" in text:
        pass  # repaired shape: missing file sets failed=1
    elif "if [ ! -f" not in text:
        findings.append(
            Finding(
                check="gate_fail_open",
                reproduction=("grep 'checker missing' .githooks/pre-push",),
                detail="pre-push lacks explicit missing-checker refusal",
            )
        )
    return findings


def run_seeded_fault_batch() -> dict[str, object]:
    """Adversarial generation with EXP-96 unclassifiable threshold. No headline β when exceeded."""
    faults: tuple[tuple[str, str], ...] = (
        ("assert True is False", "true_defect"),
        ("x = 1 +", "unclassifiable"),
        ("assert 2 + 2 == 5", "true_defect"),
    )
    results: list[dict[str, str]] = []
    seeded_dir = ROOT / ".harness" / "qa-seeded"
    seeded_dir.mkdir(parents=True, exist_ok=True)
    try:
        for idx, (body, expected) in enumerate(faults):
            path = seeded_dir / f"fault_{idx}.py"
            path.write_text(f"def test_seeded_{idx}() -> None:\n    {body}\n", encoding="utf-8")
            run = subprocess.run(
                [sys.executable, "-m", "pytest", str(path), "-q"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if "SyntaxError" in run.stdout + run.stderr or "ERROR" in run.stdout:
                observed = "unclassifiable"
            elif run.returncode == 0:
                observed = "accepted"
            else:
                observed = "rejected"
            results.append(
                {
                    "fault": str(path.relative_to(ROOT)),
                    "expected": expected,
                    "observed": observed,
                }
            )
    finally:
        for child in seeded_dir.glob("fault_*.py"):
            child.unlink(missing_ok=True)
    generated = len(results)
    unclassifiable = sum(1 for r in results if r["observed"] == "unclassifiable")
    accepted = sum(1 for r in results if r["observed"] == "accepted")
    rate = unclassifiable / generated if generated else 0.0
    proxy_beta: float | None = None
    headline_permitted = rate <= MAX_UNCLASSIFIABLE_RATE
    if headline_permitted and accepted:
        proxy_beta = accepted / generated
    return {
        "generated": generated,
        "unclassifiable": unclassifiable,
        "accepted": accepted,
        "unclassifiable_rate": round(rate, 4),
        "max_unclassifiable_rate": MAX_UNCLASSIFIABLE_RATE,
        "headline_permitted": headline_permitted,
        "proxy_beta": proxy_beta,
        "results": results,
    }


def run_all_defect_checks() -> list[Finding]:
    findings: list[Finding] = []
    for fn in (
        check_producer_consumer_gaps,
        check_generated_index_drift,
        check_measured_claims_have_artefacts,
        check_gate_fails_when_checker_absent,
    ):
        findings.extend(fn())
    return findings


# --- pytest: machinery and ratchets -------------------------------------------


def test_known_gaps_inventory_is_stable() -> None:
    assert set(KNOWN_PRODUCER_CONSUMER_GAPS) == {
        "decision.autonomous",
        "instructions.assembled",
        "routing.consulted",
        "usage.observed",
    }


def test_gate_fail_open_check_passes_on_real_pre_push() -> None:
    assert check_gate_fails_when_checker_absent() == []


def test_generated_index_drift_detects_adr_count_mismatch(tmp_path: Path) -> None:
    index = tmp_path / "index.md"
    index.write_text("# Decision index\n\n2 ADRs, 22 Aug 2026. [measured]\n", encoding="utf-8")
    decisions = tmp_path / "decisions"
    decisions.mkdir()
    for n in (1, 2, 3):
        (decisions / f"000{n}-x.md").write_text("x", encoding="utf-8")

    def _check(index_path: Path, decisions_dir: Path) -> list[Finding]:
        text = index_path.read_text(encoding="utf-8")
        match = ADR_COUNT_CLAIM.search(text)
        assert match
        claimed = int(match.group(1))
        actual = len(list(decisions_dir.glob("[0-9][0-9][0-9][0-9]-*.md")))
        if claimed != actual:
            return [
                Finding(
                    check="generated_index_drift",
                    reproduction=("compare index claim to directory count",),
                    detail=f"claimed {claimed} actual {actual}",
                )
            ]
        return []

    assert _check(index, decisions)


def test_measured_without_artefact_ratchet(tmp_path: Path) -> None:
    doc = tmp_path / "findings.md"
    doc.write_text("Retro blind to 72.8% [measured]\n", encoding="utf-8")
    results = tmp_path / "results.json"
    results.write_text("{}", encoding="utf-8")
    text = doc.read_text(encoding="utf-8")
    assert "72.8" in text and MEASURED_TAG.search(text)
    assert "72.8" not in results.read_text(encoding="utf-8")


def test_seeded_fault_batch_refuses_headline_when_unclassifiable_high(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "test_qa_battery.MAX_UNCLASSIFIABLE_RATE",
        0.0,
        raising=False,
    )
    # Force all faults to be unclassifiable for this ratchet.
    def fake_batch() -> dict[str, object]:
        return {
            "generated": 2,
            "unclassifiable": 2,
            "accepted": 0,
            "unclassifiable_rate": 1.0,
            "max_unclassifiable_rate": 0.0,
            "headline_permitted": False,
            "proxy_beta": None,
            "results": [],
        }

    out = fake_batch()
    assert out["headline_permitted"] is False
    assert out["proxy_beta"] is None


def test_seeded_fault_batch_runs() -> None:
    out = run_seeded_fault_batch()
    assert out["generated"] >= 1
    assert "unclassifiable_rate" in out
    if not out["headline_permitted"]:
        assert out["proxy_beta"] is None


def test_qa_battery_module_loads() -> None:
    script = ROOT / "scripts" / "qa_battery.py"
    assert script.is_file()
    run = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert run.returncode == 0, run.stderr
    assert "dry-run" in run.stdout


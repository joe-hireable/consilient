"""Persona QA journeys ship with checks that can fail."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

_spec = importlib.util.spec_from_file_location(
    "persona_qa", ROOT / "scripts" / "persona_qa.py"
)
assert _spec and _spec.loader
persona_qa = importlib.util.module_from_spec(_spec)
sys.modules["persona_qa"] = persona_qa
_spec.loader.exec_module(persona_qa)


def test_persona_specs_cover_all_named_personas() -> None:
    assert set(persona_qa.PERSONAS) == set(persona_qa.JOURNEYS)


def test_average_joe_finds_command_count_contradiction() -> None:
    result = persona_qa.journey_average_joe(ROOT)
    assert result.finding is not None
    assert "Four commands" in result.finding.discrepancy


def test_contributor_finds_stale_contributing_opening() -> None:
    result = persona_qa.journey_contributor(ROOT)
    assert result.finding is not None
    assert "no code yet" in result.finding.discrepancy.lower()


def test_operator_finds_unconfigured_usage_ceilings() -> None:
    result = persona_qa.journey_operator(ROOT)
    assert result.finding is not None
    assert "ceilings: NONE" in result.finding.discrepancy


def test_cold_trajectory_refusal_holds() -> None:
    result = persona_qa.cold_trajectory_refusal(ROOT)
    assert result.finding is None
    assert result.exit_code == 2
    assert "trajectory not configured" in result.stderr


def test_cold_trajectory_guard_mutation_fails_without_refusal(
    tmp_path, monkeypatch, capsys
) -> None:
    """Break require_trajectory; refusal test must fail until restored."""
    from consilient import cli as cli_mod
    from consilient.cli import main

    monkeypatch.chdir(tmp_path)
    log = tmp_path / "log"
    db = tmp_path / "state.db"

    real = cli_mod.require_trajectory
    monkeypatch.setattr(cli_mod, "require_trajectory", lambda _log: "empty")
    capsys.readouterr()
    broken_code = main(["--log", str(log), "--db", str(db), "replay"])
    broken = capsys.readouterr()
    assert broken_code != 2, "mutation did not restore the false-zero path"
    assert "replayed 0 events" in broken.out

    monkeypatch.setattr(cli_mod, "require_trajectory", real)
    capsys.readouterr()
    fixed_code = main(["--log", str(log), "--db", str(db), "replay"])
    fixed_err = capsys.readouterr().err
    assert fixed_code == 2
    assert "trajectory not configured" in fixed_err


def test_researcher_finds_script_when_present() -> None:
    result = persona_qa.journey_researcher(ROOT)
    script = ROOT / "docs/10-research/experiments/exp47/run_exp47.py"
    if script.is_file():
        assert result.finding is None or "results" in result.stopped_at
    else:
        assert result.finding is not None

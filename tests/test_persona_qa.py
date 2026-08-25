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


def _present_as_mutated(
    monkeypatch: pytest.MonkeyPatch, path: Path, old: str, new: str, count: int = -1
) -> None:
    """Make `path` read as mutated WITHOUT writing to the tracked tree.

    These ratchets used to write the broken text to the real file and restore it in a
    `finally`. A `finally` does not run when the process is killed, and on 24 August 2026
    one of them was: `docs/00-context/getting-started.md` was found in the working tree
    still carrying this test's own mutation string, `limits-removed.example.json`. That
    turned the operator ratchet red and, worse, pointed any operator following
    getting-started at an example file that does not exist. The suite runs under timeouts
    and gets killed; a guard that corrupts the repository when it dies is a worse defect
    than the one it guards, so the mutation now lives in memory and the file is never
    written.
    """
    original = path.read_text(encoding="utf-8")
    broken = original.replace(old, new) if count < 0 else original.replace(old, new, count)
    assert broken != original, f"mutation {old!r} -> {new!r} changed nothing in {path.name}"
    real_read_text = Path.read_text

    def fake_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if self == path:
            return broken
        return real_read_text(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "read_text", fake_read_text)



def _skip_if_trajectory_unreadable(result) -> None:
    """A journey that never reached its check has not disproved the check.

    `journey_operator` shells out to `consil usage` and `consil doctor`. Both read the live
    trajectory, and under concurrent dispatch a writer denies the reader -- doctor then exits
    non-zero and the journey stops at "usage and doctor ran", before the ceilings comparison
    this ratchet is about. That is infrastructure, not a verdict on the documentation.
    """
    if getattr(result, "exit_code", 0) not in (0, 1) or "could not be read" in (
        getattr(result, "stderr", "") or ""
    ):
        pytest.skip(
            "consil could not read the live trajectory, so the journey stopped before its "
            f"check: stopped_at={getattr(result, 'stopped_at', '?')!r}"
        )


def test_persona_specs_cover_all_named_personas() -> None:
    assert set(persona_qa.PERSONAS) == set(persona_qa.JOURNEYS)


def test_average_joe_has_no_command_count_contradiction() -> None:
    result = persona_qa.journey_average_joe(ROOT)
    assert result.finding is None, result.finding.discrepancy if result.finding else ""


def test_contributor_finds_no_stale_contributing_opening() -> None:
    result = persona_qa.journey_contributor(ROOT)
    assert result.finding is None, result.finding.discrepancy if result.finding else ""


def test_operator_documents_usage_ceilings() -> None:
    result = persona_qa.journey_operator(ROOT)
    assert result.finding is None, result.finding.discrepancy if result.finding else ""


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


def test_average_joe_ratchet_fails_when_four_commands_returns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _present_as_mutated(
        monkeypatch,
        ROOT / "docs/00-context/getting-started.md",
        "Six commands",
        "Four commands",
        count=1,
    )
    result = persona_qa.journey_average_joe(ROOT)
    assert result.finding is not None


def test_contributor_ratchet_fails_when_stale_opening_returns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _present_as_mutated(
        monkeypatch,
        ROOT / "CONTRIBUTING.md",
        "Stage 3 is active",
        "pre-brainstorm and has no code yet",
        count=1,
    )
    result = persona_qa.journey_contributor(ROOT)
    assert result.finding is not None


def test_operator_ratchet_fails_when_ceilings_undocumented(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _present_as_mutated(
        monkeypatch,
        ROOT / "docs/00-context/getting-started.md",
        "limits.example.json",
        "limits-removed.example.json",
    )
    result = persona_qa.journey_operator(ROOT)
    _skip_if_trajectory_unreadable(result)
    assert result.finding is not None
    assert "undocumented" in result.stopped_at

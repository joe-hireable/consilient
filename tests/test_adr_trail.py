"""R03: the ADR trail checker — supersede, never silently edit."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "check_adr_trail.py"
SPEC = importlib.util.spec_from_file_location("check_adr_trail", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def test_silent_edit_of_settled_adr_is_a_violation() -> None:
    assert CHECKER.classify_edit("ACCEPTED", ["new body"], ["old body"]) == "violation"
    assert CHECKER.classify_edit("SUPERSEDED by 0002", ["x"], ["y"]) == "violation"


def test_marker_cannot_launder_a_settled_adr_removal() -> None:
    assert (
        CHECKER.classify_edit("ACCEPTED", ["Superseded by 0067"], ["old body"])
        == "violation"
    )
    assert (
        CHECKER.classify_edit("ACCEPTED", ["Update 21 Aug 2026: corrected"], ["old"])
        == "violation"
    )


def test_unsettled_adr_and_pure_additions_are_fine() -> None:
    assert CHECKER.classify_edit("PROPOSED", ["anything"], ["old body"]) == "ok"
    assert CHECKER.classify_edit("ACCEPTED", ["reworded"], []) == "ok"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )


def _write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "history"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "ADR Trail Tests")
    monkeypatch.setattr(CHECKER, "ROOT", repo)
    return repo


def _pin_settled_records(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pin = _git(repo, "rev-parse", "HEAD").stdout.strip()
    monkeypatch.setattr(CHECKER, "HISTORY_PIN", pin)
    monkeypatch.setattr(CHECKER, "SETTLED_RECORD_PIN", pin, raising=False)


def test_settled_experiment_outcomes_are_append_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/10-research/experiment-register.md"
    _write(repo, rel, "### EXP-7 — test `DONE`\n\nsettled text\n")
    _commit(repo, "record outcome")
    _pin_settled_records(repo, monkeypatch)

    _write(repo, rel, "### EXP-7 — test `DONE`\n\nrewritten text\n")
    sha = _commit(repo, "rewrite outcome")

    reported, failed = CHECKER.check_history()

    assert reported == []
    assert any(sha in message and rel in message and "EXP-7#1" in message for message in failed)


def test_current_non_done_outcome_is_append_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/10-research/experiment-register.md"
    _write(repo, rel, "### EXP-8 — test `INSUFFICIENT-EVIDENCE`\n\nsettled text\n")
    _commit(repo, "record outcome")
    _pin_settled_records(repo, monkeypatch)

    _write(repo, rel, "### EXP-8 — test `INSUFFICIENT-EVIDENCE`\n\nrewritten text\n")
    sha = _commit(repo, "rewrite outcome")

    _, failed = CHECKER.check_history()

    assert any(sha in message and "EXP-8#1" in message for message in failed)


def test_ready_experiment_is_editable_until_its_done_entry_is_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/10-research/experiment-register.md"
    _write(repo, rel, "### EXP-9 — test `READY`\n\nfirst draft\n")
    _commit(repo, "add ready experiment")
    _pin_settled_records(repo, monkeypatch)

    _write(repo, rel, "### EXP-9 — test `READY`\n\nrevised draft\n")
    _commit(repo, "edit ready experiment")
    assert CHECKER.check_history()[1] == []

    _write(repo, rel, "### EXP-9 — test `DONE`\n\nrevised draft\n")
    _commit(repo, "settle experiment")
    assert CHECKER.check_history()[1] == []

    _write(repo, rel, "### EXP-9 — test `DONE`\n\nrewritten result\n")
    sha = _commit(repo, "rewrite settled experiment")
    assert any(sha in message and "EXP-9#1" in message for message in CHECKER.check_history()[1])


@pytest.mark.parametrize(
    ("changed", "message"),
    [
        ("### EXP-10 — test `DONE`\n\nsettled text \n", "whitespace mutation"),
        ("### EXP-10 — test `DONE`\n\ninserted\nsettled text\n", "insertion"),
        ("### EXP-10 — test `DONE`\n", "line deletion"),
    ],
)
def test_settled_experiment_rejects_non_append_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed: str, message: str
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/10-research/experiment-register.md"
    _write(repo, rel, "### EXP-10 — test `DONE`\n\nsettled text\n")
    _commit(repo, "record outcome")
    _pin_settled_records(repo, monkeypatch)

    _write(repo, rel, changed)
    sha = _commit(repo, message)

    assert any(sha in item and "EXP-10#1" in item for item in CHECKER.check_history()[1])


def test_settled_experiment_allows_an_appended_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/10-research/experiment-register.md"
    settled = "### EXP-11 — test `DONE`\n\nsettled text\n"
    _write(repo, rel, settled)
    _commit(repo, "record outcome")
    _pin_settled_records(repo, monkeypatch)

    _write(repo, rel, settled + "\n### EXP-12 — follow-up `READY`\n\nnew text\n")
    _commit(repo, "append section")

    assert CHECKER.check_history()[1] == []


@pytest.mark.parametrize("rename", [False, True])
def test_settled_experiment_rejects_deletion_or_rename_away(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rename: bool
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/10-research/experiment-register.md"
    _write(repo, rel, "### EXP-13 — test `DONE`\n\nsettled text\n")
    _commit(repo, "record outcome")
    _pin_settled_records(repo, monkeypatch)

    source = repo / rel
    if rename:
        source.rename(repo / "docs/10-research/renamed-register.md")
        message = "rename register"
    else:
        source.unlink()
        message = "delete register"
    sha = _commit(repo, message)

    assert any(sha in item and rel in item and "EXP-13#1" in item for item in CHECKER.check_history()[1])


def test_correction_records_are_exactly_append_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/00-context/corrections-2026-08-23.md"
    _write(repo, rel, "first correction\nsecond correction\n")
    _commit(repo, "record corrections")
    _pin_settled_records(repo, monkeypatch)

    _write(repo, rel, "rewritten correction\nsecond correction\n")
    sha = _commit(repo, "rewrite correction")

    assert any(
        sha in item and rel in item and "correction line 1" in item
        for item in CHECKER.check_history()[1]
    )


def test_correction_record_allows_eof_append(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/00-context/corrections-2026-08-23.md"
    parent = "first correction\nsecond correction\n"
    _write(repo, rel, parent)
    _commit(repo, "record corrections")
    _pin_settled_records(repo, monkeypatch)

    _write(repo, rel, parent + "third correction\n")
    _commit(repo, "append correction")

    assert CHECKER.check_history()[1] == []


def test_duplicate_experiment_ids_keep_their_ordinal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/10-research/experiment-register.md"
    _write(
        repo,
        rel,
        "### EXP-14 — first `DONE`\n\nfirst result\n\n"
        "### EXP-14 — second `READY`\n\nsecond draft\n",
    )
    _commit(repo, "record duplicate ids")
    _pin_settled_records(repo, monkeypatch)

    _write(
        repo,
        rel,
        "### EXP-14 — first `DONE`\n\nrewritten result\n\n"
        "### EXP-14 — second `READY`\n\nrevised draft\n",
    )
    sha = _commit(repo, "change duplicate entries")

    assert any(sha in item and "EXP-14#1" in item for item in CHECKER.check_history()[1])


def test_prepin_settled_record_violation_is_reported_not_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/10-research/experiment-register.md"
    _write(repo, rel, "### EXP-15 — test `DONE`\n\nsettled text\n")
    _commit(repo, "record outcome")
    _write(repo, rel, "### EXP-15 — test `DONE`\n\nrewritten text\n")
    sha = _commit(repo, "prepin rewrite")
    _pin_settled_records(repo, monkeypatch)

    reported, failed = CHECKER.check_history()

    assert any(sha in item and "EXP-15#1" in item for item in reported)
    assert failed == []


def test_marker_cannot_launder_removed_settled_adr_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/decisions/0001-test.md"
    _write(repo, rel, "# Test\n\n**Status:** ACCEPTED\n\nsettled body\n")
    _commit(repo, "accept adr")
    _pin_settled_records(repo, monkeypatch)

    _write(repo, rel, "# Test\n\n**Status:** ACCEPTED\n\nUpdate: corrected\n")
    sha = _commit(repo, "launder removal")

    assert any(sha[:9] in item and rel in item for item in CHECKER.check_history()[1])


@pytest.mark.parametrize("rename", [False, True])
def test_settled_adr_rejects_deletion_or_rename_away(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rename: bool
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    rel = "docs/decisions/0002-test.md"
    _write(repo, rel, "# Test\n\n**Status:** ACCEPTED\n\nsettled body\n")
    _commit(repo, "accept adr")
    _pin_settled_records(repo, monkeypatch)

    source = repo / rel
    if rename:
        source.rename(repo / "docs/decisions/renamed-test.md")
        message = "rename adr"
    else:
        source.unlink()
        message = "delete adr"
    sha = _commit(repo, message)

    assert any(sha[:9] in item and rel in item for item in CHECKER.check_history()[1])


def test_trail_integrity_runs_on_the_real_tree() -> None:
    """Leg 1 must execute; violations are reported in the message, not hidden."""
    problems = CHECKER.check_trail_integrity()
    assert isinstance(problems, list)
    if problems:
        pytest.fail("ADR trail integrity violations:\n" + "\n".join(problems))


def test_history_leg_runs_and_reports_without_failing_prepin() -> None:
    reported, failed = CHECKER.check_history()
    assert failed == [], "post-pin silent edits of settled ADRs:\n" + "\n".join(failed)
    assert isinstance(reported, list)


def test_self_test_passes() -> None:
    run = subprocess.run(
        [sys.executable, str(SCRIPT), "--self-test"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert run.returncode == 0, run.stderr

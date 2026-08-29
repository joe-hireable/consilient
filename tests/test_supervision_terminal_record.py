"""BU-4 / N04: exit zero is not success, and the terminal record is the field that says
so.

F-02 is a missing field. Seven tracked files sat modified with no dispatcher running,
because the streams that wrote them completed and exited without committing. [measured,
F-02] `classify_artefact` may still say ok — the child produced an artefact and exited 0
— so the terminal record is what carries the rest: the uncommitted tracked paths by
name, the outcome as incomplete, and what became of the claim. Untracked noise is not
counted; a stranded tracked file is.

A clean tree must come out complete, or dirty would be unfalsifiable, and these two
cases are kept in one module for that reason.

The wrapper writes `terminal` after the child exits, never before and never by goodwill.
A record that already exists while `run_process` is still running is an ending we
invented; a record that never appears leaves F-02 exactly where it was.

Where the tree cannot be inspected at all — no git, no repo, an unreadable tree — the
outcome is incomplete rather than an empty path list dressed as complete. F-09 again: a
checker that cannot distinguish a false condition from a failed check fails closed, and
`inspected` records which of the two happened. These checks skip rather than lie when
git is absent."""

from family_source import seam

import json
import shutil
import subprocess
from pathlib import Path
import pytest
from consilient.harness import harness_by_id
from supervision_helpers import (
    _script,
)


def _git(repo: Path, *args: str) -> None:
    done = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert done.returncode == 0, done.stderr


def _repo_with_tracked_file(root: Path, name: str = "worker") -> Path:
    repo = root / name
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_dirty_worker_terminal_records_uncommitted_paths(tmp_path, monkeypatch):
    """BU-4 / N04. F-02 is a missing field: worker exits dirty, terminal names
    the uncommitted tracked paths and marks the outcome incomplete.

    Exit zero is not success. Seven tracked files sat modified with no
    dispatcher running because the streams that wrote them completed and
    exited without committing. [measured, F-02]
    """
    script = _script()
    repo = _repo_with_tracked_file(tmp_path)
    (repo / "tracked.txt").write_text("stranded\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("noise\n", encoding="utf-8")

    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_a, **_k: ["agent"])
    monkeypatch.setattr(seam("dispatch_launch"), "run_process", lambda *_a, **_k: (0, False, 0.1, None))
    harness = harness_by_id("codex")
    assert harness is not None
    result = script.run_harness(
        harness,
        task="pong",
        cwd=repo,
        run_dir=tmp_path / "n04-dirty",
        timeout_s=5,
        model=None,
        run_id="n04-dirty",
        expected_artefact="stdout.txt",
        unit="N04",
        claim_run_id="n04-dirty",
    )

    # classify_artefact may still say ok: the child produced an artefact and
    # exited 0. The terminal record is the field F-02 was missing.
    record = json.loads((tmp_path / "n04-dirty.json").read_text(encoding="utf-8"))
    terminal = record["terminal"]
    assert terminal["exit_code"] == 0
    assert terminal["uncommitted_tracked_paths"] == ["tracked.txt"]
    assert terminal["outcome"] == "incomplete"
    assert terminal["claim_disposition"] == "held"
    assert result.exit_code == 0


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_clean_worker_terminal_is_complete(tmp_path, monkeypatch):
    """A clean tree is a complete outcome, or dirty would be unfalsifiable."""
    script = _script()
    repo = _repo_with_tracked_file(tmp_path)

    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_a, **_k: ["agent"])
    monkeypatch.setattr(seam("dispatch_launch"), "run_process", lambda *_a, **_k: (0, False, 0.1, None))
    harness = harness_by_id("codex")
    assert harness is not None
    script.run_harness(
        harness,
        task="pong",
        cwd=repo,
        run_dir=tmp_path / "n04-clean",
        timeout_s=5,
        model=None,
        run_id="n04-clean",
        expected_artefact="stdout.txt",
        unit="N04",
    )

    terminal = json.loads((tmp_path / "n04-clean.json").read_text(encoding="utf-8"))[
        "terminal"
    ]
    assert terminal["uncommitted_tracked_paths"] == []
    assert terminal["outcome"] == "complete"
    assert terminal["claim_disposition"] == "none"
    assert terminal["exit_code"] == 0


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_terminal_is_written_by_the_wrapper_after_exit(tmp_path, monkeypatch):
    """The wrapper writes `terminal` after the child exits, never by goodwill.

    If the record appears before `run_process` returns, we are inventing an
    ending. If it never appears, F-02 is still a missing field.
    """
    script = _script()
    repo = _repo_with_tracked_file(tmp_path)
    (repo / "tracked.txt").write_text("still stranded\n", encoding="utf-8")
    run_id = "n04-after"
    record_path = tmp_path / f"{run_id}.json"
    seen: dict[str, object] = {}

    def fake_run_process(*_a, **_k):
        payload = (
            json.loads(record_path.read_text(encoding="utf-8"))
            if record_path.exists()
            else {}
        )
        seen["terminal_during"] = "terminal" in payload
        return 0, False, 0.1, None

    monkeypatch.setattr(seam("dispatch_invocation"), "build_command", lambda *_a, **_k: ["agent"])
    monkeypatch.setattr(seam("dispatch_launch"), "run_process", fake_run_process)
    harness = harness_by_id("codex")
    assert harness is not None
    script.run_harness(
        harness,
        task="pong",
        cwd=repo,
        run_dir=tmp_path / run_id,
        timeout_s=5,
        model=None,
        run_id=run_id,
        expected_artefact="stdout.txt",
        unit="N04",
    )

    assert seen.get("terminal_during") is False
    terminal = json.loads(record_path.read_text(encoding="utf-8"))["terminal"]
    assert terminal["uncommitted_tracked_paths"] == ["tracked.txt"]
    assert terminal["outcome"] == "incomplete"


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_inspection_failure_is_incomplete_not_clean(tmp_path):
    """F-09: a checker that cannot inspect is not a pass. No git, no repo,
    unreadable tree — the outcome is incomplete, not an empty path list
    dressed as complete.
    """
    script = _script()
    missing = tmp_path / "not-a-repo"
    missing.mkdir()
    path = script.write_terminal(
        tmp_path,
        run_id="n04-unknown",
        exit_code=0,
        cwd=missing,
        claim_disposition="none",
    )
    terminal = json.loads(path.read_text(encoding="utf-8"))["terminal"]
    assert terminal["outcome"] == "incomplete"
    assert terminal["uncommitted_tracked_paths"] == []
    assert terminal["inspected"] is False

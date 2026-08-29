"""Deciding that a unit's work is already in HEAD — the driver's own false-accept
surface.

This is the classifier that retires a unit without review, so every mistake it makes is
a false accept, which is the quantity this project exists to measure.

MEASURED 24 August 2026: the already-landed detector used to grep commit *subjects*.
Over 646 commits this repository reused 14 subjects, and 9 of the top 12 reused subjects
carry different patch content. A subject hit retired the unit, and that is how
`harness.py` acquired a duplicate 313-line block. `--grep` must stay gone. The
replacement compares content, and it must be indentation-sensitive: `.strip()` on both
sides discarded leading whitespace too, so a commit that only re-indents an existing
block — moving it into a loop or a conditional, changing what it means — read as already
present [measured, 26 August 2026].

MEASURED 25 August 2026: both halves of `_cherry_and_diff_match` pass trivially when the
worktree head *is* HEAD — `git cherry` prints nothing and `git diff --quiet` exits 0 —
so the driver reported BN's work as present in HEAD while `rebase_mergeable_worktrees`
and `SUBSYSTEM_JACCARD_THRESHOLD` were both absent from it. The unit was then dropped
from `conflicts`, so the driver stopped trying to merge the work it had actually done.
`_refresh_worktree` resets clean unit worktrees to HEAD every tick, so this is the
ordinary state of a conflicted unit rather than an edge case. Emptiness is not evidence
of completion.

The rest are BL's done criteria. No uid may sit in both `conflicts` and `force_done`,
which K01 did live. A cherry-pick whose result fails the gate is undone and the unit
escalates, leaving HEAD exactly where it was. And the escalation banner grows when the
classifier retires rather than quietly shrinking, so a retirement is visible as a
retirement. These run against a real git repository built in a `tmp_path` and isolated
from this checkout by `_isolate_driver`, because a content classifier tested only
against a fake `sh` is testing the fake."""

import os
import subprocess
from pathlib import Path
from typing import Any, cast
import pytest
from build_driver_helpers import (
    DRIVER,
    _load_driver,
)


def test_a_worktree_sitting_at_head_is_not_already_landed(monkeypatch) -> None:
    """Emptiness is not evidence of completion.

    MEASURED 25 August 2026: both halves of `_cherry_and_diff_match` pass trivially when the
    worktree head IS HEAD -- `git cherry` prints nothing and `git diff --quiet` exits 0 -- so
    the driver reported BN's work as present in HEAD while `rebase_mergeable_worktrees` and
    `SUBSYSTEM_JACCARD_THRESHOLD` were both absent from it. The unit was then dropped from
    `conflicts`, so the driver stopped trying to merge the work it had actually done.

    `_refresh_worktree` resets clean unit worktrees to HEAD every tick, so this is the ordinary
    state of a conflicted unit, not an edge case. A gate accepting an artefact that is not there
    is a false accept, which is the quantity this project exists to measure.
    """
    driver = _load_driver()
    head = "a" * 40

    def fake_sh(args: list[str], **_kw):
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""

        result = _R()
        if args[:2] == ["git", "rev-parse"]:
            result.stdout = head + "\n"
        return result

    monkeypatch.setattr(driver, "sh", fake_sh)
    assert driver._cherry_and_diff_match(head, [".harness/build_driver.py"]) is False, (
        "a worktree at exactly HEAD has done nothing and must not read as landed"
    )
    # A genuinely different head still reaches the real checks (which the stub passes).
    assert driver._cherry_and_diff_match("b" * 40, [".harness/build_driver.py"]) is True


# --- BL: classify conflicts by content, clear them on retirement, gate merges --
#
# The already-landed detector used to grep commit SUBJECTS. Over 646 commits this
# repository reused 14 subjects; 9 of the top 12 reused subjects carry different
# patch content [measured, 24 August 2026]. A subject hit retired the unit. That
# is a false-accept in the driver's own classifier, and it is how harness.py
# acquired a duplicate 313-line block.
#
# These four tests are the unit's done criteria (A1, A2, A5-driver-half, F).


_GIT_ENV = {
    key: value
    for key, value in os.environ.items()
    if key not in {"GIT_DIR", "GIT_WORK_TREE"}
}


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_GIT_ENV,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init")
    _git(path, "config", "user.email", "bl@test")
    _git(path, "config", "user.name", "BL")


def _commit_file(repo: Path, rel: str, body: str, subject: str) -> str:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    _git(repo, "add", rel)
    _git(repo, "commit", "-m", subject)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _isolate_driver(
    driver: object, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(driver, "ROOT", repo)
    monkeypatch.setattr(driver, "WORKTREES", repo / ".harness" / "unit-worktrees")
    monkeypatch.setattr(driver, "STATE", repo / ".harness" / "driver-state.json")

    def isolated_sh(args: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=str(repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=_GIT_ENV,
            **kw,
        )

    monkeypatch.setattr(driver, "sh", isolated_sh)


def test_classifier_does_not_retire_on_subject_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A1: identical subject, different content — the second stays escalated."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "mod.py", "base = 0\n", "init")
    default = _git(repo, "branch", "--show-current").stdout.strip()
    first_lines = "\n".join(f"FIRST_{i} = {i}" for i in range(25)) + "\n"
    second_lines = "\n".join(f"SECOND_{i} = {i}" for i in range(25)) + "\n"
    _git(repo, "checkout", "-b", "first")
    _commit_file(repo, "mod.py", first_lines, "feat: shared subject")
    _git(repo, "checkout", default)
    _git(repo, "checkout", "-b", "second")
    second_sha = _commit_file(repo, "mod.py", second_lines, "feat: shared subject")
    _git(repo, "checkout", default)
    _git(repo, "merge", "--no-ff", "first", "-m", "land first")

    driver = _load_driver()
    _isolate_driver(driver, repo, monkeypatch)
    state: dict[str, object] = {
        "conflicts": {
            "U2": f"CONFLICT cherry-picking {second_sha[:9]} for U2 (0 applied); needs resolution"
        },
        "force_done": [],
        "built": [],
        "done": [],
    }
    retired = driver.retest_conflicts(state)
    assert retired == 0
    assert "U2" in cast("dict[str, str]", state["conflicts"])


def test_conflict_cleared_on_retire() -> None:
    """A2: no uid may sit in both conflicts and force_done — that was K01 live."""
    driver = _load_driver()
    state: dict[str, object] = {
        "conflicts": {"K01": "CONFLICT cherry-picking deadbeef for K01"},
        "force_done": ["K01", "T01"],
        "built": [],
        "done": [],
    }
    driver.clear_retired_conflicts(state)
    overlap = set(cast("dict[str, str]", state["conflicts"])) & set(
        cast("list[str]", state["force_done"])
    )
    assert overlap == set(), overlap


def test_failed_gate_reverts_cherry_pick(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cherry-pick whose result fails the gate is undone and the unit escalates."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    pre = _commit_file(repo, "ok.py", "VALUE = 1\n", "init")
    default = _git(repo, "branch", "--show-current").stdout.strip()
    _git(repo, "checkout", "-b", "unit")
    _commit_file(repo, "ok.py", "VALUE = 2\n", "feat: change value")
    _git(repo, "checkout", default)
    worktree = repo / ".harness" / "unit-worktrees" / "U1"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "add", str(worktree), "unit")

    driver = _load_driver()
    _isolate_driver(driver, repo, monkeypatch)
    monkeypatch.setattr(
        driver,
        "gate_merged_tree",
        lambda _touched, _baseline: "ruff: simulated gate failure",
    )

    msg = driver.merge_unit_worktree("U1")
    assert msg.startswith("CONFLICT"), msg
    assert "gate" in msg.lower()
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == pre


def test_classifier_does_not_grep_subjects() -> None:
    """The false-accept path was `git log --grep <subject>`. It must stay gone."""
    source = DRIVER.read_text(encoding="utf-8")
    assert "--grep" not in source
    assert "--merge-base=" in source
    assert "retired without review" in source
    assert "--config-file" in source and "mypy.ini" in source
    gate = source.split("def gate_merged_tree", 1)[1].split("\ndef ", 1)[0]
    assert "--config-file" in gate and "mypy.ini" in gate
    assert "--strict" not in gate.replace("never bare `--strict`", "")


def test_content_landed_is_indentation_sensitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MEASURED 26 August 2026: `.strip()` on both sides discarded leading whitespace too, so
    a commit that only re-indents an existing block (moves it into a loop or a conditional,
    changing what it means) read as "already present". 25 unindented lines on HEAD, the same
    25 lines each indented by 4 spaces in the unit's commit, must NOT be classified as landed.
    """
    repo = tmp_path / "repo"
    _init_repo(repo)
    driver = _load_driver()
    _isolate_driver(driver, repo, monkeypatch)

    flat_lines = "\n".join(f"LINE_{i} = {i}" for i in range(25)) + "\n"
    indented_lines = "\n".join(f"    LINE_{i} = {i}" for i in range(25)) + "\n"
    _commit_file(repo, "mod.py", flat_lines, "feat: flat lines land on HEAD")
    default = _git(repo, "branch", "--show-current").stdout.strip()
    _git(repo, "checkout", "-b", "reindented")
    sha = _commit_file(repo, "mod.py", indented_lines, "feat: same lines, now indented")
    _git(repo, "checkout", default)

    assert driver._content_landed(sha) is False, (
        "re-indented lines are not the same code and must not read as already landed"
    )


def test_escalation_banner_counts_retirements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """F: the banner grows when the classifier retires, it does not shrink."""
    driver = _load_driver()
    units = {f"E{i}": {"title": "held", "claims": []} for i in range(5)}
    units["T02"] = {"title": "landed", "claims": []}
    units["K01"] = {"title": "landed", "claims": []}
    remaining = {
        f"E{i}": f"CONFLICT cherry-picking {'abcdabcd'[:7]}{i} for E{i}"
        for i in range(5)
    }
    state: dict[str, object] = {
        "conflicts": {
            **remaining,
            "T02": "CONFLICT cherry-picking deadbee1 for T02",
            "K01": "CONFLICT cherry-picking deadbee2 for K01",
        },
        "force_done": [],
        "built": [],
        "done": [],
        "in_flight": {},
        "attempts": {},
    }
    monkeypatch.setattr(
        driver, "load", lambda path, _default: units if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "committed", lambda _uid, _unit: False)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: None)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(driver, "crashed_dispatches", lambda _state: [])
    monkeypatch.setattr(driver, "save_state", lambda _state: None)
    monkeypatch.setattr(driver, "live_dispatchers", lambda _state: 1)
    monkeypatch.setattr(driver, "publish_if_ready", lambda _state, _green: "")
    monkeypatch.setattr(driver, "ready", lambda *_a, **_k: False)
    monkeypatch.setattr(driver.subprocess, "Popen", lambda *_a, **_k: None)
    monkeypatch.setattr(driver, "rebase_mergeable_worktrees", lambda *_a, **_k: None)
    # Isolates this test from whatever real unit worktrees the live driver has actually
    # created on disk in this checkout -- without this, main()'s built-unmerged scan
    # (WORKTREES / uid).exists() sees real T02/K01 worktrees and calls the real `sh()`,
    # which crashes because `subprocess.Popen` above is mocked to return None.
    monkeypatch.setattr(driver, "WORKTREES", tmp_path / "unit-worktrees")

    def fake_retest(current: dict[str, object]) -> int:
        for uid in ("T02", "K01"):
            cast("dict[str, str]", current.get("conflicts", {})).pop(uid, None)
            built = cast("list[str]", current.setdefault("built", []))
            if uid not in built:
                built.append(uid)
        return 2

    monkeypatch.setattr(driver, "retest_conflicts", fake_retest)
    monkeypatch.setattr(driver, "clear_retired_conflicts", lambda _state: None)
    monkeypatch.setattr(
        driver,
        "merge_unit_worktree",
        lambda uid: current_conflict(uid),
    )

    def current_conflict(uid: str) -> str:
        if uid in ("T02", "K01"):
            return "no worktree"
        return cast("dict[str, str]", state["conflicts"]).get(uid, "CONFLICT leftover")

    assert driver.main() == 0
    out = capsys.readouterr().out
    assert "5 escalated, 2 retired without review" in out

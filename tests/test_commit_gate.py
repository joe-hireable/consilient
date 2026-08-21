"""Tests for the commit-attribution gate: policy, execution, and wiring.

The invariants under test are the ones the measured defect named:

- a commit staging a path claimed by another live run is refused (the sweep);
- while any claim is live, a commit must name its committer, or the checks
  cannot tell the claim-holder from a bystander;
- a run that claimed paths at dispatch cannot commit outside them;
- a run that claimed no paths must enumerate what it commits (17 of 18 claims
  on 21 August 2026 declared none, so without this leg the gate is nearly dead);
- a dead agent's claim releases itself by the clock, so the gate admits again
  with no lock file to go stale;
- claims recorded against a different worktree share no index with this one
  and must not obstruct it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from consilient import coordination
from consilient.commit_gate import (
    PATHS_ENV,
    RUN_ID_ENV,
    Admission,
    Refusal,
    check_commit,
    relevant_claims,
)
from consilient.events import read_all

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "commit_gate.py"
HOOK = ROOT / ".githooks" / "pre-commit"

T0 = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)


def _live(log: Path, *, now: datetime) -> tuple[coordination.Claim, ...]:
    events, rejected = read_all(log)
    assert not rejected
    return coordination.live_claims(events, now=now)


def _claim(
    log: Path,
    run_id: str,
    paths: list[str],
    cwd: Path,
    *,
    now: datetime = T0,
    timeout_s: int = 600,
) -> None:
    coordination.open_claim(
        log, run_id=run_id, paths=paths, cwd=cwd, timeout_s=timeout_s, now=now
    )


# --- policy: admission -------------------------------------------------------


def test_no_live_claims_admits_without_identity(tmp_path):
    decision = check_commit(
        staged=["src/x.py"], live=(), worktree=tmp_path, run_id=None, declared=None
    )
    assert isinstance(decision, Admission)
    assert decision.committer is None


def test_an_empty_staged_set_is_admitted_even_while_claims_are_live(tmp_path):
    log = tmp_path / "log"
    _claim(log, "run-holder", ["docs"], tmp_path)
    decision = check_commit(
        staged=[],
        live=_live(log, now=T0),
        worktree=tmp_path,
        run_id=None,
        declared=None,
    )
    assert isinstance(decision, Admission)


def test_a_claim_held_against_another_worktree_does_not_obstruct_this_one(tmp_path):
    """A linked worktree has its own index; its claims cannot be swept by a
    commit here, so they must not force identity here either."""
    elsewhere = Path("C:\\elsewhere\\repo")  # shares no prefix with tmp_path
    log = tmp_path / "log"
    _claim(log, "run-away", ["docs"], elsewhere)
    live = _live(log, now=T0)
    assert relevant_claims(live, worktree=tmp_path) == ()
    decision = check_commit(
        staged=["docs/x.md"],
        live=live,
        worktree=tmp_path,
        run_id=None,
        declared=None,
    )
    assert isinstance(decision, Admission)


def test_a_subdirectory_dispatch_still_shares_this_index(tmp_path):
    log = tmp_path / "log"
    _claim(log, "run-sub", ["docs"], tmp_path / "src")
    assert len(relevant_claims(_live(log, now=T0), worktree=tmp_path)) == 1


# --- policy: identity ----------------------------------------------------------


def test_a_commit_while_claims_are_live_must_name_its_committer(tmp_path):
    log = tmp_path / "log"
    _claim(log, "run-holder", ["docs"], tmp_path)
    decision = check_commit(
        staged=["src/x.py"],
        live=_live(log, now=T0),
        worktree=tmp_path,
        run_id=None,
        declared=None,
    )
    assert isinstance(decision, Refusal)
    assert RUN_ID_ENV in decision.reason


def test_a_blank_identity_is_no_identity(tmp_path):
    log = tmp_path / "log"
    _claim(log, "run-holder", ["docs"], tmp_path)
    decision = check_commit(
        staged=["src/x.py"],
        live=_live(log, now=T0),
        worktree=tmp_path,
        run_id="   ",
        declared=None,
    )
    assert isinstance(decision, Refusal)


def test_a_self_named_outsider_is_admitted_off_claimed_paths(tmp_path):
    """The principal committing while a dispatch runs: named, disjoint, admitted."""
    log = tmp_path / "log"
    _claim(log, "run-holder", ["docs"], tmp_path)
    decision = check_commit(
        staged=["src/x.py"],
        live=_live(log, now=T0),
        worktree=tmp_path,
        run_id="joe",
        declared=None,
    )
    assert isinstance(decision, Admission)
    assert decision.committer == "joe"


# --- policy: the sweep ---------------------------------------------------------


def test_staging_a_path_another_live_run_claims_is_refused(tmp_path):
    log = tmp_path / "log"
    _claim(log, "run-holder", ["docs"], tmp_path)
    decision = check_commit(
        staged=["src/x.py", "docs/register.md"],
        live=_live(log, now=T0),
        worktree=tmp_path,
        run_id="run-other",
        declared=None,
    )
    assert isinstance(decision, Refusal)
    assert "run-holder" in decision.reason
    assert "docs/register.md" in decision.reason


def test_the_holder_may_commit_inside_its_own_claim(tmp_path):
    log = tmp_path / "log"
    _claim(log, "run-holder", ["docs"], tmp_path)
    decision = check_commit(
        staged=["docs/register.md"],
        live=_live(log, now=T0),
        worktree=tmp_path,
        run_id="run-holder",
        declared=None,
    )
    assert isinstance(decision, Admission)


def test_holding_a_claim_is_no_licence_over_a_third_partys(tmp_path):
    """A badge-holder staging into another run's claim is refused like anyone."""
    log = tmp_path / "log"
    _claim(log, "run-a", ["src"], tmp_path)
    _claim(log, "run-b", ["docs"], tmp_path)
    decision = check_commit(
        staged=["src/x.py", "docs/register.md"],
        live=_live(log, now=T0),
        worktree=tmp_path,
        run_id="run-a",
        declared=None,
    )
    assert isinstance(decision, Refusal)
    assert "run-b" in decision.reason


def test_the_sweep_is_caught_across_the_windows_wsl_boundary(tmp_path):
    """The claim was recorded from Windows; the commit is staged from WSL."""
    log = tmp_path / "log"
    _claim(log, "run-win", ["docs"], Path("C:\\Users\\joe\\repo"))
    live = _live(log, now=T0)
    decision = check_commit(
        staged=["docs/register.md"],
        live=live,
        worktree=Path("/mnt/c/Users/joe/repo"),
        run_id="run-wsl",
        declared=None,
    )
    assert isinstance(decision, Refusal)
    assert "run-win" in decision.reason


# --- policy: containment and enumeration ---------------------------------------


def test_a_claimed_run_cannot_commit_outside_its_claim(tmp_path):
    log = tmp_path / "log"
    _claim(log, "run-holder", ["src/consilient"], tmp_path)
    decision = check_commit(
        staged=["src/consilient/commit_gate.py", "tests/test_commit_gate.py"],
        live=_live(log, now=T0),
        worktree=tmp_path,
        run_id="run-holder",
        declared=None,
    )
    assert isinstance(decision, Refusal)
    assert "outside the paths" in decision.reason


def test_a_pathless_claim_requires_enumeration(tmp_path):
    log = tmp_path / "log"
    _claim(log, "run-holder", [], tmp_path)
    live = _live(log, now=T0)
    refused = check_commit(
        staged=["src/x.py"], live=live, worktree=tmp_path, run_id="run-holder",
        declared=None,
    )
    assert isinstance(refused, Refusal)
    assert PATHS_ENV in refused.reason
    admitted = check_commit(
        staged=["src/x.py"], live=live, worktree=tmp_path, run_id="run-holder",
        declared=["src/x.py"],
    )
    assert isinstance(admitted, Admission)


def test_an_unenumerated_staged_path_is_refused(tmp_path):
    """`git add -A` followed by an honest enumeration of one's own work fails:
    the neighbour's file is staged but not enumerated."""
    log = tmp_path / "log"
    _claim(log, "run-holder", [], tmp_path)
    decision = check_commit(
        staged=["src/mine.py", "docs/theirs.md"],
        live=_live(log, now=T0),
        worktree=tmp_path,
        run_id="run-holder",
        declared=["src/mine.py"],
    )
    assert isinstance(decision, Refusal)
    assert "docs/theirs.md" in decision.reason


def test_an_empty_enumeration_is_no_enumeration(tmp_path):
    log = tmp_path / "log"
    _claim(log, "run-holder", [], tmp_path)
    decision = check_commit(
        staged=["src/x.py"], live=_live(log, now=T0), worktree=tmp_path,
        run_id="run-holder", declared=[""],
    )
    assert isinstance(decision, Refusal)
    assert PATHS_ENV in decision.reason


def test_a_fanout_child_badges_under_the_parents_claim(tmp_path):
    """Fan-out children run under the parent's claim; the badge names it."""
    log = tmp_path / "log"
    _claim(log, "run-parent", ["src"], tmp_path)
    decision = check_commit(
        staged=["src/x.py"],
        live=_live(log, now=T0),
        worktree=tmp_path,
        run_id="run-parent",
        declared=None,
    )
    assert isinstance(decision, Admission)


# --- policy: the dead agent ----------------------------------------------------


def test_a_dead_agents_claim_releases_the_gate_by_the_clock(tmp_path):
    """The crash-safety invariant at the gate: no completion, no outcome event,
    just the passage of time. Before expiry the commit is refused; after it,
    admitted — and there is no lock file to go stale."""
    log = tmp_path / "log"
    _claim(log, "run-dies", ["docs"], tmp_path, timeout_s=60)
    grace = coordination.CLAIM_GRACE_S
    during = check_commit(
        staged=["docs/x.md"],
        live=_live(log, now=T0 + timedelta(seconds=60 + grace - 1)),
        worktree=tmp_path,
        run_id="run-other",
        declared=None,
    )
    assert isinstance(during, Refusal)
    after = check_commit(
        staged=["docs/x.md"],
        live=_live(log, now=T0 + timedelta(seconds=60 + grace + 1)),
        worktree=tmp_path,
        run_id=None,
        declared=None,
    )
    assert isinstance(after, Admission)


# --- execution: the hook script against a real repository ----------------------


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _git(repo, "init", "-q").returncode == 0
    top = _git(repo, "rev-parse", "--show-toplevel").stdout.strip()
    return Path(top).resolve()


def _stage(repo: Path, relative: str) -> None:
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"content of {relative}\n", encoding="utf-8")
    assert _git(repo, "add", relative).returncode == 0


def _gate(repo: Path, **env_overrides: str) -> subprocess.CompletedProcess[str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {RUN_ID_ENV, PATHS_ENV}
    }
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_script_admits_a_solo_commit_without_identity(tmp_path):
    repo = _repo(tmp_path)
    _stage(repo, "src/x.py")
    result = _gate(repo)
    assert result.returncode == 0, result.stderr


def test_script_refuses_the_sweep_and_admits_the_owner(tmp_path):
    repo = _repo(tmp_path)
    _claim(repo / ".harness" / "log", "run-holder", ["docs"], repo,
           now=datetime.now(timezone.utc))
    _stage(repo, "docs/register.md")
    refused = _gate(repo, **{RUN_ID_ENV: "run-other"})
    assert refused.returncode == 1
    assert "run-holder" in refused.stderr
    admitted = _gate(repo, **{RUN_ID_ENV: "run-holder"})
    assert admitted.returncode == 0, admitted.stderr


def test_script_requires_identity_while_a_claim_is_live(tmp_path):
    repo = _repo(tmp_path)
    _claim(repo / ".harness" / "log", "run-holder", ["docs"], repo,
           now=datetime.now(timezone.utc))
    _stage(repo, "src/x.py")
    result = _gate(repo)
    assert result.returncode == 1
    assert RUN_ID_ENV in result.stderr


def test_script_enforces_enumeration_for_a_pathless_claim(tmp_path):
    repo = _repo(tmp_path)
    _claim(repo / ".harness" / "log", "run-holder", [], repo,
           now=datetime.now(timezone.utc))
    _stage(repo, "src/mine.py")
    _stage(repo, "docs/theirs.md")
    refused = _gate(repo, **{RUN_ID_ENV: "run-holder"})
    assert refused.returncode == 1
    assert PATHS_ENV in refused.stderr
    swept = _gate(
        repo, **{RUN_ID_ENV: "run-holder", PATHS_ENV: "src/mine.py"}
    )
    assert swept.returncode == 1
    assert "docs/theirs.md" in swept.stderr
    admitted = _gate(
        repo,
        **{RUN_ID_ENV: "run-holder", PATHS_ENV: "src/mine.py,docs/theirs.md"},
    )
    assert admitted.returncode == 0, admitted.stderr


def test_script_admits_after_a_dead_holders_claim_expires(tmp_path):
    """SIGKILLed two hours ago, never completed: the clock alone releases it."""
    repo = _repo(tmp_path)
    _claim(
        repo / ".harness" / "log",
        "run-dies",
        ["docs"],
        repo,
        now=datetime.now(timezone.utc) - timedelta(hours=2),
        timeout_s=60,
    )
    _stage(repo, "docs/x.md")
    result = _gate(repo)
    assert result.returncode == 0, result.stderr


def test_script_fails_closed_when_git_cannot_enumerate_the_index(tmp_path):
    """A gate that cannot see the staged set must not count as a pass."""
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()
    (not_a_repo / "x.py").write_text("x\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=not_a_repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env={key: value for key, value in os.environ.items() if key != RUN_ID_ENV},
    )
    assert result.returncode == 1
    assert "could not enumerate the staged set" in result.stderr


# --- wiring ---------------------------------------------------------------------


def test_the_tracked_pre_commit_hook_calls_the_gate():
    """Pin the invocation, not the word: an earlier draft matched a comment
    mentioning commit_gate.py, so a mutant that severed the call survived."""
    assert SCRIPT.is_file()
    hook = HOOK.read_text(encoding="utf-8")
    assert "check_secrets.py" in hook  # the secrets stage is untouched
    assert 'gate="scripts/commit_gate.py"' in hook
    assert 'python "$gate"' in hook
    # The badge variables must be bridged through WSLENV or a WSL-side
    # committer's identity never reaches a Windows python [measured].
    assert "WSLENV" in hook


def test_the_gate_script_has_no_metered_or_network_path():
    source = SCRIPT.read_text(encoding="utf-8")
    for needle in ("requests", "urllib", "socket", "openrouter"):
        assert needle not in source

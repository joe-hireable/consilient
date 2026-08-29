"""History may not be replayed over live instance state, because git deletes it on the way out.

THE MYSTERY THIS SOLVES, reproduced 29 August 2026 after two investigations failed to solve it
by reading code. `.harness/plan-units.json` -- the file defining all 147 build units, and the one
file the driver cannot work without -- was deleted at least five times. `ensure_plan` exists
solely to restore it, and its docstring records the failure honestly: "What deletes it is still
unknown ... neither the loop nor the driver removes it ... `git clean -nd` lists nothing ... a
watcher polling twice a second caught the context but not the culprit."

Nothing deletes it. GIT does.

The file is untracked and gitignored today. It was TRACKED at commit ddbf0f5, which the driver
kept cherry-picking for unit Z05. Cherry-picking a commit that touches a path HEAD does not carry
stages that path; the abort or reset that follows a conflict then REMOVES it, because there is no
HEAD version to restore. Measured in a throwaway clone:

    plan after cherry-pick  : present, but its content replaced by the old version
    plan after --abort      : GONE
    plan after reset --hard : GONE

Every earlier negative result is consistent with this: no Python unlink exists, `git clean -nd`
lists nothing while the ignore rule stands, and git's abort is atomic so no poller can catch it.

The overwrite is the worse half. A deleted plan is loud and self-heals; a plan silently replaced
by an older, smaller one looks entirely valid and the driver builds the wrong thing.

The first test below reproduces the mechanism end to end in a temporary repository, so the
danger is demonstrated rather than asserted. The rest pin the guard that now refuses it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tests.build_driver_helpers import _load_driver

DRIVER = _load_driver()


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_replaying_a_commit_over_ignored_state_destroys_it(tmp_path: Path) -> None:
    """The mechanism itself, in a repository built for the purpose.

    Without this the guard below is a rule against a danger nobody has seen. Deliberately uses
    no repository fixture: the behaviour is git's, not this project's, and it must be shown on
    a tree with no other moving parts.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main", ".")
    _git(repo, "config", "user.email", "probe@publisher.example-not-reserved.co.uk")
    _git(repo, "config", "user.name", "Probe")
    _git(repo, "config", "commit.gpgsign", "false")

    state = repo / "instance-state.json"
    (repo / "keep.txt").write_text("base\n", encoding="utf-8")
    state.write_text('{"units": 147}\n', encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base, with the state file TRACKED")

    # The commit that will later be replayed: it edits the state file while it is still tracked.
    state.write_text('{"units": 80}\n', encoding="utf-8")
    (repo / "keep.txt").write_text("diverged\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "an old commit that rewrites the state file")
    old = _git(repo, "rev-parse", "HEAD").stdout.strip()

    # The tree moves on: the state file becomes untracked, gitignored instance data, and the
    # live copy is what the running system depends on.
    _git(repo, "checkout", "-q", "HEAD~1")
    _git(repo, "checkout", "-q", "-b", "live")
    _git(repo, "rm", "-q", "--cached", "instance-state.json")
    (repo / ".gitignore").write_text("instance-state.json\n", encoding="utf-8")
    (repo / "keep.txt").write_text("live work\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "untrack the state file and ignore it")
    state.write_text('{"units": 147, "live": true}\n', encoding="utf-8")

    assert state.is_file()
    assert _git(repo, "check-ignore", "-q", "instance-state.json").returncode == 0

    picked = _git(repo, "cherry-pick", old)
    assert picked.returncode != 0, (
        "the fixture needs the cherry-pick to conflict, as Z05's did"
    )
    assert '"live": true' not in state.read_text(encoding="utf-8"), (
        "the cherry-pick was expected to overwrite the live state file"
    )

    _git(repo, "cherry-pick", "--abort")
    assert not state.is_file(), (
        "the abort was expected to DELETE the untracked state file, which is the whole finding; "
        "if git no longer does this the guard may be unnecessary and this test should be re-read"
    )


def test_the_guard_flags_a_commit_carrying_untracked_instance_state() -> None:
    """ddbf0f5 is the real commit the driver kept replaying for Z05."""
    flagged = DRIVER.replays_over_instance_state("ddbf0f5")
    assert ".harness/plan-units.json" in flagged, (
        "the commit that destroyed the plan five times is no longer detected as dangerous"
    )


def test_the_guard_leaves_ordinary_commits_alone() -> None:
    """A rule that refuses everything stops the build instead of protecting it."""
    assert DRIVER.replays_over_instance_state("HEAD") == []
    assert DRIVER.replays_over_instance_state("750f73bd3") == [], (
        "A01's commit touches only product files and must replay normally"
    )


def test_the_merge_path_actually_consults_the_guard() -> None:
    """A predicate nothing calls is decoration; the cherry-pick must ask before it starts."""
    source = Path(DRIVER.__file__ or "").read_text(encoding="utf-8")
    body = source.partition('git", "cherry-pick", "--signoff"')[0]
    assert "replays_over_instance_state(sha)" in body, (
        "the refusal is not evaluated before the cherry-pick, so the commit is applied first "
        "and the damage is already done by the time anything notices"
    )


def test_the_guard_skips_the_commit_rather_than_blocking_the_unit() -> None:
    """Preventing damage must not become deadlock, which is what the first version did.

    The guard originally returned, refusing the whole unit. Measured: 12 branches carry the
    poisoned commit in their replay range, so every one of them was blocked entirely because ONE
    commit out of several was poison. The unit's real work had done nothing wrong.

    Asserted on the source rather than by driving a merge, and that limitation is worth stating:
    exercising `merge_unit_worktree` needs a unit worktree, a plan entry, a claim and a clean main
    tree, and building all four would test the fixture more than the rule. What is cheap to check
    is the control flow, and the control flow is exactly what changed -- `continue` where there
    used to be `return`. The behaviour that MATTERS, that git destroys the file, is reproduced for
    real in the first test in this module.
    """
    source = Path(DRIVER.__file__ or "").read_text(encoding="utf-8")
    guarded = source.partition("clobbers = replays_over_instance_state(sha)")[2]
    branch = guarded.partition('r = sh(["git", "cherry-pick"')[0]
    assert branch, "the guard and the cherry-pick are no longer adjacent; re-read this test"
    assert "continue" in branch, (
        "the guard no longer skips the offending commit; if it returns instead, a unit with one "
        "poisoned commit among several is blocked for ever rather than landing its real work"
    )
    assert "return" not in branch, (
        "the guard refuses the whole unit again. Stopping the damage is necessary but it must "
        "not cost the unit its other commits -- 12 branches are affected"
    )

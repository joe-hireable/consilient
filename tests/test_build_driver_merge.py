"""What is allowed to land on the shared branch, and what the cherry-pick must stamp on
it.

Every unit's work reaches the branch through one cherry-pick, which makes that the only
chokepoint where a property can be enforced for all of it — principle 3, in the driver.
MEASURED 26 August 2026: CI's DCO check failed on every recent push with "no sign-off
found" for every commit. A dispatched worker's own commit carries no guaranteed `Signed-
off-by` — workers run arbitrary shells across several harnesses, and asking each one to
remember `--signoff` is a prompt-level fix, which the Engineering Ratchet forbids. The
sign-off is stamped at the merge.

MEASURED 27 August 2026, against real git rather than a fake `sh`: two units, W07 among
them, generated dozens of zero-diff commits — at one point 189 of the last 200 commits
on this branch were two empty messages repeating. The cause was not the one first
suspected. `--allow-empty` does not make git swallow a commit whose content is already
in HEAD; that case still exits non-zero with "the previous cherry-pick is now empty" and
is handled. What it does is let a source commit that was empty *to begin with* be
replayed as a fresh empty commit, exit 0, and be counted as applied. The replay gets a
new sha, so `HEAD..unit_head` still lists the original on the next tick, with no content
for git to recognise as already present — so it is cherry-picked again, once per tick,
for ever. It must also be reported rather than silently dropped: the driver has to be
able to say why a unit with commits merged nothing.

MEASURED 26 August 2026: `mergeable` excluded any uid already in `built`, so a unit
whose worktree gained a genuinely new commit after being marked built — a conflict
resolution or a review fix landing after the plan commit merged — was never revisited by
any later tick. AN, AJ and AL each sat that way: `built: true`, a real new commit in the
worktree, zero merge attempts logged since. `merge_unit_worktree`'s own `HEAD..head`
rev-list is the cheap no-op guard.

The type gate is the last of it, and it was refusing honest work. Bare zero-tolerance
mypy meant a file carrying pre-existing type debt — `build_driver.py` itself, about 87
long-accepted errors — could never pass for any commit that touched it, whether the
commit fixed, worsened or never touched the debt; BO's own verified-zero-delta fix was
refused by this exact gate. It now compares against the tree the cherry-pick started
from and refuses only a genuine increase, and a baseline that cannot be established at
all fails closed rather than waving the merge through."""

import subprocess
from pathlib import Path
from build_driver_helpers import (
    _load_driver,
)


def test_merge_unit_worktree_signs_off_the_cherry_pick(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 26 August 2026: CI's DCO check failed on every recent push with "no sign-off
    found" for every commit. A dispatched worker's own commit is not guaranteed to carry a
    Signed-off-by trailer -- workers run arbitrary shells across several harnesses, and
    asking each one to remember `--signoff` is a prompt-level fix. The sign-off is stamped
    at the one chokepoint all unit work must pass through instead: the cherry-pick that
    merges a unit's commits into the shared branch.
    """
    driver = _load_driver()
    worktrees = tmp_path / "worktrees"
    worktrees.mkdir()
    (worktrees / "U01").mkdir()
    monkeypatch.setattr(driver, "WORKTREES", worktrees)
    monkeypatch.setattr(driver, "gate_merged_tree", lambda _touched, _baseline: "")

    calls: list[list[str]] = []

    class _Result:
        def __init__(self, stdout: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    def fake_sh(args: list[str]) -> _Result:
        calls.append(args)
        if "-C" in args and "rev-parse" in args:
            return _Result("unit-head-sha\n")
        if args[:2] == ["git", "rev-parse"]:
            return _Result("main-head-sha\n")
        if "rev-list" in args:
            return _Result("abc123\n")
        if args[:3] == ["git", "show", "--name-only"]:
            return _Result("some/file.py\n")
        if "diff" in args and "--numstat" in args:
            return _Result("")
        if "cherry-pick" in args:
            return _Result("", 0)
        return _Result("")

    monkeypatch.setattr(driver, "sh", fake_sh)

    result = driver.merge_unit_worktree("U01")

    assert result == "applied 1 commit(s) from U01"
    cherry_pick_calls = [c for c in calls if "cherry-pick" in c]
    assert cherry_pick_calls, "expected a cherry-pick call"
    assert "--signoff" in cherry_pick_calls[0]


def test_mypy_gate_does_not_refuse_a_files_own_pre_existing_debt(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 26 August 2026: bare zero-tolerance mypy meant a file carrying pre-existing type
    debt (build_driver.py itself, ~87 long-accepted errors) could never pass this gate for ANY
    commit that touched it, regardless of whether the commit fixed, worsened, or never touched
    the debt at all. BO's own verified-zero-delta fix was refused by this exact gate. The fix
    compares against the tree the cherry-pick started from and refuses only a genuine increase.
    """
    driver = _load_driver()

    calls: list[list[str]] = []

    class _Result:
        def __init__(self, stdout: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    def fake_sh(args: list[str]) -> _Result:
        calls.append(args)
        if "worktree" in args and "add" in args:
            # _mypy_gate checks (scratch / path).exists() on real disk, so the fake
            # worktree needs the same file physically present to be treated as
            # carrying the same pre-existing debt as the working tree.
            scratch = Path(args[args.index("--detach") + 1])
            (scratch / "some").mkdir(parents=True)
            (scratch / "some" / "file.py").write_text("", encoding="utf-8")
            return _Result("", 0)
        if "worktree" in args and "remove" in args:
            return _Result("", 0)
        if "mypy" in args:
            # Both the "after" and any "before" mypy invocation land here; both see the
            # same pre-existing debt, so no new error is introduced by this merge.
            return _Result(
                "some/file.py:1: error: fake pre-existing debt  [no-untyped-def]\n"
                "Found 1 error in 1 file (checked 1 source file)\n",
                1,
            )
        return _Result("", 0)

    (tmp_path / "some").mkdir()
    (tmp_path / "some" / "file.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(driver, "sh", fake_sh)
    monkeypatch.setattr(driver, "ROOT", tmp_path)

    result = driver.gate_merged_tree(["some/file.py"], "deadbeef")

    assert result is None, (
        f"pre-existing debt with no new errors must not refuse the merge: {result}"
    )
    mypy_calls = [c for c in calls if "mypy" in c]
    assert len(mypy_calls) == 2, "expected one 'after' and one 'before' mypy invocation"


def test_mypy_gate_refuses_a_genuine_regression(tmp_path: Path, monkeypatch) -> None:
    """The other half: if the touched file's error count is actually HIGHER than at the
    baseline, the gate must still refuse -- this fix narrows what counts as a failure, it does
    not remove the check.
    """
    driver = _load_driver()

    class _Result:
        def __init__(self, stdout: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    def fake_sh(args: list[str]) -> _Result:
        if "worktree" in args and "add" in args:
            scratch = Path(args[args.index("--detach") + 1])
            (scratch / "some").mkdir(parents=True)
            (scratch / "some" / "file.py").write_text("", encoding="utf-8")
            return _Result("", 0)
        if "worktree" in args and "remove" in args:
            return _Result("", 0)
        if "mypy" in args:
            # The "before" call's file arguments point inside the scratch worktree
            # (named "gate-baseline-<hex>"); the "after" call uses the plain relative
            # path. That is the only reliable way to tell them apart here, since the
            # scratch dir never actually gets its own mypy.ini written to disk.
            if any("gate-baseline-" in arg for arg in args):
                return _Result(
                    "some/file.py:1: error: one pre-existing error  [no-untyped-def]\n",
                    1,
                )
            return _Result(
                "some/file.py:1: error: one pre-existing error  [no-untyped-def]\n"
                "some/file.py:2: error: a brand new one  [no-untyped-def]\n",
                1,
            )
        return _Result("", 0)

    (tmp_path / "some").mkdir()
    (tmp_path / "some" / "file.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(driver, "sh", fake_sh)
    monkeypatch.setattr(driver, "ROOT", tmp_path)

    result = driver.gate_merged_tree(["some/file.py"], "deadbeef")

    assert result is not None, (
        "a genuine error-count increase must still refuse the merge"
    )
    assert "regressed" in result


def test_mypy_gate_fails_closed_when_the_baseline_worktree_cannot_be_created(
    tmp_path: Path, monkeypatch
) -> None:
    """If the baseline can't be established at all, refuse rather than silently let anything
    through -- the whole point is comparing against a known-good state, not skipping the check.
    """
    driver = _load_driver()

    class _Result:
        def __init__(self, stdout: str = "", returncode: int = 0) -> None:
            self.stdout = stdout
            self.stderr = ""
            self.returncode = returncode

    def fake_sh(args: list[str]) -> _Result:
        if "worktree" in args and "add" in args:
            return _Result("fatal: could not create worktree", 1)
        if "mypy" in args:
            return _Result("some/file.py:1: error: whatever  [no-untyped-def]\n", 1)
        return _Result("", 0)

    (tmp_path / "some").mkdir()
    (tmp_path / "some" / "file.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(driver, "sh", fake_sh)
    monkeypatch.setattr(driver, "ROOT", tmp_path)

    result = driver.gate_merged_tree(["some/file.py"], "deadbeef")

    assert result is not None, (
        "an unestablished baseline must fail closed, not pass silently"
    )


def test_main_merges_a_built_units_worktree_when_it_gains_new_commits(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 26 August 2026: `mergeable` excluded any uid already in `built`, so a unit
    whose worktree gained a genuinely new commit after being marked built (a fork's
    conflict-resolution or review fix landing after the plan commit already merged) was
    never revisited by any later tick. AN, AJ and AL each sat this way -- `built: true`, a
    real new commit sitting in the worktree, zero merge attempts logged since. Excluding
    built units from the merge loop was never the right check: `merge_unit_worktree`'s own
    `HEAD..head` rev-list is the cheap no-op guard for a unit with nothing new to merge.
    """
    driver = _load_driver()
    worktrees = tmp_path / "unit-worktrees"
    (worktrees / "U01").mkdir(parents=True)
    state: dict[str, object] = {
        "in_flight": {},
        "attempts": {},
        "built": ["U01"],
        "review_dispatched": ["U01"],
    }
    units = {
        "U01": {
            "title": "already built, worktree has a newer commit",
            "commit": "feat(unit): already built",
            "claims": [],
            "deps": [],
        }
    }
    calls: list[str] = []
    monkeypatch.setattr(driver, "WORKTREES", worktrees)
    monkeypatch.setattr(
        driver, "load", lambda path, _default: units if path == driver.UNITS else state
    )
    monkeypatch.setattr(driver, "committed", lambda _uid, _unit: False)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: None)
    monkeypatch.setattr(driver, "start_failed_dispatches", lambda: [])
    monkeypatch.setattr(driver, "crashed_dispatches", lambda _state: [])
    monkeypatch.setattr(driver, "save_state", lambda _state: None)
    monkeypatch.setattr(driver, "record_tick_intent", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        driver,
        "merge_unit_worktree",
        lambda uid: calls.append(uid) or "no commits",
    )

    assert driver.main() == 0

    assert calls == ["U01"], (
        "a built unit's worktree must still be checked for new commits to merge"
    )


def test_an_originally_empty_unit_commit_lands_no_commit_at_all(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 27 August 2026, against real git, not a fake `sh`.

    Two units (W07 among them) generated dozens of zero-diff commits -- at one point 189 of
    the last 200 commits on this branch were two empty messages repeating. The cause is not
    the one first suspected. `--allow-empty` does NOT make git swallow a commit whose content
    is already in HEAD: that case still exits non-zero with "the previous cherry-pick is now
    empty", which the already-applied branch below handles correctly. What `--allow-empty`
    does is let a source commit that was empty *to begin with* be replayed as a fresh empty
    commit, exit 0, and be counted as `applied`.

    That one then cannot terminate. The replayed commit gets a new sha, so `HEAD..unit_head`
    still lists the original on the next tick, and there is no content for git to recognise as
    already present -- so it is cherry-picked again, and again, once per tick, forever.

    Dropping the flag routes an empty source commit into the same already-applied path the
    content case uses: git exits non-zero, the driver skips it, and nothing lands.
    """
    driver = _load_driver()

    root = tmp_path / "main"
    root.mkdir()

    def git(*args: str, cwd: Path = root) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        ).stdout

    git("init", "-q", "-b", "main", ".")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "Test")
    git("config", "commit.gpgsign", "false")
    (root / "f.txt").write_text("base\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "base")

    worktrees = tmp_path / "worktrees"
    worktrees.mkdir()
    unit = worktrees / "U01"
    git("worktree", "add", "-q", "-b", "unit", str(unit))
    # The one thing this unit ever committed carries no content.
    git("commit", "-q", "--allow-empty", "-m", "no-op from the harness", cwd=unit)

    monkeypatch.setattr(driver, "ROOT", root)
    monkeypatch.setattr(driver, "WORKTREES", worktrees)
    monkeypatch.setattr(driver, "gate_merged_tree", lambda _touched, _baseline: "")

    before = git("rev-parse", "HEAD").strip()
    result = driver.merge_unit_worktree("U01")
    after = git("rev-parse", "HEAD").strip()

    assert after == before, (
        f"an empty unit commit must not land a commit; HEAD moved {before[:9]} -> {after[:9]}\n"
        f"driver said: {result}"
    )
    assert "applied 1" not in result, (
        f"a commit that changed nothing must not be reported as applied: {result!r}"
    )
    # And it must be reported, not silently dropped -- the driver has to be able to say why a
    # unit with commits merged nothing.
    assert "already" in result or "no commits" in result, result

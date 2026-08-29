"""The loop's housekeeping — repairs that only count if the loop actually runs them.

These check `.harness/build_loop.py` rather than the driver, and most are structural
because the property is structural: a repair that is defined and never called is
indistinguishable from no repair, and nothing behavioural in the suite could tell the
difference.

`self_heal` was written on 24 August 2026, documented at length, and never called. A WSL
agent had written `core.worktree = /mnt/c/...` into the shared `.git/config` at 22:57
that night and it was still there thirteen hours later. `git worktree add` fails while
that line is present, so every dispatch fell through to a workspace form that clones
with `--separate-git-dir`; agent commits then landed in a different object store,
invisible to the driver. Eleven commits of finished work were stranded and one unit was
built twice [measured]. The call must also sit inside the tick loop, since the
corruption is written during operation and a startup-only repair cannot fix a fault that
appears after startup.

Pruning has the same shape and the same history: 547 worktrees and 673 stale branches
accumulated with nothing removing them, `.git` reached 136 MB, and provisioning began to
fail — which sent every dispatch to the same unharvestable fallback. It lives in the
loop rather than the driver because a destructive git sweep has no business running
inside the driver's unit tests; the first attempt did exactly that and began removing
real worktrees during a test run. Its safety rules are asserted here because they are
what make an autonomous sweep acceptable at all, and its ceiling is asserted because a
ceiling that is defined but never consulted is not a ceiling.

The WSL check guards the same estate from the other side. 37 of 41 built-and-unmerged
units had lost their git metadata: cursor-agent runs under WSL, so its git rewrote each
worktree's pointer to `/mnt/c/...`, Windows git could then not read the worktree, and
the disposal paths take an unreadable worktree for an empty one — `worktree remove
--force` skips its has-work guard and `worktree prune` drops the registration, so the
work becomes unmergeable for ever [measured, 27 August 2026]. Rewriting the path back is
lossless; not rewriting it costs the unit."""

import ast
import importlib.util
import sys
from pathlib import Path
from build_driver_helpers import (
    ROOT,
)

# --- the loop must actually CALL its self-repair, 25 August 2026 ---------------
#
# `self_heal` was written on 24 August, documented at length, and NEVER CALLED. A WSL agent had
# written `core.worktree = /mnt/c/...` into the shared .git/config at 22:57 on the 24th and it
# was still there thirteen hours later, because the repair that exists for exactly that line
# had no call site.
#
# The cost was not cosmetic. `git worktree add` fails while that line is present, so every
# dispatch fell through to the isolated_git_env workspace form, which clones with
# --separate-git-dir; agent commits then landed in a different object store, invisible to the
# driver. Eleven commits of finished work were stranded and one unit was built twice.
#
# A defined-but-uncalled repair is indistinguishable from no repair, and nothing in the suite
# could tell the difference. This is that check.


def test_the_loop_calls_self_heal_every_tick() -> None:
    # The loop's housekeeping moved into build_loop_*.py on 28 August 2026. These checks are
    # about what the loop DOES each tick, so they read the family; reading the entry point alone
    # reported self_heal "gone" when it had only moved one file over.
    source = "".join(
        p.read_text(encoding="utf-8")
        for p in sorted((ROOT / ".harness").glob("build_loop*.py"))
    )
    tree = ast.parse(source)

    defined = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "self_heal" in defined, (
        "self_heal is gone; this test guards its call, not its name"
    )

    main = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    called = {
        node.func.id
        for node in ast.walk(main)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "self_heal" in called, (
        "build_loop.main() does not call self_heal. It was defined and never called for a "
        "full day, during which a /mnt/c path sat in .git/config breaking every worktree "
        "creation and stranding eleven commits of finished work."
    )

    # And inside the loop, not once before it: the corruption is written DURING operation by a
    # dispatched agent, so a repair that only runs at startup cannot fix it.
    loops = [node for node in ast.walk(main) if isinstance(node, (ast.While, ast.For))]
    assert any(
        isinstance(inner, ast.Call)
        and isinstance(inner.func, ast.Name)
        and inner.func.id == "self_heal"
        for loop in loops
        for inner in ast.walk(loop)
    ), (
        "self_heal is called outside the tick loop; a startup-only repair cannot fix a fault that appears after startup"
    )


# --- autonomous workspace pruning lives in the loop, 25 August 2026 ------------
#
# 547 worktrees and 673 stale branches accumulated with nothing pruning them, .git reached
# 136 MB, and provisioning began to fail -- which sent every dispatch to a fallback form whose
# commits cannot be harvested. Eleven commits of finished work were stranded and one unit was
# built twice.
#
# It sits in build_loop, not build_driver, because it is housekeeping and because a destructive
# git sweep has no business running inside the driver's unit tests -- the first attempt did
# exactly that and started removing real worktrees during a test run.


def _loop_source() -> str:
    return "".join(
        p.read_text(encoding="utf-8")
        for p in sorted((ROOT / ".harness").glob("build_loop*.py"))
    )


def test_the_loop_prunes_spent_workspaces_every_tick() -> None:
    tree = ast.parse(_loop_source())
    main = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "main"
    )
    loops = [n for n in ast.walk(main) if isinstance(n, (ast.While, ast.For))]
    assert any(
        isinstance(inner, ast.Call)
        and isinstance(inner.func, ast.Name)
        and inner.func.id == "prune_spent_workspaces"
        for loop in loops
        for inner in ast.walk(loop)
    ), (
        "build_loop.main() does not prune inside the tick loop; accumulation broke provisioning once already"
    )


def test_the_prune_refuses_to_touch_anything_but_a_dispatch_workspace() -> None:
    """The safety rules are what make an autonomous sweep acceptable at all."""
    source = _loop_source()
    start = source.index("def prune_spent_workspaces(")
    body = source[start : source.index("\ndef self_heal(", start)]

    assert "/.harness/dispatch/" in body, (
        "the prune no longer restricts itself to dispatch workspaces -- a unit worktree or the "
        "main tree could be removed"
    )
    assert "rev-list" in body and "ahead" in body, (
        "the prune no longer checks whether a workspace carries commits HEAD lacks; a cleanup "
        "that discards a commit is worse than no cleanup"
    )
    assert "status" in body and "--porcelain" in body, (
        "the prune no longer checks for uncommitted work"
    )
    assert "consilient-workspace-probe-" in body, (
        "the prune no longer ignores the provisioning probe marker, so every workspace will "
        "look dirty and nothing will ever be pruned"
    )


def test_the_prune_has_a_ceiling_so_an_ordinary_tick_pays_nothing() -> None:
    source = _loop_source()
    assert "PRUNE_CEILING" in source
    start = source.index("def prune_spent_workspaces(")
    body = source[start : source.index("\ndef self_heal(", start)]
    assert "PRUNE_CEILING" in body, "the ceiling is defined but not consulted"


def test_a_wsl_git_pointer_is_normalised_before_anything_prunes_it(
    tmp_path: Path,
) -> None:
    """The guard that stops a WSL dispatch from getting a live worktree deleted.

    MEASURED 27 August 2026: 37 of 41 built-and-unmerged units had lost their git metadata.
    cursor-agent runs under WSL, so its git rewrote each worktree's pointer to /mnt/c/...,
    Windows git could then not read the worktree, and the loop's disposal paths take an
    unreadable worktree for an empty one -- `worktree remove --force` skips its has-work
    guard and `worktree prune` drops the registration. The work becomes unmergeable forever.

    Rewriting the path back is lossless. Not rewriting it costs the unit.
    """
    # Load the module the FUNCTION UNDER TEST lives in, because that is the namespace it
    # resolves `ROOT` in. `normalise_wsl_gitdirs` moved into build_loop_housekeeping.py on
    # 28 August 2026 -- which imports ROOT from build_loop_git.py -- and
    # `loop.ROOT = root` then set an attribute on a facade that the function never reads --
    # so it scanned the real repository, found nothing to rewrite, and returned 0. A patch
    # landing on a re-exported name is silent, which is why it must target the definition.
    spec = importlib.util.spec_from_file_location(
        "build_loop_housekeeping_test", ROOT / ".harness" / "build_loop_housekeeping.py"
    )
    assert spec is not None and spec.loader is not None
    loop = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loop
    spec.loader.exec_module(loop)

    root = tmp_path / "cto"
    (root / ".harness" / "unit-worktrees" / "N02").mkdir(parents=True)
    (root / ".git").write_text(
        "gitdir: /mnt/c/Users/x/repo/.git/worktrees/cto" + chr(10), encoding="utf-8"
    )
    unit = root / ".harness" / "unit-worktrees" / "N02" / ".git"
    unit.write_text(
        "gitdir: /mnt/c/Users/x/repo/.git/worktrees/N02" + chr(10), encoding="utf-8"
    )
    healthy = root / ".harness" / "unit-worktrees" / "N03"
    healthy.mkdir()
    (healthy / ".git").write_text(
        "gitdir: C:/Users/x/repo/.git/worktrees/N03" + chr(10), encoding="utf-8"
    )

    loop.ROOT = root

    class _Log:
        def __init__(self) -> None:
            self.text = ""

        def write(self, s: str) -> None:
            self.text += s

        def flush(self) -> None:
            pass

    log = _Log()
    fixed = loop.normalise_wsl_gitdirs(log)

    assert fixed == 2, f"expected both WSL pointers rewritten, got {fixed}"
    assert "C:/Users/x/repo" in (root / ".git").read_text(encoding="utf-8")
    assert "/mnt/" not in (root / ".git").read_text(encoding="utf-8")
    assert "/mnt/" not in unit.read_text(encoding="utf-8")
    # the already-correct one must be left exactly alone
    assert (healthy / ".git").read_text(encoding="utf-8").startswith("gitdir: C:/")
    assert "normalised 2 WSL-form" in log.text

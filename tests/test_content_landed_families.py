"""Work that landed in a sibling counts as landed, or a repaired unit can never retire.

THE TRAP, measured 29 August 2026. `_content_landed` decides whether a unit's work is already in
the tree by asking whether the commit's added lines are present in HEAD. It asked at the SAME
PATH the commit named. After the 28 August splits that path is often a re-export facade holding
almost no code, so a commit's lines can be wholly present in the tree and wholly absent from the
file it named.

Measured on the conflicted units that day: S02's added lines were 8.5% present at their own paths
and 70.0% present across their families; A01's were 5.8% and 37.7%. The 8.5% does not improve
when a resolver finishes the work, because the resolver puts the code in the sibling too. So the
unit could be completely repaired and still read as unlanded, for ever, burning a resolver slot
each time it was retried.

Searching the family is not a widening of the check. Before the split those siblings WERE the
file, so it asks exactly the question the check asked before the paths moved. The twenty-line
floor and the 0.99 threshold are untouched and still separate "landed" from "coincidentally
similar".

These tests drive the real function with a faked `git show`, so they assert behaviour rather than
the shape of the source. The fix changed no verdict on the day it landed -- all three conflicted
units were below the threshold for unrelated reasons -- which is precisely why it needs a test
that can fail.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.build_driver_helpers import ROOT, _load_driver

DRIVER = _load_driver()
PKG = Path("src/consilient")


def _sibling_lines(count: int) -> tuple[str, str, list[str]]:
    """Real lines from a real sibling, so the test exercises a real family.

    Returns the entry point's path, the sibling's path, and lines that live ONLY in the sibling.
    """
    entry = PKG / "events.py"
    sibling = PKG / "events_kinds.py"
    entry_lines = {
        ln.rstrip() for ln in (ROOT / entry).read_text(encoding="utf-8").splitlines()
    }
    picked: list[str] = []
    for raw in (ROOT / sibling).read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        # Substantive, and genuinely absent from the facade -- otherwise the test would pass
        # with or without the fix and prove nothing.
        if len(line.strip()) > 25 and line not in entry_lines:
            picked.append(line)
        if len(picked) == count:
            break
    assert len(picked) == count, "not enough sibling-only lines to build the fixture"
    return entry.as_posix(), sibling.as_posix(), picked


def _fake_git(
    monkeypatch: pytest.MonkeyPatch, path: str, lines: list[str], *, family: bool
):
    """Answer `git show` as git would, optionally pretending the siblings do not exist."""
    diff = "\n".join([f"+++ b/{path}"] + [f"+{line}" for line in lines])

    def fake_sh(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[:3] == ["git", "show", "--format="]:
            return subprocess.CompletedProcess(args, 0, diff, "")
        if len(args) == 3 and args[:2] == ["git", "show"]:
            target = args[2].removeprefix("HEAD:")
            if not family and target != path:
                return subprocess.CompletedProcess(args, 1, "", "not found")
            blob = (
                (ROOT / target).read_text(encoding="utf-8")
                if (ROOT / target).is_file()
                else ""
            )
            return subprocess.CompletedProcess(args, 0, blob, "")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(DRIVER, "sh", fake_sh)


def test_lines_that_moved_into_a_sibling_count_as_landed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry, _sibling, lines = _sibling_lines(30)
    _fake_git(monkeypatch, entry, lines, family=True)
    assert DRIVER._content_landed("deadbeef") is True, (
        "work present in a sibling of the claimed file read as unlanded; a unit whose code was "
        "moved by a split can then never retire, however completely it is repaired"
    )


def test_without_the_family_those_same_lines_read_as_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The counterfactual, so the test above is not passing for an unrelated reason."""
    entry, _sibling, lines = _sibling_lines(30)
    _fake_git(monkeypatch, entry, lines, family=False)
    assert DRIVER._content_landed("deadbeef") is False, (
        "these lines were supposed to be absent from the entry point itself; the fixture is not "
        "exercising the family lookup and the sibling test proves nothing"
    )


def test_a_small_diff_still_refuses_to_guess(monkeypatch: pytest.MonkeyPatch) -> None:
    """The twenty-line floor survives the change: below it, 'landed' cannot be told from luck."""
    entry, _sibling, lines = _sibling_lines(30)
    _fake_git(monkeypatch, entry, lines[:5], family=True)
    assert DRIVER._content_landed("deadbeef") is False


def test_unrelated_lines_are_not_landed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Widening the search must not make everything look present."""
    entry, _sibling, _lines = _sibling_lines(1)
    invented = [
        f"    invented_symbol_{i} = 'not in this repository at all'" for i in range(30)
    ]
    _fake_git(monkeypatch, entry, invented, family=True)
    assert DRIVER._content_landed("deadbeef") is False

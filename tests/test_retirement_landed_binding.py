"""A unit that passed adversarial review and whose work is in HEAD must be able to retire.

THE DEFECT, measured 31 August 2026 against the live `.harness/driver-state.json`. Twenty-six of
147 units hold a SOUND verdict in `review_results`, are flagged verified, and sit in neither
`done` nor `force_done` -- 18% of the plan, reviewed and unbankable. Both branches of
`retired_units` ask about the unit's own diff and both need a stored record of it. Twenty-five of
the twenty-six have no `deliverable`: fourteen earned their verdict before ADR-0109 existed, and
eleven got an empty one because 92 of 138 unit worktrees no longer resolve `rev-parse HEAD`, and
that worktree is the only place the fingerprint is captured. It cannot be captured for them now.

So the fallback decided them, and the fallback re-derives `artefact_identity` from HEAD: it hashes
every blob the unit CLAIMS, so any other unit editing a shared file silently voids a standing SOUND
verdict. `events.py` is claimed by 41 units [measured 31 August 2026]. Z02 is the worked example -- four SOUND verdicts over
four distinct artefacts, none of which retired it, until it produced a DEFECTIVE and escalated at
three attempts. The system spent four successful reviews and then punished the unit for continuing.

The rung added here asks git rather than asking stored state, using the predicate this driver
already trusts for the same question elsewhere. Two properties are load-bearing and both have a
test below:

  * It is ADDITIVE. Eleven of the twelve units done on 31 August retire through `artefact_identity`
    and FIVE of those fail the rung added here, so replacing that branch rather than appending to
    it would un-retire five finished units. Retirement may only ever grow.
  * It refuses AMBIGUITY. A subject is not identity -- 133 commits share W07's plan subject, 114
    share X01's, and K02's subject is a strict prefix of AX's -- and `review_results` records no
    timestamp, so nothing in stored state can say which same-subject commit the reviewer read.
    F04 is why that matters: its SOUND verdict carries zero findings and its work was reverted by
    `9531c10`, 41 of its 48 added lines absent from HEAD.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from tests.build_driver_helpers import ROOT, _load_driver

DRIVER = _load_driver()
PKG = Path("src/consilient")
SUBJECT = "feat(events): a subject the plan names"


def _sibling_lines(count: int) -> tuple[str, list[str]]:
    """Real lines that live ONLY in a split sibling of a real entry point.

    The same fixture shape as `test_content_landed_families.py`, for the same reason: a fixture
    of invented strings would pass with or without the family lookup and prove nothing.
    """
    entry, sibling = PKG / "events.py", PKG / "events_kinds.py"
    facade = {
        ln.rstrip() for ln in (ROOT / entry).read_text(encoding="utf-8").splitlines()
    }
    picked = []
    for raw in (ROOT / sibling).read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if len(line.strip()) > 25 and line not in facade:
            picked.append(line)
        if len(picked) == count:
            break
    assert len(picked) == count, "not enough sibling-only lines to build the fixture"
    return entry.as_posix(), picked


def _fake_git(
    monkeypatch: pytest.MonkeyPatch, path: str, lines: list[str], *, log: list[str]
) -> None:
    """Answer the four git calls `retired_units` makes, and nothing else.

    `git rev-parse HEAD:<path>` fails deliberately, so `artefact_identity` returns None and the
    unit falls through to the rung under test rather than retiring on the branch above it.
    """
    diff = "\n".join([f"+++ b/{path}"] + [f"+{line}" for line in lines])

    def fake_sh(args: list[str], **_kw: object) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "log"]:
            return subprocess.CompletedProcess(args, 0, "\n".join(log), "")
        if args[:3] == ["git", "show", "--format="]:
            return subprocess.CompletedProcess(args, 0, diff, "")
        if args[:2] == ["git", "rev-parse"]:
            return subprocess.CompletedProcess(args, 1, "", "no such path")
        if len(args) == 3 and args[:2] == ["git", "show"]:
            target = ROOT / args[2].removeprefix("HEAD:")
            blob = target.read_text(encoding="utf-8") if target.is_file() else ""
            return subprocess.CompletedProcess(args, 0, blob, "")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(DRIVER, "sh", fake_sh)


def _state() -> dict[str, object]:
    return {"review_results": {"U": {"outcome": "SOUND", "attempt": 1, "findings": []}}}


def _units() -> dict[str, dict[str, object]]:
    return {"U": {"commit": SUBJECT, "claims": [(PKG / "events.py").as_posix()]}}


def test_a_stranded_sound_verdict_retires_on_the_commit_the_plan_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry, lines = _sibling_lines(30)
    _fake_git(monkeypatch, entry, lines, log=[f"aaaaaaa {SUBJECT} (U)"])
    assert DRIVER.retired_units(_state(), _units()) == {"U"}, (
        "a unit that passed adversarial review, with no stored fingerprint and no surviving "
        "worktree, and whose added lines are in HEAD, still could not retire -- the 26-unit defect"
    )


def test_it_refuses_a_unit_whose_work_is_not_in_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F04's shape: SOUND, zero findings, and the work reverted out of the tree."""
    entry, _ = _sibling_lines(1)
    gone = [
        f"    withdrawn_symbol_{i} = 'reverted out of this repository'"
        for i in range(30)
    ]
    _fake_git(monkeypatch, entry, gone, log=[f"aaaaaaa {SUBJECT} (U)"])
    assert DRIVER.retired_units(_state(), _units()) == set(), (
        "a SOUND verdict retired a unit whose added lines are absent from HEAD. F04 is exactly "
        "this and it is live: commit 9531c10 reverted it, 41 of its 48 lines are gone, and the "
        "verdict records zero findings. Retiring here certifies code that is not shipped"
    )


def test_it_refuses_when_the_plan_subject_names_more_than_one_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Identical content to the positive test; only the log is ambiguous.

    So this can only fail because the ambiguity guard went, never because the content check did.
    """
    entry, lines = _sibling_lines(30)
    _fake_git(
        monkeypatch,
        entry,
        lines,
        log=[f"aaaaaaa {SUBJECT} (U)", f"bbbbbbb {SUBJECT} (U, second attempt)"],
    )
    assert DRIVER.retired_units(_state(), _units()) == set(), (
        "two commits share this plan subject and the unit retired anyway. Nothing in stored "
        "state says which one the reviewer was handed -- `review_results` has no timestamp -- so "
        "this retires on a union that may include attempts no reviewer read, or, where one "
        "subject is a prefix of another (K02 and AX), on a different unit's work entirely"
    )


def test_deliverable_present_searches_the_family_not_only_the_claimed_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The primary ADR-0109 path had the split-family bug `_content_landed` had already fixed.

    Measured 31 August 2026: Z01's stored deliverable reads 3.73% present at its claimed paths and
    89.44% across their families, because the 28 August refactor left the claim naming a facade.
    """
    entry, lines = _sibling_lines(30)
    _fake_git(monkeypatch, entry, lines, log=[])
    deliverable = {
        entry: [hashlib.sha256(ln.encode("utf-8")).hexdigest()[:16] for ln in lines]
    }
    assert DRIVER.deliverable_present(deliverable) is True, (
        "a deliverable whose lines moved into a split sibling read as absent, so the ADR-0109 "
        "primary path can never retire the unit however completely its work is in the tree"
    )

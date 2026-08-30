"""A rejected artefact does not re-enter the review queue by way of the conflict path.

MEASURED 30 August 2026. `retest_conflicts` re-added a unit to `built` whenever its added
lines were found in HEAD. Content being in HEAD means the work MERGED; it says nothing about
whether a review accepted it. Since a DEFECTIVE verdict removes a unit from `built` and
records the rejected artefact, and `built` is what makes a unit a REVIEW candidate, the unit
was queued for review again against the identical artefact and again returned DEFECTIVE.

W01 took 7 verdicts over 2 distinct artefacts -- the last six all f0083e6ec527 -- BJ 5 over 2,
W07 10 over 4. Each repeat spent a full workspace clone to re-derive a verdict already on
file, and each ended in a "reached 3 attempts" escalation no repair could clear, because a
unit sitting in `built` is never a build candidate and its repair brief is never dispatched.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.build_driver_helpers import _load_driver

DRIVER = _load_driver()


def _state(uid: str, *, rejected: bool) -> dict[str, Any]:
    state: dict[str, Any] = {
        "conflicts": {uid: "CONFLICT cherry-picking deadbeef for " + uid},
        "built": [],
        "resolve_dispatched": [],
        "rejected_artefacts": {uid: "aaaa1111"} if rejected else {},
        "repair_findings": {uid: ["a real finding"]} if rejected else {},
    }
    return state


def _drive(
    monkeypatch: pytest.MonkeyPatch, state: dict[str, Any], uid: str
) -> None:
    """Run retest_conflicts with the git layer stubbed to report 'already landed'."""

    class _R:
        returncode = 1
        stdout = "head\n"
        stderr = ""

    monkeypatch.setattr(DRIVER, "sh", lambda *a, **k: _R())
    monkeypatch.setattr(DRIVER, "_unit_own_shas", lambda *a, **k: ("head", ["s"], ["f"]))
    monkeypatch.setattr(DRIVER, "_content_landed", lambda _own: True)
    DRIVER.retest_conflicts(state)


def test_a_rejected_artefact_does_not_re_enter_the_review_queue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _state("U01", rejected=True)
    _drive(monkeypatch, state, "U01")
    assert "U01" not in state["built"], (
        "a unit whose artefact a review rejected was put back into `built`, so the identical "
        "artefact will be reviewed again -- the loop that drove W01 to seven verdicts on one "
        "hash and escalated it with an undispatchable repair brief"
    )
    assert "U01" not in state["conflicts"], "the conflict should still clear"


def test_an_unrejected_landed_unit_still_retires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The path must keep working for the case it exists to serve."""
    state = _state("U02", rejected=False)
    _drive(monkeypatch, state, "U02")
    assert "U02" in state["built"], (
        "a landed unit with no rejection must still enter `built` and retire; without this "
        "the fix would trade one stall for another"
    )

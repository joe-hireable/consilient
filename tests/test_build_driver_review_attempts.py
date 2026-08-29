"""The review budget — what spends an attempt, what refunds one, and what resets the
count.

Three attempts, then escalate to a person. That is only just if the three were spent on
the same code, judged by a reviewer that actually ran. Both halves of that condition
were violated.

DECIDED BY THE PRINCIPAL, 25 August 2026: AL, AO and AP were each escalated — "reached 3
attempts, refusing another dispatch" — while each held a different, newer artefact than
the one their three attempts had been spent against. `review_attempts` was a pure
lifetime counter, unrelated to which code was under review, so a unit rebuilt after each
genuine DEFECTIVE finding accumulated exactly as fast as one stuck reviewing the same
broken code three times over, and both landed on the identical "it needs a person"
though only the second is actually stuck. A new artefact resets the count; an unchanged
one must not, or F-05's refund of an infrastructure retry would quietly buy an extra
attempt against the same code.

The refunds are F-05 itself: an infrastructure death must not spend a retry. MEASURED 25
August 2026, ~23:30 — AL and AO, freshly reset for review, crashed on a workspace-setup
timeout (`git clone --separate-git-dir`) before a reviewer ever ran, and the crash-
handling loop refunded `state["attempts"]`, the *build* counter, unconditionally for
every crash regardless of which pool the dead run belonged to. A crash during a review
dispatch never had its review attempt refunded at all. MEASURED 26 August 2026:
`_INFRASTRUCTURE_LOSS` then turned out to refund only two of the six outcomes that
`clear_stale_review_memos`'s own docstring names as infrastructure losses — AC's
DEFECTIVE receipt arrived after `dispatch_failed` had already been recorded, and AT's
SOUND was lost to a WSL path-translation failure and recorded as `no_receipt_file`.
Neither is evidence about the code.

The clearing routines repair the damage those left standing: A01, AB and AC each had a
real SOUND or DEFECTIVE receipt on disk made unreachable by a non-terminal memo frozen
on their (attempt, artefact) pair, and AC, AT and B01 each reached the cap entirely on
infrastructure losses against an unchanged artefact while AJ and AP were genuinely
escalated and must be left alone. Both routines run every tick, so both must be no-ops
once nothing is stale."""

from pathlib import Path
from build_driver_helpers import (
    _load_driver,
)


def test_review_cap_refuses_a_fourth_dispatch_and_escalates_once() -> None:
    """A review that has used its three permitted attempts may not launch again."""
    driver = _load_driver()
    state: dict[str, object] = {"review_attempts": {"U01": 3}}

    assert driver.review_dispatch_allowed(state, "U01") is False
    assert driver.review_dispatch_allowed(state, "U01") is False
    assert state["review_attempts"] == {"U01": 3}
    assert state["review_escalated"] == ["U01"]


def test_clear_stale_review_memos_recovers_units_stuck_by_the_old_semantics(
    tmp_path: Path,
) -> None:
    """The one-time migration for memos written before outcome-gating existed. A01, AB and AC
    were exactly this: a real SOUND/DEFECTIVE receipt sat on disk, unreachable because a
    non-terminal memo from an earlier tick had already frozen their (attempt, artefact) pair."""
    driver = _load_driver()
    state: dict[str, object] = {
        "review_consumed": {
            "A01": {"attempt": 1, "artefact": "a" * 64},  # stuck: non-terminal
            "AF": {
                "attempt": 1,
                "artefact": "f" * 64,
            },  # correctly terminal, must survive
            "GONE": {
                "attempt": 1,
                "artefact": "g" * 64,
            },  # not a real unit; must not be re-queued
        },
        "review_results": {
            "A01": {"outcome": "no_dispatch"},
            "AF": {"outcome": "SOUND"},
            "GONE": {"outcome": "no_dispatch"},
        },
        "review_dispatched": [],
    }
    units = {"A01": {"claims": []}, "AF": {"claims": []}}

    cleared = driver.clear_stale_review_memos(state, units)

    assert sorted(cleared) == ["A01", "GONE"]
    assert "A01" not in state["review_consumed"]
    assert "A01" in state["review_dispatched"], (
        "must be re-queued so it is looked at again"
    )
    assert "AF" in state["review_consumed"], "a terminal memo must not be disturbed"
    assert "AF" not in state["review_dispatched"], (
        "a correctly-consumed unit is not re-queued"
    )
    assert "GONE" not in state["review_dispatched"], (
        "a uid absent from the plan must not be queued for review"
    )


def test_clear_stale_review_memos_is_a_no_op_once_nothing_is_stale(
    tmp_path: Path,
) -> None:
    """Safe to run every tick: once every memo is terminal, this changes nothing."""
    driver = _load_driver()
    state: dict[str, object] = {
        "review_consumed": {"AF": {"attempt": 1, "artefact": "f" * 64}},
        "review_results": {"AF": {"outcome": "SOUND"}},
        "review_dispatched": [],
    }
    units = {"AF": {"claims": []}}
    assert driver.clear_stale_review_memos(state, units) == []
    assert state["review_consumed"] == {"AF": {"attempt": 1, "artefact": "f" * 64}}
    assert state["review_dispatched"] == []


def test_a_rebuilt_unit_gets_a_fresh_review_budget(monkeypatch) -> None:
    """DECIDED BY THE PRINCIPAL, 25 August 2026: AL, AO and AP were each escalated -- "reached
    3 attempts, refusing another dispatch" -- while each held a DIFFERENT, newer artefact than
    the one their three attempts had actually been spent against. `review_attempts` was a pure
    LIFETIME counter, unrelated to which code was under review: a unit rebuilt after a genuine
    DEFECTIVE finding, each time addressing what the review found, accumulated exactly as fast
    as one stuck reviewing the SAME broken code three times over -- and both landed on the
    identical "it needs a person," even though only the second is actually stuck.
    """
    driver = _load_driver()
    old_artefact = "a" * 64
    new_artefact = "b" * 64
    state: dict[str, object] = {
        "review_attempts": {"U01": 3},
        "review_escalated": ["U01"],
        "review_expected": {"U01": {"artefact": old_artefact, "attempt": 3}},
    }
    assert driver.review_dispatch_allowed(state, "U01") is False, (
        "sanity: three attempts against the old artefact must still be escalated"
    )

    changed = driver.reset_review_attempts_on_new_artefact(state, "U01", new_artefact)
    assert changed is True
    assert state["review_attempts"]["U01"] == 0
    assert "U01" not in state["review_escalated"]
    assert driver.review_dispatch_allowed(state, "U01") is True, (
        "a rebuilt unit's new code must be reviewable again"
    )


def test_reset_is_a_no_op_when_the_artefact_has_not_changed(monkeypatch) -> None:
    """The other half: F-05 refunds an infrastructure-loss retry WITHOUT changing
    `review_expected`, and three genuine attempts against the SAME code must still escalate."""
    driver = _load_driver()
    artefact = "c" * 64
    state: dict[str, object] = {
        "review_attempts": {"U01": 3},
        "review_escalated": ["U01"],
        "review_expected": {"U01": {"artefact": artefact, "attempt": 3}},
    }
    changed = driver.reset_review_attempts_on_new_artefact(state, "U01", artefact)
    assert changed is False
    assert state["review_attempts"]["U01"] == 3
    assert "U01" in state["review_escalated"]


def test_reset_does_nothing_for_a_unit_never_dispatched_before(monkeypatch) -> None:
    """No `review_expected` entry yet -- a first-ever dispatch -- must not be treated as a
    reset event (nothing to report, nothing to change)."""
    driver = _load_driver()
    state: dict[str, object] = {"review_expected": {}}
    assert driver.reset_review_attempts_on_new_artefact(state, "U01", "x" * 64) is False
    assert state.get("review_attempts", {}).get("U01") is None


def test_a_crash_during_review_dispatch_refunds_the_review_attempt(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 25 August 2026, ~23:30: AL and AO, freshly reset for review, crashed on a
    workspace-setup timeout (`git clone --separate-git-dir`) before a reviewer ever ran. The
    crash-handling loop refunded `state["attempts"]` -- the BUILD counter -- unconditionally,
    for every crash, regardless of whether the dead run belonged to the build pool or the
    review pool. A crash during a REVIEW dispatch never had its review attempt refunded at
    all: F-05 says an infrastructure death must not spend a retry, and this path was spending
    one silently.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    (briefs / "U01.err").write_text("boom\n", encoding="utf-8")
    monkeypatch.setattr(
        driver, "crashed_dispatches", lambda _state: [("U01", "boom", False)]
    )
    monkeypatch.setattr(driver, "record_restart", lambda *_a, **_k: False)
    monkeypatch.setattr(driver, "release_dead_claims", lambda _uids: 0)
    monkeypatch.setattr(driver, "quarantine_unit", lambda *_a, **_k: False)

    state: dict[str, object] = {
        "in_flight": {},
        "review_dispatched": ["U01"],
        "review_attempts": {"U01": 2},
        "attempts": {"U01": 5},
        "crash_history": {},
    }
    driver._handle_crashed_dispatches(state)

    assert state["review_attempts"]["U01"] == 1, "the REVIEW attempt must be refunded"
    assert state["attempts"]["U01"] == 5, (
        "the unrelated BUILD counter must be untouched"
    )
    assert "U01" not in state["review_dispatched"]


def test_a_crash_during_build_dispatch_still_refunds_the_build_attempt(
    tmp_path: Path, monkeypatch
) -> None:
    """The other half: a crash while a unit is being BUILT must keep refunding the build
    counter exactly as before -- this fix must not touch that path."""
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    (briefs / "U02.err").write_text("boom\n", encoding="utf-8")
    monkeypatch.setattr(
        driver, "crashed_dispatches", lambda _state: [("U02", "boom", False)]
    )
    monkeypatch.setattr(driver, "record_restart", lambda *_a, **_k: False)
    monkeypatch.setattr(driver, "release_dead_claims", lambda _uids: 0)
    monkeypatch.setattr(driver, "quarantine_unit", lambda *_a, **_k: False)

    state: dict[str, object] = {
        "in_flight": {"U02": (0.0, 0.0)},
        "review_dispatched": [],
        "review_attempts": {},
        "attempts": {"U02": 3},
        "crash_history": {},
    }
    driver._handle_crashed_dispatches(state)

    assert state["attempts"]["U02"] == 2, "the BUILD attempt must still be refunded"
    assert "U02" not in state["in_flight"]


def test_every_documented_infrastructure_loss_refunds_the_review_attempt(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 26 August 2026: `_INFRASTRUCTURE_LOSS` only ever refunded two of the six
    outcomes `clear_stale_review_memos`'s own docstring names as infrastructure losses.
    Two live units (AC, AT) had a real verdict silently orphaned this way: AC's DEFECTIVE
    receipt arrived after the driver had already recorded `dispatch_failed`; AT's SOUND
    was lost to a WSL path-translation failure and recorded as `no_receipt_file`. Neither
    is evidence about the code -- F-05 says an infrastructure death must not spend a retry,
    for all six outcomes it names, not just two.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    monkeypatch.setattr(driver, "append_review_outcome", lambda _record: None)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: "z" * 64)

    unit = {"claims": ["a.py"]}
    cases = {
        "U_FAILED": ("status: failed\n", None),
        "U_NORECEIPT": ("status: ok\n", None),
        "U_UNPARSEABLE": ("status: ok\n", "not json"),
        "U_MISMATCHED": (
            "status: ok\n",
            '{"v": 1, "unit": "WRONG", "artefact": "%s", "attempt": 1, '
            '"verdict": "SOUND", "findings": []}' % ("z" * 64),
        ),
    }
    for uid, (envelope, verdict_body) in cases.items():
        (briefs / f"{uid}-verify.out").write_text(envelope, encoding="utf-8")
        if verdict_body is not None:
            (briefs / f"{uid}-verdict.json").write_text(verdict_body, encoding="utf-8")
        state: dict[str, object] = {
            "review_expected": {uid: {"attempt": 1, "artefact": "z" * 64}},
            "review_attempts": {uid: 2},
        }
        outcome = driver.consume_review_verdict(state, uid, unit)
        assert outcome in (
            "dispatch_failed",
            "no_receipt_file",
            "receipt_unparseable",
            "receipt_mismatched",
        ), f"{uid}: unexpected outcome {outcome!r}"
        assert state["review_attempts"][uid] == 1, (
            f"{uid}: outcome {outcome!r} must refund the review attempt, not spend it"
        )


def test_clear_unjustly_escalated_reviews_frees_the_three_named_units() -> None:
    """MEASURED 26 August 2026: AC, AT and B01 each reached the 3-attempt cap entirely on
    infrastructure losses (a late-arriving receipt, a WSL path-translation failure, a dead
    dispatch) against an unchanged artefact -- not a genuine repeated defect. Un-escalating
    them gives each a fresh, real review rather than leaving a code bug's damage standing.
    """
    driver = _load_driver()
    state: dict[str, object] = {
        "review_escalated": ["AC", "AT", "B01", "AJ", "AP"],
        "review_attempts": {"AC": 3, "AT": 3, "B01": 3, "AJ": 3, "AP": 3},
    }
    cleared = driver.clear_unjustly_escalated_reviews(state)

    assert sorted(cleared) == ["AC", "AT", "B01"]
    for uid in ("AC", "AT", "B01"):
        assert uid not in state["review_escalated"]
        assert state["review_attempts"][uid] == 0
    for uid in ("AJ", "AP"):
        assert uid in state["review_escalated"], (
            "genuinely escalated units must be untouched"
        )
        assert state["review_attempts"][uid] == 3


def test_clear_unjustly_escalated_reviews_is_a_no_op_once_cleared() -> None:
    driver = _load_driver()
    state: dict[str, object] = {"review_escalated": [], "review_attempts": {}}
    assert driver.clear_unjustly_escalated_reviews(state) == []
    assert state["review_escalated"] == []

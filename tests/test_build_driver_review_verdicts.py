"""What counts as a verdict about this code, and what counts as the review having
finished.

Two files carry a review: `<uid>-verify.out` is the dispatch envelope, and
`<uid>-verdict.json` is what the reviewer actually wrote. Almost every failure recorded
here came from confusing the two, or from binding a verdict to the wrong thing.

MEASURED 25 August 2026: nine of the ten most recent receipts were discarded, several
with the artefact matching exactly and only the attempt counter differing — AL at 2
against an expected 3, AO at 1 against 2. A review takes about twenty minutes, the
driver re-dispatches sooner, and the original agent's valid verdict arrives one attempt
behind and is refused; nothing could be verified while agents worked continuously. The
attempt number says which dispatch spoke; the artefact says what was judged. A verdict
about different code is still refused, whatever its attempt number, and so is one whose
expectation the tree has moved out from under.

MEASURED the same evening, 21:50 — why the day produced so few verdicts. AE and AA both
held well-formed receipts bound to their unit's current artefact, and
`_load_verdict_file` returned SOUND and DEFECTIVE for them when called directly. Both
sat unconsumed because the envelope was zero bytes. A finished review with a valid
verdict was ignored because a different file was empty; the envelope can be truncated by
a re-dispatch, or never written if the wrapper died after the reviewer had already
produced its verdict.

MEASURED at ~23:00, a regression inside that very fix: `open(path, "w")` truncates the
envelope the instant a re-dispatch launches, but nothing clears the old `verdict.json`
from the attempt before, so a naive "the receipt exists" check fired before the new
review had produced anything — A01, AB and AC each hit this, and the resulting
`no_dispatch` was memoised permanently. A receipt only proves *this* review finished if
its own unit, attempt and artefact match what the driver currently expects. And MEASURED
at ~23:15, from the trajectory itself: A01 shows `attempt=1 artefact=6e826...
outcome=no_dispatch` and that pair was never looked at again, because the memo used to
be written for every outcome while F-05 refunds an infrastructure loss's counter, so the
retry reused the identical pair. Only a terminal outcome is remembered — SOUND and
DEFECTIVE still must be, or a re-dispatch double-applies a real verdict."""

import json
from pathlib import Path
from build_driver_helpers import (
    _load_driver,
)


def _verdict_fixture(
    tmp_path,
    monkeypatch,
    *,
    receipt_attempt,
    expected_attempt,
    receipt_artefact,
    expected_artefact,
    current_artefact,
    verdict="SOUND",
    findings=None,
):
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: current_artefact)
    (briefs / "U01-verdict.json").write_text(
        json.dumps(
            {
                "v": 1,
                "unit": "U01",
                "artefact": receipt_artefact,
                "attempt": receipt_attempt,
                "verdict": verdict,
                "findings": findings if findings is not None else [],
            }
        ),
        encoding="utf-8",
    )
    expected = {"artefact": expected_artefact, "attempt": expected_attempt}
    return driver._load_verdict_file("U01", {"claims": ["a.py"]}, expected)


def test_a_verdict_about_the_current_artefact_survives_a_stale_attempt_number(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 25 August 2026: nine of the ten most recent receipts were discarded, several with
    the artefact matching EXACTLY and only the attempt counter differing -- AL at 2 against an
    expected 3, AO at 1 against 2. A review takes ~20 minutes, the driver re-dispatches sooner,
    and the original agent's valid verdict arrives one attempt behind and is refused. Nothing
    could be verified while agents worked continuously.

    The attempt number says which dispatch spoke. The artefact says what was judged.
    """
    outcome, _ = _verdict_fixture(
        tmp_path,
        monkeypatch,
        receipt_attempt=2,
        expected_attempt=3,
        receipt_artefact="a" * 64,
        expected_artefact="a" * 64,
        current_artefact="a" * 64,
    )
    assert outcome == "SOUND", (
        "a verdict about the current artefact must not be lost to a counter"
    )


def test_a_verdict_about_a_different_artefact_is_still_refused(
    tmp_path: Path, monkeypatch
) -> None:
    """The binding that matters is unchanged: a verdict about other code is not evidence about
    this code, whatever its attempt number says."""
    outcome, _ = _verdict_fixture(
        tmp_path,
        monkeypatch,
        receipt_attempt=3,
        expected_attempt=3,
        receipt_artefact="b" * 64,
        expected_artefact="a" * 64,
        current_artefact="a" * 64,
    )
    assert outcome == "receipt_mismatched"


def test_a_verdict_is_refused_when_the_tree_has_moved_under_the_expectation(
    tmp_path: Path, monkeypatch
) -> None:
    """Both sides are still checked. If the unit's identity re-derived from the tree no longer
    equals what the review was told to judge, the verdict is stale and refused."""
    outcome, _ = _verdict_fixture(
        tmp_path,
        monkeypatch,
        receipt_attempt=3,
        expected_attempt=3,
        receipt_artefact="a" * 64,
        expected_artefact="a" * 64,
        current_artefact="c" * 64,
    )
    assert outcome == "receipt_mismatched"


def test_a_valid_verdict_receipt_is_consumed_even_with_an_empty_envelope(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 25 August 2026, 21:50 -- why the day produced so few verdicts.

    AE and AA both held well-formed `<uid>-verdict.json` receipts bound to their unit's CURRENT
    artefact; the driver's own `_load_verdict_file` returned SOUND and DEFECTIVE for them when
    called directly. Both sat unconsumed because `<uid>-verify.out` was ZERO BYTES. A finished
    review with a valid verdict was ignored because a DIFFERENT file was empty.

    The `.out` is the dispatch envelope; the verdict is what the reviewer wrote. The envelope can
    be truncated by a re-dispatch or never written if the wrapper died after the reviewer had
    already produced its verdict.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)

    artefact = "d" * 64
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: artefact)
    (briefs / "U01-verify.out").write_text("", encoding="utf-8")  # the empty envelope
    (briefs / "U01-verdict.json").write_text(
        json.dumps(
            {
                "v": 1,
                "unit": "U01",
                "artefact": artefact,
                "attempt": 1,
                "verdict": "SOUND",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )

    outcome, _findings = driver._load_verdict_file(
        "U01", {"claims": ["a.py"]}, {"artefact": artefact, "attempt": 1}
    )
    assert outcome == "SOUND"

    # The completion gate itself: an empty envelope must not hide a present, BOUND receipt.
    # (Superseded assertion once here checked for a literal source string; that string moved
    # when the gate was extracted into `review_receipt_is_finished` to fix the stale-receipt
    # regression below, so this now calls the real function instead of grepping for its shape.)
    assert (briefs / "U01-verify.out").stat().st_size == 0
    assert (briefs / "U01-verdict.json").stat().st_size > 0
    assert (
        driver.review_receipt_is_finished("U01", {"artefact": artefact, "attempt": 1})
        is True
    )


def test_a_stale_verdict_receipt_from_a_prior_attempt_is_not_evidence_this_one_finished(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 25 August 2026, ~23:00 -- a REGRESSION in the very fix that let a receipt count
    as completion evidence. `open(path, "w")` truncates `.out` to 0 bytes the instant a
    re-dispatch launches, but nothing clears the OLD `<uid>-verdict.json` from the attempt
    before. A01, AB and AC were each re-dispatched at a fresh attempt after their artefact
    changed; their stale verdict.json (wrong attempt/artefact) still had bytes in it, so the
    naive "verdict.json exists" check fired immediately -- before the new review had produced
    anything -- and the resulting `no_dispatch` was memoised PERMANENTLY. The real verdict,
    written minutes later, was never looked at again.

    A verdict.json only counts as evidence THIS review finished if its own (unit, attempt,
    artefact) matches what the driver currently expects.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)

    (briefs / "U01-verify.out").write_text(
        "", encoding="utf-8"
    )  # freshly truncated by re-dispatch
    (briefs / "U01-verdict.json").write_text(
        json.dumps(
            {
                "v": 1,
                "unit": "U01",
                "artefact": "OLD" + "a" * 61,
                "attempt": 1,
                "verdict": "SOUND",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )

    current_expectation = {"artefact": "NEW" + "b" * 61, "attempt": 2}
    assert driver.review_receipt_is_finished("U01", current_expectation) is False, (
        "a verdict.json from a DIFFERENT attempt/artefact must not count as this review "
        "having finished"
    )


def test_a_verdict_receipt_matching_the_current_attempt_still_counts_as_finished(
    tmp_path: Path, monkeypatch
) -> None:
    """The case `review_receipt_is_finished` exists to preserve: an empty envelope must not
    hide a genuinely current, valid verdict (the original AE/AA fix)."""
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)

    (briefs / "U01-verify.out").write_text("", encoding="utf-8")
    artefact = "c" * 64
    (briefs / "U01-verdict.json").write_text(
        json.dumps(
            {
                "v": 1,
                "unit": "U01",
                "artefact": artefact,
                "attempt": 1,
                "verdict": "SOUND",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )

    assert (
        driver.review_receipt_is_finished("U01", {"artefact": artefact, "attempt": 1})
        is True
    )


def test_a_non_empty_envelope_counts_as_finished_regardless_of_the_receipt(
    tmp_path: Path, monkeypatch
) -> None:
    """The other half: a real, completed envelope is proof enough on its own, whatever state
    the verdict.json is in -- including absent."""
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)

    (briefs / "U01-verify.out").write_text("status: ok\n", encoding="utf-8")
    assert (
        driver.review_receipt_is_finished("U01", {"artefact": "x", "attempt": 1})
        is True
    )


def test_neither_file_present_is_not_finished(tmp_path: Path, monkeypatch) -> None:
    """The ordinary, most common state: a review genuinely still running. Must not be treated
    as finished, or its eventual real verdict is exposed to the same permanent-memo hazard."""
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    assert (
        driver.review_receipt_is_finished("U01", {"artefact": "x", "attempt": 1})
        is False
    )


def test_consume_review_verdict_only_memoises_a_terminal_outcome(
    tmp_path: Path, monkeypatch
) -> None:
    """MEASURED 25 August 2026, ~23:15, from the trajectory itself: A01's history shows
    `attempt=1 artefact=6e826... outcome=no_dispatch`, and the SAME (attempt, artefact) pair
    was never looked at again -- because the memo used to be written for EVERY outcome, and
    F-05 refunds an infrastructure loss's attempt counter so a retry reuses the identical pair.

    SOUND and DEFECTIVE must still be remembered, so a re-dispatch under the same pair cannot
    double-apply a real verdict.
    """
    driver = _load_driver()
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    monkeypatch.setattr(driver, "BRIEFS", briefs)
    monkeypatch.setattr(driver, "append_review_outcome", lambda _record: None)
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: None)

    unit = {"claims": ["a.py"]}

    state: dict[str, object] = {
        "review_expected": {"U01": {"attempt": 1, "artefact": "x" * 64}}
    }
    driver.consume_review_verdict(state, "U01", unit)  # no files -> no_dispatch
    assert state["review_results"]["U01"]["outcome"] == "no_dispatch"
    assert "U01" not in state.get("review_consumed", {}), (
        "a non-terminal outcome must not be memoised"
    )

    artefact = "y" * 64
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: artefact)
    (briefs / "U02-verdict.json").write_text(
        json.dumps(
            {
                "v": 1,
                "unit": "U02",
                "artefact": artefact,
                "attempt": 1,
                "verdict": "SOUND",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    state2: dict[str, object] = {
        "review_expected": {"U02": {"attempt": 1, "artefact": artefact}}
    }
    driver.consume_review_verdict(state2, "U02", unit)
    assert state2["review_results"]["U02"]["outcome"] == "SOUND"
    assert state2["review_consumed"]["U02"] == {"attempt": 1, "artefact": artefact}, (
        "a terminal SOUND outcome must still be memoised"
    )

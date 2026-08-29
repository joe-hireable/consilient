"""Does a standing judgement still apply to the artefact it was earned against?

One predicate underlies every check here — has this unit's own work landed, or moved, or
gone — and it has been wrong in both directions, expensively, with both directions
measured.

Too tight and verdicts die faster than they can be earned. MEASURED 27 August 2026:
`src/consilient/events.py` is claimed by 67 units, `projection.py` by 40, `dispatch.py`
by 32. Under blob binding, any one of those 67 landing work in events.py killed the
standing SOUND verdict of the other 66, whose own work was untouched; ten verdicts were
dead of this at once against six review slots, and the rate rises with every merge.
ADR-0109 binds a verdict to the unit's own added lines instead, and the falsifiable half
is kept beside the permissive one: if a deliverable can be deleted, reverted or gutted
by a fifth and the verdict survive, ADR-0109 is refuted and the binding goes back to
blobs. Below twenty added lines a diff cannot be told from coincidence, so such a unit
falls back to the stricter blob binding rather than being waved through on a weak signal
— and the threshold is `_content_landed`'s, deliberately, because two ways of asking
"did this work land" that disagreed about how much drift is drift would be worse than
either alone.

Too loose and merging stops. A skip added and withdrawn on 27 August 2026 used
`artefact_identity`, which answers "do these paths exist", where the question is
`_content_landed`'s, "did this work arrive". Z03 is the counterexample:
`.harness/build_loop.py` is in HEAD, Z03's changes to it are not, and all six of its
tests fail against the tree. The skip withheld a resolver from 37 of 39 conflicted units
and merging stopped dead for 47 minutes. The withdrawal is kept as a check so it cannot
come back.

Releasing an escalation is the same question asked of a finding rather than a verdict,
and it costs no review slot — no clone, no dispatch, only a hash of the claimed blobs.
It nonetheless lived inside the review DISPATCH loop, after `admit_review`'s `break`, so
with `reviews_out` at 6 against `MAX_REVIEWS` 6 the loop broke on its first iteration
and no escalation could clear however completely its defect had been repaired. BK's
verdict named a DDL-detection bypass in `check_merge_acceptance.py`; commit 6322d3b
fixed exactly that on 26 August and BK's identity moved 06d792af -> e54878b3. BK stayed
escalated. 76 units were pending review; zero were examined. The release must not become
a way out of a real, repeated finding, so an escalation on unchanged code survives, and
units that can report nothing are not hashed at all — that was 11 of 76 on the live
state, at two `git rev-parse` calls each to learn nothing."""

from driver_bulkhead_helpers import (
    _load_driver,
)


def test_an_escalation_clears_even_while_the_review_lane_is_full(monkeypatch) -> None:
    """MEASURED 27 August 2026: it did not, and that is what froze BK.

    Releasing a unit whose finding has since been fixed costs no review slot -- no clone, no
    dispatch, only a hash of the claimed blobs. But the call lived inside the review DISPATCH
    loop, after `admit_review`'s `break`. With `reviews_out` at 6 against `MAX_REVIEWS` 6, that
    loop broke on its first iteration, so no unit's artefact was recomputed and no escalation
    could clear however completely its defect had been repaired.

    BK's verdict named a DDL-detection bypass in `check_merge_acceptance.py`. Commit 6322d3b
    fixed exactly that on 26 August and BK's identity moved 06d792af -> e54878b3. BK stayed
    escalated. 76 units were pending review; zero were examined.
    """
    driver = _load_driver()
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: "new-artefact")

    state = {
        # The lane is full, exactly as it was live.
        "review_dispatched": [f"R{i}" for i in range(driver.MAX_REVIEWS)],
        "review_escalated": ["BK"],
        "review_attempts": {"BK": 3},
        "review_expected": {"BK": {"artefact": "old-artefact", "attempt": 3}},
    }
    assert not driver.admit_review(len(state["review_dispatched"])), (
        "this test is meaningless unless the lane is genuinely at ceiling"
    )

    cleared = driver.clear_escalations_whose_artefact_moved(
        state, {"BK": {"claims": ["a.py"]}}, ["BK"]
    )

    assert cleared == ["BK"], cleared
    assert "BK" not in state["review_escalated"]
    assert state["review_attempts"]["BK"] == 0


def test_an_escalation_on_unchanged_code_survives(monkeypatch) -> None:
    """The release must not become a way out of a real, repeated finding.

    Three genuine attempts against the SAME artefact is what escalation is for -- an
    infrastructure-loss retry under F-05 does not move `review_expected`, so nothing here may
    reset on it either.
    """
    driver = _load_driver()
    monkeypatch.setattr(driver, "artefact_identity", lambda _unit: "same-artefact")

    state = {
        "review_dispatched": [],
        "review_escalated": ["BK"],
        "review_attempts": {"BK": 3},
        "review_expected": {"BK": {"artefact": "same-artefact", "attempt": 3}},
    }
    cleared = driver.clear_escalations_whose_artefact_moved(
        state, {"BK": {"claims": ["a.py"]}}, ["BK"]
    )

    assert cleared == []
    assert state["review_escalated"] == ["BK"]
    assert state["review_attempts"]["BK"] == 3


def test_clearing_escalations_does_not_hash_units_it_cannot_report_on(
    monkeypatch,
) -> None:
    """`reset_review_attempts_on_new_artefact` returns False unless the unit is escalated or
    has attempts on the clock, so hashing the rest spends two `git rev-parse` calls each to
    learn nothing. On the live state that was 11 units of 76."""
    driver = _load_driver()
    hashed: list[dict] = []

    def spy(unit):
        hashed.append(unit)
        return "new-artefact"

    monkeypatch.setattr(driver, "artefact_identity", spy)
    state = {
        "review_escalated": ["BK"],
        "review_attempts": {"BK": 3, "AL": 1},
        "review_expected": {
            "BK": {"artefact": "old", "attempt": 3},
            "AL": {"artefact": "old", "attempt": 1},
        },
    }
    units = {u: {"claims": ["a.py"]} for u in ("BK", "AL", "QUIET1", "QUIET2")}

    driver.clear_escalations_whose_artefact_moved(
        state, units, ["BK", "AL", "QUIET1", "QUIET2"]
    )

    assert len(hashed) == 2, (
        f"hashed {len(hashed)} units; only BK and AL can report anything"
    )


def test_a_conflict_that_survived_the_retest_still_gets_a_resolver() -> None:
    """WITHDRAWAL of the skip added earlier today, recorded as a test so it cannot come back.

    That change skipped the resolver for any conflicted unit whose every CLAIMED PATH resolved in
    HEAD. The predicate was wrong and the driver already held the right one: `artefact_identity`
    answers "do these paths exist", not "did this work arrive", and Z03 is the counterexample --
    `.harness/build_loop.py` is in HEAD, Z03's changes to it are not, and all six of its tests fail
    against the tree.

    `_content_landed` is the real question, and `retest_conflicts` asks it every tick and pops the
    conflict when it is true. So a unit still in `conflicts` after the retest has content that is
    NOT in HEAD, by construction, and needs resolving. The skip withheld a resolver from 37 of 39
    such units and merging stopped dead for 47 minutes. [measured 27 August 2026]
    """
    import inspect

    driver = _load_driver()
    assert not hasattr(driver, "resolver_can_change_nothing"), (
        "the withdrawn predicate is back; read the comment where it used to live"
    )
    source = inspect.getsource(driver.main)
    assert "already_present" not in source, (
        "the skip's accumulator survived the withdrawal"
    )
    # The two fixes that were right are kept.
    assert "expire_finished_dispatches(" in inspect.getsource(driver), (
        "the slot reaper was lost"
    )


def _hash_lines(driver, lines):
    import hashlib

    return sorted({hashlib.sha256(ln.encode("utf-8")).hexdigest()[:16] for ln in lines})


def test_a_verdict_survives_an_unrelated_edit_to_a_shared_file(
    tmp_path, monkeypatch
) -> None:
    """ADR-0109. The claim, and it is falsifiable: binding a verdict to the unit's own added lines
    rather than to every claimed blob does NOT admit a unit whose deliverable has been broken.

    MEASURED 27 August 2026: `src/consilient/events.py` is claimed by 67 units, `projection.py` by
    40, `dispatch.py` by 32. Under blob binding, any one of those 67 landing work in events.py
    killed the standing SOUND verdict of the other 66 -- whose own work was untouched. Ten
    verdicts were dead of this at once against six review slots, and the rate rises with every
    merge, so verdicts were being invalidated faster than they could be earned.

    This half of the claim: an unrelated edit must NOT invalidate. The other half is the next
    test, and it is the one that matters for beta.
    """
    driver = _load_driver()
    ours = [f"    unit_line_{i} = {i}" for i in range(30)]
    theirs = [f"    someone_elses_line_{i} = {i}" for i in range(40)]

    class _R:
        def __init__(self, out):
            self.stdout, self.stderr, self.returncode = out, "", 0

    # HEAD holds our thirty lines PLUS forty someone else added afterwards.
    monkeypatch.setattr(driver, "sh", lambda a, **k: _R(chr(10).join(ours + theirs)))
    fingerprint = {"src/consilient/events.py": _hash_lines(driver, ours)}

    assert driver.deliverable_present(fingerprint) is True, (
        "an unrelated edit to a shared file invalidated a verdict about work it never touched"
    )


def test_a_verdict_dies_when_the_units_own_work_is_removed(
    tmp_path, monkeypatch
) -> None:
    """The half that protects beta. A looser binding is only defensible if it still catches the
    case it exists to catch: the unit's own deliverable being deleted or rewritten.

    If this ever passes wrongly, ADR-0109 is refuted and the binding must go back to blobs.
    """
    driver = _load_driver()
    ours = [f"    unit_line_{i} = {i}" for i in range(30)]

    class _R:
        def __init__(self, out):
            self.stdout, self.stderr, self.returncode = out, "", 0

    fingerprint = {"src/consilient/events.py": _hash_lines(driver, ours)}

    # Our work is gone from HEAD; someone reverted or rewrote it.
    monkeypatch.setattr(
        driver, "sh", lambda a, **k: _R("    something_entirely_different = 1")
    )
    assert driver.deliverable_present(fingerprint) is False, (
        "a verdict survived the deletion of the very work it certified"
    )

    # And a partial gutting: 20% of the lines removed is well past the 1% tolerance.
    monkeypatch.setattr(driver, "sh", lambda a, **k: _R(chr(10).join(ours[:24])))
    assert driver.deliverable_present(fingerprint) is False, (
        "a verdict survived a fifth of its deliverable being removed"
    )


def test_a_diff_too_small_to_identify_falls_back_to_blob_binding() -> None:
    """Below twenty added lines a diff cannot be told from coincidence, so such a unit is NOT
    waved through on a weak signal -- it falls back to the old, stricter blob binding. The
    threshold is `_content_landed`'s, deliberately: two ways of asking "did this work land" that
    disagreed about how much drift is drift would be worse than either alone."""
    driver = _load_driver()
    assert driver.deliverable_present({"a.py": ["deadbeefdeadbeef"] * 19}) is False
    assert driver.deliverable_present(None) is False
    assert driver.deliverable_present({}) is False

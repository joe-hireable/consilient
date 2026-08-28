"""Z06: build and review lanes are independent admission pools.

The shared `MAX_CONCURRENT` pool let one lane consume the other's slots. That
was observed live: 64 reviews in flight while builds could not start. A safety
property held only by an incidental constant is not a chokepoint — shedding is
named, per-lane, and tested here.

The lane ceilings on 25 August 2026 are 12 builds and 6 reviews. The plan
unit's 24/12 figures were the earlier restoration; a later measured knee
sat between 19 and 31 concurrent starts, and the file itself forbids raising
the caps to paper over contention. Independent pools do not require larger
ceilings.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / ".harness" / "build_driver.py"


def _load_driver():
    spec = importlib.util.spec_from_file_location("build_driver_bulkhead", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fn(name: str) -> ast.FunctionDef:
    tree = ast.parse(DRIVER.read_text(encoding="utf-8"))
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _names_in(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


def test_ceilings_are_not_raised_to_paper_over_contention() -> None:
    """More concurrency made the suite slower (degradation ~2.2 at n=9). Do not raise the caps."""
    driver = _load_driver()
    assert driver.MAX_BUILDS == 12
    assert driver.MAX_REVIEWS == 6
    assert driver.MAX_CONCURRENT == driver.MAX_BUILDS + driver.MAX_REVIEWS


def test_a_lane_at_its_ceiling_sheds_rather_than_borrowing() -> None:
    driver = _load_driver()
    assert driver.admit_review(driver.MAX_REVIEWS) is False
    assert driver.admit_review(driver.MAX_REVIEWS + 58) is False  # the live 64
    assert driver.admit_build(driver.MAX_BUILDS) is False
    assert driver.admit_build(driver.MAX_CONCURRENT) is False


def test_a_review_backlog_cannot_consume_build_slots() -> None:
    """The live failure: reviews filled the shared pool and builds could not start."""
    driver = _load_driver()
    reviews_out = 64
    assert driver.admit_review(reviews_out) is False
    assert driver.admit_build(0) is True
    assert driver.admit_build(driver.MAX_BUILDS - 1) is True


def test_a_build_backlog_cannot_consume_review_slots() -> None:
    """Leftover builds grew into MAX_CONCURRENT and the review loop refused on live."""
    driver = _load_driver()
    builds_out = driver.MAX_CONCURRENT
    assert driver.admit_build(builds_out) is False
    assert driver.admit_review(0) is True
    assert driver.admit_review(driver.MAX_REVIEWS - 1) is True


def test_each_lane_keeps_its_own_reserved_capacity_when_the_other_is_full() -> None:
    driver = _load_driver()
    assert driver.admit_review(driver.MAX_REVIEWS) is False
    assert driver.admit_build(0) is True
    assert driver.admit_build(driver.MAX_BUILDS) is False
    assert driver.admit_review(0) is True


def test_outstanding_builds_are_the_persisted_in_flight_set() -> None:
    """MAX_BUILDS used to count only this tick's launches, so leftover in_flight
    could grow to MAX_CONCURRENT and borrow the review half of the shared pool."""
    driver = _load_driver()
    leftover = {f"U{i:02d}": (0.0, 60.0) for i in range(driver.MAX_BUILDS)}
    state = {
        "in_flight": leftover,
        "review_dispatched": [],
    }
    assert driver.builds_outstanding(state) == driver.MAX_BUILDS
    assert driver.reviews_outstanding(state) == 0
    assert driver.admit_build(driver.builds_outstanding(state)) is False
    assert driver.admit_review(driver.reviews_outstanding(state)) is True


def test_outstanding_reviews_are_the_persisted_review_set() -> None:
    driver = _load_driver()
    state = {
        "in_flight": {},
        "review_dispatched": [f"R{i:02d}" for i in range(driver.MAX_REVIEWS)],
    }
    assert driver.reviews_outstanding(state) == driver.MAX_REVIEWS
    assert driver.builds_outstanding(state) == 0
    assert driver.admit_review(driver.reviews_outstanding(state)) is False
    assert driver.admit_build(driver.builds_outstanding(state)) is True


def test_choose_selected_does_not_borrow_review_capacity() -> None:
    """The old formula was min(MAX_BUILDS, MAX_CONCURRENT - live). At live ==
    MAX_BUILDS that still offered review-lane slots to builds."""
    driver = _load_driver()
    startable = [f"U{i:02d}" for i in range(20)]
    assert driver.choose_selected(startable, driver.MAX_BUILDS) == []
    assert driver.choose_selected(startable, 0) == startable[: driver.MAX_BUILDS]
    assert driver.choose_selected(startable, driver.MAX_BUILDS - 1) == startable[:1]


def test_admission_helpers_do_not_name_the_shared_pool() -> None:
    for name in ("admit_review", "admit_build", "choose_selected", "shed_lane"):
        names = _names_in(_fn(name))
        assert "MAX_CONCURRENT" not in names, (
            f"{name} still admits against the shared pool"
        )


def test_main_does_not_admit_against_a_shared_live_pool() -> None:
    """Admission written as `live >= MAX_CONCURRENT` or `live + launched >=
    MAX_CONCURRENT` is the shared pool. Shedding belongs to each lane's ceiling."""
    names = _names_in(_fn("main"))
    assert "MAX_CONCURRENT" not in names, (
        "main() still names MAX_CONCURRENT. That constant is the shared pool; "
        "lane admission must use MAX_BUILDS and MAX_REVIEWS only."
    )


def test_shedding_is_a_named_function_not_an_incidental_constant() -> None:
    """A safety property held by MAX_CONCURRENT as 'a load cap on the machine'
    is the finding this unit exists to retire. The shed must be callable."""
    driver = _load_driver()
    assert driver.shed_lane(6, 6) is True
    assert driver.shed_lane(5, 6) is False
    assert driver.shed_lane(0, 12) is False
    assert driver.admit_review(6) is (not driver.shed_lane(6, driver.MAX_REVIEWS))
    assert driver.admit_build(12) is (not driver.shed_lane(12, driver.MAX_BUILDS))


def test_pick_arm_skips_a_cooled_down_arm() -> None:
    """27 August 2026: codex and grok were both exhausted at once and pick_arm kept
    rotating into both anyway, spending build slots on dispatches with nothing behind them."""
    driver = _load_driver()
    state = {"arm_cooldown": {"codex": driver.time.time()}}
    for index in range(len(driver.ARMS)):
        harness, _model, _leash = driver.pick_arm(index, state)
        assert harness != "codex", "a cooled-down arm must never be picked"


def test_pick_arm_returns_none_when_every_arm_is_unusable() -> None:
    """Every configured arm in cooldown at once must not fall back to inventing a harness --
    the caller needs to know to skip dispatching this tick.

    The cooled set is derived from `ARMS`, not listed here. This test named codex and grok
    literally and went red the moment cursor-composer was restored on 27 August 2026, reporting
    a rotation change as a bulkhead failure. A test that has to be edited every time the table
    it guards is edited is a maintenance tax that eventually gets paid by deleting the test.
    """
    driver = _load_driver()
    now = driver.time.time()
    state = {"arm_cooldown": {harness: now for harness, _m, _l in driver.ARMS}}
    for index in range(len(driver.ARMS)):
        assert driver.pick_arm(index, state) is None


def test_pick_arm_recovers_once_the_cooldown_expires() -> None:
    driver = _load_driver()
    state = {"arm_cooldown": {"codex": driver.time.time() - driver.ARM_COOLDOWN_S - 1}}
    harness, _model, _leash = driver.pick_arm(0, state)
    assert harness == "codex", (
        "an expired cooldown must not keep blocking the arm forever"
    )


def test_detect_exhausted_arms_reads_a_completed_dispatchs_own_output(
    tmp_path,
) -> None:
    """The motivating case: N03's build EXITED 0 on 27 August 2026 while its own internal
    test run hit Grok's 402 -- a signal buried in a successful dispatch, not a crash."""
    driver = _load_driver()
    driver.BRIEFS = tmp_path
    (tmp_path / "N03.err").write_text("", encoding="utf-8")
    (tmp_path / "N03.out").write_text(
        "...the suite's own live Grok check returning "
        '"API error (status 402 Payment Required): Grok Build usage balance exhausted"...',
        encoding="utf-8",
    )
    state = {"in_flight": {"N03": (0.0, 3600)}, "last_arm": {"N03": "grok"}}
    driver.detect_exhausted_arms(state)
    assert "grok" in state["arm_cooldown"]
    assert "codex" not in state.get("arm_cooldown", {})


def test_detect_exhausted_arms_ignores_bare_status_codes() -> None:
    """ "429" and "402" alone are not admitted -- a real transcript scan found both as false
    positives (line numbers, commit-ish fragments) with no connection to usage at all."""
    driver = _load_driver()
    assert not any(code in driver.ARM_EXHAUSTION_PHRASES for code in ("429", "402"))


def test_a_stale_exhaustion_report_is_counted_once_not_every_tick(tmp_path) -> None:
    """27 August 2026: Joe moved every harness onto a fresh second account, and a stale 402
    from the RETIRED grok account re-cooled the NEW one 11 minutes after it authenticated.

    `<stem>.out`/`.err` persist until the next dispatch overwrites them, so re-stamping
    `cooldown[harness] = now` on every tick pins an arm in a cooldown that never expires.
    Same defect `crashed_dispatches` already fingerprints against; the fix is the same shape.
    """
    driver = _load_driver()
    driver.BRIEFS = tmp_path
    (tmp_path / "N03.err").write_text("", encoding="utf-8")
    (tmp_path / "N03.out").write_text(
        'API error (status 402 Payment Required): Grok Build usage balance exhausted',
        encoding="utf-8",
    )
    state = {"in_flight": {"N03": (0.0, 3600)}, "last_arm": {"N03": "grok"}}

    driver.detect_exhausted_arms(state)
    first = state["arm_cooldown"]["grok"]

    # Second tick over the UNCHANGED file must not re-stamp the cooldown.
    state["arm_cooldown"]["grok"] = first - 900  # pretend 15 min elapsed
    driver.detect_exhausted_arms(state)
    assert state["arm_cooldown"]["grok"] == first - 900, (
        "an unchanged exhaustion report re-stamped the cooldown; it can now never expire"
    )


def test_a_genuinely_new_exhaustion_report_is_counted_again(tmp_path) -> None:
    """The fingerprint must not silence a REAL second report -- a rewritten file is new evidence."""
    driver = _load_driver()
    driver.BRIEFS = tmp_path
    (tmp_path / "N03.err").write_text("", encoding="utf-8")
    out = tmp_path / "N03.out"
    out.write_text("Grok Build usage balance exhausted", encoding="utf-8")
    state = {"in_flight": {"N03": (0.0, 3600)}, "last_arm": {"N03": "grok"}}

    driver.detect_exhausted_arms(state)
    state["arm_cooldown"]["grok"] = 0.0  # a long-expired cooldown

    out.write_text("quota exhausted -- a genuinely new report", encoding="utf-8")
    driver.detect_exhausted_arms(state)
    assert state["arm_cooldown"]["grok"] > 0.0, "a new report must re-cool the arm"


def test_exhaustion_fingerprints_do_not_grow_without_bound(tmp_path) -> None:
    driver = _load_driver()
    driver.BRIEFS = tmp_path
    (tmp_path / "N03.err").write_text("", encoding="utf-8")
    (tmp_path / "N03.out").write_text("quota exhausted", encoding="utf-8")
    state = {"in_flight": {"N03": (0.0, 3600)}, "last_arm": {"N03": "grok"}}
    driver.detect_exhausted_arms(state)
    assert "N03" in state["arm_exhaustion_counted"]

    state["in_flight"] = {}  # N03 no longer watched
    driver.detect_exhausted_arms(state)
    assert "N03" not in state["arm_exhaustion_counted"], "fingerprints must be pruned"


def test_a_report_older_than_the_cooldown_cannot_cool_an_arm(tmp_path) -> None:
    """MEASURED 27 August 2026, live in `.harness/driver-state.json`.

    The fingerprint added the same morning stops a report being counted twice while its unit
    stays watched. It does not survive the unit LEAVING that set: `arm_exhaustion_counted` is
    pruned for any stem no longer watched, while `<stem>.out` is not, because nothing rewrites
    it until that unit dispatches again. A unit that leaves and re-enters therefore arrives
    with its memory erased and its evidence intact.

    That is not hypothetical. `AP-verify.out` carried a "Payment Required" written at 23:34 on
    26 August by the grok account since retired, and it cooled grok at 12:57 the next day --
    13.5 hours later, on a bill belonging to a different subscription. By then `last_arm["AP"]`
    had moved to codex, so the next re-entry would have cooled codex: the only arm still
    dispatching, measured at 0.0% of its weekly pool.

    Age is the check that does not depend on bookkeeping surviving. A report older than
    `ARM_COOLDOWN_S` describes a window the arm has already served.
    """
    driver = _load_driver()
    driver.BRIEFS = tmp_path
    (tmp_path / "AP-verify.err").write_text("", encoding="utf-8")
    stale = tmp_path / "AP-verify.out"
    stale.write_text(
        "API error (status 402 Payment Required): Grok Build usage balance exhausted",
        encoding="utf-8",
    )
    old = driver.time.time() - driver.ARM_COOLDOWN_S - 60
    os.utime(stale, (old, old))
    os.utime(tmp_path / "AP-verify.err", (old, old))

    # No memory of it at all -- exactly the state pruning leaves behind.
    state: dict = {
        "in_flight": {"AP": (0.0, 3600)},
        "last_arm": {"AP": "codex"},
        "arm_exhaustion_counted": {},
    }
    driver.detect_exhausted_arms(state)

    assert not state.get("arm_cooldown"), (
        "a 13.5-hour-old report cooled an arm: "
        f"{state.get('arm_cooldown')}"
    )


def test_a_fresh_report_still_cools_the_arm_after_the_age_check(tmp_path) -> None:
    """The age guard must not blunt the signal it was added around -- a report written now is
    exactly the case `detect_exhausted_arms` exists to catch."""
    driver = _load_driver()
    driver.BRIEFS = tmp_path
    (tmp_path / "AP-verify.err").write_text("", encoding="utf-8")
    (tmp_path / "AP-verify.out").write_text(
        "API error (status 402 Payment Required): Grok Build usage balance exhausted",
        encoding="utf-8",
    )
    state: dict = {
        "in_flight": {"AP": (0.0, 3600)},
        "last_arm": {"AP": "grok"},
        "arm_exhaustion_counted": {},
    }
    driver.detect_exhausted_arms(state)
    assert "grok" in state.get("arm_cooldown", {})


def test_cursor_arms_do_not_borrow_another_familys_model() -> None:
    """A family that is only a name is not a different class of facts.

    Reviewer selection is `[a for a in ARMS if FAMILY.get(a[0]) != FAMILY.get(builder)]` --
    keyed on the HARNESS ID and nothing else. So `("cursor-composer", "cursor-grok-4.6-high-fast")`
    is offered as the cross-family check on grok-built work while running xAI's Grok 4.6. The
    map says "cursor"; the model is the builder's own model. Four of the six cursor arms
    withdrawn on 26 August 2026 were exactly that, so a share of every cross-family review run
    in that period was one Grok agreeing with another Grok.

    AGENTS.md principle 6, from Whewell's "another DIFFERENT class": agreement between agents
    that share evidence is not consilience, it is echo. This repository's whole subject is the
    error rate of that test, so a reviewer that silently shares the builder's model is not a
    weak check, it is a corrupted measurement.

    Written as a check rather than a comment because the rule was already stated in this file
    and stated rules do not enforce themselves -- which is how the four got there.
    """
    driver = _load_driver()
    # Vendor markers that appear in model ids, mapped to the family that actually serves them.
    vendor_markers = {
        "grok": "xai",
        "claude": "anthropic",
        "gpt": "openai",
        "codex": "openai",
        "gemini": "google",
    }
    offenders = []
    for harness, model, _leash in driver.ARMS:
        if not model:
            continue
        declared = driver.FAMILY.get(harness)
        lowered = model.casefold()
        for marker, actual in vendor_markers.items():
            if marker in lowered and actual != declared:
                offenders.append((harness, model, declared, actual))
    assert not offenders, (
        "an arm declares one family and runs another's model, so cross-family review can "
        f"pair a builder with itself: {offenders}"
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


def test_clearing_escalations_does_not_hash_units_it_cannot_report_on(monkeypatch) -> None:
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

    assert len(hashed) == 2, f"hashed {len(hashed)} units; only BK and AL can report anything"


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
    assert "already_present" not in source, "the skip's accumulator survived the withdrawal"
    # The two fixes that were right are kept.
    assert "expire_finished_dispatches(" in inspect.getsource(driver), "the slot reaper was lost"


def test_resolvers_count_against_the_lane_they_are_gated_on() -> None:
    """The resolve loop admitted on `admit_build(len(inflight))`, where `inflight` holds BUILDS
    only -- so a resolver was admitted on the build lane's occupancy while adding nothing to it,
    and the next was admitted on the same unchanged number. 34 ran at once against a cap of
    MAX_BUILDS.

    This is the MAX_REVIEWS defect in a second place, and the fix is the same shape: count what
    is being capped. Asserted on the source because the loop lives inside `main()`; the ceiling
    itself is untouched and stays pinned by
    `test_ceilings_are_not_raised_to_paper_over_contention`.
    """
    import inspect

    driver = _load_driver()
    source = inspect.getsource(driver.main)
    sites = [
        ln.strip()
        for ln in source.splitlines()
        if ln.strip().startswith("if not admit_build(")
    ]
    assert len(sites) == 2, f"expected two admission sites, found {sites}"
    assert "len(resolving)" in " ".join(sites), "no admission counts live resolvers"


def test_a_finished_resolver_releases_its_slot_however_it_ended() -> None:
    """MEASURED 27 August 2026: 34 `resolve_dispatched` entries against roughly nine live
    dispatch processes in total, builds and reviews included.

    The bucket was only ever emptied on two paths -- the unit's conflict clearing, or
    `crashed_dispatches` finding the run dead. A resolver that ran, failed to fix the conflict
    and exited CLEANLY matched neither, so its entry stayed for ever. Every one of those units
    was then permanently barred from re-dispatch by `uid in resolving`, and once resolvers began
    counting against their own lane the stale entries alone exceeded MAX_BUILDS: the loop broke
    before examining anything, so even the two units that genuinely needed a resolver got none.

    This file already states the lesson, from Y02: stopping the retries is right, leaking the
    capacity is not.
    """
    driver = _load_driver()
    now = 1_000_000.0
    state = {
        "resolve_dispatched": ["OLD", "FRESH", "ADOPTED"],
        "resolve_started": {
            "OLD": [now - 3600 - 301, 3600],
            "FRESH": [now - 10, 3600],
        },
    }

    expired = driver.expire_finished_dispatches(state, now=now)

    assert expired == ["OLD"], expired
    assert state["resolve_dispatched"] == ["FRESH", "ADOPTED"]
    # An entry with no start time is UNKNOWN, not known-dead. Reaping it immediately would
    # cancel a resolver that may be doing real work, so it is adopted at `now` and expires on
    # its own leash from here.
    assert state["resolve_started"]["ADOPTED"][0] == now
    assert state["resolve_started"]["ADOPTED"][1] == driver.RESOLVE_ADOPTED_LEASH_S
    # A slow-but-living resolver is never reaped out from under itself.
    assert "FRESH" in state["resolve_dispatched"]


def test_expiry_grace_matches_the_crash_detector() -> None:
    """A dispatch is not late until its leash plus 300s has passed -- the same grace
    `crashed_dispatches` uses, so the two cannot disagree about whether a run is over."""
    driver = _load_driver()
    now = 1_000_000.0
    just_inside = {
        "resolve_dispatched": ["U"],
        "resolve_started": {"U": [now - 3600 - 299, 3600]},
    }
    assert driver.expire_finished_dispatches(just_inside, now=now) == []
    just_outside = {
        "resolve_dispatched": ["U"],
        "resolve_started": {"U": [now - 3600 - 301, 3600]},
    }
    assert driver.expire_finished_dispatches(just_outside, now=now) == ["U"]


def test_a_review_slot_is_released_when_its_dispatch_is_over() -> None:
    """MEASURED 27 August 2026, and this was the largest brake on the pipeline.

    `review_dispatched` held four entries whose newest output was 36, 36, 45 and 50 HOURS old,
    against a lane capped at six. Two thirds of the review lane was held by runs that had ended
    two days earlier while 76 units waited for a verdict -- and the review lane is what decides a
    unit, so nothing could move.

    `crashed_dispatches` could not see them. It defines death as `<stem>.err` carrying a
    traceback, which finds a dispatch that CRASHED and never one that simply stopped existing:
    killed, cut off with the machine, or exited quietly. An empty `.err` reads exactly like a
    healthy run. Time is the signal that does not depend on the dead process having written its
    own death certificate.
    """
    driver = _load_driver()
    now = 1_000_000.0
    state = {
        "review_dispatched": ["TWO_DAYS_DEAD", "RUNNING"],
        "review_started": {
            "TWO_DAYS_DEAD": [now - (50 * 3600), 3600],
            "RUNNING": [now - 60, 3600],
        },
    }

    expired = driver.expire_finished_dispatches(
        state, "review_dispatched", "review_started", now=now
    )

    assert expired == ["TWO_DAYS_DEAD"], expired
    assert state["review_dispatched"] == ["RUNNING"], (
        "a live review was reaped out from under itself"
    )


def test_every_dispatch_bucket_has_an_expiry() -> None:
    """Builds expired on `(started, leash)` in `in_flight`; resolves and reviews recorded a name
    and nothing else, so there was no fact to expire against and both leaked -- resolves for up
    to 32 hours, reviews for up to 50. Three buckets, one lesson, learned twice more than it
    should have been. The driver must record a start time wherever it records a dispatch."""
    import inspect

    driver = _load_driver()
    source = inspect.getsource(driver.main)
    assert '"resolve_started"' in source or "resolve_started" in source, (
        "resolves record no start time"
    )
    assert "review_started" in source, "reviews record no start time"
    assert source.count("expire_finished_dispatches(") == 2, (
        "both leaking buckets must be expired every tick"
    )


def test_adoption_asks_the_artefact_before_holding_a_slot(tmp_path, monkeypatch) -> None:
    """An entry recorded before start times existed has no time to expire against. Asking the
    dispatch's own output is better than guessing either way.

    MEASURED 27 August 2026: 38 such entries, whose newest output was 32 hours old for resolves
    and 50 for reviews. A blind adoption at `now` would have held every one of those slots for a
    further full leash on runs that had been over for two days.

    Where the artefact says nothing at all, adoption is still the safe answer: unknown is not
    known-dead, and cancelling a live run is worse than waiting one leash for certainty.
    """
    driver = _load_driver()
    monkeypatch.setattr(driver, "BRIEFS", tmp_path)
    now = 1_000_000.0

    long_dead = tmp_path / "DEAD-resolve.out"
    long_dead.write_text("output from two days ago", encoding="utf-8")
    import os

    old = now - (50 * 3600)
    os.utime(long_dead, (old, old))

    recent = tmp_path / "BUSY-resolve.out"
    recent.write_text("still writing", encoding="utf-8")
    os.utime(recent, (now - 30, now - 30))

    state = {"resolve_dispatched": ["DEAD", "BUSY", "SILENT"], "resolve_started": {}}
    expired = driver.expire_finished_dispatches(state, now=now)

    assert expired == ["DEAD"], expired
    assert state["resolve_dispatched"] == ["BUSY", "SILENT"]
    # BUSY wrote recently, so it is adopted rather than reaped.
    assert "BUSY" in state["resolve_started"]
    # SILENT never wrote at all: unknown, not known-dead, so it gets a leash to prove itself.
    assert "SILENT" in state["resolve_started"]
    assert state["resolve_started"]["SILENT"][0] == now


def test_the_artefact_beats_an_adopted_start_time(tmp_path, monkeypatch) -> None:
    """A dispatch cannot have last written output before it started.

    MEASURED 27 August 2026: the first tick to run this reaper stamped 34 resolve entries at
    `now`, before the artefact check existed. They then read as "started 47 minutes ago" while
    their own output was 32 HOURS old -- and would have held their slots for a further full leash
    on the strength of a timestamp the reaper itself had invented.

    An adopted start is a guess. The artefact is evidence. Where they disagree in the only
    direction that is physically impossible, the guess is what gives way.
    """
    driver = _load_driver()
    monkeypatch.setattr(driver, "BRIEFS", tmp_path)
    import os

    now = 1_000_000.0
    out = tmp_path / "ADOPTED-resolve.out"
    out.write_text("last wrote 32 hours ago", encoding="utf-8")
    old = now - (32 * 3600)
    os.utime(out, (old, old))

    state = {
        "resolve_dispatched": ["ADOPTED"],
        # exactly the shape a blind adoption leaves behind
        "resolve_started": {"ADOPTED": [now - (47 * 60), 3600]},
    }
    assert driver.expire_finished_dispatches(state, now=now) == ["ADOPTED"]
    assert state["resolve_dispatched"] == []


def test_a_real_dispatch_is_still_judged_on_its_own_start(tmp_path, monkeypatch) -> None:
    """The override must only fire in the impossible direction. A genuine dispatch that started
    ten minutes ago and wrote output two minutes ago has an artefact NEWER than its start, so its
    recorded start stands and it is not reaped."""
    driver = _load_driver()
    monkeypatch.setattr(driver, "BRIEFS", tmp_path)
    import os

    now = 1_000_000.0
    out = tmp_path / "LIVE-resolve.out"
    out.write_text("still going", encoding="utf-8")
    os.utime(out, (now - 120, now - 120))

    state = {
        "resolve_dispatched": ["LIVE"],
        "resolve_started": {"LIVE": [now - 600, 3600]},
    }
    assert driver.expire_finished_dispatches(state, now=now) == []
    assert state["resolve_dispatched"] == ["LIVE"]


def _hash_lines(driver, lines):
    import hashlib

    return sorted({hashlib.sha256(ln.encode("utf-8")).hexdigest()[:16] for ln in lines})


def test_a_verdict_survives_an_unrelated_edit_to_a_shared_file(tmp_path, monkeypatch) -> None:
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


def test_a_verdict_dies_when_the_units_own_work_is_removed(tmp_path, monkeypatch) -> None:
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
    monkeypatch.setattr(driver, "sh", lambda a, **k: _R("    something_entirely_different = 1"))
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


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

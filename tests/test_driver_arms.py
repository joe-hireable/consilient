"""Which harness the driver asks, and when it must stop asking.

A build slot spent on an arm with nothing behind it is lost twice: the dispatch fails
and the unit still waits. On 27 August 2026 codex and grok were exhausted at once and
`pick_arm` kept rotating into both anyway. The cooldown is the answer, and every rule
around it is here because the naive version was wrong in a way that was measured rather
than imagined.

Exhaustion is read from a completed dispatch's own output, not from a crash: N03's build
EXITED 0 that day while its own internal test run hit Grok's 402 — a signal buried in a
successful dispatch. That evidence then persists, because `<stem>.out` is not rewritten
until the unit dispatches again, so a report is fingerprinted against re-stamping,
pruned when the unit stops being watched, and refused outright once it is older than
`ARM_COOLDOWN_S`. The age check is the one that does not depend on bookkeeping
surviving: `AP-verify.out` carried a "Payment Required" written at 23:34 on 26 August by
a grok account since retired, and it cooled grok at 12:57 the next day — 13.5 hours
later, on a bill belonging to a different subscription. By then `last_arm["AP"]` had
moved to codex, so the next re-entry would have cooled the only arm still dispatching,
measured at 0.0% of its weekly pool. Bare "429" and "402" are not admitted as phrases at
all; a real transcript scan found both as false positives with no connection to usage.

The family check belongs with the arm table rather than with review scheduling, because
it is a fact about the table. Reviewer selection is keyed on the harness id alone, so
four of the six cursor arms withdrawn on 26 August 2026 declared "cursor" while running
xAI's Grok 4.6, and a share of every cross-family review in that period was one Grok
agreeing with another. AGENTS.md principle 6, from Whewell's "another DIFFERENT class":
that is echo, not consilience, and in a repository whose whole subject is the error rate
of that test it is a corrupted measurement rather than a weak check."""

import os
from driver_bulkhead_helpers import (
    _load_driver,
)


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
        "API error (status 402 Payment Required): Grok Build usage balance exhausted",
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
        f"a 13.5-hour-old report cooled an arm: {state.get('arm_cooldown')}"
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

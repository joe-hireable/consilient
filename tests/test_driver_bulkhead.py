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
        assert "MAX_CONCURRENT" not in names, f"{name} still admits against the shared pool"


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

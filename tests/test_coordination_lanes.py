"""The serial-lane contract (T01B): plan text to lane order to a claim-order refusal.

These tests never touch the trajectory. They read markdown — stream plans declaring what
each unit claims exactly and what it depends on — and derive from it the order in which
units may take a shared path. That is a different mechanism from the runtime lease, and
it answers a different question: not "who holds this path now?" but "who is allowed to
want it next?".

The derived order is checked against the hand-written lane table in the build plan, and
a disagreement is reported as an inversion rather than resolved silently — the hand
table is a claim about ordering and the dependency graph is the evidence for it. Two
units overlapping on a path with no dependency edge between them still take a serial
order, broken stably by unit id, because overlap alone is enough to forbid concurrency.
A unit whose predecessors have not completed is refused.

The final test pins a measured contract against the real plans on disk: T02 precedes C03
on `src/consilient/coordination.py`, derived from the 22 August 2026 stream plans and
agreeing with the build plan's own table."""

from consilient import coordination
from coordination_helpers import (
    ROOT,
)

# --- serial-lane contract and claim ordering (T01B) -------------------------


_MINI_BUILD_PLAN = """\
## Parallelism and claim lanes

| Lane | Required order |
|---|---|
| `src/widget.py` | `A -> B -> C` |
"""

_MINI_STREAM_PLAN = """\
## A — first

**Claim exactly:**

- `src/widget.py`

**Depends on:** none.

## B — second

**Claim exactly:**

- `src/widget.py`

**Depends on:** A.

## C — third

**Claim exactly:**

- `src/widget.py`
- `docs/readme.md`

**Depends on:** B.
"""


def test_parse_plan_units_reads_claims_and_dependencies() -> None:
    units = coordination.parse_plan_units({"mini.md": _MINI_STREAM_PLAN})
    assert set(units) == {"A", "B", "C"}
    assert units["B"].depends == ("A",)
    assert units["C"].paths == ("src/widget.py", "docs/readme.md")


def test_derive_lane_order_follows_declared_dependencies() -> None:
    units = coordination.parse_plan_units({"mini.md": _MINI_STREAM_PLAN})
    order = coordination.derive_lane_order(units, "src/widget.py")
    assert order == ("A", "B", "C")


def test_lane_order_inversion_detects_dependency_violations() -> None:
    units = coordination.parse_plan_units({"mini.md": _MINI_STREAM_PLAN})
    hand = coordination.parse_build_plan_lanes(_MINI_BUILD_PLAN)
    # Hand table says A -> B -> C which matches dependencies — no inversion.
    assert coordination.lane_order_inversions(units, hand) == ()
    bad_lanes = {"src/widget.py": ["B", "A", "C"]}
    inversions = coordination.lane_order_inversions(units, bad_lanes)
    assert inversions == (("src/widget.py", "B", "A"),)


def test_claim_order_violation_refuses_until_predecessors_complete() -> None:
    units = coordination.parse_plan_units({"mini.md": _MINI_STREAM_PLAN})
    assert coordination.claim_order_violation("C", frozenset(), units) is not None
    assert coordination.claim_order_violation("C", frozenset({"A"}), units) is not None
    assert coordination.claim_order_violation("C", frozenset({"A", "B"}), units) is None


def test_overlapping_claims_without_dependency_still_impose_serial_order() -> None:
    plan = """\
## X — one

**Claim exactly:**

- `src/shared.py`

**Depends on:** none.

## Y — two

**Claim exactly:**

- `src/shared.py`

**Depends on:** none.
"""
    units = coordination.parse_plan_units({"mini.md": plan})
    # No depends edge: stable unit-id tie-break puts X before Y.
    order = coordination.derive_lane_order(units, "src/shared.py")
    assert order == ("X", "Y")
    assert coordination.claim_order_violation("Y", frozenset({"X"}), units) is None
    assert coordination.claim_order_violation("Y", frozenset(), units) is not None


def test_coordination_lane_derived_order_respects_t02_before_c03() -> None:
    """Measured contract: T02 -> C03 on src/consilient/coordination.py (build plan)."""
    plans_dir = ROOT / "docs" / "superpowers" / "plans"
    build_plan = (plans_dir / "2026-08-22-build-plan.md").read_text(encoding="utf-8")
    stream_plans = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(plans_dir.glob("2026-08-22-*-plan.md"))
        if path.name != "2026-08-22-build-plan.md"
    }
    units = coordination.parse_plan_units(stream_plans)
    hand = coordination.parse_build_plan_lanes(build_plan)
    lane = "src/consilient/coordination.py"
    derived = coordination.derive_lane_order(units, lane)
    assert "T02" in derived and "C03" in derived
    assert derived.index("T02") < derived.index("C03")
    assert coordination.lane_order_inversions(units, hand) == ()

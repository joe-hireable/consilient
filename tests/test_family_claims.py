"""A claim must cover the file the behaviour is actually in, not the facade it left behind.

THE FAILURE THIS PREVENTS, measured 29 August 2026 while preparing the loop restart. The splits of
28 August moved behaviour out of 22 modules into `<stem>_*.py` siblings; `.harness/plan-units.json`
still named the originals. 102 of 147 planned units -- 76 of them not done -- claimed a path that
had become an almost-empty re-export manifest. `events.py` was claimed by 41 units and now has 15
siblings; `projection.py` by 34 with 5; `dispatch.py` by 31 with 12.

That is a safety failure and not untidiness, because claims are the driver's concurrency guard:
`scripts/dispatch.py` refuses a second dispatch whose paths overlap a live claim. A unit claiming
`events.py` and needing to change what now lives in `events_projection.py` either writes logic back
into a manifest, or edits a file no claim covers -- where two units that look disjoint collide with
nothing to detect it, and the conflict-resolution lane was already full.

`build_driver.family_claims` expands an entry point to its family at dispatch time. The tests below
pin the three properties that make that safe, and the last one is the one that matters: run against
the real plan and the real tree, no unit may be left claiming a facade whose siblings it does not
also hold.
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.build_driver_helpers import ROOT, _load_driver

DRIVER = _load_driver()


def test_an_entry_point_claim_covers_its_siblings() -> None:
    expanded = DRIVER.family_claims(["src/consilient/events.py"])
    assert "src/consilient/events.py" in expanded, "the original claim must survive"
    assert "src/consilient/events_kinds.py" in expanded
    assert len(expanded) > 10, (
        f"events has many siblings but only {len(expanded)} path(s) were claimed: {expanded}"
    )


def test_a_sibling_claim_is_taken_at_its_word() -> None:
    """Widening a precise claim would cost concurrency to protect a unit that was already precise.

    A unit that names `events_kinds.py` said exactly what it meant. Expanding it to the whole
    family would make it conflict with every other unit touching any part of events, which is a
    real cost paid for no safety the unit did not already have.
    """
    expanded = DRIVER.family_claims(["src/consilient/events_kinds.py"])
    assert expanded == ["src/consilient/events_kinds.py"]


def test_a_non_python_claim_is_untouched() -> None:
    paths = ["docs/decisions/index.md", "pyproject.toml", "src/consilient/beta.py"]
    expanded = DRIVER.family_claims(paths)
    assert expanded[:2] == paths[:2], "only .py entry points expand"


def test_the_expansion_is_stable_and_free_of_duplicates() -> None:
    once = DRIVER.family_claims(["src/consilient/events.py"])
    twice = DRIVER.family_claims(
        ["src/consilient/events.py", "src/consilient/events.py"]
    )
    assert once == twice, "a repeated claim must not duplicate the family"
    assert len(once) == len(set(once))


def test_no_planned_unit_is_left_claiming_a_facade() -> None:
    """The measurement that motivated the fix, kept as the check that it stayed fixed.

    Reads the real plan and the real tree. If a future split creates a family whose entry point a
    unit claims, this passes anyway -- because `family_claims` reads the tree rather than a frozen
    list, which is the whole reason the expansion lives in the driver and not in the plan.
    """
    plan_path = ROOT / ".harness" / "plan-units.json"
    if not plan_path.is_file():  # pragma: no cover - the plan is instance data
        return
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    units = plan if isinstance(plan, list) else plan.get("units", plan)
    if isinstance(units, dict):
        units = [{"id": key, **value} for key, value in units.items()]

    uncovered: list[str] = []
    for unit in units:
        claims = unit.get("claims")
        if not isinstance(claims, list):
            continue
        held = set(DRIVER.family_claims([c for c in claims if isinstance(c, str)]))
        for claim in claims:
            if not isinstance(claim, str) or not claim.endswith(".py"):
                continue
            path = ROOT / claim
            stem = Path(claim).stem
            if "_" in stem and (path.parent / (stem.split("_")[0] + ".py")).is_file():
                continue
            missing = [
                str(sibling.relative_to(ROOT)).replace("\\", "/")
                for sibling in sorted(path.parent.glob(stem + "_*.py"))
                if str(sibling.relative_to(ROOT)).replace("\\", "/") not in held
            ]
            if missing:
                uncovered.append(f"{unit.get('id')}: {claim} -> {missing[:3]}")

    assert uncovered == [], (
        "these units claim a module whose behaviour has moved into siblings they do not hold, "
        "so two apparently disjoint dispatches can edit the same code:\n  "
        + "\n  ".join(uncovered[:15])
    )

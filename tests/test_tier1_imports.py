"""ADR-0065 tier 1: the measured-error-rate modules keep a hard third-party-import ban.

This is the tier-1 half of the check ADR-0065 owes (its lines 134-136). The existing
whole-package stdlib test (``tests/test_v0_invariants.py``,
``test_the_dashboard_adds_no_dependency_outside_the_standard_library``) currently bans
third-party imports across **all** of ``src/consilient/`` — which enforces "adopt nothing",
the opposite of the principal's adopt-vs-build instruction. The ADR's design is two tiers:
tier 1 (the modules whose error rate must be measured — beta, events, projection, recall,
budget, work_items, coordination, routing) keeps the hard ban; tier 2 may import an adopted,
licence-cleared component once the licence record names it (the record is being built in
``docs/legal/adopted-components.json``).

The whole-package test stays in force until its owner re-scopes it to tier 2 — it is another
run's file tonight. This file is the tier-1 half, pinned so the split has something to point
at: when tier 2 adopts its first component and the whole-package test is narrowed, this test
must still fail on any third-party import in the eight modules below. [asserted: the tier
list is ADR-0065's; measured: the AST scan below runs over the real tree]
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "consilient"

TIER1_MODULES = (
    "beta",
    "events",
    "projection",
    "recall",
    "budget",
    "work_items",
    "coordination",
    "routing",
)


def _external_imports(source: Path) -> set[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [] if node.level else [(node.module or "").split(".")[0]]
        else:
            continue
        found.update(n for n in names if n and n not in sys.stdlib_module_names)
    return found


def test_tier1_list_names_exactly_the_eight_modules_and_they_exist() -> None:
    """A rename or a quiet eleventh module breaks the ban rather than narrowing it."""
    assert sorted(TIER1_MODULES) == sorted(
        {"beta", "events", "projection", "recall", "budget", "work_items", "coordination", "routing"}
    )
    for module in TIER1_MODULES:
        assert (PACKAGE / f"{module}.py").is_file(), f"tier-1 module missing: {module}.py"


def test_tier1_modules_import_nothing_outside_stdlib_and_the_package() -> None:
    offenders: set[str] = set()
    for module in TIER1_MODULES:
        external = _external_imports(PACKAGE / f"{module}.py") - {"consilient"}
        offenders.update(f"{module}.py: {name}" for name in sorted(external))
    assert not offenders, (
        "tier-1 modules (ADR-0065) import outside stdlib and the package:\n"
        + "\n".join(sorted(offenders))
    )


def test_the_ban_can_fail() -> None:
    """Mutation check: a third-party import in a tier-1 module must be caught."""
    fixture = ROOT / "tests" / "fixtures" / "_tier1_mutation_target.py"
    fixture.parent.mkdir(exist_ok=True)
    fixture.write_text("import requests\n", encoding="utf-8")
    try:
        assert "requests" in _external_imports(fixture)
    finally:
        fixture.unlink()

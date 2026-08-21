from __future__ import annotations

import ast
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / ".github" / "scripts" / "check_component_licences.py"
RECORD = ROOT / "docs" / "legal" / "adopted-components.json"
TIER_1_MODULES = ("beta", "events", "projection", "recall", "budget", "work_items")
EXPECTED_COMPONENTS = {
    ("microsoft/playwright-mcp", "supplied"),
    ("modelcontextprotocol/servers/src/fetch", "supplied"),
    ("modelcontextprotocol/servers/src/filesystem", "supplied"),
    ("modelcontextprotocol/servers/src/git", "supplied"),
    ("brave/brave-search-mcp-server", "supplied"),
    ("exa-labs/exa-mcp-server", "supplied"),
    ("tavily-ai/tavily-mcp", "supplied"),
    ("anthropics/skills document skills", "refused"),
    ("resend/resend-mcp", "supplied"),
    ("mcp-router/mcp-router", "refused"),
}


def load_checker() -> ModuleType:
    assert CHECKER.is_file(), "component-licence checker is missing"
    spec = importlib.util.spec_from_file_location("check_component_licences", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_component() -> dict[str, str]:
    return {
        "name": "example/component",
        "capability": "example",
        "source": "https://example.test/component",
        "licence": "MIT",
        "verified": date.today().isoformat(),
        "status": "supplied",
    }


def test_adopted_component_record_is_valid():
    assert RECORD.is_file(), "adopted-component record is missing"
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    assert not load_checker().findings(record, set())
    assert {(entry["name"], entry["status"]) for entry in record["components"]} == (
        EXPECTED_COMPONENTS
    )


@pytest.mark.parametrize(
    ("change", "adopted_names", "expected"),
    [
        ({"capability": ""}, set(), "capability"),
        ({"verified": "not-a-date"}, set(), "ISO date"),
        ({"verified": (date.today() + timedelta(days=1)).isoformat()}, set(), "future"),
        ({"licence": "BUSL-1.1"}, set(), "denied licence"),
        ({"status": "refused", "reason": ""}, set(), "reason"),
        (
            {"verified": (date.today() - timedelta(days=181)).isoformat()},
            set(),
            "re-read the licence",
        ),
        ({}, {"missing/component"}, "missing/component"),
        ({"status": "unknown"}, set(), "status"),
    ],
)
def test_rule_function_rejects_each_failure_mode(change, adopted_names, expected):
    component = valid_component()
    component.update(change)
    errors = load_checker().findings({"components": [component]}, adopted_names)
    assert any(expected in error for error in errors), errors


def test_rule_function_accepts_a_valid_record():
    assert not load_checker().findings({"components": [valid_component()]}, set())


def test_rule_function_rejects_an_empty_record():
    errors = load_checker().findings({"components": []}, set())
    assert any("must not be empty" in error for error in errors), errors


def test_component_licence_check_is_wired_into_ci():
    workflow = (ROOT / ".github" / "workflows" / "invariants.yml").read_text(
        encoding="utf-8"
    )
    step = workflow.partition("- name: Adopted component licence invariant check")[
        2
    ].partition("- name:")[0]
    assert step, "the adopted component licence invariant step is gone"
    commands = "\n".join(
        line for line in step.splitlines() if not line.strip().startswith("#")
    )
    assert (
        "run: python .github/scripts/check_component_licences.py --self-test"
        in commands
    )


def test_tier_1_modules_import_only_the_standard_library():
    # Deliberate duplication: the package-wide rule is locked in test_v0_invariants.py;
    # naming these modules separately keeps the tier-1 guarantee if that wider rule changes.
    package = ROOT / "src" / "consilient"
    external: set[str] = set()
    for module in TIER_1_MODULES:
        tree = ast.parse((package / f"{module}.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [] if node.level else [(node.module or "").split(".")[0]]
            else:
                continue
            external.update(name for name in names if name not in sys.stdlib_module_names)
    assert not external, "tier-1 imports outside stdlib: " + repr(sorted(external))

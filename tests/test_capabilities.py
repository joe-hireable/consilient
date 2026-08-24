from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "src" / "consilient" / "capabilities.py"
SCRIPT = ROOT / "scripts" / "capability_context.py"
sys.path.insert(0, str(ROOT / "src"))

from consilient.capabilities import (  # noqa: E402
    CAPABILITY_KINDS,
    CapabilityError,
    default_gate,
    select_capabilities,
)


def _inventory(*items: dict[str, object]) -> dict[str, object]:
    return {"allowlist": list(items)}


def _authority_event() -> dict[str, object]:
    return {
        "event_id": "evt-authority-1",
        "event_kind": "human.approval",
        "event_sha256": "b" * 64,
    }


def _admitted_gate(*, expires_at: str | None = "2099-01-01T00:00:00+00:00") -> dict[str, object]:
    return {
        "state": "admitted",
        "reason": "exact_grant",
        "grant_kind": "principal_authority",
        "authority_event": _authority_event(),
        "decision_id": None,
        "recovery_proof_ref": None,
        "scope": [],
        "operations": [],
        "effect_classes": [],
        "expires_at": expires_at,
    }


def _gated_gate() -> dict[str, object]:
    gate = default_gate()
    return {
        "state": gate.state,
        "reason": gate.reason,
        "grant_kind": gate.grant_kind,
        "authority_event": gate.authority_event,
        "decision_id": gate.decision_id,
        "recovery_proof_ref": gate.recovery_proof_ref,
        "scope": list(gate.scope),
        "operations": list(gate.operations),
        "effect_classes": list(gate.effect_classes),
        "expires_at": gate.expires_at,
    }


def _available(
    kind: str,
    name: str,
    *,
    provenance: list[str] | None = None,
) -> dict[str, object]:
    return {
        "kind": kind,
        "name": name,
        "available": True,
        "provenance": provenance or [f"probe:{kind}:{name}"],
        "gate": _admitted_gate(),
    }


def _selected(
    kind: str,
    name: str,
    *,
    provenance: list[str],
    reason: str,
) -> dict[str, object]:
    return {
        "kind": kind,
        "name": name,
        "provenance": provenance,
        "reason": reason,
        "gate": _admitted_gate(),
    }


def _request(*items: dict[str, object]) -> dict[str, object]:
    return {"capabilities": list(items)}


def _wanted(kind: str, name: str, reason: str = "needed by this task") -> dict[str, object]:
    return {"kind": kind, "name": name, "reason": reason}


def test_selects_exactly_the_five_capability_kinds_with_explanations() -> None:
    assert CAPABILITY_KINDS == ("tool", "mcp", "skill", "plugin", "connection")
    inventory = _inventory(
        _available("connection", "github"),
        _available("plugin", "obsidian"),
        _available("skill", "citing-sources"),
        _available("mcp", "filesystem"),
        _available("tool", "pytest"),
    )
    task = _request(
        _wanted("skill", "citing-sources", "attribute claims"),
        _wanted("tool", "pytest", "run the verifier"),
        _wanted("connection", "github", "read the named repository"),
        _wanted("mcp", "filesystem", "read task files"),
        _wanted("plugin", "obsidian", "use the requested note format"),
    )

    result = select_capabilities(inventory, task)

    assert result == {
        "schema_version": 1,
        "capabilities": [
            _selected(
                "tool",
                "pytest",
                provenance=["probe:tool:pytest"],
                reason="run the verifier",
            ),
            _selected(
                "mcp",
                "filesystem",
                provenance=["probe:mcp:filesystem"],
                reason="read task files",
            ),
            _selected(
                "skill",
                "citing-sources",
                provenance=["probe:skill:citing-sources"],
                reason="attribute claims",
            ),
            _selected(
                "plugin",
                "obsidian",
                provenance=["probe:plugin:obsidian"],
                reason="use the requested note format",
            ),
            _selected(
                "connection",
                "github",
                provenance=["probe:connection:github"],
                reason="read the named repository",
            ),
        ],
    }


def test_unknown_and_unavailable_capabilities_refuse() -> None:
    inventory = _inventory(
        _available("tool", "pytest"),
        {
            "kind": "connection",
            "name": "github",
            "available": False,
            "provenance": ["probe:connection:github"],
        },
    )

    with pytest.raises(CapabilityError, match=r"unknown capability: mcp:missing"):
        select_capabilities(inventory, _request(_wanted("mcp", "missing")))
    with pytest.raises(CapabilityError, match=r"unavailable capability: connection:github"):
        select_capabilities(inventory, _request(_wanted("connection", "github")))


@pytest.mark.parametrize(
    ("inventory", "task", "message"),
    (
        (_inventory(), {"capabilities": [], "domain": "code"}, "task request keys"),
        (_inventory(), _request(_wanted("service", "github")), "kind"),
        (_inventory(), _request({"kind": "tool", "name": "pytest"}), "keys"),
        (_inventory(), _request(_wanted("tool", "bad name")), "name"),
        (
            _inventory(
                {
                    "kind": "tool",
                    "name": "pytest",
                    "available": "yes",
                    "provenance": ["probe:tool:pytest"],
                }
            ),
            _request(),
            "available",
        ),
        (
            _inventory(
                {
                    "kind": "tool",
                    "name": "pytest",
                    "available": True,
                    "provenance": [],
                }
            ),
            _request(),
            "provenance",
        ),
    ),
)
def test_malformed_inventory_or_request_refuses(
    inventory: object,
    task: object,
    message: str,
) -> None:
    with pytest.raises(CapabilityError, match=message):
        select_capabilities(inventory, task)


@pytest.mark.parametrize(
    ("inventory", "task"),
    (
        (
            _inventory(_available("tool", "pytest"), _available("tool", "pytest")),
            _request(),
        ),
        (
            _inventory(_available("tool", "pytest"), _available("tool", "PyTest")),
            _request(),
        ),
        (
            _inventory(_available("tool", "pytest")),
            _request(_wanted("tool", "pytest"), _wanted("tool", "pytest")),
        ),
    ),
)
def test_duplicate_or_case_ambiguous_capabilities_refuse(
    inventory: object,
    task: object,
) -> None:
    with pytest.raises(CapabilityError, match="duplicate or ambiguous"):
        select_capabilities(inventory, task)


def test_selection_is_canonical_across_input_order() -> None:
    entries = [_available("plugin", "zeta"), _available("plugin", "alpha")]
    wanted = [_wanted("plugin", "zeta"), _wanted("plugin", "alpha")]
    forward = select_capabilities(_inventory(*entries), _request(*wanted))
    reverse = select_capabilities(
        _inventory(*reversed(entries)),
        _request(*reversed(wanted)),
    )
    assert forward == reverse
    assert [item["name"] for item in forward["capabilities"]] == ["alpha", "zeta"]


def test_script_emits_the_same_portable_json_without_network(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.json"
    task = tmp_path / "task.json"
    inventory.write_text(
        json.dumps(_inventory(_available("tool", "pytest"))), encoding="utf-8"
    )
    task.write_text(
        json.dumps(_request(_wanted("tool", "pytest", "run checks"))),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), str(inventory), str(task)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == select_capabilities(
        json.loads(inventory.read_text(encoding="utf-8")),
        json.loads(task.read_text(encoding="utf-8")),
    )
    assert set(json.loads(completed.stdout)) == {"schema_version", "capabilities"}


def test_select_refuses_a_gated_inventory_entry() -> None:
    inventory = _inventory(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
            "gate": _gated_gate(),
        }
    )
    with pytest.raises(CapabilityError, match=r"gated capability: tool:pytest"):
        select_capabilities(inventory, _request(_wanted("tool", "pytest")))


def test_select_refuses_an_entry_whose_gate_is_synthesised_as_gated() -> None:
    inventory = _inventory(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
        }
    )
    with pytest.raises(CapabilityError, match=r"gated capability: tool:pytest"):
        select_capabilities(inventory, _request(_wanted("tool", "pytest")))


def test_select_refuses_an_expired_grant() -> None:
    inventory = _inventory(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
            "gate": _admitted_gate(expires_at="2000-01-01T00:00:00+00:00"),
        }
    )
    with pytest.raises(CapabilityError, match=r"expired grant: tool:pytest"):
        select_capabilities(inventory, _request(_wanted("tool", "pytest")))


def test_malformed_inventory_row_names_its_index() -> None:
    inventory = _inventory(
        _available("tool", "pytest"),
        {
            "kind": "tool",
            "name": "ruff",
            "available": "yes",
            "provenance": ["probe:tool:ruff"],
        },
    )
    with pytest.raises(CapabilityError, match=r"inventory allowlist\[1\]"):
        select_capabilities(inventory, _request())


def test_policy_module_is_pure_stdlib_policy() -> None:
    tree = ast.parse(CORE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".", 1)[0])
    assert imported <= {"__future__", "dataclasses", "datetime", "re", "typing"}

    forbidden_calls = {
        "connect",
        "getenv",
        "open",
        "read_text",
        "request",
        "run",
        "urlopen",
        "write_text",
    }
    called = {
        node.func.id
        if isinstance(node.func, ast.Name)
        else node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Name, ast.Attribute))
    }
    assert called.isdisjoint(forbidden_calls)


def test_policy_has_no_domain_or_document_mode_branch() -> None:
    forbidden = {"code", "document", "domain", "mode"}
    violations: list[str] = []
    for path in (CORE, SCRIPT):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        predicates: list[ast.AST] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp, ast.While)):
                predicates.append(node.test)
            elif isinstance(node, ast.Match):
                predicates.append(node.subject)
            elif isinstance(node, ast.comprehension):
                predicates.extend(node.ifs)
        for predicate in predicates:
            words: set[str] = set()
            for part in ast.walk(predicate):
                if isinstance(part, ast.Name):
                    words.update(re.findall(r"[a-z]+", part.id.casefold()))
                elif isinstance(part, ast.Attribute):
                    words.update(re.findall(r"[a-z]+", part.attr.casefold()))
                elif isinstance(part, ast.Constant) and isinstance(part.value, str):
                    words.update(re.findall(r"[a-z]+", part.value.casefold()))
            if words & forbidden:
                violations.append(f"{path.name}:{predicate.lineno}")
    assert not violations, f"domain-keyed branch found: {violations}"

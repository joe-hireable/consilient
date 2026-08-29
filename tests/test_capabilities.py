"""Capability selection: which of the five kinds is chosen, and how the choice is explained.

Refusal behaviour lives in test_capabilities_gates.py and the source-level purity ban in
test_capabilities_purity.py.
"""

import json

import subprocess

import sys

from pathlib import Path

import pytest

from capabilities_helpers import (
    ROOT,
    SCRIPT,
    _available,
    _inventory,
    _request,
    _selected,
    _wanted,
)

sys.path.insert(0, str(ROOT / "src"))

from consilient.capabilities import (
    CAPABILITY_KINDS,
    CapabilityError,
    select_capabilities,
)


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
    with pytest.raises(
        CapabilityError, match=r"unavailable capability: connection:github"
    ):
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

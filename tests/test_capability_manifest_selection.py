"""M04 — what the log yields once manifests are in it: versions, heads, conflicts and
selection.

The projection keeps every version and elects a head only where election is unambiguous.
Two manifests that share an execution contract key and differ only in authored run are
not a supersession, so both versions are kept, no head is elected, and a conflict is
recorded naming the contract key, the destination class and both event ids.

Selection is explicit or it does not happen. An empty request selects nothing; an
identity or an execution contract key has to be named, and both routes must return the
same row. An inactive predecessor stays retrievable by version digest and stays
unselectable. A conflicted head refuses selection with `conflict` in the reason, and
refuses under both names when one contract has been authored under two identities —
otherwise renaming a capability would be a way to walk out of the conflict.

Two tests guard against selection inventing a surface it has never measured. A schema-v1
inventory carrying only an allowlist yields exactly `{schema_version, capabilities}`: no
`selected_manifests`, no `active` anywhere in the payload, no `inventory_status`
conjured from nothing. And `scripts/capability_context.py` is put through a process
boundary to confirm it renders the same answer the library does — the version digest,
the evidence class, the permission and trust boundaries, and `inventory_status` reported
as `unmeasured`."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import cast
from consilient import projection
from consilient.capabilities import retrieve_manifest, select_capabilities
from capability_manifests_helpers import (
    LOCAL,
    LOG,
    TOOL_PYTEST,
    _append,
    _capability_event,
    _event_data,
    _reference,
    _seed_source,
)

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = ROOT / "scripts" / "capability_context.py"


def _rows(document: dict[str, object], key: str) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], document[key])


def _project(workspace: Path) -> sqlite3.Connection:
    db = workspace / "projection.db"
    return projection.build(workspace / LOG, db, workspace=workspace)


def _inventory_from_projection(conn: sqlite3.Connection) -> dict[str, object]:
    return {
        "allowlist": [],
        "manifests": projection.capability_versions(conn),
        "heads": projection.capability_heads(conn),
        "conflicts": projection.capability_conflicts(conn),
    }


def test_projection_keeps_versions_and_refuses_two_active_heads(tmp_path: Path) -> None:
    source = _seed_source(tmp_path)
    first = _append(
        tmp_path,
        _capability_event(source, event_id="550e8400-e29b-41d4-a716-446655440010"),
    )
    conn = _project(tmp_path)
    heads = projection.capability_heads(conn)
    versions = projection.capability_versions(conn)
    conn.close()
    assert len(versions) == 1
    assert len(heads) == 1
    assert heads[0]["identity"] == TOOL_PYTEST
    assert heads[0]["version_digest"] == _event_data(first)["version_digest"]

    twin = _append(
        tmp_path,
        _capability_event(
            source,
            event_id="550e8400-e29b-41d4-a716-446655440011",
            authored_run="run-2",
        ),
    )
    assert (
        _event_data(twin)["execution_contract_key"]
        == _event_data(first)["execution_contract_key"]
    )
    assert _event_data(twin)["version_digest"] != _event_data(first)["version_digest"]
    conn = _project(tmp_path)
    heads = projection.capability_heads(conn)
    conflicts = projection.capability_conflicts(conn)
    versions = projection.capability_versions(conn)
    conn.close()
    assert len(versions) == 2
    assert heads == []
    assert len(conflicts) == 1
    assert (
        conflicts[0]["execution_contract_key"]
        == _event_data(first)["execution_contract_key"]
    )
    assert conflicts[0]["destination_class"] == LOCAL
    assert set(cast(list[str], conflicts[0]["event_ids"])) == {
        first["event_id"],
        twin["event_id"],
    }


def test_select_capabilities_requires_explicit_identity_or_contract_key(
    tmp_path: Path,
) -> None:
    source = _seed_source(tmp_path)
    stored = _append(
        tmp_path,
        _capability_event(source, event_id="550e8400-e29b-41d4-a716-446655440010"),
    )
    conn = _project(tmp_path)
    inventory = _inventory_from_projection(conn)
    conn.close()

    empty = select_capabilities(inventory, {"capabilities": []})
    assert empty["selected_manifests"] == []
    assert empty["capabilities"] == []

    selected = select_capabilities(
        inventory,
        {"capabilities": [], "identities": [TOOL_PYTEST]},
    )
    selected_manifests = _rows(selected, "selected_manifests")
    assert len(selected_manifests) == 1
    assert selected_manifests[0]["identity"] == TOOL_PYTEST
    assert selected_manifests[0]["manifest_event_id"] == stored["event_id"]
    assert (
        selected_manifests[0]["version_digest"] == _event_data(stored)["version_digest"]
    )
    assert (
        selected_manifests[0]["execution_contract_key"]
        == _event_data(stored)["execution_contract_key"]
    )
    assert selected_manifests[0]["destination_class"] == LOCAL
    assert selected_manifests[0]["status"] == "active"
    by_key = select_capabilities(
        inventory,
        {
            "capabilities": [],
            "execution_contract_keys": [_event_data(stored)["execution_contract_key"]],
            "destination_class": LOCAL,
        },
    )
    assert _rows(by_key, "selected_manifests") == selected_manifests


def test_inactive_predecessor_is_retrievable_but_not_selectable(tmp_path: Path) -> None:
    source = _seed_source(tmp_path)
    old = _append(
        tmp_path,
        _capability_event(
            source,
            event_id="550e8400-e29b-41d4-a716-446655440010",
            status="inactive",
        ),
    )
    new = _append(
        tmp_path,
        _capability_event(
            source,
            event_id="550e8400-e29b-41d4-a716-446655440011",
            supersedes=_reference(old),
            authored_run="run-2",
        ),
    )
    conn = _project(tmp_path)
    inventory = _inventory_from_projection(conn)
    conn.close()
    selected = select_capabilities(
        inventory, {"capabilities": [], "identities": [TOOL_PYTEST]}
    )
    selected_manifests = _rows(selected, "selected_manifests")
    assert len(selected_manifests) == 1
    assert selected_manifests[0]["version_digest"] == _event_data(new)["version_digest"]
    found = retrieve_manifest(
        inventory,
        identity=TOOL_PYTEST,
        version_digest=cast(str, _event_data(old)["version_digest"]),
    )
    assert found["status"] == "inactive"
    assert found["version_digest"] == _event_data(old)["version_digest"]


def test_active_head_conflict_refuses_selection(tmp_path: Path) -> None:
    source = _seed_source(tmp_path)
    first = _append(
        tmp_path,
        _capability_event(source, event_id="550e8400-e29b-41d4-a716-446655440010"),
    )
    twin = _append(
        tmp_path,
        _capability_event(
            source,
            event_id="550e8400-e29b-41d4-a716-446655440011",
            authored_run="run-2",
        ),
    )
    assert (
        _event_data(twin)["execution_contract_key"]
        == _event_data(first)["execution_contract_key"]
    )
    conn = _project(tmp_path)
    inventory = _inventory_from_projection(conn)
    conn.close()
    result = select_capabilities(
        inventory, {"capabilities": [], "identities": [TOOL_PYTEST]}
    )
    assert result["selected_manifests"] == []
    refusals = _rows(result, "refusals")
    assert refusals
    assert "conflict" in cast(str, refusals[0]["reason"])


def test_same_contract_different_identity_refuses_both_names(tmp_path: Path) -> None:
    source = _seed_source(tmp_path)
    first = _append(
        tmp_path,
        _capability_event(source, event_id="550e8400-e29b-41d4-a716-446655440010"),
    )
    twin = _append(
        tmp_path,
        _capability_event(
            source,
            event_id="550e8400-e29b-41d4-a716-446655440011",
            identity="tool:other",
            authored_run="run-2",
        ),
    )
    assert (
        _event_data(twin)["execution_contract_key"]
        == _event_data(first)["execution_contract_key"]
    )
    assert _event_data(twin)["identity"] != _event_data(first)["identity"]
    conn = _project(tmp_path)
    inventory = _inventory_from_projection(conn)
    conn.close()
    for identity in (TOOL_PYTEST, "tool:other"):
        result = select_capabilities(
            inventory, {"capabilities": [], "identities": [identity]}
        )
        assert result["selected_manifests"] == []
        refusals = _rows(result, "refusals")
        assert refusals, identity
        assert "conflict" in cast(str, refusals[0]["reason"])


def test_schema_v1_inventory_is_unmeasured_never_an_active_version() -> None:
    # An explicit admitted gate is required to reach selection: `default_gate()` is
    # `gated`, and `select_capabilities` refuses anything not `admitted`. The gate is
    # scaffolding here — this test is about the manifest keys being absent, not the gate.
    inventory = {
        "allowlist": [
            {
                "kind": "tool",
                "name": "pytest",
                "available": True,
                "provenance": ["probe:tool:pytest"],
                "gate": {
                    "state": "admitted",
                    "reason": "exact_grant",
                    "grant_kind": "principal_authority",
                    "authority_event": {
                        "event_id": "evt-authority-1",
                        "event_kind": "human.approval",
                        "event_sha256": "b" * 64,
                    },
                    "decision_id": None,
                    "recovery_proof_ref": None,
                    "scope": [],
                    "operations": [],
                    "effect_classes": [],
                    "expires_at": "2099-01-01T00:00:00+00:00",
                },
            }
        ]
    }
    result = select_capabilities(
        inventory,
        {"capabilities": [{"kind": "tool", "name": "pytest", "reason": "run"}]},
    )
    assert result["schema_version"] == 1
    assert _rows(result, "capabilities")[0]["kind"] == "tool"
    assert result.get("selected_manifests", []) == []
    assert "active" not in json.dumps(result.get("selected_manifests", []))
    assert result.get("inventory_status", "unmeasured") == "unmeasured"
    assert set(result) == {"schema_version", "capabilities"}


def test_script_renders_selected_manifests_and_boundaries(tmp_path: Path) -> None:
    source = _seed_source(tmp_path)
    stored = _append(
        tmp_path,
        _capability_event(source, event_id="550e8400-e29b-41d4-a716-446655440010"),
    )
    conn = _project(tmp_path)
    inventory = _inventory_from_projection(conn)
    conn.close()
    inventory_path = tmp_path / "inventory.json"
    request_path = tmp_path / "task.json"
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    request_path.write_text(
        json.dumps({"capabilities": [], "identities": [TOOL_PYTEST]}),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), str(inventory_path), str(request_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert (
        payload["selected_manifests"][0]["version_digest"]
        == _event_data(stored)["version_digest"]
    )
    assert payload["selected_manifests"][0]["evidence_class"] == "measured"
    assert payload["selected_manifests"][0]["permission_boundary"] == "workspace-read"
    assert payload["selected_manifests"][0]["trust_boundary"] == "untrusted-child"
    assert payload["inventory_status"] == "unmeasured"

"""M04 — explicit active capability-manifest selection."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import pytest

from consilient import events, projection
from consilient.capabilities import retrieve_manifest, select_capabilities
from consilient.events import (
    CapabilityManifest,
    canonical_manifest,
    content_digest,
    execution_contract_key,
    version_digest,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "capability_context.py"
OBJECTS = Path(".harness/objects")
LOG = Path(".harness/log")

TOOL_PYTEST = "tool:pytest"
LOCAL = "local-harness"
PAYLOAD = b"capability body\n"


def _event_data(event: dict[str, object]) -> dict[str, object]:
    return cast(dict[str, object], event["data"])


def _rows(document: dict[str, object], key: str) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], document[key])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(payload: bytes = PAYLOAD) -> str:
    return hashlib.sha256(payload).hexdigest()


def _reference(event: dict[str, object]) -> dict[str, str]:
    return {
        "event_id": str(event["event_id"]),
        "event_kind": str(event["event"]),
        "event_sha256": events.event_sha256(event),
    }


def _record_event(
    *,
    event_id: str,
    record_id: str,
    digest: str,
    ts: str | None = None,
) -> dict[str, object]:
    timestamp = ts or _now()
    return {
        "v": events.SCHEMA_VERSION,
        "ts": timestamp,
        "event": events.RECORD_CAPTURED_KIND,
        "actor": "capability-manifest-test",
        "event_id": event_id,
        "data": {
            "record_id": record_id,
            "digest": digest,
            "byte_count": len(PAYLOAD),
            "media_type": "application/octet-stream",
            "object_locator": f".harness/objects/sha256/{digest[:2]}/{digest[2:]}",
            "source": "inputs/capability.bin",
            "consent_purpose": "task-evidence",
            "retention_class": "project",
            "valid_time": {"from": timestamp, "to": None},
            "supersedes": [],
            "invalidates": [],
        },
    }


def _manifest_fields(
    source: dict[str, str],
    *,
    identity: str = TOOL_PYTEST,
    status: str = "active",
    destination_class: str = LOCAL,
    purpose: str = "run the verifier",
    interface: dict[str, object] | None = None,
    permission_boundary: str = "workspace-read",
    trust_boundary: str = "untrusted-child",
    verifier_semantics: str = "pytest-exit-zero",
    duplicate_of: dict[str, str] | None = None,
    supersedes: dict[str, str] | None = None,
    expires_at: str | None = None,
    recheck_at: str | None = None,
    authored_run: str = "run-1",
) -> dict[str, object]:
    body: dict[str, object] = {
        "identity": identity,
        "source_object": source,
        "authored_run": authored_run,
        "licence": "MIT",
        "privacy_class": "private",
        "purpose": purpose,
        "interface": interface or {"inputs": ["path"], "outputs": ["report"]},
        "permission_boundary": permission_boundary,
        "trust_boundary": trust_boundary,
        "verifier_semantics": verifier_semantics,
        "evidence_class": "measured",
        "status": status,
        "destination_class": destination_class,
        "duplicate_of": duplicate_of,
        "supersedes": supersedes,
        "expires_at": expires_at,
        "recheck_at": recheck_at,
    }
    body["content_digest"] = content_digest(body)
    body["execution_contract_key"] = execution_contract_key(body)
    body["version_digest"] = version_digest(body)
    return body


def _capability_event(
    source: dict[str, str],
    *,
    event_id: str = "550e8400-e29b-41d4-a716-446655440010",
    ts: str | None = None,
    **overrides: object,
) -> dict[str, object]:
    data = _manifest_fields(source)
    data.update(overrides)
    if "content_digest" not in overrides:
        data["content_digest"] = content_digest(data)
    if "execution_contract_key" not in overrides:
        data["execution_contract_key"] = execution_contract_key(data)
    if "version_digest" not in overrides:
        data["version_digest"] = version_digest(data)
    return {
        "v": events.SCHEMA_VERSION,
        "ts": ts or _now(),
        "event": events.CAPABILITY_VERSIONED_KIND,
        "actor": "capability-manifest-test",
        "event_id": event_id,
        "data": data,
    }


def _install_object(workspace: Path, payload: bytes = PAYLOAD) -> str:
    digest = _digest(payload)
    path = workspace / f".harness/objects/sha256/{digest[:2]}/{digest[2:]}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return digest


def _append(workspace: Path, event: dict[str, object]) -> dict[str, object]:
    log = workspace / LOG
    log.mkdir(parents=True, exist_ok=True)
    return events.append(log / f"{str(event['ts'])[:10]}.jsonl", event)


def _project(workspace: Path) -> sqlite3.Connection:
    db = workspace / "projection.db"
    return projection.build(workspace / LOG, db, workspace=workspace)


def _seed_source(workspace: Path) -> dict[str, str]:
    digest = _install_object(workspace)
    captured = _append(
        workspace,
        _record_event(
            event_id="550e8400-e29b-41d4-a716-446655440001",
            record_id="650e8400-e29b-41d4-a716-446655440001",
            digest=digest,
        ),
    )
    return _reference(captured)


def _inventory_from_projection(conn: sqlite3.Connection) -> dict[str, object]:
    return {
        "allowlist": [],
        "manifests": projection.capability_versions(conn),
        "heads": projection.capability_heads(conn),
        "conflicts": projection.capability_conflicts(conn),
    }


def test_manifest_freezes_identity_canonical_form_and_digests() -> None:
    source = {
        "event_id": "550e8400-e29b-41d4-a716-446655440001",
        "event_kind": events.RECORD_CAPTURED_KIND,
        "event_sha256": "a" * 64,
    }
    fields = _manifest_fields(source)
    manifest = CapabilityManifest.from_mapping(fields)
    encoded = canonical_manifest(manifest)
    again = canonical_manifest(CapabilityManifest.from_mapping(json.loads(encoded)))
    assert encoded == again
    assert manifest.identity == TOOL_PYTEST
    assert manifest.kind == "tool"
    assert manifest.name == "pytest"
    assert manifest.version_digest == version_digest(fields)
    assert manifest.content_digest == content_digest(fields)
    assert manifest.execution_contract_key == execution_contract_key(fields)
    twin = _manifest_fields(source, authored_run="run-2")
    assert twin["execution_contract_key"] == fields["execution_contract_key"]
    assert twin["version_digest"] != fields["version_digest"]
    with pytest.raises(AttributeError):
        manifest.status = "inactive"  # type: ignore[misc]


def test_kind_name_and_digest_validation_refuse() -> None:
    source = {
        "event_id": "550e8400-e29b-41d4-a716-446655440001",
        "event_kind": events.RECORD_CAPTURED_KIND,
        "event_sha256": "a" * 64,
    }
    with pytest.raises(events.EventError, match="identity"):
        CapabilityManifest.from_mapping(
            _manifest_fields(source, identity="tool pytest")
        )
    with pytest.raises(events.EventError, match="identity"):
        CapabilityManifest.from_mapping(
            _manifest_fields(source, identity="service:github")
        )
    broken = _manifest_fields(source)
    broken["version_digest"] = "latest"
    with pytest.raises(events.EventError, match="version"):
        CapabilityManifest.from_mapping(broken)


def test_capability_versioned_contract_refuses_aliases_and_missing_fields() -> None:
    source = {
        "event_id": "550e8400-e29b-41d4-a716-446655440001",
        "event_kind": events.RECORD_CAPTURED_KIND,
        "event_sha256": "a" * 64,
    }
    event = _capability_event(source)
    alias = dict(event)
    alias["event"] = "capability.version"
    with pytest.raises(events.EventError, match="alias|capability.versioned"):
        events.validate(alias)
    missing = dict(event)
    missing_data = dict(_event_data(event))
    missing["data"] = missing_data
    del missing_data["status"]
    with pytest.raises(events.EventError, match="missing"):
        events.validate(missing)


def test_writer_refuses_unresolvable_source_mutable_alias_unknown_status_and_bad_links(
    tmp_path: Path,
) -> None:
    source = _seed_source(tmp_path)
    events.validate(_capability_event(source))

    dangling = _capability_event(
        {
            "event_id": "550e8400-e29b-41d4-a716-446655440099",
            "event_kind": events.RECORD_CAPTURED_KIND,
            "event_sha256": "b" * 64,
        }
    )
    with pytest.raises(events.EventError, match="source"):
        _append(tmp_path, dangling)

    aliased = _capability_event(source, version_digest="v1")
    with pytest.raises(events.EventError, match="version"):
        events.validate(aliased)

    unknown = _capability_event(source, status="recommended")
    with pytest.raises(events.EventError, match="status"):
        events.validate(unknown)

    self_ref = _capability_event(
        source, event_id="550e8400-e29b-41d4-a716-446655440010"
    )
    self_ref_data = _event_data(self_ref)
    self_ref_data["supersedes"] = _reference(self_ref)
    self_ref_data["content_digest"] = content_digest(self_ref_data)
    self_ref_data["execution_contract_key"] = execution_contract_key(self_ref_data)
    self_ref_data["version_digest"] = version_digest(self_ref_data)
    with pytest.raises(events.EventError, match="self|supersedes"):
        _append(tmp_path, self_ref)


def test_inconsistent_duplicate_of_and_supersedes_refuse(tmp_path: Path) -> None:
    source = _seed_source(tmp_path)
    first = _append(
        tmp_path,
        _capability_event(source, event_id="550e8400-e29b-41d4-a716-446655440010"),
    )
    both = _capability_event(
        source,
        event_id="550e8400-e29b-41d4-a716-446655440011",
        duplicate_of=_reference(first),
        supersedes=_reference(first),
        status="active",
    )
    with pytest.raises(events.EventError, match="duplicate_of|supersedes"):
        _append(tmp_path, both)


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


def test_lineage_references_refuse_a_legacy_unmeasured_row(tmp_path: Path) -> None:
    """Every capability edge names an identified event, so none can resolve to `unmeasured`.

    `resolve_reference` returns the string `"unmeasured"` for a schema-v1 row that
    carries only kind and content hash. A capability manifest must never rest on one:
    the writer refuses the reference shape before resolution, and the link validator
    additionally refuses a non-`Event` resolution. This pins the first layer, which is
    what keeps the second unreachable.
    """
    _install_object(tmp_path)
    legacy = _record_event(
        event_id="550e8400-e29b-41d4-a716-446655440001",
        record_id="650e8400-e29b-41d4-a716-446655440001",
        digest=_digest(),
    )
    del legacy["event_id"]
    log = tmp_path / LOG
    log.mkdir(parents=True, exist_ok=True)
    day = log / f"{str(legacy['ts'])[:10]}.jsonl"
    day.write_text(
        json.dumps(legacy, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    unidentified = {
        "event_kind": events.RECORD_CAPTURED_KIND,
        "event_sha256": events.event_sha256(legacy),
    }

    with pytest.raises(
        events.EventError, match="source_object must be an exact F03 event reference"
    ):
        _append(tmp_path, _capability_event(unidentified))

    source = _seed_source(tmp_path)
    with pytest.raises(
        events.EventError, match="supersedes must be an exact F03 event reference"
    ):
        _append(
            tmp_path,
            _capability_event(
                source,
                event_id="550e8400-e29b-41d4-a716-446655440011",
                supersedes={
                    "event_kind": events.CAPABILITY_VERSIONED_KIND,
                    "event_sha256": events.event_sha256(legacy),
                },
            ),
        )

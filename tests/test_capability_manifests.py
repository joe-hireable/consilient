"""M04 — what a capability manifest must be, and every shape refused before one is
stored.

The record first. Identity is `kind:name` over a closed set of kinds, so `tool pytest`
and `service:github` are both refused. The canonical form round-trips through JSON
unchanged, the frozen manifest refuses attribute assignment, and the three digests
separate concerns: the same body authored by a second run keeps its execution contract
key and takes a new version digest.

Then the refusals, which are what the record is for. The event contract rejects the
`capability.version` alias and any missing field. The writer, appending to a real log,
rejects a `source_object` that resolves to nothing, a mutable digest alias such as `v1`,
a status outside the vocabulary, a manifest that supersedes itself, and a manifest
carrying both `duplicate_of` and `supersedes` for the same predecessor. A legacy
schema-v1 row — one carrying only kind and content hash, for which `resolve_reference`
returns the string `unmeasured` — is refused at the reference shape, before resolution
is ever attempted, which is what keeps the second layer of that defence unreachable.

These belong together because they all answer one question at authoring time: is this
thing a manifest at all? What the log yields once manifests are in it is
`test_capability_manifest_selection.py`."""

import json
from pathlib import Path
import pytest
from consilient import events
from consilient.events import (
    CapabilityManifest,
    canonical_manifest,
    content_digest,
    execution_contract_key,
    version_digest,
)
from capability_manifests_helpers import (
    LOG,
    TOOL_PYTEST,
    _append,
    _capability_event,
    _digest,
    _event_data,
    _install_object,
    _manifest_fields,
    _record_event,
    _reference,
    _seed_source,
)


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

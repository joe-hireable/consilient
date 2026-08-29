"""Builders for capability-manifest events, shared by the M04 test modules.

`_manifest_fields` assembles a complete manifest body and then computes the three
digests over it in order — `content_digest`, `execution_contract_key`, `version_digest`
— because the distinction between them is what most of these tests turn on: the same
body authored by a second run keeps its execution contract key and takes a new version
digest. `_capability_event` wraps that body in a `capability.versioned` event and
recomputes any digest an override did not supply, so a test can corrupt exactly one
field and leave everything else consistent.

The workspace helpers seed a real object store and a real log rather than stubbing them,
so the writer's link resolution is genuinely exercised: `_seed_source` captures an
object and returns the exact F03 event reference a manifest's `source_object` is
required to be. They are shared because the refusal tests and the selection tests both
need a well-formed manifest before they can say anything about a malformed one.

`OBJECTS` is referenced by nothing and was already unreferenced before the split. It is
kept rather than dropped so that the split changes behaviour nowhere; deleting dead code
is a separate change with a separate justification."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from consilient import events
from consilient.events import (
    content_digest,
    execution_contract_key,
    version_digest,
)

OBJECTS = Path(".harness/objects")

LOG = Path(".harness/log")

TOOL_PYTEST = "tool:pytest"

LOCAL = "local-harness"

PAYLOAD = b"capability body\n"


def _event_data(event: dict[str, object]) -> dict[str, object]:
    return cast(dict[str, object], event["data"])


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

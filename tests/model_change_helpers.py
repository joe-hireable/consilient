"""M06 — the lineage a ``model.change`` event has to point at.

``_seed_lineage`` appends the events a change must reference before the change itself
can be valid: a captured base-model record, a versioned capability standing for the
training procedure, and optionally a dataset record and a checkpoint record. Its two
flags exist because the suite has to build lineages that are deliberately incomplete — a
non-data-driven change has no dataset, a failed or refused change has no checkpoint —
without letting any test hand-roll a log that a real run could not have produced.
``_change_body`` and ``_change_event`` then assemble a well-formed change over that
lineage, so a test can break exactly one field and attribute the refusal to that field
alone.

The digests in the change body are computed from the same payload constants the records
are seeded from, so a change body and the record it points at cannot silently drift
apart inside the fixture and turn a real refusal into a fixture bug.
``_manifest_fields`` builds the capability manifest with its content, execution-contract
and version digests derived rather than hard-coded, for the same reason."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from consilient import events
from consilient.events import content_digest, execution_contract_key, version_digest

LOG = Path(".harness/log")

BASE_PAYLOAD = b"base-model-weights\n"

DATASET_PAYLOAD = b"training-rows\n"

CHECKPOINT_PAYLOAD = b"checkpoint-adapter\n"

PROCEDURE_PAYLOAD = b"training-procedure\n"

BASE_EVENT_ID = "550e8400-e29b-41d4-a716-446655440001"

DATASET_EVENT_ID = "550e8400-e29b-41d4-a716-446655440002"

CHECKPOINT_EVENT_ID = "550e8400-e29b-41d4-a716-446655440003"

PROCEDURE_EVENT_ID = "550e8400-e29b-41d4-a716-446655440010"

CHANGE_EVENT_ID = "550e8400-e29b-41d4-a716-446655440020"

CHANGE_ID = "750e8400-e29b-41d4-a716-446655440000"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _event_data(event: dict[str, object]) -> dict[str, object]:
    return cast(dict[str, object], event["data"])


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
    byte_count: int,
    source: str,
    ts: str | None = None,
) -> dict[str, object]:
    timestamp = ts or _now()
    return {
        "v": events.SCHEMA_VERSION,
        "ts": timestamp,
        "event": events.RECORD_CAPTURED_KIND,
        "actor": "model-change-test",
        "event_id": event_id,
        "data": {
            "record_id": record_id,
            "digest": digest,
            "byte_count": byte_count,
            "media_type": "application/octet-stream",
            "object_locator": f".harness/objects/sha256/{digest[:2]}/{digest[2:]}",
            "source": source,
            "consent_purpose": "task-evidence",
            "retention_class": "project",
            "valid_time": {"from": timestamp, "to": None},
            "supersedes": [],
            "invalidates": [],
        },
    }


def _manifest_fields(source: dict[str, str]) -> dict[str, object]:
    body: dict[str, object] = {
        "identity": "skill:embedding-fit",
        "source_object": source,
        "authored_run": "run-1",
        "licence": "MIT",
        "privacy_class": "private",
        "purpose": "fit an embedding model",
        "interface": {"inputs": ["dataset"], "outputs": ["checkpoint"]},
        "permission_boundary": "workspace-read",
        "trust_boundary": "untrusted-child",
        "verifier_semantics": "held-out-compare",
        "evidence_class": "measured",
        "status": "inactive",
        "destination_class": "local-harness",
        "duplicate_of": None,
        "supersedes": None,
        "expires_at": None,
        "recheck_at": None,
    }
    body["content_digest"] = content_digest(body)
    body["execution_contract_key"] = execution_contract_key(body)
    body["version_digest"] = version_digest(body)
    return body


def _capability_event(
    source: dict[str, str],
    *,
    event_id: str = PROCEDURE_EVENT_ID,
    ts: str | None = None,
) -> dict[str, object]:
    return {
        "v": events.SCHEMA_VERSION,
        "ts": ts or _now(),
        "event": events.CAPABILITY_VERSIONED_KIND,
        "actor": "model-change-test",
        "event_id": event_id,
        "data": _manifest_fields(source),
    }


def _append(workspace: Path, event: dict[str, object]) -> dict[str, object]:
    log = workspace / LOG
    log.mkdir(parents=True, exist_ok=True)
    return events.append(log / f"{str(event['ts'])[:10]}.jsonl", event)


def _seed_lineage(
    workspace: Path,
    *,
    with_dataset: bool = True,
    with_checkpoint: bool = True,
) -> dict[str, dict[str, object]]:
    seeded: dict[str, dict[str, object]] = {}
    base = _append(
        workspace,
        _record_event(
            event_id=BASE_EVENT_ID,
            record_id="650e8400-e29b-41d4-a716-446655440001",
            digest=_digest(BASE_PAYLOAD),
            byte_count=len(BASE_PAYLOAD),
            source="inputs/base.bin",
        ),
    )
    seeded["base"] = base
    procedure = _append(workspace, _capability_event(_reference(base)))
    seeded["procedure"] = procedure
    if with_dataset:
        seeded["dataset"] = _append(
            workspace,
            _record_event(
                event_id=DATASET_EVENT_ID,
                record_id="650e8400-e29b-41d4-a716-446655440002",
                digest=_digest(DATASET_PAYLOAD),
                byte_count=len(DATASET_PAYLOAD),
                source="inputs/dataset.bin",
            ),
        )
    if with_checkpoint:
        seeded["checkpoint"] = _append(
            workspace,
            _record_event(
                event_id=CHECKPOINT_EVENT_ID,
                record_id="650e8400-e29b-41d4-a716-446655440003",
                digest=_digest(CHECKPOINT_PAYLOAD),
                byte_count=len(CHECKPOINT_PAYLOAD),
                source="inputs/checkpoint.bin",
            ),
        )
    return seeded


def _change_body(
    seeded: dict[str, dict[str, object]],
    *,
    mutation_class: str = "data_driven_training",
    status: str = "succeeded",
    failure: str | None = None,
    licence: str = "MIT",
    privacy_class: str = "private",
    authoring_run: str = "20260825T022615-bd05853725",
    include_dataset: bool = True,
    include_checkpoint: bool = True,
) -> dict[str, object]:
    body: dict[str, object] = {
        "change_id": CHANGE_ID,
        "mutation_class": mutation_class,
        "base_model_digest": _event_data(seeded["base"])["digest"],
        "dataset_digest": (
            _event_data(seeded["dataset"])["digest"]
            if include_dataset and "dataset" in seeded
            else None
        ),
        "procedure_digest": _event_data(seeded["procedure"])["version_digest"],
        "authoring_run": authoring_run,
        "checkpoint_digest": (
            _event_data(seeded["checkpoint"])["digest"]
            if include_checkpoint and "checkpoint" in seeded
            else None
        ),
        "status": status,
        "failure": failure,
        "licence": licence,
        "privacy_class": privacy_class,
        "base_model": _reference(seeded["base"]),
        "dataset": (
            _reference(seeded["dataset"])
            if include_dataset and "dataset" in seeded
            else None
        ),
        "procedure": _reference(seeded["procedure"]),
        "checkpoint": (
            _reference(seeded["checkpoint"])
            if include_checkpoint and "checkpoint" in seeded
            else None
        ),
    }
    return body


def _change_event(
    seeded: dict[str, dict[str, object]],
    *,
    event_id: str = CHANGE_EVENT_ID,
    ts: str | None = None,
    **overrides: object,
) -> dict[str, object]:
    data = _change_body(seeded)
    data.update(overrides)
    return {
        "v": events.SCHEMA_VERSION,
        "ts": ts or _now(),
        "event": events.MODEL_CHANGE_KIND,
        "actor": "model-change-test",
        "event_id": event_id,
        "data": data,
    }

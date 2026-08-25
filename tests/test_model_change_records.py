"""M06 — model-change provenance record.

Every attempted persistent model-state mutation is one validated ``model.change``
event. This unit records provenance; it does not train, promote or activate.
"""

from __future__ import annotations

import ast
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

import pytest

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


def test_model_change_body_fields_are_frozen() -> None:
    assert events.MODEL_CHANGE_KIND == "model.change"
    assert events.MODEL_CHANGE_FIELDS == {
        "change_id",
        "mutation_class",
        "base_model_digest",
        "dataset_digest",
        "procedure_digest",
        "authoring_run",
        "checkpoint_digest",
        "status",
        "failure",
        "licence",
        "privacy_class",
        "base_model",
        "dataset",
        "procedure",
        "checkpoint",
    }
    assert events.MODEL_CHANGE_MUTATION_CLASSES == {
        "data_driven_training",
        "non_data_driven_state_change",
    }
    assert events.MODEL_CHANGE_STATUSES == {
        "started",
        "succeeded",
        "failed",
        "refused",
    }


def test_aliases_and_missing_fields_are_refused(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    event = _change_event(seeded)
    alias = dict(event)
    alias["event"] = "model.changed"
    with pytest.raises(events.EventError, match="alias|model.change"):
        events.validate(alias)

    missing = dict(event)
    missing_data = dict(_event_data(event))
    missing["data"] = missing_data
    del missing_data["status"]
    with pytest.raises(events.EventError, match="missing"):
        events.validate(missing)

    extra = dict(event)
    extra_data = dict(_event_data(event))
    extra_data["weights"] = "mutated"
    extra["data"] = extra_data
    with pytest.raises(events.EventError, match="unexpected"):
        events.validate(extra)


def test_mutation_class_and_status_are_closed(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    with pytest.raises(events.EventError, match="mutation_class"):
        events.validate(_change_event(seeded, mutation_class="fine_tune"))
    with pytest.raises(events.EventError, match="status"):
        events.validate(_change_event(seeded, status="promoted"))


def test_data_driven_training_requires_a_dataset_record(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    with pytest.raises(events.EventError, match="dataset"):
        events.validate(
            _change_event(
                seeded,
                mutation_class="data_driven_training",
                dataset=None,
                dataset_digest=None,
            )
        )


def test_non_data_driven_change_forbids_a_dataset(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    with pytest.raises(events.EventError, match="dataset"):
        events.validate(
            _change_event(
                seeded,
                mutation_class="non_data_driven_state_change",
                status="succeeded",
                failure=None,
            )
        )


def test_success_requires_a_checkpoint_and_no_failure(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    with pytest.raises(events.EventError, match="checkpoint"):
        events.validate(
            _change_event(
                seeded,
                status="succeeded",
                checkpoint=None,
                checkpoint_digest=None,
            )
        )
    with pytest.raises(events.EventError, match="failure"):
        events.validate(
            _change_event(seeded, status="succeeded", failure="should-not-be-set")
        )


def test_failed_and_refused_require_a_visible_reason(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path, with_checkpoint=False)
    for status in ("failed", "refused"):
        with pytest.raises(events.EventError, match="failure"):
            events.validate(
                _change_event(
                    seeded,
                    status=status,
                    failure=None,
                    checkpoint=None,
                    checkpoint_digest=None,
                )
            )


def test_private_derived_output_requires_explicit_licence_and_privacy(
    tmp_path: Path,
) -> None:
    seeded = _seed_lineage(tmp_path)
    for field, value in (
        ("licence", ""),
        ("licence", "unknown"),
        ("privacy_class", "  "),
        ("privacy_class", "unspecified"),
    ):
        with pytest.raises(events.EventError, match="licence|privacy"):
            events.validate(_change_event(seeded, **{field: value}))


def test_references_must_be_exact_earlier_record_or_capability_events(
    tmp_path: Path,
) -> None:
    seeded = _seed_lineage(tmp_path)
    dangling = _change_event(
        seeded,
        base_model={
            "event_id": "550e8400-e29b-41d4-a716-446655440099",
            "event_kind": events.RECORD_CAPTURED_KIND,
            "event_sha256": "b" * 64,
        },
    )
    with pytest.raises(events.EventError, match="base_model"):
        _append(tmp_path, dangling)

    self_ref = _change_event(seeded, event_id=CHANGE_EVENT_ID)
    self_data = _event_data(self_ref)
    self_data["base_model"] = {
        "event_id": CHANGE_EVENT_ID,
        "event_kind": events.RECORD_CAPTURED_KIND,
        "event_sha256": "c" * 64,
    }
    with pytest.raises(events.EventError, match="self|base_model"):
        _append(tmp_path, self_ref)

    wrong_kind = _change_event(
        seeded,
        dataset=_reference(seeded["procedure"]),
        dataset_digest=_event_data(seeded["procedure"])["version_digest"],
    )
    with pytest.raises(events.EventError, match="dataset"):
        events.validate(wrong_kind)


def test_digest_must_match_the_referenced_record(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path)
    with pytest.raises(events.EventError, match="digest"):
        _append(tmp_path, _change_event(seeded, base_model_digest="a" * 64))


def test_embedding_fit_is_training_and_frozen_embedding_is_not_a_model_change() -> None:
    assert events.mutation_class_for("embedding_fit") == "data_driven_training"
    assert events.mutation_class_for("optimiser") == "data_driven_training"
    assert events.mutation_class_for("closed_form") == "data_driven_training"
    assert events.mutation_class_for("direct_edit") == "non_data_driven_state_change"
    assert events.mutation_class_for("frozen_embedding") is None
    assert events.mutation_class_for("embedding_inference") is None
    with pytest.raises(events.EventError, match="procedure"):
        events.mutation_class_for("retrieval")


def test_success_failure_and_refusal_replay_with_complete_provenance(
    tmp_path: Path,
) -> None:
    seeded = _seed_lineage(tmp_path)
    success = _append(tmp_path, _change_event(seeded))
    failed = _append(
        tmp_path,
        _change_event(
            seeded,
            event_id="550e8400-e29b-41d4-a716-446655440021",
            change_id="750e8400-e29b-41d4-a716-446655440001",
            status="failed",
            failure="checkpoint write refused",
            checkpoint=None,
            checkpoint_digest=None,
        ),
    )
    refused = _append(
        tmp_path,
        _change_event(
            seeded,
            event_id="550e8400-e29b-41d4-a716-446655440022",
            change_id="750e8400-e29b-41d4-a716-446655440002",
            status="refused",
            failure="missing licence disposition",
            checkpoint=None,
            checkpoint_digest=None,
        ),
    )
    started = _append(
        tmp_path,
        _change_event(
            seeded,
            event_id="550e8400-e29b-41d4-a716-446655440023",
            change_id="750e8400-e29b-41d4-a716-446655440003",
            status="started",
            failure=None,
            checkpoint=None,
            checkpoint_digest=None,
        ),
    )

    accepted, rejected = events.read_all(tmp_path / LOG)
    assert rejected == []
    changes = [event for event in accepted if event.kind == events.MODEL_CHANGE_KIND]
    assert [event.raw["event_id"] for event in changes] == [
        success["event_id"],
        failed["event_id"],
        refused["event_id"],
        started["event_id"],
    ]
    prefix = tuple(accepted)
    for event in changes:
        data = event.data
        assert events.resolve_reference(data["base_model"], prefix).kind == (
            events.RECORD_CAPTURED_KIND
        )
        assert events.resolve_reference(data["procedure"], prefix).kind == (
            events.CAPABILITY_VERSIONED_KIND
        )
        if data["dataset"] is not None:
            dataset = events.resolve_reference(data["dataset"], prefix)
            assert dataset.kind == events.RECORD_CAPTURED_KIND
            assert dataset.data["digest"] == data["dataset_digest"]
        if data["checkpoint"] is not None:
            checkpoint = events.resolve_reference(data["checkpoint"], prefix)
            assert checkpoint.kind == events.RECORD_CAPTURED_KIND
            assert checkpoint.data["digest"] == data["checkpoint_digest"]
        assert data["licence"] == "MIT"
        assert data["privacy_class"] == "private"
        assert data["authoring_run"] == "20260825T022615-bd05853725"

    assert _event_data(success)["status"] == "succeeded"
    assert _event_data(success)["checkpoint_digest"] == _digest(CHECKPOINT_PAYLOAD)
    assert _event_data(failed)["failure"] == "checkpoint write refused"
    assert _event_data(refused)["failure"] == "missing licence disposition"
    assert _event_data(started)["status"] == "started"
    assert _event_data(started)["checkpoint"] is None


def test_non_data_driven_success_replays_without_a_dataset(tmp_path: Path) -> None:
    seeded = _seed_lineage(tmp_path, with_dataset=False)
    stored = _append(
        tmp_path,
        _change_event(
            seeded,
            mutation_class="non_data_driven_state_change",
            dataset=None,
            dataset_digest=None,
        ),
    )
    accepted, rejected = events.read_all(tmp_path / LOG)
    assert rejected == []
    change = next(
        event for event in accepted if event.raw["event_id"] == stored["event_id"]
    )
    assert change.data["mutation_class"] == "non_data_driven_state_change"
    assert change.data["dataset"] is None
    assert change.data["dataset_digest"] is None
    assert change.data["checkpoint_digest"] == _digest(CHECKPOINT_PAYLOAD)


def test_unit_imports_no_trainer_changes_no_model_bytes_and_cannot_activate() -> None:
    source_path = Path(__file__).resolve().parents[1] / "src" / "consilient" / "events.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    forbidden = {
        "torch",
        "transformers",
        "peft",
        "trl",
        "accelerate",
        "openai",
        "anthropic",
        "huggingface_hub",
        "datasets",
        "sklearn",
        "subprocess",
        "socket",
        "http",
        "urllib",
        "requests",
    }
    assert not (imported & forbidden), sorted(imported & forbidden)
    dumped = ast.dump(tree)
    assert "select_capabilities" not in dumped
    assert "getattr" not in dumped
    assert "from .capabilities" not in source
    assert "from consilient.capabilities" not in source
    assert "MODEL_CHANGE_KIND" in dumped
    assert events.MODEL_CHANGE_KIND not in {
        events.CAPABILITY_VERSIONED_KIND,
        events.RECORD_CAPTURED_KIND,
    }

"""A04 — atomic fake effect admission: decision, intent, one reach, receipt, outcome."""

from __future__ import annotations

import hashlib
import importlib.util
import multiprocessing
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient import events
from consilient.effects import (
    ADMISSION_DISPOSITIONS,
    EffectAdmissionRefusal,
    EffectManifest,
    admit_effect,
    build_effect_intent_event,
)
from consilient.events import (
    DECISION_KIND,
    EventError,
    OUTCOME_KIND,
    SCHEMA_VERSION,
    read,
)


DISPATCH_PATH = Path(__file__).resolve().parent.parent / "scripts" / "dispatch.py"
DIGEST = "a" * 64
REFERENCE = {
    "event_id": "00000000-0000-4000-8000-000000000001",
    "event_kind": "evidence.observed",
    "event_sha256": DIGEST,
}


def _reset_admission_handles():
    dispatch = _load_dispatch()
    dispatch._ADMITTED_EFFECTS.clear()


@pytest.fixture(autouse=True)
def _clear_admission_handles():
    _reset_admission_handles()


def _load_dispatch():
    name = "consilient_dispatch_action_boundary"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, DISPATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def commitment(domain: str, digest: str = DIGEST) -> dict[str, str]:
    return {
        "kind": "keyed_commitment",
        "algorithm": "hmac-sha256",
        "domain": domain,
        "key_version": "v1",
        "commitment": digest,
    }


def broker_reference(name: str) -> dict[str, str]:
    return {
        "kind": "broker_reference",
        "reference": f"broker://effects/{hashlib.sha256(name.encode()).hexdigest()}",
    }


def envelope(
    kind: str, data: dict[str, object], *, actor: str = "owner"
) -> dict[str, object]:
    return {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": kind,
        "actor": actor,
        "data": data,
    }


def protocol() -> dict[str, object]:
    return {
        "status": "not_warranted",
        "threshold": {
            "version": "better-than-best.v1",
            "later_reliance": "false",
            "question_open": "true",
            "wrong_costs_more": "true",
        },
    }


def binding(admission_class: str, manifest_digest: str) -> dict[str, object]:
    if admission_class == "material_choice":
        return {"kind": admission_class}
    if admission_class in {"contained_execution", "proof_operation"}:
        return {
            "kind": admission_class,
            "effect_manifest_digest": manifest_digest,
            "sandbox_policy_digest": "2" * 64,
            "verifier_policy_digest": "3" * 64,
            "expected_receipt_digest": "4" * 64,
        }
    if admission_class == "recoverable_mutation":
        return {
            "kind": admission_class,
            "effect_manifest_digest": manifest_digest,
            "sandbox_policy_digest": "2" * 64,
            "verifier_policy_digest": "3" * 64,
            "expected_receipt_digest": "4" * 64,
            "recovery_proof_digest": "5" * 64,
        }
    protected = {
        "kind": admission_class,
        "protected_class": "principal_authority",
        "effect_manifest_digest": manifest_digest,
    }
    if admission_class == "protected_covered":
        protected["authority_ref"] = dict(REFERENCE)
    return protected


def manifest_record(
    *,
    operation_id: str = "operation-1",
    attempt_id: str = "attempt-1",
    effects: tuple[str, ...] = ("file.change",),
    operations: tuple[str, ...] = ("write",),
) -> EffectManifest:
    return EffectManifest(
        operation_id=operation_id,
        work_item_id="work-1",
        attempt_id=attempt_id,
        adapter={
            "id": "test.file-adapter",
            "version": "v1",
            "implementation_digest": "e" * 64,
        },
        forward=commitment("effect.manifest.forward"),
        scope=broker_reference("scope"),
        operations=operations,
        effects=effects,
        inventory_snapshot={"digest": "f" * 64},
        gate_snapshot={"digest": "d" * 64},
        authority_snapshot=broker_reference("authority"),
        law_snapshot={"digest": "0" * 64},
        start_state=commitment("effect.manifest.start_state"),
        observer={"id": "observer-1", "policy_digest": "1" * 64},
        expected_state=commitment("effect.manifest.expected_state"),
        reversal={"kind": "named_inverse", "name": "restore"},
        declared_residuals=("elapsed_time",),
        ceilings={"wall_time_s": 1, "writes": 2},
    )


def decision_event(manifest: EffectManifest) -> dict[str, object]:
    return envelope(
        DECISION_KIND,
        {
            "decision_id": "decision-1",
            "operation_id": manifest.operation_id,
            "ticket": "WORK-1",
            "owner": "owner",
            "actor": "owner",
            "record_level": "minimal",
            "decision": "Use the accepted standard-library path",
            "reasoning": "It is the smallest path satisfying the frozen contract",
            "falsifier": "A required effect cannot be represented",
            "reversal": {"kind": "inverse", "value": "consilient.effects.validate"},
            "alternatives": [
                {
                    "option": "Add a dependency",
                    "rejected_because": "No dependency is needed",
                }
            ],
            "evidence_refs": [dict(REFERENCE)],
            "acceptance_contract_digest": "b" * 64,
            "protocol": protocol(),
            "binding": binding("recoverable_mutation", manifest.digest),
        },
    )


def seed_decision(log_dir: Path, manifest: EffectManifest) -> dict[str, object]:
    source = envelope("evidence.observed", {"claim": "independent observation"})
    day = log_dir / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    events.append(day, source)
    decision = decision_event(manifest)
    exact = {
        "event_id": source["event_id"],
        "event_kind": source["event"],
        "event_sha256": events.event_sha256(source),
    }
    decision["data"]["evidence_refs"] = [exact]
    events.append(day, decision)
    return decision


def test_admit_effect_refuses_without_matching_pre_action_decision() -> None:
    manifest = manifest_record()
    planned = admit_effect(
        manifest,
        disposition="execute",
        prefix=(),
        intent_id="intent-1",
        receipt_id="receipt-1",
    )
    assert isinstance(planned, EffectAdmissionRefusal)
    assert planned.reason == "decision_missing"


def test_admit_effect_refuses_mismatched_manifest_digest(tmp_path: Path) -> None:
    log = tmp_path
    manifest = manifest_record()
    decision = seed_decision(log, manifest)
    bad_manifest = manifest_record(
        operation_id=manifest.operation_id, attempt_id="attempt-2"
    )
    planned = admit_effect(
        bad_manifest,
        disposition="execute",
        prefix=events.read_all(log)[0],
        decision_event=decision,
        intent_id="intent-1",
        receipt_id="receipt-1",
    )
    assert isinstance(planned, EffectAdmissionRefusal)
    assert planned.reason == "manifest_digest_mismatch"


def test_admit_effect_refuses_duplicate_operation_intent(tmp_path: Path) -> None:
    log = tmp_path
    manifest = manifest_record()
    decision = seed_decision(log, manifest)
    prefix = events.read_all(log)[0]
    from consilient.events import append_transaction

    first = admit_effect(
        manifest,
        disposition="execute",
        prefix=prefix,
        decision_event=decision,
        intent_id="intent-1",
        receipt_id="receipt-1",
    )
    assert not isinstance(first, EffectAdmissionRefusal)
    append_transaction(
        log,
        [envelope("effect.intent", first.intent_data)],
        lambda p, r, c: None,
    )
    prefix = events.read_all(log)[0]
    again = admit_effect(
        manifest,
        disposition="execute",
        prefix=prefix,
        decision_event=decision,
        intent_id="intent-2",
        receipt_id="receipt-2",
    )
    assert isinstance(again, EffectAdmissionRefusal)
    assert again.reason == "operation_intent_exists"


def test_admit_effect_observation_skips_decision_id() -> None:
    manifest = manifest_record(effects=("data.read",), operations=("read",))
    planned = admit_effect(
        manifest,
        disposition="execute",
        observation_id="observation-1",
        prefix=(),
        intent_id="intent-obs",
        receipt_id="receipt-obs",
    )
    assert not isinstance(planned, EffectAdmissionRefusal)
    assert planned.intent_data["decision_id"] is None
    assert planned.intent_data["admission"]["kind"] == "observation"


def test_observation_intent_refuses_mutating_operation() -> None:
    manifest = manifest_record(effects=("file.change",), operations=("write",))
    planned = admit_effect(
        manifest,
        disposition="execute",
        observation_id="observation-1",
        prefix=(),
        intent_id="intent-bad",
        receipt_id="receipt-bad",
    )
    assert isinstance(planned, EffectAdmissionRefusal)
    assert planned.reason == "observation_predicate_failed"


def test_run_admitted_fake_effect_orders_decision_intent_reach_receipt_outcome(
    tmp_path: Path,
) -> None:
    dispatch = _load_dispatch()
    manifest = manifest_record()
    log = tmp_path
    decision = seed_decision(log, manifest)
    sink = dispatch.FakeEffectSink(status="succeeded")
    result = dispatch.run_admitted_fake_effect(
        log,
        manifest=manifest,
        disposition="execute",
        decision_event=decision,
        sink=sink,
        intent_id="intent-1",
        receipt_id="receipt-1",
    )
    assert result.status == "succeeded"
    assert sink.invocations == 1
    day = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    recorded, rejected = read(day)
    assert not rejected
    kinds = [event.kind for event in recorded]
    assert kinds.index(DECISION_KIND) < kinds.index("effect.intent")
    assert kinds.index("effect.intent") < kinds.index("effect.receipt")
    assert kinds.index("effect.receipt") < kinds.index(OUTCOME_KIND)


def test_refused_disposition_appends_intent_without_fake_reach(tmp_path: Path) -> None:
    dispatch = _load_dispatch()
    manifest = manifest_record()
    log = tmp_path
    decision = seed_decision(log, manifest)
    sink = dispatch.FakeEffectSink(status="succeeded")
    result = dispatch.run_admitted_fake_effect(
        log,
        manifest=manifest,
        disposition="refuse",
        decision_event=decision,
        sink=sink,
        intent_id="intent-refused",
        receipt_id="receipt-refused",
    )
    assert result.status == "refused"
    assert sink.invocations == 0
    day = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    recorded, _ = read(day)
    assert [event.kind for event in recorded].count("effect.receipt") == 0


def test_retry_after_success_returns_committed_receipt_without_second_reach(
    tmp_path: Path,
) -> None:
    dispatch = _load_dispatch()
    manifest = manifest_record()
    log = tmp_path
    decision = seed_decision(log, manifest)
    sink = dispatch.FakeEffectSink(status="succeeded")
    first = dispatch.run_admitted_fake_effect(
        log,
        manifest=manifest,
        disposition="execute",
        decision_event=decision,
        sink=sink,
        intent_id="intent-1",
        receipt_id="receipt-1",
    )
    second = dispatch.run_admitted_fake_effect(
        log,
        manifest=manifest,
        disposition="execute",
        decision_event=decision,
        sink=sink,
        intent_id="intent-1",
        receipt_id="receipt-1",
    )
    assert first.receipt_id == second.receipt_id
    assert sink.invocations == 1


def _contend(log_dir: str, results) -> None:
    dispatch = _load_dispatch()
    manifest = manifest_record()
    log = Path(log_dir)
    day = log / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    recorded, _ = read(day)
    decision = next(e.raw for e in recorded if e.kind == DECISION_KIND)
    sink = dispatch.FakeEffectSink(status="succeeded")
    try:
        dispatch.run_admitted_fake_effect(
            log,
            manifest=manifest,
            disposition="execute",
            decision_event=decision,
            sink=sink,
            intent_id="intent-shared",
            receipt_id="receipt-shared",
        )
        results.put(("ok", sink.invocations))
    except Exception as exc:
        results.put(("error", str(exc)))


def test_two_concurrent_admissions_reach_fake_sink_once(tmp_path: Path) -> None:
    manifest = manifest_record()
    seed_decision(tmp_path, manifest)
    results: multiprocessing.Queue = multiprocessing.Queue()
    workers = [
        multiprocessing.Process(target=_contend, args=(str(tmp_path), results))
        for _ in range(2)
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=30)
        assert worker.exitcode == 0
    outcomes = [results.get(timeout=5) for _ in workers]
    invocations = sum(item[1] for item in outcomes if item[0] == "ok")
    assert invocations == 1


def test_crash_before_intent_leaves_no_fake_reach(tmp_path: Path, monkeypatch) -> None:
    dispatch = _load_dispatch()
    manifest = manifest_record()
    log = tmp_path
    decision = seed_decision(log, manifest)
    sink = dispatch.FakeEffectSink(status="succeeded")

    def fail_fsync(fd):
        raise OSError("injected fsync failure")

    monkeypatch.setattr("os.fsync", fail_fsync)
    with pytest.raises(EventError, match="not acknowledged"):
        dispatch.run_admitted_fake_effect(
            log,
            manifest=manifest,
            disposition="execute",
            decision_event=decision,
            sink=sink,
            intent_id="intent-crash",
            receipt_id="receipt-crash",
        )
    assert sink.invocations == 0


def test_build_effect_intent_event_matches_validator() -> None:
    manifest = manifest_record()
    data = build_effect_intent_event(
        manifest,
        disposition="execute",
        intent_id="intent-1",
        decision_id="decision-1",
    )
    events.validate(envelope("effect.intent", data))


@pytest.mark.parametrize("disposition", sorted(ADMISSION_DISPOSITIONS))
def test_admit_effect_accepts_every_admission_disposition_label(
    disposition: str,
) -> None:
    manifest = manifest_record(effects=("data.read",), operations=("read",))
    planned = admit_effect(
        manifest,
        disposition=disposition,
        observation_id="observation-1",
        prefix=(),
        intent_id=f"intent-{disposition}",
        receipt_id=f"receipt-{disposition}",
    )
    if disposition == "execute":
        assert not isinstance(planned, EffectAdmissionRefusal)
    elif disposition == "refuse":
        assert isinstance(planned, EffectAdmissionRefusal)
    else:
        assert isinstance(planned, EffectAdmissionRefusal)

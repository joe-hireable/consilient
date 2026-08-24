"""Isolated recovery proof is executed, not declared.

A named inverse, a successful exit code or a restored file tree the adapter
itself reports is not mechanical reversibility. A03 evaluates forward state,
inverse state, enclosing-scope equality, escaped effects and residuals against
a fake scratch broker, and only exact restoration with no escaped protected
effect yields a digest bound to a later live operation.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient.effects import (
    EffectManifest,
    ProofObservation,
    canonical_state_digest,
    evaluate_recovery_proof,
)
from consilient.events import SCHEMA_VERSION, validate


DISPATCH_PATH = Path(__file__).resolve().parent.parent / "scripts" / "dispatch.py"
POLICY = "2" * 64
VERIFIER = "3" * 64
ADAPTER_DIGEST = "e" * 64


def _load_script():
    name = "consilient_dispatch_script"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, DISPATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def commitment(domain: str, digest: str) -> dict[str, str]:
    return {
        "kind": "keyed_commitment",
        "algorithm": "hmac-sha256",
        "domain": domain,
        "key_version": "v1",
        "commitment": digest,
    }


def broker_reference(name: str) -> dict[str, str]:
    return {"kind": "broker_reference", "reference": f"broker://effects/{name}"}


def proof_ids(**overrides: str) -> dict[str, str]:
    values = {
        "proof_operation_id": "proof-op-1",
        "proof_decision_id": "proof-decision-1",
        "proof_intent_id": "proof-intent-1",
        "live_operation_id": "live-op-1",
    }
    values.update(overrides)
    return values


def mutation_manifest(
    *,
    start: str,
    expected: str,
    effects: tuple[str, ...] = ("file.change",),
    operations: tuple[str, ...] = ("write",),
    residuals: tuple[str, ...] = ("elapsed_time",),
) -> EffectManifest:
    return EffectManifest(
        operation_id="live-op-1",
        work_item_id="work-1",
        attempt_id="attempt-1",
        adapter={
            "id": "test.file-adapter",
            "version": "v1",
            "implementation_digest": ADAPTER_DIGEST,
        },
        forward=commitment("effect.forward", "a" * 64),
        scope=broker_reference("scope"),
        operations=operations,
        effects=effects,
        inventory_snapshot={"digest": "f" * 64},
        gate_snapshot={"digest": "d" * 64},
        authority_snapshot=broker_reference("authority"),
        law_snapshot={"digest": "0" * 64},
        start_state=commitment("effect.start-state", start),
        observer={"id": "observer-1", "policy_digest": POLICY},
        expected_state=commitment("effect.expected-state", expected),
        reversal={"kind": "named_inverse", "name": "restore"},
        declared_residuals=residuals,
        ceilings={"wall_time_s": 1, "writes": 2},
    )


def restore_adapter() -> dict[str, object]:
    return {
        "forward": [{"kind": "write", "path": "note.txt", "content": "beta"}],
        "inverse": [{"kind": "write", "path": "note.txt", "content": "alpha"}],
    }


def run_proof(
    tmp_path: Path,
    *,
    adapter: dict[str, object],
    start_files: dict[str, str] | None = None,
    expected_files: dict[str, str] | None = None,
    enclosing_files: dict[str, str] | None = None,
    ids: dict[str, str] | None = None,
    effects: tuple[str, ...] = ("file.change",),
    operations: tuple[str, ...] = ("write",),
    residuals: tuple[str, ...] = ("elapsed_time",),
    start_commitment: str | None = None,
    verifier_policy: str = VERIFIER,
    sandbox_policy: str = POLICY,
) -> object:
    start_files = start_files or {"note.txt": "alpha"}
    expected_files = expected_files or {"note.txt": "beta"}
    enclosing = tmp_path / "enclosing"
    scratch = enclosing / "scratch"
    scratch.mkdir(parents=True)
    if enclosing_files:
        for relative, content in enclosing_files.items():
            path = enclosing / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    verifier_log = tmp_path / "verifier.jsonl"
    verifier_log.write_text("", encoding="utf-8")
    start_digest = start_commitment or canonical_state_digest(start_files)
    expected_digest = canonical_state_digest(expected_files)
    manifest = mutation_manifest(
        start=start_digest,
        expected=expected_digest,
        effects=effects,
        operations=operations,
        residuals=residuals,
    )
    script = _load_script()
    return script.run_isolated_recovery_proof(
        scratch,
        verifier_log,
        identities=ids or proof_ids(),
        manifest=manifest,
        start_files=start_files,
        adapter=adapter,
        sandbox_policy_digest=sandbox_policy,
        verifier_policy_digest=verifier_policy,
    )


def test_exact_scratch_restoration_emits_bound_digest(tmp_path: Path) -> None:
    proof = run_proof(tmp_path, adapter=restore_adapter())
    assert proof.status == "passed"
    assert proof.reason == "restored"
    assert proof.digest is not None
    assert len(proof.digest) == 64
    assert proof.live_operation_id == "live-op-1"
    assert proof.proof_operation_id == "proof-op-1"
    assert proof.proof_operation_id != proof.live_operation_id
    assert proof.proof_decision_id == "proof-decision-1"
    assert proof.proof_intent_id == "proof-intent-1"


def test_wrong_preimage_is_refused(tmp_path: Path) -> None:
    proof = run_proof(
        tmp_path,
        adapter=restore_adapter(),
        start_commitment="0" * 64,
    )
    assert proof.status == "refused"
    assert proof.reason == "start_state_mismatch"
    assert proof.digest is None


def test_incomplete_scope_is_refused(tmp_path: Path) -> None:
    proof = run_proof(
        tmp_path,
        enclosing_files={"outside.txt": "keep"},
        adapter={
            "forward": [
                {"kind": "write", "path": "note.txt", "content": "beta"},
                {"kind": "write", "path": "../outside.txt", "content": "leaked"},
            ],
            "inverse": [{"kind": "write", "path": "note.txt", "content": "alpha"}],
        },
    )
    assert proof.status == "refused"
    assert proof.reason == "enclosing_scope_mismatch"
    assert proof.digest is None


def test_failed_inverse_is_refused(tmp_path: Path) -> None:
    proof = run_proof(
        tmp_path,
        adapter={
            "forward": [{"kind": "write", "path": "note.txt", "content": "beta"}],
            "inverse": [{"kind": "write", "path": "note.txt", "content": "not-alpha"}],
        },
    )
    assert proof.status == "refused"
    assert proof.reason == "inverse_failed"
    assert proof.digest is None


@pytest.mark.parametrize(
    "step",
    (
        {"kind": "write", "path": "../../escape.txt", "content": "nope"},
        {"kind": "network", "target": "https://example.invalid"},
        {"kind": "credential", "name": "api_key"},
    ),
    ids=("out_of_root", "network", "credential"),
)
def test_undeclared_protected_attempt_is_refused(
    tmp_path: Path, step: dict[str, str]
) -> None:
    adapter = restore_adapter()
    adapter["forward"] = list(adapter["forward"]) + [step]
    proof = run_proof(tmp_path, adapter=adapter)
    assert proof.status == "refused"
    assert proof.reason == "escaped_protected_effect"
    assert proof.digest is None
    assert proof.observation.escaped_attempts


def test_escaped_child_is_refused(tmp_path: Path) -> None:
    adapter = restore_adapter()
    adapter["forward"] = list(adapter["forward"]) + [
        {"kind": "spawn_child", "id": "child-1"}
    ]
    proof = run_proof(tmp_path, adapter=adapter)
    assert proof.status == "refused"
    assert proof.reason == "escaped_child"
    assert proof.digest is None
    assert "escaped_child" in proof.observation.escaped_attempts


def test_changed_verifier_policy_is_refused(tmp_path: Path) -> None:
    adapter = restore_adapter()
    adapter["forward"] = list(adapter["forward"]) + [
        {"kind": "change_verifier_policy", "digest": "f" * 64}
    ]
    proof = run_proof(tmp_path, adapter=adapter)
    assert proof.status == "refused"
    assert proof.reason == "verifier_policy_changed"
    assert proof.digest is None


def test_residual_only_process_execution_is_capability_gap(tmp_path: Path) -> None:
    proof = run_proof(
        tmp_path,
        start_files={"note.txt": "alpha"},
        expected_files={"note.txt": "alpha"},
        effects=("process.run",),
        operations=("run",),
        residuals=("elapsed_time", "cpu_time"),
        adapter={
            "forward": [{"kind": "process", "residuals": ["elapsed_time", "cpu_time"]}],
            "inverse": [],
        },
    )
    assert proof.status == "capability_gap"
    assert proof.reason == "process_run_not_restorable"
    assert proof.digest is None


def test_lying_adapter_is_independently_refused_despite_passing_declared_inverse(
    tmp_path: Path,
) -> None:
    proof = run_proof(
        tmp_path,
        adapter={
            "forward": [
                {"kind": "write", "path": "note.txt", "content": "beta"},
                {"kind": "network", "target": "https://example.invalid"},
            ],
            "inverse": [{"kind": "write", "path": "note.txt", "content": "alpha"}],
        },
    )
    assert proof.observation.end_state_digest == proof.observation.start_state_digest
    assert proof.observation.inverse_status == "succeeded"
    assert proof.status == "refused"
    assert proof.reason == "escaped_protected_effect"
    assert proof.digest is None
    assert "network" in proof.observation.escaped_attempts


def test_missing_proof_identities_are_refused(tmp_path: Path) -> None:
    proof = run_proof(
        tmp_path,
        adapter=restore_adapter(),
        ids=proof_ids(proof_decision_id="", proof_intent_id=""),
    )
    assert proof.status == "refused"
    assert proof.reason == "proof_identities_missing"
    assert proof.digest is None


def test_proof_digest_binds_separate_live_operation(tmp_path: Path) -> None:
    first = run_proof(tmp_path / "one", adapter=restore_adapter())
    second = run_proof(
        tmp_path / "two",
        adapter=restore_adapter(),
        ids=proof_ids(live_operation_id="live-op-2"),
    )
    same_op = run_proof(
        tmp_path / "same",
        adapter=restore_adapter(),
        ids=proof_ids(live_operation_id="proof-op-1"),
    )
    assert first.status == "passed"
    assert second.status == "passed"
    assert first.digest != second.digest
    assert same_op.status == "refused"
    assert same_op.reason == "live_operation_not_separate"
    assert same_op.digest is None


def test_syntactic_reversal_is_not_mechanical_proof() -> None:
    event = {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "decision.autonomous",
        "actor": "consilient.dispatch",
        "data": {
            "decision": "Use the standard-library implementation",
            "reasoning": "It is the smallest implementation that meets the requirement",
            "falsifier": "A required input cannot be represented",
            "reversal": {
                "kind": "inverse",
                "value": "consilient.effects.no_such_restore",
            },
        },
    }
    validate(event)

    start = canonical_state_digest({"note.txt": "alpha"})
    proof = evaluate_recovery_proof(
        proof_operation_id="proof-op-1",
        proof_decision_id="proof-decision-1",
        proof_intent_id="proof-intent-1",
        live_operation_id="live-op-1",
        manifest=mutation_manifest(start=start, expected=start),
        observation=ProofObservation(
            start_state_digest=start,
            forward_state_digest=start,
            end_state_digest=start,
            enclosing_before_digest=start,
            enclosing_after_digest=start,
            expected_state_digest=start,
            forward_status="not_run",
            inverse_status="not_run",
            sandbox_policy_digest=POLICY,
            verifier_policy_digest=VERIFIER,
            observed_verifier_policy_digest=VERIFIER,
            observer_log_digest="0" * 64,
            escaped_attempts=(),
            observed_residuals=("elapsed_time",),
        ),
    )
    assert proof.status == "refused"
    assert proof.reason == "proof_not_executed"
    assert proof.digest is None


def test_outer_runner_receives_only_scratch_root_and_verifier_log() -> None:
    script = _load_script()
    params = inspect.signature(script.run_isolated_recovery_proof).parameters
    assert list(params)[:2] == ["scratch_root", "verifier_log"]
    forbidden = {
        "live_target",
        "network",
        "credential",
        "provider",
        "spend",
        "network_handle",
        "credential_handle",
        "provider_handle",
    }
    assert set(params) & forbidden == set()

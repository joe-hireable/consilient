"""S02 — sealed one-use evaluation and reversal proof (ADR-0076)."""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from consilient.promote import (
    AdverseTable,
    CandidateInstrumentView,
    EvaluationPackage,
    EvaluationRefusal,
    LineageRegistry,
    SealedManifest,
    candidate_visible,
    digest,
    evaluate_sealed,
    find_forbidden_imports,
    manifest_digest,
    privileged_fields,
    record_evaluation,
    reserve_qualification_batch,
    validate_adverse_table,
    verify_manifest_seal,
)

EXP78 = Path("docs/10-research/experiments/exp78")
TRAINING = [
    (row["prompt"], row["expected"])
    for row in json.loads((EXP78 / "tasks.json").read_text(encoding="utf-8"))
]
HELDOUT = [
    ("What is 5+2?", "7"),
    ("What is 6+1?", "7"),
    ("What is 3+4?", "7"),
]


def _exp78(name: str) -> str:
    return (EXP78 / name).read_text(encoding="utf-8")


def _loop_execute():
    script = Path("scripts/promote_loop.py")
    spec = importlib.util.spec_from_file_location("promote_loop", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.execute


def _manifest_dict(*, hidden: list[tuple[str, str]] | None = None) -> dict[str, object]:
    development = [(prompt, expected) for prompt, expected in TRAINING]
    hidden_items = hidden if hidden is not None else list(HELDOUT)
    payload = {
        "lineage_id": "exp78-lineage",
        "qualification_batch_id": "batch-001",
        "development_tasks": [{"prompt": p, "expected": e} for p, e in development],
        "hidden_items": [{"prompt": p, "expected": e} for p, e in hidden_items],
        "predecessor_digest": digest("predecessor"),
        "epoch_anchor_digest": digest("epoch"),
        "allowed_imports": [],
        "acceptance_threshold": 1.0,
        "seed": "1040076",
    }
    payload["instrument_digest"] = manifest_digest(payload)
    return payload


def _manifest(**kwargs: object) -> SealedManifest:
    data = _manifest_dict(**kwargs)
    return SealedManifest.from_mapping(data)


def _execute(source: str, cases: list[tuple[str, str]]) -> tuple[bool, float]:
  execute = _loop_execute()
  return execute(source, cases)


def _adverse(**overrides: int) -> AdverseTable:
    base = {
        "refusals": 0,
        "timeouts": 0,
        "quarantine": 0,
        "missing_telemetry": 0,
        "boundary_attempts": 0,
    }
    base.update(overrides)
    return AdverseTable(**base)


def _evaluate(
    manifest: SealedManifest,
    *,
    candidate: str,
    baseline: str,
    registry: LineageRegistry | None = None,
    adverse: AdverseTable | None = None,
    contained: bool = True,
    scratch_preimage: str = "scratch-before",
    scratch_postimage: str = "scratch-before",
) -> EvaluationPackage | EvaluationRefusal:
    return evaluate_sealed(
        manifest,
        candidate_source=candidate,
        baseline_source=baseline,
        execute=_execute,
        registry=registry or LineageRegistry(),
        adverse=adverse or _adverse(),
        contained=contained,
        scratch_preimage_digest=digest(scratch_preimage),
        scratch_postimage_digest=digest(scratch_postimage),
    )


def test_manifest_seal_rejects_mutated_instrument():
    manifest = _manifest()
    with pytest.raises(EvaluationRefusal, match="instrument_unsealed"):
        verify_manifest_seal(manifest, digest("wrong"))


def test_alternate_import_refuses_before_evaluation():
    source = "import os\n\ndef solve(prompt):\n    return '4'\n"
    forbidden = find_forbidden_imports(source, frozenset())
    assert forbidden == ["os"]
    manifest = _manifest()
    result = _evaluate(manifest, candidate=source, baseline=_exp78("solver.py"))
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "instrument_unsealed"
    assert "os" in result.detail


def test_repeat_query_refuses_second_lineage_use():
    manifest = _manifest()
    registry = LineageRegistry()
    first = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        registry=registry,
    )
    assert isinstance(first, EvaluationPackage)
    registry = reserve_qualification_batch(
        registry, manifest.lineage_id, manifest.qualification_batch_id
    )
    second = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        registry=registry,
    )
    assert isinstance(second, EvaluationRefusal)
    assert second.reason == "repeat_query"


def test_hidden_fields_are_not_exposed_to_candidate_view():
    manifest = _manifest()
    view = CandidateInstrumentView(manifest)
    assert view.development_tasks == tuple(TRAINING)
    with pytest.raises(AttributeError):
        _ = view.hidden_items
    visible = candidate_visible(
        _evaluate(
            manifest,
            candidate=_exp78("helpful.py"),
            baseline=_exp78("solver.py"),
        )
    )
    assert set(visible) == {"qualification_accept"}
    assert "hidden_items" not in json.dumps(visible)
    assert "development_score" not in json.dumps(visible)
    for field in privileged_fields():
        assert field not in visible


def test_missing_adverse_row_refuses():
    manifest = _manifest()
    with pytest.raises(EvaluationRefusal, match="missing_adverse_row"):
        validate_adverse_table(
            AdverseTable(
                refusals=0,
                timeouts=0,
                quarantine=0,
                missing_telemetry=0,
                boundary_attempts=-1,
            )
        )
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        adverse=AdverseTable(
            refusals=0,
            timeouts=0,
            quarantine=0,
            missing_telemetry=0,
            boundary_attempts=-1,
        ),
    )
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "missing_adverse_row"


def test_goodhart_improvement_refuses_despite_training_gain():
    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("harmful.py"),
        baseline=_exp78("solver.py"),
    )
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "goodhart_improvement"


def test_reversal_mismatch_refuses():
    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        scratch_preimage="before",
        scratch_postimage="after",
    )
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "reversal_mismatch"


def test_sealed_helpful_candidate_yields_one_immutable_package():
    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
    )
    assert isinstance(result, EvaluationPackage)
    assert result.qualification_accept is True
    assert result.reversal_match is True
    assert result.manifest_digest == manifest.instrument_digest
    assert result.adverse.refusals == 0
    assert result.adverse.missing_telemetry == 0
    visible = candidate_visible(result)
    assert visible == {"qualification_accept": True}
    replay = candidate_visible(result)
    assert replay == visible


def test_uncontained_real_candidate_records_candidate_unexecutable():
    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        contained=False,
    )
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "candidate_unexecutable"


def test_record_evaluation_appends_without_activation_fields(tmp_path: Path):
    manifest = _manifest()
    package = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
    )
    assert isinstance(package, EvaluationPackage)
    recorded = record_evaluation(tmp_path, package)
    assert recorded["event"] == "promote.evaluated"
    payload = recorded["data"]
    assert payload["qualification_accept"] is True
    assert "hidden_items" not in payload
    assert "card" not in payload
    assert "activated" not in payload


def test_promote_loop_evaluate_only_runs_scratch_reversal(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest_dict()), encoding="utf-8")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    log_dir = tmp_path / "log"
    marker = scratch / "state.txt"
    marker.write_text("parent", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/promote_loop.py",
            "--sealed-manifest",
            str(manifest_path),
            "--source",
            str(EXP78 / "helpful.py"),
            "--baseline",
            str(EXP78 / "solver.py"),
            "--scratch-dir",
            str(scratch),
            "--log",
            str(log_dir),
            "--evaluate-only",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["action"] == "evaluated"
    assert payload["qualification_accept"] is True
    assert payload["reversal_match"] is True
    assert payload["applied"] is False
    assert payload["activated"] is False
    assert marker.read_text(encoding="utf-8") == "parent"


def test_promote_loop_goodhart_refuses_without_mutating_scratch(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest_dict()), encoding="utf-8")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    log_dir = tmp_path / "log"
    marker = scratch / "state.txt"
    marker.write_text("parent", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/promote_loop.py",
            "--sealed-manifest",
            str(manifest_path),
            "--source",
            str(EXP78 / "harmful.py"),
            "--baseline",
            str(EXP78 / "solver.py"),
            "--scratch-dir",
            str(scratch),
            "--log",
            str(log_dir),
            "--evaluate-only",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    assert completed.returncode == 2, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["action"] == "refused"
    assert payload["reason"] == "goodhart_improvement"
    assert marker.read_text(encoding="utf-8") == "parent"

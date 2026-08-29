"""S02 — sealed one-use evaluation: the one accept, and every named refusal (ADR-0076).

The seal over the instrument digest, the alternate-import check that fires before any
evaluation runs, the one-use lineage registry, the adverse table, the Goodhart check and
the reversal proof. They belong together because they are a single decision taken once:
one sealed manifest yields either one immutable evaluation package or a refusal with a
reason, and a refusal is only meaningful beside the accept built the same way. Split
them and the accept drifts away from the refusals that are supposed to guard it.

The candidate's view is pinned here for the same reason: a candidate sees
`qualification_accept` and nothing else — no hidden items, no development score, no
privileged field — and the recorded `promote.evaluated` event carries no card and no
activation. Evaluation is not activation, and nothing on this path may imply that it
was."""

import json
from pathlib import Path
import pytest
from consilient.promote import (
    AdverseTable,
    CandidateInstrumentView,
    EvaluationPackage,
    EvaluationRefusal,
    LineageRegistry,
    candidate_visible,
    digest,
    find_forbidden_imports,
    privileged_fields,
    record_evaluation,
    reserve_qualification_batch,
    validate_adverse_table,
    verify_manifest_seal,
)
from promote_instrument_helpers import (
    TRAINING,
    _evaluate,
    _exp78,
    _manifest,
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

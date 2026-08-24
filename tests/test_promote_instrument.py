"""S02 — sealed one-use evaluation and reversal proof (ADR-0076)."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from consilient.promote import (
    CONTAINMENT_DENIED,
    CONTAINMENT_PROBE_SOURCE,
    CONTAINMENT_SOCKET_ESCAPED,
    CONTAINMENT_SOCKET_PROMPT,
    CONTAINMENT_WRITE_ESCAPED,
    CONTAINMENT_WRITE_PROMPT,
    AdverseTable,
    CandidateInstrumentView,
    EvaluationPackage,
    EvaluationRefusal,
    ExecuteFn,
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


def _loop_module():
    script = Path("scripts/promote_loop.py")
    spec = importlib.util.spec_from_file_location("promote_loop", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _loop_execute():
    return _loop_module().execute


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


def _run_candidate(
    source: str, prompts: list[str]
) -> tuple[bool, list[str | None]]:
    run_candidate = _loop_module().run_candidate
    return run_candidate(source, prompts)


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


def _contained_execute(
    source: str, prompts: list[str]
) -> tuple[bool, list[str | None]]:
    """Test double: report the probe denied, then run the candidate for real.

    A sandbox that actually blocked socket bind and out-of-scratch write would
    return these denials from the probe payload itself. This double stands in
    for that sandbox so scoring tests can still exercise the sealed instrument.
    """
    if source == CONTAINMENT_PROBE_SOURCE:
        return True, [CONTAINMENT_DENIED] * len(prompts)
    return _run_candidate(source, prompts)


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
    execute: ExecuteFn | None = None,
) -> EvaluationPackage | EvaluationRefusal:
    return evaluate_sealed(
        manifest,
        candidate_source=candidate,
        baseline_source=baseline,
        execute=_contained_execute if execute is None else execute,
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


def test_candidate_runs_in_another_process_without_parent_expected_answers():
    source = """
def solve(prompt):
    if prompt == "pid":
        return str(__import__("os").getpid())
    frame = __import__("sys")._getframe()
    while frame is not None:
        for value in frame.f_locals.values():
            if isinstance(value, (list, tuple)):
                for item in value:
                    if (
                        isinstance(item, (list, tuple))
                        and len(item) == 2
                        and item[0] == prompt
                    ):
                        return str(item[1])
        frame = frame.f_back
    return "expected-answer-not-found"
"""
    ran, score = _loop_execute()(
        source,
        [("pid", str(os.getpid())), ("sealed prompt", "sealed expected answer")],
    )
    assert ran is True
    assert score == 0.0


def test_candidate_timeout_kills_descendant_process_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = _loop_module()
    monkeypatch.setattr(module, "EXECUTION_TIMEOUT_SECONDS", 0.2)
    marker = tmp_path / "survived.txt"
    grandchild = (
        "import pathlib,time; time.sleep(0.8); "
        f"pathlib.Path({str(marker)!r}).write_text('survived', encoding='utf-8')"
    )
    source = f"""
def solve(prompt):
    subprocess = __import__("subprocess")
    sys = __import__("sys")
    subprocess.Popen([sys.executable, "-c", {grandchild!r}])
    __import__("time").sleep(60)
"""
    started = time.monotonic()
    ran, score = module.execute(source, [("prompt", "answer")])
    assert ran is False
    assert score == 0.0
    assert time.monotonic() - started < 5
    time.sleep(1)
    assert not marker.exists()


def test_hung_windows_taskkill_falls_back_to_direct_child_kill(monkeypatch):
    module = _loop_module()

    class Windows:
        name = "nt"

    class Process:
        pid = 123
        killed = False

        def poll(self):
            return None

        def kill(self):
            self.killed = True

    def hung_taskkill(argv, *, timeout, **kwargs):
        raise subprocess.TimeoutExpired(argv, timeout)

    process = Process()
    monkeypatch.setattr(module, "os", Windows())
    monkeypatch.setattr(module.subprocess, "run", hung_taskkill)
    module._kill_process_tree(process)
    assert process.killed is True


def test_candidate_cannot_crash_parent_with_malformed_child_output():
    source = """
__import__("sys").stdout.write("[]")
__import__("sys").stdout.flush()
__import__("os")._exit(0)
"""
    ran, score = _loop_execute()(source, [("prompt", "answer")])
    assert ran is False
    assert score == 0.0


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


def test_claimed_containment_does_not_skip_the_execute_probe():
    """A caller-supplied contained=True is not evidence. The probe is."""
    seen: list[tuple[str, tuple[str, ...]]] = []

    def execute(source: str, prompts: list[str]) -> tuple[bool, list[str | None]]:
        seen.append((source, tuple(prompts)))
        return True, [CONTAINMENT_DENIED] * len(prompts)

    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        execute=execute,
        contained=True,
    )
    assert seen, "evaluate_sealed never called execute"
    assert seen[0][0] == CONTAINMENT_PROBE_SOURCE
    assert seen[0][1] == (CONTAINMENT_SOCKET_PROMPT, CONTAINMENT_WRITE_PROMPT)
    assert isinstance(result, EvaluationPackage)


def test_socket_escape_through_execute_is_candidate_unexecutable():
    def execute(source: str, prompts: list[str]) -> tuple[bool, list[str | None]]:
        if list(prompts) == [CONTAINMENT_SOCKET_PROMPT, CONTAINMENT_WRITE_PROMPT]:
            return True, [CONTAINMENT_SOCKET_ESCAPED, CONTAINMENT_DENIED]
        raise AssertionError("scored a candidate after a socket escape")

    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        execute=execute,
        contained=True,
    )
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "candidate_unexecutable"


def test_out_of_scratch_write_through_execute_is_candidate_unexecutable():
    def execute(source: str, prompts: list[str]) -> tuple[bool, list[str | None]]:
        if list(prompts) == [CONTAINMENT_SOCKET_PROMPT, CONTAINMENT_WRITE_PROMPT]:
            return True, [CONTAINMENT_DENIED, CONTAINMENT_WRITE_ESCAPED]
        raise AssertionError("scored a candidate after an out-of-scratch write")

    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        execute=execute,
        contained=True,
    )
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "candidate_unexecutable"


def test_real_execute_path_escape_is_candidate_unexecutable():
    """The isolated child can still bind a socket and write outside scratch.

    That is the measured residual after Y02 process isolation. Scoring through
    that path is a false accept of an uncontained candidate.
    """
    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        execute=_run_candidate,
        contained=True,
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
    assert completed.returncode == 2, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["action"] == "refused"
    assert payload["reason"] == "candidate_unexecutable"
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
    assert payload["reason"] == "candidate_unexecutable"
    assert marker.read_text(encoding="utf-8") == "parent"

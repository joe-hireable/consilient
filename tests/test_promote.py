"""Native promoter invariants (V0-42 … V0-45)."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient import beta as beta_mod
from consilient.cli import build_parser
from consilient.events import SCHEMA_VERSION, append, read_all
from consilient.promote import (
    ACCEPTED,
    ALLOWLIST_PREFIXES,
    DISABLED,
    ENABLED_BY_DEFAULT,
    NO_IMPROVEMENT,
    NOT_ALLOWLISTED,
    NOT_EXECUTED,
    PROTECTED,
    PROTECTED_PREFIXES,
    REFUSED,
    THRESHOLD,
    UNMEASURED_BETA,
    Candidate,
    Decision,
    ExecutionEvidence,
    PromoteError,
    decide,
    digest,
    path_status,
    record,
    reverse,
)

SKILL = ".agents/skills/exp78/SKILL.md"


def measured_beta() -> beta_mod.Beta:
    n = 30
    false_accepts = 5
    return beta_mod.Beta(
        beta_mod.MEASURED,
        "self-mod-fixture",
        "exp78-training-v1",
        n,
        false_accepts,
        false_accepts / n,
        beta_mod.wilson(false_accepts, n),
        ("2026-08-01T00:00:00+00:00", "2026-08-21T00:00:00+00:00"),
        False,
    )


def insufficient_beta() -> beta_mod.Beta:
    return beta_mod.compute([])


def evidence(*, improved: bool = True, ran: bool = True) -> ExecutionEvidence:
    return ExecutionEvidence(
        ran=ran,
        suite_passed=ran,
        metric_before=0.2,
        metric_after=1.0 if improved else 0.2,
        verifier_version="exp78-training-v1",
    )


def candidate(
    *,
    path: str = SKILL,
    improved: bool = True,
    ran: bool = True,
    identity: str = "c1",
) -> Candidate:
    return Candidate(
        identity=identity,
        path=path,
        preimage_sha256=digest("before"),
        postimage_sha256=digest("after"),
        evidence=evidence(improved=improved, ran=ran),
    )


def test_loop_is_disabled_by_default():
    assert ENABLED_BY_DEFAULT is False
    decision = decide(candidate(), measured_beta())
    assert decision.action == "refuse"
    assert decision.reason == DISABLED


def test_unmeasured_beta_refuses_even_when_enabled():
    decision = decide(candidate(), insufficient_beta(), enabled=True)
    assert decision.action == "refuse"
    assert decision.reason == UNMEASURED_BETA


def test_measured_beta_at_threshold_refuses():
    n = 30
    false_accepts = 6
    measured = beta_mod.Beta(
        beta_mod.MEASURED,
        "self-mod-fixture",
        "exp78-training-v1",
        n,
        false_accepts,
        false_accepts / n,
        beta_mod.wilson(false_accepts, n),
        ("2026-08-01T00:00:00+00:00", "2026-08-21T00:00:00+00:00"),
        False,
    )
    assert measured.point == THRESHOLD
    decision = decide(candidate(), measured, enabled=True)
    assert decision.action == "refuse"
    assert decision.reason == "beta_above_threshold"


def test_not_executed_refuses():
    decision = decide(
        candidate(ran=False),
        measured_beta(),
        enabled=True,
    )
    assert decision.action == "refuse"
    assert decision.reason == NOT_EXECUTED


def test_no_improvement_refuses():
    decision = decide(
        candidate(improved=False),
        measured_beta(),
        enabled=True,
    )
    assert decision.action == "refuse"
    assert decision.reason == NO_IMPROVEMENT


def test_protected_path_refuses():
    decision = decide(
        candidate(path="src/consilient/beta.py"),
        measured_beta(),
        enabled=True,
    )
    assert decision.action == "refuse"
    assert decision.reason == PROTECTED
    assert path_status("src/consilient/promote.py") == PROTECTED
    assert path_status("tests/test_promote.py") == PROTECTED
    assert path_status("docs/10-research/experiment-register.md") == PROTECTED


def test_unlisted_path_refuses():
    decision = decide(
        candidate(path="src/consilient/harness.py"),
        measured_beta(),
        enabled=True,
    )
    assert decision.action == "refuse"
    assert decision.reason == NOT_ALLOWLISTED


def test_allowlisted_executed_improvement_promotes_only_when_enabled_and_measured():
    decision = decide(candidate(), measured_beta(), enabled=True)
    assert decision.action == "promote"
    assert SKILL.startswith(ALLOWLIST_PREFIXES[0])


def test_record_writes_through_append(tmp_path: Path):
    decision = decide(candidate(), insufficient_beta(), enabled=False)
    recorded = record(tmp_path, decision)
    events, rejected = read_all(tmp_path)
    assert rejected == []
    assert recorded["event"] == REFUSED
    assert events[0].kind == REFUSED
    assert events[0].data["reason"] == DISABLED
    assert events[0].actor == "consilient.promote"


def test_record_cannot_write_an_accept_for_a_refusal(tmp_path: Path):
    decision = decide(candidate(), insufficient_beta(), enabled=True)
    assert decision.action == "refuse"
    recorded = record(tmp_path, decision)
    assert recorded["event"] == REFUSED


def test_reverse_requires_a_recorded_promotion(tmp_path: Path):
    with pytest.raises(PromoteError, match="no recorded promotion"):
        reverse(tmp_path, "c1", digest("before"))


def test_reverse_records_the_preimage(tmp_path: Path):
    accepted = decide(candidate(), measured_beta(), enabled=True)
    record(tmp_path, accepted)
    reversed_event = reverse(tmp_path, "c1", digest("before"))
    assert reversed_event["event"] == "promote.reversed"
    events, rejected = read_all(tmp_path)
    assert rejected == []
    assert [event.kind for event in events] == [ACCEPTED, "promote.reversed"]
    assert events[1].data["preimage_sha256"] == digest("before")


def test_cli_still_has_exactly_six_commands():
    parser = build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    assert set(subparsers.choices) == {
        "record",
        "replay",
        "beta",
        "doctor",
        "dashboard",
        "usage",
    }
    assert "promote" not in subparsers.choices


def test_only_record_emits_accepted_in_the_product_tree():
    root = Path("src/consilient")
    emitters: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        text = path.read_text(encoding="utf-8")
        if ACCEPTED not in text and "promote.accepted" not in text:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "record":
                emitters.append(f"{path.as_posix()}:{node.name}")
    assert emitters == ["src/consilient/promote.py:record"]


def test_protected_prefixes_include_the_allowlist_itself():
    assert "src/consilient/promote.py" in PROTECTED_PREFIXES
    assert path_status(".agents/skills/foo.md") == "allowlisted"


def test_record_rejects_a_forged_promotion_without_improvement(tmp_path: Path):
    forged = Decision(
        "promote",
        "promoted",
        candidate(improved=False),
        True,
        measured_beta(),
    )
    with pytest.raises(PromoteError, match="no recorded execution evidence"):
        record(tmp_path, forged)


def test_record_rejects_a_forged_promotion_on_unmeasured_beta(tmp_path: Path):
    forged = Decision(
        "promote",
        "promoted",
        candidate(),
        True,
        insufficient_beta(),
    )
    with pytest.raises(PromoteError, match="unmeasured beta"):
        record(tmp_path, forged)


def test_direct_append_of_accepted_is_the_gap_events_py_was_too_dirty_to_close(
    tmp_path: Path,
):
    """events.py was already modified in this worktree, so validate does not
    yet refuse a bare promote.accepted. The product writer does. Named so the
    gap cannot be mistaken for a closed chokepoint.
    """
    now = datetime.now(timezone.utc)
    append(
        tmp_path / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": ACCEPTED,
            "actor": "consilient.promote",
            "data": {"note": "no evidence"},
        },
    )
    events, rejected = read_all(tmp_path)
    assert rejected == []
    assert events[0].kind == ACCEPTED
    assert events[0].data.get("execution") is None


def _loop_execute():
    script = Path("scripts/promote_loop.py")
    spec = importlib.util.spec_from_file_location("promote_loop", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.execute


def _exp78(name: str) -> str:
    return Path("docs/10-research/experiments/exp78", name).read_text(encoding="utf-8")


def test_helpful_improves_training_and_heldout():
    execute = _loop_execute()
    training = [
        (row["prompt"], row["expected"])
        for row in json.loads(_exp78("tasks.json"))
    ]
    heldout = [
        ("What is 5+2?", "7"),
        ("What is 6+1?", "7"),
        ("What is 3+4?", "7"),
        ("What is 9+9?", "18"),
        ("What is 0+0?", "0"),
    ]
    _, baseline = execute(_exp78("solver.py"), training)
    _, helpful_train = execute(_exp78("helpful.py"), training)
    _, helpful_held = execute(_exp78("helpful.py"), heldout)
    _, harmful_train = execute(_exp78("harmful.py"), training)
    _, harmful_held = execute(_exp78("harmful.py"), heldout)
    assert baseline == pytest.approx(0.2)
    assert helpful_train == 1.0
    assert helpful_held == 1.0
    assert harmful_train > baseline
    assert harmful_held == 0.0


def test_production_promoter_refuses_the_goodhart_candidate():
    execute = _loop_execute()
    training = [
        (row["prompt"], row["expected"])
        for row in json.loads(_exp78("tasks.json"))
    ]
    ran, metric = execute(_exp78("harmful.py"), training)
    _, before = execute(_exp78("solver.py"), training)
    harmful = Candidate(
        identity="harmful",
        path=SKILL,
        preimage_sha256=digest(_exp78("solver.py")),
        postimage_sha256=digest(_exp78("harmful.py")),
        evidence=ExecutionEvidence(
            ran=ran,
            suite_passed=ran,
            metric_before=before,
            metric_after=metric,
            verifier_version="exp78-training-v1",
        ),
    )
    decision = decide(harmful, insufficient_beta(), enabled=False)
    assert decision.action == "refuse"
    assert decision.reason == DISABLED

"""O01 — frozen minimum-stream plan."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient import work_items
from consilient.events import EventError, SCHEMA_VERSION, append, prefix_digest


def _current_log(log: Path) -> Path:
    """The daily log file the writes above actually landed in.

    These tests used `f"{TS[:10]}.jsonl"` -- a date literal -- while every write went through the
    real API, which names the file after the current date. The two agreed on 23 August 2026 and
    stopped agreeing at midnight, so eleven tests went red with no code change and the whole build
    queue stalled behind them: a unit only retires on a green suite. [measured 24 Aug 2026]

    Reading the directory instead of computing a date is immune to that, and also to a run that
    straddles midnight, which computing `date.today()` would not be.
    """
    files = sorted(log.glob("*.jsonl"), key=lambda q: q.stat().st_mtime)
    if not files:
        raise AssertionError(f"no daily log was written under {log}")
    return files[-1]

TS = "2026-08-23T12:00:00+00:00"
CONVERSATION_ID = "conv-plan-001"
TURN_ID = "turn-plan-001"
COMMITMENT_ID = "commit-plan-001"
PLAN_ID = "plan-001"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _minimal_commitment(**over: object) -> dict[str, object]:
    success_criteria = ["tests pass"]
    non_goals: list[str] = []
    contract: dict[str, object] = {
        "commitment_id": COMMITMENT_ID,
        "revision": 1,
        "conversation_id": CONVERSATION_ID,
        "source_turn_ids": [TURN_ID],
        "request_text": "ship the plan kernel",
        "goal_text": "freeze a minimum verifiable plan",
        "success_criteria": success_criteria,
        "non_goals": non_goals,
        "success_digest": work_items.success_digest(success_criteria, non_goals),
        "incumbent": {
            "name": "manual dispatch",
            "source": "measured",
            "retrieval_date": "2026-08-22",
            "search_digest": "0" * 64,
            "evidence_tag": "measured",
            "delta": "structured plan before native tasks",
            "killing_check": "plan digest mismatch",
        },
        "deliverable_contract": {
            "kind": "code",
            "handoff_schema": "git-diff",
            "allowed_locators": ["repository"],
        },
        "accountable": "delivery-owner",
        "composition": {"owner": "delivery-owner"},
        "assumptions": [],
        "autonomous_decision_refs": [],
        "reserved_decisions": [],
        "authority_ref": {"kind": "unprotected"},
        "verifier_contracts": [
            {
                "id": "pytest",
                "digest": "a" * 64,
                "task_family": "code",
                "required_outcome": "pass",
            }
        ],
        "mutation_scope": {"paths": ["src/consilient/"]},
        "budget_ref": "none",
        "expires_at": "2026-09-22T12:00:00+00:00",
        "question_count": 0,
    }
    contract.update(over)
    contract["source_turn_digest"] = work_items.source_turn_digest(
        str(contract["conversation_id"]),
        list(contract["source_turn_ids"]),
        {TURN_ID: "ship the plan kernel"},
    )
    contract["commitment_digest"] = work_items.commitment_digest(contract)
    return contract


def _handoff_contract() -> dict[str, str]:
    return {
        "schema": "git-diff",
        "digest": work_items.handoff_contract_digest("git-diff", ["repository"]),
    }


def _stream(
    *,
    stream_id: str = "S1",
    deliverable: str = "implement plan kernel",
    accountable: str = "owner-a",
    owned_paths: list[str] | None = None,
    dependencies: list[dict[str, object]] | None = None,
    integration: bool = False,
    title: str | None = None,
    model: str | None = None,
    specialism: str | None = None,
    verifier_contracts: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    stream: dict[str, object] = {
        "stream_id": stream_id,
        "deliverable": deliverable,
        "accountable": accountable,
        "owned_paths": owned_paths if owned_paths is not None else ["src/consilient/work_items.py"],
        "dependencies": dependencies or [],
        "deliverable_contract": {
            "kind": "code",
            "handoff_schema": "git-diff",
            "allowed_locators": ["repository"],
        },
        "handoff_contract": _handoff_contract(),
        "verifier_contracts": verifier_contracts
        or [
            {
                "id": "pytest",
                "digest": "a" * 64,
                "task_family": "code",
                "required_outcome": "pass",
            }
        ],
        "composition": {"owner": accountable},
        "checkpoint_required": True,
        "integration": integration,
    }
    if title is not None:
        stream["title"] = title
    if model is not None:
        stream["model"] = model
    if specialism is not None:
        stream["specialism"] = specialism
    return stream


def _minimal_plan(
    log: Path,
    commitment: dict[str, object] | None = None,
    *,
    streams: list[dict[str, object]] | None = None,
    **over: object,
) -> dict[str, object]:
    if commitment is None:
        work_items.seal_turn(
            log,
            conversation_id=CONVERSATION_ID,
            turn_id=TURN_ID,
            root_request_turn_id=TURN_ID,
            role="user",
            text="ship the plan kernel",
        )
        commitment = work_items.commit_request(log, _minimal_commitment())["data"]
    line_count = sum(1 for _ in _current_log(log).open(encoding="utf-8"))
    plan_streams = streams
    if plan_streams is None:
        plan_streams = [_stream(integration=True)]
    plan: dict[str, object] = {
        "plan_id": PLAN_ID,
        "revision": 1,
        "commitment_id": commitment["commitment_id"],
        "commitment_digest": commitment["commitment_digest"],
        "prefix_anchor": {
            "line_count": line_count,
            "prefix_digest": prefix_digest(_current_log(log), line_count),
        },
        "streams": plan_streams,
        "estimate_inputs": {
            "duration_lower_s": 60,
            "duration_upper_s": 600,
            "derivation": "cold start slice budget",
            "evidence_class": "asserted: low evidence",
        },
        "budget_ref": commitment["budget_ref"],
        "expires_at": commitment["expires_at"],
    }
    plan.update(over)
    plan["plan_digest"] = work_items.plan_digest(plan)
    return plan


def _seed_commitment(log: Path) -> dict[str, object]:
    work_items.seal_turn(
        log,
        conversation_id=CONVERSATION_ID,
        turn_id=TURN_ID,
        root_request_turn_id=TURN_ID,
        role="user",
        text="ship the plan kernel",
    )
    return work_items.commit_request(log, _minimal_commitment())["data"]


def test_plan_digest_is_deterministic_for_the_same_input(tmp_path):
    log = tmp_path / "log"
    plan = _minimal_plan(log)

    first = work_items.plan_digest(plan)
    shuffled = work_items.plan_digest(dict(sorted(plan.items(), reverse=True)))
    assert first == shuffled
    assert first == plan["plan_digest"]


def test_atomic_request_remains_one_stream(tmp_path):
    log = tmp_path / "log"
    plan = _minimal_plan(log, streams=[_stream(integration=True)])

    recorded = work_items.freeze_plan(log, plan)
    assert len(recorded["data"]["streams"]) == 1
    assert recorded["data"]["streams"][0]["integration"] is True


def test_independently_checkable_dependency_splits_into_two_streams(tmp_path):
    log = tmp_path / "log"
    producer = _stream(
        stream_id="S-producer",
        deliverable="produce interface",
        accountable="owner-a",
        owned_paths=["src/api.py"],
    )
    consumer = _stream(
        stream_id="S-consumer",
        deliverable="consume interface",
        accountable="owner-b",
        owned_paths=["src/client.py"],
        dependencies=[
            {
                "stream_id": "S-producer",
                "revision": 1,
                "handoff_contract_digest": producer["handoff_contract"]["digest"],
            }
        ],
        integration=True,
    )
    plan = _minimal_plan(log, streams=[producer, consumer])

    recorded = work_items.freeze_plan(log, plan)
    assert len(recorded["data"]["streams"]) == 2


def test_title_model_or_specialism_alone_cannot_split_streams(tmp_path):
    log = tmp_path / "log"
    producer = _stream(
        stream_id="S-producer",
        accountable="owner-a",
        owned_paths=["src/feature.py"],
        integration=False,
    )
    theatre = _stream(
        stream_id="S-theatre",
        deliverable=producer["deliverable"],
        accountable=producer["accountable"],
        owned_paths=list(producer["owned_paths"]),
        dependencies=list(producer["dependencies"]),
        title="Reviewer",
        model="claude",
        specialism="security",
        integration=False,
    )
    integration = _stream(
        stream_id="S-integration",
        deliverable="integrate feature",
        accountable="delivery-owner",
        owned_paths=["src/feature.py"],
        dependencies=[
            {
                "stream_id": "S-producer",
                "revision": 1,
                "handoff_contract_digest": producer["handoff_contract"]["digest"],
            }
        ],
        integration=True,
    )
    plan = _minimal_plan(log, streams=[producer, theatre, integration])

    with pytest.raises(EventError, match="specialism alone"):
        work_items.freeze_plan(log, plan)


def test_cycles_missing_predecessors_and_pathless_streams_are_refused(tmp_path):
    log = tmp_path / "log"
    commitment = _seed_commitment(log)
    cyclic_a = _stream(
        stream_id="A",
        owned_paths=["src/a.py"],
        dependencies=[
            {
                "stream_id": "B",
                "revision": 1,
                "handoff_contract_digest": _handoff_contract()["digest"],
            }
        ],
    )
    cyclic_b = _stream(
        stream_id="B",
        owned_paths=["src/b.py"],
        dependencies=[
            {
                "stream_id": "A",
                "revision": 1,
                "handoff_contract_digest": _handoff_contract()["digest"],
            }
        ],
        integration=True,
    )
    with pytest.raises(EventError, match="cycle"):
        work_items.freeze_plan(
            log,
            _minimal_plan(log, commitment=commitment, streams=[cyclic_a, cyclic_b]),
        )

    missing = _stream(
        stream_id="S-only",
        dependencies=[
            {
                "stream_id": "missing",
                "revision": 1,
                "handoff_contract_digest": _handoff_contract()["digest"],
            }
        ],
        integration=True,
    )
    with pytest.raises(EventError, match="missing predecessor"):
        work_items.freeze_plan(
            log, _minimal_plan(log, commitment=commitment, streams=[missing])
        )

    pathless = _stream(stream_id="S1", owned_paths=[], integration=False)
    integration = _stream(stream_id="S2", owned_paths=["src/b.py"], integration=True)
    with pytest.raises(EventError, match="owned_paths"):
        work_items.freeze_plan(
            log,
            _minimal_plan(log, commitment=commitment, streams=[pathless, integration]),
        )


def test_future_artefact_digests_are_forbidden_in_the_frozen_plan(tmp_path):
    log = tmp_path / "log"
    bad_dependency = _stream(
        stream_id="S1",
        dependencies=[
            {
                "stream_id": "S0",
                "revision": 1,
                "handoff_contract_digest": _handoff_contract()["digest"],
                "artefact_digest": "f" * 64,
            }
        ],
        integration=True,
    )
    with pytest.raises(EventError, match="artefact_digest"):
        work_items.freeze_plan(log, _minimal_plan(log, streams=[bad_dependency]))


def test_overlapping_paths_require_an_explicit_integration_owner(tmp_path):
    log = tmp_path / "log"
    commitment = _seed_commitment(log)
    first = _stream(stream_id="S1", accountable="owner-a", owned_paths=["src/shared.py"])
    second = _stream(
        stream_id="S2",
        accountable="owner-b",
        owned_paths=["src/shared.py"],
        deliverable="integrate shared surface",
        integration=True,
    )
    with pytest.raises(EventError, match="integration_owner"):
        work_items.freeze_plan(
            log, _minimal_plan(log, commitment=commitment, streams=[first, second])
        )

    plan = _minimal_plan(
        log,
        commitment=commitment,
        streams=[first, second],
        integration_owner="delivery-owner",
    )
    work_items.freeze_plan(log, plan)


def test_generic_append_and_helper_agree_on_plan_validation(tmp_path):
    log = tmp_path / "log"
    plan = _minimal_plan(log)
    helper_event = work_items.freeze_plan(log, plan)
    assert helper_event["data"]["plan_digest"] == plan["plan_digest"]

    bad = {
        "v": SCHEMA_VERSION,
        "ts": _now(),
        "event": work_items.PLAN_FROZEN,
        "actor": work_items.DEFAULT_ACTOR,
        "data": dict(plan, plan_digest="0" * 64),
    }
    with pytest.raises(EventError, match="plan_digest"):
        append(log / f"{_now()[:10]}.jsonl", bad)


def test_plan_must_follow_a_matching_commitment_in_the_prefix(tmp_path):
    log = tmp_path / "log"
    commitment = _seed_commitment(log)
    line_count = sum(1 for _ in _current_log(log).open(encoding="utf-8"))
    plan = {
        "plan_id": PLAN_ID,
        "revision": 1,
        "commitment_id": commitment["commitment_id"],
        "commitment_digest": commitment["commitment_digest"],
        "prefix_anchor": {
            "line_count": line_count,
            "prefix_digest": prefix_digest(_current_log(log), line_count),
        },
        "streams": [_stream(integration=True)],
        "estimate_inputs": {
            "duration_lower_s": 60,
            "duration_upper_s": 600,
            "derivation": "cold start slice budget",
            "evidence_class": "asserted: low evidence",
        },
        "budget_ref": commitment["budget_ref"],
        "expires_at": commitment["expires_at"],
        "plan_digest": "0" * 64,
    }
    plan["plan_digest"] = work_items.plan_digest(plan)
    bad_plan = dict(plan, commitment_digest="f" * 64)
    bad_plan["plan_digest"] = work_items.plan_digest(bad_plan)
    with pytest.raises(EventError, match="commitment"):
        append(log / f"{_now()[:10]}.jsonl", {
            "v": SCHEMA_VERSION,
            "ts": _now(),
            "event": work_items.PLAN_FROZEN,
            "actor": work_items.DEFAULT_ACTOR,
            "data": bad_plan,
        })


def test_outcome_aware_plan_edit_is_refused_after_freeze(tmp_path):
    log = tmp_path / "log"
    commitment = _seed_commitment(log)
    first = work_items.freeze_plan(log, _minimal_plan(log, commitment=commitment))
    edited = _minimal_plan(
        log,
        commitment=commitment,
        revision=2,
        supersedes_plan_digest=first["data"]["plan_digest"],
        streams=[
            _stream(
                integration=True,
                verifier_contracts=[
                    {
                        "id": "pytest",
                        "digest": "b" * 64,
                        "task_family": "code",
                        "required_outcome": "pass-after-failure",
                    }
                ],
            )
        ],
    )
    with pytest.raises(EventError, match="outcome-aware"):
        work_items.freeze_plan(log, edited)


def test_exactly_one_integration_stream_is_required(tmp_path):
    log = tmp_path / "log"
    commitment = _seed_commitment(log)
    none_integration = _minimal_plan(
        log,
        commitment=commitment,
        streams=[
            _stream(stream_id="S1", integration=False),
            _stream(stream_id="S2", integration=False, owned_paths=["src/b.py"]),
        ],
    )
    with pytest.raises(EventError, match="integration"):
        work_items.freeze_plan(log, none_integration)

    two_integration = _minimal_plan(
        log,
        commitment=commitment,
        streams=[
            _stream(stream_id="S1", integration=True),
            _stream(stream_id="S2", integration=True, owned_paths=["src/b.py"]),
        ],
    )
    with pytest.raises(EventError, match="integration"):
        work_items.freeze_plan(log, two_integration)

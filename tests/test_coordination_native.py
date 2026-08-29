"""Native work items: what must be true of a commitment, a plan and its streams before a
unit may be claimed at all.

The subject here is admission on grounds other than the path — readiness and scope, not
the lease. The builders (`_commitment`, `_stream`, `_plan`, `_native_item`) construct
the full digest-linked chain, because the readiness check is only meaningful against a
plan whose digest the item actually carries; they are long, and they are here rather
than in the shared module because nothing outside this file needs them.

Four refusals are pinned. A stale revision is refused when the prefix already holds a
later one. A pathless item is refused, because a unit owning nothing cannot be given a
lease. A dependent whose predecessor has not delivered is unready, even when the caller
supplies bindings that look complete. And composite exposure is refused unless the
estimate matches the scope it is being spent against: a mutation-proxy β is not a human-
verdict β, and a `docs` task family may not borrow a `code` measurement. Only the fully
matched case is admitted, at `n_attempt_max == 1`.

`claim_ready_work` is the composition of all of it — it binds the fencing epoch and the
ticket reference on success, and raises `ClaimReadyError` naming "unready" for the
dependent whose source stream has not completed."""

from datetime import datetime, timezone
from pathlib import Path
import pytest
from consilient import coordination, work_items
from consilient.beta import MEASURED, Beta
from consilient.events import Event
from coordination_helpers import (
    T0,
)

# --- T02 atomic readiness, claim and fencing ----------------------------------


DIGEST = "a" * 64

HANDOFF = "b" * 64


def test_admit_composite_exposure_refuses_unwired_proxy_and_mismatched_scope():
    measured = Beta(
        MEASURED, "code", "pytest-v1", 163, 51, 0.3132, (0.2926, 0.3346), None
    )
    missing = coordination.admit_composite_exposure(
        candidate_ordinal=1,
        task_family="code",
        protocol_id="pytest",
        protocol_version="pytest-v1",
        epsilon=0.40,
    )
    assert missing.admitted is False
    assert missing.recorded_exposure is False
    proxy = coordination.admit_composite_exposure(
        candidate_ordinal=1,
        task_family="code",
        protocol_id="pytest",
        protocol_version="pytest-v1",
        epsilon=0.40,
        estimate=measured,
        estimand_kind="mutation_proxy_beta",
        auth_status="authenticated",
    )
    assert proxy.admitted is False
    mismatched = coordination.admit_composite_exposure(
        candidate_ordinal=1,
        task_family="docs",
        protocol_id="pytest",
        protocol_version="pytest-v1",
        epsilon=0.40,
        estimate=measured,
        estimand_kind="human_verdict_beta",
        auth_status="authenticated",
    )
    assert mismatched.admitted is False
    admitted = coordination.admit_composite_exposure(
        candidate_ordinal=1,
        task_family="code",
        protocol_id="pytest",
        protocol_version="pytest-v1",
        epsilon=0.40,
        estimate=measured,
        estimand_kind="human_verdict_beta",
        auth_status="authenticated",
    )
    assert admitted.admitted is True
    assert admitted.n_attempt_max == 1


def test_native_readiness_refuses_unready_stale_pathless_and_mismatched_predecessors():
    from consilient.events import SCHEMA_VERSION

    def opened(
        ticket: str, revision: int, *, owned: list[str], deps: list[object]
    ) -> Event:
        return Event(
            {
                "v": SCHEMA_VERSION,
                "ts": T0.isoformat(),
                "event": work_items.OPENED,
                "actor": "owner",
                "data": {
                    "ticket": ticket,
                    "revision": revision,
                    "item_schema": work_items.NATIVE_SCHEMA,
                    "owned_paths": owned,
                    "dependencies": deps,
                    "plan_digest": DIGEST,
                },
            }
        )

    prefix = (opened("native:source", 2, owned=["src/a.py"], deps=[]),)
    assert (
        coordination.native_readiness_refusal(
            prefix,
            ticket="native:source",
            revision=1,
            predecessor_bindings=[],
            cwd=Path("."),
        )
        is not None
    )
    assert "stale-revision" in (
        coordination.native_readiness_refusal(
            (
                opened("native:source", 1, owned=["src/a.py"], deps=[]),
                opened("native:source", 2, owned=["src/a.py"], deps=[]),
            ),
            ticket="native:source",
            revision=1,
            predecessor_bindings=[],
            cwd=Path("."),
        )
        or ""
    )
    assert "pathless" in (
        coordination.native_readiness_refusal(
            (opened("native:empty", 1, owned=[], deps=[]),),
            ticket="native:empty",
            revision=1,
            predecessor_bindings=[],
            cwd=Path("."),
        )
        or ""
    )
    assert "unready" in (
        coordination.native_readiness_refusal(
            (
                opened(
                    "native:child",
                    1,
                    owned=["src/child.py"],
                    deps=[
                        {
                            "ticket": "native:source",
                            "revision": 1,
                            "handoff_contract_digest": HANDOFF,
                        }
                    ],
                ),
            ),
            ticket="native:child",
            revision=1,
            predecessor_bindings=[
                {
                    "ticket": "native:source",
                    "revision": 1,
                    "handoff_contract_digest": HANDOFF,
                    "artefact_digest": DIGEST,
                    "receipt_digest": DIGEST,
                }
            ],
            cwd=Path("."),
        )
        or ""
    )


def _commitment() -> dict[str, object]:
    data: dict[str, object] = {
        "commitment_id": "commit-1",
        "revision": 1,
        "conversation_id": "conversation-1",
        "source_turn_ids": ["turn-1"],
        "source_turn_digest": DIGEST,
        "request_text": "Build T02",
        "goal_text": "Build T02",
        "success_criteria": ["atomic claim"],
        "non_goals": [],
        "success_digest": work_items.success_digest(["atomic claim"], []),
        "incumbent": {
            "name": "Kleppmann fencing tokens",
            "source": "repository",
            "retrieval_date": "2026-08-24",
            "search_digest": DIGEST,
            "evidence_tag": "cited",
            "delta": "atomic claim at the trajectory writer",
            "killing_check": "two overlapping claims both live",
        },
        "deliverable_contract": {
            "kind": "code",
            "handoff_schema": "git-diff",
            "allowed_locators": ["repository"],
        },
        "accountable": "owner",
        "composition": {"owner": "owner"},
        "assumptions": [],
        "autonomous_decision_refs": [],
        "reserved_decisions": [],
        "authority_ref": {"kind": "unprotected"},
        "verifier_contracts": [
            {
                "id": "pytest",
                "digest": DIGEST,
                "task_family": "code",
                "required_outcome": "pass",
            }
        ],
        "mutation_scope": {"paths": ["src/"]},
        "budget_ref": "local",
        "expires_at": "2026-09-01T00:00:00+00:00",
        "question_count": 0,
    }
    data["commitment_digest"] = work_items.commitment_digest(data)
    return data


def _stream(stream_id: str, dependencies: list[dict[str, object]]) -> dict[str, object]:
    return {
        "stream_id": stream_id,
        "deliverable": f"{stream_id} deliverable",
        "accountable": "owner",
        "owned_paths": [f"src/{stream_id}.py"],
        "dependencies": dependencies,
        "deliverable_contract": {
            "kind": "code",
            "handoff_schema": "git-diff",
            "allowed_locators": ["repository"],
        },
        "handoff_contract": {"schema": "git-diff", "digest": HANDOFF},
        "verifier_contracts": [
            {
                "id": "pytest",
                "digest": DIGEST,
                "task_family": "code",
                "required_outcome": "pass",
            }
        ],
        "composition": {"owner": "owner"},
        "checkpoint_required": True,
        "integration": stream_id == "integration",
    }


def _plan() -> dict[str, object]:
    commitment = _commitment()
    data: dict[str, object] = {
        "plan_id": "plan-1",
        "revision": 1,
        "commitment_id": commitment["commitment_id"],
        "commitment_digest": commitment["commitment_digest"],
        "prefix_anchor": {"line_count": 0, "prefix_digest": DIGEST},
        "streams": [
            _stream("source", []),
            _stream(
                "integration",
                [
                    {
                        "stream_id": "source",
                        "revision": 1,
                        "handoff_contract_digest": HANDOFF,
                    }
                ],
            ),
        ],
        "integration_owner": "owner",
        "estimate_inputs": {
            "duration_lower_s": 1,
            "duration_upper_s": 60,
            "derivation": "bounded slice",
            "evidence_class": "asserted",
        },
        "budget_ref": "local",
        "expires_at": "2026-09-01T00:00:00+00:00",
    }
    data["plan_digest"] = work_items.plan_digest(data)
    return data


def _native_item(plan: dict[str, object], stream_id: str) -> dict[str, object]:
    stream = next(item for item in plan["streams"] if item["stream_id"] == stream_id)
    dependencies = [
        {
            "ticket": f"native:{dependency['stream_id']}",
            "revision": dependency["revision"],
            "handoff_contract_digest": dependency["handoff_contract_digest"],
        }
        for dependency in stream["dependencies"]
    ]
    return {
        "ticket": f"native:{stream_id}",
        "revision": 1,
        "plan_id": plan["plan_id"],
        "plan_digest": plan["plan_digest"],
        "stream_id": stream_id,
        "goal_text": f"Deliver {stream_id}",
        "success_digest": DIGEST,
        "incumbent": _commitment()["incumbent"],
        "deliverable_contract": stream["deliverable_contract"],
        "accountable": "owner",
        "authority_ref": {"kind": "unprotected"},
        "verifier_contracts": stream["verifier_contracts"],
        "dependencies": dependencies,
        "owned_paths": stream["owned_paths"],
        "budget_ref": "local",
        "expires_at": "2026-09-01T00:00:00+00:00",
        "exposure_contract": {
            "key": "goal:code",
            "epsilon": 0.1,
            "rule": "frozen",
            "beta_version": "unestimated",
            "n_max": 0,
        },
        "composition": {"owner": "owner"},
    }


def test_claim_ready_work_binds_epoch_and_refuses_an_unready_dependent(tmp_path):
    log = tmp_path / "log"
    plan = _plan()
    seeded = datetime.now(timezone.utc).isoformat()
    work_items.commit_request(log, _commitment(), ts=seeded)
    work_items.freeze_plan(log, plan, ts=seeded)
    work_items.open_native_item(log, _native_item(plan, "source"), ts=seeded)
    work_items.open_native_item(log, _native_item(plan, "integration"), ts=seeded)
    claimed = coordination.claim_ready_work(
        log,
        run_id="ready-source",
        cwd=tmp_path,
        timeout_s=600,
        ticket="native:source",
        revision=1,
        attempt_id="attempt-1",
        harness="grok",
        model="grok",
        family="grok",
        pool="grok-weekly",
        capability_context_digest=DIGEST,
        candidate_ordinal=1,
        predecessor_bindings=[],
        task_family="code",
        protocol_id="pytest",
        protocol_version="pytest-v1",
        epsilon=0.40,
        now=T0,
    )
    assert claimed["data"]["fencing_epoch"] == 1
    assert claimed["data"]["ticket_ref"] == "native:source"
    with pytest.raises(coordination.ClaimReadyError, match="unready"):
        coordination.claim_ready_work(
            log,
            run_id="blocked-integration",
            cwd=tmp_path,
            timeout_s=600,
            ticket="native:integration",
            revision=1,
            attempt_id="attempt-2",
            harness="grok",
            model="grok",
            family="grok",
            pool="grok-weekly",
            capability_context_digest=DIGEST,
            candidate_ordinal=1,
            predecessor_bindings=[
                {
                    "ticket": "native:source",
                    "revision": 1,
                    "handoff_contract_digest": HANDOFF,
                    "artefact_digest": DIGEST,
                    "receipt_digest": DIGEST,
                }
            ],
            task_family="code",
            protocol_id="pytest",
            protocol_version="pytest-v1",
            epsilon=0.40,
            now=T0,
        )

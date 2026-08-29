"""The scaffolding every delivery-estimate test needs: a sealed turn, a committed
request, a frozen plan whose digest chains back to it, and prior dispatch outcomes in
the cohort.

One definition of a well-formed plan is kept here on purpose. `_seed_plan` seals the
turn, commits the minimal contract, anchors the plan to the log prefix by line count and
prefix digest, and freezes it — a plan built any other way would test the builder rather
than the invariant. Its `estimate_inputs` carry the cold-start slice budget of 120 s to
900 s tagged `asserted: low evidence`, which is the fallback the derivation tests
exercise.

`COHORT` is the four-part cohort key — artefact kind, verifier contract digest, size
band and route capability class — and `_analogue_outcome` writes a prior
`dispatch.outcome` stamped with it, since only outcomes sharing the cohort may be drawn
on as analogues. `_log_file` returns the single day file the log already holds, so that
appends and prefix digests address the same file throughout a test."""

from datetime import datetime, timezone
from pathlib import Path
from consilient import events, work_items
from consilient.events import SCHEMA_VERSION, append

CONVERSATION_ID = "conv-est-001"

TURN_ID = "turn-est-001"

COMMITMENT_ID = "commit-est-001"

PLAN_ID = "plan-est-001"

DELIVERY_ID = "delivery-est-001"

COHORT = {
    "artefact_kind": "code",
    "verifier_contract_digest": "a" * 64,
    "size_band": "small",
    "route_capability_class": "cursor-composer",
}

RESOURCE_SNAPSHOT = "b" * 64


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _issued() -> datetime:
    return datetime.now(timezone.utc)


def _event(
    kind: str, data: dict[str, object], *, ts: str | None = None
) -> dict[str, object]:
    stamp = ts or _now()
    return {
        "v": SCHEMA_VERSION,
        "ts": stamp,
        "event": kind,
        "actor": events.DELIVERY_ACTOR,
        "data": data,
    }


def _log_file(log: Path) -> Path:
    files = sorted(log.glob("*.jsonl"))
    if files:
        return files[0]
    stamp = _now()
    return log / f"{stamp[:10]}.jsonl"


def _minimal_commitment(**over: object) -> dict[str, object]:
    success_criteria = ["tests pass"]
    non_goals: list[str] = []
    contract: dict[str, object] = {
        "commitment_id": COMMITMENT_ID,
        "revision": 1,
        "conversation_id": CONVERSATION_ID,
        "source_turn_ids": [TURN_ID],
        "request_text": "ship delivery estimate",
        "goal_text": "freeze estimate before work",
        "success_criteria": success_criteria,
        "non_goals": non_goals,
        "success_digest": work_items.success_digest(success_criteria, non_goals),
        "incumbent": {
            "name": "manual dispatch",
            "source": "measured",
            "retrieval_date": "2026-08-22",
            "search_digest": "0" * 64,
            "evidence_tag": "measured",
            "delta": "dated window before claims",
            "killing_check": "estimate ordering",
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
                "digest": COHORT["verifier_contract_digest"],
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
        {TURN_ID: "ship delivery estimate"},
    )
    contract["commitment_digest"] = work_items.commitment_digest(contract)
    return contract


def _stream(*, stream_id: str = "S1", integration: bool = True) -> dict[str, object]:
    return {
        "stream_id": stream_id,
        "deliverable": "implement estimate",
        "accountable": "owner-a",
        "owned_paths": ["src/consilient/events.py"],
        "dependencies": [],
        "deliverable_contract": {
            "kind": "code",
            "handoff_schema": "git-diff",
            "allowed_locators": ["repository"],
        },
        "handoff_contract": {
            "schema": "git-diff",
            "digest": work_items.handoff_contract_digest("git-diff", ["repository"]),
        },
        "verifier_contracts": [
            {
                "id": "pytest",
                "digest": COHORT["verifier_contract_digest"],
                "task_family": "code",
                "required_outcome": "pass",
            }
        ],
        "composition": {"owner": "owner-a"},
        "checkpoint_required": True,
        "integration": integration,
    }


def _seed_plan(log: Path) -> dict[str, object]:
    work_items.seal_turn(
        log,
        conversation_id=CONVERSATION_ID,
        turn_id=TURN_ID,
        root_request_turn_id=TURN_ID,
        role="user",
        text="ship delivery estimate",
    )
    commitment = work_items.commit_request(log, _minimal_commitment())["data"]
    line_count = sum(1 for _ in _log_file(log).open(encoding="utf-8"))
    plan: dict[str, object] = {
        "plan_id": PLAN_ID,
        "revision": 1,
        "commitment_id": commitment["commitment_id"],
        "commitment_digest": commitment["commitment_digest"],
        "prefix_anchor": {
            "line_count": line_count,
            "prefix_digest": events.prefix_digest(_log_file(log), line_count),
        },
        "streams": [_stream()],
        "estimate_inputs": {
            "duration_lower_s": 120,
            "duration_upper_s": 900,
            "derivation": "cold start slice budget",
            "evidence_class": "asserted: low evidence",
        },
        "budget_ref": commitment["budget_ref"],
        "expires_at": commitment["expires_at"],
        "plan_digest": "",
    }
    plan["plan_digest"] = work_items.plan_digest(plan)
    work_items.freeze_plan(log, plan)
    return plan


def _analogue_outcome(
    log: Path,
    *,
    duration_s: float,
    timed_out: bool = False,
    status: str = "ok",
    ts: str = "2026-08-22T10:00:00+00:00",
) -> dict[str, object]:
    stamp = _now()
    payload = _event(
        "dispatch.outcome",
        {
            "run_id": f"run-{duration_s}",
            "task": "prior delivery",
            "cwd": "/tmp",
            "harness": "cursor",
            "family": "cursor",
            "pool": "cursor-models",
            "status": status,
            "reason": "done",
            "exit_code": 0 if status == "ok" else 1,
            "artefact_bytes": 10,
            "diff_bytes": 5,
            "timed_out": timed_out,
            "duration_s": duration_s,
            "command": ["echo"],
            "supervised": True,
            "estimate_cohort": dict(COHORT),
            "occurred_at": ts,
        },
        ts=stamp,
    )
    return append(_log_file(log), payload)

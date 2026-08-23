"""Durable pre-action decisions bind planning to exact earlier evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient import events


DIGEST = "a" * 64
REFERENCE = {
    "event_id": "00000000-0000-4000-8000-000000000001",
    "event_kind": "evidence.observed",
    "event_sha256": DIGEST,
}


def event(kind: str, data: dict[str, object], *, actor: str = "owner") -> dict[str, object]:
    return {
        "v": events.SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": kind,
        "actor": actor,
        "data": data,
    }


def reference(raw: events.EventPayload) -> dict[str, str]:
    return {
        "event_id": raw["event_id"],
        "event_kind": raw["event"],
        "event_sha256": events.event_sha256(raw),
    }


def protocol(
    status: str = "not_warranted",
    *,
    refs: dict[str, str] | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "status": status,
        "threshold": {
            "version": "better-than-best.v1",
            "later_reliance": "false" if status == "not_warranted" else "true",
            "question_open": "true",
            "wrong_costs_more": "true",
        },
    }
    if status == "completed":
        assert refs is not None
        record.update(
            {
                "instructions_ref": dict(refs),
                "bar_ref": dict(refs),
                "search_ref": dict(refs),
                "killing_check_ref": dict(refs),
            }
        )
    return record


def binding(admission_class: str) -> dict[str, object]:
    if admission_class == "material_choice":
        return {"kind": admission_class}
    if admission_class in {"contained_execution", "proof_operation"}:
        return {
            "kind": admission_class,
            "effect_manifest_digest": "1" * 64,
            "sandbox_policy_digest": "2" * 64,
            "verifier_policy_digest": "3" * 64,
            "expected_receipt_digest": "4" * 64,
        }
    if admission_class == "recoverable_mutation":
        return {
            "kind": admission_class,
            "effect_manifest_digest": "1" * 64,
            "sandbox_policy_digest": "2" * 64,
            "verifier_policy_digest": "3" * 64,
            "expected_receipt_digest": "4" * 64,
            "recovery_proof_digest": "5" * 64,
        }
    protected: dict[str, object] = {
        "kind": admission_class,
        "protected_class": "principal_authority",
        "effect_manifest_digest": "1" * 64,
    }
    if admission_class == "protected_covered":
        protected["authority_ref"] = dict(REFERENCE)
    return protected


def planning(
    admission_class: str = "material_choice",
    *,
    record_level: str | None = None,
    protocol_record: dict[str, object] | None = None,
    evidence_refs: list[dict[str, str]] | None = None,
    decision_id: str = "decision-1",
    operation_id: str = "operation-1",
    ticket: str = "WORK-1",
    supersedes: dict[str, str] | None = None,
) -> dict[str, object]:
    protected = admission_class in {"protected_covered", "protected_uncovered"}
    if record_level is None:
        record_level = "full" if protected else "minimal"
    record: dict[str, object] = {
        "decision_id": decision_id,
        "operation_id": operation_id,
        "ticket": ticket,
        "owner": "owner",
        "actor": "owner",
        "record_level": record_level,
        "decision": "Use the accepted standard-library path",
        "reasoning": "It is the smallest path satisfying the frozen contract",
        "falsifier": "A required effect cannot be represented",
        "reversal": {"kind": "inverse", "value": "consilient.events.validate"},
        "alternatives": [
            {"option": "Add a dependency", "rejected_because": "No dependency is needed"}
        ],
        "evidence_refs": evidence_refs or [dict(REFERENCE)],
        "acceptance_contract_digest": "b" * 64,
        "protocol": protocol_record or protocol(),
        "binding": binding(admission_class),
    }
    if supersedes is not None:
        record["supersedes"] = supersedes
    return record


def decision(**overrides: object) -> dict[str, object]:
    record = planning()
    record.update(overrides)
    return event(events.DECISION_KIND, record)


def proposal(
    admission_class: str,
    *,
    proposal_id: str = "proposal-1",
    **overrides: object,
) -> dict[str, object]:
    record = planning(admission_class)
    record.update(overrides)
    return event("action.proposal", {"proposal_id": proposal_id, "planning": record})


@pytest.mark.parametrize(
    ("admission_class", "kind", "accepted"),
    (
        ("observation", events.DECISION_KIND, False),
        ("contained_execution", events.DECISION_KIND, True),
        ("proof_operation", events.DECISION_KIND, True),
        ("material_choice", events.DECISION_KIND, True),
        ("recoverable_mutation", events.DECISION_KIND, True),
        ("protected_covered", "action.proposal", True),
        ("protected_uncovered", "action.proposal", True),
        ("capability_gap", events.DECISION_KIND, False),
    ),
)
def test_each_admission_class_has_one_decision_or_proposal_shape(
    admission_class: str, kind: str, accepted: bool
) -> None:
    candidate = (
        proposal(admission_class)
        if kind == "action.proposal"
        else event(kind, planning(admission_class))
    )
    if accepted:
        events.validate(candidate)
    else:
        with pytest.raises(events.EventError, match="admission"):
            events.validate(candidate)


@pytest.mark.parametrize("record_level", ("minimal", "full"))
@pytest.mark.parametrize("use_only_admissible", (False, True))
def test_both_record_depths_require_real_alternatives_or_only_admissible_rules(
    record_level: str, use_only_admissible: bool
) -> None:
    status = "completed" if record_level == "full" else "not_warranted"
    record = planning(
        record_level=record_level,
        protocol_record=protocol(status, refs=REFERENCE if status == "completed" else None),
    )
    if use_only_admissible:
        record["alternatives"] = []
        record["only_admissible"] = {"rule_refs": ["ADR-0075", "ADR-0079"]}

    events.validate(event(events.DECISION_KIND, record))

    record["alternatives"] = []
    record.pop("only_admissible", None)
    with pytest.raises(events.EventError, match="only_admissible"):
        events.validate(event(events.DECISION_KIND, record))


def test_completed_protocol_requires_full_record_and_all_completion_references() -> None:
    completed = protocol("completed", refs=REFERENCE)
    completed.pop("search_ref")
    with pytest.raises(events.EventError, match="search_ref"):
        events.validate(
            decision(record_level="full", protocol=completed)
        )

    with pytest.raises(events.EventError, match="record_level"):
        events.validate(
            decision(record_level="minimal", protocol=protocol("completed", refs=REFERENCE))
        )


def test_class_binding_cannot_copy_a_future_result_backwards() -> None:
    class_binding = binding("contained_execution")
    class_binding["result"] = "passed"
    with pytest.raises(events.EventError, match="binding"):
        events.validate(decision(binding=class_binding))


def test_legacy_syntactic_decision_remains_audit_only() -> None:
    legacy = event(
        events.DECISION_KIND,
        {
            "decision": "Keep the existing audit record",
            "reasoning": "EXP-106 has not activated structural admission",
            "falsifier": "The treatment is activated",
            "reversal": {"kind": "inverse", "value": "consilient.events.validate"},
        },
    )

    events.validate(legacy)
    assert events.decision_protocol_data(legacy) is None


def test_principal_authority_cannot_be_recorded_as_an_autonomous_decision() -> None:
    candidate = event(
        events.DECISION_KIND,
        {
            "decision": "Approve the protected action",
            "reasoning": "The agent proposes approval",
            "falsifier": "The principal refuses",
            "reversal": {"kind": "inverse", "value": "consilient.events.validate"},
            "class": "principal_authority",
        },
    )

    with pytest.raises(events.EventError, match="protected.*cannot be autonomous"):
        events.validate(candidate)


def append_source(path: Path, *, kind: str = "evidence.observed") -> events.EventPayload:
    raw = event(kind, {"claim": "independent observation"})
    return events.append(path, raw)


def test_decision_references_resolve_to_exact_earlier_events(tmp_path: Path) -> None:
    log = tmp_path / "events.jsonl"
    source = append_source(log)
    exact = reference(source)
    candidate = decision(evidence_refs=[exact])

    events.append(log, candidate)

    mismatched = decision(
        decision_id="decision-2",
        operation_id="operation-2",
        evidence_refs=[{**exact, "event_sha256": "0" * 64}],
    )
    with pytest.raises(events.EventError, match="event_sha256"):
        events.append(log, mismatched)


def test_decision_reference_cannot_point_later_in_the_same_transaction(tmp_path: Path) -> None:
    source = event("evidence.observed", {"claim": "later"})
    source["event_id"] = events.new_event_id()
    later_ref = reference(source)
    candidate = decision(evidence_refs=[later_ref])

    with pytest.raises(events.EventError, match="earlier"):
        events.append_transaction(tmp_path, [candidate, source], lambda p, r, c: None)


@pytest.mark.parametrize("duplicate", ("decision_id", "operation_id"))
def test_decision_identity_and_operation_binding_are_unique(
    tmp_path: Path, duplicate: str
) -> None:
    log = tmp_path / "events.jsonl"
    source = append_source(log)
    exact = reference(source)
    first = decision(evidence_refs=[exact])
    events.append(log, first)
    second = decision(
        decision_id="decision-2",
        operation_id="operation-2",
        evidence_refs=[exact],
    )
    second["data"][duplicate] = first["data"][duplicate]

    with pytest.raises(events.EventError, match=duplicate):
        events.append(log, second)


def test_superseding_decision_preserves_the_exact_prior_record(tmp_path: Path) -> None:
    log = tmp_path / "events.jsonl"
    source = append_source(log)
    exact = reference(source)
    first = decision(evidence_refs=[exact])
    events.append(log, first)
    successor = decision(
        decision_id="decision-2",
        operation_id="operation-2",
        evidence_refs=[exact],
        supersedes=reference(first),
    )

    events.append(log, successor)

    recorded, rejected = events.read(log)
    assert rejected == []
    assert [item.data["decision_id"] for item in recorded[1:]] == [
        "decision-1",
        "decision-2",
    ]
    assert recorded[-1].data["supersedes"] == reference(first)
    assert recorded[1].data["alternatives"] == first["data"]["alternatives"]


def authority(
    proposal_id: str = "proposal-1", decision_id: str = "decision-1"
) -> dict[str, object]:
    return event(
        "authority.granted",
        {
            "human_decision": "approval",
            "principal": "Joe",
            "via": "cli",
            "proposal_id": proposal_id,
            "decision_id": decision_id,
        },
        actor="Joe",
    )


def test_protected_proposal_is_not_an_autonomous_or_self_authored_decision(
    tmp_path: Path,
) -> None:
    with pytest.raises(events.EventError, match="protected"):
        events.validate(
            event(events.DECISION_KIND, planning("protected_covered"))
        )

    log = tmp_path / "events.jsonl"
    source = append_source(log)
    exact = reference(source)
    authority_event = events.append(log, authority())
    covered = proposal(
        "protected_covered",
        evidence_refs=[exact],
        binding={
            **binding("protected_covered"),
            "authority_ref": reference(authority_event),
        },
    )
    events.append(log, covered)

    self_authorised = proposal(
        "protected_covered",
        proposal_id="proposal-self",
        decision_id="decision-self",
        operation_id="operation-self",
        evidence_refs=[exact],
    )
    self_authorised["event_id"] = events.new_event_id()
    self_authorised["data"]["planning"]["binding"]["authority_ref"] = reference(
        self_authorised
    )
    with pytest.raises(events.EventError, match="authority.*earlier"):
        events.append(log, self_authorised)


def test_protected_authority_must_match_the_proposal_and_reserved_decision(
    tmp_path: Path,
) -> None:
    log = tmp_path / "events.jsonl"
    source = append_source(log)
    wrong = events.append(log, authority(proposal_id="another-proposal"))
    candidate = proposal(
        "protected_covered",
        evidence_refs=[reference(source)],
        binding={
            **binding("protected_covered"),
            "authority_ref": reference(wrong),
        },
    )

    with pytest.raises(events.EventError, match="proposal_id"):
        events.append(log, candidate)

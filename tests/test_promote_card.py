"""S03 — deterministic owner card and privileged omissions (ADR-0076)."""

from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient.dashboard import (
    CardRefusal,
    ProposalCardFacts,
    build_payload,
    project_proposal_card,
    render_html,
    render_proposal_card,
)
from consilient.events import Event, SCHEMA_VERSION
from consilient.instructions import assemble
from consilient.promote import (
    EVALUATED,
    IMPACT_CONTRACT_KIND,
    PROMOTER_BETA_RECEIPT_KIND,
    REQUIRED_ADVERSE_ROWS,
    contract_digest,
    digest,
    exp104_impact_contract,
    privileged_fields,
)
from consilient.recall import pack_events, parse_receipt


CANDIDATE = digest("s03-candidate")
RESTORED = digest("s03-restored")
REVERSAL_REF = "promote.evaluated:scratch-reversal"
_CONTRACT = exp104_impact_contract()
PARENT = _CONTRACT.baseline_digests["parent"]
EPOCH = _CONTRACT.baseline_digests["epoch_anchor"]
INSTRUMENT = _CONTRACT.baseline_digests["instrument"]

QUALIFICATION_CANARY = "qualification-canary-value-s03"
SENTINEL_CANARY = "sentinel-canary-value-s03"
CARD_CANARY = "card-private-canary-value-s03"


def _facts(**over: object) -> ProposalCardFacts:
    contract = _CONTRACT
    payload = {
        "experiment_id": contract.experiment_id,
        "confirm_rule": contract.confirm_rule,
        "candidate_digest": CANDIDATE,
        "target_surface": contract.target_surface,
        "predecessor_digest": PARENT,
        "epoch_anchor_digest": EPOCH,
        "held_out_effect": "accept",
        "held_out_interval": "unavailable",
        "promoter_beta_point": "0.100000",
        "promoter_beta_interval": "[0.034732, 0.256210]",
        "promoter_beta_n": "30",
        "downstream_beta_point": "unavailable",
        "downstream_beta_interval": "unavailable",
        "downstream_beta_n": "unavailable",
        "downstream_alpha_point": "unavailable",
        "downstream_alpha_interval": "unavailable",
        "downstream_alpha_n": "unavailable",
        "cost": "unavailable",
        "adverse": {
            "refusals": 0,
            "timeouts": 0,
            "quarantine": 0,
            "missing_telemetry": None,
            "boundary_attempts": 2,
        },
        "consumer": "frozen task mixture",
        "before_behaviour": "skill inactive",
        "after_behaviour": "skill installed",
        "largest_effect": contract.largest_effect,
        "parent_digest": PARENT,
        "instrument_digest": INSTRUMENT,
        "rollback_trigger": contract.kill_rule,
        "scratch_reversal_ref": REVERSAL_REF,
        "restored_digest": RESTORED,
    }
    payload.update(over)
    return ProposalCardFacts(**payload)


def _event(kind: str, data: dict[str, object], *, event_id: str | None = None) -> Event:
    raw: dict[str, object] = {
        "v": SCHEMA_VERSION,
        "ts": "2026-08-24T12:00:00+00:00",
        "event": kind,
        "actor": "consilient.promote",
        "data": data,
    }
    if event_id is not None:
        raw["event_id"] = event_id
    return Event(raw)


def _bound_events() -> list[Event]:
    contract = exp104_impact_contract()
    return [
        _event(
            IMPACT_CONTRACT_KIND,
            {
                "experiment_id": contract.experiment_id,
                "registration_digest": contract_digest(contract),
                "contract": contract.as_dict(),
            },
            event_id="550e8400-e29b-41d4-a716-446655440010",
        ),
        _event(
            PROMOTER_BETA_RECEIPT_KIND,
            {
                "receipt_kind": "promoter_beta",
                "experiment_id": contract.experiment_id,
                "qualification_rule_digest": contract.baseline_digests["qualification_rule"],
                "decision_surface_digest": contract.baseline_digests["decision_surface"],
                "instrument_digest": contract.baseline_digests["instrument"],
                "generator_policy_digest": contract.baseline_digests["generator_policy"],
                "sampling_frame_digest": contract.baseline_digests["sampling_frame"],
                "interval_rule_digest": contract.baseline_digests["interval_rule"],
                "n_human_rejected": 30,
                "n_false_accept": 3,
                "beta_point": 0.1,
                "wilson_interval": [0.034732, 0.256210],
                "wilson_upper": 0.256210,
            },
            event_id="550e8400-e29b-41d4-a716-446655440011",
        ),
        _event(
            EVALUATED,
            {
                "qualification_accept": True,
                "manifest_digest": INSTRUMENT,
                "lineage_id": "s03-lineage",
                "candidate_digest": CANDIDATE,
                "reversal_match": True,
                "adverse": {
                    "refusals": 0,
                    "timeouts": 0,
                    "quarantine": 0,
                    "boundary_attempts": 2,
                },
                "consumer": "frozen task mixture",
                "before_behaviour": "skill inactive",
                "after_behaviour": "skill installed",
                "cost": "unavailable",
                "scratch_reversal_ref": REVERSAL_REF,
                "restored_digest": RESTORED,
            },
            event_id="550e8400-e29b-41d4-a716-446655440012",
        ),
    ]


def _payload(events: list[Event]) -> dict[str, object]:
    return build_payload(
        events,
        [],
        doctor={
            "routing_orchestration_enabled": False,
            "gates": {},
            "generated_at": "now",
        },
        beta_result={
            "verdict": "unmeasured",
            "n_rejected": 0,
            "n_false_accept": 0,
            "caveat": "no data",
            "lower_bound_on_joint_error": False,
        },
        beta_line="beta: no data",
        bypassed=0,
    )


def _expected_card(facts: ProposalCardFacts) -> str:
    surface = ", ".join(facts.target_surface)
    adverse = " ".join(
        f"{row}={'unavailable' if facts.adverse.get(row) is None else facts.adverse[row]}"
        for row in REQUIRED_ADVERSE_ROWS
    )
    return "\n".join(
        (
            (
                f"{facts.experiment_id} met {facts.confirm_rule}; "
                f"candidate {facts.candidate_digest} proposes {surface}."
            ),
            (
                f"Against {facts.predecessor_digest} and {facts.epoch_anchor_digest}, "
                f"sealed held-out outcome was {facts.held_out_effect} and "
                f"{facts.held_out_interval}; promoter beta and downstream beta/alpha were "
                f"{facts.promoter_beta_point}, {facts.promoter_beta_interval}, "
                f"{facts.promoter_beta_n} / {facts.downstream_beta_point}, "
                f"{facts.downstream_beta_interval}, {facts.downstream_beta_n} / "
                f"{facts.downstream_alpha_point}, {facts.downstream_alpha_interval}, "
                f"{facts.downstream_alpha_n}; cost and every adverse count were "
                f"{facts.cost}; {adverse}."
            ),
            (
                f"Executed probes changed {facts.consumer} from {facts.before_behaviour} "
                f"to {facts.after_behaviour}; the largest plausible effect is "
                f"{facts.largest_effect}, while parent/instrument {facts.parent_digest}/"
                f"{facts.instrument_digest} and every protected effect are unchanged."
            ),
            (
                f"No reply leaves the baseline active; trigger {facts.rollback_trigger} "
                f"restores {facts.parent_digest}, and scratch reversal "
                f"{facts.scratch_reversal_ref} restored the governed-state digest "
                f"{facts.restored_digest} exactly."
            ),
        )
    )


def test_four_sentence_card_is_exact_and_has_no_free_form_summary() -> None:
    facts = _facts()
    card = render_proposal_card(facts)
    expected = _expected_card(facts)
    assert card == expected
    assert card.count("\n") == 3
    assert len(card.split("\n")) == 4
    assert "I think" not in card
    assert "summary" not in card.casefold()


def test_absent_adverse_telemetry_prints_unavailable_never_zero() -> None:
    facts = _facts(
        adverse={
            "refusals": 0,
            "timeouts": 0,
            "quarantine": 0,
            "boundary_attempts": 0,
        }
    )
    card = render_proposal_card(facts)
    assert "missing_telemetry=unavailable" in card
    assert "missing_telemetry=0" not in card
    assert "refusals=0" in card


def test_missing_observable_change_refuses_the_card() -> None:
    with pytest.raises(CardRefusal, match="no_bounded_observable_change"):
        render_proposal_card(
            _facts(before_behaviour="skill inactive", after_behaviour="skill inactive")
        )
    with pytest.raises(CardRefusal, match="no_bounded_observable_change"):
        render_proposal_card(_facts(before_behaviour="", after_behaviour="skill installed"))


def test_projection_rebuild_is_byte_identical() -> None:
    events = _bound_events()
    first = project_proposal_card(events)
    second = project_proposal_card(list(events))
    assert first == second
    assert first == render_proposal_card(_facts())


def test_dashboard_renders_the_projected_card() -> None:
    events = _bound_events()
    payload = _payload(events)
    card = project_proposal_card(events)
    assert payload["promotion_card"]["text"] == card
    assert payload["promotion_card"]["sentence_count"] == 4
    page = render_html(payload)
    for sentence in card.split("\n"):
        assert html.escape(sentence, quote=True) in page


def test_dashboard_records_refusal_when_facts_are_absent() -> None:
    payload = _payload([])
    assert payload["promotion_card"]["refused"] is True
    assert payload["promotion_card"]["reason"] == "missing_bound_fact"
    assert "text" not in payload["promotion_card"]


def test_privileged_field_canaries_are_omitted_from_recall() -> None:
    events = [
        _event(
            "note.made",
            {"text": "public candidate context"},
            event_id="550e8400-e29b-41d4-a716-446655440001",
        ),
        _event(
            EVALUATED,
            {
                "qualification_score": QUALIFICATION_CANARY,
                "hidden_items": [{"prompt": QUALIFICATION_CANARY, "expected": "x"}],
                "qualification_accept": True,
            },
            event_id="550e8400-e29b-41d4-a716-446655440002",
        ),
        _event(
            "note.made",
            {"sentinel_batch_id": SENTINEL_CANARY, "sentinel_score": 0.99},
            event_id="550e8400-e29b-41d4-a716-446655440003",
        ),
        _event(
            "note.made",
            {"owner_card": CARD_CANARY, "proposal_card": CARD_CANARY},
            event_id="550e8400-e29b-41d4-a716-446655440004",
        ),
    ]
    text = pack_events(events, query="candidate context", limit_chars=8000)
    receipt = parse_receipt(text)
    omitted = {entry["id"]: entry["reason"] for entry in receipt["omitted"]}
    assert omitted["550e8400-e29b-41d4-a716-446655440002"] == "qualification"
    assert omitted["550e8400-e29b-41d4-a716-446655440003"] == "sentinel"
    assert omitted["550e8400-e29b-41d4-a716-446655440004"] == "card_private"
    assert "550e8400-e29b-41d4-a716-446655440001" in receipt["selected_ids"]
    assert QUALIFICATION_CANARY not in text
    assert SENTINEL_CANARY not in text
    assert CARD_CANARY not in text
    for field in privileged_fields():
        assert f'"{field}"' not in text
    assert "qualification_score" not in text
    assert "sentinel_batch_id" not in text
    assert "owner_card" not in text
    assert "proposal_card" not in text


def test_every_privileged_evaluation_field_is_a_canary() -> None:
    events = [
        _event(
            EVALUATED,
            {field: f"canary-{field}" for field in sorted(privileged_fields())},
            event_id="550e8400-e29b-41d4-a716-446655440005",
        )
    ]
    text = pack_events(events, query="canary", limit_chars=8000)
    receipt = parse_receipt(text)
    assert receipt["selected_ids"] == []
    assert receipt["omitted"] == [
        {"id": "550e8400-e29b-41d4-a716-446655440005", "reason": "qualification"}
    ]
    for field in privileged_fields():
        assert field not in text
        assert f"canary-{field}" not in text


def test_instruction_assembly_omits_privileged_fields_with_named_reasons(
    tmp_path: Path,
) -> None:
    skills = tmp_path / "skills"
    skill = skills / "alpha-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: alpha-skill\ndescription: Use when measuring beta.\n---\nbody\n",
        encoding="utf-8",
    )
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    from consilient.events import append

    now = datetime.now(timezone.utc)
    public = {
        "v": SCHEMA_VERSION,
        "ts": now.isoformat(),
        "event": "note.made",
        "actor": "test",
        "event_id": "550e8400-e29b-41d4-a716-446655440006",
        "data": {"text": "public instruction context"},
    }
    privileged = {
        "v": SCHEMA_VERSION,
        "ts": (now + timedelta(seconds=1)).isoformat(),
        "event": EVALUATED,
        "actor": "consilient.promote",
        "event_id": "550e8400-e29b-41d4-a716-446655440007",
        "data": {
            "qualification_score": QUALIFICATION_CANARY,
            "sentinel_items": [SENTINEL_CANARY],
            "owner_card": CARD_CANARY,
        },
    }
    append(log_dir / "2026-08-24.jsonl", public)
    append(log_dir / "2026-08-24.jsonl", privileged)

    assembly = assemble(skills, log_dir, task="public instruction context")
    omitted = {
        omission.event_id: omission.reason
        for omission in assembly.recall_selection.omissions
    }
    assert omitted["550e8400-e29b-41d4-a716-446655440007"] in {
        "qualification",
        "sentinel",
        "card_private",
    }
    assert QUALIFICATION_CANARY not in assembly.text
    assert SENTINEL_CANARY not in assembly.text
    assert CARD_CANARY not in assembly.text
    assert "qualification_score" not in assembly.text
    assert "owner_card" not in assembly.text
    recorded = assembly.recall_selection
    assert any(
        omission.reason in {"qualification", "sentinel", "card_private"}
        for omission in recorded.omissions
    )

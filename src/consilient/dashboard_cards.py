"""The owner card (S03, ADR-0076) — a deterministic sentence-count projection that
refuses rather than guesses.

This is the one part of the surface that can decline to render. `CardRefusal` is not an
error path bolted on; it is the contract. When the bound facts do not support a card the
payload carries `{"refused": True, "reason": ...}` and the page prints the reason,
because a card assembled from missing facts would be exactly the invented artefact the
surface exists to refuse.

`UNAVAILABLE` lives here because every user of it is here. It is the word printed where
a number would have gone, and keeping it beside the four formatters that emit it is what
stops one of them quietly printing a zero instead.

The projection and the rendering stay together deliberately. `project_proposal_card`
decides what the card may say and `render_proposal_card` decides how it reads; splitting
them would let the two drift, and the adverse-row contract that `promote` supplies is
checked across both."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from .events import Event
from . import promote
from .dashboard_types import (
    Payload,
)

from .dashboard_css import (
    CSS,
)


__all__ = [
    "CSS",
    "CardRefusal",
    "Payload",
    "ProposalCardFacts",
    "UNAVAILABLE",
    "project_proposal_card",
    "render_proposal_card",
]

UNAVAILABLE = "unavailable"


class CardRefusal(Exception):
    """The owner card cannot be rendered from the bound facts."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class ProposalCardFacts:
    """Bound evaluation and contract facts; never a free-form model summary."""

    experiment_id: str
    confirm_rule: str
    candidate_digest: str
    target_surface: tuple[str, ...]
    predecessor_digest: str
    epoch_anchor_digest: str
    held_out_effect: str
    held_out_interval: str
    promoter_beta_point: str
    promoter_beta_interval: str
    promoter_beta_n: str
    downstream_beta_point: str
    downstream_beta_interval: str
    downstream_beta_n: str
    downstream_alpha_point: str
    downstream_alpha_interval: str
    downstream_alpha_n: str
    cost: str
    adverse: Mapping[str, object]
    consumer: str
    before_behaviour: str
    after_behaviour: str
    largest_effect: str
    parent_digest: str
    instrument_digest: str
    rollback_trigger: str
    scratch_reversal_ref: str
    restored_digest: str


def _format_adverse(adverse: Mapping[str, object]) -> str:
    parts: list[str] = []
    for row in promote.REQUIRED_ADVERSE_ROWS:
        if row not in adverse or adverse[row] is None:
            parts.append(f"{row}={UNAVAILABLE}")
        else:
            parts.append(f"{row}={adverse[row]}")
    return " ".join(parts)


def render_proposal_card(facts: ProposalCardFacts) -> str:
    """Exactly four deterministic sentences. Templates render facts only."""
    if not facts.consumer.strip() or not facts.before_behaviour.strip():
        raise CardRefusal("no_bounded_observable_change")
    if not facts.after_behaviour.strip():
        raise CardRefusal("no_bounded_observable_change")
    if facts.before_behaviour == facts.after_behaviour:
        raise CardRefusal("no_bounded_observable_change")
    if not facts.experiment_id.strip() or not facts.candidate_digest.strip():
        raise CardRefusal("missing_bound_fact")
    if not facts.confirm_rule.strip() or not facts.target_surface:
        raise CardRefusal("missing_bound_fact")
    surface = ", ".join(facts.target_surface)
    adverse = _format_adverse(facts.adverse)
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


def _format_number(value: object) -> str:
    if value is None:
        return UNAVAILABLE
    if isinstance(value, bool):
        return UNAVAILABLE
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, int):
        return str(value)
    text = str(value).strip()
    return text if text else UNAVAILABLE


def _format_interval(value: object) -> str:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return f"[{_format_number(value[0])}, {_format_number(value[1])}]"
    if value is None:
        return UNAVAILABLE
    text = str(value).strip()
    return text if text else UNAVAILABLE


def _optional_text(value: object) -> str:
    if value is None:
        return UNAVAILABLE
    text = str(value).strip()
    return text if text else UNAVAILABLE


def project_proposal_card(events: Sequence[Event]) -> str:
    """Rebuild the owner card from bound evaluation and contract events."""
    contract_data: Mapping[str, object] | None = None
    receipt_data: Mapping[str, object] | None = None
    evaluation_data: Mapping[str, object] | None = None
    for event in events:
        if event.kind == promote.IMPACT_CONTRACT_KIND:
            payload = event.data.get("contract")
            if isinstance(payload, dict):
                contract_data = payload
        elif event.kind == promote.PROMOTER_BETA_RECEIPT_KIND:
            receipt_data = event.data
        elif event.kind == promote.EVALUATED:
            evaluation_data = event.data
    if contract_data is None or evaluation_data is None:
        raise CardRefusal("missing_bound_fact")
    baselines = contract_data.get("baseline_digests", {})
    if not isinstance(baselines, dict):
        raise CardRefusal("missing_bound_fact")
    surfaces = contract_data.get("target_surface", [])
    if not isinstance(surfaces, list) or not surfaces:
        raise CardRefusal("missing_bound_fact")
    experiment_id = contract_data.get("experiment_id")
    confirm_rule = contract_data.get("confirm_rule")
    candidate_digest = evaluation_data.get("candidate_digest")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise CardRefusal("missing_bound_fact")
    if not isinstance(confirm_rule, str) or not confirm_rule.strip():
        raise CardRefusal("missing_bound_fact")
    if not isinstance(candidate_digest, str) or not candidate_digest.strip():
        raise CardRefusal("missing_bound_fact")
    adverse_raw = evaluation_data.get("adverse", {})
    adverse: dict[str, object] = {}
    if isinstance(adverse_raw, dict):
        for row in promote.REQUIRED_ADVERSE_ROWS:
            adverse[row] = adverse_raw[row] if row in adverse_raw else None
    else:
        for row in promote.REQUIRED_ADVERSE_ROWS:
            adverse[row] = None
    accept = evaluation_data.get("qualification_accept")
    if accept is True:
        held_out = "accept"
    elif accept is False:
        held_out = "refuse"
    else:
        held_out = UNAVAILABLE
    parent = _optional_text(baselines.get("parent"))
    epoch = _optional_text(baselines.get("epoch_anchor"))
    instrument = evaluation_data.get("manifest_digest")
    if not isinstance(instrument, str) or not instrument.strip():
        instrument = _optional_text(baselines.get("instrument"))
    promoter_point = UNAVAILABLE
    promoter_interval = UNAVAILABLE
    promoter_n = UNAVAILABLE
    if receipt_data is not None:
        promoter_point = _format_number(receipt_data.get("beta_point"))
        promoter_interval = _format_interval(receipt_data.get("wilson_interval"))
        promoter_n = _format_number(receipt_data.get("n_human_rejected"))
    held_out_interval = evaluation_data.get("held_out_interval")
    cost = evaluation_data.get("cost")
    facts = ProposalCardFacts(
        experiment_id=experiment_id,
        confirm_rule=confirm_rule,
        candidate_digest=candidate_digest,
        target_surface=tuple(str(item) for item in surfaces),
        predecessor_digest=parent,
        epoch_anchor_digest=epoch,
        held_out_effect=held_out,
        held_out_interval=_optional_text(held_out_interval),
        promoter_beta_point=promoter_point,
        promoter_beta_interval=promoter_interval,
        promoter_beta_n=promoter_n,
        downstream_beta_point=_optional_text(
            evaluation_data.get("downstream_beta_point")
        ),
        downstream_beta_interval=_format_interval(
            evaluation_data.get("downstream_beta_interval")
        )
        if evaluation_data.get("downstream_beta_interval") is not None
        else UNAVAILABLE,
        downstream_beta_n=_optional_text(evaluation_data.get("downstream_beta_n")),
        downstream_alpha_point=_optional_text(
            evaluation_data.get("downstream_alpha_point")
        ),
        downstream_alpha_interval=_format_interval(
            evaluation_data.get("downstream_alpha_interval")
        )
        if evaluation_data.get("downstream_alpha_interval") is not None
        else UNAVAILABLE,
        downstream_alpha_n=_optional_text(evaluation_data.get("downstream_alpha_n")),
        cost=_optional_text(cost),
        adverse=adverse,
        consumer=str(evaluation_data.get("consumer") or ""),
        before_behaviour=str(evaluation_data.get("before_behaviour") or ""),
        after_behaviour=str(evaluation_data.get("after_behaviour") or ""),
        largest_effect=_optional_text(contract_data.get("largest_effect")),
        parent_digest=parent,
        instrument_digest=instrument if isinstance(instrument, str) else UNAVAILABLE,
        rollback_trigger=_optional_text(contract_data.get("kill_rule")),
        scratch_reversal_ref=_optional_text(
            evaluation_data.get("scratch_reversal_ref")
        ),
        restored_digest=_optional_text(evaluation_data.get("restored_digest")),
    )
    return render_proposal_card(facts)


def _promotion_card_payload(events: Sequence[Event]) -> Payload:
    try:
        text = project_proposal_card(events)
    except CardRefusal as exc:
        return {"refused": True, "reason": exc.reason}
    return {"text": text, "sentence_count": 4}

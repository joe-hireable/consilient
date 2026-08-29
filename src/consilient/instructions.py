"""Dynamic system instructions: layered, recorded, and adapted only on measured β.

Joe Brown, 21 August 2026: the harness needs decision-making, communication and
collaboration protocols baked into its system instructions, but "dynamic and not static
... continuously autonomously improve with seamless recursive self learning (PROVEN)".
PROVEN is the load-bearing word. A layer that rewrites itself and cannot show the
rewrite helped is drifting, and drift is indistinguishable from improvement without a
measurement.

The design rule: instructions adapt on OUTCOMES, never on REFLECTION. A layer may change
because a verdict was recorded, a test failed, a gate refused, a dispatch returned
nothing, or the principal corrected something — observations, all of them. It may never
change because a model reviewed the trajectory and formed an opinion about what would
work better; that is echo, and this project is named against it (CONSILIENCE.md, clause
2). Live-SWE-agent is the standing counter-example that an execution boundary is
necessary but not sufficient: it built task-local executable tools and cut GPT-5-Nano
success from 44% to 14% [cited: dispatch brief, 21 Aug 2026]. So adaptation here is
gated on measured β, not on the mere existence of an execution boundary.

Four layers, in fixed precedence order:

1. INVARIANT_CORE — evidence tags, verify-by-artefact, invariant-ships-with-its-check,
   refuse-rather-than-guess, the hard boundaries. Never adapted, never learned, never
   overridden. It lives in this file, which promote.PROTECTED_PREFIXES puts beyond the
   promoter's reach, and `render` builds the core section from the module constant and
   from nothing else — no assembly input can reach it.
2. Skills — selected by the task from `.agents/skills/`, never loaded wholesale.
   Selection is deterministic token overlap: no model call, no self-reported
   confidence. The matched tokens are recorded with the assembly, so the choice is
   auditable rather than trusted.
3. Recall pack — recall.pack_events over the trajectory, verbatim and bounded (EXP-45
   measured condensation dropping ~59%). The assembly event pins how many events were
   read and their digest, so the pack is exactly reproducible from the append-only
   prefix.
4. Adapted layer — what has been learned about THIS user, and the only layer that
   changes. It changes one way only: a proposal through promote.decide, accepted only
   on a measured promoter β (ADR-0018), with content admitted by record_adapted() only
   when its digest matches an unreversed acceptance. A hand edit has no acceptance to
   match, so unpromoted content is inert by construction — there is no second path to
   the layer, which is the jobboard-v2 lesson applied to self-modification.

ADR-0057: the adapted layer is derived from the user's trajectory and inherits its
privacy. It is therefore persisted as trajectory events under the gitignored log
directory — never as a file a repository could publish — and it is never shared without
explicit consent.

Invariants, each with a test in the same commit (tests/test_instructions.py):

  V0-46  The adapted layer cannot reach the invariant core.
  V0-47  Assemblies are recorded through append() with the identity of every layer,
         and record_assembly is the package's only writer of instructions.assembled.
  V0-48  Adapted content enters the layer only against an unreversed promote.accepted
         whose postimage digest it matches.
  V0-49  An unmeasured promoter β refuses adaptation, legibly.

The layers beneath this file, bottom-up. instructions_vocabulary.py holds the invariant
core text, the headers, the budgets and scan bounds, and the frozen record shapes.
instructions_admission.py holds record_adapted and the sibling refusals that decide what
may enter a layer. instructions_composition.py sources the skills, the recall pack and
the adapted layer and renders the document. instructions_audit.py records an assembly,
reconstructs one, and derives the decision-protocol threshold. This file keeps the entry
points — assemble, load_adapted, propose_adaptation and bind_protocol."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from pathlib import Path
from . import beta as beta_mod
from . import promote
from .events import (
    Event,
    EventError,
    read_all,
    resolve_reference,
)
from .instructions_vocabulary import (
    ADAPTED_LAYER_PATH,
    ADAPTED_LIMIT_CHARS,
    AdaptedLayer,
    BETTER_THAN_BEST_NAME,
    CORE_VERSION,
    INVARIANT_CORE,
    InstructionError,
    PROTOCOL_COMPLETED,
    PROTOCOL_NOT_WARRANTED,
    ProposalOutcome,
    RECALL_LIMIT_CHARS,
    SKILL_CHARS,
    SKILL_LIMIT,
    SkillRef,
    _capability_manifest_bindings,
    _explain,
    _source_digest,
    bind_recall_receipt,
)

from .instructions_admission import (
    Assembly,
    CostCeiling,
    EnvelopeReconstruction,
    IndexLookup,
    KINDS,
    ProtocolThreshold,
    Reconstruction,
    _event_reference,
    _omitted_digest,
    _same_task_assembly,
    _skill_file,
    record_adapted,
)

from .instructions_audit import (
    ProtocolBinding,
    _selection_receipt,
    protocol_threshold,
    reconstruct,
    record_assembly,
)

from .instructions_composition import (
    _adapted_from_events,
    _load_named_skill,
    _recorded_selection_receipt,
    _select_recall,
    reconstruct_envelope,
    render,
    select_skills,
)

from .instructions_vocabulary import (
    ACTIVE,
    ACTOR,
    ADAPTED,
    ADAPTED_HEADER,
    ASSEMBLED,
    BETTER_THAN_BEST_FILE,
    CORE_HEADER,
    COST_UNIT,
    EnvelopePart,
    INERT,
    INERT_NOTICE,
    IndexAnswer,
    LayerReport,
    PROTECTED_SCAN_EVENTS,
    RECALL_HEADER,
    RECALL_SCAN_EVENTS,
    RELIANCE_CONSUMERS,
    SKILLS_HEADER,
    TRI_STATES,
    _TOKEN,
    _omission_rows,
)

__all__ = [
    "ACTIVE",
    "ACTOR",
    "ADAPTED",
    "ADAPTED_HEADER",
    "ADAPTED_LAYER_PATH",
    "ADAPTED_LIMIT_CHARS",
    "ASSEMBLED",
    "AdaptedLayer",
    "Assembly",
    "BETTER_THAN_BEST_FILE",
    "BETTER_THAN_BEST_NAME",
    "CORE_HEADER",
    "CORE_VERSION",
    "COST_UNIT",
    "CostCeiling",
    "EnvelopePart",
    "EnvelopeReconstruction",
    "INERT",
    "INERT_NOTICE",
    "INVARIANT_CORE",
    "IndexAnswer",
    "IndexLookup",
    "InstructionError",
    "KINDS",
    "LayerReport",
    "PROTECTED_SCAN_EVENTS",
    "PROTOCOL_COMPLETED",
    "PROTOCOL_NOT_WARRANTED",
    "ProposalOutcome",
    "ProtocolBinding",
    "ProtocolThreshold",
    "RECALL_HEADER",
    "RECALL_LIMIT_CHARS",
    "RECALL_SCAN_EVENTS",
    "RELIANCE_CONSUMERS",
    "Reconstruction",
    "SKILLS_HEADER",
    "SKILL_CHARS",
    "SKILL_LIMIT",
    "SkillRef",
    "TRI_STATES",
    "_TOKEN",
    "_adapted_from_events",
    "_capability_manifest_bindings",
    "_event_reference",
    "_explain",
    "_load_named_skill",
    "_omission_rows",
    "_omitted_digest",
    "_recorded_selection_receipt",
    "_same_task_assembly",
    "_select_recall",
    "_selection_receipt",
    "_skill_file",
    "_source_digest",
    "assemble",
    "bind_protocol",
    "bind_recall_receipt",
    "load_adapted",
    "propose_adaptation",
    "protocol_threshold",
    "reconstruct",
    "reconstruct_envelope",
    "record_adapted",
    "record_assembly",
    "render",
    "select_skills",
]


def _bind_selected_skill(
    skills: tuple[SkillRef, ...], skills_dir: Path, threshold: ProtocolThreshold | None
) -> tuple[SkillRef, ...]:
    if threshold is None or not threshold.selects:
        return skills
    required = _load_named_skill(skills_dir, BETTER_THAN_BEST_NAME)
    if any(skill.name == required.name for skill in skills):
        return skills
    return (required, *skills)


def load_adapted(log_dir: Path) -> AdaptedLayer:
    events, _ = read_all(log_dir)
    return _adapted_from_events(events)


def assemble(
    skills_dir: Path,
    log_dir: Path,
    *,
    task: str,
    recall_limit_chars: int = RECALL_LIMIT_CHARS,
    skill_limit: int = SKILL_LIMIT,
    skill_chars: int = SKILL_CHARS,
    threshold: ProtocolThreshold | None = None,
    capability_selection: Mapping[str, object] | None = None,
) -> Assembly:
    """Assemble the four layers for one task.

    Pure read: nothing is recorded here. record_assembly is the write, and the
    caller pairs the two — the same discipline dispatch already owes the trajectory
    for its claims. What append() enforces is that a recorded assembly names every
    layer; what it cannot enforce is that a caller records at all."""
    if not task.strip():
        raise ValueError("an assembly serves a task; the task text may not be empty")
    events, _ = read_all(log_dir)
    selection = _select_recall(events, query=task, limit_chars=recall_limit_chars)
    pack = selection.text
    skills, omitted = select_skills(
        skills_dir, task, limit=skill_limit, budget_chars=skill_chars
    )
    skills = _bind_selected_skill(skills, skills_dir, threshold)
    adapted = _adapted_from_events(events)
    text = render(skills, pack, adapted, skills_omitted=omitted)
    return Assembly(
        core_version=CORE_VERSION,
        skills=skills,
        skills_omitted=omitted,
        recall_pack=pack,
        recall_selection=selection,
        recall_limit_chars=recall_limit_chars,
        recall_source_events=len(events),
        recall_source_digest=_source_digest(events),
        adapted=adapted,
        text=text,
        sha256=promote.digest(text),
        capability_manifests=_capability_manifest_bindings(capability_selection),
        recall_receipt=bind_recall_receipt(pack),
    )


def propose_adaptation(
    log_dir: Path,
    proposed_text: str,
    measured_beta: beta_mod.Beta,
    *,
    enabled: bool = promote.ENABLED_BY_DEFAULT,
    evidence: promote.ExecutionEvidence | None = None,
) -> ProposalOutcome:
    """Route a proposed adapted-layer change through the existing promoter (a8b8108).

    This function never applies anything. Today promoter β is unmeasured, so the
    refusal path is the one that runs; the explanation says why, and what a real
    promotion would require (V0-49).
    """
    if len(proposed_text) > ADAPTED_LIMIT_CHARS:
        raise InstructionError(
            f"the adapted layer is bounded at {ADAPTED_LIMIT_CHARS} characters; "
            f"the proposal carries {len(proposed_text)}"
        )
    current = load_adapted(log_dir)
    candidate = promote.Candidate(
        identity=f"adapted-layer-{promote.digest(proposed_text)[:16]}",
        path=ADAPTED_LAYER_PATH,
        preimage_sha256=promote.digest(current.text),
        postimage_sha256=promote.digest(proposed_text),
        evidence=evidence,
    )
    decision = promote.decide(candidate, measured_beta, enabled=enabled)
    event = promote.record(log_dir, decision)
    return ProposalOutcome(
        decision=decision, event=event, explanation=_explain(decision)
    )


def _require_reconstructed_skill(
    log_dir: Path, skills_dir: Path, assembly_event: Event
) -> None:
    assembly_id = assembly_event.data.get("assembly_id")
    if not isinstance(assembly_id, str):
        raise InstructionError("instructions.assembled is missing assembly_id")
    result = reconstruct(log_dir, skills_dir, assembly_id)
    if not result.ok:
        raise InstructionError(
            "the pinned skill body does not reconstruct from the same tree"
        )
    recorded_skills = assembly_event.data.get("skills")
    if not isinstance(recorded_skills, list):
        raise InstructionError("instructions.assembled carries no skills")
    required = _load_named_skill(skills_dir, BETTER_THAN_BEST_NAME)
    match: dict[str, object] | None = None
    for entry in recorded_skills:
        if isinstance(entry, dict) and entry.get("name") == BETTER_THAN_BEST_NAME:
            match = entry
            break
    if match is None:
        raise InstructionError(
            "the earlier same-task assembly does not contain the better-than-best skill"
        )
    if match.get("path") != required.path:
        raise InstructionError("the recorded skill path does not match the pinned tree")
    if match.get("sha256") != required.sha256:
        raise InstructionError(
            "the recorded skill digest does not match the pinned body"
        )
    replayed = _skill_file(skills_dir, BETTER_THAN_BEST_NAME).read_text(
        encoding="utf-8"
    )
    if replayed != required.body or promote.digest(replayed) != required.sha256:
        raise InstructionError(
            "the reconstructed skill body does not match the pinned body"
        )


def bind_protocol(
    log_dir: Path,
    skills_dir: Path,
    *,
    task: str,
    threshold: ProtocolThreshold,
    bar_ref: Mapping[str, str] | None = None,
    search_ref: Mapping[str, str] | None = None,
    killing_check_ref: Mapping[str, str] | None = None,
    events: Sequence[Event] | None = None,
) -> ProtocolBinding:
    """Bind completion artefacts only when the threshold fires.

    A firing threshold needs an earlier same-task assembly whose Better-Than-Best
    name, path, digest and body reconstruct from the pinned tree, plus bar, search
    and killing-check references. A non-firing threshold cannot carry those
    artefacts.
    """
    if not task.strip():
        raise ValueError("an assembly serves a task; the task text may not be empty")
    prefix = list(events) if events is not None else read_all(log_dir)[0]
    if not threshold.selects:
        if (
            bar_ref is not None
            or search_ref is not None
            or killing_check_ref is not None
        ):
            raise InstructionError(
                "a non-firing threshold cannot carry a completion artefact"
            )
        return ProtocolBinding(
            status=PROTOCOL_NOT_WARRANTED,
            threshold=threshold,
            instructions_ref=None,
            bar_ref=None,
            search_ref=None,
            killing_check_ref=None,
        )
    if bar_ref is None or search_ref is None or killing_check_ref is None:
        raise InstructionError(
            "a firing threshold requires bar, search and killing-check references"
        )
    for label, reference in (
        ("bar_ref", bar_ref),
        ("search_ref", search_ref),
        ("killing_check_ref", killing_check_ref),
    ):
        try:
            resolve_reference(reference, prefix)
        except EventError as exc:
            raise InstructionError(
                f"{label} does not resolve to an earlier event"
            ) from exc
    assembly_event = _same_task_assembly(prefix, task)
    if assembly_event is None:
        raise InstructionError(
            "a firing threshold requires an earlier same-task instructions.assembled event"
        )
    _require_reconstructed_skill(log_dir, skills_dir, assembly_event)
    return ProtocolBinding(
        status=PROTOCOL_COMPLETED,
        threshold=threshold,
        instructions_ref=_event_reference(assembly_event.raw),
        bar_ref=dict(bar_ref),
        search_ref=dict(search_ref),
        killing_check_ref=dict(killing_check_ref),
    )

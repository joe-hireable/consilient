"""Dynamic system instructions: layered, recorded, and adapted only on measured β.

Joe Brown, 21 August 2026: the harness needs decision-making, communication and
collaboration protocols baked into its system instructions, but "dynamic and not static
... continuously autonomously improve with seamless recursive self learning (PROVEN)".
PROVEN is the load-bearing word. A layer that rewrites itself and cannot show the
rewrite helped is drifting, and drift is indistinguishable from improvement without a
measurement.

The design rule: instructions adapt on OUTCOMES, never on REFLECTION. A layer may
change because a verdict was recorded, a test failed, a gate refused, a dispatch
returned nothing, or the principal corrected something — observations, all of them. It
may never change because a model reviewed the trajectory and formed an opinion about
what would work better; that is echo, and this project is named against it
(CONSILIENCE.md, clause 2). Live-SWE-agent is the standing counter-example that an
execution boundary is necessary but not sufficient: it built task-local executable
tools and cut GPT-5-Nano success from 44% to 14% [cited: dispatch brief, 21 Aug 2026].
So adaptation here is gated on measured β, not on the mere existence of an execution
boundary.

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
directory — never as a file a repository could publish — and it is never shared
without explicit consent.

Invariants, each with a test in the same commit (tests/test_instructions.py):

  V0-46  The adapted layer cannot reach the invariant core.
  V0-47  Assemblies are recorded through append() with the identity of every layer,
         and record_assembly is the package's only writer of instructions.assembled.
  V0-48  Adapted content enters the layer only against an unreversed promote.accepted
         whose postimage digest it matches.
  V0-49  An unmeasured promoter β refuses adaptation, legibly.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import beta as beta_mod
from . import promote, recall
from .events import SCHEMA_VERSION, Event, EventPayload, append, canonical, read_all

ACTOR = "consilient.instructions"
ASSEMBLED = "instructions.assembled"
ADAPTED = "instructions.adapted"
KINDS = frozenset({ASSEMBLED, ADAPTED})

CORE_VERSION = 1

# The one layer that may never change under adaptation. If this text is to change, a
# human changes it by commit — the promoter cannot reach this file (V0-45), and the
# assembly renders it from this constant and nothing else (V0-46).
INVARIANT_CORE: tuple[str, ...] = (
    "Tag every claim with its evidence: [measured], [simulated], [cited] or "
    "[asserted]. Never upgrade a tag without new evidence.",
    "Verify by artefact, never by exit code or process identity.",
    "An invariant ships with the check that enforces it, in the same commit.",
    "Refuse rather than guess. State assumptions explicitly and label confidence.",
    "Never gate on a model's self-reported confidence; use verifier outcomes and "
    "human verdicts.",
    "A multi-agent structure names the different class of facts it introduces, or "
    "it does not ship. Agreement over shared evidence is echo, not consilience.",
    "No secret anywhere a public repository can reach; a capability that needs one "
    "runs locally or not at all.",
    "Gate state is what `consil doctor` reports, never what a document asserts; do "
    "not cross a gate by inference.",
)

# The adapted layer's stable address. It is a logical path, used by the promoter's
# allowlist routing; persistence is trajectory events, not a file (ADR-0057).
ADAPTED_LAYER_PATH = ".harness/adapted/layer.md"

RECALL_LIMIT_CHARS = 8000
SKILL_LIMIT = 3
SKILL_CHARS = 12000
ADAPTED_LIMIT_CHARS = 4000

CORE_HEADER = "# Invariant core — never adapted, never learned, never overridden"
SKILLS_HEADER = "# Skills selected for this task"
RECALL_HEADER = "# Recall pack — verbatim, bounded"
ADAPTED_HEADER = "# Adapted layer — learned about this user; changes only on a measured promoter β"

INERT_NOTICE = (
    "No adaptation has ever been promoted, so this layer is empty. Adaptation is "
    "proposed, measured and promoted through the native promoter (ADR-0018); while "
    "promoter β is unmeasured every proposal is refused. See `consil beta`."
)

INERT = "inert"
ACTIVE = "active"

# Tokens too frequent to discriminate one skill from another. Selection is recorded
# with its matched tokens, so a bad match is auditable rather than hidden.
_STOPWORDS = frozenset(
    {
        "about", "after", "again", "against", "also", "always", "before", "being",
        "below", "between", "could", "does", "doing", "done", "each", "every",
        "from", "have", "here", "into", "just", "like", "made", "make", "more",
        "most", "must", "never", "only", "over", "same", "shall", "should", "some",
        "such", "than",         "that", "their", "them", "then", "there", "these", "they",
        "this", "those", "through", "under", "until", "upon", "used", "uses",
        "what", "when", "where", "which", "while", "will", "with", "would", "your",
        # Generic in THIS corpus: every skill description talks about the user and
        # the system, so neither token discriminates one skill from another.
        "system", "user",
    }
)

_TOKEN = re.compile(r"[a-z0-9]+")


class InstructionError(RuntimeError):
    """An instruction-layer rule was violated."""


@dataclass(frozen=True)
class SkillRef:
    """One selected skill: identity, content digest, and why it was chosen."""

    name: str
    path: str
    sha256: str
    matched: tuple[str, ...]
    body: str


@dataclass(frozen=True)
class AdaptedLayer:
    """The current adapted layer. Inert unless every check in _adapted_from_events
    passed: a recorded, unreversed acceptance whose postimage digest matches the
    recorded content."""

    status: str
    text: str
    candidate_id: str | None

    @property
    def sha256(self) -> str:
        return promote.digest(self.text)


_INERT_LAYER = AdaptedLayer(INERT, "", None)


@dataclass(frozen=True)
class Assembly:
    """One assembled instruction set. `text` is what the agent is shown; the rest is
    what makes it auditable after the fact."""

    core_version: int
    skills: tuple[SkillRef, ...]
    skills_omitted: int
    recall_pack: str
    recall_selection: recall.Selection
    recall_limit_chars: int
    recall_source_events: int
    recall_source_digest: str
    adapted: AdaptedLayer
    text: str
    sha256: str


@dataclass(frozen=True)
class ProposalOutcome:
    """What happened to a proposed adaptation, in one legible place."""

    decision: promote.Decision
    event: EventPayload
    explanation: str


@dataclass(frozen=True)
class LayerReport:
    layer: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class Reconstruction:
    """Re-derivation of a recorded assembly, layer by layer. Drift is reported per
    layer, never smoothed into a single yes."""

    assembly_id: str
    found: bool
    layers: tuple[LayerReport, ...]

    @property
    def ok(self) -> bool:
        return self.found and all(report.ok for report in self.layers)


def _tokens(text: str) -> frozenset[str]:
    return frozenset(
        token
        for token in _TOKEN.findall(text.lower())
        if len(token) >= 4 and token not in _STOPWORDS
    )


def _frontmatter(text: str) -> dict[str, str]:
    """name/description from a SKILL.md header. A heuristic parse: enough to select
    on, with the full file embedded verbatim so nothing depends on parsing the body."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fields: dict[str, str] = {}
    key: str | None = None
    for line in text[3:end].splitlines():
        if line.startswith((" ", "\t")) and key is not None:
            fields[key] = f"{fields[key]} {line.strip()}"
            continue
        name, sep, value = line.partition(":")
        if not sep:
            continue
        key = name.strip()
        fields[key] = value.strip()
    return fields


def select_skills(
    skills_dir: Path,
    task: str,
    *,
    limit: int = SKILL_LIMIT,
    budget_chars: int = SKILL_CHARS,
) -> tuple[tuple[SkillRef, ...], int]:
    """Deterministic task-relevant selection, never wholesale loading.

    A skill is a candidate when at least two distinctive task tokens appear in its
    declared name or description; candidates rank by matched count, ties by name.
    The returned count is how many candidates the character budget excluded.
    """
    if limit < 0 or budget_chars < 1:
        raise ValueError("limit must be >= 0 and budget_chars >= 1")
    task_tokens = _tokens(task)
    candidates: list[tuple[int, str, SkillRef]] = []
    for path in sorted(skills_dir.glob("*/SKILL.md")):
        body = path.read_text(encoding="utf-8")
        fields = _frontmatter(body)
        name = fields.get("name") or path.parent.name
        haystack = _tokens(f"{name} {fields.get('description', '')}")
        matched = tuple(sorted(task_tokens & haystack))
        if len(matched) < 2:
            continue
        relative = path.parent.name
        ref = SkillRef(
            name=name,
            path=f"{skills_dir.as_posix().rstrip('/')}/{relative}/SKILL.md",
            sha256=promote.digest(body),
            matched=matched,
            body=body,
        )
        candidates.append((-len(matched), name, ref))
    candidates.sort(key=lambda item: (item[0], item[1]))
    chosen: list[SkillRef] = []
    spent = 0
    omitted = 0
    for _, _, ref in candidates[:limit] if limit else []:
        if spent + len(ref.body) > budget_chars:
            omitted += 1
            continue
        chosen.append(ref)
        spent += len(ref.body)
    omitted += max(0, len(candidates) - (limit if limit else 0))
    return tuple(chosen), omitted


def _render_core(core_version: int) -> str:
    lines = "\n".join(f"- {line}" for line in INVARIANT_CORE)
    return f"{CORE_HEADER} (v{core_version})\n\n{lines}\n"


def render(
    skills: Sequence[SkillRef],
    recall_pack: str,
    adapted: AdaptedLayer,
    *,
    core_version: int = CORE_VERSION,
    skills_omitted: int = 0,
) -> str:
    """Compose the document. The core section is built from INVARIANT_CORE only —
    it is the first thing in the text and no parameter of this function can reach it
    (V0-46)."""
    parts = [_render_core(core_version)]
    note = f" ({skills_omitted} further matched skill(s) omitted by the budget)" if skills_omitted else ""
    parts.append(f"\n{SKILLS_HEADER}{note}\n")
    for skill in skills:
        parts.append(f"\n## {skill.name}\n\n{skill.body.rstrip()}\n")
    parts.append(f"\n{RECALL_HEADER}\n\n{recall_pack.rstrip()}\n")
    adapted_text = adapted.text if adapted.status == ACTIVE else INERT_NOTICE
    parts.append(f"\n{ADAPTED_HEADER}\n\n{adapted_text.rstrip()}\n")
    return "".join(parts)


def _source_digest(events: Sequence[Event]) -> str:
    return promote.digest("\n".join(canonical(event.raw) for event in events))


def _selection_receipt(selection: recall.Selection) -> dict[str, object]:
    return {
        "selected_event_ids": list(selection.selected_event_ids),
        "selected_digest": selection.selected_digest,
        "omitted": [
            {
                "event_id": omission.event_id,
                "event_kind": omission.event_kind,
                "reason": omission.reason,
                "protected": omission.protected,
            }
            for omission in selection.omissions
        ],
        "context_complete": selection.context_complete,
        "continuation": (
            {"event_id": selection.continuation_event_id}
            if selection.continuation_event_id is not None
            else None
        ),
    }


def _guard_privileged_selection(
    selection: recall.Selection, events: Sequence[Event]
) -> recall.Selection:
    """Refuse an assembly whose candidate context still carries privileged fields."""
    indexed = {recall._stable_id(event): event for event in events}
    for event_id in selection.selected_event_ids:
        event = indexed.get(event_id)
        if event is None:
            continue
        reason = recall.privileged_omission_reason(event)
        if reason is not None:
            raise InstructionError(
                f"privileged field omitted as {reason} reached instruction context"
            )
    return selection


def _select_recall(
    events: Sequence[Event], *, query: str, limit_chars: int
) -> recall.Selection:
    """Shrink the scan window until its honest receipt fits, then return its provenance."""
    window = len(events)
    protected = recall._protected_event_indexes(events)
    while True:
        candidate = (
            events
            if window >= len(events)
            else [
                event
                for index, event in enumerate(events)
                if index in protected or index >= len(events) - window
            ]
        )
        try:
            return _guard_privileged_selection(
                recall.select_events(
                    candidate,
                    query=query,
                    limit_chars=limit_chars,
                    scan_complete=window >= len(events),
                    shrink_to_receipt=True,
                ),
                candidate,
            )
        except ValueError:
            if window <= 1:
                return _guard_privileged_selection(
                    recall.select_events(
                        candidate,
                        query=query,
                        limit_chars=limit_chars,
                        scan_complete=window >= len(events),
                    ),
                    candidate,
                )
            window = max(1, window // 2)


def _adapted_from_events(events: Sequence[Event]) -> AdaptedLayer:
    """Project the adapted layer from the record. Content counts only when a
    recorded, unreversed acceptance vouches for its digest (V0-48). A reversal
    removes that candidate's layer wherever it sits in the applied stack, so the
    layer falls back to the previous promotion rather than to nothing."""
    accepted: dict[str, str] = {}
    reversed_ids: set[str] = set()
    applied: list[AdaptedLayer] = []
    for event in events:
        data = event.data
        if event.kind == promote.ACCEPTED:
            candidate_id = data.get("candidate_id")
            postimage = data.get("postimage_sha256")
            if (
                data.get("path") == ADAPTED_LAYER_PATH
                and isinstance(candidate_id, str)
                and isinstance(postimage, str)
            ):
                accepted[candidate_id] = postimage
        elif event.kind == promote.REVERSED:
            candidate_id = data.get("candidate_id")
            if isinstance(candidate_id, str):
                reversed_ids.add(candidate_id)
                applied = [
                    layer for layer in applied if layer.candidate_id != candidate_id
                ]
        elif event.kind == ADAPTED:
            candidate_id = data.get("candidate_id")
            text = data.get("text")
            text_digest = data.get("text_sha256")
            if not (
                isinstance(candidate_id, str)
                and isinstance(text, str)
                and isinstance(text_digest, str)
            ):
                continue
            if candidate_id not in accepted or candidate_id in reversed_ids:
                continue
            if accepted[candidate_id] != text_digest or promote.digest(text) != text_digest:
                continue
            applied = [
                layer for layer in applied if layer.candidate_id != candidate_id
            ]
            applied.append(AdaptedLayer(ACTIVE, text, candidate_id))
    return applied[-1] if applied else _INERT_LAYER


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
    )


def record_assembly(log_dir: Path, assembly: Assembly, *, task: str) -> EventPayload:
    """Append the assembly through the single writer, naming every layer (V0-47)."""
    now = datetime.now(timezone.utc)
    return append(
        log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": ASSEMBLED,
            "actor": ACTOR,
            "data": {
                "assembly_id": assembly.sha256,
                "core": {
                    "version": assembly.core_version,
                    "sha256": promote.digest(_render_core(assembly.core_version)),
                },
                "skills": [
                    {
                        "name": skill.name,
                        "path": skill.path,
                        "sha256": skill.sha256,
                        "matched": list(skill.matched),
                    }
                    for skill in assembly.skills
                ],
                "skills_omitted": assembly.skills_omitted,
                "recall": {
                    "query": task,
                    "limit_chars": assembly.recall_limit_chars,
                    "sha256": promote.digest(assembly.recall_pack),
                    "source_events": assembly.recall_source_events,
                    "source_digest": assembly.recall_source_digest,
                    **_selection_receipt(assembly.recall_selection),
                },
                "adapted": {
                    "status": assembly.adapted.status,
                    "sha256": assembly.adapted.sha256,
                    "candidate_id": assembly.adapted.candidate_id,
                },
            },
        },
    )


def _explain(decision: promote.Decision) -> str:
    measured = decision.measured_beta
    if decision.action == "promote":
        return (
            "PROMOTED: recorded as promote.accepted. The content enters the adapted "
            "layer only through record_adapted, which re-checks the digest against "
            "this acceptance (V0-48)."
        )
    if decision.reason == promote.DISABLED:
        return (
            "REFUSED (disabled): the promotion loop is disabled by default (V0-44). "
            "The adapted layer is unchanged. Enabling is a deliberate act, and even "
            "enabled, promotion requires a measured promoter β."
        )
    if decision.reason == promote.UNMEASURED_BETA:
        return (
            f"REFUSED (unmeasured_beta): promoter β is {measured.verdict} "
            f"({measured.n_rejected} human rejections, need {beta_mod.MIN_REJECTIONS}). "
            "A default would be a fabricated measurement (ADR-0018). The adapted layer "
            "is unchanged; the refusal is recorded as promote.refused."
        )
    return (
        f"REFUSED ({decision.reason}): the adapted layer is unchanged; the refusal "
        "is recorded as promote.refused."
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
    return ProposalOutcome(decision=decision, event=event, explanation=_explain(decision))


def record_adapted(log_dir: Path, *, candidate_id: str, text: str) -> EventPayload:
    """Admit promoted content to the layer. The chokepoint (V0-48): without a
    recorded, unreversed promote.accepted whose postimage digest matches `text`,
    there is nothing to record — a direct write to the layer does not exist."""
    if len(text) > ADAPTED_LIMIT_CHARS:
        raise InstructionError(
            f"the adapted layer is bounded at {ADAPTED_LIMIT_CHARS} characters"
        )
    events, _ = read_all(log_dir)
    accepted: dict[str, str] = {}
    reversed_ids: set[str] = set()
    for event in events:
        data = event.data
        if event.kind == promote.ACCEPTED and data.get("path") == ADAPTED_LAYER_PATH:
            cid = data.get("candidate_id")
            postimage = data.get("postimage_sha256")
            if isinstance(cid, str) and isinstance(postimage, str):
                accepted[cid] = postimage
        elif event.kind == promote.REVERSED:
            cid = data.get("candidate_id")
            if isinstance(cid, str):
                reversed_ids.add(cid)
    if candidate_id not in accepted:
        raise InstructionError(
            f"no recorded promotion for {candidate_id!r}; adapted content cannot "
            "enter the layer without one (V0-48)"
        )
    if candidate_id in reversed_ids:
        raise InstructionError(
            f"the promotion for {candidate_id!r} was reversed; its content is not "
            "the layer (V0-48)"
        )
    if accepted[candidate_id] != promote.digest(text):
        raise InstructionError(
            "the content does not match the accepted postimage digest; what enters "
            "the layer is what the promoter accepted, byte for byte (V0-48)"
        )
    now = datetime.now(timezone.utc)
    return append(
        log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": ADAPTED,
            "actor": ACTOR,
            "data": {
                "candidate_id": candidate_id,
                "path": ADAPTED_LAYER_PATH,
                "text": text,
                "text_sha256": promote.digest(text),
            },
        },
    )


def reconstruct(log_dir: Path, skills_dir: Path, assembly_id: str) -> Reconstruction:
    """Re-derive a recorded assembly, layer by layer, and say exactly what drifted.

    An instruction set that cannot be reconstructed after the fact is not auditable,
    and an unauditable instruction set cannot be proven to have helped. The core and
    skills are recovered from the tree and checked by digest; the recall pack is
    replayed over the pinned append-only prefix; the adapted layer is replayed from
    the events that preceded the assembly."""
    events, _ = read_all(log_dir)
    index: int | None = None
    for position, event in enumerate(events):
        if event.kind == ASSEMBLED and event.data.get("assembly_id") == assembly_id:
            index = position
    if index is None:
        return Reconstruction(
            assembly_id,
            False,
            (LayerReport("event", False, "no instructions.assembled event carries this id"),),
        )
    data = events[index].data
    reports: list[LayerReport] = []

    core = data.get("core")
    expected_version = core.get("version") if isinstance(core, dict) else None
    expected_core_sha = core.get("sha256") if isinstance(core, dict) else None
    if expected_version != CORE_VERSION:
        reports.append(
            LayerReport(
                "core",
                False,
                f"the event records core v{expected_version}; this build renders "
                f"v{CORE_VERSION}. The core changed by commit since; recover the "
                "assembled text from git at the assembly's commit.",
            )
        )
    elif promote.digest(_render_core(CORE_VERSION)) != expected_core_sha:
        reports.append(
            LayerReport("core", False, "the rendered core digest does not match the record")
        )
    else:
        reports.append(LayerReport("core", True, f"v{CORE_VERSION} digest matches"))

    recorded_skills = data.get("skills")
    skill_reports_ok = True
    skill_details: list[str] = []
    if isinstance(recorded_skills, list):
        for entry in recorded_skills:
            if not isinstance(entry, dict):
                skill_reports_ok = False
                continue
            name = entry.get("name")
            recorded_sha = entry.get("sha256")
            path = skills_dir / str(name) / "SKILL.md"
            if not path.exists():
                skill_reports_ok = False
                skill_details.append(f"{name}: file gone")
                continue
            actual_sha = promote.digest(path.read_text(encoding="utf-8"))
            if actual_sha != recorded_sha:
                skill_reports_ok = False
                skill_details.append(f"{name}: content drifted")
            else:
                skill_details.append(f"{name}: ok")
    reports.append(
        LayerReport(
            "skills",
            skill_reports_ok,
            "; ".join(skill_details) if skill_details else "no skills were selected",
        )
    )

    recall_data = data.get("recall")
    if not isinstance(recall_data, dict):
        reports.append(LayerReport("recall", False, "the record carries no recall layer"))
    else:
        source_events = recall_data.get("source_events")
        source_digest = recall_data.get("source_digest")
        query = recall_data.get("query")
        limit_chars = recall_data.get("limit_chars")
        recorded_pack_sha = recall_data.get("sha256")
        if not (
            isinstance(source_events, int)
            and isinstance(source_digest, str)
            and isinstance(query, str)
            and isinstance(limit_chars, int)
            and isinstance(recorded_pack_sha, str)
        ):
            reports.append(LayerReport("recall", False, "the recall record is malformed"))
        elif len(events) < source_events:
            reports.append(
                LayerReport(
                    "recall",
                    False,
                    f"the log holds {len(events)} events, fewer than the "
                    f"{source_events} the pack consumed; the append-only prefix is gone",
                )
            )
        elif _source_digest(events[:source_events]) != source_digest:
            reports.append(
                LayerReport(
                    "recall", False, "the pinned log prefix no longer digests to the record"
                )
            )
        else:
            selection = _select_recall(
                events[:source_events], query=query, limit_chars=limit_chars
            )
            pack = selection.text
            if promote.digest(pack) != recorded_pack_sha:
                reports.append(
                    LayerReport("recall", False, "the replayed pack does not match the record")
                )
            elif any(
                key in recall_data
                for key in (
                    "selected_event_ids",
                    "selected_digest",
                    "omitted",
                    "context_complete",
                    "continuation",
                )
            ) and _selection_receipt(selection) != {
                key: recall_data.get(key)
                for key in (
                    "selected_event_ids",
                    "selected_digest",
                    "omitted",
                    "context_complete",
                    "continuation",
                )
            }:
                reports.append(
                    LayerReport(
                        "recall",
                        False,
                        "the replayed selection receipt does not match the record",
                    )
                )
            else:
                reports.append(
                    LayerReport(
                        "recall",
                        True,
                        f"replayed over the pinned prefix of {source_events} event(s)",
                    )
                )

    recorded_adapted = data.get("adapted")
    if not isinstance(recorded_adapted, dict):
        reports.append(LayerReport("adapted", False, "the record carries no adapted layer"))
    else:
        replayed = _adapted_from_events(events[:index])
        if (
            replayed.status == recorded_adapted.get("status")
            and replayed.sha256 == recorded_adapted.get("sha256")
            and replayed.candidate_id == recorded_adapted.get("candidate_id")
        ):
            reports.append(
                LayerReport("adapted", True, f"{replayed.status} as recorded")
            )
        else:
            reports.append(
                LayerReport(
                    "adapted",
                    False,
                    f"recorded {recorded_adapted.get('status')}/"
                    f"{recorded_adapted.get('sha256')}, replay gives "
                    f"{replayed.status}/{replayed.sha256}",
                )
            )

    return Reconstruction(assembly_id, True, tuple(reports))

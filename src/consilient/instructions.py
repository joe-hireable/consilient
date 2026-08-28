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

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import beta as beta_mod
from . import promote, recall
from .events import (
    SCHEMA_VERSION,
    Event,
    EventError,
    EventPayload,
    append,
    canonical,
    event_sha256,
    read_all,
    resolve_reference,
)

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
ADAPTED_HEADER = (
    "# Adapted layer — learned about this user; changes only on a measured promoter β"
)

INERT_NOTICE = (
    "No adaptation has ever been promoted, so this layer is empty. Adaptation is "
    "proposed, measured and promoted through the native promoter (ADR-0018); while "
    "promoter β is unmeasured every proposal is refused. See `consil beta`."
)

INERT = "inert"
ACTIVE = "active"
BETTER_THAN_BEST_NAME = "better-than-best"
BETTER_THAN_BEST_FILE = "SKILL.md"
PROTOCOL_COMPLETED = "completed"
PROTOCOL_NOT_WARRANTED = "not_warranted"
COST_UNIT = "review_adjusted_minutes"
RELIANCE_CONSUMERS = frozenset(
    {"later_work", "money", "public_claim", "design_constraint"}
)
TRI_STATES = frozenset({"true", "false", "unknown"})

# Tokens too frequent to discriminate one skill from another. Selection is recorded
# with its matched tokens, so a bad match is auditable rather than hidden.
_STOPWORDS = frozenset(
    {
        "about",
        "after",
        "again",
        "against",
        "also",
        "always",
        "before",
        "being",
        "below",
        "between",
        "could",
        "does",
        "doing",
        "done",
        "each",
        "every",
        "from",
        "have",
        "here",
        "into",
        "just",
        "like",
        "made",
        "make",
        "more",
        "most",
        "must",
        "never",
        "only",
        "over",
        "same",
        "shall",
        "should",
        "some",
        "such",
        "than",
        "that",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "under",
        "until",
        "upon",
        "used",
        "uses",
        "what",
        "when",
        "where",
        "which",
        "while",
        "will",
        "with",
        "would",
        "your",
        # Generic in THIS corpus: every skill description talks about the user and
        # the system, so neither token discriminates one skill from another.
        "system",
        "user",
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
    capability_manifests: tuple[dict[str, str], ...]
    recall_receipt: dict[str, object]


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


@dataclass(frozen=True)
class EnvelopePart:
    """One reconstructable slot in a dispatch envelope."""

    name: str
    ok: bool
    digest: str | None
    detail: str


@dataclass(frozen=True)
class EnvelopeReconstruction:
    """Fresh-process reconstruction of one dispatch from trajectory and objects."""

    run_id: str
    ok: bool
    parts: tuple[EnvelopePart, ...]


@dataclass(frozen=True)
class IndexAnswer:
    """One generated-index hit compared by question, scope and version digest."""

    question_digest: str
    scope_digest: str
    version_digest: str
    verified: bool


@dataclass(frozen=True)
class IndexLookup:
    """A same-question lookup. Incomplete indexes cannot prove absence."""

    complete: bool
    question_digest: str
    scope_digest: str
    version_digest: str
    answers: tuple[IndexAnswer, ...] = ()


@dataclass(frozen=True)
class CostCeiling:
    """One review-adjusted-minutes ceiling. Unversioned inputs are incomparable."""

    minutes: float
    policy_version: str
    unit: str = COST_UNIT


@dataclass(frozen=True)
class ProtocolThreshold:
    """Conservative proxies for the Better-Than-Best skill's three conditions."""

    later_reliance: str
    question_open: str
    wrong_costs_more: str

    def __post_init__(self) -> None:
        for name, value in (
            ("later_reliance", self.later_reliance),
            ("question_open", self.question_open),
            ("wrong_costs_more", self.wrong_costs_more),
        ):
            if value not in TRI_STATES:
                raise ValueError(f"{name} must be true, false or unknown")

    @property
    def selects(self) -> bool:
        return "false" not in (
            self.later_reliance,
            self.question_open,
            self.wrong_costs_more,
        )

    @property
    def false_reasons(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, state in (
                ("later_reliance", self.later_reliance),
                ("question_open", self.question_open),
                ("wrong_costs_more", self.wrong_costs_more),
            )
            if state == "false"
        )


@dataclass(frozen=True)
class ProtocolBinding:
    """Decision-protocol references derived from a threshold and the pinned tree."""

    status: str
    threshold: ProtocolThreshold
    instructions_ref: dict[str, str] | None
    bar_ref: dict[str, str] | None
    search_ref: dict[str, str] | None
    killing_check_ref: dict[str, str] | None


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


def _later_reliance(consumers: Sequence[str] | None) -> str:
    if consumers is None:
        return "unknown"
    return "true" if any(kind in RELIANCE_CONSUMERS for kind in consumers) else "false"


def _question_open(index: IndexLookup | None) -> str:
    if index is None:
        return "unknown"
    matched = any(
        answer.verified
        and answer.question_digest == index.question_digest
        and answer.scope_digest == index.scope_digest
        and answer.version_digest == index.version_digest
        for answer in index.answers
    )
    if matched:
        return "false"
    if not index.complete:
        return "unknown"
    return "true"


def _wrong_costs_more(rework: CostCeiling | None, protocol: CostCeiling | None) -> str:
    if rework is None or protocol is None:
        return "unknown"
    if not rework.policy_version or not protocol.policy_version:
        return "unknown"
    if rework.policy_version != protocol.policy_version:
        return "unknown"
    if rework.unit != protocol.unit:
        return "unknown"
    return "true" if rework.minutes > protocol.minutes else "false"


def protocol_threshold(
    *,
    consumers: Sequence[str] | None = None,
    index: IndexLookup | None = None,
    rework_ceiling: CostCeiling | None = None,
    protocol_cost_ceiling: CostCeiling | None = None,
) -> ProtocolThreshold:
    """Return the three conservative proxies. Unknown never becomes a skip."""

    return ProtocolThreshold(
        later_reliance=_later_reliance(consumers),
        question_open=_question_open(index),
        wrong_costs_more=_wrong_costs_more(rework_ceiling, protocol_cost_ceiling),
    )


def _skill_file(skills_dir: Path, name: str) -> Path:
    return skills_dir / name / BETTER_THAN_BEST_FILE


def _load_named_skill(skills_dir: Path, name: str) -> SkillRef:
    path = _skill_file(skills_dir, name)
    if not path.is_file():
        raise InstructionError(f"the {name} skill is missing from {path.as_posix()}")
    body = path.read_text(encoding="utf-8")
    fields = _frontmatter(body)
    recorded_name = fields.get("name") or path.parent.name
    if recorded_name != name:
        raise InstructionError(
            f"skill at {path.as_posix()} declares name {recorded_name!r}, not {name!r}"
        )
    return SkillRef(
        name=recorded_name,
        path=f"{skills_dir.as_posix().rstrip('/')}/{name}/{BETTER_THAN_BEST_FILE}",
        sha256=promote.digest(body),
        matched=(),
        body=body,
    )


def _bind_selected_skill(
    skills: tuple[SkillRef, ...], skills_dir: Path, threshold: ProtocolThreshold | None
) -> tuple[SkillRef, ...]:
    if threshold is None or not threshold.selects:
        return skills
    required = _load_named_skill(skills_dir, BETTER_THAN_BEST_NAME)
    if any(skill.name == required.name for skill in skills):
        return skills
    return (required, *skills)


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
    note = (
        f" ({skills_omitted} further matched skill(s) omitted by the budget)"
        if skills_omitted
        else ""
    )
    parts.append(f"\n{SKILLS_HEADER}{note}\n")
    for skill in skills:
        parts.append(f"\n## {skill.name}\n\n{skill.body.rstrip()}\n")
    parts.append(f"\n{RECALL_HEADER}\n\n{recall_pack.rstrip()}\n")
    adapted_text = adapted.text if adapted.status == ACTIVE else INERT_NOTICE
    parts.append(f"\n{ADAPTED_HEADER}\n\n{adapted_text.rstrip()}\n")
    return "".join(parts)


def _source_digest(events: Sequence[Event]) -> str:
    return promote.digest("\n".join(canonical(event.raw) for event in events))


# The omission list used to be inlined here in full, and it is what made the trajectory grow
# faster every day. MEASURED 24 August 2026: .harness/log/ went 21,137 -> 166,465 -> 792,359 ->
# 1,069,904 -> 5,865,602 -> 40,771,519 bytes across six days. The list grows with the log, so
# each `instructions.assembled` event is larger than the last, so the log grows faster, so the
# next event is larger again. One sampled event was 85,442 B of which `data.recall.omitted` was
# 84,603 B -- 99%, 454 entries -- while `selected_event_ids` was EMPTY.
#
# That is not a tidiness problem. Dozens of concurrent dispatchers then collide on Windows
# byte-range locks over a 40 MB file, and `could not be read after 6 attempts: observed access
# denial` became the commonest crash signature in driver state, with single units dying that way
# 77 and 78 times. The compounding receipt stopped the build lane.
#
# A digest keeps the audit property and drops the bytes: `verify` compares through this same
# function, so a replay that produces a different omission set produces a different digest. What
# is lost is the ability to read WHICH events were omitted straight out of the log; that is a
# real cost, accepted, because the alternative is a log nothing can read at all.
_OMISSION_FIELDS = ("event_id", "event_kind", "reason", "protected")


def _omission_rows(selection: recall.Selection) -> list[dict[str, object]]:
    # Written out rather than via getattr: `getattr` is in FORBIDDEN_CALLS for this package
    # (tests/test_budget.py), because dynamic attribute access is a capability escape hatch.
    return [
        {
            "event_id": omission.event_id,
            "event_kind": omission.event_kind,
            "reason": omission.reason,
            "protected": omission.protected,
        }
        for omission in selection.omissions
    ]


def _omitted_digest(rows: Sequence[Mapping[str, object]]) -> str:
    """Digest the omission set. Key order cannot matter -- `canonical` sorts."""
    return promote.digest(
        canonical(
            {"omitted": [{k: row.get(k) for k in _OMISSION_FIELDS} for row in rows]}
        )
    )


def _selection_receipt(selection: recall.Selection) -> dict[str, object]:
    rows = _omission_rows(selection)
    return {
        "selected_event_ids": list(selection.selected_event_ids),
        "selected_digest": selection.selected_digest,
        "omitted_count": len(rows),
        "omitted_digest": _omitted_digest(rows),
        "context_complete": selection.context_complete,
        "continuation": (
            {"event_id": selection.continuation_event_id}
            if selection.continuation_event_id is not None
            else None
        ),
    }


_RECEIPT_FIELDS = (
    "selected_event_ids",
    "selected_digest",
    "omitted_count",
    "omitted_digest",
    "context_complete",
    "continuation",
)


def _recorded_selection_receipt(recall_data: Mapping[str, object]) -> dict[str, object]:
    """Read a recorded receipt in the current shape OR the pre-24-August fat-list shape.

    Events already written carry the full `omitted` list and must keep verifying, so an old
    record is folded forward by digesting the list it stored. Both sides then route through
    `_omitted_digest`, which is what preserves the property: a different omission set still
    produces a different digest, whichever shape it was recorded in.

    A digest-era record that also inlines `omitted` is not either of those shapes. The
    extra key is kept so equality with `_selection_receipt` fails, and `reconstruct`
    names the co-resident list rather than treating it as invisible extra.
    """
    data = {field: recall_data.get(field) for field in _RECEIPT_FIELDS}
    if "omitted" in recall_data:
        if recall_data.get("omitted_digest") is not None:
            # Digest-era record that still inlines the list. Reconstruct refuses
            # this shape before comparing; keep the key so a caller that only
            # compares receipts cannot treat the fat list as invisible extra.
            data["omitted"] = recall_data.get("omitted")
        else:
            legacy = recall_data.get("omitted")
            rows = (
                [row for row in legacy if isinstance(row, Mapping)]
                if isinstance(legacy, list)
                else []
            )
            data["omitted_count"] = len(rows)
            data["omitted_digest"] = _omitted_digest(rows)
    return data


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


# The newest events the recall scan starts from. Protected events are always included on top
# of this, whatever their age, so the bound cannot hide one.
#
# MEASURED 25 August 2026, and it had stopped the harness dispatching at all. `assemble` reads
# the whole trajectory and hands it to this function, which began its scan at EVERY event. The
# trajectory had reached 48 MB across ~3,100 events -- 283 of them over 80 KB each, because
# until Z01 landed every `instructions.assembled` event inlined its full omitted list -- and a
# full-window scan then took OVER TEN MINUTES.
#
# `dispatch.py` calls `instructions.assemble(...)` immediately BEFORE it writes `brief.md`, so
# every dispatch sat in this scan and never wrote the brief the agent was told to read. The
# agent had nothing to do, produced nothing, and the driver recorded
# "START_FAILED -- no artefact within the start window (0 bytes after 3711.74s)". Ten runs
# died that way in one night, each burning an hour, and the units they carried never started.
#
# Z01 stopped the log growing -- 25 August's file is 627 KB against the 24th's 48 MB -- but an
# append-only log never shrinks, so the cost of reading it can only be bounded here. A scan
# that grows without limit is a dispatch cost that grows without limit.
#
# This is not a weakened check. `scan_complete` becomes False, which is an outcome the receipt
# already models: the selection records `context_complete: false` and a continuation event id,
# so a bounded scan is declared rather than silently passed off as a whole one. `verify`
# replays through this same function, so both sides bound identically and the digests still
# agree.
RECALL_SCAN_EVENTS = 400

# How many BULK-protected events the scan starts from. Rank 4 (active commitments) and rank 3
# (committed work, and turns linked to it) are never bounded -- those are few, and dropping one
# would lose something the context genuinely depends on. This bounds rank 2 only: the
# always-include AUDIT kinds.
#
# MEASURED 25 August 2026. `_protected_event_indexes` returned 1,544 of 5,311 events, and
# because protected events are added to the candidate REGARDLESS of the scan window, the
# candidate was 1,877 events and 13.2 MILLION characters however small the window got. Where
# that came from:
#
#     dispatch.outcome   845 events   6,778,908 chars   51.4%
#     capability.gap     578 events   4,657,831 chars   35.3%
#     dispatch.refused   118 events   1,333,841 chars   10.1%
#
# 97% of the scan, and all three are in ALWAYS_INCLUDE_KINDS. Every dispatch WRITES a
# dispatch.outcome, so every dispatch then had to rescan all 845 previous ones: the cost of
# starting work grew linearly with the amount of work already done. `select_events` took 164 s
# per attempt and raised ValueError because the protected floor alone could not fit the
# character limit -- so the shrink loop halved the window, which changes nothing about the
# floor, and tried again. Twelve times. Over ten minutes, every dispatch, before the brief was
# written.
#
# "Always include" cannot mean "include every one ever recorded" in an append-only log; that is
# not a policy, it is an unbounded scan wearing a policy's clothes. Recency is the honest bound,
# and the receipt already models the consequence: an omission carries `protected: true`, so a
# dropped protected event is DECLARED rather than quietly dropped.
PROTECTED_SCAN_EVENTS = 200


def _bounded_protection(events: Sequence[Event]) -> frozenset[int]:
    """Protected indexes, with the bulk audit kinds bounded to the most recent."""
    ranks = recall._protection_ranks(events)
    keep = {index for index, rank in enumerate(ranks) if rank >= 3}
    bulk = [index for index, rank in enumerate(ranks) if rank == 2]
    keep.update(bulk[-PROTECTED_SCAN_EVENTS:])
    return frozenset(keep)


def _select_recall(
    events: Sequence[Event], *, query: str, limit_chars: int
) -> recall.Selection:
    """Shrink the scan window until its honest receipt fits, then return its provenance."""
    window = min(len(events), RECALL_SCAN_EVENTS)
    protected = _bounded_protection(events)
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
            if (
                accepted[candidate_id] != text_digest
                or promote.digest(text) != text_digest
            ):
                continue
            applied = [layer for layer in applied if layer.candidate_id != candidate_id]
            applied.append(AdaptedLayer(ACTIVE, text, candidate_id))
    return applied[-1] if applied else _INERT_LAYER


def load_adapted(log_dir: Path) -> AdaptedLayer:
    events, _ = read_all(log_dir)
    return _adapted_from_events(events)


def bind_recall_receipt(pack: str) -> dict[str, object]:
    """Digest one canonical recall receipt, or name why it cannot be bound."""
    try:
        receipt = recall.parse_receipt(pack)
    except ValueError as exc:
        return {"status": "refused", "reason": str(exc)}
    encoded = json.dumps(
        receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )
    return {"status": "ok", "digest": promote.digest(encoded)}


def _capability_manifest_bindings(
    selection: Mapping[str, object] | None,
) -> tuple[dict[str, str], ...]:
    """Take the M04 selector result. An absent request selects nothing."""
    if selection is None:
        return ()
    rows = selection.get("selected_manifests")
    if not isinstance(rows, list):
        return ()
    bound: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        identity = row.get("identity")
        version = row.get("version_digest")
        if isinstance(identity, str) and isinstance(version, str):
            bound.append({"identity": identity, "version_digest": version})
    return tuple(bound)


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


def record_assembly(
    log_dir: Path,
    assembly: Assembly,
    *,
    task: str,
    pre_run_records: Mapping[str, object] | None = None,
) -> EventPayload:
    """Append the assembly through the single writer, naming every layer (V0-47)."""
    now = datetime.now(timezone.utc)
    receipt = _selection_receipt(assembly.recall_selection)
    recall_payload: dict[str, object] = {
        "query": task,
        "limit_chars": assembly.recall_limit_chars,
        "sha256": promote.digest(assembly.recall_pack),
        "source_events": assembly.recall_source_events,
        "source_digest": assembly.recall_source_digest,
    }
    for field in _RECEIPT_FIELDS:
        recall_payload[field] = receipt[field]
    # The compounding loop was this list landing on instructions.assembled. Copying
    # only `_RECEIPT_FIELDS` already drops it; the raise is the chokepoint so a
    # later edit that re-adds the key cannot append.
    if "omitted" in recall_payload:
        raise InstructionError(
            "instructions.assembled must not inline the omission list"
        )
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
                "recall": recall_payload,
                "adapted": {
                    "status": assembly.adapted.status,
                    "sha256": assembly.adapted.sha256,
                    "candidate_id": assembly.adapted.candidate_id,
                },
                "recall_receipt": dict(assembly.recall_receipt),
                "capability_manifests": [
                    dict(row) for row in assembly.capability_manifests
                ],
                "pre_run_records": dict(pre_run_records or {}),
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
    return ProposalOutcome(
        decision=decision, event=event, explanation=_explain(decision)
    )


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
            (
                LayerReport(
                    "event", False, "no instructions.assembled event carries this id"
                ),
            ),
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
            LayerReport(
                "core", False, "the rendered core digest does not match the record"
            )
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
            recorded_path = entry.get("path")
            path = skills_dir / str(name) / BETTER_THAN_BEST_FILE
            if isinstance(recorded_path, str):
                normalised = recorded_path.replace("\\", "/")
                suffix = f"{name}/{BETTER_THAN_BEST_FILE}"
                if not normalised.endswith(suffix):
                    skill_reports_ok = False
                    skill_details.append(f"{name}: path drifted")
                    continue
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
        reports.append(
            LayerReport("recall", False, "the record carries no recall layer")
        )
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
            reports.append(
                LayerReport("recall", False, "the recall record is malformed")
            )
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
                    "recall",
                    False,
                    "the pinned log prefix no longer digests to the record",
                )
            )
        else:
            selection = _select_recall(
                events[:source_events], query=query, limit_chars=limit_chars
            )
            pack = selection.text
            if promote.digest(pack) != recorded_pack_sha:
                reports.append(
                    LayerReport(
                        "recall", False, "the replayed pack does not match the record"
                    )
                )
            elif (
                recall_data.get("omitted_digest") is not None
                and "omitted" in recall_data
            ):
                reports.append(
                    LayerReport(
                        "recall",
                        False,
                        "the recorded receipt inlines omitted next to omitted_digest",
                    )
                )
            elif any(
                key in recall_data for key in (*_RECEIPT_FIELDS, "omitted")
            ) and _selection_receipt(selection) != _recorded_selection_receipt(
                recall_data
            ):
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
        reports.append(
            LayerReport("adapted", False, "the record carries no adapted layer")
        )
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


def _object_digest(workspace_root: Path, locator: object) -> tuple[str | None, str]:
    if not isinstance(locator, str) or not locator or locator.startswith("/"):
        return None, "object locator is not a repository-relative path"
    if ".." in locator.split("/") or "\\" in locator:
        return None, "object locator is not a canonical relative path"
    path = workspace_root / locator
    try:
        payload = path.read_bytes()
    except OSError as exc:
        return None, f"object unreadable: {exc}"
    return hashlib.sha256(payload).hexdigest(), "matched object bytes"


def _part_from_binding(name: str, binding: object, workspace_root: Path) -> EnvelopePart:
    if not isinstance(binding, dict):
        return EnvelopePart(name, False, None, "missing binding")
    status = binding.get("status")
    if status != "ok":
        reason = binding.get("reason")
        return EnvelopePart(
            name,
            False,
            None,
            str(reason if isinstance(reason, str) and reason else status),
        )
    digest = binding.get("digest")
    locator = binding.get("object_locator")
    if not isinstance(digest, str):
        return EnvelopePart(name, False, None, "incomplete ok binding")
    actual, detail = _object_digest(workspace_root, locator)
    if actual is None:
        return EnvelopePart(name, False, digest, detail)
    if actual != digest:
        return EnvelopePart(name, False, digest, "digest mismatch")
    return EnvelopePart(name, True, digest, detail)


def reconstruct_envelope(
    log_dir: Path, workspace_root: Path, run_id: str
) -> EnvelopeReconstruction:
    """Rebuild one dispatch envelope from the trajectory and object store."""
    events, _rejected = read_all(log_dir)
    outcome: Event | None = None
    for event in events:
        if event.kind == "dispatch.outcome" and event.data.get("run_id") == run_id:
            outcome = event
    if outcome is None:
        return EnvelopeReconstruction(
            run_id,
            False,
            (EnvelopePart("outcome", False, None, "no dispatch.outcome for run"),),
        )

    assembly_id = outcome.data.get("assembly_id")
    assembled: Event | None = None
    if isinstance(assembly_id, str):
        for event in events:
            if event.kind == ASSEMBLED and event.data.get("assembly_id") == assembly_id:
                assembled = event

    parts: list[EnvelopePart] = []
    pre_run = assembled.data.get("pre_run_records") if assembled is not None else None
    if not isinstance(pre_run, dict):
        pre_run = {}
    parts.append(_part_from_binding("task", pre_run.get("task"), workspace_root))
    parts.append(
        _part_from_binding("instructions", pre_run.get("instructions"), workspace_root)
    )

    receipt = assembled.data.get("recall_receipt") if assembled is not None else None
    if isinstance(receipt, dict) and receipt.get("status") == "ok":
        digest = receipt.get("digest")
        parts.append(
            EnvelopePart(
                "recall_receipt",
                isinstance(digest, str),
                digest if isinstance(digest, str) else None,
                "bound" if isinstance(digest, str) else "missing digest",
            )
        )
    else:
        reason = receipt.get("reason") if isinstance(receipt, dict) else "missing"
        parts.append(
            EnvelopePart(
                "recall_receipt",
                False,
                None,
                str(reason if isinstance(reason, str) and reason else "missing"),
            )
        )

    manifests = (
        assembled.data.get("capability_manifests") if assembled is not None else None
    )
    if manifests == []:
        parts.append(EnvelopePart("capability_manifests", True, None, "none selected"))
    elif isinstance(manifests, list) and manifests:
        valid = True
        first_digest: str | None = None
        for row in manifests:
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("identity"), str)
                or not isinstance(row.get("version_digest"), str)
            ):
                valid = False
                break
            if first_digest is None:
                version = row.get("version_digest")
                first_digest = version if isinstance(version, str) else None
        parts.append(
            EnvelopePart(
                "capability_manifests",
                valid,
                first_digest,
                "bound" if valid else "invalid manifest binding",
            )
        )
    else:
        parts.append(EnvelopePart("capability_manifests", False, None, "missing"))

    outputs = outcome.data.get("output_records")
    if not isinstance(outputs, dict):
        outputs = {}
    for name in ("stdout", "stderr", "artefact_manifest", "verifier_outcome"):
        parts.append(_part_from_binding(name, outputs.get(name), workspace_root))

    listed = outputs.get("listed_artefacts")
    if listed is None or listed == []:
        parts.append(EnvelopePart("listed_artefacts", True, None, "none listed"))
    elif isinstance(listed, list):
        failed: list[str] = []
        for index, row in enumerate(listed):
            part = _part_from_binding(f"listed_artefacts[{index}]", row, workspace_root)
            if not part.ok:
                failed.append(part.detail)
        parts.append(
            EnvelopePart(
                "listed_artefacts",
                not failed,
                None,
                "; ".join(failed) if failed else "matched object bytes",
            )
        )
    else:
        parts.append(
            EnvelopePart("listed_artefacts", False, None, "listed_artefacts is not a list")
        )

    return EnvelopeReconstruction(
        run_id, all(part.ok for part in parts), tuple(parts)
    )


def _event_reference(raw: EventPayload) -> dict[str, str]:
    event_id = raw.get("event_id")
    kind = raw.get("event")
    if not isinstance(event_id, str) or not isinstance(kind, str):
        raise InstructionError("instructions.assembled is missing a stable identity")
    return {
        "event_id": event_id,
        "event_kind": kind,
        "event_sha256": event_sha256(raw),
    }


def _same_task_assembly(events: Sequence[Event], task: str) -> Event | None:
    found: Event | None = None
    for event in events:
        if event.kind != ASSEMBLED:
            continue
        recall_data = event.data.get("recall")
        if not isinstance(recall_data, dict):
            continue
        if recall_data.get("query") != task:
            continue
        found = event
    return found


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

"""What may enter a layer, and the frozen shapes that describe one once it has.

record_adapted is the chokepoint. Promoted content is admitted only against a recorded,
unreversed promote.accepted whose postimage digest it matches, so a hand edit has no
acceptance to match and unpromoted content is inert by construction — there is no second
path to the layer, which is working principle 3 -- a chokepoint without an enforcement
rule is not a chokepoint -- applied to self-modification.

  V0-48  Adapted content enters the layer only against an unreversed promote.accepted
         whose postimage digest it matches.

The rest of the file refuses in the same shape. A recall selection still carrying a
privileged field is refused rather than quietly trimmed; the protected floor of the scan
is bounded to the most recent bulk events instead of meaning every event ever recorded;
an envelope part is ok only when the bytes on disk digest to what the record claims, and
an unreadable or non-canonical locator is named rather than skipped. The core section is
rendered from the module constant alone, which is what keeps the adapted layer out of
it.

The records — Assembly, Reconstruction, EnvelopeReconstruction, and the
ProtocolThreshold with its cost-ceiling and index inputs — are frozen and derive nothing
but their own verdicts. A threshold state that is not true, false or unknown is rejected
on construction, and unknown never becomes a skip: only an explicit false stops the
decision protocol firing."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from . import promote, recall
from .events import (
    SCHEMA_VERSION,
    Event,
    EventPayload,
    append,
    canonical,
    event_sha256,
    read_all,
)
from .instructions_vocabulary import (
    ACTOR,
    ADAPTED,
    ADAPTED_LAYER_PATH,
    ADAPTED_LIMIT_CHARS,
    ASSEMBLED,
    AdaptedLayer,
    BETTER_THAN_BEST_FILE,
    CORE_HEADER,
    COST_UNIT,
    EnvelopePart,
    INERT,
    INVARIANT_CORE,
    IndexAnswer,
    InstructionError,
    LayerReport,
    PROTECTED_SCAN_EVENTS,
    RELIANCE_CONSUMERS,
    SkillRef,
    TRI_STATES,
    _OMISSION_FIELDS,
    _STOPWORDS,
    _TOKEN,
    _object_digest,
)


__all__ = [
    "ACTOR",
    "ADAPTED",
    "ADAPTED_LAYER_PATH",
    "ADAPTED_LIMIT_CHARS",
    "ASSEMBLED",
    "AdaptedLayer",
    "Assembly",
    "BETTER_THAN_BEST_FILE",
    "CORE_HEADER",
    "COST_UNIT",
    "CostCeiling",
    "EnvelopePart",
    "EnvelopeReconstruction",
    "INERT",
    "INVARIANT_CORE",
    "IndexAnswer",
    "IndexLookup",
    "InstructionError",
    "KINDS",
    "LayerReport",
    "PROTECTED_SCAN_EVENTS",
    "ProtocolThreshold",
    "RELIANCE_CONSUMERS",
    "Reconstruction",
    "SkillRef",
    "TRI_STATES",
    "_OMISSION_FIELDS",
    "_STOPWORDS",
    "_TOKEN",
    "_object_digest",
    "record_adapted",
]

KINDS = frozenset({ASSEMBLED, ADAPTED})

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
class EnvelopeReconstruction:
    """Fresh-process reconstruction of one dispatch from trajectory and objects."""

    run_id: str
    ok: bool
    parts: tuple[EnvelopePart, ...]


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


def _tokens(text: str) -> frozenset[str]:
    return frozenset(
        token
        for token in _TOKEN.findall(text.lower())
        if len(token) >= 4 and token not in _STOPWORDS
    )


def _later_reliance(consumers: Sequence[str] | None) -> str:
    if consumers is None:
        return "unknown"
    return "true" if any(kind in RELIANCE_CONSUMERS for kind in consumers) else "false"


def _skill_file(skills_dir: Path, name: str) -> Path:
    return skills_dir / name / BETTER_THAN_BEST_FILE


def _render_core(core_version: int) -> str:
    lines = "\n".join(f"- {line}" for line in INVARIANT_CORE)
    return f"{CORE_HEADER} (v{core_version})\n\n{lines}\n"


def _omitted_digest(rows: Sequence[Mapping[str, object]]) -> str:
    """Digest the omission set. Key order cannot matter -- `canonical` sorts."""
    return promote.digest(
        canonical(
            {"omitted": [{k: row.get(k) for k in _OMISSION_FIELDS} for row in rows]}
        )
    )


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


def _bounded_protection(events: Sequence[Event]) -> frozenset[int]:
    """Protected indexes, with the bulk audit kinds bounded to the most recent."""
    ranks = recall._protection_ranks(events)
    keep = {index for index, rank in enumerate(ranks) if rank >= 3}
    bulk = [index for index, rank in enumerate(ranks) if rank == 2]
    keep.update(bulk[-PROTECTED_SCAN_EVENTS:])
    return frozenset(keep)


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


def _part_from_binding(
    name: str, binding: object, workspace_root: Path
) -> EnvelopePart:
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

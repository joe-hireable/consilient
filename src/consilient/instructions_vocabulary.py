"""The fixed vocabulary of the instruction layers — core text, budgets, record shapes.

Nothing here reads anything else in the family; everything else reads this. It holds the
invariant core itself, the headers and character budgets each layer is rendered under,
the small frozen records a layer is described by — a selected skill, an adapted layer, a
reconstruction report, an envelope part, an index answer — the leaf helpers that turn
text into tokens, frontmatter and digests, and the wording a refused promotion explains
itself with.

INVARIANT_CORE carries the evidence tags, verify-by-artefact,
invariant-ships-with-its-check, refuse-rather-than-guess and the hard boundaries. It is
never adapted, never learned, never overridden. It lives in this file, which
promote.PROTECTED_PREFIXES puts beyond the promoter's reach, and the rendered core
section is built from this module constant and from nothing else — no assembly input can
reach it.

ADR-0057: the adapted layer is derived from the user's trajectory and inherits its
privacy. It is therefore persisted as trajectory events under the gitignored log
directory — never as a file a repository could publish — and it is never shared without
explicit consent. ADAPTED_LAYER_PATH is a logical address used by the promoter's
allowlist routing, not a file anything writes.

The budgets are the other load-bearing thing here, and they are measurements rather than
taste. RECALL_SCAN_EVENTS and PROTECTED_SCAN_EVENTS bound how much of an append-only
trajectory one assembly may read, and each carries beside it the day it was forced and
what it cost; a bound loosened here is a dispatch cost that grows with the amount of
work already done.
"""

from __future__ import annotations
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from . import beta as beta_mod
from . import promote, recall
from .events import (
    Event,
    EventPayload,
    canonical,
)

ACTOR = "consilient.instructions"

ASSEMBLED = "instructions.assembled"

ADAPTED = "instructions.adapted"

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
class EnvelopePart:
    """One reconstructable slot in a dispatch envelope."""

    name: str
    ok: bool
    digest: str | None
    detail: str


@dataclass(frozen=True)
class IndexAnswer:
    """One generated-index hit compared by question, scope and version digest."""

    question_digest: str
    scope_digest: str
    version_digest: str
    verified: bool


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


_RECEIPT_FIELDS = (
    "selected_event_ids",
    "selected_digest",
    "omitted_count",
    "omitted_digest",
    "context_complete",
    "continuation",
)

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

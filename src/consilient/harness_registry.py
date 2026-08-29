"""The harness, pool and decision vocabulary every other half of this family speaks.

This module holds the nouns and nothing that reasons about them: the six literal type
aliases, the frozen dataclasses (Harness, PoolState, Probe, Decision, FanoutDecision),
the registered harnesses, the default pool snapshot, the permission-mode flags, and the
three by-id lookups. It imports nothing from its siblings, which is what lets every one
of them import from it without a cycle.

DISPATCH_ACTOR lives here rather than beside the code that stamps it, because two
writers need it — harness_recording and harness_requests — and putting it in either
would make the other reach across. src/consilient/coordination.py restates it and a test
pins the equality, so the two cannot drift apart.

The permission-mode note is preserved verbatim above DEFAULT_PERMISSION_MODE: the
default is bypass because the principal asked that dispatched harnesses run without
per-tool prompts, and the flags were read from each CLI's --help on 21 August 2026.
[measured]
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DISPATCH_ACTOR = "consilient.dispatch"

Status = Literal["ok", "silent", "failed", "timeout", "refused", "killed"]

DecisionKind = Literal["run", "refuse"]

VerdictKind = Literal["agree", "disagree", "incomparable"]

PermissionMode = Literal["bypass", "prompt"]

# Default is bypass: the principal asked that dispatched harnesses run like this Grok
# session, without per-tool prompts. `prompt` is the attended alternative. Flags were
# read from each CLI's --help on 21 August 2026. [measured]
DEFAULT_PERMISSION_MODE: PermissionMode = "bypass"

BYPASS_FLAGS: dict[str, tuple[str, ...]] = {
    "claude": ("--dangerously-skip-permissions",),
    "codex": ("--dangerously-bypass-approvals-and-sandbox",),
    "grok": ("--always-approve",),
    "cursor-composer": ("--force", "--trust"),
}

SILENT_MARKERS: tuple[str, ...] = (
    "workspace trust required",
    "untrusted workspace",
    "trust this workspace",
)


@dataclass(frozen=True)
class Harness:
    """One installed-or-installable coding harness and the pool it draws on."""

    id: str
    family: str
    pool: str
    binary: str


@dataclass(frozen=True)
class PoolState:
    """Known headroom for one quota pool. `used_percent` is None when unknown."""

    name: str
    used_percent: float | None
    exhausted: bool
    note: str
    observed_at: str
    source: str


@dataclass(frozen=True)
class Probe:
    """Result of probing whether a harness is actually reachable. Produced by the runner."""

    harness_id: str
    installed: bool
    version: str | None
    detail: str


@dataclass(frozen=True)
class Decision:
    kind: DecisionKind
    harness: Harness | None
    reason: str
    considered: tuple[str, ...]


@dataclass(frozen=True)
class FanoutDecision:
    kind: DecisionKind
    first: Harness | None
    second: Harness | None
    reason: str
    considered: tuple[str, ...]


HARNESSES: tuple[Harness, ...] = (
    Harness(id="claude", family="anthropic", pool="claude-weekly", binary="claude"),
    Harness(
        id="cursor-composer",
        family="cursor",
        pool="cursor-models",
        binary="cursor-agent",
    ),
    Harness(id="grok", family="xai", pool="grok-weekly", binary="grok"),
    Harness(id="codex", family="openai", pool="codex-weekly", binary="codex"),
)

DEFAULT_OBSERVED_AT = "2026-08-21T00:00:00+00:00"

DEFAULT_SOURCE = "operator observation, 21 August 2026"

DEFAULT_POOLS: tuple[PoolState, ...] = (
    PoolState(
        name="claude-weekly",
        used_percent=None,
        exhausted=True,
        note="nearly exhausted",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="cursor-models",
        used_percent=1.0,
        exhausted=False,
        note="Cursor Models (composer)",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="cursor-other",
        used_percent=58.0,
        exhausted=False,
        note="avoid — Cursor Other Models (claude-*/gpt-*/gemini-*)",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="grok-weekly",
        used_percent=2.0,
        exhausted=False,
        note="SuperGrok Heavy weekly",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="codex-weekly",
        used_percent=None,
        exhausted=False,
        note="unknown",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
)


def permission_flags(
    harness_id: str, mode: PermissionMode = DEFAULT_PERMISSION_MODE
) -> tuple[str, ...]:
    """Flags the meta-harness injects. Empty in `prompt` mode. Unknown harnesses get none."""
    if mode == "prompt":
        return ()
    return BYPASS_FLAGS.get(harness_id, ())


def load_permission_mode(path: Path | None = None) -> PermissionMode:
    """INSTANCE override. Missing or unreadable file → the default, bypass."""
    if path is None or not path.is_file():
        return DEFAULT_PERMISSION_MODE
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_PERMISSION_MODE
    if not isinstance(raw, dict):
        return DEFAULT_PERMISSION_MODE
    mode = raw.get("mode")
    if mode == "bypass":
        return "bypass"
    if mode == "prompt":
        return "prompt"
    return DEFAULT_PERMISSION_MODE


def harness_by_id(
    harness_id: str, harnesses: tuple[Harness, ...] = HARNESSES
) -> Harness | None:
    for item in harnesses:
        if item.id == harness_id:
            return item
    return None


def pool_by_name(name: str, pools: tuple[PoolState, ...]) -> PoolState | None:
    for item in pools:
        if item.name == name:
            return item
    return None


def probe_by_id(harness_id: str, probes: Sequence[Probe]) -> Probe | None:
    for item in probes:
        if item.harness_id == harness_id:
            return item
    return None

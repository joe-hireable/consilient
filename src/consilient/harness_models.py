"""The Cursor model registry, and the provenance that decides which of its rows may be
spent.

The snapshot's own note is preserved above CURSOR_MODEL_POOL_ASSIGNMENTS: `cursor-agent
--list-models` on this machine, 21 August 2026, returned 204 ids [measured]. Vendor
Cursor Models inclusion, retrieved 24 August 2026, covers Composer 2.5 and Cursor Grok
4.5/4.6; claude-*, gpt-* and gemini-* bill to the avoided Other Models pool; Kimi and
GLM appear on the vendor's Other Models table by family name rather than by exact CLI
id, so those rows stay on cursor-models marked unverified and automatic selection
refuses them. `auto` is deliberately absent — selection must name what it spends.

The unverified rows are the point of separating this module. A model id whose pool
assignment came from a family-level table is not the same class of fact as one read off
the vendor's own inclusion list, and ModelOption carries the difference in a field
rather than in a comment. Reasoning capability works the same way: a scaffold is
permitted only where verified registry data says reasoning is absent, and native, hybrid
and unknown all fail closed.

scripts/refresh_models.py rewrites the MODELS literal in this file by path — repointed
in the same commit."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal
from .harness_registry import (
    HARNESSES,
    Harness,
    harness_by_id,
)


__all__ = [
    "AVOIDED_CURSOR_POOL",
    "CURSOR_MODELS_POOL_PROVENANCE",
    "CURSOR_MODEL_POOL_ASSIGNMENTS",
    "CURSOR_OTHER_PREFIXES",
    "CURSOR_UNVERIFIED_POOL_PROVENANCE",
    "HARNESSES",
    "Harness",
    "MODELS",
    "ModelOption",
    "REASONING_CAPABILITIES",
    "ReasoningCapability",
    "UNMAPPED_POOL_PROVENANCE",
    "UNMAPPED_REASONING_PROVENANCE",
    "allows_reasoning_scaffold",
    "cursor_models_pool_ids",
    "cursor_pool_for_model",
    "harness_by_id",
    "model_family",
    "models_for_harness",
    "parse_list_models",
    "pool_for_model",
    "registry_drift",
]

ReasoningCapability = Literal["native", "hybrid", "absent", "unknown"]

REASONING_CAPABILITIES: frozenset[str] = frozenset(
    {"native", "hybrid", "absent", "unknown"}
)

UNMAPPED_REASONING_PROVENANCE = (
    "unmapped model id; no verified reasoning-capability source"
)

UNMAPPED_POOL_PROVENANCE = "unmapped model id; no verified pool-assignment source"

CURSOR_MODELS_POOL_PROVENANCE = (
    "Cursor Models and Pricing, https://cursor.com/docs/models-and-pricing, "
    "retrieved 2026-08-24; Cursor Models includes Cursor Grok 4.6, Grok 4.5, "
    "and Composer 2.5 (including Fast variants)"
)

CURSOR_UNVERIFIED_POOL_PROVENANCE = (
    "Cursor Models and Pricing, https://cursor.com/docs/models-and-pricing, "
    "retrieved 2026-08-24; Other Models table lists Kimi K3, Kimi K2.7 Code, "
    "and GLM 5.2 by family, not by exact CLI id"
)

AVOIDED_CURSOR_POOL = "cursor-other"

CURSOR_OTHER_PREFIXES: tuple[str, ...] = ("claude-", "gpt-", "gemini-")


@dataclass(frozen=True)
class ModelOption:
    """One selectable model, its quota pool, and verified routing provenance.

    `native` means mandatory reasoning and `hybrid` means a user-selectable native
    mode. Legacy callers default to fail-closed `unknown`; a model name never supplies
    evidence about reasoning capability or pool assignment.
    """

    id: str
    harness_id: str
    family: str
    pool: str
    reasoning_capability: ReasoningCapability = "unknown"
    reasoning_provenance: str = UNMAPPED_REASONING_PROVENANCE
    pool_verified: bool = False
    pool_provenance: str = UNMAPPED_POOL_PROVENANCE

    def __post_init__(self) -> None:
        if (
            not isinstance(self.reasoning_capability, str)
            or self.reasoning_capability not in REASONING_CAPABILITIES
        ):
            raise ValueError(
                "reasoning_capability must be native, hybrid, absent, or unknown"
            )
        if (
            not isinstance(self.reasoning_provenance, str)
            or not self.reasoning_provenance.strip()
        ):
            raise ValueError("reasoning_provenance must be a non-empty string")
        if not isinstance(self.pool_verified, bool):
            raise ValueError("pool_verified must be a bool")
        if (
            not isinstance(self.pool_provenance, str)
            or not self.pool_provenance.strip()
        ):
            raise ValueError("pool_provenance must be a non-empty string")


def allows_reasoning_scaffold(model: ModelOption) -> bool:
    """Permit a scaffold only when verified registry data says reasoning is absent.

    Native mandatory, hybrid user-selectable, and unknown capabilities all fail closed.
    """
    return model.reasoning_capability == "absent"


# `cursor-agent --list-models` on this machine, 21 August 2026 [measured]: 204 ids.
# Vendor Cursor Models inclusion (retrieved 2026-08-24): Composer 2.5 and Cursor Grok
# 4.5/4.6. claude-*/gpt-*/gemini-* bill to the avoided Other Models pool
# (CURSOR_OTHER_PREFIXES). Kimi/GLM appear on the vendor Other Models table by family
# name, not by exact CLI id, so those rows stay on cursor-models marked unverified and
# automatic selection refuses them. Only cursor-composer has a measured multi-model
# surface today; the other harnesses expose no probed model list here, so they register
# none rather than an invented one. `auto` is deliberately absent: selection must name
# what it spends. Registry order is the preference order within a family when pools
# tie — highest measured tier first [asserted].
CURSOR_MODEL_POOL_ASSIGNMENTS: tuple[tuple[str, str, bool, str], ...] = (
    ("composer-2.5", "composer", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("composer-2.5-fast", "composer", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("kimi-k3-max", "kimi", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
    ("kimi-k3-high", "kimi", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
    ("kimi-k3-low", "kimi", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
    ("kimi-k2.7-code", "kimi", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
    ("cursor-grok-4.6-xhigh", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-xhigh-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-high", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-high-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-medium", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-medium-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-low", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.6-low-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-high", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-high-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-medium", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-medium-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-low", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("cursor-grok-4.5-low-fast", "grok", True, CURSOR_MODELS_POOL_PROVENANCE),
    ("glm-5.2-max", "glm", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
    ("glm-5.2-high", "glm", False, CURSOR_UNVERIFIED_POOL_PROVENANCE),
)

MODELS: tuple[ModelOption, ...] = tuple(
    ModelOption(
        model_id,
        "cursor-composer",
        family,
        "cursor-models",
        pool_verified=pool_verified,
        pool_provenance=pool_provenance,
    )
    for model_id, family, pool_verified, pool_provenance in CURSOR_MODEL_POOL_ASSIGNMENTS
)


def models_for_harness(
    harness_id: str, models: tuple[ModelOption, ...] = MODELS
) -> tuple[ModelOption, ...]:
    return tuple(item for item in models if item.harness_id == harness_id)


def model_family(model_id: str) -> str:
    """The model family an id belongs to. A heuristic for unregistered ids."""
    lowered = model_id.strip().casefold()
    if lowered.startswith("cursor-grok"):
        return "grok"
    return lowered.split("-", 1)[0]


def pool_for_model(
    harness_id: str,
    model_id: str,
    *,
    models: tuple[ModelOption, ...] = MODELS,
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> str:
    """The pool a model draws on: the registry first, then the prefix rule."""
    for item in models:
        if item.harness_id == harness_id and item.id == model_id:
            return item.pool
    if harness_id == "cursor-composer":
        return cursor_pool_for_model(model_id)
    harness = harness_by_id(harness_id, harnesses)
    return harness.pool if harness is not None else "unknown"


def cursor_pool_for_model(model: str) -> str:
    """Composer draws on Cursor Models; vendor aliases draw on the avoided Other pool."""
    lowered = model.strip().casefold()
    for prefix in CURSOR_OTHER_PREFIXES:
        if lowered.startswith(prefix):
            return "cursor-other"
    return "cursor-models"


def parse_list_models(output: str) -> tuple[str, ...]:
    """Model ids from `cursor-agent --list-models` output, in output order.

    Lines are `id - Display Name`; the header and blank lines carry no ` - `
    separator and drop out. Ids contain no spaces, so anything before the first
    separator that does is not an id line. Parsing is pure: the subprocess that
    produces `output` lives in scripts/refresh_models.py, not here (AST lock).
    """
    ids: list[str] = []
    for raw in output.splitlines():
        line = raw.strip()
        if " - " not in line:
            continue
        candidate = line.split(" - ", 1)[0].strip()
        if candidate and " " not in candidate:
            ids.append(candidate)
    return tuple(ids)


def cursor_models_pool_ids(live_ids: Sequence[str]) -> tuple[str, ...]:
    """The live ids that bill to the Cursor Models pool: no vendor aliases, no `auto`.

    `auto` is excluded because the registry omits it deliberately — selection must
    name what it spends — so its absence from MODELS is policy, not drift.
    """
    return tuple(
        sorted(
            {
                item.strip()
                for item in live_ids
                if item.strip()
                and item.strip() != "auto"
                and cursor_pool_for_model(item) == "cursor-models"
            }
        )
    )


def registry_drift(
    live_ids: Sequence[str],
    registered: tuple[ModelOption, ...] = MODELS,
    *,
    harness_id: str = "cursor-composer",
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(unregistered live ids, stale registered ids) on the Cursor Models surface.

    Vendor-pool ids are out of scope: the registry never lists them, so their
    absence is the avoid-pool rule working, not the snapshot going stale.
    """
    live = set(cursor_models_pool_ids(live_ids))
    known = {item.id for item in registered if item.harness_id == harness_id}
    return tuple(sorted(live - known)), tuple(sorted(known - live))

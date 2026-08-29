"""Inventory, gate and request builders shared by the test_capabilities_* family.

Not named test_*, so pytest does not collect it. ROOT/CORE/PACKAGE/SCRIPT live here rather than
being redeclared per file: `Path(__file__).resolve().parents[1]` resolves to the repository root
from any module in tests/, and one definition means a moved file cannot leave a stale copy
pointing somewhere else.
"""

import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORE = ROOT / "src" / "consilient" / "capabilities.py"

PACKAGE = ROOT / "src" / "consilient"

SCRIPT = ROOT / "scripts" / "capability_context.py"

sys.path.insert(0, str(ROOT / "src"))

from consilient.capabilities import (  # noqa: E402
    default_gate,
)


def _inventory(*items: dict[str, object]) -> dict[str, object]:
    return {"allowlist": list(items)}


def _authority_event() -> dict[str, object]:
    return {
        "event_id": "evt-authority-1",
        "event_kind": "human.approval",
        "event_sha256": "b" * 64,
    }


def _admitted_gate(
    *, expires_at: str | None = "2099-01-01T00:00:00+00:00"
) -> dict[str, object]:
    return {
        "state": "admitted",
        "reason": "exact_grant",
        "grant_kind": "principal_authority",
        "authority_event": _authority_event(),
        "decision_id": None,
        "recovery_proof_ref": None,
        "scope": [],
        "operations": [],
        "effect_classes": [],
        "expires_at": expires_at,
    }


def _gated_gate() -> dict[str, object]:
    gate = default_gate()
    return {
        "state": gate.state,
        "reason": gate.reason,
        "grant_kind": gate.grant_kind,
        "authority_event": gate.authority_event,
        "decision_id": gate.decision_id,
        "recovery_proof_ref": gate.recovery_proof_ref,
        "scope": list(gate.scope),
        "operations": list(gate.operations),
        "effect_classes": list(gate.effect_classes),
        "expires_at": gate.expires_at,
    }


def _available(
    kind: str,
    name: str,
    *,
    provenance: list[str] | None = None,
) -> dict[str, object]:
    return {
        "kind": kind,
        "name": name,
        "available": True,
        "provenance": provenance or [f"probe:{kind}:{name}"],
        "gate": _admitted_gate(),
    }


def _selected(
    kind: str,
    name: str,
    *,
    provenance: list[str],
    reason: str,
) -> dict[str, object]:
    return {
        "kind": kind,
        "name": name,
        "provenance": provenance,
        "reason": reason,
        "gate": _admitted_gate(),
    }


def _request(*items: dict[str, object]) -> dict[str, object]:
    return {"capabilities": list(items)}


def _wanted(
    kind: str, name: str, reason: str = "needed by this task"
) -> dict[str, object]:
    return {"kind": kind, "name": name, "reason": reason}

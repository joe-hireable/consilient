"""Selection refuses on the gate: gated, unexpired, expired, and malformed rows.

Grouped because expiry is where the fail-open would be cheapest to introduce -- a grant that
expired a minute ago and one that expires in a minute differ by one comparison, and both cases
are pinned here side by side so a change to that comparison cannot pass by fixing only one.
"""

import sys

from datetime import datetime, timedelta, timezone

import pytest

from capabilities_helpers import (
    ROOT,
    _admitted_gate,
    _available,
    _gated_gate,
    _inventory,
    _request,
    _wanted,
)

sys.path.insert(0, str(ROOT / "src"))

from consilient.capabilities import (
    CapabilityError,
    parse_inventory_entry,
    select_capabilities,
)


def test_select_refuses_a_gated_inventory_entry() -> None:
    inventory = _inventory(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
            "gate": _gated_gate(),
        }
    )
    with pytest.raises(CapabilityError, match=r"gated capability: tool:pytest"):
        select_capabilities(inventory, _request(_wanted("tool", "pytest")))


def test_select_rejects_admitted_gate_without_expiry() -> None:
    inventory = _inventory(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
            "gate": {
                "state": "admitted",
                "reason": "exact_grant",
                "grant_kind": "controller_baseline.local_restorable.v1",
                "authority_event": None,
                "decision_id": "decision-1",
                "recovery_proof_ref": {
                    "event_id": "evt-proof-1",
                    "event_kind": "effect.receipt",
                    "event_sha256": "c" * 64,
                },
                "scope": ["workspace"],
                "operations": ["read"],
                "effect_classes": ["data.read"],
                "expires_at": None,
            },
        }
    )
    with pytest.raises(CapabilityError, match="expires_at"):
        parse_inventory_entry(inventory["allowlist"][0])
    with pytest.raises(CapabilityError, match="expires_at"):
        select_capabilities(inventory, _request(_wanted("tool", "pytest")))


def test_select_refuses_an_entry_whose_gate_is_synthesised_as_gated() -> None:
    inventory = _inventory(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
        }
    )
    with pytest.raises(CapabilityError, match=r"gated capability: tool:pytest"):
        select_capabilities(inventory, _request(_wanted("tool", "pytest")))


def test_select_refuses_an_expired_grant() -> None:
    inventory = _inventory(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
            "gate": _admitted_gate(expires_at="2000-01-01T00:00:00+00:00"),
        }
    )
    with pytest.raises(CapabilityError, match=r"expired grant: tool:pytest"):
        select_capabilities(inventory, _request(_wanted("tool", "pytest")))


def test_select_refuses_a_grant_that_expired_a_minute_ago() -> None:
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    inventory = _inventory(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
            "gate": _admitted_gate(expires_at=past),
        }
    )
    with pytest.raises(CapabilityError, match=r"expired grant: tool:pytest"):
        select_capabilities(inventory, _request(_wanted("tool", "pytest")))


def test_select_keeps_a_grant_that_expires_in_a_minute() -> None:
    soon = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
    inventory = _inventory(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
            "gate": _admitted_gate(expires_at=soon),
        }
    )
    result = select_capabilities(inventory, _request(_wanted("tool", "pytest")))
    assert [item["name"] for item in result["capabilities"]] == ["pytest"]


def test_select_refuses_an_expired_grant_with_a_non_utc_offset() -> None:
    # 2000-01-01 23:00 at +14h is 09:00 UTC the same day — long past.
    inventory = _inventory(
        {
            "kind": "tool",
            "name": "pytest",
            "available": True,
            "provenance": ["probe:tool:pytest"],
            "gate": _admitted_gate(expires_at="2000-01-01T23:00:00+14:00"),
        }
    )
    with pytest.raises(CapabilityError, match=r"expired grant: tool:pytest"):
        select_capabilities(inventory, _request(_wanted("tool", "pytest")))


def test_malformed_inventory_row_names_its_index() -> None:
    inventory = _inventory(
        _available("tool", "pytest"),
        {
            "kind": "tool",
            "name": "ruff",
            "available": "yes",
            "provenance": ["probe:tool:ruff"],
        },
    )
    with pytest.raises(CapabilityError, match=r"inventory allowlist\[1\]"):
        select_capabilities(inventory, _request())


def test_malformed_gate_on_a_row_names_its_index() -> None:
    inventory = _inventory(
        _available("tool", "pytest"),
        {
            "kind": "tool",
            "name": "ruff",
            "available": True,
            "provenance": ["probe:tool:ruff"],
            "gate": {"state": "gated"},
        },
    )
    with pytest.raises(CapabilityError, match=r"inventory allowlist\[1\]"):
        select_capabilities(inventory, _request())

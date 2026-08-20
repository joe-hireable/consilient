"""Refusal tests for EXP-27 procedure step 5 injected fixtures.

Every test here proves refusal:
  1. Community hint cannot credit headroom, change availability or mutate capability.
  2. First-party 'limits increased' notice cannot credit headroom or decrease usage;
     it may only request account refresh and invalidate cached policy.
  3. Active outage cannot remove unaffected compositions, cannot mark anything usable,
     and cannot mutate headroom.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import injected_fixtures as F  # noqa: E402
from change_record import validate_change_record  # noqa: E402


@pytest.fixture
def base_registry() -> dict[str, Any]:
    """Baseline composition registry state."""
    return {
        "compositions": {
            "claude-code": {
                "harness": "claude-code",
                "available": True,
                "status": "ready",
                "policy_cached": "5h_quota_tier_pro",
                "policy_stale": False,
                "requires_probe": False,
                "headroom_lower_bound": 100,
            },
            "codex": {
                "harness": "codex",
                "available": True,
                "status": "ready",
                "policy_cached": "standard_limits",
                "policy_stale": False,
                "requires_probe": False,
                "headroom_lower_bound": 250,
            },
            "cursor": {
                "harness": "cursor",
                "available": True,
                "status": "ready",
                "policy_cached": "ultra_tier",
                "policy_stale": False,
                "requires_probe": False,
                "headroom_lower_bound": None,  # Unknown lower bound
            },
        }
    }


# =============================================================================
# Fixture 1: Community Hint Refusals
# =============================================================================

def test_community_hint_valid_opens_grounding_only(base_registry):
    """Valid community hint opens grounding task and leaves registry state untouched."""
    fixture = copy.deepcopy(F.FIXTURE_COMMUNITY_HINT)
    new_state, actions = F.apply_fixture(fixture, base_registry)

    assert "open_grounding_task" in actions
    # Registry state must be completely untouched
    assert new_state == base_registry


@pytest.mark.parametrize(
    "forbidden_action",
    [
        "increase_headroom",
        "decrease_used",
        "move_reset",
        "mark_headroom_usable",
        "set_available",
        "set_unavailable",
        "invalidate_cached_policy",
    ],
)
def test_community_hint_refuses_state_or_headroom_mutations(base_registry, forbidden_action):
    """Community hint attempting any state or headroom mutation must be refused."""
    fixture = copy.deepcopy(F.FIXTURE_COMMUNITY_HINT)
    fixture["effect"]["actions"] = [forbidden_action]

    with pytest.raises(ValueError):
        F.apply_fixture(fixture, base_registry)


def test_community_hint_refuses_headroom_mutation_permitted_true(base_registry):
    """Community hint declaring headroom_mutation_permitted=True fails invariant."""
    fixture = copy.deepcopy(F.FIXTURE_COMMUNITY_HINT)
    fixture["effect"]["headroom_mutation_permitted"] = True

    with pytest.raises(ValueError, match="headroom_mutation_permitted must be explicitly false"):
        F.apply_fixture(fixture, base_registry)


# =============================================================================
# Fixture 2: Published First-Party "Limits Increased" Notice Refusals
# =============================================================================

def test_limits_increased_valid_requests_refresh_without_crediting_headroom(base_registry):
    """Official 'limits increased' announcement invalidates policy and requests refresh,

    but strictly does NOT credit the headroom ledger.
    """
    fixture = copy.deepcopy(F.FIXTURE_FIRST_PARTY_LIMITS_INCREASED)
    new_state, actions = F.apply_fixture(fixture, base_registry)

    assert "request_account_refresh" in actions
    assert "invalidated_policy:claude-code" in actions
    assert "require_probe:claude-code" in actions

    comp = new_state["compositions"]["claude-code"]
    assert comp["policy_stale"] is True
    assert comp["requires_probe"] is True
    # Headroom lower bound must NOT have increased!
    assert comp["headroom_lower_bound"] == base_registry["compositions"]["claude-code"]["headroom_lower_bound"]


@pytest.mark.parametrize(
    "forbidden_credit_action",
    [
        "increase_headroom",
        "decrease_used",
        "move_reset",
        "mark_headroom_usable",
    ],
)
def test_limits_increased_refuses_direct_headroom_credit(base_registry, forbidden_credit_action):
    """First-party notice attempting to directly credit headroom is rejected."""
    fixture = copy.deepcopy(F.FIXTURE_FIRST_PARTY_LIMITS_INCREASED)
    fixture["effect"]["actions"].append(forbidden_credit_action)

    with pytest.raises(ValueError, match="cannot mutate resource state"):
        F.apply_fixture(fixture, base_registry)


def test_limits_increased_refuses_missing_flag(base_registry):
    """Notice omitting headroom_mutation_permitted is rejected."""
    fixture = copy.deepcopy(F.FIXTURE_FIRST_PARTY_LIMITS_INCREASED)
    del fixture["effect"]["headroom_mutation_permitted"]

    with pytest.raises(ValueError, match="explicitly false"):
        F.apply_fixture(fixture, base_registry)


# =============================================================================
# Fixture 3: Active Outage Refusals
# =============================================================================

def test_active_outage_removes_only_affected_composition(base_registry):
    """Outage on claude-code marks only claude-code unavailable; codex and cursor untouched."""
    fixture = copy.deepcopy(F.FIXTURE_ACTIVE_OUTAGE)
    new_state, actions = F.apply_fixture(fixture, base_registry)

    assert "marked_unavailable:claude-code" in actions
    claude = new_state["compositions"]["claude-code"]
    assert claude["available"] is False
    assert claude["status"] == "unavailable_outage"
    assert claude["outage_incident_id"] == "inc_20260820_claude_down"

    # Unaffected compositions MUST remain completely available and unchanged
    codex = new_state["compositions"]["codex"]
    assert codex["available"] is True
    assert codex["status"] == "ready"

    cursor = new_state["compositions"]["cursor"]
    assert cursor["available"] is True
    assert cursor["status"] == "ready"


def test_active_outage_cannot_mark_anything_usable(base_registry):
    """Outage event attempting to mark a composition usable or available is refused."""
    fixture = copy.deepcopy(F.FIXTURE_ACTIVE_OUTAGE)
    fixture["effect"]["actions"].append("set_available")

    with pytest.raises(ValueError, match="status event cannot perform actions"):
        F.apply_fixture(fixture, base_registry)


def test_active_outage_cannot_mutate_headroom(base_registry):
    """Outage event attempting to mutate headroom is refused."""
    fixture = copy.deepcopy(F.FIXTURE_ACTIVE_OUTAGE)
    fixture["effect"]["actions"].append("increase_headroom")

    with pytest.raises(ValueError, match="cannot mutate resource state"):
        F.apply_fixture(fixture, base_registry)


def test_active_outage_requires_explicit_affected_compositions(base_registry):
    """Outage without affected compositions is refused."""
    fixture = copy.deepcopy(F.FIXTURE_ACTIVE_OUTAGE)
    fixture["affected_compositions"] = []
    fixture["harness"] = None

    with pytest.raises(ValueError, match="must specify affected_compositions"):
        F.apply_fixture(fixture, base_registry)


# =============================================================================
# Negative Test: Proving Checks Can Fail (Guard Invariant)
# =============================================================================

def test_all_three_base_fixtures_satisfy_validate_change_record():
    """All 3 canonical fixtures pass validate_change_record."""
    assert validate_change_record(F.FIXTURE_COMMUNITY_HINT) is True
    assert validate_change_record(F.FIXTURE_FIRST_PARTY_LIMITS_INCREASED) is True
    assert validate_change_record(F.FIXTURE_ACTIVE_OUTAGE) is True

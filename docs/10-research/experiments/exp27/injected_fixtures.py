"""EXP-27 procedure step 5: Three injected fixtures and refusal guards.

Decides ADR-0029 / ADR-0026:
  1. Community hint: unofficial report that limits changed. Must not credit resource state;
     may only request grounding.
  2. Published 'limits increased' notice: first-party announcement that headroom went up.
     Forbidden from crediting (only authenticated account read may increase headroom);
     must request an account refresh instead.
  3. Active outage: may remove an explicitly affected composition, and ONLY that one.
     Cannot remove an unaffected composition, and cannot mark anything usable.

All fixtures enforce:
  - headroom_mutation_permitted=False
  - strict refusal of forbidden resource effects
  - negative-authority invariants
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from change_record import FORBIDDEN_RESOURCE_EFFECTS, validate_change_record  # noqa: E402

COMMUNITY_HINT_ALLOWED_ACTIONS = {
    "request_grounding_task",
    "open_grounding_task",
}

FIRST_PARTY_ALLOWED_ACTIONS = {
    "invalidate_cached_capability",
    "invalidate_cached_policy",
    "request_account_refresh",
    "require_probe",
    "notify_operator",
}

STATUS_OUTAGE_ALLOWED_ACTIONS = {
    "set_unavailable",
    "require_probe",
    "notify_operator",
}


# Fixture 1: Unofficial community report
FIXTURE_COMMUNITY_HINT: dict[str, Any] = {
    "id": "fixture_exp27_community_hint_01",
    "source_kind": "community_hint",
    "source_url": "https://discord.com/channels/123/456/789",
    "harness": "claude-code",
    "title": "Community hint: Claude Code 5-hour limit reportedly doubled for subscribers",
    "published_at": "2026-08-20T10:00:00Z",
    "content_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "effect": {
        "actions": ["request_grounding_task"],
        "headroom_mutation_permitted": False,
    },
}

# Fixture 2: Published first-party "limits increased" announcement
FIXTURE_FIRST_PARTY_LIMITS_INCREASED: dict[str, Any] = {
    "id": "fixture_exp27_limits_increased_01",
    "source_kind": "first_party_changelog",
    "source_url": "https://raw.githubusercontent.com/anthropics/claude-code/refs/heads/main/feed.xml",
    "harness": "claude-code",
    "title": "Official Release: Claude Opus 5-hour rate limits increased by 50%",
    "published_at": "2026-08-20T10:15:00Z",
    "content_sha256": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
    "effect": {
        "actions": [
            "invalidate_cached_policy",
            "request_account_refresh",
            "require_probe",
        ],
        "headroom_mutation_permitted": False,
    },
}

# Fixture 3: First-party status incident / active outage
FIXTURE_ACTIVE_OUTAGE: dict[str, Any] = {
    "id": "fixture_exp27_active_outage_01",
    "source_kind": "first_party_status",
    "source_url": "https://status.claude.com/api/v2/summary.json",
    "harness": "claude-code",
    "affected_compositions": ["claude-code"],
    "title": "Major Outage: Claude API and Claude Code execution degraded",
    "incident_id": "inc_20260820_claude_down",
    "status": "major_outage",
    "published_at": "2026-08-20T10:30:00Z",
    "effect": {
        "actions": ["set_unavailable", "require_probe"],
        "headroom_mutation_permitted": False,
    },
}


def apply_fixture(
    fixture: dict[str, Any],
    registry_state: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Process an injected change event against composition registry state.

    Asserts refusal for any forbidden action:
      - Community hints cannot alter runtime capability, availability, or headroom.
      - First-party limit notices cannot credit headroom (must request account refresh).
      - Active outages may only remove explicitly affected compositions and cannot
        mark anything usable.
    """
    validate_change_record(fixture)

    effect = fixture.get("effect") or {}
    actions = set(effect.get("actions") or [])
    source_kind = fixture.get("source_kind")

    # Invariant Check 1: No change intelligence event may mutate headroom
    forbidden = actions & FORBIDDEN_RESOURCE_EFFECTS
    if forbidden:
        raise ValueError(
            f"change event from {source_kind} cannot mutate resource state: "
            + ", ".join(sorted(forbidden))
        )

    updated_state = copy.deepcopy(registry_state)
    emitted_actions: list[str] = []

    # Rule 1: Community hint
    if source_kind == "community_hint":
        disallowed = actions - COMMUNITY_HINT_ALLOWED_ACTIONS
        if disallowed:
            raise ValueError(
                f"community hint has no state-transition authority; forbidden actions: "
                + ", ".join(sorted(disallowed))
            )
        emitted_actions.append("open_grounding_task")
        return updated_state, emitted_actions

    # Rule 2: First-party changelog / announcement
    elif source_kind in ("first_party_changelog", "first_party_release"):
        disallowed = actions - FIRST_PARTY_ALLOWED_ACTIONS
        if disallowed:
            raise ValueError(
                f"first-party release note cannot directly perform actions: "
                + ", ".join(sorted(disallowed))
            )

        target_harness = fixture.get("harness")
        if target_harness and target_harness in updated_state.get("compositions", {}):
            comp = updated_state["compositions"][target_harness]
            if "invalidate_cached_policy" in actions:
                comp["policy_cached"] = None
                comp["policy_stale"] = True
                emitted_actions.append(f"invalidated_policy:{target_harness}")
            if "require_probe" in actions:
                comp["requires_probe"] = True
                emitted_actions.append(f"require_probe:{target_harness}")

        if "request_account_refresh" in actions:
            emitted_actions.append("request_account_refresh")

        return updated_state, emitted_actions

    # Rule 3: Active outage on status feed
    elif source_kind == "first_party_status":
        disallowed = actions - STATUS_OUTAGE_ALLOWED_ACTIONS
        if disallowed:
            raise ValueError(
                f"status event cannot perform actions: " + ", ".join(sorted(disallowed))
            )

        affected = fixture.get("affected_compositions") or ([fixture.get("harness")] if fixture.get("harness") else [])
        if not affected:
            raise ValueError("status outage event must specify affected_compositions")

        compositions = updated_state.get("compositions", {})

        # Verify that outage only targets explicitly affected compositions
        for comp_name, comp_info in compositions.items():
            if comp_name in affected:
                if "set_unavailable" in actions:
                    comp_info["available"] = False
                    comp_info["status"] = "unavailable_outage"
                    comp_info["outage_incident_id"] = fixture.get("incident_id")
                    emitted_actions.append(f"marked_unavailable:{comp_name}")
                if "require_probe" in actions:
                    comp_info["requires_probe"] = True
            else:
                # An outage cannot alter state of unaffected compositions
                # (asserted invariant)
                pass

        return updated_state, emitted_actions

    else:
        raise ValueError(f"unrecognised source_kind '{source_kind}'")

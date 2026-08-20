"""Tests for EXP-27 procedure step 4: version/capability handshake.

Verifies:
  - Zero-inference probes against installed harnesses (Claude Code, Codex, Cursor).
  - Fail-closed capability validation (unobservable capability cannot be marked usable).
  - Refusal to mutate resource ledger (ADR-0029 invariant on every record).
  - Admission gating per ADR-0026 and ADR-0029:
      - Cursor excluded from unbounded unattended work due to unknown headroom lower bound.
      - Cursor admitted for bounded supervised work under recorded user attestation.
      - Missing or unauthenticated harnesses rejected.
  - Diff detection for version bumps, capability shifts and admission state changes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import handshake as H  # noqa: E402
from change_record import validate_change_record  # noqa: E402


def test_handshake_record_asserts_no_headroom_mutation():
    """Every emitted handshake record must declare headroom_mutation_permitted=False."""
    record = H.run_handshake("claude-code")
    assert validate_change_record(record) is True
    assert record["effect"]["headroom_mutation_permitted"] is False


def test_handshake_rejects_forbidden_resource_effects():
    """Handshake records claiming resource mutation must fail validate_change_record."""
    record = H.run_handshake("codex")
    record["effect"]["actions"].append("increase_headroom")
    with pytest.raises(ValueError, match="cannot mutate resource state"):
        validate_change_record(record)


def test_unobservable_capability_cannot_be_marked_usable_fails_closed():
    """Unobservable or unknown capability marked usable must raise ValueError."""
    # Defective record: capability is unobservable but claims usable=True
    bad_record = {
        "capabilities": {
            "rate_limit_dashboard": {
                "status": "unobservable",
                "usable": True,
            }
        }
    }
    with pytest.raises(ValueError, match="unobservable capability 'rate_limit_dashboard' cannot be marked usable"):
        H.validate_capability_record(bad_record)


def test_unknown_capability_prefix_fails_closed():
    """Unknown capability flag must not be admitted as usable."""
    bad_record = {
        "capabilities": {
            "unknown_feature_flag": True,
        }
    }
    with pytest.raises(ValueError, match="unknown capability 'unknown_feature_flag' cannot be marked usable"):
        H.validate_capability_record(bad_record)


def test_valid_capabilities_pass_validation():
    """Observable supported capabilities pass validation."""
    valid_record = {
        "capabilities": {
            "json_stream": {"status": "supported", "usable": True},
            "missing_surface": {"status": "unobservable", "usable": False},
        }
    }
    assert H.validate_capability_record(valid_record) is True


def test_probe_claude_code_live():
    """Live probe of Claude Code on this machine."""
    res = H.probe_claude_code()
    assert res["harness"] == "claude-code"
    assert res["installed"] is True
    assert res["version"] is not None
    assert "2.1." in res["version"]
    assert res["capabilities"]["headless_print"]["usable"] is True
    assert res["capabilities"]["sandbox_bypass"]["usable"] is True


def test_probe_codex_live():
    """Live probe of Codex on this machine."""
    res = H.probe_codex()
    assert res["harness"] == "codex"
    assert res["installed"] is True
    assert res["version"] is not None
    assert res["version"] == "0.148.0"
    assert res["capabilities"]["headless_exec"]["usable"] is True
    assert res["capabilities"]["json_stream"]["usable"] is True
    assert res["capabilities"]["sandbox_bypass"]["usable"] is True


def test_probe_cursor_live():
    """Live probe of Cursor on this machine via WSL binary."""
    res = H.probe_cursor()
    assert res["harness"] == "cursor"
    assert res["installed"] is True
    assert res["version"] is not None
    assert res["subscription_tier"] == "Ultra"
    assert res["is_authenticated"] is True
    assert res["configured_model"] == "Gemini 3.7 Flash High"
    assert res["available_models_count"] > 100
    # Crucial ADR-0026 finding: individual headroom is unobservable
    assert res["capabilities"]["remaining_allowance_surface"]["status"] == "unobservable"
    assert res["capabilities"]["remaining_allowance_surface"]["usable"] is False


def test_admission_cursor_unbounded_unattended_excluded():
    """Cursor without headroom counter is excluded from unbounded unattended routing."""
    probe_res = H.probe_cursor()
    admission = H.evaluate_admission(
        "cursor",
        probe_res,
        context={"mode": "unattended_unbounded"},
    )
    assert admission["admitted"] is False
    assert admission["admission_state"] == "excluded_unknown_headroom"
    assert admission["usable_for_unattended"] is False


def test_admission_cursor_bounded_supervised_admitted():
    """Cursor is admitted for bounded supervised work with recorded user attestation."""
    probe_res = H.probe_cursor()
    admission = H.evaluate_admission(
        "cursor",
        probe_res,
        context={
            "mode": "bounded_supervised",
            "user_headroom_attestation": "Joe Brown 2026-08-20: Ultra tier verified active",
        },
    )
    assert admission["admitted"] is True
    assert admission["admission_state"] == "admitted_bounded_supervised"
    assert admission["usable_for_unattended"] is False


def test_admission_missing_or_uninstalled_harness_fails_closed():
    """Uninstalled or failed probe fails closed to rejected."""
    fake_probe: dict[str, Any] = {
        "harness": "unknown-agent",
        "installed": False,
        "version": None,
        "capabilities": {},
    }
    admission = H.evaluate_admission("unknown-agent", fake_probe)
    assert admission["admitted"] is False
    assert admission["admission_state"] == "rejected_uninstalled_or_unobservable"


def test_admission_unauthenticated_cursor_fails_closed():
    """Cursor with isAuthenticated=False fails closed."""
    fake_cursor_probe: dict[str, Any] = {
        "harness": "cursor",
        "installed": True,
        "version": "2026.08.11",
        "is_authenticated": False,
        "subscription_tier": "Ultra",
        "capabilities": {},
    }
    admission = H.evaluate_admission(
        "cursor",
        fake_cursor_probe,
        context={"mode": "bounded_supervised", "user_headroom_attestation": "attested"},
    )
    assert admission["admitted"] is False
    assert admission["admission_state"] == "rejected_unauthenticated"


def test_diff_handshake_detects_version_bump():
    """Handshake diff accurately notices an installed version change."""
    prior = {
        "version": "2.1.236",
        "admitted": True,
        "capabilities": {"headless_print": {"status": "supported", "usable": True}},
    }
    current_probe: dict[str, Any] = {
        "version": "2.1.237",
        "capabilities": {"headless_print": {"status": "supported", "usable": True}},
    }
    current_admission: dict[str, Any] = {"admitted": True}

    diff = H.diff_handshake(prior, current_probe, current_admission)
    assert diff["version_changed"] is True
    assert diff["admission_changed"] is False
    assert any("version_changed" in d for d in diff["details"])


def test_diff_handshake_detects_admission_change():
    """Handshake diff notices when admission state changes."""
    prior = {
        "version": "2026.08.11",
        "admitted": False,
        "capabilities": {},
    }
    current_probe: dict[str, Any] = {
        "version": "2026.08.11",
        "capabilities": {},
    }
    current_admission: dict[str, Any] = {"admitted": True}

    diff = H.diff_handshake(prior, current_probe, current_admission)
    assert diff["version_changed"] is False
    assert diff["admission_changed"] is True
    assert any("admission_changed" in d for d in diff["details"])


def test_to_wsl_path():
    """Path translation converts Windows absolute path to WSL path."""
    assert H.to_wsl_path("C:\\Users\\jpbpr\\repo") == "/mnt/c/Users/jpbpr/repo"
    assert H.to_wsl_path("/mnt/c/Users/jpbpr/repo") == "/mnt/c/Users/jpbpr/repo"


def test_run_all_handshakes_live():
    """End-to-end execution across all three harnesses."""
    suite = H.run_all_handshakes()
    assert "handshakes" in suite
    assert set(suite["handshakes"].keys()) == {"claude-code", "codex", "cursor"}
    assert validate_change_record(suite) is True
    for harness, h_record in suite["handshakes"].items():
        assert h_record["harness"] == harness
        assert h_record["probe"]["installed"] is True
        assert h_record["probe"]["version"] is not None
        assert validate_change_record(h_record) is True

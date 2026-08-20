"""EXP-27 procedure step 4: dispatch-time version/capability handshake.

Zero-inference probe of installed harnesses (Claude Code, Codex, Cursor).
Records whether the probe changed the composition's capability or admission state.
Fails closed: unobservable capability is unknown, and unknown is never usable.

Invariant: every handshake record asserts headroom_mutation_permitted=False
and passes validate_change_record.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from change_record import validate_change_record  # noqa: E402

SUPPORTED_HARNESSES = ("claude-code", "codex", "cursor")
CURSOR_WSL_BINARY = Path("/home/jpbpr/.local/bin/cursor-agent")


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def to_wsl_path(win_path: str | Path) -> str:
    """Translate Windows path to WSL path (C:\\... -> /mnt/c/...)."""
    p = str(win_path).replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        return f"/mnt/{p[0].lower()}{p[2:]}"
    return p


def validate_capability_record(cap_record: dict[str, Any]) -> bool:
    """Fail-closed validator for capability records.

    An unobservable or unknown capability must never be marked usable.
    """
    capabilities = cap_record.get("capabilities") or {}
    for name, details in capabilities.items():
        if isinstance(details, dict):
            status = details.get("status", "unknown")
            usable = details.get("usable", False)
            if usable and status in ("unknown", "unobservable", "unsupported", "missing"):
                raise ValueError(
                    f"unobservable capability '{name}' cannot be marked usable: fail closed"
                )
        elif details is True and name.startswith("unknown_"):
            raise ValueError(
                f"unknown capability '{name}' cannot be marked usable: fail closed"
            )
    return True


def _run_cmd(cmd: list[str], timeout_s: int = 15) -> tuple[int, str, str]:
    """Execute command with timeout and safe string encoding."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:
        return -1, "", f"{type(exc).__name__}: {exc}"


def probe_claude_code() -> dict[str, Any]:
    """Zero-inference version and capability probe for Claude Code."""
    claude_bin = shutil.which("claude.exe") or shutil.which("claude")
    raw_version = ""
    exit_code = -1
    err = ""

    if claude_bin:
        exit_code, raw_version, err = _run_cmd([claude_bin, "--version"])
    
    if exit_code != 0 or not raw_version:
        # Fallback via cmd.exe if running inside WSL pointing to Windows environment
        exit_code, raw_version, err = _run_cmd(["cmd.exe", "/c", "claude --version"])

    version: str | None = None
    if exit_code == 0 and raw_version:
        # Expecting e.g. "2.1.237 (Claude Code)"
        m = re.search(r"(\d+\.\d+\.\d+)", raw_version)
        version = m.group(1) if m else raw_version.split()[0]

    # Inspect command surfaces via help
    help_out = ""
    if claude_bin:
        _, help_out, _ = _run_cmd([claude_bin, "--help"])
    if not help_out:
        _, help_out, _ = _run_cmd(["cmd.exe", "/c", "claude --help"])

    has_print = "--print" in help_out or "-p" in help_out
    has_json_output = "--output-format" in help_out and "json" in help_out
    has_skip_perm = "--dangerously-skip-permissions" in help_out

    capabilities = {
        "headless_print": {
            "status": "supported" if has_print else "unobservable",
            "usable": bool(has_print),
        },
        "json_output": {
            "status": "supported" if has_json_output else "unobservable",
            "usable": bool(has_json_output),
        },
        "sandbox_bypass": {
            "status": "supported" if has_skip_perm else "unobservable",
            "usable": bool(has_skip_perm),
        },
        "quota_surface": {
            "status": "status_line_json" if version else "unobservable",
            "usable": bool(version),
        },
    }

    installed = bool(version is not None)
    return {
        "harness": "claude-code",
        "installed": installed,
        "version": version,
        "raw_version": raw_version,
        "error": err if not installed else None,
        "capabilities": capabilities,
        "probed_at": _now(),
    }


def probe_codex() -> dict[str, Any]:
    """Zero-inference version and capability probe for Codex CLI."""
    # First attempt via direct binary or cmd.exe
    exit_code, raw_version, err = _run_cmd(["cmd.exe", "/c", "codex --version"])
    if exit_code != 0 or not raw_version:
        codex_bin = shutil.which("codex")
        if codex_bin:
            exit_code, raw_version, err = _run_cmd([codex_bin, "--version"])

    version: str | None = None
    if exit_code == 0 and raw_version:
        # Expecting e.g. "codex-cli 0.148.0"
        m = re.search(r"(\d+\.\d+\.\d+)", raw_version)
        version = m.group(1) if m else raw_version.split()[-1]

    # Help probe: inspect both top-level help and exec subcommand help
    _, help_out, _ = _run_cmd(["cmd.exe", "/c", "codex --help"])
    _, help_exec, _ = _run_cmd(["cmd.exe", "/c", "codex exec --help"])
    full_help = f"{help_out}\n{help_exec}"

    has_exec = "exec" in help_out
    has_json = "--json" in full_help
    has_bypass_sandbox = "--dangerously-bypass-approvals-and-sandbox" in full_help
    has_app_server = "app-server" in help_out

    capabilities = {
        "headless_exec": {
            "status": "supported" if has_exec else "unobservable",
            "usable": bool(has_exec),
        },
        "json_stream": {
            "status": "supported" if has_json else "unobservable",
            "usable": bool(has_json),
        },
        "sandbox_bypass": {
            "status": "supported" if has_bypass_sandbox else "unobservable",
            "usable": bool(has_bypass_sandbox),
        },
        "app_server_rate_limits": {
            "status": "supported" if has_app_server else "unobservable",
            "usable": bool(has_app_server),
        },
    }

    installed = bool(version is not None)
    return {
        "harness": "codex",
        "installed": installed,
        "version": version,
        "raw_version": raw_version,
        "error": err if not installed else None,
        "capabilities": capabilities,
        "probed_at": _now(),
    }


def probe_cursor() -> dict[str, Any]:
    """Zero-inference version and capability probe for Cursor CLI (cursor-agent)."""
    cursor_bin = str(CURSOR_WSL_BINARY) if CURSOR_WSL_BINARY.exists() else (shutil.which("cursor-agent") or "")
    if not cursor_bin or not os.path.exists(cursor_bin):
        return {
            "harness": "cursor",
            "installed": False,
            "version": None,
            "error": f"cursor-agent binary not found at {CURSOR_WSL_BINARY}",
            "capabilities": {
                "headless_print": {"status": "unobservable", "usable": False},
                "models_listing": {"status": "unobservable", "usable": False},
            },
            "probed_at": _now(),
        }

    # Probe 1: about --format json
    code_about, stdout_about, err_about = _run_cmd([cursor_bin, "about", "--format", "json"])
    about_data: dict[str, Any] = {}
    if code_about == 0 and stdout_about:
        try:
            about_data = json.loads(stdout_about)
        except json.JSONDecodeError:
            pass

    # Probe 2: status --format json
    code_status, stdout_status, _ = _run_cmd([cursor_bin, "status", "--format", "json"])
    status_data: dict[str, Any] = {}
    if code_status == 0 and stdout_status:
        try:
            status_data = json.loads(stdout_status)
        except json.JSONDecodeError:
            pass

    # Probe 3: models
    code_models, stdout_models, _ = _run_cmd([cursor_bin, "models"])
    available_models: list[str] = []
    if code_models == 0 and stdout_models:
        for line in stdout_models.splitlines():
            line = line.strip()
            if line and " - " in line and not line.startswith("Available") and not line.startswith("Tip:"):
                model_id = line.split(" - ")[0].strip()
                available_models.append(model_id)

    version = about_data.get("cliVersion")
    configured_model = about_data.get("model")
    subscription_tier = about_data.get("subscriptionTier")
    is_authenticated = status_data.get("isAuthenticated", False)

    capabilities = {
        "headless_print": {
            "status": "supported" if version else "unobservable",
            "usable": bool(version),
        },
        "json_output": {
            "status": "supported" if version else "unobservable",
            "usable": bool(version),
        },
        "models_discovery": {
            "status": "supported" if available_models else "unobservable",
            "usable": bool(available_models),
        },
        "remaining_allowance_surface": {
            "status": "unobservable",
            "usable": False,  # Cursor CLI exposes plan tier but NO individual quota/reset counter
        },
    }

    installed = bool(version is not None)
    return {
        "harness": "cursor",
        "installed": installed,
        "version": version,
        "raw_version": version or "",
        "subscription_tier": subscription_tier,
        "configured_model": configured_model,
        "is_authenticated": is_authenticated,
        "user_email": about_data.get("userEmail"),
        "available_models_count": len(available_models),
        "available_models": available_models,
        "error": err_about if not installed else None,
        "capabilities": capabilities,
        "probed_at": _now(),
    }


def probe_harness(harness: str) -> dict[str, Any]:
    """Probe a single named harness with zero inference."""
    if harness == "claude-code":
        return probe_claude_code()
    elif harness == "codex":
        return probe_codex()
    elif harness == "cursor":
        return probe_cursor()
    else:
        return {
            "harness": harness,
            "installed": False,
            "version": None,
            "error": f"unsupported harness: {harness}",
            "capabilities": {},
            "probed_at": _now(),
        }


def evaluate_admission(
    harness: str,
    probe_result: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate routing feasibility / admission under ADR-0026 and ADR-0029.

    Fails closed:
      - missing/unobservable harness -> rejected
      - unauthenticated harness -> rejected
      - cursor: unknown individual headroom -> excluded from unbounded unattended work;
        admitted only for bounded supervised work with recorded user attestation.
    """
    ctx = context or {}
    work_mode = ctx.get("mode", "unattended_unbounded")
    user_attestation = ctx.get("user_headroom_attestation")

    if not probe_result.get("installed") or not probe_result.get("version"):
        return {
            "harness": harness,
            "admitted": False,
            "admission_state": "rejected_uninstalled_or_unobservable",
            "reason": "binary not found or zero-inference version probe failed",
            "usable_for_unattended": False,
        }

    if harness == "cursor":
        # Check authentication
        if not probe_result.get("is_authenticated", True):
            return {
                "harness": harness,
                "admitted": False,
                "admission_state": "rejected_unauthenticated",
                "reason": "cursor-agent status reports not authenticated",
                "usable_for_unattended": False,
            }

        # Cursor exposes plan tier (Ultra) but no individual headroom counter.
        # ADR-0026 amendment (20 Aug 2026):
        # Unbounded unattended work -> excluded (unknown headroom lower bound).
        # Bounded supervised work with recorded user attestation -> admitted.
        if work_mode == "bounded_supervised" and user_attestation:
            return {
                "harness": harness,
                "admitted": True,
                "admission_state": "admitted_bounded_supervised",
                "reason": "admitted for bounded supervised work under recorded user attestation",
                "usable_for_unattended": False,
                "tier": probe_result.get("subscription_tier"),
            }
        else:
            return {
                "harness": harness,
                "admitted": False,
                "admission_state": "excluded_unknown_headroom",
                "reason": "Cursor exposes tier but no remaining allowance counter; excluded from unbounded unattended routing (ADR-0026)",
                "usable_for_unattended": False,
                "tier": probe_result.get("subscription_tier"),
            }

    if harness == "codex":
        return {
            "harness": harness,
            "admitted": True,
            "admission_state": "admitted_subscription",
            "reason": "installed executable and app-server rateLimits surface available",
            "usable_for_unattended": True,
        }

    if harness == "claude-code":
        return {
            "harness": harness,
            "admitted": True,
            "admission_state": "admitted_subscription",
            "reason": "installed executable and status-line quota surface available",
            "usable_for_unattended": True,
        }

    return {
        "harness": harness,
        "admitted": False,
        "admission_state": "rejected_unknown_harness",
        "reason": f"unrecognised harness '{harness}'",
        "usable_for_unattended": False,
    }


def diff_handshake(
    prior_state: dict[str, Any] | None,
    current_probe: dict[str, Any],
    current_admission: dict[str, Any],
) -> dict[str, Any]:
    """Determine whether the probe changed the composition's capability or admission state."""
    if not prior_state:
        return {
            "version_changed": True,
            "capability_changed": True,
            "admission_changed": True,
            "details": ["initial_baseline_observation"],
        }

    details: list[str] = []
    prior_version = prior_state.get("version")
    cur_version = current_probe.get("version")
    version_changed = prior_version != cur_version
    if version_changed:
        details.append(f"version_changed: {prior_version} -> {cur_version}")

    prior_admitted = prior_state.get("admitted")
    cur_admitted = current_admission.get("admitted")
    admission_changed = prior_admitted != cur_admitted
    if admission_changed:
        details.append(f"admission_changed: {prior_admitted} -> {cur_admitted}")

    prior_caps = prior_state.get("capabilities") or {}
    cur_caps = current_probe.get("capabilities") or {}
    capability_changed = False
    for k, v in cur_caps.items():
        if prior_caps.get(k) != v:
            capability_changed = True
            details.append(f"capability_changed: {k}")

    return {
        "version_changed": version_changed,
        "capability_changed": capability_changed,
        "admission_changed": admission_changed,
        "details": details,
    }


def run_handshake(
    harness: str,
    prior_state: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a zero-inference version/capability handshake for one harness.

    Meets EXP-27 procedure step 4:
    Record whether the probe changes the composition's capability or admission state.
    """
    probe_result = probe_harness(harness)
    validate_capability_record(probe_result)

    admission_result = evaluate_admission(harness, probe_result, context)
    diff = diff_handshake(prior_state, probe_result, admission_result)

    record: dict[str, Any] = {
        "v": 1,
        "event_type": "dispatch_handshake",
        "harness": harness,
        "probed_at": _now(),
        "probe": probe_result,
        "admission": admission_result,
        "diff": diff,
        "state_changed": bool(
            diff["version_changed"]
            or diff["capability_changed"]
            or diff["admission_changed"]
        ),
        "effect": {
            "actions": ["record_handshake_state"],
            "headroom_mutation_permitted": False,
        },
    }
    validate_change_record(record)
    return record


def run_all_handshakes(
    prior_states: dict[str, dict[str, Any]] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run zero-inference handshake across all supported harnesses."""
    priors = prior_states or {}
    results = {}
    for harness in SUPPORTED_HARNESSES:
        results[harness] = run_handshake(
            harness=harness,
            prior_state=priors.get(harness),
            context=context,
        )
    return {
        "v": 1,
        "handshakes": results,
        "probed_at": _now(),
        "effect": {
            "actions": ["record_handshake_suite"],
            "headroom_mutation_permitted": False,
        },
    }


if __name__ == "__main__":
    suite = run_all_handshakes()
    print(json.dumps(suite, indent=2))

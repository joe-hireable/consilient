"""Unit tests for Grok Build adapter #7 and dispatch handshake integration."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Add exp05 and exp27 to sys.path for test imports
ROOT = Path(__file__).resolve().parent.parent
EXP05 = ROOT / "docs" / "10-research" / "experiments" / "exp05"
EXP27 = ROOT / "docs" / "10-research" / "experiments" / "exp27"
sys.path.insert(0, str(EXP05))
sys.path.insert(0, str(EXP27))

import adapter_grok as A  # noqa: E402
from run_all import composition_for, grok_auth_ready  # noqa: E402


def test_composition_mapping_grok():
    assert composition_for("grok") == {
        "agent": "grok",
        "domain": "coding",
        "harness": "grok",
        "provider": "xai-subscription",
        "model": "unknown:not-recorded-by-adapter",
    }
    assert composition_for("grok:grok-4.6") == {
        "agent": "grok:grok-4.6",
        "domain": "coding",
        "harness": "grok",
        "provider": "xai-subscription",
        "model": "grok-4.6",
    }


def test_grok_auth_ready_helper():
    assert grok_auth_ready(
        "Default model: grok-4.6\n\nAvailable models:\n  * grok-4.6", 0
    )
    assert not grok_auth_ready(
        "You are not authenticated.\n\nDefault model: grok-4.6", 0
    )
    assert not grok_auth_ready(
        "Not signed in. To authenticate without a browser, run: grok login --device-code",
        0,
    )
    assert not grok_auth_ready("", 1)
    assert not grok_auth_ready(None, 0)


def test_grok_command_structure():
    ticket = {
        "id": "test-1",
        "goal": "Implement feature X",
        "repo_dir": r"C:\Users\Joe\repo",
        "model": "grok-4.6",
        "max_turns": 3,
    }
    cmd = A.grok_command(ticket, grok_bin="grok.exe")
    assert cmd[0] == "grok.exe"
    assert cmd[1] == "-p"
    assert cmd[2] == "Implement feature X"
    assert "--output-format" in cmd and "json" in cmd
    assert "--permission-mode" in cmd and "bypassPermissions" in cmd
    assert "--always-approve" in cmd
    assert "--cwd" in cmd and r"C:\Users\Joe\repo" in cmd
    assert "--model" in cmd and "grok-4.6" in cmd
    assert "--max-turns" in cmd and "3" in cmd


def test_refuse_metered_key():
    # Clean environment: should not raise
    A.refuse_metered_key({"CLEAN_VAR": "ok"})

    # Metered keys: must raise RuntimeError per ADR-0044
    for key_var in ("XAI_API_KEY", "GROK_CODE_XAI_API_KEY", "GROK_API_KEY"):
        env = {key_var: "test-metered-key-value"}
        with pytest.raises(RuntimeError, match="Metered xAI API key detected"):
            A.refuse_metered_key(env)


def test_parse_result_json():
    # Single line JSON
    single = '{"status": "ok", "usage": {"inputTokens": 100, "outputTokens": 20}}'
    res = A.parse_result(single)
    assert res.get("status") == "ok"

    # Multiline with trailing JSON
    multi = "some log line\n" + '{"model": "grok-4.6", "sessionId": "sess-123"}'
    res2 = A.parse_result(multi)
    assert res2.get("model") == "grok-4.6"
    assert res2.get("sessionId") == "sess-123"

    # Empty / non-JSON
    assert A.parse_result("") == {}
    assert A.parse_result("just raw text") == {}


def test_usage_and_identity_fields():
    result = {
        "sessionId": "s-100",
        "requestId": "r-200",
        "usage": {
            "input_tokens": 150,
            "output_tokens": 45,
            "cache": {"read": 80, "write": 10},
        },
    }
    usage = A.usage_fields(result)
    assert usage["tokens_in"] == 150
    assert usage["tokens_out"] == 45
    assert usage["cache_read_tokens"] == 80
    assert usage["cache_write_tokens"] == 10

    identity = A.identity_fields(result)
    assert identity["session_id"] == "s-100"
    assert identity["request_id"] == "r-200"


def test_model_fields_handling():
    # Model reported by runtime
    models = A.model_fields("grok-4.6", {"model": "grok-4.6-preview"})
    assert models["model"] == "grok-4.6-preview"
    assert models["model_requested"] == "grok-4.6"
    assert models["model_selected"] == "grok-4.6-preview"

    # Model not reported by runtime
    models2 = A.model_fields("grok-4.6", {})
    assert models2["model"] == "grok-4.6"
    assert models2["model_requested"] == "grok-4.6"
    assert models2["model_selected"] is None

    # No model specified
    models3 = A.model_fields(None, {})
    assert models3["model"] == "unknown:not-reported-by-runtime"


def test_unauthenticated_detection():
    stdout = "Not signed in. To authenticate without a browser, run:\n  grok login --device-code\n"
    assert A.is_unauthenticated_output(stdout, "") is True
    assert A.is_unauthenticated_output("You are not authenticated.", "") is True
    assert A.is_unauthenticated_output('{"status": "ok"}', "") is False


def test_unauthenticated_run_reports_not_ready():
    """Unauthenticated detection must return status='not_ready', not a failure.

    This asserted against the LIVE machine and was green only because nobody had signed in
    yet. It broke the moment Joe authenticated on 20 Aug 2026 — the same defect as
    `test_doctor_fails_the_unbuilt_weekly_fallback`, which was green only because a file did
    not exist. A test that passes because of the environment's current state is measuring the
    environment.

    Now stubbed: the adapter is shown the exact stdout the CLI emits when signed out, so the
    assertion holds whether or not this machine has a session. It also stops the suite making
    a live model call, which cost 17 seconds and real subscription usage per run.
    """
    from unittest import mock

    # Substitute the command rather than the subprocess module. Patching `subprocess.run`
    # globally intercepts the adapter's other calls too and left the temporary directory
    # locked; swapping the command keeps the real Popen path, the real timeout handling and
    # the real parsing under test, and only replaces what is executed.
    signed_out = "Not signed in. To authenticate without a browser, run:\n  grok login --device-code"
    fake = [sys.executable, "-c", f"print({signed_out!r})"]

    with (
        tempfile.TemporaryDirectory() as tmp_dir,
        mock.patch.object(A, "grok_command", return_value=fake),
    ):
        ticket = {
            "id": "unauth-test",
            "goal": "Verify unauthenticated detection",
            "repo_dir": tmp_dir,
            "timeout_s": 15,
        }
        outcome = A.run(ticket)
        assert outcome["ticket_id"] == "unauth-test"
        assert outcome["agent"] == "grok"
        assert outcome["harness"] == "grok"
        assert outcome["provider"] == "xai-subscription"
        assert outcome["authenticated"] is False
        assert outcome["ok"] is False
        assert outcome["status"] == "not_ready"


def test_refusal_when_metered_key_passed_to_run():
    """Passing a metered key to run() must fail closed before starting subprocess."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ticket = {
            "id": "refusal-test",
            "goal": "Should be refused immediately",
            "repo_dir": tmp_dir,
            "timeout_s": 5,
        }
        env = {"XAI_API_KEY": "forbidden-metered-key"}
        with pytest.raises(RuntimeError, match="Metered xAI API key detected"):
            A.run(ticket, env=env)


def test_timeout_and_process_tree_kill():
    """Verify _kill_process_tree terminates a running subprocess tree."""
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(60)",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    )
    assert proc.poll() is None
    A._kill_process_tree(proc)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    assert proc.poll() is not None

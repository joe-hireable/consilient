"""Regression and safety checks for Grok Build adapter #7."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import adapter_grok as A  # noqa: E402
from run_all import composition_for  # noqa: E402


def test_composition_mapping():
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


def test_grok_command_structure():
    ticket = {
        "id": "test-1",
        "goal": "Edit only util.py",
        "repo_dir": r"C:\Users\Joe\repo",
        "model": "grok-4.6",
        "max_turns": 5,
    }
    cmd = A.grok_command(ticket, grok_bin="grok.exe")
    assert cmd[0] == "grok.exe"
    assert cmd[1] == "-p"
    assert cmd[2] == "Edit only util.py"
    assert "--output-format" in cmd and "json" in cmd
    assert "--permission-mode" in cmd and "bypassPermissions" in cmd
    assert "--always-approve" in cmd
    assert "--cwd" in cmd and r"C:\Users\Joe\repo" in cmd
    assert "--model" in cmd and "grok-4.6" in cmd
    assert "--max-turns" in cmd and "5" in cmd


def test_refuse_metered_key():
    # Clean environment: should not raise
    A.refuse_metered_key({"OTHER_VAR": "val"})

    # Metered keys: must raise RuntimeError per ADR-0044
    for key_var in ("XAI_API_KEY", "GROK_CODE_XAI_API_KEY", "GROK_API_KEY"):
        env = {key_var: "test-metered-key-value"}
        try:
            A.refuse_metered_key(env)
        except RuntimeError as exc:
            assert "Metered xAI API key detected" in str(exc)
            assert key_var in str(exc)
            assert "ADR-0044" in str(exc)
        else:
            raise AssertionError(f"Expected refusal for metered key '{key_var}'")


def test_parse_result():
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


def test_usage_fields():
    result = {
        "usage": {
            "input_tokens": 150,
            "output_tokens": 45,
            "cache": {"read": 80, "write": 10},
        }
    }
    usage = A.usage_fields(result)
    assert usage["tokens_in"] == 150
    assert usage["tokens_out"] == 45
    assert usage["cache_read_tokens"] == 80
    assert usage["cache_write_tokens"] == 10

    # CamelCase variant
    result_camel = {
        "usage": {
            "inputTokens": 200,
            "outputTokens": 50,
            "cacheReadTokens": 90,
            "cacheWriteTokens": 15,
        }
    }
    usage_camel = A.usage_fields(result_camel)
    assert usage_camel["tokens_in"] == 200
    assert usage_camel["tokens_out"] == 50
    assert usage_camel["cache_read_tokens"] == 90
    assert usage_camel["cache_write_tokens"] == 15


def test_identity_fields():
    result = {"sessionId": "s-1", "requestId": "r-1"}
    identity = A.identity_fields(result)
    assert identity["session_id"] == "s-1"
    assert identity["request_id"] == "r-1"


def test_model_fields():
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
    """Live unauthenticated run must detect not signed in and return status='not_ready'."""
    with tempfile.TemporaryDirectory() as tmp_dir:
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
        assert "grok login" in outcome["raw_tail"].lower() or "not signed in" in outcome["raw_tail"].lower()


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
        try:
            A.run(ticket, env=env)
        except RuntimeError as exc:
            assert "Metered xAI API key detected" in str(exc)
        else:
            raise AssertionError("run() must refuse execution when XAI_API_KEY is present")


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


if __name__ == "__main__":
    test_composition_mapping()
    test_grok_command_structure()
    test_refuse_metered_key()
    test_parse_result()
    test_usage_fields()
    test_identity_fields()
    test_model_fields()
    test_unauthenticated_detection()
    test_unauthenticated_run_reports_not_ready()
    test_refusal_when_metered_key_passed_to_run()
    test_timeout_and_process_tree_kill()
    print("All Grok adapter tests pass")

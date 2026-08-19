"""Cursor's ACP control path stays distinct from Cursor-as-MCP-client."""

from adapter_cursor_acp import (
    agent_text,
    is_success_stop_reason,
    parse_acp_outcome,
)
from run_all import composition_for


if __name__ == "__main__":
    # Distinct control observation check
    assert composition_for("cursor-acp") == {
        "agent": "cursor-acp",
        "domain": "coding",
        "harness": "cursor",
        "provider": "cursor-subscription",
        "model": "unknown:not-recorded-by-adapter",
        "control_protocol": "acp-v1-stdio",
    }

    # Transcript extraction check
    messages = [
        {
            "method": "session/update",
            "params": {
                "update": {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"type": "text", "text": "hello"},
                }
            },
        },
        {"method": "cursor/update_todos", "params": {}},
        {
            "method": "session/update",
            "params": {
                "update": {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"type": "text", "text": " world"},
                }
            },
        },
    ]
    assert agent_text(messages) == "hello world"

    # Stop reason validation: fail closed on missing, cancelled, error, unknown
    assert is_success_stop_reason("end_turn")
    assert is_success_stop_reason("stop")
    assert is_success_stop_reason("completed")
    assert is_success_stop_reason("complete")
    assert not is_success_stop_reason(None)
    assert not is_success_stop_reason("")
    assert not is_success_stop_reason("cancelled")
    assert not is_success_stop_reason("error")
    assert not is_success_stop_reason("unknown")
    assert not is_success_stop_reason("aborted")
    assert not is_success_stop_reason("unrecognized_status")

    # Outcome parsing: success case with preserved identity, stopReason and available usage
    session_data = {"sessionId": "74a9142a-4e3f-4f0a-9387-507c2f0d80fd"}
    prompt_result_success = {
        "stopReason": "end_turn",
        "requestId": "req-12345",
        "usage": {
            "inputTokens": 500,
            "outputTokens": 42,
            "cacheReadTokens": 100,
            "cacheWriteTokens": 0,
        },
    }
    out_success = parse_acp_outcome(
        ticket_id="ticket-01",
        session=session_data,
        result=prompt_result_success,
        requested_model="gemini-3.7-flash-high",
        diff="diff --git a/util.py...",
        duration_s=12.3,
        raw_tail="tail-log",
    )
    assert out_success["ok"] is True
    assert out_success["stop_reason"] == "end_turn"
    assert out_success["session_id"] == "74a9142a-4e3f-4f0a-9387-507c2f0d80fd"
    assert out_success["request_id"] == "req-12345"
    assert out_success["model_requested"] == "gemini-3.7-flash-high"
    assert out_success["model_selected"] is None
    assert out_success["model"] == "gemini-3.7-flash-high"
    assert out_success["tokens_in"] == 500
    assert out_success["tokens_out"] == 42
    assert out_success["cache_read_tokens"] == 100
    assert out_success["cache_write_tokens"] == 0

    # Outcome parsing: missing stopReason fails closed and preserves stop_reason=None
    prompt_result_missing = {
        "requestId": "req-empty",
    }
    out_missing = parse_acp_outcome(
        ticket_id="ticket-02",
        session=session_data,
        result=prompt_result_missing,
        requested_model=None,
        diff="",
        duration_s=5.0,
        raw_tail="empty",
    )
    assert out_missing["ok"] is False
    assert out_missing["stop_reason"] is None
    assert out_missing["session_id"] == "74a9142a-4e3f-4f0a-9387-507c2f0d80fd"
    assert out_missing["request_id"] == "req-empty"
    assert out_missing["model"] == "unknown:not-reported-by-runtime"
    assert out_missing["tokens_in"] is None
    assert out_missing["tokens_out"] is None

    # Outcome parsing: error stopReason fails closed and preserves exact value
    prompt_result_error = {
        "stopReason": "error",
        "requestId": "req-err",
    }
    out_error = parse_acp_outcome(
        ticket_id="ticket-03",
        session=session_data,
        result=prompt_result_error,
        requested_model=None,
        diff="",
        duration_s=1.0,
        raw_tail="error",
    )
    assert out_error["ok"] is False
    assert out_error["stop_reason"] == "error"

    # Outcome parsing: cancelled stopReason fails closed and preserves exact value
    prompt_result_cancelled = {
        "stopReason": "cancelled",
    }
    out_cancelled = parse_acp_outcome(
        ticket_id="ticket-04",
        session=session_data,
        result=prompt_result_cancelled,
        requested_model=None,
        diff="",
        duration_s=2.0,
        raw_tail="cancelled",
    )
    assert out_cancelled["ok"] is False
    assert out_cancelled["stop_reason"] == "cancelled"

    # Outcome parsing: unknown stopReason fails closed and preserves exact value
    prompt_result_unknown = {
        "stopReason": "unknown",
    }
    out_unknown = parse_acp_outcome(
        ticket_id="ticket-05",
        session=session_data,
        result=prompt_result_unknown,
        requested_model=None,
        diff="",
        duration_s=3.0,
        raw_tail="unknown",
    )
    assert out_unknown["ok"] is False
    assert out_unknown["stop_reason"] == "unknown"

    # Selected model emitted by runtime evidence is recorded
    prompt_result_with_model = {
        "stopReason": "end_turn",
        "model": "gemini-3.7-flash-high",
    }
    out_model = parse_acp_outcome(
        ticket_id="ticket-06",
        session=session_data,
        result=prompt_result_with_model,
        requested_model="auto",
        diff="",
        duration_s=4.0,
        raw_tail="",
    )
    assert out_model["model_requested"] == "auto"
    assert out_model["model_selected"] == "gemini-3.7-flash-high"
    assert out_model["model"] == "gemini-3.7-flash-high"

    print("Cursor ACP adapter regression tests pass")

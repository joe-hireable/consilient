"""Cursor's ACP control path stays distinct from Cursor-as-MCP-client."""

from adapter_cursor_acp import (
    acp_requested_model,
    agent_text,
    is_success_stop_reason,
    parse_acp_outcome,
)
from run_all import composition_for


if __name__ == "__main__":
    assert composition_for("cursor-acp") == {
        "agent": "cursor-acp",
        "domain": "coding",
        "harness": "cursor",
        "provider": "cursor-subscription",
        "model": "unknown:not-recorded-by-adapter",
        "control_protocol": "acp-v1-stdio",
    }
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

    assert is_success_stop_reason("end_turn")
    for reason in (None, "", "stop", "completed", "cancelled", "error", "unknown"):
        assert not is_success_stop_reason(reason)

    assert acp_requested_model({}) is None
    try:
        acp_requested_model({"model": "unproved-model"})
    except ValueError as exc:
        assert "not been exercised" in str(exc)
    else:
        raise AssertionError("unproved ACP model selection must fail closed")

    success = parse_acp_outcome(
        ticket_id="ticket-1",
        session={"sessionId": "session-1"},
        result={
            "stopReason": "end_turn",
            "requestId": "request-1",
            "usage": {"inputTokens": 500, "outputTokens": 42},
        },
        requested_model="requested-model",
        diff="diff",
        duration_s=12.3,
        raw_tail="tail",
    )
    assert success["ok"] is True
    assert success["stop_reason"] == "end_turn"
    assert success["session_id"] == "session-1"
    assert success["request_id"] == "request-1"
    assert success["tokens_in"] == 500 and success["tokens_out"] == 42
    assert success["model_requested"] == "requested-model"
    assert success["model_selected"] is None
    assert success["model"] == "unknown:not-reported-by-runtime"

    for result in ({}, {"stopReason": "error"}, {"stopReason": "unknown"}):
        failure = parse_acp_outcome(
            ticket_id="ticket-2",
            session={},
            result=result,
            requested_model=None,
            diff="",
            duration_s=1,
            raw_tail="",
        )
        assert failure["ok"] is False
        assert failure["stop_reason"] == result.get("stopReason")
        assert failure["tokens_in"] is None

    print("Cursor ACP identity, usage and fail-closed checks pass")

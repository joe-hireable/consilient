"""Cursor's ACP control path stays distinct from Cursor-as-MCP-client."""

from adapter_cursor_acp import agent_text
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
    print("Cursor ACP adapter checks pass")

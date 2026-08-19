"""The namespace, identity, model and result-parsing seams in adapter #3 get checks (I2)."""

from adapter_cursor import (
    cursor_command,
    identity_fields,
    model_fields,
    parse_result,
    to_wsl_path,
    usage_fields,
)

CASES = [
    (
        r"C:\Users\jpbpr\Repositories\consilience",
        "/mnt/c/Users/jpbpr/Repositories/consilience",
    ),
    (r"D:\tmp\exp05_abc", "/mnt/d/tmp/exp05_abc"),
    ("/already/posix", "/already/posix"),
    (r"C:\a b\c", "/mnt/c/a b/c"),
]

if __name__ == "__main__":
    for inp, want in CASES:
        got = to_wsl_path(inp)
        assert got == want, f"{inp} -> {got}, wanted {want}"
        print(f"  ok  {inp}  ->  {got}")
    print(f"path seam: {len(CASES)}/{len(CASES)} pass")

    # Command builder preserves goal, repo dir and requested model
    ticket = {
        "id": "test-1",
        "goal": "fix 'quotes' in code",
        "repo_dir": r"C:\tmp\exp05_test",
    }
    cmd_default = cursor_command(ticket)
    assert "cd '/mnt/c/tmp/exp05_test'" in cmd_default
    assert "--print --force --output-format json" in cmd_default
    assert "'fix '\\''quotes'\\'' in code'" in cmd_default
    assert "--model" not in cmd_default

    cmd_model = cursor_command(ticket, model="gemini-3.7-flash-high")
    assert "--model 'gemini-3.7-flash-high'" in cmd_model

    # Parse stdout with JSON result
    raw_stdout = (
        "Some preceding log text\n"
        '{"session_id":"ed6c6290-8892-42ab-9ced-504b543d230c","request_id":"2291a7ca-ae7d-497a-ad05-8df44b7df216",'
        '"usage":{"inputTokens":74781,"outputTokens":918,"cacheReadTokens":92160,"cacheWriteTokens":0}}\n'
    )
    parsed = parse_result(raw_stdout)
    assert parsed["session_id"] == "ed6c6290-8892-42ab-9ced-504b543d230c"
    assert parsed["request_id"] == "2291a7ca-ae7d-497a-ad05-8df44b7df216"

    # Identity fields: direct-run session_id and request_id preserved when emitted
    ids = identity_fields(parsed)
    assert ids == {
        "session_id": "ed6c6290-8892-42ab-9ced-504b543d230c",
        "request_id": "2291a7ca-ae7d-497a-ad05-8df44b7df216",
    }
    assert identity_fields({}) == {
        "session_id": None,
        "request_id": None,
    }

    # Model fields: requested model recorded separately from selected-model evidence
    m_none = model_fields(None, {})
    assert m_none == {
        "model": "unknown:not-reported-by-runtime",
        "model_requested": None,
        "model_selected": None,
    }

    m_req = model_fields("claude-opus-5-thinking-high", {})
    assert m_req == {
        "model": "claude-opus-5-thinking-high",
        "model_requested": "claude-opus-5-thinking-high",
        "model_selected": None,
    }

    m_selected = model_fields("auto", {"model": "gemini-3.7-flash-high"})
    assert m_selected == {
        "model": "gemini-3.7-flash-high",
        "model_requested": "auto",
        "model_selected": "gemini-3.7-flash-high",
    }

    # Usage fields: live-shaped + missing-usage cases
    got = usage_fields(
        {
            "usage": {
                "inputTokens": 74781,
                "outputTokens": 918,
                "cacheReadTokens": 92160,
                "cacheWriteTokens": 0,
            }
        }
    )
    assert got == {
        "tokens_in": 74781,
        "tokens_out": 918,
        "cache_read_tokens": 92160,
        "cache_write_tokens": 0,
    }
    assert all(value is None for value in usage_fields({}).values())
    print("usage, identity, model and path seams pass")

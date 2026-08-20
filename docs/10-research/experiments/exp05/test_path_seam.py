"""The namespace, identity, model and result seams in adapter #3 get checks (I2)."""

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

    ticket = {
        "id": "test-1",
        "goal": "fix 'quotes' in code",
        "repo_dir": r"C:\tmp\exp05_test",
    }
    assert "--model" not in cursor_command(ticket)
    command = cursor_command(ticket, "gemini-3.7-flash-high")
    assert "--model 'gemini-3.7-flash-high'" in command
    assert "'fix '\\''quotes'\\'' in code'" in command

    parsed = parse_result(
        'log\n{"session_id":"session-1","request_id":"request-1",'
        '"usage":{"inputTokens":74781,"outputTokens":918}}\n'
    )
    assert identity_fields(parsed) == {
        "session_id": "session-1",
        "request_id": "request-1",
    }
    assert identity_fields({}) == {"session_id": None, "request_id": None}
    assert model_fields("requested", {}) == {
        "model": "unknown:not-reported-by-runtime",
        "model_requested": "requested",
        "model_selected": None,
    }
    assert model_fields("requested", {"model": "selected"}) == {
        "model": "selected",
        "model_requested": "requested",
        "model_selected": "selected",
    }

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

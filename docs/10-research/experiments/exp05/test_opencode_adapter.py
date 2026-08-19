"""Regression checks for OpenCode × OpenRouter composition #6."""

import os

from adapter_opencode import (
    OPENCODE_WSL,
    WSL,
    opencode_command,
    opencode_env,
    parse_opencode_events,
)


if __name__ == "__main__":
    ticket = {
        "goal": "Edit only util.py.",
        "repo_dir": r"C:\Users\Joe\scratch repo",
        "timeout_s": 30,
    }
    command = opencode_command(ticket, "qwen/qwen3-coder")
    assert command == [
        WSL or "wsl",
        "-d",
        "Ubuntu",
        "-e",
        OPENCODE_WSL,
        "run",
        "--auto",
        "--format",
        "json",
        "--model",
        "openrouter/qwen/qwen3-coder",
        "--dir",
        "/mnt/c/Users/Joe/scratch repo",
        "Edit only util.py.",
    ]
    assert "OPENROUTER_API_KEY" not in " ".join(command)

    source = {"OPENROUTER_API_KEY": "not-a-real-key", "WSLENV": "EXISTING"}
    child = opencode_env(source)
    assert child["OPENROUTER_API_KEY"] == "not-a-real-key"
    assert child["WSLENV"].split(":") == ["EXISTING", "OPENROUTER_API_KEY"]
    assert source["WSLENV"] == "EXISTING"

    stdout = "\n".join(
        [
            '{"type":"step_finish","part":{"cost":0.001,"tokens":{"input":10,"output":2,"cache":{"read":3,"write":4}}}}',
            '{"type":"step_finish","part":{"cost":0.002,"tokens":{"input":20,"output":5,"cache":{"read":6,"write":7}}}}',
            '{"type":"error","error":{"message":"example"}}',
        ]
    )
    usage, errors = parse_opencode_events(stdout)
    assert usage == {
        "tokens_in": 30,
        "tokens_out": 7,
        "cache_read_tokens": 9,
        "cache_write_tokens": 11,
        "cost_usd": 0.003,
    }
    assert len(errors) == 1 and "example" in errors[0]
    print("OpenCode adapter command, environment and parser checks pass")

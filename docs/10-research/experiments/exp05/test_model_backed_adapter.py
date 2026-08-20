"""The model-backed coding adapter must expose composition and ignore user config."""

from pathlib import Path

import subprocess

from adapter_model_backed import (
    codex_command,
    codex_run_options,
    composition,
    parse_codex_events,
)


if __name__ == "__main__":
    ticket = {"goal": "test goal", "repo_dir": "scratch-repo"}
    command = codex_command(ticket, ["-m", "example/model"], Path("last.txt"))
    assert "--ignore-user-config" in command
    assert command[-2:] == ["-m", "example/model"]
    options = codex_run_options({"timeout_s": 123})
    assert options["stdin"] is subprocess.DEVNULL
    assert options["timeout"] == 123

    got = composition("openrouter", "qwen/qwen3-coder")
    assert got == {
        "agent": "codex+openrouter:qwen/qwen3-coder",
        "domain": "coding",
        "harness": "codex",
        "provider": "openrouter",
        "model": "qwen/qwen3-coder",
    }
    tok_in, tok_out, errors = parse_codex_events(
        '{"type":"turn.failed","error":{"message":"provider rejected"}}\n'
        '{"type":"usage","usage":{"input_tokens":12,"output_tokens":3}}\n'
    )
    assert (tok_in, tok_out) == (12, 3)
    assert len(errors) == 1 and "provider rejected" in errors[0]
    print("model-backed adapter: isolation + stdin + diagnostics + schema pass")

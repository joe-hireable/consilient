"""Antigravity admission fails closed on credits and incomplete probes."""

import json
import tempfile
from pathlib import Path

from adapter_antigravity import (
    antigravity_command,
    credit_overage_disabled,
    parse_stream,
    probe_ready,
)
from run_all import composition_for


if __name__ == "__main__":
    assert composition_for("antigravity:gemini-3.7-flash-low") == {
        "agent": "antigravity:gemini-3.7-flash-low",
        "domain": "coding",
        "harness": "antigravity",
        "provider": "google-account:plan-unverified",
        "model": "gemini-3.7-flash-low",
    }
    command = antigravity_command(
        {"goal": "Edit only util.py", "timeout_s": 45},
        "gemini-3.7-flash-low",
        Path("agy.exe"),
    )
    assert command[1] == "--print=Edit only util.py"
    assert "--output-format=stream-json" in command
    assert "--model=gemini-3.7-flash-low" in command
    assert "--print-timeout=45s" in command
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / "settings.json"
        assert credit_overage_disabled(settings)

        settings.write_text(json.dumps({"useG1Credits": False}), encoding="utf-8")
        assert credit_overage_disabled(settings)

        settings.write_text(json.dumps({"useG1Credits": True}), encoding="utf-8")
        assert not credit_overage_disabled(settings)

        settings.write_text("not json", encoding="utf-8")
        assert not credit_overage_disabled(settings)

    failed = "\n".join(
        [
            json.dumps(
                {
                    "event": "init",
                    "init": {"model": "gemini-3.7-flash-low"},
                }
            ),
            json.dumps(
                {
                    "event": "result",
                    "result": {
                        "status": "ERROR",
                        "usage": {"total_tokens": 0},
                    },
                }
            ),
        ]
    )
    parsed = parse_stream(failed)
    assert parsed["model"] == "gemini-3.7-flash-low"
    assert not probe_ready(0, parsed)

    passed = parse_stream(
        json.dumps(
            {
                "event": "result",
                "result": {"status": "SUCCESS", "response": "READY"},
            }
        )
    )
    assert probe_ready(0, passed)
    assert not probe_ready(1, passed)
    print("Antigravity adapter checks pass")

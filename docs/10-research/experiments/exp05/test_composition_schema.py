"""Every experimental result names domain, harness, provider and model (ADR-0027)."""

import json
from pathlib import Path

from run_all import composition_for

REQUIRED = {"domain", "harness", "provider", "model"}


if __name__ == "__main__":
    assert composition_for("openrouter:qwen/qwen3-coder") == {
        "agent": "codex+openrouter:qwen/qwen3-coder",
        "domain": "coding",
        "harness": "codex",
        "provider": "openrouter",
        "model": "qwen/qwen3-coder",
    }
    assert composition_for("ollama:qwen3:8b")["harness"] == "codex"
    assert composition_for("opencode+openrouter:qwen/qwen3-coder") == {
        "agent": "opencode+openrouter:qwen/qwen3-coder",
        "domain": "coding",
        "harness": "opencode",
        "provider": "openrouter",
        "model": "qwen/qwen3-coder",
    }

    rows = json.loads(
        (Path(__file__).parent / "backend-comparison.json").read_text(encoding="utf-8")
    )
    for row in rows:
        missing = REQUIRED - row.keys()
        assert not missing, f"{row.get('agent')}: missing {sorted(missing)}"
    print(f"composition schema: {len(rows)} stored rows pass")

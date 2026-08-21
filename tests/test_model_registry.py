"""R24 clause 1: the model registry is refreshed by live enumeration, not by hand.

The registry was a hand-transcribed snapshot of one `cursor-agent --list-models`
run and went stale silently. These tests pin the parser, the pool filter, and the
drift detector, and — when cursor-agent is reachable — fail the moment the
registry and the machine disagree. The mutation test proves the detector can
fail; without it a detector that never fires is indistinguishable from none.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from consilient.harness import (  # noqa: E402
    MODELS,
    ModelOption,
    cursor_models_pool_ids,
    parse_list_models,
    registry_drift,
)

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "refresh_models.py"
sys.path.insert(0, str(ROOT / "scripts"))

import refresh_models  # noqa: E402

SAMPLE_OUTPUT = """Available models

auto - Auto (default)
gpt-5.3-codex-low - Codex 5.3 Low
composer-2.5 - Composer 2.5
cursor-grok-4.6-high-fast - Cursor Grok 4.6 Fast
gemini-3.7-flash-high - Gemini 3.7 Flash
kimi-k3-max - Kimi K3 Max
"""


def test_parse_list_models_extracts_ids_and_skips_furniture() -> None:
    assert parse_list_models(SAMPLE_OUTPUT) == (
        "auto",
        "gpt-5.3-codex-low",
        "composer-2.5",
        "cursor-grok-4.6-high-fast",
        "gemini-3.7-flash-high",
        "kimi-k3-max",
    )
    assert parse_list_models("") == ()
    assert parse_list_models("Available models\n\n") == ()


def test_pool_filter_drops_vendor_aliases_and_auto() -> None:
    assert cursor_models_pool_ids(parse_list_models(SAMPLE_OUTPUT)) == (
        "composer-2.5",
        "cursor-grok-4.6-high-fast",
        "kimi-k3-max",
    )


def test_registry_drift_reports_both_directions() -> None:
    registered = (
        ModelOption("composer-2.5", "cursor-composer", "composer", "cursor-models"),
        ModelOption("dead-model", "cursor-composer", "dead", "cursor-models"),
    )
    live = ("composer-2.5", "kimi-k3-max", "gpt-5.3-codex-low", "auto")
    missing, stale = registry_drift(live, registered)
    assert missing == ("kimi-k3-max",)
    assert stale == ("dead-model",)
    # Vendor-pool and auto ids are policy exclusions, never drift.
    assert "gpt-5.3-codex-low" not in missing
    assert "auto" not in missing


def test_the_detector_can_fail() -> None:
    """Mutation: a registry the machine disagrees with must produce drift."""
    live = tuple(item.id for item in MODELS)
    assert registry_drift(live, MODELS) == ((), ())
    broken = MODELS + (ModelOption("invented-9", "cursor-composer", "invented", "cursor-models"),)
    _, stale = registry_drift(live, broken)
    assert stale == ("invented-9",)
    _, stale = registry_drift(tuple(mid for mid in live if mid != MODELS[0].id), MODELS)
    assert stale == (MODELS[0].id,)


def test_render_registry_preserves_order_appends_new_and_drops_stale() -> None:
    existing = (
        ModelOption("composer-2.5", "cursor-composer", "composer", "cursor-models"),
        ModelOption("dead-model", "cursor-composer", "dead", "cursor-models"),
        ModelOption("kimi-k3-max", "cursor-composer", "kimi", "cursor-models"),
    )
    live = ("kimi-k3-max", "composer-2.5", "glm-5.2-max", "gpt-5.3-codex-low", "auto")
    rendered = refresh_models.render_registry(live, existing)
    rows = [line for line in rendered.splitlines() if line.startswith("    ModelOption(")]
    assert rows == [
        '    ModelOption("composer-2.5", "cursor-composer", "composer", "cursor-models"),',
        '    ModelOption("kimi-k3-max", "cursor-composer", "kimi", "cursor-models"),',
        '    ModelOption("glm-5.2-max", "cursor-composer", "glm", "cursor-models"),',
    ]
    assert "dead-model" not in rendered
    assert "gpt-5.3-codex-low" not in rendered  # vendor pool is never written
    assert all('"auto"' not in row for row in rows)


def test_registry_matches_the_machine_when_cursor_agent_is_reachable() -> None:
    if not SCRIPT.is_file():
        pytest.skip("refresh_models.py not present in this checkout")
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if completed.returncode == 2:
        pytest.skip(completed.stdout.strip() or "cursor-agent not reachable")
    assert completed.returncode == 0, (
        "the model registry and the machine disagree:\n" + completed.stdout
    )

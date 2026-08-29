"""Selection: which pool and which harness a task is sent to, automatically and when the
operator names one.

Two invariants are load-bearing and each ships with the check that can fail it — an
exhausted pool is never selected while another has headroom, and automatic selection
never spends unknown headroom. Both are mutation targets: ranking on `used_percent`
alone would pick claude at 0%, and treating unknown as free would spend a plan nobody
has measured. The Cursor Other pool is avoided automatically, so `claude-4-sonnet` and
`gpt-5` route there only when the operator names the model, and a model whose reasoning
capability is unregistered is refused before a brief is written or a process launched.

Naming a harness explicitly is attended operation, not a fallback: an unknown pool may
be spent that way, an exhausted one only with `--allow-exhausted`. Fan-out selection is
here too because it is a selection rule — two arms of the same family are echo, not
consilience, so it refuses rather than pick twice from one family. The headroom file
tests belong with these because the pool states the selector reasons over come from it:
a written file overrides the defaults, the exhaustion threshold is a boundary not a
strict inequality, and a recent probe is reused rather than re-run.

Preserved from before the 28 August 2026 split, which rewrote this docstring and carried
the paragraph below into no sibling. It is reproduced WHOLE. An earlier restoration took
only the individual lines a checker had reported missing, which spliced halves of two
different sentences together beneath a claim of being verbatim -- found by an outside
review on 29 August 2026.

    The load-bearing ones:
      - an exhausted pool is never selected while any other pool has headroom
      - automatic selection never spends unknown headroom
      - a silent exit-0 is recorded silent, not retried on another pool
      - fan-out requires two different families
      - the consil CLI surface is unchanged
"""

from family_source import seam

import json
import sys
from datetime import datetime, timezone
import pytest
from consilient.harness import (
    DEFAULT_POOLS,
    HARNESSES,
    EXHAUSTED_USED_PERCENT,
    PoolState,
    Probe,
    cursor_pool_for_model,
    harness_by_id,
    load_pools,
    pools_from_mapping,
    remaining_percent,
    select,
    select_fanout,
)
from dispatch_helpers import (
    CAP_HELP,
    INSTALLED,
    _load_script,
)


def _pool(
    name: str,
    *,
    used: float | None,
    exhausted: bool = False,
    note: str = "",
) -> PoolState:
    return PoolState(
        name=name,
        used_percent=used,
        exhausted=exhausted,
        note=note,
        observed_at="2026-08-21T00:00:00+00:00",
        source="test",
    )


def _probes(*missing: str) -> tuple[Probe, ...]:
    skip = set(missing)
    return tuple(
        Probe(
            item.id,
            item.id not in skip,
            "1.0" if item.id not in skip else None,
            "fixture",
        )
        for item in HARNESSES
    )


def test_default_snapshot_prefers_cursor_models_over_grok():
    decision = select(probes=INSTALLED, pools=DEFAULT_POOLS)
    assert decision.kind == "run"
    assert decision.harness is not None
    assert decision.harness.id == "cursor-composer"
    assert "claude" not in decision.reason


def test_exhausted_pool_with_lowest_used_percent_is_never_selected():
    """Mutation target: ranking on used_percent alone would pick claude at 0%."""
    pools = (
        _pool("claude-weekly", used=0.0, exhausted=True, note="nearly exhausted"),
        _pool("cursor-models", used=40.0),
        _pool("cursor-other", used=58.0),
        _pool("grok-weekly", used=50.0),
        _pool("codex-weekly", used=None, note="unknown"),
    )
    decision = select(probes=INSTALLED, pools=pools)
    assert decision.kind == "run"
    assert decision.harness is not None
    assert decision.harness.id == "cursor-composer"
    assert decision.harness.pool != "claude-weekly"
    assert remaining_percent(pools[0]) == 100.0


def test_automatic_selection_refuses_when_only_the_exhausted_pool_is_left():
    pools = (
        _pool("claude-weekly", used=None, exhausted=True, note="nearly exhausted"),
        _pool("cursor-models", used=1.0),
        _pool("cursor-other", used=58.0),
        _pool("grok-weekly", used=2.0),
        _pool("codex-weekly", used=None, note="unknown"),
    )
    decision = select(probes=_probes("cursor-composer", "grok", "codex"), pools=pools)
    assert decision.kind == "refuse"
    assert decision.harness is None
    assert "exhausted" in decision.reason
    assert "claude" in decision.reason


def test_unknown_headroom_is_not_selected_automatically():
    pools = (
        _pool("claude-weekly", used=None, exhausted=True),
        _pool("cursor-models", used=None, note="unknown"),
        _pool("cursor-other", used=58.0),
        _pool("grok-weekly", used=None, note="unknown"),
        _pool("codex-weekly", used=None, note="unknown"),
    )
    decision = select(probes=INSTALLED, pools=pools)
    assert decision.kind == "refuse"
    assert "unknown" in decision.reason


def test_explicit_unknown_harness_is_attended_not_a_fallback():
    decision = select(
        probes=INSTALLED,
        pools=DEFAULT_POOLS,
        requested="codex",
    )
    assert decision.kind == "run"
    assert decision.harness is not None
    assert decision.harness.id == "codex"


def test_explicit_exhausted_harness_is_refused_without_override():
    decision = select(
        probes=INSTALLED,
        pools=DEFAULT_POOLS,
        requested="claude",
    )
    assert decision.kind == "refuse"
    assert decision.harness is None
    assert "exhausted" in decision.reason


def test_allow_exhausted_is_required_to_spend_claude():
    decision = select(
        probes=INSTALLED,
        pools=DEFAULT_POOLS,
        requested="claude",
        allow_exhausted=True,
    )
    assert decision.kind == "run"
    assert decision.harness is not None
    assert decision.harness.id == "claude"


def test_missing_install_is_not_selected():
    decision = select(probes=_probes("cursor-composer"), pools=DEFAULT_POOLS)
    assert decision.kind == "run"
    assert decision.harness is not None
    assert decision.harness.id == "grok"


def test_fanout_picks_two_different_families():
    decision = select_fanout(probes=INSTALLED, pools=DEFAULT_POOLS)
    assert decision.kind == "run"
    assert decision.first is not None and decision.second is not None
    assert decision.first.family != decision.second.family
    assert {decision.first.id, decision.second.id} == {"cursor-composer", "grok"}


def test_fanout_refuses_when_only_one_family_is_eligible():
    decision = select_fanout(
        probes=_probes("cursor-composer", "codex", "claude"),
        pools=DEFAULT_POOLS,
    )
    assert decision.kind == "refuse"
    assert decision.first is None
    assert "different model families" in decision.reason


def test_cursor_vendor_aliases_draw_on_the_avoided_pool():
    assert cursor_pool_for_model("composer-2.5") == "cursor-models"
    assert cursor_pool_for_model("claude-4-sonnet") == "cursor-other"
    assert cursor_pool_for_model("gpt-5") == "cursor-other"
    assert cursor_pool_for_model("gemini-3.7-flash") == "cursor-other"


def test_pools_from_file_override_defaults(tmp_path):
    path = tmp_path / "headroom.json"
    path.write_text(
        json.dumps(
            {
                "observed_at": "2026-08-21T12:00:00+00:00",
                "source": "test file",
                "pools": {"grok-weekly": {"used_percent": 80}},
            }
        ),
        encoding="utf-8",
    )
    pools = load_pools(path)
    grok = next(item for item in pools if item.name == "grok-weekly")
    claude = next(item for item in pools if item.name == "claude-weekly")
    assert grok.used_percent == 80.0
    assert claude.exhausted is True


def test_used_percent_at_threshold_is_exhausted():
    pools = pools_from_mapping(
        {
            "observed_at": "2026-08-21T00:00:00+00:00",
            "source": "t",
            "pools": {"grok-weekly": {"used_percent": EXHAUSTED_USED_PERCENT}},
        }
    )
    grok = next(item for item in pools if item.name == "grok-weekly")
    assert grok.exhausted is True
    assert remaining_percent(grok) == 100.0 - EXHAUSTED_USED_PERCENT


def test_unknown_explicit_model_refuses_before_brief_or_launch(monkeypatch, tmp_path):
    script = _load_script()
    monkeypatch.setattr(seam("dispatch_launch"), "DEFAULT_CURSOR_LOCK", tmp_path / "cursor.lock")
    monkeypatch.setattr(seam("dispatch_launch"), "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: CAP_HELP)
    monkeypatch.setattr(
        seam("dispatch_launch"),
        "run_process",
        lambda *_args, **_kwargs: pytest.fail("unknown model must not launch"),
    )
    harness = harness_by_id("cursor-composer")
    assert harness is not None
    run_dir = tmp_path / "run"

    result = script.run_harness(
        harness,
        task="pong",
        cwd=tmp_path,
        run_dir=run_dir,
        timeout_s=5,
        model="unregistered-reasoner-xhigh",
        run_id="run-unknown",
    )

    assert result.status == "refused"
    assert "reasoning capability is unknown" in result.reason
    assert not (run_dir / "brief.md").exists()


def test_default_headroom_refresh_is_bounded_and_uses_the_local_probe(
    monkeypatch, tmp_path
):
    script = _load_script()
    output = (tmp_path / "headroom.json").resolve()
    monkeypatch.setattr(seam("dispatch_launch"), "DEFAULT_HEADROOM", output)
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return 0, False, 0.1, None

    monkeypatch.setattr(seam("dispatch_launch"), "run_process", fake_run)

    assert script.refresh_default_headroom(output) is None
    assert captured["argv"][0] == sys.executable
    assert captured["argv"][1].endswith("scripts\\headroom.py")
    assert captured["argv"][-2:] == ["--timeout", "5"]
    assert captured["kwargs"]["timeout_s"] == 45


def test_recent_default_headroom_is_reused_without_another_probe(monkeypatch, tmp_path):
    script = _load_script()
    output = (tmp_path / "headroom.json").resolve()
    monkeypatch.setattr(seam("dispatch_launch"), "DEFAULT_HEADROOM", output)
    observed_at = datetime.now(timezone.utc).isoformat()
    output.write_text(
        json.dumps(
            {
                "observed_at": observed_at,
                "source": "fresh test probe",
                "pools": {
                    pool.name: {
                        "used_percent": None,
                        "exhausted": False,
                        "note": "unknown",
                    }
                    for pool in DEFAULT_POOLS
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        seam("dispatch_launch"),
        "run_process",
        lambda *_args, **_kwargs: pytest.fail("fresh headroom must be reused"),
    )

    assert script.refresh_default_headroom(output) is None


def test_explicit_cursor_other_model_is_attended(tmp_path, monkeypatch):
    """Automatic selection avoids the Other pool; an explicit --model is the operator naming it."""
    script = _load_script()
    monkeypatch.setattr(seam("dispatch_launch"), "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(seam("dispatch_launch"), "help_text", lambda _argv: CAP_HELP)
    harness = harness_by_id("cursor-composer")
    assert harness is not None
    built = script.build_command(
        harness,
        task="pong",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model="gpt-5",
    )
    assert isinstance(built, list)
    assert any("gpt-5" in str(part) for part in built)

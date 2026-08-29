"""`scripts/dispatch.py` as the coordination layer's caller — the only tests here that
load the script from disk and drive it end to end.

Dispatch is a script rather than a `consil` subcommand (ADR-0058), so it is loaded by
path and cached in `sys.modules`; that mechanism is the reason these tests sit together
rather than anything about the assertions. What they establish is the wiring: a brief is
written with a `recall.md` beside it and the recall pack embedded so a brief-only reader
still sees it; a run opens exactly one claim and closes it, leaving `OPENED` then
`COMPLETED` against its own ticket and nothing live afterwards; a conflicting claim
refuses *before* any claim of its own is opened, and `run_harness` must not be reached
at all; a dry run reports the conflict and the in-flight count while writing nothing to
the log.

Command building for Cursor is here for the same reason — it is dispatch, not the
registry, that turns pool state into a command line. The family case carries a
superseding note worth keeping. Superseded by F04 on 23 August 2026: this once asserted
that naming a family automatically selects a model from it. The kimi rows are now
`pool_verified=False`, because Cursor's own billing page lists Cursor Models as "Cursor
Grok and Composer" and names neither kimi nor glm, while Other Models rose 58% to 81%
across a day of heavy kimi dispatch. Automatic selection must therefore refuse an
unverified pool rather than spend what it cannot account for — a strengthening, not a
relaxation. The attended override is unaffected and is covered by `tests/test_model_pool
s.py::test_explicit_model_keeps_the_attended_override_for_an_unverified_pool`."""

from family_source import seam

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from consilient import coordination, work_items
from consilient.events import read_all
from consilient.harness import (
    DEFAULT_POOLS,
    HARNESSES,
    harness_by_id,
    select,
)
from coordination_helpers import (
    DISPATCH_PATH,
    _live,
)


def _load_script():
    name = "consilient_dispatch_script"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, DISPATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _probes_installed():
    from consilient.harness import Probe

    return tuple(
        Probe(item.id, True, "1.0", f"{item.binary} (fixture)") for item in HARNESSES
    )


# --- dispatch wiring ------------------------------------------------------------


def _seed_recallable_event(log: Path) -> None:
    from consilient.events import SCHEMA_VERSION, append

    log.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    append(
        log / f"{ts[:10]}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": "dispatch.outcome",
            "actor": "consilient.dispatch",
            "data": {
                "status": "ok",
                "harness": "grok",
                "task": "earlier work",
                "supervised": True,
            },
        },
    )


def test_write_brief_writes_recall_md_beside_the_brief_and_references_it(tmp_path):
    script = _load_script()
    log = tmp_path / "log"
    _seed_recallable_event(log)
    run_dir = tmp_path / "run"
    brief = script.write_brief(
        run_dir, "continue the work", log_dir=log, in_flight="## In flight\n\n- one\n"
    )
    text = brief.read_text(encoding="utf-8")
    recall = (run_dir / "recall.md").read_text(encoding="utf-8")
    assert "Recall pack" in recall
    assert "`recall.md` beside this brief" in text
    assert "## In flight" in text
    assert "Recall pack" in text  # the embed survives for brief-only readers


def test_dispatch_one_refuses_a_second_claim_on_an_overlapping_path(
    tmp_path, monkeypatch
):
    script = _load_script()
    log = tmp_path / "log"
    coordination.open_claim(
        log,
        run_id="other-run",
        paths=["src"],
        cwd=tmp_path,
        timeout_s=3600,
        now=datetime.now(timezone.utc),
    )

    def forbidden(*_args, **_kwargs):
        raise AssertionError("run_harness must not run when a claim conflicts")

    monkeypatch.setattr(seam("dispatch_harness"), "run_harness", forbidden)
    payload, code = script.dispatch_one(
        decision=select(
            probes=_probes_installed(), pools=DEFAULT_POOLS, requested="grok"
        ),
        task="pong",
        cwd=tmp_path,
        log_dir=log,
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=False,
        claims=("src/consilient",),
    )
    assert payload["status"] == "refused"
    assert code == 2
    assert "other-run" in payload["reason"]
    events, rejected = read_all(log)
    assert not rejected
    kinds = [event.kind for event in events]
    assert "dispatch.refused" in kinds
    # The refusal happened before this dispatch opened any claim of its own.
    assert f"dispatch:{payload['run_id']}" not in [
        event.data.get("ticket") for event in events
    ]


def test_dispatch_one_opens_and_releases_its_claim_around_the_run(
    tmp_path, monkeypatch
):
    script = _load_script()
    log = tmp_path / "log"
    grok = harness_by_id("grok")
    assert grok is not None

    def fake_run(harness, **kwargs):
        return script.RunResult(
            harness=harness,
            status="ok",
            reason="done",
            exit_code=0,
            stdout="worked",
            stderr="",
            artefact_bytes=6,
            diff_bytes=6,
            timed_out=False,
            duration_s=0.1,
            command=("grok", "-p"),
            run_id=kwargs["run_id"],
            stdout_path=str(tmp_path / "stdout.txt"),
            stderr_path=str(tmp_path / "stderr.txt"),
        )

    monkeypatch.setattr(seam("dispatch_harness"), "run_harness", fake_run)
    payload, code = script.dispatch_one(
        decision=select(
            probes=_probes_installed(), pools=DEFAULT_POOLS, requested="grok"
        ),
        task="pong",
        cwd=tmp_path,
        log_dir=log,
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=False,
        claims=("src",),
    )
    assert code == 0
    assert payload["claim"]["released"] is True
    events, rejected = read_all(log)
    assert not rejected
    ticket = coordination.claim_ticket(payload["run_id"])
    kinds_by_ticket = [
        event.kind for event in events if event.data.get("ticket") == ticket
    ]
    assert kinds_by_ticket == [work_items.OPENED, work_items.COMPLETED]
    assert _live(log, now=datetime.now(timezone.utc)) == ()


def test_dry_run_reports_a_claim_conflict_without_writing_one(tmp_path):
    script = _load_script()
    log = tmp_path / "log"
    coordination.open_claim(
        log,
        run_id="other-run",
        paths=["src"],
        cwd=tmp_path,
        timeout_s=3600,
        now=datetime.now(timezone.utc),
    )
    before, _ = read_all(log)
    payload, code = script.dispatch_one(
        decision=select(
            probes=_probes_installed(), pools=DEFAULT_POOLS, requested="grok"
        ),
        task="pong",
        cwd=tmp_path,
        log_dir=log,
        runs_dir=tmp_path / "runs",
        timeout_s=5,
        model=None,
        dry_run=True,
        claims=("src",),
    )
    assert payload["status"] == "dry-run"
    assert payload["claim_conflict"]["ticket"] == "dispatch:other-run"
    assert payload["in_flight"] == 1
    after, _ = read_all(log)
    assert len(after) == len(before)  # a dry run writes nothing


def test_build_command_cursor_selects_a_model_from_pool_state(tmp_path, monkeypatch):
    script = _load_script()
    monkeypatch.setattr(seam("dispatch_launch"), "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(
        seam("dispatch_launch"),
        "help_text",
        lambda _argv: "--max-turns <N> --max-tokens <N> --force --trust",
    )
    cursor = harness_by_id("cursor-composer")
    assert cursor is not None
    built = script.build_command(
        cursor,
        task="pong",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model=None,
        pools=DEFAULT_POOLS,
    )
    assert isinstance(built, list)
    assert any("composer-2.5" in str(part) for part in built)


def test_build_command_cursor_family_without_pool_state_refuses(tmp_path):
    """--family with no headroom snapshot must not silently default to composer."""
    script = _load_script()
    cursor = harness_by_id("cursor-composer")
    assert cursor is not None
    built = script.build_command(
        cursor,
        task="pong",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model=None,
        family="grok",
    )
    assert isinstance(built, str)
    assert "headroom" in built or "no eligible model" in built


def test_build_command_cursor_family_selection_picks_the_family(tmp_path, monkeypatch):
    script = _load_script()
    monkeypatch.setattr(seam("dispatch_launch"), "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(
        seam("dispatch_launch"),
        "help_text",
        lambda _argv: "--max-turns <N> --max-tokens <N> --force --trust",
    )
    cursor = harness_by_id("cursor-composer")
    assert cursor is not None
    built = script.build_command(
        cursor,
        task="pong",
        cwd=tmp_path,
        brief=tmp_path / "brief.md",
        model=None,
        family="kimi",
        pools=DEFAULT_POOLS,
    )
    # Superseded by F04 on 23 Aug 2026. This asserted that naming a family automatically
    # selects a model from it. The kimi rows are now `pool_verified=False`: Cursor's own
    # billing page lists Cursor Models as "Cursor Grok and Composer" and names neither kimi
    # nor glm, while Other Models rose 58% -> 81% across a day of heavy kimi dispatch.
    # Automatic selection must therefore REFUSE an unverified pool rather than spend what it
    # cannot account for. This is a strengthening, not a relaxation: the assertion below is
    # harder to satisfy than the one it replaces.
    #
    # The attended override is unaffected and is covered separately —
    # `tests/test_model_pools.py::test_explicit_model_keeps_the_attended_override_for_an_unverified_pool`
    # proves an explicitly named kimi model still dispatches.
    assert isinstance(built, str), (
        "automatic family selection must refuse an unverified pool, not build a command"
    )
    assert "unverified" in built.casefold()

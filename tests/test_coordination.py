"""Tests for the coordination layer: claims, model selection, β ceilings, wiring.

The invariants under test are the ones the brief named:

- a second dispatch claiming an overlapping path is refused;
- a crashed dispatcher cannot hold a claim forever (expiry is read from the event,
  so the passage of time alone releases it — no lock file to go stale);
- automatic model selection never drifts to the avoided cursor-other pool;
- routing on an absent β refuses rather than assumes.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import coordination, routing, work_items
from consilient.beta import INSUFFICIENT, MEASURED, Beta
from consilient.events import EventError, read_all
from consilient.harness import (
    DEFAULT_POOLS,
    HARNESSES,
    MODELS,
    PoolState,
    harness_by_id,
    model_family,
    models_for_harness,
    pool_for_model,
    select,
    select_model,
)

ROOT = Path(__file__).resolve().parent.parent
DISPATCH_PATH = ROOT / "scripts" / "dispatch.py"

T0 = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)


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


def _pool(name: str, *, used: float | None, exhausted: bool = False) -> PoolState:
    return PoolState(
        name=name,
        used_percent=used,
        exhausted=exhausted,
        note="fixture",
        observed_at="2026-08-21T00:00:00+00:00",
        source="fixture",
    )


def _live(log: Path, *, now: datetime) -> tuple[coordination.Claim, ...]:
    events, rejected = read_all(log)
    assert not rejected
    return coordination.live_claims(events, now=now)


# --- path canonicalisation -------------------------------------------------


def test_dispatch_actor_constant_cannot_drift_from_the_registry():
    """coordination restates harness.DISPATCH_ACTOR because the product capability
    allowlist forbids the import; this test is the drift check for that restatement."""
    from consilient.harness import DISPATCH_ACTOR as REGISTRY_ACTOR

    assert coordination.DISPATCH_ACTOR == REGISTRY_ACTOR


def test_canonical_path_unifies_the_windows_wsl_boundary():
    win = coordination.canonical_path("C:\\Users\\joe\\repo\\src\\A.py")
    wsl = coordination.canonical_path("/mnt/c/Users/joe/repo/src/a.py")
    assert win == wsl


def test_canonical_path_resolves_relative_against_the_dispatch_cwd(tmp_path):
    got = coordination.canonical_path("src/x.py", cwd=tmp_path)
    assert got == coordination.canonical_path(str(tmp_path / "src" / "x.py"))


def test_paths_overlap_is_containment_at_a_boundary_either_way():
    assert coordination.paths_overlap("/a/b", "/a/b")
    assert coordination.paths_overlap("/a/b", "/a/b/c.py")
    assert coordination.paths_overlap("/a/b/c.py", "/a/b")
    assert not coordination.paths_overlap("/a/b", "/a/bc")
    assert not coordination.paths_overlap("/a/b", "/a/c")


# --- claim lifecycle ---------------------------------------------------------


def test_open_claim_is_live_until_completed(tmp_path):
    log = tmp_path / "log"
    coordination.open_claim(
        log, run_id="run-1", paths=["src"], cwd=tmp_path, timeout_s=600, now=T0
    )
    assert [c.run_id for c in _live(log, now=T0)] == ["run-1"]
    coordination.close_claim(log, run_id="run-1")
    assert _live(log, now=T0) == ()


def test_a_crashed_dispatchers_claim_expires_on_its_own(tmp_path):
    """The crash-safety invariant: no completion, no outcome, just the clock.

    The stale `.budget.lock` measured on this machine refuses forever after a
    SIGKILL because it is a file. A claim is a projection with a clock, so the
    passage of time alone releases it.
    """
    log = tmp_path / "log"
    coordination.open_claim(
        log, run_id="run-dies", paths=["src"], cwd=tmp_path, timeout_s=60, now=T0
    )
    grace = coordination.CLAIM_GRACE_S
    assert _live(log, now=T0 + timedelta(seconds=60 + grace - 1)) != ()
    assert _live(log, now=T0 + timedelta(seconds=60 + grace + 1)) == ()


def test_a_terminal_outcome_releases_the_claim_without_a_completion(tmp_path):
    from consilient.harness import record_outcome

    log = tmp_path / "log"
    coordination.open_claim(
        log, run_id="run-2", paths=["src"], cwd=tmp_path, timeout_s=3600, now=T0
    )
    grok = harness_by_id("grok")
    assert grok is not None
    record_outcome(
        log,
        ts=datetime.now(timezone.utc).isoformat(),
        run_id="run-2",
        task="pong",
        cwd=str(tmp_path),
        harness=grok,
        status="failed",
        reason="died before close_claim ran",
        exit_code=1,
        artefact_bytes=0,
        diff_bytes=0,
        timed_out=False,
        duration_s=1.0,
        command=("grok",),
    )
    assert _live(log, now=T0 + timedelta(seconds=10)) == ()


def test_a_malformed_claim_is_not_live(tmp_path):
    """A claim-shaped event without parseable fields is declined, not guessed at."""
    from consilient.events import SCHEMA_VERSION, append

    log = tmp_path / "log"
    log.mkdir()
    ts = datetime.now(timezone.utc).isoformat()
    for ticket, extra in (
        # No opened_at, no expires_at: the projection cannot know when this
        # claim ends, so it declines to treat it as live at all.
        ("dispatch:hand-written", {}),
        # opened_at but no expires_at: a guessed expiry would resurrect it.
        ("dispatch:half-formed", {"opened_at": T0.isoformat()}),
    ):
        append(
            log / f"{ts[:10]}.jsonl",
            {
                "v": SCHEMA_VERSION,
                "ts": ts,
                "event": work_items.OPENED,
                "actor": "consilient.dispatch",
                "data": {
                    "ticket": ticket,
                    "accountable": "consilient.dispatch",
                    "run_id": ticket.removeprefix("dispatch:"),
                    "paths": ["src"],
                    **extra,
                },
            },
        )
    assert _live(log, now=T0 + timedelta(seconds=1)) == ()


def test_conflicting_claims_are_detected_across_the_windows_wsl_boundary(tmp_path):
    """The same file claimed from both sides of the boundary is one overlap."""
    log = tmp_path / "log"
    coordination.open_claim(
        log,
        run_id="run-win",
        paths=["src\\consilient"],
        cwd=Path("C:\\Users\\joe\\repo"),
        timeout_s=600,
        now=T0,
    )
    live = _live(log, now=T0)
    hit = coordination.conflict(
        ["/mnt/c/Users/joe/repo/src/consilient/x.py"], live, cwd=tmp_path
    )
    assert hit is not None
    assert hit[0].run_id == "run-win"
    assert (
        coordination.conflict(["/mnt/c/Users/joe/repo/docs/x.md"], live, cwd=tmp_path)
        is None
    )


def test_a_claim_with_no_declared_paths_conflicts_with_nothing(tmp_path):
    log = tmp_path / "log"
    coordination.open_claim(
        log, run_id="run-3", paths=[], cwd=tmp_path, timeout_s=600, now=T0
    )
    live = _live(log, now=T0)
    assert len(live) == 1
    assert coordination.conflict(["anything/at/all.py"], live, cwd=tmp_path) is None


def test_open_claim_extra_may_not_restate_identity_or_authority(tmp_path):
    log = tmp_path / "log"
    with pytest.raises(EventError, match="may not override"):
        work_items.open_item(
            log,
            ticket="dispatch:x",
            accountable="consilient.dispatch",
            extra={"ticket": "dispatch:forged"},
        )
    with pytest.raises(EventError, match="may not override"):
        work_items.open_item(
            log,
            ticket="dispatch:x",
            accountable="consilient.dispatch",
            extra={"human_verdict": "accept"},
        )


# --- the bounded in-flight render -------------------------------------------


def test_render_in_flight_empty_is_explicit():
    text = coordination.render_in_flight((), now=T0)
    assert "No live dispatch claims" in text


def test_render_in_flight_is_bounded_and_counts_the_omitted(tmp_path):
    log = tmp_path / "log"
    for index in range(30):
        coordination.open_claim(
            log,
            run_id=f"run-{index:02d}",
            paths=[f"src/some/rather/long/path/number/{index:02d}/module.py"],
            cwd=tmp_path,
            timeout_s=3600,
            now=T0,
        )
    live = _live(log, now=T0)
    assert len(live) == 30
    text = coordination.render_in_flight(live, now=T0, limit_chars=1200)
    assert len(text) <= 1200
    assert "omitted" in text
    assert "run-00" in text  # earliest claims render first


def test_render_in_flight_rejects_an_absurd_limit():
    with pytest.raises(ValueError, match="limit_chars"):
        coordination.render_in_flight((), now=T0, limit_chars=0)


def test_render_in_flight_clamps_even_a_pathological_limit(tmp_path):
    """The degenerate case: no row fits, so only the clamp keeps the bound."""
    log = tmp_path / "log"
    coordination.open_claim(
        log,
        run_id="run-lone",
        paths=["src"],
        cwd=tmp_path,
        timeout_s=3600,
        now=T0,
    )
    live = _live(log, now=T0)
    text = coordination.render_in_flight(live, now=T0, limit_chars=60)
    assert len(text) <= 60


# --- model selection ----------------------------------------------------------


def test_models_are_registered_only_where_a_list_was_measured():
    assert models_for_harness("cursor-composer") == MODELS
    for harness_id in ("claude", "grok", "codex"):
        assert models_for_harness(harness_id) == ()


def test_select_model_picks_the_idlest_registered_pool():
    pools = (_pool("cursor-models", used=1.0), _pool("cursor-other", used=2.0))
    chosen = select_model("cursor-composer", pools=pools)
    assert not isinstance(chosen, str)
    assert chosen.id == "composer-2.5"  # registry order breaks the same-pool tie
    assert chosen.pool == "cursor-models"


def test_select_model_honours_a_family_request():
    pools = (_pool("cursor-models", used=1.0),)
    chosen = select_model("cursor-composer", pools=pools, family="grok")
    assert not isinstance(chosen, str)
    assert chosen.family == "grok"
    assert chosen.id == "cursor-grok-4.6-xhigh"


def test_select_model_never_falls_to_the_avoided_pool_on_its_own(tmp_path):
    """cursor-models exhausted is a refusal, not a quiet drift to cursor-other."""
    pools = (
        _pool("cursor-models", used=95.0, exhausted=True),
        _pool("cursor-other", used=3.0),
    )
    chosen = select_model("cursor-composer", pools=pools)
    assert isinstance(chosen, str)
    assert "exhausted or unmeasured" in chosen


def test_select_model_refuses_when_headroom_is_unknown():
    pools = (_pool("cursor-models", used=None),)
    chosen = select_model("cursor-composer", pools=pools)
    assert isinstance(chosen, str)


def test_select_model_treats_an_explicit_request_as_attended_naming():
    chosen = select_model("cursor-composer", pools=(), requested="claude-opus-5")
    assert not isinstance(chosen, str)
    assert chosen.id == "claude-opus-5"
    assert chosen.pool == "cursor-other"  # named, so the avoided pool is the operator's


def test_select_model_refuses_an_unknown_harness_or_family():
    assert isinstance(select_model("no-such", pools=()), str)
    refusal = select_model("cursor-composer", pools=(), family="no-such-family")
    assert isinstance(refusal, str)
    assert "known families" in refusal


def test_select_model_names_the_gap_when_a_harness_has_no_registered_models():
    refusal = select_model("grok", pools=DEFAULT_POOLS)
    assert isinstance(refusal, str)
    assert "no models registered" in refusal


def test_pool_for_model_is_registry_then_prefix_then_harness():
    assert pool_for_model("cursor-composer", "kimi-k3-max") == "cursor-models"
    assert pool_for_model("cursor-composer", "claude-opus-5") == "cursor-other"
    assert pool_for_model("grok", "anything") == "grok-weekly"
    assert pool_for_model("no-such", "anything") == "unknown"


def test_model_family_heuristic():
    assert model_family("cursor-grok-4.6-high") == "grok"
    assert model_family("composer-2.5") == "composer"
    assert model_family("Kimi-K3-Max") == "kimi"


# --- β-conditioned ceilings ----------------------------------------------------


def _measured_beta() -> Beta:
    # EXP-47's measured shape: point 0.3132 over [0.2926, 0.3346], 51 of 163.
    return Beta(MEASURED, None, None, 163, 51, 0.3132, (0.2926, 0.3346), None)


def test_ceiling_at_the_exp47_interval_is_one_at_epsilon_040():
    ceiling = routing.candidates_ceiling(_measured_beta(), 0.40)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 1
    assert ceiling.beta_used == pytest.approx(0.3346)  # the top of the interval


def test_ceiling_is_zero_below_beta_upper():
    ceiling = routing.candidates_ceiling(_measured_beta(), 0.3345)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 0


def test_ceiling_is_one_at_beta_upper():
    ceiling = routing.candidates_ceiling(_measured_beta(), 0.3346)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 1


def test_ceiling_does_not_round_up_at_a_float_boundary():
    beta = Beta(MEASURED, None, None, 30, 10, 1 / 3, (1 / 3, 1 / 3), None)
    epsilon = math.nextafter(1.0, -math.inf)
    ceiling = routing.candidates_ceiling(beta, epsilon)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 2


def test_ceiling_grows_above_beta_upper():
    ceiling = routing.candidates_ceiling(_measured_beta(), 0.70)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 2


def test_an_absent_beta_is_a_refusal_not_an_assumption():
    beta = Beta(INSUFFICIENT, None, None, 0, 0, None, None, None)
    outcome = routing.candidates_ceiling(beta, 0.20)
    assert isinstance(outcome, routing.RoutingRefusal)
    assert "fabricated" in outcome.reason


def test_epsilon_is_an_exposure_ceiling_and_must_be_in_the_open_unit_interval():
    for bad in (0.0, 1.0, 1.5, -0.1):
        with pytest.raises(ValueError, match="exposure ceiling"):
            routing.candidates_ceiling(_measured_beta(), bad)


def test_a_certain_bad_verifier_allows_zero_candidates():
    beta = Beta(MEASURED, None, None, 30, 30, 1.0, (1.0, 1.0), None)
    ceiling = routing.candidates_ceiling(beta, 0.99)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max == 0


def test_a_measured_zero_beta_states_the_arithmetic_not_a_licence():
    beta = Beta(MEASURED, None, None, 30, 0, 0.0, (0.0, 0.0), None)
    ceiling = routing.candidates_ceiling(beta, 0.20)
    assert isinstance(ceiling, routing.Ceiling)
    assert ceiling.n_attempt_max is None


def test_ceiling_for_the_real_shape_of_todays_trajectory_is_a_refusal(tmp_path):
    """An empty trajectory has zero human rejections, so the bridge refuses."""
    from consilient import projection

    log = tmp_path / "log"
    log.mkdir()
    conn = projection.build(log, tmp_path / "projection.db")
    conn.close()
    outcome = routing.ceiling_for_trajectory(log, tmp_path / "projection.db", 0.20)
    assert isinstance(outcome, routing.RoutingRefusal)


def test_the_routing_mechanism_is_built_but_not_wired():
    """The brief: build β-conditioned routing, leave it disabled. Disabled means no
    run-path importer — a statement in a docstring is not a check, so here is the
    check. If this fails, someone wired the ceiling into dispatch and this pinning
    test is where the conversation about whether that was authorised starts."""
    source = DISPATCH_PATH.read_text(encoding="utf-8")
    assert "routing" not in source
    assert "candidates_ceiling" not in source


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

    monkeypatch.setattr(script, "run_harness", forbidden)
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

    monkeypatch.setattr(script, "run_harness", fake_run)
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
    monkeypatch.setattr(script, "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(
        script,
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
    monkeypatch.setattr(script, "cursor_native", lambda: "cursor-agent")
    monkeypatch.setattr(
        script,
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

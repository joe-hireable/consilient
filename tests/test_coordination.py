"""The claim ledger: what a claim is, when it is live, and how it is shown.

These tests share one subject — a claim is a projection over the trajectory with a
clock, not a file — and each of the three parts here is a face of it.

Path canonicalisation comes first because it is what makes two spellings one claim. A
Windows path and its `/mnt/c` translation must canonicalise to the same string or the
overlap check is blind at exactly the boundary this machine straddles.
`coordination.DISPATCH_ACTOR` restates `harness.DISPATCH_ACTOR` because the product
capability allowlist forbids the import; the drift check for that restatement is here.

The lifecycle tests carry the crash-safety invariant. The stale `.budget.lock` measured
on this machine refuses forever after a SIGKILL because it is a file; a claim is
released by the passage of time alone, with no completion and no outcome required. BU-3
replaces the hour-plus-grace TTL with a 30 s fencing-token lease, so a killed holder is
reclaimable in one lease period rather than one run timeout — `timeout_s` is the run
bound, not the claim bound, and a one-hour run that dies must not hold the path for an
hour. The fencing rules follow Kleppmann: the resource rejects a token that has gone
backwards, while a renewal buys another lease without raising the epoch, which is Chubby
renewing the session rather than the sequencer. Claims that predate fencing project as
epoch 1; claims with no parseable expiry are declined rather than guessed at, because a
guessed expiry would resurrect them.

The bounded in-flight render sits with them because it is the read side of the same
projection — the summary dispatch embeds in a brief, clamped so thirty live claims
cannot blow the brief, and refusing an absurd limit rather than silently ignoring it.

Preserved from before the 28 August 2026 split, which rewrote this docstring and carried
the paragraph below into no sibling. It is reproduced WHOLE. An earlier restoration took
only the individual lines a checker had reported missing, which spliced halves of two
different sentences together beneath a claim of being verbatim -- found by an outside
review on 29 August 2026.

    The invariants under test are the ones the brief named:

    - a second dispatch claiming an overlapping path is refused;
    - a crashed dispatcher cannot hold a claim forever (expiry is read from the event,
      so the passage of time alone releases it — no lock file to go stale);
    - automatic model selection never drifts to the avoided cursor-other pool;
    - routing on an absent β refuses rather than assumes.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from consilient import coordination, work_items
from consilient.events import EventError
from consilient.harness import (
    harness_by_id,
)
from coordination_helpers import (
    T0,
    _live,
)

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
    live = _live(log, now=T0)
    assert [c.run_id for c in live] == ["run-1"]
    assert live[0].fencing_epoch == 1
    coordination.close_claim(log, run_id="run-1")
    assert _live(log, now=T0) == ()


def test_open_claim_without_lease_s_keeps_timeout_plus_grace(tmp_path):
    """The historical bound stays until dispatch and the commit-gate clock fixture move."""
    log = tmp_path / "log"
    coordination.open_claim(
        log, run_id="run-legacy-ttl", paths=["src"], cwd=tmp_path, timeout_s=60, now=T0
    )
    grace = coordination.CLAIM_GRACE_S
    assert _live(log, now=T0 + timedelta(seconds=60 + grace - 1)) != ()
    assert _live(log, now=T0 + timedelta(seconds=60 + grace + 1)) == ()


def test_a_crashed_dispatchers_claim_expires_on_its_own(tmp_path):
    """The crash-safety invariant: no completion, no outcome, just the clock.

    The stale `.budget.lock` measured on this machine refuses forever after a
    SIGKILL because it is a file. A claim is a projection with a clock, so the
    passage of time alone releases it. BU-3 replaces the hour-plus-grace TTL
    with a 30 s fencing-token lease, so a killed holder is reclaimable in one
    lease period rather than one run timeout.
    """
    log = tmp_path / "log"
    coordination.open_claim(
        log,
        run_id="run-dies",
        paths=["src"],
        cwd=tmp_path,
        timeout_s=3600,
        now=T0,
        lease_s=coordination.LEASE_TTL_S,
    )
    ttl = coordination.LEASE_TTL_S
    assert _live(log, now=T0 + timedelta(seconds=ttl - 1)) != ()
    assert _live(log, now=T0 + timedelta(seconds=ttl + 1)) == ()


def test_a_killed_dispatch_claim_is_reclaimable_within_thirty_seconds(tmp_path):
    """BU-3: a killed dispatch's claim is reclaimable in ≤30 s.

    timeout_s is the run bound, not the claim bound. A one-hour run that dies
    must not hold the path for an hour.
    """
    log = tmp_path / "log"
    coordination.open_claim(
        log,
        run_id="run-killed",
        paths=["src/consilient/coordination.py"],
        cwd=tmp_path,
        timeout_s=3600,
        now=T0,
        lease_s=coordination.LEASE_TTL_S,
    )
    held = [c.fencing_epoch for c in _live(log, now=T0)]
    assert held == [1]
    at_deadline = T0 + timedelta(seconds=coordination.LEASE_TTL_S)
    assert _live(log, now=at_deadline) == ()
    hit = coordination.conflict(
        ["src/consilient/coordination.py"], _live(log, now=at_deadline), cwd=tmp_path
    )
    assert hit is None
    coordination.open_claim(
        log,
        run_id="run-reclaim",
        paths=["src/consilient/coordination.py"],
        cwd=tmp_path,
        timeout_s=3600,
        now=at_deadline,
        lease_s=coordination.LEASE_TTL_S,
    )
    reclaimed = _live(log, now=at_deadline)
    assert [c.run_id for c in reclaimed] == ["run-reclaim"]
    assert reclaimed[0].fencing_epoch == 2


def test_a_displaced_writer_is_rejected_on_a_stale_epoch(tmp_path):
    """BU-3 / Kleppmann: the resource rejects a token that has gone backwards."""
    log = tmp_path / "log"
    first = coordination.open_claim(
        log,
        run_id="run-old",
        paths=["src"],
        cwd=tmp_path,
        timeout_s=3600,
        now=T0,
        lease_s=coordination.LEASE_TTL_S,
    )
    stale = first["data"]["fencing_epoch"]
    assert stale == 1
    live = _live(log, now=T0)
    assert coordination.admit_write(token=stale, claim=live[0]) is live[0]
    deadline = T0 + timedelta(seconds=coordination.LEASE_TTL_S)
    coordination.open_claim(
        log,
        run_id="run-new",
        paths=["src"],
        cwd=tmp_path,
        timeout_s=3600,
        now=deadline,
        lease_s=coordination.LEASE_TTL_S,
    )
    current = _live(log, now=deadline)
    assert current[0].fencing_epoch == 2
    with pytest.raises(coordination.StaleEpoch, match="behind live epoch 2"):
        coordination.admit_write(token=stale, claim=current[0])
    assert coordination.admit_write(token=2, claim=current[0]) is current[0]


def test_renew_claim_extends_the_lease_without_raising_the_epoch(tmp_path):
    """A live holder buys another 30 s; Chubby renews the session, not the sequencer."""
    log = tmp_path / "log"
    coordination.open_claim(
        log,
        run_id="run-live",
        paths=["src"],
        cwd=tmp_path,
        timeout_s=3600,
        now=T0,
        lease_s=coordination.LEASE_TTL_S,
    )
    mid = T0 + timedelta(seconds=coordination.LEASE_TTL_S - 1)
    coordination.renew_claim(log, run_id="run-live", token=1, cwd=tmp_path, now=mid)
    after_first_lease = T0 + timedelta(seconds=coordination.LEASE_TTL_S + 1)
    live = _live(log, now=after_first_lease)
    assert [c.run_id for c in live] == ["run-live"]
    assert live[0].fencing_epoch == 1
    with pytest.raises(coordination.StaleEpoch):
        coordination.renew_claim(
            log, run_id="run-live", token=0, cwd=tmp_path, now=after_first_lease
        )


def test_a_claim_without_an_epoch_projects_as_epoch_one(tmp_path):
    """Historical claims predate fencing tokens; they remain live at epoch 1."""
    from consilient.events import SCHEMA_VERSION, append

    log = tmp_path / "log"
    log.mkdir()
    now = datetime.now(timezone.utc)
    ts = now.isoformat()
    append(
        log / f"{ts[:10]}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": ts,
            "event": work_items.OPENED,
            "actor": "consilient.dispatch",
            "data": {
                "ticket": "dispatch:legacy",
                "accountable": "consilient.dispatch",
                "run_id": "legacy",
                "paths": ["src"],
                "cwd": str(tmp_path),
                "opened_at": ts,
                "expires_at": (now + timedelta(seconds=60)).isoformat(),
            },
        },
    )
    live = _live(log, now=now + timedelta(seconds=1))
    assert len(live) == 1
    assert live[0].fencing_epoch == 1


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

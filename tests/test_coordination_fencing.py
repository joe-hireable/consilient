"""Exactly one lease, and an epoch that never goes backwards.

The first three tests are the F02 atomicity property at the trajectory writer. Two
spellings of the same file — the Windows path and its `/mnt/c` translation — yield one
lease and one `ClaimConflict`, and two threads racing for the same path produce exactly
one `ok` and one `conflict`. Disjoint paths are independent, each starting at epoch 1,
because the epoch is per path and not global.

The rest is the day-boundary regression of 25 August 2026, and it is worth stating in
full because the failure was not obvious. `open_claim` derives the epoch from
`read_all(log)`, which reads every day file. The F02 append transaction validated it
against the locked prefix — one file, the day being appended to. While every claim lived
in the same day file the two agreed. At midnight the log rolled, the new day's file held
no earlier claim, the expectation collapsed to 1, and every dispatch that had
legitimately computed a higher epoch from the real history was refused as stale. 26
units reached the retry cap this way and dispatch stopped.

Equality was never the safety property. A token that outranks by more than the minimum
is still monotone; only a token that is *behind* is unsafe. So an epoch ahead of the
locked prefix is admitted, an epoch behind it is still refused — the negative control —
and the epoch climbs past expired claims, because an expired holder can wake and write,
and the next lease must still outrank it."""

from datetime import timedelta
from pathlib import Path
import pytest
from consilient import coordination
from consilient.events import Event, EventError
from coordination_helpers import (
    T0,
    _live,
)


def test_overlapping_open_claims_admit_exactly_one_lease(tmp_path):
    """Two Windows/WSL spellings of the same path yield one lease under F02."""
    log = tmp_path / "log"
    coordination.open_claim(
        log,
        run_id="win",
        paths=["C:\\Users\\joe\\repo\\src\\a.py"],
        cwd=Path("C:/Users/joe/repo"),
        timeout_s=600,
        now=T0,
    )
    with pytest.raises(coordination.ClaimConflict):
        coordination.open_claim(
            log,
            run_id="wsl",
            paths=["/mnt/c/Users/joe/repo/src/a.py"],
            cwd=tmp_path,
            timeout_s=600,
            now=T0,
        )
    live = _live(log, now=T0)
    assert [claim.run_id for claim in live] == ["win"]
    assert live[0].fencing_epoch == 1


def test_concurrent_overlapping_open_claims_admit_exactly_one(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    log = tmp_path / "log"

    def claim(run_id: str) -> str:
        try:
            coordination.open_claim(
                log,
                run_id=run_id,
                paths=["src/shared.py"],
                cwd=tmp_path,
                timeout_s=600,
                now=T0,
            )
            return "ok"
        except coordination.ClaimConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, ("left", "right")))
    assert results.count("ok") == 1
    assert results.count("conflict") == 1
    assert len(_live(log, now=T0)) == 1


def test_disjoint_claims_receive_independent_fencing_epochs(tmp_path):
    log = tmp_path / "log"
    first = coordination.open_claim(
        log, run_id="a", paths=["src/a.py"], cwd=tmp_path, timeout_s=600, now=T0
    )
    second = coordination.open_claim(
        log, run_id="b", paths=["src/b.py"], cwd=tmp_path, timeout_s=600, now=T0
    )
    assert first["data"]["fencing_epoch"] == 1
    assert second["data"]["fencing_epoch"] == 1
    assert len(_live(log, now=T0)) == 2


# --- fencing epoch across a day boundary, 25 August 2026 -----------------------
#
# `open_claim` derives the epoch from `read_all(log)`, which reads EVERY day file. The F02
# append transaction validates it against `_read_under_lock(path, fd)` -- ONE file, the day
# being appended to. While every claim lived in the same day file the two agreed. At midnight
# the log rolled, the new day's file held no earlier claim, the expectation collapsed to 1, and
# every dispatch that had legitimately computed a higher epoch from the real history was
# refused as stale. 26 units reached the retry cap this way and dispatch stopped.
#
# Equality was never the safety property: a token that outranks by more than the minimum is
# still monotone. Only a token that is BEHIND is unsafe.


def _claim_payload(tmp_path, *, run_id, epoch, at):
    return coordination._claim_event_payload(
        run_id=run_id,
        paths=[coordination.canonical_path("src", cwd=tmp_path)],
        cwd=tmp_path,
        opened=at,
        expires=at + timedelta(seconds=coordination.LEASE_TTL_S),
        fencing_epoch=epoch,
        harness=None,
        task=None,
    )


def test_an_epoch_ahead_of_the_locked_prefix_is_admitted(tmp_path):
    """The exact regression that stopped dispatch.

    The locked prefix is the day file being appended to. On a fresh day it is EMPTY, so the
    expectation is 1 -- while the client, reading the whole trajectory, correctly computed 4.
    That must be admitted: 4 outranks everything in scope, which is the fencing property.
    """
    coordination._validate_dispatch_claim_admission(
        (),
        (),
        (_claim_payload(tmp_path, run_id="run-next-day", epoch=4, at=T0),),
        cwd=tmp_path,
        now=T0,
    )


def test_an_epoch_behind_the_locked_prefix_is_still_refused(tmp_path):
    """Negative control: the safety property is that a token may not be BEHIND."""
    held = _claim_payload(tmp_path, run_id="run-holder", epoch=2, at=T0)
    expired = T0 + timedelta(seconds=coordination.LEASE_TTL_S + 5)
    with pytest.raises(EventError, match="is stale"):
        coordination._validate_dispatch_claim_admission(
            (Event(held),),
            (),
            (_claim_payload(tmp_path, run_id="run-behind", epoch=1, at=expired),),
            cwd=tmp_path,
            now=expired,
        )


def test_the_epoch_climbs_past_expired_claims(tmp_path):
    """An expired holder can wake and write, so the next lease must still outrank it."""
    log = tmp_path / "log"
    for index, run in enumerate(("run-a", "run-b", "run-c")):
        event = coordination.open_claim(
            log,
            run_id=run,
            paths=["src"],
            cwd=tmp_path,
            timeout_s=3600,
            now=T0 + timedelta(seconds=index * (coordination.LEASE_TTL_S + 5)),
            lease_s=coordination.LEASE_TTL_S,
        )
    assert event["data"]["fencing_epoch"] == 3, event["data"]["fencing_epoch"]

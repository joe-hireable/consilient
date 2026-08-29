"""A finished dispatch gives its slot back, however it ended.

Independent lanes are worthless if entries never leave them. Builds expired on
`(started, leash)` in `in_flight`; resolves and reviews recorded a name and nothing
else, so there was no fact to expire against and both leaked. Three buckets, one lesson,
learned twice more than it should have been.

MEASURED 27 August 2026: 34 `resolve_dispatched` entries against roughly nine live
dispatch processes in total, builds and reviews included — the bucket was only ever
emptied on the unit's conflict clearing or on `crashed_dispatches` finding the run dead,
so a resolver that ran, failed and exited CLEANLY matched neither and stayed for ever,
barring its unit from re-dispatch. The review lane was worse and it was the largest
brake on the pipeline: four entries whose newest output was 36, 36, 45 and 50 HOURS old
against a lane capped at six, so two thirds of the lane was held by runs that had ended
two days earlier while 76 units waited for a verdict.

`crashed_dispatches` could not see any of it. It defines death as `<stem>.err` carrying
a traceback, which finds a dispatch that crashed and never one that simply stopped
existing — killed, cut off with the machine, or exited quietly. An empty `.err` reads
exactly like a healthy run. Time is the signal that does not depend on the dead process
having written its own death certificate, and the grace used here is deliberately the
same 300s past the leash that `crashed_dispatches` uses, so the two cannot disagree
about whether a run is over.

Adoption is the careful half. An entry recorded before start times existed has nothing
to expire against, so the artefact is asked first: 38 such entries had output 32 hours
old for resolves and 50 for reviews, and a blind adoption at `now` would have held every
one of those slots for a further full leash. Where the artefact says nothing at all,
unknown is not known-dead and the entry gets a leash to prove itself, because cancelling
a live run is worse than waiting one leash for certainty. Where the artefact is older
than the recorded start — the one direction that is physically impossible — the guess is
what gives way. From Y02: stopping the retries is right, leaking the capacity is not."""

import os
from driver_bulkhead_helpers import (
    _load_driver,
)


def test_a_finished_resolver_releases_its_slot_however_it_ended() -> None:
    """MEASURED 27 August 2026: 34 `resolve_dispatched` entries against roughly nine live
    dispatch processes in total, builds and reviews included.

    The bucket was only ever emptied on two paths -- the unit's conflict clearing, or
    `crashed_dispatches` finding the run dead. A resolver that ran, failed to fix the conflict
    and exited CLEANLY matched neither, so its entry stayed for ever. Every one of those units
    was then permanently barred from re-dispatch by `uid in resolving`, and once resolvers began
    counting against their own lane the stale entries alone exceeded MAX_BUILDS: the loop broke
    before examining anything, so even the two units that genuinely needed a resolver got none.

    This file already states the lesson, from Y02: stopping the retries is right, leaking the
    capacity is not.
    """
    driver = _load_driver()
    now = 1_000_000.0
    state = {
        "resolve_dispatched": ["OLD", "FRESH", "ADOPTED"],
        "resolve_started": {
            "OLD": [now - 3600 - 301, 3600],
            "FRESH": [now - 10, 3600],
        },
    }

    expired = driver.expire_finished_dispatches(state, now=now)

    assert expired == ["OLD"], expired
    assert state["resolve_dispatched"] == ["FRESH", "ADOPTED"]
    # An entry with no start time is UNKNOWN, not known-dead. Reaping it immediately would
    # cancel a resolver that may be doing real work, so it is adopted at `now` and expires on
    # its own leash from here.
    assert state["resolve_started"]["ADOPTED"][0] == now
    assert state["resolve_started"]["ADOPTED"][1] == driver.RESOLVE_ADOPTED_LEASH_S
    # A slow-but-living resolver is never reaped out from under itself.
    assert "FRESH" in state["resolve_dispatched"]


def test_expiry_grace_matches_the_crash_detector() -> None:
    """A dispatch is not late until its leash plus 300s has passed -- the same grace
    `crashed_dispatches` uses, so the two cannot disagree about whether a run is over."""
    driver = _load_driver()
    now = 1_000_000.0
    just_inside = {
        "resolve_dispatched": ["U"],
        "resolve_started": {"U": [now - 3600 - 299, 3600]},
    }
    assert driver.expire_finished_dispatches(just_inside, now=now) == []
    just_outside = {
        "resolve_dispatched": ["U"],
        "resolve_started": {"U": [now - 3600 - 301, 3600]},
    }
    assert driver.expire_finished_dispatches(just_outside, now=now) == ["U"]


def test_a_review_slot_is_released_when_its_dispatch_is_over() -> None:
    """MEASURED 27 August 2026, and this was the largest brake on the pipeline.

    `review_dispatched` held four entries whose newest output was 36, 36, 45 and 50 HOURS old,
    against a lane capped at six. Two thirds of the review lane was held by runs that had ended
    two days earlier while 76 units waited for a verdict -- and the review lane is what decides a
    unit, so nothing could move.

    `crashed_dispatches` could not see them. It defines death as `<stem>.err` carrying a
    traceback, which finds a dispatch that CRASHED and never one that simply stopped existing:
    killed, cut off with the machine, or exited quietly. An empty `.err` reads exactly like a
    healthy run. Time is the signal that does not depend on the dead process having written its
    own death certificate.
    """
    driver = _load_driver()
    now = 1_000_000.0
    state = {
        "review_dispatched": ["TWO_DAYS_DEAD", "RUNNING"],
        "review_started": {
            "TWO_DAYS_DEAD": [now - (50 * 3600), 3600],
            "RUNNING": [now - 60, 3600],
        },
    }

    expired = driver.expire_finished_dispatches(
        state, "review_dispatched", "review_started", now=now
    )

    assert expired == ["TWO_DAYS_DEAD"], expired
    assert state["review_dispatched"] == ["RUNNING"], (
        "a live review was reaped out from under itself"
    )


def test_every_dispatch_bucket_has_an_expiry() -> None:
    """Builds expired on `(started, leash)` in `in_flight`; resolves and reviews recorded a name
    and nothing else, so there was no fact to expire against and both leaked -- resolves for up
    to 32 hours, reviews for up to 50. Three buckets, one lesson, learned twice more than it
    should have been. The driver must record a start time wherever it records a dispatch."""
    import inspect

    driver = _load_driver()
    source = inspect.getsource(driver.main)
    assert '"resolve_started"' in source or "resolve_started" in source, (
        "resolves record no start time"
    )
    assert "review_started" in source, "reviews record no start time"
    assert source.count("expire_finished_dispatches(") == 2, (
        "both leaking buckets must be expired every tick"
    )


def test_adoption_asks_the_artefact_before_holding_a_slot(
    tmp_path, monkeypatch
) -> None:
    """An entry recorded before start times existed has no time to expire against. Asking the
    dispatch's own output is better than guessing either way.

    MEASURED 27 August 2026: 38 such entries, whose newest output was 32 hours old for resolves
    and 50 for reviews. A blind adoption at `now` would have held every one of those slots for a
    further full leash on runs that had been over for two days.

    Where the artefact says nothing at all, adoption is still the safe answer: unknown is not
    known-dead, and cancelling a live run is worse than waiting one leash for certainty.
    """
    driver = _load_driver()
    monkeypatch.setattr(driver, "BRIEFS", tmp_path)
    now = 1_000_000.0

    long_dead = tmp_path / "DEAD-resolve.out"
    long_dead.write_text("output from two days ago", encoding="utf-8")

    old = now - (50 * 3600)
    os.utime(long_dead, (old, old))

    recent = tmp_path / "BUSY-resolve.out"
    recent.write_text("still writing", encoding="utf-8")
    os.utime(recent, (now - 30, now - 30))

    state = {"resolve_dispatched": ["DEAD", "BUSY", "SILENT"], "resolve_started": {}}
    expired = driver.expire_finished_dispatches(state, now=now)

    assert expired == ["DEAD"], expired
    assert state["resolve_dispatched"] == ["BUSY", "SILENT"]
    # BUSY wrote recently, so it is adopted rather than reaped.
    assert "BUSY" in state["resolve_started"]
    # SILENT never wrote at all: unknown, not known-dead, so it gets a leash to prove itself.
    assert "SILENT" in state["resolve_started"]
    assert state["resolve_started"]["SILENT"][0] == now


def test_the_artefact_beats_an_adopted_start_time(tmp_path, monkeypatch) -> None:
    """A dispatch cannot have last written output before it started.

    MEASURED 27 August 2026: the first tick to run this reaper stamped 34 resolve entries at
    `now`, before the artefact check existed. They then read as "started 47 minutes ago" while
    their own output was 32 HOURS old -- and would have held their slots for a further full leash
    on the strength of a timestamp the reaper itself had invented.

    An adopted start is a guess. The artefact is evidence. Where they disagree in the only
    direction that is physically impossible, the guess is what gives way.
    """
    driver = _load_driver()
    monkeypatch.setattr(driver, "BRIEFS", tmp_path)

    now = 1_000_000.0
    out = tmp_path / "ADOPTED-resolve.out"
    out.write_text("last wrote 32 hours ago", encoding="utf-8")
    old = now - (32 * 3600)
    os.utime(out, (old, old))

    state = {
        "resolve_dispatched": ["ADOPTED"],
        # exactly the shape a blind adoption leaves behind
        "resolve_started": {"ADOPTED": [now - (47 * 60), 3600]},
    }
    assert driver.expire_finished_dispatches(state, now=now) == ["ADOPTED"]
    assert state["resolve_dispatched"] == []


def test_a_real_dispatch_is_still_judged_on_its_own_start(
    tmp_path, monkeypatch
) -> None:
    """The override must only fire in the impossible direction. A genuine dispatch that started
    ten minutes ago and wrote output two minutes ago has an artefact NEWER than its start, so its
    recorded start stands and it is not reaped."""
    driver = _load_driver()
    monkeypatch.setattr(driver, "BRIEFS", tmp_path)

    now = 1_000_000.0
    out = tmp_path / "LIVE-resolve.out"
    out.write_text("still going", encoding="utf-8")
    os.utime(out, (now - 120, now - 120))

    state = {
        "resolve_dispatched": ["LIVE"],
        "resolve_started": {"LIVE": [now - 600, 3600]},
    }
    assert driver.expire_finished_dispatches(state, now=now) == []
    assert state["resolve_dispatched"] == ["LIVE"]

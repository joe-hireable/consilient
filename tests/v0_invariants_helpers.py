"""Fixtures the v0 invariant families share — the event builders, the two live-
trajectory readers, and the payload runners that more than one family needs. Three of
them carry their own forensic record, kept here rather than lost with the split.
`now_ts` exists because the fixtures used to hardcode "2026-08-20T01:00:00+01:00", which
is exactly the shape `_check_clock` now forbids — a timestamp asserted rather than read.
`outcome` used to attach a `human_verdict` to an event with `actor="agent"` and no
principal, and every test passed, so the fixture was modelling the forgery V0-18 forbids
as valid. `doctor_payload` asserted `code == 0` until 21 August 2026 against a command
that returned 0 unconditionally because `cmd_doctor`'s result carries no `identical`
key; it could not fail, and it pinned that defect across every doctor test in the file.
`_read_live_trajectory` skips only on an access denial: MEASURED 24 August 2026, reads
of the 46 MB trajectory take 0.55–0.81s and succeeded twelve times out of twelve in a
quiet moment, while a write burst during one suite run produced four simultaneous
failures in tests that had passed twice within the hour — an access denial is
infrastructure, not evidence about drift. Nothing here asserts an invariant; every file
that imports these does."""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from consilient import events as events_mod
from consilient import projection
from consilient.cli import build_parser, main
from consilient.events import (
    SCHEMA_VERSION,
    EventError,
    append,
    canonical,
    read_all,
)


def now_ts(offset_s=0):
    """A timestamp from the clock, which is what an appended event must carry.

    The fixtures used to hardcode "2026-08-20T01:00:00+01:00". That is exactly the shape
    `_check_clock` now forbids — a timestamp asserted rather than read — so hardcoding it
    here would have taught the suite that the forbidden thing is normal, which is the same
    mistake the `outcome()` helper made about human verdicts.
    """
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def ev(**over):
    base = {
        "v": SCHEMA_VERSION,
        "ts": now_ts(),
        "event": "test.event",
        "actor": "agent",
        "data": {},
    }
    base.update(over)
    return base


HUMAN = "joe-brown"


def outcome(
    attempt_id,
    task,
    accept,
    family="repair",
    version="v1",
    ts=None,
):
    """An agent outcome that cannot carry a human verdict.

    This helper used to attach a `human_verdict` to an event with `actor="agent"` and no
    principal, and every test passed. That is precisely the forgery V0-18 forbids, so the
    fixture was modelling an invalid event as valid. Identity is a separate required
    argument from task because several attempts may legitimately belong to the same task.
    """
    ts = ts or now_ts()
    data = {
        "attempt_id": attempt_id,
        "task": task,
        "verifier_accept": accept,
        "task_family": family,
        "verifier_version": version,
    }
    return ev(ts=ts, event=projection.OUTCOME_KIND, data=data)


def verdict(attempt_id, human_verdict, ts=None):
    """A human verdict fixture whose actor cannot be changed to an agent."""
    return ev(
        ts=ts or now_ts(),
        actor=HUMAN,
        event=projection.VERDICT_KIND,
        data={
            "attempt_id": attempt_id,
            "human_verdict": human_verdict,
            "principal": HUMAN,
            "via": "cli",
        },
    )


def append_judged(path, attempt_id, task, accept, human_verdict):
    append(path, outcome(attempt_id, task, accept))
    append(path, verdict(attempt_id, human_verdict))


def write_capture_days(log_dir, *days):
    log_dir.mkdir(parents=True, exist_ok=True)
    for day in days:
        (log_dir / f"{day}.jsonl").write_text(
            canonical(ev(ts=f"{day}T12:00:00+00:00")) + "\n",
            encoding="utf-8",
        )


def doctor_payload(tmp_path, capsys):
    parser = build_parser()
    subparsers = next(
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    )
    assert "doctor" in subparsers.choices, "doctor command is missing"
    code = main(
        [
            "--log",
            str(tmp_path / "log"),
            "--db",
            str(tmp_path / "state.db"),
            "--json",
            "doctor",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    # This asserted `code == 0` until 21 Aug 2026, against a command that returned 0
    # unconditionally because `cmd_doctor`'s result carries no `identical` key. It could not
    # fail, and it pinned that defect across every doctor test in this file. The exit code
    # must now agree with the payload printed beside it.
    assert code == (0 if payload["routing_orchestration_enabled"] else 1), (
        f"doctor exited {code} while routing_orchestration_enabled is "
        f"{payload['routing_orchestration_enabled']}"
    )
    return payload


def _read_live_trajectory(log):
    """Read the repository's own trajectory, or skip if it is momentarily unreadable.

    These ratchets check the LIVE log while as many as 36 dispatchers append to it, and on
    Windows a writer denies every reader for as long as it holds the file.

    MEASURED 24 August 2026: reads of the 46 MB trajectory take 0.55-0.81s and succeeded 12
    times out of 12 in a quiet moment, but a write burst during one suite run produced four
    simultaneous failures in tests that had passed twice within the hour.

    An access denial is INFRASTRUCTURE, not evidence -- the same distinction the driver already
    makes for a crashed dispatch (F-05: "an infrastructure death is not evidence about the
    work"). Failing here is a false alarm about drift, and it is an expensive one, because a red
    suite blocks retirement, merging and publication at the same time.

    This skips ONLY on a denial. A trajectory that reads cleanly and HAS drifted still fails,
    which is the whole point of these ratchets, and a denial that persists shows up as a skip
    in every run rather than passing quietly.
    """
    return _against_live_trajectory(read_all, log)


def _against_live_trajectory(read, *args, **kwargs):
    """Run a read of the live trajectory, skipping only if it was denied access.

    Any denial reaching here has ALREADY exhausted the six jittered retries inside `events`,
    so this is not a second retry budget -- it is the decision about what an exhausted one
    means for a ratchet that is checking drift.
    """
    try:
        return read(*args, **kwargs)
    except EventError as exc:
        if "observed access denial" not in str(exc):
            raise
        pytest.skip(
            "the live trajectory was held by another process while this ratchet read it; "
            f"that is contention, not drift: {exc}"
        )


# ---------------------------------------------------------------- ADR-0045
def _gate_b(tmp_path, capsys):
    return {
        c["id"]: c for c in doctor_payload(tmp_path, capsys)["gates"]["B"]["conditions"]
    }


# ------------------------------------------- V0-29, V0-30, V0-20, V0-25 · the loop runtime
def _loop_runner():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_loop", Path("scripts/run_loop.py").resolve()
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _workspace(tmp_path):
    """A directory the loop will accept as a Consilient checkout, and its trajectory."""
    (tmp_path / "CONSILIENCE.md").write_text("marker\n", encoding="utf-8")
    return tmp_path, tmp_path / "log"


def _loop(tmp_path, *script, **over):
    from consilient.loop import Loop

    root, log = _workspace(tmp_path)
    settings = {
        "name": "probe",
        "root": root,
        "log_dir": log,
        "command": (sys.executable, "-c", *script),
        "interval_s": 0.0,
        "timeout_s": 60.0,
        "max_ticks": 1,
    }
    settings.update(over)
    return Loop(**settings)


def _loop_events(log, kind=None):
    events, rejected = _read_live_trajectory(log)
    assert not rejected, [r.reason for r in rejected]
    return [e for e in events if kind is None or e.kind == kind]


# ---------------------------------------------------------------- V0-39
# ADR-0056 D5: On-Demand Spending stays Disabled and only the principal may change that.
# It is the one control by which this system could spend real money, so it ships with a lint
# rule rather than a convention (I1). The tests below are the rule's own check.
_spend_scripts = str(Path(__file__).resolve().parent.parent / ".github" / "scripts")

if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)


def budget_state_event(weekly, monthly):
    stamp = datetime.now(timezone.utc)
    return {
        "v": SCHEMA_VERSION,
        "ts": stamp.isoformat(),
        "event": "budget.state",
        "actor": "openrouter-probe",
        "data": {
            "provider": "openrouter",
            "currency": "USD",
            "weekly_spent": weekly,
            "monthly_spent": monthly,
            "observed_at": stamp.isoformat(),
            "rejection_digest": events_mod.rejection_digest([]),
        },
    }


def write_budget_state(log, weekly, monthly):
    log.mkdir(parents=True, exist_ok=True)
    name = f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    append(log / name, budget_state_event(weekly, monthly))

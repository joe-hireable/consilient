"""Checks for the invariants the observe-only increment declares.

Every test names the invariant it enforces. Invariant I1: a declared chokepoint ships with
the check that bans bypassing it, in the same commit.
"""

import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilience import beta as beta_mod
from consilience import events as events_mod
from consilience import projection
from consilience.cli import build_parser, main
from consilience.events import (
    SCHEMA_VERSION,
    EventError,
    append,
    canonical,
    prefix_digest,
    read,
    read_all,
    validate,
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
    task,
    accept,
    verdict=None,
    family="repair",
    version="v1",
    ts=None,
):
    """An outcome event, authored by the human when it carries their verdict.

    This helper used to attach a `human_verdict` to an event with `actor="agent"` and no
    principal, and every test passed. That is precisely the forgery V0-18 forbids, so the
    fixture was modelling an invalid event as valid — which is why no test caught the hole
    in `_check_human_authority`. A fixture that can express a forbidden state will teach a
    suite to accept it.
    """
    ts = ts or now_ts()
    data = {
        "task": task,
        "verifier_accept": accept,
        "task_family": family,
        "verifier_version": version,
    }
    if verdict is None:
        return ev(ts=ts, event=projection.OUTCOME_KIND, data=data)
    data["human_verdict"] = verdict
    data["principal"] = HUMAN
    data["via"] = "cli"
    return ev(ts=ts, actor=HUMAN, event=projection.OUTCOME_KIND, data=data)


# ---------------------------------------------------------------- V0-01
def test_unversioned_event_is_rejected():
    bad = ev()
    del bad["v"]
    with pytest.raises(EventError, match="missing required"):
        validate(bad)


def test_wrong_schema_version_is_rejected():
    with pytest.raises(EventError, match="unsupported schema version"):
        validate(ev(v=SCHEMA_VERSION + 1))


def test_naive_timestamp_is_rejected():
    with pytest.raises(EventError, match="explicit offset"):
        validate(ev(ts="2026-08-20T01:00:00"))


def test_append_never_changes_a_committed_position(tmp_path):
    log = tmp_path / "2026-08-20.jsonl"
    append(log, ev(event="first"))
    append(log, ev(event="second"))
    before = prefix_digest(log, 2)
    append(log, ev(event="third"))
    assert prefix_digest(log, 2) == before, "appending altered a committed position"


def test_in_place_edit_of_a_committed_position_is_detected(tmp_path):
    log = tmp_path / "2026-08-20.jsonl"
    append(log, ev(event="first"))
    append(log, ev(event="second"))
    before = prefix_digest(log, 2)
    lines = log.read_text(encoding="utf-8").splitlines()
    lines[0] = canonical(ev(event="tampered"))
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert prefix_digest(log, 2) != before


def test_a_malformed_line_is_quarantined_not_silently_skipped(tmp_path):
    """The refusal is reported, and the rest of the log survives it.

    This asserted `pytest.raises` until 20 Aug 2026. Raising made one bad line fatal to an
    append-only file nobody can edit, which is how three events appended at 09:41-09:56
    that day killed `replay` and `beta` on the real trajectory. The property that matters
    is "never silently skipped", not "always fatal": the line is excluded AND named.
    """
    log = tmp_path / "2026-08-20.jsonl"
    append(log, ev())
    with log.open("a", encoding="utf-8") as fh:
        fh.write("{not json}\n")
    events, rejected = read(log)
    assert len(events) == 1, "the valid event must survive its neighbour"
    assert len(rejected) == 1
    assert rejected[0].line == 2
    assert "not valid JSON" in rejected[0].reason


# ---------------------------------------------------------------- V0-18
def test_agent_cannot_author_a_human_decision():
    """The EXP-16 failure: a fabricated human-participation claim."""
    with pytest.raises(EventError, match="only the principal may author"):
        validate(
            ev(
                actor="claude-senior-orchestrator",
                data={
                    "human_decision": "approval",
                    "principal": "joe-brown",
                    "via": "remote control",
                },
            )
        )


def test_principal_alone_is_not_an_authority_grant():
    """`principal` names whose authority is exercised; it does not convert the author."""
    agent_event = ev(
        actor="codex-root", data={"principal": "joe-brown", "task": "anything"}
    )
    validate(agent_event)  # fine as an ordinary agent event
    with pytest.raises(EventError, match="only the principal may author"):
        validate(
            ev(
                actor="codex-root",
                data={
                    "principal": "joe-brown",
                    "human_decision": "gate_lift",
                    "via": "remote control",
                },
            )
        )


def test_human_authored_decision_is_accepted():
    validate(
        ev(
            actor="joe-brown",
            data={
                "human_decision": "approval",
                "principal": "joe-brown",
                "via": "remote control session, 2026-08-20",
            },
        )
    )


def test_human_decision_must_record_its_channel():
    with pytest.raises(EventError, match="must record `via`"):
        validate(
            ev(
                actor="joe-brown",
                data={"human_decision": "approval", "principal": "joe-brown"},
            )
        )


# ---------------------------------------------------------------- V0-02
def test_delete_and_replay_reproduces_identical_state(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    for i in range(5):
        append(path, outcome(f"t{i}", accept=bool(i % 2), verdict="reject"))

    first = projection.build(log_dir, db)
    digest = projection.state_digest(first)
    first.close()

    db.unlink()
    assert not db.exists()
    second = projection.build(log_dir, db)
    assert projection.state_digest(second) == digest
    second.close()


def test_projection_carries_no_state_the_log_lacks(tmp_path):
    """A row written straight into SQLite does not survive a rebuild."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append(log_dir / "2026-08-20.jsonl", outcome("t0", accept=True, verdict="reject"))
    conn = projection.build(log_dir, db)
    conn.execute(
        "INSERT INTO outcomes (position, ts, task, verifier_accept)"
        " VALUES (999, '2026-08-20T02:00:00+01:00', 'smuggled', 1)"
    )
    conn.commit()
    smuggled = projection.state_digest(conn)
    conn.close()

    rebuilt = projection.build(log_dir, db)
    assert projection.state_digest(rebuilt) != smuggled
    assert (
        rebuilt.execute(
            "SELECT COUNT(*) FROM outcomes WHERE task='smuggled'"
        ).fetchone()[0]
        == 0
    )
    rebuilt.close()


def test_malformed_outcome_fails_closed(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    bad = ev(
        event=projection.OUTCOME_KIND, data={"task": "t", "verifier_accept": "yes"}
    )
    append(log_dir / "2026-08-20.jsonl", bad)
    with pytest.raises(projection.ProjectionError, match="must be a boolean"):
        projection.build(log_dir, db)


def test_unknown_human_verdict_fails_closed_at_validation(tmp_path):
    """Since 20 Aug 2026 this fails one layer earlier than it used to.

    Closing the V0-18 hole meant `validate` had to look at `human_verdict`, so an unknown
    verdict is now refused before it can be written to the log at all, rather than when the
    projection is built from it. Stricter, and earlier.
    """
    with pytest.raises(EventError, match="human_verdict must be"):
        append(
            log_dir_unused := tmp_path / "log" / "2026-08-20.jsonl",
            outcome("t", accept=True, verdict="probably fine"),
        )
    assert not log_dir_unused.exists(), "a refused event must not reach the log"


def test_the_projection_still_fails_closed_on_an_unknown_verdict(tmp_path):
    """Defence in depth is only defence if the second layer is tested too.

    A log written by an older version, or by hand, can carry a verdict that today's
    `validate` would refuse. The projection must not accept it either.

    The mechanism changed on 20 Aug 2026 and the property did not. This used to assert
    that `build` raised. Raising kept the bad verdict out of β and threw away the good
    event beside it, and made any future tightening of `validate` retroactively fatal to
    the whole record. It now asserts what actually has to hold: the refused verdict never
    reaches the table β is computed from, and the refusal is visible rather than silent.
    Asserting the mechanism instead of the property is what made the old test look like
    protection it was not going to keep providing.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    good = outcome("t", accept=True, verdict="reject")
    append(path, good)
    smuggled = canonical(
        {**good, "data": {**good["data"], "human_verdict": "probably fine"}}
    )
    with path.open("a", encoding="utf-8") as fh:
        fh.write(smuggled + "\n")

    conn = projection.build(log_dir, db)
    verdicts = [r[0] for r in conn.execute("SELECT human_verdict FROM outcomes")]
    assert verdicts == ["reject"], "the refused verdict must not reach β's table"

    rejected = list(conn.execute("SELECT line, reason FROM rejections"))
    assert len(rejected) == 1, "and its refusal must be recorded, not dropped"
    assert rejected[0][0] == 2
    assert "human_verdict must be" in rejected[0][1]
    assert projection.rejection_count(conn) == 1
    conn.close()


def test_beta_reports_what_the_log_refused(tmp_path, capsys):
    """A rate computed over a quietly shortened denominator is the failure this measures.

    The quarantine is only not-a-silent-skip if it appears where the number appears.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, ev())
    with path.open("a", encoding="utf-8") as fh:
        fh.write("{not json}\n")
    main(["--json", "--log", str(log_dir), "--db", str(db), "beta"])
    assert json.loads(capsys.readouterr().out)["quarantined"] == 1


def test_no_new_event_may_bypass_append(tmp_path):
    """A ratchet on the real trajectory, not a fixture.

    `append` is the documented sole writer and the only place `validate` runs. On
    20 Aug 2026, 92 of 93 logged lines had been written straight to the file by something
    else — which is how three events V0-18 forbids reached an authoritative record whose
    only writer rejects them. That is working principle 3 (`AGENTS.md`) happening inside
    the artefact the principle was written about.

    History cannot be rewritten in an append-only log, so the counts below are the
    measured legacy baseline and may only ever go DOWN. A new bypass raises the count and
    fails here. Lowering these constants is the only permitted edit.
    """
    log = Path(".harness/log")
    if not log.exists():  # pragma: no cover - repository-only check
        pytest.skip("no repository trajectory in this checkout")
    assert len(events_mod.bypassed(log)) <= 92, (
        "a new event bypassed append(); write it with `consil record`"
    )
    _, rejected = read_all(log)
    assert len(rejected) <= 3, (
        "a new event was appended that the log refuses; see the quarantine in `consil replay`"
    )


# ---------------------------------------------------------------- V0-06
def test_beta_below_the_floor_is_insufficient_data_not_a_number():
    rows = [
        {
            "ts": "2026-08-20T01:00:00+01:00",
            "task_family": "repair",
            "verifier_version": "v1",
            "verifier_accept": True,
            "human_verdict": "reject",
        }
        for _ in range(5)
    ]
    result = beta_mod.compute(rows)
    assert result.verdict == beta_mod.INSUFFICIENT
    assert result.point is None and result.interval is None
    assert "insufficient data" in result.render()


def test_beta_carries_count_interval_and_window():
    rows = []
    for i in range(40):
        rows.append(
            {
                "ts": f"2026-08-{20 if i else 19}T01:00:00+01:00",
                "task_family": "repair",
                "verifier_version": "v1",
                "verifier_accept": i < 10,
                "human_verdict": "reject",
            }
        )
    result = beta_mod.compute(rows)
    assert result.verdict == beta_mod.MEASURED
    assert result.n_rejected == 40 and result.n_false_accept == 10
    assert result.point == pytest.approx(0.25)
    low, high = result.interval
    assert low < 0.25 < high
    assert result.window == ("2026-08-19T01:00:00+01:00", "2026-08-20T01:00:00+01:00")


def test_beta_declares_itself_a_lower_bound_on_a_joint_error():
    """Q30: the oracle is a test whose errors correlate with the ones it grades."""
    result = beta_mod.compute([])
    assert result.lower_bound_on_joint_error is True
    assert "non-stationary" in result.caveat


def test_unlabelled_artefacts_are_not_counted_as_agreement():
    rows = [
        {
            "ts": "2026-08-20T01:00:00+01:00",
            "verifier_accept": True,
            "human_verdict": None,
        }
        for _ in range(100)
    ]
    rows += [
        {
            "ts": "2026-08-20T01:00:00+01:00",
            "verifier_accept": True,
            "human_verdict": "reject",
        }
        for _ in range(3)
    ]
    result = beta_mod.compute(rows)
    assert result.n_rejected == 3, "unlabelled rows must not enter the denominator"
    assert result.verdict == beta_mod.INSUFFICIENT


def test_wilson_behaves_at_the_boundaries():
    low, high = beta_mod.wilson(0, 40)
    assert low == 0.0 and 0 < high < 0.2
    low, high = beta_mod.wilson(40, 40)
    assert high == 1.0 and 0.8 < low < 1.0


# ---------------------------------------------------------------- V0-14
def test_human_output_renders_the_same_result_as_json(tmp_path, capsys):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append(log_dir / "2026-08-20.jsonl", outcome("t0", accept=True, verdict="reject"))
    argv = ["--log", str(log_dir), "--db", str(db), "beta"]

    assert main(argv + ["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert main(argv) == 0
    human = capsys.readouterr().out.strip()

    assert str(payload["n_rejected"]) in human
    assert payload["verdict"] == "insufficient_data"
    assert "insufficient data" in human


def test_replay_command_reports_a_stable_digest(tmp_path, capsys):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    for i in range(3):
        append(
            log_dir / "2026-08-20.jsonl",
            outcome(f"t{i}", accept=True, verdict="reject"),
        )
    # Nothing on disk yet: the comparison has no subject, and must not claim a pass.
    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 1
    first = json.loads(capsys.readouterr().out)
    assert first["compared"] is False and first["identical"] is None
    assert first["events"] == 3

    # The first call left state behind, so the second has something to compare against.
    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["compared"] is True and payload["identical"] is True
    assert payload["events"] == 3 and payload["prior_digest"] == payload["digest"]


def test_replay_reports_divergence_when_the_state_on_disk_has_drifted(tmp_path, capsys):
    """The check the old implementation could not perform.

    It rebuilt from the log twice and compared the rebuilds -- identical by construction --
    after unlinking the very state whose drift it was meant to detect.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append(log_dir / "2026-08-20.jsonl", outcome("t0", accept=True, verdict="reject"))
    projection.build(log_dir, db).close()

    drifted = sqlite3.connect(db)
    drifted.execute(
        "INSERT INTO outcomes (position, ts, task, verifier_accept)"
        " VALUES (999, '2026-08-20T02:00:00+01:00', 'out-of-band', 1)"
    )
    drifted.commit()
    drifted.close()

    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["compared"] is True and payload["identical"] is False


def test_cli_rejects_an_invalid_event_with_a_nonzero_exit(tmp_path, capsys):
    bad = json.dumps(
        {
            "v": 99,
            "ts": "2026-08-20T01:00:00+01:00",
            "event": "x",
            "actor": "a",
            "data": {},
        }
    )
    code = main(["--log", str(tmp_path), "record", "--event", bad, "--json"])
    assert code == 2
    assert "unsupported schema version" in capsys.readouterr().err


# ---------------------------------------------------------------- scope
def test_the_cli_exposes_no_routing_or_blocking_surface():
    """Stage 3 needs Gate B. No command or flag here may route, block or accept.

    This inspects the parser surface rather than the help prose: the description
    legitimately contains "route" while saying the tool does not do it.
    """
    parser = build_parser()
    actions = {a.dest for a in parser._actions}
    subparsers = next(
        (a for a in parser._actions if isinstance(a, argparse._SubParsersAction)), None
    )
    assert subparsers is not None
    commands = set(subparsers.choices)
    for name, sub in subparsers.choices.items():
        actions |= {a.dest for a in sub._actions}

    assert commands == {"record", "replay", "beta"}, commands
    for forbidden in ("route", "dispatch", "block", "accept", "gate", "escalate"):
        offenders = {x for x in actions | commands if forbidden in x}
        assert not offenders, f"observe-only CLI exposes {offenders}"


def test_shared_options_survive_on_either_side_of_the_command(tmp_path, capsys):
    """argparse `parents=` lets a subparser default clobber an already-parsed value.

    Before this was fixed, `--log X replay` silently reverted to the default log
    directory and replayed the wrong trajectory.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append(log_dir / "2026-08-20.jsonl", outcome("t0", accept=True, verdict="reject"))
    projection.build(log_dir, db).close()  # give `replay` something to compare against

    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 0
    before = json.loads(capsys.readouterr().out)

    assert main(["replay", "--log", str(log_dir), "--db", str(db), "--json"]) == 0
    after = json.loads(capsys.readouterr().out)

    assert before["events"] == after["events"] == 1
    assert before["digest"] == after["digest"]


# --------------------------------------------- found by strict typing, not by the tests
def test_a_measured_beta_cannot_exist_without_its_interval():
    """`mypy --strict` found this; 24 passing tests did not.

    render() unpacked self.interval unconditionally, so a JSON round-trip carrying
    verdict=measured with a null interval crashed. The state is now unconstructable.
    """
    with pytest.raises(ValueError, match="must carry both a point estimate"):
        beta_mod.Beta(beta_mod.MEASURED, "repair", "v1", 40, 10, 0.25, None, None)


def test_insufficient_data_cannot_smuggle_a_point_estimate():
    with pytest.raises(ValueError, match="must not carry a point estimate"):
        beta_mod.Beta(beta_mod.INSUFFICIENT, None, None, 3, 1, 0.33, (0.1, 0.9), None)


def test_the_measured_render_path_is_exercised():
    """The gap that let the defect through: no test rendered a measured beta."""
    rows = [
        {
            "ts": "2026-08-20T01:00:00+01:00",
            "task_family": "repair",
            "verifier_version": "v1",
            "verifier_accept": i < 10,
            "human_verdict": "reject",
        }
        for i in range(40)
    ]
    line = beta_mod.compute(rows).render()
    assert "0.250" in line and "10/40" in line
    assert "lower bound on a joint" in line


# ------------------------------------------------- V0-18, the second path (20 Aug 2026)
# Beta is measured against the human verdict. If an agent can author that verdict, beta
# measures nothing. `_check_human_authority` returned early whenever `human_decision` was
# absent, while `projection._apply_outcome` read `human_verdict` directly -- a second path
# to a guarded state, which is the `jobboard-v2` failure this project was founded on.


def test_an_agent_cannot_author_a_human_verdict_by_omitting_human_decision():
    forged = ev(
        event=projection.OUTCOME_KIND,
        actor="claude-code-agent",
        data={"task": "t1", "verifier_accept": True, "human_verdict": "accept"},
    )
    with pytest.raises(EventError, match="must name its principal"):
        validate(forged)


def test_an_agent_cannot_author_a_human_verdict_by_naming_the_principal():
    """Naming whose authority is exercised is not the same as holding it."""
    forged = ev(
        event=projection.OUTCOME_KIND,
        actor="claude-code-agent",
        data={
            "task": "t1",
            "verifier_accept": True,
            "human_verdict": "accept",
            "principal": HUMAN,
            "via": "cli",
        },
    )
    with pytest.raises(EventError, match="only the principal may author"):
        validate(forged)


def test_a_human_verdict_must_record_the_channel_it_arrived_through():
    no_via = ev(
        event=projection.OUTCOME_KIND,
        actor=HUMAN,
        data={
            "task": "t1",
            "verifier_accept": True,
            "human_verdict": "accept",
            "principal": HUMAN,
        },
    )
    with pytest.raises(EventError, match="must record"):
        validate(no_via)


def test_a_human_verdict_may_not_be_filed_as_a_different_decision():
    mislabelled = ev(
        event=projection.OUTCOME_KIND,
        actor=HUMAN,
        data={
            "task": "t1",
            "verifier_accept": True,
            "human_verdict": "accept",
            "human_decision": "approval",
            "principal": HUMAN,
            "via": "cli",
        },
    )
    with pytest.raises(EventError, match="may not be filed as anything else"):
        validate(mislabelled)


def test_the_human_authored_verdict_is_accepted():
    """The guard must not also block the legitimate path."""
    validate(outcome("t1", True, "accept"))


# ------------------------------------------------------ V0-06, the constructor beneath
# `compute` enforced the sample floor. A floor is not an invariant if the constructor
# beneath it does not hold.


def test_a_measured_beta_cannot_be_constructed_below_the_evidence_floor():
    with pytest.raises(ValueError, match="at least 30 rejections"):
        beta_mod.Beta(beta_mod.MEASURED, None, None, 0, 0, 0.0, (0.0, 0.0), None)


def test_a_rate_outside_zero_to_one_is_refused():
    with pytest.raises(ValueError, match=r"must lie in \[0, 1\]"):
        beta_mod.Beta(beta_mod.MEASURED, None, None, 40, 10, 1.5, (0.0, 1.0), None)


def test_an_inverted_interval_is_refused():
    with pytest.raises(ValueError, match="0 <= low <= high <= 1"):
        beta_mod.Beta(beta_mod.MEASURED, None, None, 40, 10, 0.25, (0.9, 0.1), None)


def test_a_point_outside_its_own_interval_is_refused():
    with pytest.raises(ValueError, match="outside its own interval"):
        beta_mod.Beta(beta_mod.MEASURED, None, None, 40, 10, 0.9, (0.1, 0.4), None)


def test_more_false_accepts_than_rejections_is_refused():
    with pytest.raises(ValueError, match=r"must lie in \[0, n_rejected\]"):
        beta_mod.Beta(beta_mod.INSUFFICIENT, None, None, 3, 9, None, None, None)


def test_the_evidence_floor_can_be_raised_but_never_lowered():
    """A knob that can lower a floor is a bypass path around it."""
    with pytest.raises(ValueError, match="may only raise the floor"):
        beta_mod.compute([], min_rejections=0)


# ---------------------------------------------- V0-01, the clock (20 Aug 2026)
# `validate` checked the FORMAT of `ts` and its offset, both impeccable, and never asked
# whether the value was true. The orchestrator wrote six consecutive trajectory events with
# invented timestamps, drifting to 2h15m ahead of the wall clock, while documenting
# instrument-integrity defects in other people's work. A format check on a timestamp is not
# a check on a timestamp.


_stamp = now_ts


def test_an_invented_future_timestamp_is_refused_at_append(tmp_path):
    log = tmp_path / "2026-08-20.jsonl"
    with pytest.raises(EventError, match="from the current clock"):
        append(log, ev(ts=_stamp(3 * 3600)))
    assert not log.exists(), "a refused event must not reach the log"


def test_an_invented_past_timestamp_is_refused_at_append(tmp_path):
    log = tmp_path / "2026-08-20.jsonl"
    with pytest.raises(EventError, match="from the current clock"):
        append(log, ev(ts=_stamp(-3 * 3600)))


def test_a_truthful_timestamp_is_accepted(tmp_path):
    log = tmp_path / "2026-08-20.jsonl"
    append(log, ev(ts=_stamp(0)))
    assert len(read(log)[0]) == 1


def test_ordinary_delay_within_tolerance_is_accepted(tmp_path):
    """The check must not punish a slow write, only an invented one."""
    log = tmp_path / "2026-08-20.jsonl"
    append(log, ev(ts=_stamp(-60)))
    assert len(read(log)[0]) == 1


def test_reading_a_historical_log_does_not_depend_on_when_it_is_read():
    """The clock check belongs to append alone.

    `validate` runs on read. If it enforced skew, every log would become unreadable as it
    aged - the same failure the explicit-offset rule exists to prevent.
    """
    validate(ev(ts="2026-08-19T01:00:00+01:00"))


def test_a_log_that_has_grown_reads_as_stale_not_diverged(tmp_path, capsys):
    """Staleness is not drift.

    The first version of this comparison reported DIVERGED whenever the log had grown since
    the projection was last built, which on the real trajectory meant every ordinary run. A
    check that cries wolf is worse than no check, because it trains its reader to ignore it.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("t0", accept=True, verdict="reject"))
    projection.build(log_dir, db).close()

    append(path, outcome("t1", accept=False, verdict="accept"))

    # Exit 0 means the check ran AND passed. A stale run verified nothing, so it is not a
    # pass - but it is reported as STALE rather than DIVERGED, which is the distinction.
    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["stale"] is True
    assert payload["compared"] is False
    assert payload["identical"] is None
    assert payload["events_projected"] == 1 and payload["events"] == 2


def test_real_drift_is_still_caught_once_the_counts_match(tmp_path, capsys):
    """The narrowing must not have blunted the check it narrows."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append(log_dir / "2026-08-20.jsonl", outcome("t0", accept=True, verdict="reject"))
    projection.build(log_dir, db).close()

    drifted = sqlite3.connect(db)
    drifted.execute("UPDATE outcomes SET human_verdict = 'accept'")
    drifted.commit()
    drifted.close()

    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["stale"] is False
    assert payload["compared"] is True
    assert payload["identical"] is False


def test_a_forged_reject_is_the_variant_that_attacks_beta():
    """Which forgery actually moves the number, recorded because I first showed the wrong one.

    The V0-18 write-up demonstrated the bypass with a forged `human_verdict: "accept"`. That
    validates and projects, but `compute()` draws its denominator from rows where the verdict
    is "reject", so an accept row changes neither n nor k. The hole was real; the example did
    not bite. The forgery that attacks beta is a **reject** paired with `verifier_accept: True`,
    which lands in both numerator and denominator.
    """
    honest = [
        {
            "ts": now_ts(),
            "task_family": "repair",
            "verifier_version": "v1",
            "verifier_accept": i < 3,
            "human_verdict": "reject",
        }
        for i in range(30)
    ]
    base = beta_mod.compute(honest)
    assert base.verdict == beta_mod.MEASURED
    assert base.point == pytest.approx(3 / 30)

    forged_accept = honest + [
        {
            "ts": now_ts(),
            "task_family": "repair",
            "verifier_version": "v1",
            "verifier_accept": True,
            "human_verdict": "accept",
        }
    ]
    assert beta_mod.compute(forged_accept).point == pytest.approx(base.point), (
        "a forged accept moved beta; the original write-up would have been right by accident"
    )

    forged_reject = honest + [
        {
            "ts": now_ts(),
            "task_family": "repair",
            "verifier_version": "v1",
            "verifier_accept": True,
            "human_verdict": "reject",
        }
    ]
    attacked = beta_mod.compute(forged_reject)
    assert attacked.point == pytest.approx(4 / 31)
    assert attacked.point > base.point, "the forged reject failed to inflate beta"


def test_replay_preserves_state_that_is_both_stale_and_drifted(tmp_path, capsys):
    """The check must not destroy the evidence it just noticed.

    When state is behind the log AND independently drifted, `projection.build` would unlink it
    before anything compared it. Found by an external audit of the staleness repair.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("t0", accept=True, verdict="reject"))
    projection.build(log_dir, db).close()

    drifted = sqlite3.connect(db)
    drifted.execute("UPDATE outcomes SET human_verdict = 'accept'")
    drifted.commit()
    drifted.close()

    append(path, outcome("t1", accept=False, verdict="reject"))  # now stale as well

    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["stale"] is True and payload["compared"] is False
    assert payload["preserved_stale_state"], (
        "the drifted state was destroyed, not preserved"
    )
    assert Path(payload["preserved_stale_state"]).exists()

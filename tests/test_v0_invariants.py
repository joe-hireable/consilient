"""Checks for the invariants the observe-only increment declares.

Every test names the invariant it enforces. Invariant I1: a declared chokepoint ships with
the check that bans bypassing it, in the same commit.
"""

import argparse
import json
import sqlite3

import pytest

from consilience import beta as beta_mod
from consilience import projection
from consilience.cli import build_parser, main
from consilience.events import (
    SCHEMA_VERSION,
    EventError,
    append,
    canonical,
    prefix_digest,
    read,
    validate,
)


def ev(**over):
    base = {
        "v": SCHEMA_VERSION,
        "ts": "2026-08-20T01:00:00+01:00",
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
    ts="2026-08-20T01:00:00+01:00",
):
    """An outcome event, authored by the human when it carries their verdict.

    This helper used to attach a `human_verdict` to an event with `actor="agent"` and no
    principal, and every test passed. That is precisely the forgery V0-18 forbids, so the
    fixture was modelling an invalid event as valid — which is why no test caught the hole
    in `_check_human_authority`. A fixture that can express a forbidden state will teach a
    suite to accept it.
    """
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


def test_a_malformed_line_is_an_error_not_a_skip(tmp_path):
    log = tmp_path / "2026-08-20.jsonl"
    append(log, ev())
    with log.open("a", encoding="utf-8") as fh:
        fh.write("{not json}\n")
    with pytest.raises(EventError, match="not valid JSON"):
        read(log)


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
    with pytest.raises(EventError, match="human_verdict must be"):
        projection.build(log_dir, db)


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

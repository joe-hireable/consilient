"""Checks for the invariants the observe-only increment declares.

Every test names the invariant it enforces. Invariant I1: a declared chokepoint ships with
the check that bans bypassing it, in the same commit.
"""

import argparse
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from consilient import beta as beta_mod
from consilient import events as events_mod
from consilient import projection
from consilient.cli import build_parser, main
from consilient.events import (
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


def verdict_correction(attempt_id, previous, human_verdict, reason, ts=None):
    """A human correction fixture whose actor cannot be changed to an agent."""
    return ev(
        ts=ts or now_ts(),
        actor=HUMAN,
        event=projection.VERDICT_CORRECTION_KIND,
        data={
            "attempt_id": attempt_id,
            "previous_verdict": previous,
            "human_verdict": human_verdict,
            "reason": reason,
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
                "via": "cli",
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


# ---------------------------------------------------------------- V0-28
@pytest.mark.parametrize(
    "decision", ("verdict", "approval", "gate_lift", "spend_authorisation")
)
@pytest.mark.parametrize(
    "via",
    (
        "slack",
        " TWILIO ",
        "Email",
        "webhook",
        "slack message 123",
        "sms",
        "clickup",
        "gmail",
        "remote control session, 2026-08-20",
        "unknown",
    ),
)
def test_only_declared_local_cli_can_deliver_a_human_decision(decision, via):
    remote = ev(
        actor=HUMAN,
        data={"human_decision": decision, "principal": HUMAN, "via": via},
    )
    with pytest.raises(EventError, match="V0-28"):
        validate(remote)


def test_untrusted_transport_cannot_deliver_an_implicit_human_verdict():
    remote = verdict("attempt-001", "accept")
    remote["data"]["via"] = "slack"
    with pytest.raises(EventError, match="V0-28"):
        validate(remote)


def test_a_self_reported_signature_does_not_bypass_transport_refusal():
    remote = ev(
        actor=HUMAN,
        data={
            "human_decision": "approval",
            "principal": HUMAN,
            "via": "slack",
            "signature": "self-reported-and-unverified",
        },
    )
    with pytest.raises(EventError, match="no signature verifier"):
        validate(remote)


def test_a_human_decision_channel_must_be_a_non_empty_string():
    remote = ev(
        actor=HUMAN,
        data={"human_decision": "approval", "principal": HUMAN, "via": 1},
    )
    with pytest.raises(EventError, match="non-empty string"):
        validate(remote)


# ---------------------------------------------------------------- V0-02
def test_delete_and_replay_reproduces_identical_state(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    for i in range(5):
        append_judged(path, f"attempt-{i}", f"t{i}", bool(i % 2), "reject")

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
    append_judged(log_dir / "2026-08-20.jsonl", "attempt-0", "t0", True, "reject")
    conn = projection.build(log_dir, db)
    conn.execute(
        "INSERT INTO outcomes (position, attempt_id, ts, task, verifier_accept)"
        " VALUES (999, 'smuggled-attempt', '2026-08-20T02:00:00+01:00',"
        " 'smuggled', 1)"
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
        event=projection.OUTCOME_KIND,
        data={"attempt_id": "attempt-001", "task": "t", "verifier_accept": "yes"},
    )
    append(log_dir / "2026-08-20.jsonl", bad)
    with pytest.raises(projection.ProjectionError, match="must be a boolean"):
        projection.build(log_dir, db)


def test_a_deferred_human_verdict_amends_one_attempt_for_beta(tmp_path):
    """The verifier result and human judgement may arrive at different times."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("attempt-001", "same-task-may-have-retries", True))
    append(path, verdict("attempt-001", "reject"))

    conn = projection.build(log_dir, db)
    assert conn.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0] == 1
    result = beta_mod.from_connection(conn)
    assert result.n_rejected == 1
    assert result.n_false_accept == 1
    conn.close()


def test_an_attempt_outcome_without_identity_is_quarantined(tmp_path):
    log = tmp_path / "2026-08-20.jsonl"
    log.write_text(
        canonical(
            ev(
                event=projection.OUTCOME_KIND,
                data={"task": "t", "verifier_accept": True},
            )
        )
        + "\n",
        encoding="utf-8",
    )

    events, rejected = read(log)
    assert events == []
    assert len(rejected) == 1
    assert "attempt_id" in rejected[0].reason


def test_a_verdict_for_an_unknown_attempt_fails_closed(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append(log_dir / "2026-08-20.jsonl", verdict("missing-attempt", "reject"))

    with pytest.raises(projection.ProjectionError, match="unknown attempt"):
        projection.build(log_dir, db)


def test_two_verdicts_for_one_attempt_fail_closed(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("attempt-001", "t", True))
    for human_verdict in ("accept", "reject"):
        append(path, verdict("attempt-001", human_verdict))

    with pytest.raises(projection.ProjectionError, match="already has a verdict"):
        projection.build(log_dir, db)


def test_duplicate_attempt_identity_fails_closed(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    for task in ("first-task", "second-task"):
        append(path, outcome("attempt-001", task, True))

    with pytest.raises(projection.ProjectionError, match="duplicate attempt_id"):
        projection.build(log_dir, db)


def test_attempt_identity_not_task_selects_the_deferred_verdict(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("attempt-001", "repeated-task", False))
    append(path, outcome("attempt-002", "repeated-task", True))
    append(path, verdict("attempt-002", "reject"))

    conn = projection.build(log_dir, db)
    rows = list(
        conn.execute("SELECT attempt_id, human_verdict FROM outcomes ORDER BY position")
    )
    assert rows == [("attempt-001", None), ("attempt-002", "reject")]
    result = beta_mod.from_connection(conn)
    assert result.n_rejected == 1 and result.n_false_accept == 1
    conn.close()


def test_an_agent_cannot_author_a_deferred_human_verdict():
    forged = ev(
        event="attempt.verdict",
        actor="claude-code-agent",
        data={
            "attempt_id": "attempt-001",
            "human_verdict": "reject",
            "principal": HUMAN,
            "via": "cli",
        },
    )
    with pytest.raises(EventError, match="only the principal may author"):
        validate(forged)


def test_a_null_correction_cannot_bypass_human_authority():
    forged = ev(
        event=projection.VERDICT_CORRECTION_KIND,
        actor="claude-code-agent",
        data={
            "attempt_id": "attempt-001",
            "previous_verdict": "accept",
            "human_verdict": None,
            "reason": "erase the label",
        },
    )
    with pytest.raises(EventError, match="human_verdict must be"):
        validate(forged)


def test_an_agent_cannot_author_a_verdict_correction():
    forged = ev(
        event=projection.VERDICT_CORRECTION_KIND,
        actor="claude-code-agent",
        data={
            "attempt_id": "attempt-001",
            "previous_verdict": "accept",
            "human_verdict": "reject",
            "reason": "changed my mind",
            "principal": HUMAN,
            "via": "cli",
        },
    )
    with pytest.raises(EventError, match="only the principal may author"):
        validate(forged)


def test_a_human_changes_their_mind_with_an_explicit_correction(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("attempt-001", "t", True))
    append(path, verdict("attempt-001", "accept"))
    append(
        path,
        verdict_correction(
            "attempt-001", "accept", "reject", "reviewed the failing edge case"
        ),
    )

    conn = projection.build(log_dir, db)
    assert (
        conn.execute(
            "SELECT human_verdict FROM outcomes WHERE attempt_id = 'attempt-001'"
        ).fetchone()[0]
        == "reject"
    )
    result = beta_mod.from_connection(conn)
    assert result.n_rejected == 1
    assert result.n_false_accept == 1
    conn.close()


def test_a_correction_against_the_wrong_prior_verdict_fails_closed(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("attempt-001", "t", True))
    append(path, verdict("attempt-001", "accept"))
    append(
        path,
        verdict_correction("attempt-001", "reject", "accept", "mistyped prior state"),
    )

    with pytest.raises(projection.ProjectionError, match="expected prior verdict"):
        projection.build(log_dir, db)


def test_a_correction_without_an_existing_verdict_fails_closed(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("attempt-001", "t", True))
    append(
        path,
        verdict_correction(
            "attempt-001", "accept", "reject", "review changed the judgement"
        ),
    )

    with pytest.raises(projection.ProjectionError, match="no verdict to correct"):
        projection.build(log_dir, db)


def test_a_verdict_correction_requires_a_reason():
    with pytest.raises(EventError, match="non-empty reason"):
        validate(verdict_correction("attempt-001", "accept", "reject", ""))


def test_an_outcome_cannot_carry_the_human_verdict():
    combined = ev(
        event=projection.OUTCOME_KIND,
        actor=HUMAN,
        data={
            "attempt_id": "attempt-001",
            "task": "t",
            "verifier_accept": True,
            "human_verdict": "reject",
            "principal": HUMAN,
            "via": "cli",
        },
    )
    with pytest.raises(EventError, match="separate attempt.verdict"):
        validate(combined)


def test_the_projection_has_no_inline_human_verdict_path():
    conn = sqlite3.connect(":memory:")
    conn.executescript(projection.SCHEMA)
    combined = events_mod.Event(outcome("attempt-001", "t", True) | {"actor": HUMAN})
    combined.raw["data"].update(
        {
            "human_verdict": "reject",
            "principal": HUMAN,
            "via": "cli",
        }
    )

    with pytest.raises(projection.ProjectionError, match="separate attempt.verdict"):
        projection._apply_outcome(conn, 0, combined)
    conn.close()


def test_unknown_human_verdict_fails_closed_at_validation(tmp_path):
    """Since 20 Aug 2026 this fails one layer earlier than it used to.

    Closing the V0-18 hole meant `validate` had to look at `human_verdict`, so an unknown
    verdict is now refused before it can be written to the log at all, rather than when the
    projection is built from it. Stricter, and earlier.
    """
    with pytest.raises(EventError, match="human_verdict must be"):
        append(
            log_dir_unused := tmp_path / "log" / "2026-08-20.jsonl",
            verdict("attempt-001", "probably fine"),
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
    append(path, outcome("attempt-001", "t", True))
    good = verdict("attempt-001", "reject")
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
    assert rejected[0][0] == 3
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


def test_ci_static_gate_runs_mypy_strict():
    workflow = Path(".github/workflows/invariants.yml").read_text(encoding="utf-8")
    static_step = workflow.partition("- name: Static checks")[2].partition("- name:")[0]
    assert "run: python -m mypy --strict src/consilient" in static_step


def test_ci_ruff_gate_matches_release_command():
    workflow = Path(".github/workflows/invariants.yml").read_text(encoding="utf-8")
    ruff_step = workflow.partition("- name: Repository-wide Ruff")[2].partition(
        "- name:"
    )[0]
    assert "run: python -m ruff check ." in ruff_step


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


def test_beta_claims_no_bound_unless_the_sampling_is_declared():
    """Q30: the oracle is a test whose errors correlate with the ones it grades.

    This asserted `is True` until 20 Aug 2026, against a field hard-coded to True. It
    enforced the claim rather than the property — the fourth instance of that pattern found
    in this repository — and the claim does not hold in general. β is a bound on joint error
    only if the sample is not conditioned on the verifier's own outcome. If artefacts reach
    a human only when the checks already accepted them, every rejected row has
    verifier_accept=True and β is 1 by construction. No collection protocol exists, so the
    honest default is that no bound is claimed.
    """
    result = beta_mod.compute([])
    assert result.lower_bound_on_joint_error is False, (
        "no bound may be claimed by default; the sampling property that would justify it "
        "is not established anywhere"
    )
    assert "non-stationary" in result.caveat

    declared = beta_mod.compute([], sampling_unconditioned=True)
    assert declared.lower_bound_on_joint_error is True, (
        "a caller with an unconditioned sampling protocol must be able to declare it"
    )


def test_the_rendered_beta_does_not_say_bound_when_no_bound_is_claimed():
    """The claim appeared in rendered output, which is the one place a reader looks."""
    rows = [
        {
            "ts": now_ts(),
            "verifier_accept": i < 7,
            "human_verdict": "reject",
        }
        for i in range(30)
    ]
    undeclared = beta_mod.compute(rows).render()
    assert "NOT a bound" in undeclared
    assert "lower bound" not in undeclared

    declared = beta_mod.compute(rows, sampling_unconditioned=True).render()
    assert "lower bound on a joint human-plus-checks error" in declared


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
    append_judged(log_dir / "2026-08-20.jsonl", "attempt-0", "t0", True, "reject")
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
        append_judged(
            log_dir / "2026-08-20.jsonl",
            f"attempt-{i}",
            f"t{i}",
            True,
            "reject",
        )
    # Nothing on disk yet: the comparison has no subject, and must not claim a pass.
    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 1
    first = json.loads(capsys.readouterr().out)
    assert first["compared"] is False and first["identical"] is None
    assert first["events"] == 6

    # The first call left state behind, so the second has something to compare against.
    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["compared"] is True and payload["identical"] is True
    assert payload["events"] == 6 and payload["prior_digest"] == payload["digest"]


def test_replay_reports_divergence_when_the_state_on_disk_has_drifted(tmp_path, capsys):
    """The check the old implementation could not perform.

    It rebuilt from the log twice and compared the rebuilds -- identical by construction --
    after unlinking the very state whose drift it was meant to detect.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append_judged(log_dir / "2026-08-20.jsonl", "attempt-0", "t0", True, "reject")
    projection.build(log_dir, db).close()

    drifted = sqlite3.connect(db)
    drifted.execute(
        "INSERT INTO outcomes (position, attempt_id, ts, task, verifier_accept)"
        " VALUES (999, 'out-of-band-attempt', '2026-08-20T02:00:00+01:00',"
        " 'out-of-band', 1)"
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
    """Stage 3 needs Gate B. The CLI exposes no labelled connector control surface.

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
    for sub in subparsers.choices.values():
        actions |= {a.dest for a in sub._actions}

    assert commands == {"record", "replay", "beta", "doctor"}, commands
    for forbidden in (
        "route",
        "dispatch",
        "block",
        "accept",
        "gate",
        "escalate",
        "connector",
        "mcp",
        "admit",
        "admission",
        "invoke",
    ):
        offenders = {x for x in actions | commands if forbidden in x}
        assert not offenders, f"observe-only CLI exposes {offenders}"

    for forbidden_argv in (
        ["connector"],
        ["doctor", "--connector", "x"],
        ["replay", "--admission", "x"],
        ["beta", "--invoke", "x"],
        ["record", "--mcp", "x", "--event", "{}"],
    ):
        with pytest.raises(SystemExit) as refused:
            parser.parse_args(forbidden_argv)
        assert refused.value.code == 2


def test_doctor_fails_a_gapped_capture_run_and_names_the_gap(tmp_path, capsys):
    write_capture_days(tmp_path / "log", "2026-08-14", "2026-08-15", "2026-08-17")

    condition = doctor_payload(tmp_path, capsys)["gates"]["A"]["conditions"][2]

    assert condition["id"] == "A3" and condition["status"] == "fail"
    assert "2026-08-16" in condition["reason"]


def test_doctor_passes_seven_clean_consecutive_capture_days(tmp_path, capsys):
    write_capture_days(
        tmp_path / "log",
        "2026-08-14",
        "2026-08-15",
        "2026-08-16",
        "2026-08-17",
        "2026-08-18",
        "2026-08-19",
        "2026-08-20",
    )

    condition = doctor_payload(tmp_path, capsys)["gates"]["A"]["conditions"][2]

    assert condition["id"] == "A3" and condition["status"] == "pass"


def test_doctor_reports_a_quarantined_line_in_the_seven_day_run(tmp_path, capsys):
    """Amended by ADR-0043, accepted 20 August 2026. This test used to assert FAIL.

    It asserted that a single quarantined line inside the window fails A3. That was the
    behaviour which made A3 unsatisfiable: refusals are permanent in an append-only log, so
    the condition could only ever be met by breaking capture — losing a day of data in order
    to satisfy "no data loss".

    The half of the old assertion that survives, and the half worth pinning, is the
    REPORTING. ADR-0043 says pre-existing refusals are "counted, reported, and non-blocking".
    Non-blocking is covered by `test_a3_tolerates_the_recorded_historical_refusals`, blocking
    on a new one by `test_a3_still_fails_on_one_new_refusal`. This one guards the failure mode
    neither of those would catch — the count going quiet.
    """
    write_capture_days(
        tmp_path / "log",
        "2026-08-14",
        "2026-08-15",
        "2026-08-16",
        "2026-08-17",
        "2026-08-18",
        "2026-08-19",
        "2026-08-20",
    )
    with (tmp_path / "log" / "2026-08-20.jsonl").open("a", encoding="utf-8") as stream:
        stream.write("not-json\n")

    condition = doctor_payload(tmp_path, capsys)["gates"]["A"]["conditions"][2]

    assert condition["id"] == "A3"
    assert "1 refused line(s)" in condition["reason"], (
        "a tolerated refusal must still be named in the verdict, never silently absorbed"
    )


def test_doctor_unknown_evidence_cannot_enable_control(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_capture_days(tmp_path / "log", "2026-08-20")

    payload = doctor_payload(tmp_path, capsys)
    condition = payload["gates"]["A"]["conditions"][0]

    assert condition["id"] == "A1" and condition["status"] == "unknown"
    assert condition["evidence"] == []
    assert {
        name: {item["id"] for item in gate["conditions"]}
        for name, gate in payload["gates"].items()
    } == {"A": {"A1", "A2", "A3"}, "B": {"B1", "B2", "B3", "B4"}}
    assert payload["routing_orchestration_enabled"] is False


def test_doctor_fails_the_unbuilt_weekly_fallback(tmp_path, capsys, monkeypatch):
    """Amended by ADR-0046. The evidence path changed; the assertion did not weaken.

    This used to assert the condition cites `.github/workflows`. Under Joe's no-secrets rule
    the exercise can never run in this repository's CI, so the gate stopped having an opinion
    about GitHub Actions and reads the dated result instead. An absent result still FAILS —
    never `unknown`, which is the status that made B3 a wall in the first place.
    """
    # Isolate from the repository's own result file. Since 20 Aug 2026 a real passing result
    # exists at the repository root, so without this the test reads it and B3 passes — the
    # test was only ever green because the artefact did not exist yet.
    monkeypatch.chdir(tmp_path)
    write_capture_days(tmp_path / "log", "2026-08-20")

    condition = doctor_payload(tmp_path, capsys)["gates"]["B"]["conditions"][2]

    assert condition["id"] == "B3" and condition["status"] == "fail"
    assert ".harness/fallback-result.json" in condition["evidence"]
    assert "never recorded one" in condition["reason"]


def test_doctor_reads_the_wrapped_exp05_result_as_pass(tmp_path, capsys):
    write_capture_days(tmp_path / "log", "2026-08-20")

    condition = doctor_payload(tmp_path, capsys)["gates"]["B"]["conditions"][0]

    assert condition["id"] == "B1" and condition["status"] == "pass"


def test_doctor_does_not_substitute_repository_beta_for_exp08(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text("### EXP-08 · Critic recall `DONE`\n", encoding="utf-8")
    log = tmp_path / "log" / "2026-08-20.jsonl"
    for index in range(30):
        append_judged(log, f"critic-{index}", f"t{index}", False, "reject")

    payload = doctor_payload(tmp_path, capsys)
    condition = payload["gates"]["B"]["conditions"][1]

    # Amended by ADR-0045. The intent is unchanged and now stronger: thirty repository-wide
    # human rejections are not critic-recall evidence and must not satisfy B2. Previously the
    # condition read the repository beta and reported `unknown`; it no longer reads it at all
    # and requires an explicit `critic-beta-measured:` marker, so the substitution the test
    # guards against is now structurally impossible rather than merely refused.
    assert condition["id"] == "B2" and condition["status"] == "fail"
    assert "records no `critic-beta-measured" in condition["reason"]
    assert payload["routing_orchestration_enabled"] is False


def _accepted_b4_docs(root):
    """The two documents B4 reads: the circularity finding, and ADR-0039 accepting its repair."""
    circularity = root / "docs/00-context/gate-b-cannot-be-passed-2026-08-20.md"
    circularity.parent.mkdir(parents=True, exist_ok=True)
    circularity.write_text(
        "Condition 4 can only be satisfied by doing the thing the gate forbids\n",
        encoding="utf-8",
    )
    adr = (
        root
        / "docs/decisions/0039-stage-3-entered-on-approval-gate-b-gates-dependence.md"
    )
    adr.parent.mkdir(parents=True, exist_ok=True)
    adr.write_text(
        "# 0039. Stage 3 is entered on approval\n\n"
        "- **Status:** **ACCEPTED 20 August 2026.**\n",
        encoding="utf-8",
    )


def test_doctor_reports_gate_b4_as_unfinished_work_not_a_wall(tmp_path, capsys):
    """Amended after ADR-0039 was ACCEPTED. The circularity was real and is now resolved.

    B4 required twenty tickets orchestrated on another repository; orchestrating another
    repository was Stage 3; Stage 3 began only after Gate B. ADR-0039 separated entry from
    exit, so the work that produces this evidence is permitted and B4 gates *dependence*
    rather than construction.

    Continuing to report `structurally_unsatisfiable` would be reporting something an
    accepted decision has superseded — a check asserting a fact that is no longer true. The
    honest report is a count, and the count is zero.
    """
    write_capture_days(tmp_path / "log", "2026-08-20")

    condition = doctor_payload(tmp_path, capsys)["gates"]["B"]["conditions"][3]

    assert condition["id"] == "B4"
    assert condition["status"] == "fail"
    assert "0 of 20" in condition["reason"]
    assert any(
        source.endswith("gate-b-gates-dependence.md")
        for source in condition["evidence"]
    )


def test_gate_b4_still_reports_a_wall_if_adr_0039_is_not_accepted(
    tmp_path, capsys, monkeypatch
):
    """The repair is conditional on the decision, not on the code having been edited.

    If ADR-0039 were reverted, B4 must go back to reporting the circularity rather than
    quietly counting toward a condition that cannot be reached. This is what stops the
    amendment being a one-way door taken by an agent.
    """
    monkeypatch.chdir(tmp_path)
    for relative in (
        "docs/00-context/gate-b-cannot-be-passed-2026-08-20.md",
        "docs/decisions/0039-stage-3-entered-on-approval-gate-b-gates-dependence.md",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "Condition 4 can only be satisfied by doing the thing the gate forbids\n",
            encoding="utf-8",
        )
    write_capture_days(tmp_path / "log", "2026-08-20")

    condition = doctor_payload(tmp_path, capsys)["gates"]["B"]["conditions"][3]
    assert condition["status"] == "structurally_unsatisfiable"


def test_gate_b4_counts_only_validated_tickets_on_another_repository(
    tmp_path, capsys, monkeypatch
):
    """Tickets on this repository do not count, and neither do duplicates."""
    monkeypatch.chdir(tmp_path)
    _accepted_b4_docs(tmp_path)
    log = tmp_path / "log" / "2026-08-20.jsonl"
    for index in range(3):
        append(
            log,
            ev(
                event="attempt.outcome",
                data={
                    "repository": "other",
                    "attempt_id": f"att-{index}",
                    "task": f"ticket-{index}",
                    "verifier_accept": True,
                },
            ),
        )
        append(
            log,
            ev(
                event="ticket.completed",
                data={
                    "repository": "other",
                    "ticket": f"ticket-{index}",
                    "attempt_id": f"att-{index}",
                },
            ),
        )
    append(
        log,
        ev(
            event="ticket.completed",
            data={
                "repository": "other",
                "ticket": "ticket-0",
                "attempt_id": "att-0",
            },
        ),
    )
    append(
        log,
        ev(
            event="ticket.completed",
            data={"repository": "consilient", "ticket": "ticket-99"},
        ),
    )

    condition = _gate_b(tmp_path, capsys)["B4"]
    assert "3 of 20" in condition["reason"], condition["reason"]


def test_shared_options_survive_on_either_side_of_the_command(tmp_path, capsys):
    """argparse `parents=` lets a subparser default clobber an already-parsed value.

    Before this was fixed, `--log X replay` silently reverted to the default log
    directory and replayed the wrong trajectory.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append_judged(log_dir / "2026-08-20.jsonl", "attempt-0", "t0", True, "reject")
    projection.build(log_dir, db).close()  # give `replay` something to compare against

    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 0
    before = json.loads(capsys.readouterr().out)

    assert main(["replay", "--log", str(log_dir), "--db", str(db), "--json"]) == 0
    after = json.loads(capsys.readouterr().out)

    assert before["events"] == after["events"] == 2
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
    # Was `assert "lower bound on a joint" in line` until 20 Aug 2026, when the bound was
    # found to be asserted rather than established. The rendered claim is now conditional
    # on a declared sampling protocol, and the default declares none.
    assert "NOT a bound" in line


# ------------------------------------------------- V0-18, the second path (20 Aug 2026)
# Beta is measured against the human verdict. If an agent can author that verdict, beta
# measures nothing. `_check_human_authority` returned early whenever `human_decision` was
# absent, while `projection._apply_outcome` read `human_verdict` directly -- a second path
# to a guarded state, which is the `jobboard-v2` failure this project was founded on.


def test_an_agent_cannot_author_a_human_verdict_by_omitting_human_decision():
    forged = ev(
        event=projection.VERDICT_KIND,
        actor="claude-code-agent",
        data={"attempt_id": "attempt-001", "human_verdict": "accept"},
    )
    with pytest.raises(EventError, match="must name its principal"):
        validate(forged)


def test_an_agent_cannot_author_a_human_verdict_by_naming_the_principal():
    """Naming whose authority is exercised is not the same as holding it."""
    forged = ev(
        event=projection.VERDICT_KIND,
        actor="claude-code-agent",
        data={
            "attempt_id": "attempt-001",
            "human_verdict": "accept",
            "principal": HUMAN,
            "via": "cli",
        },
    )
    with pytest.raises(EventError, match="only the principal may author"):
        validate(forged)


def test_a_human_verdict_must_record_the_channel_it_arrived_through():
    no_via = ev(
        event=projection.VERDICT_KIND,
        actor=HUMAN,
        data={
            "attempt_id": "attempt-001",
            "human_verdict": "accept",
            "principal": HUMAN,
        },
    )
    with pytest.raises(EventError, match="must record"):
        validate(no_via)


def test_a_human_verdict_may_not_be_filed_as_a_different_decision():
    mislabelled = ev(
        event=projection.VERDICT_KIND,
        actor=HUMAN,
        data={
            "attempt_id": "attempt-001",
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
    validate(verdict("attempt-001", "accept"))


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
    append_judged(path, "attempt-0", "t0", True, "reject")
    projection.build(log_dir, db).close()

    append_judged(path, "attempt-1", "t1", False, "accept")

    # Exit 0 means the check ran AND passed. A stale run verified nothing, so it is not a
    # pass - but it is reported as STALE rather than DIVERGED, which is the distinction.
    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["stale"] is True
    assert payload["compared"] is False
    assert payload["identical"] is None
    assert payload["events_projected"] == 2 and payload["events"] == 4


def test_real_drift_is_still_caught_once_the_counts_match(tmp_path, capsys):
    """The narrowing must not have blunted the check it narrows."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    append_judged(log_dir / "2026-08-20.jsonl", "attempt-0", "t0", True, "reject")
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
    append_judged(path, "attempt-0", "t0", True, "reject")
    projection.build(log_dir, db).close()

    drifted = sqlite3.connect(db)
    drifted.execute("UPDATE outcomes SET human_verdict = 'accept'")
    drifted.commit()
    drifted.close()

    append_judged(path, "attempt-1", "t1", False, "reject")  # now stale as well

    assert main(["--log", str(log_dir), "--db", str(db), "replay", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["stale"] is True and payload["compared"] is False
    assert payload["preserved_stale_state"], (
        "the drifted state was destroyed, not preserved"
    )
    assert Path(payload["preserved_stale_state"]).exists()


# ---------------------------------------------------------------- V0-26
# ADR-0010 and CONSILIENCE.md clause 2: every multi-agent structure must name the distinct
# class of facts it introduces. Two agents declaring the same evidence class is echo, not
# consilience, and must be refused by validate(). Single-actor events remain unaffected.


def multi_event(contributors, **over):
    data = {"contributors": contributors}
    over_data = over.pop("data", {})
    data.update(over_data)
    return ev(data=data, **over)


def test_multi_contributor_event_with_duplicate_evidence_class_is_refused():
    bad = multi_event(
        [
            {"logical_identity": "reader-a", "evidence_class": "literature"},
            {"logical_identity": "reader-b", "evidence_class": "literature"},
        ]
    )
    with pytest.raises(EventError, match="duplicate evidence_class 'literature'"):
        validate(bad)


def test_multi_contributor_event_with_case_variant_duplicate_is_refused():
    """Case and whitespace variation must not disguise identical evidence classes."""
    bad = multi_event(
        [
            {"logical_identity": "analyst-1", "evidence_class": "Primary Sources"},
            {"logical_identity": "analyst-2", "evidence_class": "  primary sources  "},
        ]
    )
    with pytest.raises(EventError, match="duplicate evidence_class"):
        validate(bad)


def test_multi_contributor_event_with_missing_evidence_class_is_refused():
    bad = multi_event(
        [
            {"logical_identity": "worker-1", "evidence_class": "test execution"},
            {"logical_identity": "worker-2"},
        ]
    )
    with pytest.raises(EventError, match="requires a non-empty evidence_class"):
        validate(bad)


def test_multi_contributor_event_with_empty_or_whitespace_evidence_class_is_refused():
    bad = multi_event(
        [
            {"logical_identity": "worker-1", "evidence_class": "test execution"},
            {"logical_identity": "worker-2", "evidence_class": "   "},
        ]
    )
    with pytest.raises(EventError, match="requires a non-empty evidence_class"):
        validate(bad)


def test_multi_contributor_event_with_non_dict_contributor_is_refused():
    bad = multi_event(["agent-1", "agent-2"])
    with pytest.raises(EventError, match="contributor must be an object"):
        validate(bad)


def test_multi_contributor_event_with_non_list_contributors_is_refused():
    bad = ev(data={"contributors": "invalid-string"})
    with pytest.raises(EventError, match="contributors must be a list"):
        validate(bad)


def test_multi_contributor_event_with_distinct_evidence_classes_is_accepted():
    good = multi_event(
        [
            {"logical_identity": "tester", "evidence_class": "execution output"},
            {"logical_identity": "auditor", "evidence_class": "static inspection"},
        ]
    )
    assert validate(good) == good


def test_many_contributors_with_partial_duplicate_is_refused():
    bad = multi_event(
        [
            {"logical_identity": "c1", "evidence_class": "algebra"},
            {"logical_identity": "c2", "evidence_class": "simulation"},
            {"logical_identity": "c3", "evidence_class": "literature"},
            {"logical_identity": "c4", "evidence_class": "algebra"},
        ]
    )
    with pytest.raises(EventError, match="duplicate evidence_class 'algebra'"):
        validate(bad)


def test_single_contributor_event_is_unaffected():
    """An event with a single contributor does not require evidence_class."""
    single = multi_event([{"logical_identity": "single-worker"}])
    assert validate(single) == single


def test_single_actor_ordinary_event_is_unaffected():
    """The overwhelming majority of events carry no contributors and must pass."""
    ordinary = ev(data={"task": "t1", "note": "ordinary event"})
    assert validate(ordinary) == ordinary


def test_duplicate_evidence_class_is_quarantined_at_read_without_breaking_log(tmp_path):
    """Refused multi-contributor events are quarantined rather than crashing reader."""
    log = tmp_path / "2026-08-20.jsonl"
    valid = multi_event(
        [
            {"logical_identity": "a", "evidence_class": "source a"},
            {"logical_identity": "b", "evidence_class": "source b"},
        ]
    )
    append(log, valid)

    smuggled_bad = canonical(
        multi_event(
            [
                {"logical_identity": "a", "evidence_class": "same class"},
                {"logical_identity": "b", "evidence_class": "same class"},
            ]
        )
    )
    with log.open("a", encoding="utf-8") as fh:
        fh.write(smuggled_bad + "\n")

    events, rejected = read(log)
    assert len(events) == 1, "the valid event must survive"
    assert len(rejected) == 1, "the duplicate class event must be quarantined"
    assert rejected[0].line == 2
    assert "duplicate evidence_class" in rejected[0].reason


def test_no_new_commit_may_be_authored_by_a_fixture_identity():
    """A ratchet on git authorship, found on 20 Aug 2026 and not by any check here.

    EXP-07 builds throwaway repositories and stamps them `EXP-07 <exp07@local>` so its
    synthetic commits are distinguishable. That identity — along with a WSL-absolute
    `core.worktree` — was also present in the *primary* repository's `.git/config`, which
    every worktree shares. Fifty-one of this branch's commits, including two written the
    day this test was added, are therefore authored and committed by a test fixture rather
    than by the person accountable for them.

    This is V0-18's concern inverted. V0-18 stops an agent claiming a human's decision; the
    same record silently attributed a human's work to a fixture, and nothing looked. The
    repair for the config is done; this is the ratchet that stops it recurring.

    The published history is NOT rewritten here — that is a force-push and belongs to the
    principal. The constant below is the measured legacy baseline and may only go DOWN.
    """
    git = shutil.which("git")
    if git is None or not Path(".git").exists():  # pragma: no cover - repository-only
        pytest.skip("no git checkout")
    result = subprocess.run(
        [git, "log", "--format=%ae%n%ce", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    fixture_stamped = [
        line for line in result.stdout.splitlines() if line.endswith("@local")
    ]
    assert len(fixture_stamped) <= 102, (
        "a commit was authored by a fixture identity; check `git config user.email` — "
        "worktrees share the primary repository's config"
    )


def _reachable_statuses() -> dict[str, set[str]]:
    """Which statuses can each gate condition in `doctor` actually emit?

    Reads `_condition(...)` call sites out of the AST. The status argument is either an
    expression containing string literals, or a local name assigned string literals inside
    the same function; both are resolved.
    """
    import ast

    source = Path("src/consilient/cli.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    reachable: dict[str, set[str]] = {}

    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        assigned: dict[str, set[str]] = {}
        delegated = _delegated_calls(function)
        for node in ast.walk(function):
            if isinstance(node, ast.Assign):
                names = {t.id for t in node.targets if isinstance(t, ast.Name)}
                literals = {
                    n.value
                    for n in ast.walk(node.value)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)
                }
                for name in names:
                    assigned.setdefault(name, set()).update(literals)

        for node in ast.walk(function):
            call = node
            if not isinstance(call, ast.Call):
                continue
            if not (isinstance(call.func, ast.Name) and call.func.id == "_condition"):
                continue
            if len(call.args) < 2:
                continue
            identifier, status = call.args[0], call.args[1]
            if not (
                isinstance(identifier, ast.Constant)
                and isinstance(identifier.value, str)
            ):
                continue
            found = {
                n.value
                for n in ast.walk(status)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            }
            if isinstance(status, ast.Name):
                found |= assigned.get(status.id, set())
                found |= _returned_literals(tree, delegated.get(status.id, set()))
            reachable.setdefault(identifier.value, set()).update(found)

    return reachable


def _delegated_calls(function) -> dict[str, set[str]]:
    """Local helper names a status variable was assigned from, e.g. `s, r = _helper()`."""
    import ast

    out: dict[str, set[str]] = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        callee = node.value.func
        if not isinstance(callee, ast.Name):
            continue
        names: set[str] = set()
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, ast.Tuple):
                names |= {e.id for e in target.elts if isinstance(e, ast.Name)}
        for name in names:
            out.setdefault(name, set()).add(callee.id)
    return out


def _returned_literals(tree, callees: set[str]) -> set[str]:
    """String literals any of the named module-level functions can return."""
    import ast

    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name not in callees:
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Return) and inner.value is not None:
                found |= {
                    c.value
                    for c in ast.walk(inner.value)
                    if isinstance(c, ast.Constant) and isinstance(c.value, str)
                }
    return found


def test_every_gate_condition_has_a_reachable_pass_state():
    """A gate condition that cannot report PASS is not a gate, it is a wall.

    Measured 20 Aug 2026: of the seven conditions, four cannot be satisfied. A3 is
    satisfiable only by breaking capture, which is the data loss it exists to detect
    (ADR-0043). B4 is circular by construction (ADR-0039). And **B2 and B3 have no `pass`
    branch at all** — every path through `_fallback_condition` and through B2's arm of
    `_experiment_conditions` returns `unknown` or `fail`, so no artefact anyone could build
    would make them pass.

    The set is now EMPTY. B2 and B3 were given success criteria by ADR-0045 and ADR-0046, and
    B4 stopped being circular when ADR-0039 was accepted — all on the day this test was
    written. Every one of the seven conditions can now report `pass`.

    That is the whole point: an empty set means every gate condition is a gate. If a future
    condition arrives without a success path, this fails, and the correct response is to give
    it one rather than to add its name here.

    The three are grandfathered BY NAME and the set may only SHRINK. Adding an identifier
    here is not permitted; removing one is the whole point.
    """
    from consilient.cli import REQUIREMENTS

    reachable = _reachable_statuses()
    assert set(reachable) == set(REQUIREMENTS), (
        f"conditions found in the AST {sorted(reachable)} do not match "
        f"REQUIREMENTS {sorted(REQUIREMENTS)}"
    )

    known_unpassable: set[str] = set()
    unpassable = {key for key, statuses in reachable.items() if "pass" not in statuses}
    assert unpassable <= known_unpassable, (
        f"a gate condition lost its pass state: {sorted(unpassable - known_unpassable)}. "
        "A condition that cannot report pass is a wall, not a gate."
    )


# ---------------------------------------------------------------- ADR-0043
def _a3(tmp_path, capsys):
    gate_a = doctor_payload(tmp_path, capsys)["gates"]["A"]
    return {c["id"]: c for c in gate_a["conditions"]}["A3"]


def test_a3_passes_seven_clean_days(tmp_path, capsys):
    """The amended condition is satisfiable at all, which the original was not."""
    log = tmp_path / "log"
    write_capture_days(log, *[f"2026-08-{day:02d}" for day in range(10, 17)])
    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "pass", condition["reason"]


HISTORICAL_REFUSAL_LINES: list[str] = [
    (
        '{"v": 1, "ts": "2026-08-20T09:41:46+01:00", "exp": "EXP-27", '
        '"event": "longitudinal.clock_started", "actor": "claude-senior-orchestrator", '
        '"data": {"principal": "joe-brown", "logical_identity": "senior-orchestrator", '
        '"runtime_identity": "claude-code/remote-control-session", "model": "claude-opus-5", '
        '"work_role": "implementer", "human_decision": "approval", "via": "chat, 20 August 2026", '
        '"authority": "Joe: \'YES PROCEED DONT WANT MONTHS OF DELAY\' - explicit approval for the '
        'read-only collector, which is new product-adjacent code and was the one gate he had to lift", '
        '"day_1": "09:39, all six fixed first-party sources reachable, 31 events frozen", '
        '"earliest_promotion": "19 September 2026, one day later for each day missed", '
        '"design": "conditional polling with ETag and If-Modified-Since; each event frozen by upstream id '
        'or content hash; one appended observation per source per run", "idempotent": "a second run '
        'within the same day returned 304 on every source and zero new events, so the day count cannot be '
        'inflated by re-running", "invariant_enforced_not_promised": "every emitted record passes '
        'validate_change_record, which raises on any record claiming to increase headroom, decrease usage, '
        'move a reset window or mark unknown headroom usable. Eleven tests, including one per forbidden action, '
        'plus one asserting that silence about headroom is not permission.", "no_inference_no_metered_provider": true, '
        '"owed": "the dispatch-time version/capability handshake (procedure step 4) and the three injected fixtures '
        '(step 5). Neither blocks the clock; both must land before the window closes or the run cannot answer its '
        'own question.", "scheduling_gap": "the collector must run once a day. Today\'s run is manual. A scheduled '
        'task or a daily invocation is needed and is not yet in place - if nobody runs it, the window silently '
        'accumulates missing days, which is exactly the failure the register warns about."}}\n'
    ),
    (
        '{"v": 1, "ts": "2026-08-20T09:42:46+01:00", "exp": "decision-protocol", '
        '"event": "autonomy.scope_widened", "actor": "claude-senior-orchestrator", '
        '"data": {"principal": "joe-brown", "logical_identity": "senior-orchestrator", '
        '"runtime_identity": "claude-code/remote-control-session", "model": "claude-opus-5", '
        '"work_role": "decision owner", "human_decision": "approval", "via": "chat, 20 August 2026", '
        '"quote": "I don\'t have any appetite for granular technical decisions - these need to be made by '
        'agents. Many users will prefer it this way.", "why_it_is_an_ADR_and_not_a_note": "the second sentence '
        'makes it a statement about who the product is for, not one maintainer\'s preference on one morning", '
        '"unchanged": "the reserved list - money, credentials, anything published or exposed outside the machine, '
        'irrecoverable deletion, and genuine preference questions no fact settles", "now_explicit": "the converse '
        'the ADR implied and did not say: a technical question with a defensible answer is not a preference '
        'question and must not be escalated as one. Escalating one is a defect, not caution.", "named_classes": '
        '["which of two conditionals a quantity is defined on, where one is already implied by the code and the '
        'algebra", "which of several defensible estimators, thresholds or samples", "whether an experiment is '
        're-run and in what order work is done", "how an instrument is repaired and what its tests must cover", '
        '"any change reversible by one git revert, whatever its blast radius on paper"], "the_failure_it_prevents": '
        '"an ask the user cannot cheaply answer gets approved to keep things moving, and a rubber-stamped approval '
        'launders the agent\'s decision into a human one - worse than deciding, because it destroys the record of who '
        'actually chose", "obligation_replacing_the_ask": "every such decision carries, in the same commit, the '
        'reasoning including the option not taken, the reversal command rather than an assurance, and the falsifier. '
        'A decision recorded without a falsifier is a preference wearing a technical costume and should have been '
        'escalated.", "product_posture": "the harness decides technical questions and reports; the human decides '
        'irreversible and preferential ones and is asked. A user who wants more say turns the ADR-0035 visibility '
        'dial up rather than the harness asking more.", "overturning_test": "a user who wanted to be asked, was not, '
        'and lost something they cared about - measurable, and EXP-33 is where it would show. The unread-approval '
        'floor is the same signal from the other side: approvals returned faster than they could be read mean the asks '
        'were not wanted either."}}\n'
    ),
    (
        '{"v": 1, "ts": "2026-08-20T09:56:48+01:00", "exp": "EXP-27", '
        '"event": "collection.scheduled", "actor": "claude-senior-orchestrator", '
        '"data": {"principal": "joe-brown", "logical_identity": "senior-orchestrator", '
        '"runtime_identity": "claude-code/remote-control-session", "model": "claude-opus-5", '
        '"work_role": "implementer", "human_decision": "approval", "via": "chat, 20 August 2026", '
        '"authority": "Joe: \'exp 27 schedule what you need to schedule\' - explicit authorisation for a '
        'system-level change, a Windows scheduled task on his machine", "task": "Consilience-EXP27-Collector, '
        'daily 09:00, first fire 21 August 2026", "verified_by_artefact": "task Ready, next run 21/08 09:00, '
        'on-demand run returned Last Result 0, log grew 11 to 22 lines, six of six sources reachable - '
        'checked rather than inferred from the SUCCESS message", "settings_that_matter": {"StartWhenAvailable": '
        '"a laptop asleep at 09:00 runs on wake rather than skipping the day - the single most important setting", '
        '"RunOnlyIfNetworkAvailable": "a run with no network would record six failures and make the day look '
        'collected when it was not", "RestartOnFailure": "3 attempts 30 minutes apart, so a transient outage does '
        'not cost a day", "DisallowStartIfOnBatteries": "false, because the default would skip on battery, which '
        'on a laptop is most of the time", "InteractiveToken": "runs as Joe with no stored credentials. A day he '
        'never logs in is a day missed; storing a password to avoid that is not a trade worth making for a read-only '
        'poll."}, "wrapper_rationale": "a scheduled task that fails silently is worse than none, because the window '
        'accumulates missing days while looking healthy. run-daily.cmd prefers the worktree, falls back to the main '
        'checkout so it survives the branch being merged, writes a loud failure if the collector is in neither place, '
        'and preserves the exit code.", "branch_note": "the collector currently exists only on branch '
        'worktree-consilience-cto. Main is still at 27b4bc2, last night\'s handoff, and the main checkout has no '
        'collector.py. The wrapper\'s fallback handles the merge whenever it happens.", "how_to_tell_it_stopped": '
        '"python collector.py prints \'distinct days recorded N of 30\'. If N stops advancing the window has '
        'stalled regardless of what Task Scheduler claims. Running it by hand is idempotent - a second run the same '
        'day returns 304 everywhere and adds nothing.", "reversal": "schtasks /Delete /TN Consilience-EXP27-Collector /F. '
        'Touches nothing else, and the collected log survives deletion.", "still_owed": "the dispatch-time capability '
        'handshake and the three injected fixtures. Neither blocks the clock; both must land before the window '
        'closes or the run cannot answer its own question."}}\n'
    ),
]


def test_a3_tolerates_the_recorded_historical_refusals(tmp_path, capsys):
    """ADR-0043's whole content: a permanent refusal must not block forever.

    Before the amendment, unbroken capture failed A3 at 7 days, at 60 and at 365, while a run
    that LOST a day passed. The only way to satisfy "no data loss" was to lose data.
    """
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(10, 17)]
    write_capture_days(log, *days)
    with (log / f"{days[0]}.jsonl").open("a", encoding="utf-8") as fh:
        for line in HISTORICAL_REFUSAL_LINES:
            fh.write(line)

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "pass", condition["reason"]
    assert "historical baseline" in condition["reason"]
    assert "0 are new" in condition["reason"]


def test_a3_still_fails_on_one_new_refusal(tmp_path, capsys):
    """The amendment is not a removal. One refusal above the baseline still fails."""
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(10, 17)]
    write_capture_days(log, *days)
    with (log / f"{days[0]}.jsonl").open("a", encoding="utf-8") as fh:
        for line in HISTORICAL_REFUSAL_LINES:
            fh.write(line)
        fh.write("{not json}\n")

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "fail", condition["reason"]
    assert "1 are new" in condition["reason"]


def test_a3_still_fails_on_a_misdated_line(tmp_path, capsys):
    """Misdated lines are deliberately NOT ratcheted.

    A refusal is a historical judgement about a line that is present. A timestamp that
    disagrees with its own file is a live capture fault, and the amendment must not quietly
    tolerate it alongside the refusals.
    """
    log = tmp_path / "log"
    days = [f"2026-08-{day:02d}" for day in range(10, 17)]
    write_capture_days(log, *days)
    with (log / f"{days[0]}.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(canonical(ev(ts="2026-07-01T12:00:00+00:00")) + "\n")

    condition = _a3(tmp_path, capsys)
    assert condition["status"] == "fail", condition["reason"]
    assert "misdated" in condition["reason"]


def test_the_capture_refusal_baseline_may_only_fall():
    """A ratchet on the tolerance itself, in the shape used for `append()` bypass.

    ADR-0043's own Evidence-against names the hazard: a ratchet with a non-zero floor can
    normalise its floor. The number below is the measured past and raising it is the way this
    amendment would quietly become "count nothing".
    """
    from consilient.cli import CAPTURE_REFUSAL_BASELINE

    assert CAPTURE_REFUSAL_BASELINE <= 3, (
        "the A3 refusal tolerance was raised; ADR-0043 permits it to fall only"
    )


# ---------------------------------------------------------------- ADR-0045
def _gate_b(tmp_path, capsys):
    return {
        c["id"]: c for c in doctor_payload(tmp_path, capsys)["gates"]["B"]["conditions"]
    }


def _b3_world(tmp_path, result):
    """A workspace carrying a given fallback result.

    ADR-0046 removed the schedule-trigger half. The exercise cannot run in this repository's
    CI at all — that would need a secret in a public repository — and a schedule trigger was
    only ever a proxy for "this runs regularly". A result dated inside the window cannot be
    produced without something having run, so the dated result is the whole of the evidence.
    """
    if result is not None:
        harness = tmp_path / ".harness"
        harness.mkdir(parents=True, exist_ok=True)
        (harness / "fallback-result.json").write_text(
            result if isinstance(result, str) else json.dumps(result), encoding="utf-8"
        )
    write_capture_days(tmp_path / "log", "2026-08-20")


def _fallback(days_old, outcome="pass"):
    stamped = datetime.now(timezone.utc) - timedelta(days=days_old)
    from consilient.cli import EXPECTED_FALLBACK_COMMAND, FALLBACK_RUNNER_IDENTITY

    return {
        "ts": stamped.isoformat(),
        "command": EXPECTED_FALLBACK_COMMAND,
        "outcome": outcome,
        "runner": FALLBACK_RUNNER_IDENTITY,
        "run": "https://example.invalid/run/1",
    }


def test_b3_passes_on_a_recent_passing_fallback(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _b3_world(tmp_path, _fallback(2))
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "pass", condition["reason"]
    assert "2 day(s) ago and passed" in condition["reason"]


def test_b3_fails_on_a_stale_fallback(tmp_path, capsys, monkeypatch):
    """Fifteen days is two missed weekly cycles. ADR-0045 names this case explicitly.

    A green result from a month ago is evidence about a month ago. The failure mode this
    guards is a workflow that silently stopped running while its last result stayed green.
    """
    monkeypatch.chdir(tmp_path)
    _b3_world(tmp_path, _fallback(15))
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail", condition["reason"]
    assert "15 days old" in condition["reason"]


def test_b3_fails_when_the_fallback_itself_failed(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _b3_world(tmp_path, _fallback(1, outcome="fail"))
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail" and "'fail'" in condition["reason"]


def test_b3_fails_on_an_unreadable_or_undated_fallback(tmp_path, capsys, monkeypatch):
    """Malformed evidence FAILS rather than reporting unknown.

    `unknown` was the status that made B2 and B3 unpassable in the first place: a placeholder
    that reads like outstanding work. A result nobody can parse is not an open question.
    """
    monkeypatch.chdir(tmp_path)
    _b3_world(tmp_path, "{not json}")
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail" and "unreadable" in condition["reason"]


def test_b3_fails_when_the_result_timestamp_has_no_offset(
    tmp_path, capsys, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    payload = _fallback(1)
    payload["ts"] = "2026-08-20T06:00:00"
    _b3_world(tmp_path, payload)
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail" and "offset" in condition["reason"]


def test_b2_passes_on_a_recorded_critic_beta(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-08 · Critic recall `DONE 21 Aug 2026`\n"
        "critic-beta-measured: 0.31 [0.29, 0.33]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    condition = _gate_b(tmp_path, capsys)["B2"]
    assert condition["status"] == "pass", condition["reason"]
    assert "0.31" in condition["reason"]


def test_b2_fails_when_the_recorded_point_is_outside_its_own_interval(
    tmp_path, capsys, monkeypatch
):
    """A transcription error in the register must not become a passing gate."""
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-08 · Critic recall `DONE 21 Aug 2026`\n"
        "critic-beta-measured: 0.91 [0.29, 0.33]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    condition = _gate_b(tmp_path, capsys)["B2"]
    assert (
        condition["status"] == "fail"
        and "outside its own interval" in condition["reason"]
    )


# ---------------------------------------------------------------- ADR-0046
def test_the_fallback_runner_and_the_gate_agree_on_the_result_shape(
    tmp_path, capsys, monkeypatch
):
    """Producer and consumer must not drift, and nothing else would notice if they did.

    `scripts/run_fallback.py` writes the result and `_fallback_condition` reads it. They live
    in different files, run in different places — one on the principal's machine, one in CI —
    and share only a JSON shape. A renamed key would make B3 fail permanently with a message
    about unreadable evidence, and the cause would be a keystroke.

    This builds the result by executing the runner's own writer code path against a stubbed
    command, then asserts the gate reads it as a pass.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_fallback", Path("scripts/run_fallback.py").resolve()
    )
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    monkeypatch.setattr(runner, "run", lambda: ("pass", "stubbed"))
    monkeypatch.setattr(
        runner, "RESULT", tmp_path / ".harness" / "fallback-result.json"
    )
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["run_fallback.py"])
    assert runner.main() == 0
    capsys.readouterr()  # the runner prints; drain it so doctor's JSON stands alone

    write_capture_days(tmp_path / "log", "2026-08-20")
    monkeypatch.chdir(tmp_path)
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "pass", condition["reason"]


def test_the_fallback_runner_records_a_failure_rather_than_crashing(
    tmp_path, monkeypatch
):
    """A broken fallback is a measurement. It must not look like a broken script.

    If the runner exited non-zero on a failed exercise, a scheduler would treat the evidence
    as an error and — depending on how it is wired — retry it, alert on it, or drop it. The
    result file is the output; the exit code is not.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_fallback_fail", Path("scripts/run_fallback.py").resolve()
    )
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    result_path = tmp_path / ".harness" / "fallback-result.json"
    monkeypatch.setattr(
        runner, "run", lambda: ("fail", "the `claude` executable is not on PATH")
    )
    monkeypatch.setattr(runner, "RESULT", result_path)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["run_fallback.py"])

    assert runner.main() == 0, "a failed fallback must not exit non-zero"
    recorded = json.loads(result_path.read_text(encoding="utf-8"))
    assert recorded["outcome"] == "fail"
    assert "not on PATH" in recorded["detail"]


# ------------------------------------------------- A3's evidence source
def _capture_health_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "capture_health", Path("scripts/capture_health.py").resolve()
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_capture_health_reports_a_healthy_trajectory_and_a_broken_one(tmp_path, monkeypatch):
    """A3's evidence must be a check, not a heartbeat.

    Until 20 Aug 2026 nothing wrote A3's trajectory daily. The log had files for two days
    because work happened on them; the only scheduled task on the machine writes a different
    file entirely. **A quiet day would have broken the consecutive run and reset A3 to one**,
    silently, while the gate looked like it was progressing.

    The fix must not be a heartbeat. A heartbeat proves a writer ran and says nothing about
    the record, which would turn A3 into a check that cannot fail — the exact defect this
    repository catalogued four times today. This asserts the opposite property: a corrupted
    log produces `healthy: false` rather than a cheerful line.
    """
    module = _capture_health_module()
    log = tmp_path / "log"
    monkeypatch.setattr(module, "LOG", log)
    monkeypatch.setattr(module, "DB", tmp_path / "state.db")

    write_capture_days(log, "2026-08-20")
    healthy = module.inspect()
    assert healthy["healthy"] is True
    assert healthy["events"] == 1
    assert healthy["state_digest"]

    # A line the reader refuses is reported, not fatal — the trajectory is still intact.
    with (log / "2026-08-20.jsonl").open("a", encoding="utf-8") as stream:
        stream.write("{not json}\n")
    refused = module.inspect()
    assert refused["healthy"] is True
    assert refused["refused"] == 1, "a refused line must be counted, not hidden"


def test_capture_health_records_what_it_found(tmp_path, monkeypatch):
    """The recorded event must carry the digest, or it is a heartbeat after all."""
    module = _capture_health_module()
    log = tmp_path / "log"
    monkeypatch.setattr(module, "LOG", log)
    monkeypatch.setattr(module, "DB", tmp_path / "state.db")
    monkeypatch.setattr("sys.argv", ["capture_health.py"])
    write_capture_days(log, "2026-08-20")

    assert module.main() == 0

    events, rejected = read_all(log)
    assert not rejected
    recorded = [event for event in events if event.kind == module.CHECK_KIND]
    assert len(recorded) == 1
    data = recorded[0].raw["data"]
    assert data["healthy"] is True
    assert data["state_digest"], "the check must record the digest it verified"
    assert data["checked_by"] == "scripts/capture_health.py"


# ---------------------------------------------------------------- ADR-0047
ADAPTERS = Path("docs/10-research/experiments/exp05")


def _adapter_lines() -> dict[str, int]:
    return {
        path.stem.replace("adapter_", ""): sum(
            1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
        for path in sorted(ADAPTERS.glob("adapter_*.py"))
    }


def test_the_adapter_contract_is_asserted_not_counted():
    """ADR-0047 retired "N adapters fit" as evidence. This is what replaces it.

    Seven backends fitting the boundary told us it was stable; an eighth tells us nothing.
    What the count was really guarding — that nobody quietly redesigns the boundary — is
    guarded here instead, by naming the fields.
    """
    outcome_fields = {
        "ticket_id", "agent", "domain", "harness", "provider", "model",
        "ok", "diff", "tokens_in", "tokens_out", "cost_usd", "duration_s", "raw_tail",
    }
    ticket_fields = {"id", "goal", "repo_dir", "timeout_s"}

    # The canonical declaration lives in the FIRST adapter's module docstring, where it was
    # written before any second runtime existed. That is the text seven backends were built
    # against, so it is the text worth pinning.
    canonical = (ADAPTERS / "adapter_claude_code.py").read_text(encoding="utf-8")
    missing = {name for name in outcome_fields | ticket_fields if f'"{name}"' not in canonical}
    assert not missing, (
        f"the adapter contract lost {sorted(missing)}; ADR-0047 promoted this boundary and a "
        "redesign must be argued in an ADR, not absorbed"
    )

    # And every adapter must still speak it. A contract only the first adapter remembers is
    # documentation, not a boundary.
    for path in sorted(ADAPTERS.glob("adapter_*.py")):
        text = path.read_text(encoding="utf-8")
        absent = {name for name in ("ticket_id", "ok", "diff", "raw_tail") if name not in text}
        assert not absent, f"{path.name} does not speak {sorted(absent)} of the outcome contract"


def test_a_new_adapter_may_not_silently_exceed_the_largest_one():
    """A boundary that never moves while what sits behind it grows is not obviously right.

    Measured 20 Aug 2026 across eight adapter modules: 78, 90, 107, 124, 130, 148, 233, and
    **295** for Grok — the newest is 3.8x the smallest. The contract held; that is not the
    same as adapters being cheap, and conflating the two is the easy mistake ADR-0047 exists
    to prevent.

    This does not forbid a larger adapter. It forces the excess to be argued in the commit
    rather than absorbed silently, which is the ratchet shape used for `append()` bypass and
    the A3 refusal baseline. Raising the constant is the permitted edit; doing it without a
    reason in the message is not.
    """
    lines = _adapter_lines()
    assert lines, "no adapters found; the path in ADR-0047's check is wrong"
    worst = max(lines.values())
    assert worst <= 295, (
        f"an adapter now exceeds the recorded maximum: {max(lines, key=lines.get)} at {worst} "
        "lines. Say in the commit what forced it — contract, vendor, platform or policy."
    )


# --------------------------------------------- credentials, after Joe's 20 Aug 2026 request
def _secret_checker_source() -> str:
    return Path(".github/scripts/check_secrets.py").read_text(encoding="utf-8")


def test_every_adapter_has_a_declared_credential_shape():
    """Adding a runtime must force adding its credential pattern, or the gap recurs.

    Grok Build was installed and authenticated on 20 Aug 2026 and the secret checker had **no
    xAI pattern at all** for the first hours of that runtime's life. Nothing failed, because
    nothing was checking that the pattern list kept pace with the runtimes.

    The fix goes in code rather than in a memory (working principle 4). Each adapter declares
    the credential shape its vendor issues; a vendor that issues none — subscription-only
    sign-in with a token the CLI keeps outside the repository — declares that explicitly, so
    the absence is a statement rather than an oversight.
    """
    # adapter stem -> the token prefix its vendor issues, or None for subscription-only.
    DECLARED = {
        "claude_code": "sk-ant-",
        "codex": "sk-",
        "cursor": None,          # editor sign-in; no user-visible key format
        "cursor_acp": None,      # same credential as cursor
        "antigravity": None,     # editor sign-in
        "opencode": None,        # brings its own provider key, covered by that provider
        "model_backed": None,    # local weights, no credential
        "grok": "xai-",
    }
    present = {
        path.stem.replace("adapter_", "")
        for path in Path("docs/10-research/experiments/exp05").glob("adapter_*.py")
    }
    undeclared = present - set(DECLARED)
    assert not undeclared, (
        f"adapter(s) {sorted(undeclared)} have no declared credential shape. Add the vendor's "
        "token prefix here and to .github/scripts/check_secrets.py, or declare None and say "
        "why in the commit."
    )

    source = _secret_checker_source()
    for stem, prefix in sorted(DECLARED.items()):
        if prefix is None or stem not in present:
            continue
        # The checker splits its literals so it does not match itself; match the same way.
        head, tail = prefix[:2], prefix[2:]
        assert f'"{head}" + r"{tail}' in source or f'"{head}" + r"-{tail}' in source, (
            f"{stem}'s vendor issues {prefix!r}-shaped tokens and check_secrets.py has no "
            f"pattern for it. This is the exact gap xAI sat in on 20 August 2026."
        )


def test_ci_secret_scan_also_reads_untracked_files():
    """`git grep` sees only tracked content, and agents leave files in the tree.

    A dispatched agent's transcript sitting untracked in the working directory was invisible to
    this check until someone staged it — the moment it is already too late. `--untracked` is
    what closes that, and it must not quietly disappear from the workflow.
    """
    workflow = Path(".github/workflows/secret-scan.yml").read_text(encoding="utf-8")
    assert "--untracked" in workflow, "the CI secret scan stopped reading untracked files"
    assert "--history" in workflow, "the CI secret scan stopped reading history"
    assert "--self-test" in workflow, "the CI secret scan stopped proving it can still detect"


def test_agent_transcripts_and_briefs_cannot_be_committed():
    """Dispatch transcripts are multi-megabyte verbatim records and belong nowhere near a commit.

    They carry whatever an agent read, printed, or was told. `git add -A` swept four brief files
    into a commit on 20 August 2026, so this is not hypothetical.
    """
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    assert ".harness/dispatch/" in ignored, "agent transcripts became committable again"
    assert "brief-*.md" in ignored, "dispatch briefs became committable again"


# ---------------------------------------------------------------- Audit Fixes (ADR-0043, ADR-0045, ADR-0046, ADR-0039)
def test_gate_a1_fails_when_exp01_stopping_rule_fired(tmp_path, capsys, monkeypatch):
    """Gate A1 must fail if EXP-01 stopping rule fired, even if status is DONE."""
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-01 · Mining beta from prior repositories `DONE: stopping rule FIRED: history mining could not narrow interval`\n"
        "beta-measured: 0.3132 [0.2800, 0.3464]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    gate_a = doctor_payload(tmp_path, capsys)["gates"]["A"]
    condition = {c["id"]: c for c in gate_a["conditions"]}["A1"]
    assert condition["status"] == "fail", condition["reason"]
    assert "stopping rule fired" in condition["reason"].lower()


def test_gate_a1_fails_when_interval_half_width_exceeds_tolerance(
    tmp_path, capsys, monkeypatch
):
    """Gate A1 must fail if EXP-01 beta interval half-width is > 0.05."""
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-01 · Mining beta from prior repositories `DONE 20 Aug 2026`\n"
        "beta-measured: 0.3132 [0.1500, 0.4500]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    gate_a = doctor_payload(tmp_path, capsys)["gates"]["A"]
    condition = {c["id"]: c for c in gate_a["conditions"]}["A1"]
    assert condition["status"] == "fail", condition["reason"]
    assert "exceeds" in condition["reason"] and "0.05" in condition["reason"]


def test_gate_a1_passes_when_usable_interval_recorded(tmp_path, capsys, monkeypatch):
    """Gate A1 passes when EXP-01 is DONE and carries a usable interval (half-width <= 0.05)."""
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-01 · Mining beta from prior repositories `DONE 20 Aug 2026`\n"
        "beta-measured: 0.3132 [0.2800, 0.3464]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    gate_a = doctor_payload(tmp_path, capsys)["gates"]["A"]
    condition = {c["id"]: c for c in gate_a["conditions"]}["A1"]
    assert condition["status"] == "pass", condition["reason"]
    assert "0.3132" in condition["reason"]


def test_gate_b2_fails_when_exp08_not_done(tmp_path, capsys, monkeypatch):
    """Gate B2 must fail if EXP-08 is not DONE, even if a measurement tag exists."""
    monkeypatch.chdir(tmp_path)
    register = tmp_path / "docs" / "10-research" / "experiment-register.md"
    register.parent.mkdir(parents=True)
    register.write_text(
        "### EXP-08 · Critic recall `IN PROGRESS`\n"
        "critic-beta-measured: 0.31 [0.29, 0.33]\n",
        encoding="utf-8",
    )
    write_capture_days(tmp_path / "log", "2026-08-20")
    condition = _gate_b(tmp_path, capsys)["B2"]
    assert condition["status"] == "fail", condition["reason"]
    assert "must be DONE" in condition["reason"]


def test_b3_fails_on_unexpected_command_or_runner(tmp_path, capsys, monkeypatch):
    """Gate B3 fails if fallback result JSON has forged command or runner."""
    monkeypatch.chdir(tmp_path)

    # Wrong command
    bad_cmd = _fallback(1)
    bad_cmd["command"] = "claude -p 'do something else'"
    _b3_world(tmp_path, bad_cmd)
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail", condition["reason"]
    assert "unexpected command" in condition["reason"]

    # Wrong runner
    bad_runner = _fallback(1)
    bad_runner["runner"] = "scripts/forged_runner.py"
    _b3_world(tmp_path, bad_runner)
    condition = _gate_b(tmp_path, capsys)["B3"]
    assert condition["status"] == "fail", condition["reason"]
    assert "unexpected runner" in condition["reason"]


def test_gate_b4_ignores_bare_ticket_completed_and_repo_aliases(
    tmp_path, capsys, monkeypatch
):
    """Gate B4 ignores bare ticket.completed without verifier acceptance and filters internal repo aliases."""
    monkeypatch.chdir(tmp_path)
    _accepted_b4_docs(tmp_path)
    log = tmp_path / "log" / "2026-08-20.jsonl"

    # Bare ticket.completed without attempt.outcome is ignored
    append(
        log,
        ev(
            event="ticket.completed",
            data={"repository": "foreign-repo", "ticket": "T1"},
        ),
    )
    # Internal repo aliases are ignored even with outcome
    for idx, alias in enumerate(("consilient", "consilience", "joe-hireable/consilient", "consilient-work")):
        append(
            log,
            ev(
                event="attempt.outcome",
                data={"repository": alias, "attempt_id": f"a-{idx}", "task": f"T-{idx}", "verifier_accept": True},
            ),
        )
        append(
            log,
            ev(
                event="ticket.completed",
                data={"repository": alias, "ticket": f"T-{idx}", "attempt_id": f"a-{idx}"},
            ),
        )

    condition = _gate_b(tmp_path, capsys)["B4"]
    assert "0 of 20" in condition["reason"], condition["reason"]


def test_historical_refusal_digests_pin_real_log_rejections():
    """The baseline must match the trajectory, not just the fixture beside it.

    Until 21 Aug 2026 this hashed `HISTORICAL_REFUSAL_LINES` from this file and checked the
    digests were in `cli.HISTORICAL_REFUSAL_DIGESTS` — two hand-written constants agreeing
    with each other. Both could drift from the log together and nothing would notice, while
    `_capture_condition` silently widened A3's tolerance. Measured: the three pinned digests
    are exactly the three refusals in `.harness/log`, with none unpinned. That is the
    property; the fixture agreeing with the constant is only the mechanism.
    """
    import hashlib
    from consilient.cli import HISTORICAL_REFUSAL_DIGESTS

    assert len(HISTORICAL_REFUSAL_DIGESTS) == 3
    for line in HISTORICAL_REFUSAL_LINES:
        digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
        assert digest in HISTORICAL_REFUSAL_DIGESTS, f"digest {digest} not in baseline"

    log = Path(".harness/log")
    if not log.exists():  # pragma: no cover - repository-only check
        pytest.skip("no repository trajectory in this checkout")
    real = {rejection.content_digest for rejection in read_all(log)[1]}
    assert real == set(HISTORICAL_REFUSAL_DIGESTS), (
        "the tolerated baseline and the trajectory's actual refusals have diverged; "
        f"{len(real - set(HISTORICAL_REFUSAL_DIGESTS))} refusal(s) in the log are not "
        f"pinned, {len(set(HISTORICAL_REFUSAL_DIGESTS) - real)} pinned digest(s) match "
        "nothing in the log"
    )



# ------------------------------------------- publication safety, after the 21 Aug 2026 block
def test_foreign_commit_identifiers_may_only_decrease():
    """A pre-publication audit blocked a public push over identifiers no path-matcher can see.

    `check_private_corpus.py` matches FILE PATHS from the private corpora and passed. What it
    could not see: `results-exp43.json` carries **71 forty-character commit SHAs**, none of
    which resolves in this repository. They are commits from a private commercial repository.

    `AGENTS.md` permits the corpora's names and AGGREGATE measured metrics. A list of specific
    commits is neither — it is a list of incidents.

    The count below is the measured state at the moment of discovery and may only ever go DOWN.
    Lowering it is the permitted edit; the fix for EXP-43 is to aggregate the identifiers, not
    to raise this number.
    """
    import subprocess

    script = Path(".github/scripts/check_foreign_identifiers.py")
    if not script.exists():  # pragma: no cover - repository-only check
        pytest.skip("checker not present in this checkout")
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    # One reported line per offending file, plus the header and the two-line explanation.
    offenders = [line for line in result.stdout.splitlines() if line.startswith("- ")]
    total = 0
    for line in offenders:
        match = re.search(r": (\d+) identifier", line)
        if match:
            total += int(match.group(1))

    # Lowered from 85 to 14 on 21 Aug 2026 after EXP-43's 71 private-corpus commit identifiers
    # were pseudonymised. The 14 that remain are benign and identified: ten are GitHub permalinks
    # citing upstream projects (julep-ai/julep, mlflow/mlflow), three reference EXP-49's
    # pre-registration commit, one is EXP-05's. A ratchet only goes down.
    assert total <= 14, (
        f"foreign commit identifiers rose to {total}; publishing them would put another "
        "repository's commit history into a public one. Aggregate them instead."
    )


# ------------------------------------------- packaging and exit codes, 21 August 2026
# `pip install .` failed on a clean machine: neither `pyproject.toml` nor `setup.py`
# existed, so the `consil` entry point that `packages/consil/README.md` and thirty-odd
# documents refer to could not be installed by anyone. These pin the repair.


def _pyproject() -> dict:
    import tomllib

    return tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))


def test_the_consil_entry_point_resolves_to_a_real_callable():
    """A declared console script that does not import is a broken install, not a typo."""
    import importlib

    target = _pyproject()["project"]["scripts"]["consil"]
    module_name, _, attribute = target.partition(":")
    assert module_name and attribute, f"malformed entry point {target!r}"
    resolved = getattr(importlib.import_module(module_name), attribute)
    assert callable(resolved), f"{target} is not callable"


def test_the_declared_python_floor_matches_mypy():
    """Two files state the supported interpreter. They must not drift apart.

    `requires-python` is what pip enforces on a stranger's machine; `python_version` in
    mypy.ini is what the type checker assumes. If the floor is lowered in one and not the
    other, the gate type-checks against a version pip will not install on.
    """
    declared = _pyproject()["project"]["requires-python"]
    assert declared.startswith(">="), f"floor {declared!r} is not a simple lower bound"
    floor = declared.removeprefix(">=").strip()
    mypy_ini = Path("mypy.ini").read_text(encoding="utf-8")
    assert f"python_version = {floor}" in mypy_ini, (
        f"pyproject requires-python is {declared!r} but mypy.ini does not target {floor}"
    )


def test_the_package_declares_no_runtime_dependencies():
    """`consilient` is standard library only. A new dependency is a decision, not a diff.

    AGENTS.md requires a new dependency to be argued. Nothing enforced that, so this does:
    adding one fails here and the commit has to say what it bought.
    """
    assert _pyproject()["project"]["dependencies"] == [], (
        "consilient gained a runtime dependency; say in the commit what it buys and why "
        "the standard library could not"
    )


def test_doctor_exits_nonzero_while_the_gates_are_shut(tmp_path, capsys):
    """`consil doctor` printed `Gate A: FAIL` and exited 0 until 21 August 2026.

    `main()` returned `0 if result.get("identical", True) else 1`, and `cmd_doctor`'s
    result carries no `identical` key, so every doctor invocation returned 0 whatever the
    gates said. ADR-0015's Enforcement clause calls this command "Not advisory"; a command
    whose failure a caller cannot read from `$?` is advisory. B9 in the guard catalogue is
    the same mistake made accidentally with a pipe.
    """
    write_capture_days(tmp_path / "log", "2026-08-20")
    code = main(
        ["--log", str(tmp_path / "log"), "--db", str(tmp_path / "state.db"), "--json", "doctor"]
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["routing_orchestration_enabled"] is False, "fixture should not open the gates"
    assert code == 1, "doctor reported shut gates and told its caller they were open"


def test_doctor_exits_zero_when_every_gate_passes(tmp_path, capsys, monkeypatch):
    """The other direction, so the exit code is a report and not a constant.

    Building a world where all seven conditions pass needs evidence this repository does
    not have. The mapping from payload to exit code is what is under test here, so the
    payload is supplied directly.
    """
    from consilient import cli as cli_mod

    monkeypatch.setattr(
        cli_mod,
        "cmd_doctor",
        lambda args: {"gates": {}, "routing_orchestration_enabled": True},
    )
    assert main(["--json", "doctor"]) == 0
    assert json.loads(capsys.readouterr().out)["routing_orchestration_enabled"] is True


def test_gate_a2_does_not_pass_on_an_empty_trajectory(tmp_path, capsys):
    """Comparing zero events to zero events is not evidence that replay works.

    Measured 21 August 2026 from a clean install in an empty directory: two `consil doctor`
    runs reported A2 `pass`, reason "Compared 0 events; canonical state is identical." The
    first run creates the state the second one compares against, and both are rebuilds of
    the same empty log. That is A1 — two rebuilds compared — one invocation further out.
    """
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    log_dir.mkdir(parents=True)
    projection.build(log_dir, db).close()  # a prior projection exists, over zero events

    condition = {
        c["id"]: c for c in doctor_payload(tmp_path, capsys)["gates"]["A"]["conditions"]
    }["A2"]

    assert condition["status"] == "unknown", condition["reason"]
    assert "zero events" in condition["reason"]


def test_gate_a2_still_passes_on_a_non_empty_identical_replay(tmp_path, capsys):
    """The narrowing must not have blunted the condition it narrows."""
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    write_capture_days(log_dir, "2026-08-20")
    projection.build(log_dir, db).close()

    condition = {
        c["id"]: c for c in doctor_payload(tmp_path, capsys)["gates"]["A"]["conditions"]
    }["A2"]

    assert condition["status"] == "pass", condition["reason"]
    assert "Compared 1 events" in condition["reason"]


def test_ci_replay_step_carries_a_control_that_can_fail():
    """The CI replay step must not manufacture the subject it then compares against.

    Until 21 August 2026 it ran `beta` before `replay` "so that replay has a subject". The
    subject `cmd_beta` leaves behind is a rebuild from the same log — it calls
    `projection.build`, which unlinks the database — so `identical: true` was guaranteed.
    A fresh checkout carries no `.harness/state.db` at all; it is gitignored. Measured:
    with that sequence, deliberate out-of-band drift produced `identical: true` and the
    gate exited 0.
    """
    workflow = Path(".github/workflows/invariants.yml").read_text(encoding="utf-8")
    step = workflow.partition("- name: Replay invariant")[2]
    assert step, "the replay invariant step is gone"
    assert "cli --json beta" not in step, (
        "the replay step seeds its own comparison subject again; a rebuild is not evidence "
        "that the state on disk was intact"
    )
    assert "identical'] is False" in step or 'identical"] is False' in step, (
        "the replay step lost the drift control that proves it can fail"
    )

"""V0-02: the log is the only source of state, and a row it refuses is excluded AND
named. Half of these delete the database and rebuild it, smuggle a row straight into
SQLite, or drift the state out of band, and assert that `replay` says so — including the
distinction the first implementation could not make, that a log which has merely GROWN
reads as stale rather than diverged. That version reported DIVERGED on every ordinary
run of the real trajectory, and a check that cries wolf is worse than no check because
it trains its reader to ignore it; the narrowing must not blunt the check it narrows, so
real drift with matching counts is still caught, and state that is both stale and
drifted is preserved rather than unlinked before anything compares it. The other half
are the relational quarantines: an outcome with no `attempt_id`, a verdict for an
unknown attempt, a duplicate attempt identity, a second verdict for one attempt. Each is
kept out of β's table and recorded with its reason, and
`test_beta_reports_what_the_log_refused` closes the circle — a quarantine is only not-a-
silent-skip if it appears where the number appears, because a rate computed over a
quietly shortened denominator is the failure this measures."""

import json
import sqlite3
import sys
from pathlib import Path
import pytest
from consilient import beta as beta_mod
from consilient import projection
from consilient.cli import main
from consilient.events import (
    append,
    canonical,
    read,
)
from v0_invariants_helpers import (
    _spend_scripts,
    append_judged,
    ev,
    outcome,
    verdict,
)


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
    assert conn.execute(
        "SELECT estimand_kind, auth_status FROM outcomes"
    ).fetchone() == (beta_mod.HUMAN_VERDICT_BETA, "declared_principal")
    result = beta_mod.from_connection(conn)
    assert result.verdict == beta_mod.INSUFFICIENT
    assert result.n_rejected == 0
    assert result.n_false_accept == 0
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


def test_a_verdict_for_an_unknown_attempt_is_quarantined_and_replay_continues(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("attempt-001", "valid-before", True))
    append(path, verdict("missing-attempt", "reject"))
    append(path, outcome("attempt-002", "valid-after", False))
    append(path, verdict("attempt-002", "accept"))

    conn = projection.build(log_dir, db)
    assert conn.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0] == 2
    reasons = projection.relational_quarantines(conn)
    assert len(reasons) == 1 and "unknown attempt" in reasons[0]["reason"]
    conn.close()


def test_two_verdicts_for_one_attempt_quarantine_the_duplicate(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("attempt-001", "t", True))
    for human_verdict in ("accept", "reject"):
        append(path, verdict("attempt-001", human_verdict))

    conn = projection.build(log_dir, db)
    assert (
        conn.execute(
            "SELECT human_verdict FROM outcomes WHERE attempt_id = 'attempt-001'"
        ).fetchone()[0]
        == "accept"
    )
    reasons = projection.relational_quarantines(conn)
    assert len(reasons) == 1 and "already has a verdict" in reasons[0]["reason"]
    conn.close()


def test_duplicate_attempt_identity_quarantines_the_later_row(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    for task in ("first-task", "second-task"):
        append(path, outcome("attempt-001", task, True))

    conn = projection.build(log_dir, db)
    assert (
        conn.execute(
            "SELECT task FROM outcomes WHERE attempt_id = 'attempt-001'"
        ).fetchone()[0]
        == "first-task"
    )
    reasons = projection.relational_quarantines(conn)
    assert len(reasons) == 1 and "duplicate attempt_id" in reasons[0]["reason"]
    conn.close()


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
    assert conn.execute(
        "SELECT estimand_kind, auth_status FROM outcomes WHERE attempt_id = 'attempt-002'"
    ).fetchone() == (beta_mod.HUMAN_VERDICT_BETA, "declared_principal")
    result = beta_mod.from_connection(conn)
    assert result.verdict == beta_mod.INSUFFICIENT
    assert result.n_rejected == 0 and result.n_false_accept == 0
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


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)

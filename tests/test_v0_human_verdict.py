"""β is measured against the human verdict, so if an agent can author that verdict, β
measures nothing. This is V0-18's second path, found on 20 August 2026:
`_check_human_authority` returned early whenever `human_decision` was absent, while
`projection._apply_outcome` read `human_verdict` directly — a second route to a guarded
state, which is the `jobboard-v2` failure this project was founded on, occurring inside
the instrument. The forgeries covered are omission, naming the principal without holding
the authority, filing the verdict as a different decision, and a null correction that
would erase the label; the legitimate paths must still work, so a deferred verdict and
an explicit correction naming its prior state and its reason are accepted, and a
correction against the wrong prior state or with no verdict to correct is quarantined
rather than applied. Both layers are tested, because defence in depth is only defence if
the second layer is tested too: since 20 August 2026 `validate` refuses an unknown
verdict before it can reach the log at all, and the projection refuses it again at read
— asserting the property rather than the mechanism, after the old version asserted that
`build` raised and would have made any future tightening of `validate` retroactively
fatal to the whole record. `scripts/verdict.py` is the operator's only route to
recording one, and `--checks` is required so that β cannot be 1.000 by construction."""

import sqlite3
import sys
from pathlib import Path
import pytest
from consilient import beta as beta_mod
from consilient import events as events_mod
from consilient import projection
from consilient.events import (
    EventError,
    append,
    canonical,
    validate,
)
from v0_invariants_helpers import (
    HUMAN,
    _read_live_trajectory,
    _spend_scripts,
    ev,
    now_ts,
    outcome,
    verdict,
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
    assert conn.execute(
        "SELECT estimand_kind, auth_status FROM outcomes WHERE attempt_id = 'attempt-001'"
    ).fetchone() == (beta_mod.HUMAN_VERDICT_BETA, "declared_principal")
    result = beta_mod.from_connection(conn)
    assert result.verdict == beta_mod.INSUFFICIENT
    assert result.n_rejected == 0
    assert result.n_false_accept == 0
    conn.close()


def test_a_correction_against_the_wrong_prior_verdict_is_quarantined(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("attempt-001", "t", True))
    append(path, verdict("attempt-001", "accept"))
    append(
        path,
        verdict_correction("attempt-001", "reject", "accept", "mistyped prior state"),
    )

    conn = projection.build(log_dir, db)
    assert (
        conn.execute(
            "SELECT human_verdict FROM outcomes WHERE attempt_id = 'attempt-001'"
        ).fetchone()[0]
        == "accept"
    )
    reasons = projection.relational_quarantines(conn)
    assert len(reasons) == 1 and "expected prior verdict" in reasons[0]["reason"]
    conn.close()


def test_a_correction_without_an_existing_verdict_is_quarantined(tmp_path):
    log_dir, db = tmp_path / "log", tmp_path / "state.db"
    path = log_dir / "2026-08-20.jsonl"
    append(path, outcome("attempt-001", "t", True))
    append(
        path,
        verdict_correction(
            "attempt-001", "accept", "reject", "review changed the judgement"
        ),
    )

    conn = projection.build(log_dir, db)
    assert (
        conn.execute(
            "SELECT human_verdict FROM outcomes WHERE attempt_id = 'attempt-001'"
        ).fetchone()[0]
        is None
    )
    reasons = projection.relational_quarantines(conn)
    assert len(reasons) == 1 and "no verdict to correct" in reasons[0]["reason"]
    conn.close()


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
        # V01 gave _apply_outcome a fourth parameter when it added verdict quarantining.
        # The set is empty because this test asserts the refusal of a combined
        # outcome-and-verdict event, which is decided before any attempt lookup.
        projection._apply_outcome(conn, 0, combined, set())
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


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)


# ------------------------------------------- the cost of recording one verdict
def _verdict_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "verdict", Path("scripts/verdict.py").resolve()
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verdict_script_preserves_order_checks_and_declared_principal_beta_exclusion(
    tmp_path,
):
    """The script writes valid joins in outcome-before-verdict order.

    Relationally invalid rows quarantine so replay can continue. The caller-supplied
    principal is declared, not authenticated, and neither CLI row enters beta.
    """
    module = _verdict_module()
    log = tmp_path / "log"
    common = ["--log", str(log), "--principal", "reviewer"]
    assert module.main(["reject", "fix pagination", "--checks", "pass", *common]) == 0
    assert module.main(["accept", "retry backoff", "--checks", "fail", *common]) == 0

    events, rejected = _read_live_trajectory(log)
    assert not rejected, [r.reason for r in rejected]
    recorded = set()
    for event in events:
        attempt_id = event.raw["data"]["attempt_id"]
        if event.kind == events_mod.OUTCOME_KIND:
            recorded.add(attempt_id)
        else:
            assert attempt_id in recorded, (
                f"verdict for {attempt_id!r} precedes its outcome; the trajectory is "
                "outside the current quarantine-safe contract"
            )

    checks = [
        event.raw["data"]["verifier_accept"]
        for event in events
        if event.kind == events_mod.OUTCOME_KIND
    ]
    assert checks == [True, False], (
        "--checks must record what the checks said, both ways"
    )

    conn = projection.build(log, tmp_path / "state.db")
    result = beta_mod.from_connection(conn, None, None)
    assert conn.execute(
        "SELECT auth_status FROM outcomes ORDER BY position"
    ).fetchall() == [("declared_principal",), ("declared_principal",)]
    assert result.verdict == beta_mod.INSUFFICIENT
    assert result.window is None
    assert result.n_rejected == 0
    assert result.n_false_accept == 0
    conn.close()


def test_verdict_script_refuses_to_guess_what_the_checks_said(tmp_path):
    """`--checks` is required so that beta cannot be 1.000 by construction.

    Review only what the checks already passed and every rejected row carries
    verifier_accept=True, so beta is 1 by sampling rather than by measurement
    (`src/consilient/beta.py`). A default would make that the silent path.
    """
    module = _verdict_module()
    with pytest.raises(SystemExit):
        # --log is passed only so that a regression here writes to a temporary
        # directory rather than into the real trajectory.
        module.main(["reject", "no checks named", "--log", str(tmp_path / "log")])

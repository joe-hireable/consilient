"""The record itself: what `validate` and `append` will accept as an event, and who may
author one. V0-01 covers the schema version, the explicit offset, the append-only prefix
digest and the quarantine of a malformed line — that last one asserted `pytest.raises`
until 20 August 2026, and raising made one bad line fatal to a file nobody can edit,
which is how three events appended at 09:41–09:56 that day killed `replay` and `beta` on
the real trajectory. V0-01's clock half belongs here for the same reason: `validate`
checked the FORMAT of `ts` and its offset, both impeccable, and never asked whether the
value was true, while the orchestrator wrote six consecutive trajectory events with
invented timestamps drifting to 2h15m ahead of the wall clock. A format check on a
timestamp is not a check on a timestamp, and the check belongs to `append` alone, or
every log would become unreadable as it aged. V0-18 governs who may author a human
decision — including R19's consent grants, where the same rule decides whether data may
leave at all — and V0-28 governs which transport may deliver one, with a self-reported
signature refused because no signature verifier exists. This file keeps the original
name because every other family is downstream of it.

Preserved from before the 28 August 2026 split, which rewrote this docstring and carried
the paragraph below into no sibling. It is reproduced WHOLE. An earlier restoration took
only the individual lines a checker had reported missing, which spliced halves of two
different sentences together beneath a claim of being verbatim -- found by an outside
review on 29 August 2026.

    Every test names the invariant it enforces. Invariant I1: a declared chokepoint ships with
    the check that bans bypassing it, in the same commit.
"""

import sys
import pytest
from consilient import events as events_mod
from consilient.events import (
    SCHEMA_VERSION,
    EventError,
    append,
    canonical,
    prefix_digest,
    read,
    validate,
)
from v0_invariants_helpers import (
    HUMAN,
    _spend_scripts,
    ev,
    now_ts,
    verdict,
)


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


def test_consent_purposes_are_exactly_the_three_named_purposes():
    """R19: improvement and training consent are separately obtained, never bundled;
    commercial training exists only as per-use grants. Adding a fourth purpose is a
    decision, not a silent widen."""
    assert events_mod.CONSENT_PURPOSES == {
        "improve-consilient",
        "train-consilient",
        "commercial-training",
    }


def _consent_grant(actor, **data_over):
    data = {
        "purpose": "improve-consilient",
        "retention_days": 365,
        "principal": HUMAN,
        "via": "cli",
        **data_over,
    }
    return ev(event="consent.granted", actor=actor, data=data)


def test_principal_can_author_a_consent_grant():
    validate(_consent_grant(HUMAN))


def test_agent_cannot_author_a_consent_grant():
    with pytest.raises(EventError, match="only the principal may author"):
        validate(_consent_grant("claude-senior-orchestrator"))


def test_an_agent_cannot_author_consent_by_omitting_human_decision():
    """The 20 August verdict hole, on the event that would authorise data leaving."""
    grant = _consent_grant("agent")
    assert "human_decision" not in grant["data"]
    with pytest.raises(EventError, match="only the principal may author"):
        validate(grant)


def test_consent_grant_without_retention_is_refused():
    grant = _consent_grant(HUMAN)
    del grant["data"]["retention_days"]
    with pytest.raises(EventError, match="retention_days"):
        validate(grant)


def test_consent_grant_with_non_positive_retention_is_refused():
    with pytest.raises(EventError, match="retention_days"):
        validate(_consent_grant(HUMAN, retention_days=0))
    with pytest.raises(EventError, match="retention_days"):
        validate(_consent_grant(HUMAN, retention_days=True))


def test_consent_grant_with_unknown_purpose_is_refused():
    with pytest.raises(EventError, match="purposes are not bundled"):
        validate(_consent_grant(HUMAN, purpose="marketing"))


def test_commercial_training_consent_is_per_use_or_refused():
    """R19's third limb: commercial gain requires fresh consent for each use."""
    with pytest.raises(EventError, match="per_use"):
        validate(_consent_grant(HUMAN, purpose="commercial-training"))
    with pytest.raises(EventError, match="use_ref"):
        validate(_consent_grant(HUMAN, purpose="commercial-training", per_use=True))
    validate(
        _consent_grant(
            HUMAN,
            purpose="commercial-training",
            per_use=True,
            use_ref="the one named authorised use",
        )
    )


def test_consent_withdrawal_carries_no_commercial_grant_fields():
    with pytest.raises(EventError, match="withdrawal"):
        validate(
            ev(
                event="consent.withdrawn",
                actor=HUMAN,
                data={
                    "purpose": "commercial-training",
                    "principal": HUMAN,
                    "via": "cli",
                    "per_use": True,
                    "use_ref": "sneaking a grant into a withdrawal",
                },
            )
        )


def test_consent_event_cannot_be_filed_as_a_different_decision():
    with pytest.raises(EventError, match="may not be filed as anything else"):
        validate(_consent_grant(HUMAN, human_decision="approval"))


def test_principal_can_author_a_consent_withdrawal():
    validate(
        ev(
            event="consent.withdrawn",
            actor=HUMAN,
            data={
                "purpose": "improve-consilient",
                "principal": HUMAN,
                "via": "cli",
            },
        )
    )


def test_agent_cannot_author_a_consent_withdrawal():
    with pytest.raises(EventError, match="only the principal may author"):
        validate(
            ev(
                event="consent.withdrawn",
                actor="codex-root",
                data={
                    "purpose": "improve-consilient",
                    "principal": HUMAN,
                    "via": "cli",
                },
            )
        )


# ---------------------------------------------------------------- V0-28
@pytest.mark.parametrize(
    "decision",
    ("verdict", "approval", "consent", "gate_lift", "spend_authorisation"),
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


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)

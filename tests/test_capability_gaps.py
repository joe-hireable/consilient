"""V0-41, part one: what a capability gap *is*, and which class a failure falls into.

Two halves of a single rule, tested from both sides. The schema half pins the event
contract — a gap names what was asked, what was attempted, how it failed (one of four
classes that may not be conflated), and which side of the self-healing boundary it sits
on — and refuses a payload missing any required field, carrying an unknown failure class
or an unknown closure. The cross-field rule is the load-bearing one: `silent` and
`not_implemented` may never claim `retry`, because a silent run already reported success
while doing nothing, and an unattended retry repeats the lie with pool spend attached.
`refused` and `failed` may retry.

The policy half pins `classify_gap`, which is what must never produce a payload the
schema would reject. A missing install or an absent invocation is `not_implemented` and
escalates; an exhausted pool or a claim conflict is `refused` and retries, because time
closes it; an unrecognised refusal escalates rather than guessing. The aggregate refusal
— "every pool is exhausted, unknown, or not installed" — is ambiguous from prose alone,
since it may name a resettable window or a missing install, and it fails closed as
`not_implemented`/`escalate` because guessing is the failure this event exists to
record. That one is pinned deliberately: loosening it is a policy change, not a test
fix.

The last test is the seam between the halves. The classifier matches markers in prose
this codebase actually writes, so it drives `select` for real and classifies the reason
it produces; reword a refusal upstream and this fails loudly instead of misclassifying
quietly.

Preserved from before the 28 August 2026 split, which rewrote this docstring and carried
the paragraph below into no sibling. It is reproduced WHOLE. An earlier restoration took
only the individual lines a checker had reported missing, which spliced halves of two
different sentences together beneath a claim of being verbatim -- found by an outside
review on 29 August 2026.

    The invariant has three parts, each with a check here:
      1. the event contract — a gap names what was asked, what was attempted, how it failed
         (one of four classes that may not be conflated), and which side of the self-healing
         boundary it sits on; `silent` and `not_implemented` may never claim `retry`;
      2. the wiring — the existing dispatch chokepoints (record_refusal, record_outcome)
         record the gap alongside their own event, so a caller cannot forget it;
      3. the view — the dashboard ranks gaps by repetition, because a gap hit twice is a
         stronger signal than a novel one, and states the retry/escalate boundary in words.
"""

from datetime import datetime, timezone
import pytest
from consilient.events import EventError, append, read, validate
from consilient.harness import (
    DEFAULT_POOLS,
    HARNESSES,
    Probe,
    classify_gap,
    select,
)
from capability_gap_helpers import (
    INSTALLED,
    _append_gap,
    _gap_data,
)


def test_a_well_formed_gap_is_accepted_and_readable(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    recorded = _append_gap(tmp_path, ts)
    events, rejected = read(tmp_path / f"{ts[:10]}.jsonl")
    assert not rejected
    assert events[0].raw == recorded
    assert events[0].kind == "capability.gap"


@pytest.mark.parametrize(
    "field", ("asked", "attempted", "detail", "repair", "run_id", "source")
)
def test_a_gap_missing_a_required_field_is_refused(tmp_path, field):
    ts = datetime.now(timezone.utc).isoformat()
    data = _gap_data()
    data.pop(field)
    with pytest.raises(EventError, match=field):
        append(
            tmp_path / f"{ts[:10]}.jsonl",
            {
                "v": 1,
                "ts": ts,
                "event": "capability.gap",
                "actor": "dispatch",
                "data": data,
            },
        )


def test_a_gap_with_an_unknown_failure_class_is_refused(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    with pytest.raises(EventError, match="failure"):
        _append_gap(tmp_path, ts, failure="crashed")


def test_a_gap_with_an_unknown_closure_is_refused(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    with pytest.raises(EventError, match="closure"):
        _append_gap(tmp_path, ts, closure="ignore")


def test_a_silent_gap_may_not_claim_to_retry(tmp_path):
    # The cross-field rule: a silent run already reported success while doing nothing;
    # an unattended retry repeats the lie with pool spend attached.
    ts = datetime.now(timezone.utc).isoformat()
    with pytest.raises(EventError, match="escalate"):
        _append_gap(tmp_path, ts, failure="silent", closure="retry")


def test_a_not_implemented_gap_may_not_claim_to_retry(tmp_path):
    ts = datetime.now(timezone.utc).isoformat()
    with pytest.raises(EventError, match="escalate"):
        _append_gap(tmp_path, ts, failure="not_implemented", closure="retry")


@pytest.mark.parametrize("failure", ("refused", "failed"))
def test_a_loud_or_policy_gap_may_retry(tmp_path, failure):
    ts = datetime.now(timezone.utc).isoformat()
    recorded = _append_gap(tmp_path, ts, failure=failure, closure="retry")
    assert validate(recorded)["data"]["closure"] == "retry"


def test_classify_gap_leaves_a_success_alone():
    assert classify_gap("ok", "") is None


def test_classify_gap_escalates_a_silent_run():
    failure, closure, repair = classify_gap("silent", "exit 0, no artefact")
    assert (failure, closure) == ("silent", "escalate")
    assert "human" in repair


@pytest.mark.parametrize("status", ("failed", "timeout"))
def test_classify_gap_retries_a_loud_failure(status):
    failure, closure, _ = classify_gap(status, "exit 1")
    assert (failure, closure) == ("failed", "retry")


@pytest.mark.parametrize(
    "reason",
    (
        "grok is not installed",
        "binary not on PATH",
        "no invocation for harness 'cursor'",
        "unknown harness 'hal'",
        "no models registered for cursor",
    ),
)
def test_classify_gap_escalates_a_missing_capability(reason):
    failure, closure, _ = classify_gap("refused", reason)
    assert (failure, closure) == ("not_implemented", "escalate")


@pytest.mark.parametrize(
    "reason",
    (
        "claude is exhausted (92% used)",
        "claims overlap a live dispatch: other-run holds src",
    ),
)
def test_classify_gap_retries_what_time_closes(reason):
    failure, closure, _ = classify_gap("refused", reason)
    assert (failure, closure) == ("refused", "retry")


def test_classify_gap_escalates_an_unrecognised_refusal():
    failure, closure, repair = classify_gap("refused", "policy forbids this cwd")
    assert (failure, closure) == ("refused", "escalate")
    assert "human" in repair


def test_the_aggregate_selection_refusal_escalates_rather_than_guesses():
    # "every pool is exhausted, unknown, or not installed" is ambiguous from prose
    # alone: it may name a resettable window or a missing install. The record fails
    # closed — not_implemented, escalate — because guessing is the failure this event
    # exists to record. Pinned deliberately: loosening this is a policy change.
    reason = (
        "no eligible harness: every pool is exhausted, unknown, or not installed. "
        "claude: exhausted; grok: not installed"
    )
    failure, closure, _ = classify_gap("refused", reason)
    assert (failure, closure) == ("not_implemented", "escalate")


def test_the_reasons_select_generates_classify_as_intended():
    # The markers match prose this codebase writes, and this is the check that keeps
    # them matched: reword the reason and this fails loudly instead of misclassifying.
    exhausted = select(probes=INSTALLED, pools=DEFAULT_POOLS, requested="claude")
    assert exhausted.kind == "refuse"
    assert classify_gap("refused", exhausted.reason)[:2] == ("refused", "retry")

    missing = select(
        probes=tuple(Probe(item.id, False, None, "missing") for item in HARNESSES),
        pools=DEFAULT_POOLS,
        requested="grok",
    )
    assert missing.kind == "refuse"
    assert classify_gap("refused", missing.reason)[:2] == (
        "not_implemented",
        "escalate",
    )

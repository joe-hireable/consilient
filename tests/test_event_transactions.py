"""F02 — atomic compare-and-append transaction: the checks.

`events.append` validates a candidate against itself alone. A rule that depends on
the current state of the log — "this claim is still unheld", "this revision is
still the tip" — had no honest place to run, and ADR-0070's evidence names the
consequence: central `events.append()` called only `events.validate()`, so a
helper's domain rule could be bypassed through the generic door. [measured:
ADR-0070 evidence] These tests pin the repair, `append_transaction(log_dir,
candidates, transition_validator)`: every candidate is validated before any byte
is written, the accepted prefix and the rejections are read while holding the
F01 per-log lock and handed to a pure transition validator, and only then is the
batch written contiguously with one fsync. A rule registered with
`register_transition_validator` runs inside that same transaction whichever door
the caller takes, so `consil record` cannot bypass it. A failure at any point —
before validation, between candidates, before the fsync or after it — returns no
success acknowledgement, and a partial multi-event success is never returned.
"""

from __future__ import annotations

import multiprocessing
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from consilient import events as events_mod
from consilient.events import (
    SCHEMA_VERSION,
    EventError,
    append,
    append_transaction,
    read,
    register_transition_validator,
)


def ev(**over):
    base = {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "test.txn",
        "actor": "transaction-test",
        "data": {},
    }
    base.update(over)
    return base


def _only_log(log_dir: Path) -> Path:
    logs = list(log_dir.glob("*.jsonl"))
    assert len(logs) == 1, f"expected exactly one daily log, found {logs}"
    return logs[0]


def _unique_claim_validator(prefix, rejections, candidates):
    """Admit a claim only while no accepted event already holds it."""
    wanted = candidates[0]["data"]["claim"]
    for event in prefix:
        if event.data.get("claim") == wanted:
            raise EventError(f"claim {wanted!r} is already held")


def _contend(log_dir: str, claim: str, go, results) -> None:
    """Child worker: wait for the starting gun, then try to admit the claim."""
    go.wait()
    candidate = ev(event="test.txn.claim", data={"claim": claim})
    try:
        append_transaction(Path(log_dir), [candidate], _unique_claim_validator)
        results.put("admitted")
    except EventError:
        results.put("refused")


def test_candidates_are_validated_before_any_byte_is_written(tmp_path):
    append_transaction_calls = []

    def spy(prefix, rejections, candidates):
        append_transaction_calls.append((prefix, rejections, candidates))

    log_dir = tmp_path
    with pytest.raises(EventError, match="non-empty string"):
        append_transaction(
            log_dir,
            [ev(data={"n": 1}), ev(data={"n": 2}, actor="")],
            spy,
        )
    assert append_transaction_calls == [], "the validator ran on invalid candidates"
    assert list(log_dir.glob("*.jsonl")) == [], "an invalid candidate still created the log"


def test_the_validator_receives_the_locked_prefix_and_rejections(tmp_path):
    log = tmp_path / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    append(log, ev(event="test.txn.pre", data={"n": 1}))
    append(log, ev(event="test.txn.pre", data={"n": 2}))
    with log.open("a", encoding="utf-8") as fh:
        fh.write("this is not json\n")

    seen = []

    def spy(prefix, rejections, candidates):
        seen.append((prefix, rejections, candidates))

    batch = [ev(event="test.txn.new", data={"n": 3})]
    acknowledged = append_transaction(tmp_path, batch, spy)

    assert acknowledged == batch
    assert len(seen) == 1
    prefix, rejections, candidates = seen[0]
    assert [event.data["n"] for event in prefix] == [1, 2]
    assert len(rejections) == 1
    assert rejections[0].line == 3
    assert "not valid JSON" in rejections[0].reason
    assert list(candidates) == batch

    events, rejected = read(log)
    assert [event.data["n"] for event in events] == [1, 2, 3]
    assert len(rejected) == 1, "the quarantined line stays quarantined, not dropped"


def test_a_rejection_is_never_treated_as_an_empty_history(tmp_path):
    """A log whose only line is quarantined is handed to the validator as one
    rejection, not as an empty accepted prefix."""
    log = tmp_path / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    log.write_bytes(b"this is not json\n")

    def refuse_if_any_rejection(prefix, rejections, candidates):
        if rejections:
            raise EventError("the history is not clean; refusing to compare")
        if prefix:
            raise EventError("unreachable in this fixture")

    with pytest.raises(EventError, match="not clean"):
        append_transaction(tmp_path, [ev()], refuse_if_any_rejection)
    assert log.read_bytes() == b"this is not json\n"


def test_two_contenders_sharing_a_stale_prefix_cannot_both_admit_a_unique_transition(
    tmp_path,
):
    """The Done criterion: both contenders built their candidate against the same
    empty prefix. Because the validator runs against the prefix while holding the
    per-log lock, the second contender re-reads after the first commit and
    refuses; exactly one unique transition admits."""
    ctx = multiprocessing.get_context("spawn")
    go = ctx.Event()
    results = ctx.Queue()
    procs = [
        ctx.Process(target=_contend, args=(str(tmp_path), "shared", go, results))
        for _ in range(2)
    ]
    for proc in procs:
        proc.start()
    go.set()
    for proc in procs:
        proc.join(timeout=60)
    for proc in procs:
        if proc.is_alive():
            proc.kill()
            proc.join(timeout=10)
    assert [proc.exitcode for proc in procs] == [0, 0], (
        "a contender process did not finish cleanly"
    )
    outcomes = sorted(results.get(timeout=5) for _ in procs)
    assert outcomes == ["admitted", "refused"]

    events, rejected = read(_only_log(tmp_path))
    assert not rejected
    assert [event.data["claim"] for event in events] == ["shared"]


def test_an_outcome_plus_closure_batch_is_durably_ordered_and_rereadable(tmp_path):
    """The positive half of the Done criterion: the batch lands contiguously, in
    candidate order, and is rereadable the moment the call returns."""
    log_dir = tmp_path
    batch = [
        ev(event="test.txn.outcome", data={"seq": 1}),
        ev(event="test.txn.closure", data={"seq": 2}),
    ]
    acknowledged = append_transaction(log_dir, batch, lambda p, r, c: None)
    assert acknowledged == batch

    log = _only_log(log_dir)
    lines = log.read_text(encoding="utf-8").splitlines()
    assert lines == [events_mod.canonical(candidate) for candidate in batch]
    events, rejected = read(log)
    assert not rejected
    assert [event.raw for event in events] == batch


def test_a_write_failure_between_candidates_rolls_the_whole_batch_back(
    tmp_path, monkeypatch
):
    """The negative half: candidate one's bytes land, candidate two's write fails,
    and the transaction truncates back to its start offset — no partial
    multi-event success is returned and no bytes are left behind."""
    log = tmp_path / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    append(log, ev(event="test.txn.pre", data={"marker": "before"}))
    before = log.read_bytes()

    marker = b"between-candidates-marker"
    real_write = os.write

    def failing_write(fd, data):
        if marker in bytes(data):
            raise OSError("injected write failure on the second candidate")
        return real_write(fd, data)

    monkeypatch.setattr("os.write", failing_write)
    with pytest.raises(EventError, match="not acknowledged"):
        append_transaction(
            tmp_path,
            [
                ev(event="test.txn.outcome", data={"seq": 1}),
                ev(event="test.txn.closure", data={"marker": marker.decode()}),
            ],
            lambda p, r, c: None,
        )

    assert log.read_bytes() == before, "a failed transaction left bytes behind"
    events, rejected = read(log)
    assert not rejected, "the rollback left a torn line behind"
    assert [event.data["marker"] for event in events] == ["before"], (
        "no false closure: neither batch event may survive the rollback"
    )


def test_an_fsync_failure_before_durability_acknowledges_nothing_and_rolls_back(
    tmp_path, monkeypatch
):
    log = tmp_path / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    append(log, ev(event="test.txn.pre", data={"marker": "before"}))
    before = log.read_bytes()

    def failing_fsync(fd):
        raise OSError("injected fsync failure")

    monkeypatch.setattr("os.fsync", failing_fsync)
    with pytest.raises(EventError, match="not acknowledged"):
        append_transaction(tmp_path, [ev(), ev()], lambda p, r, c: None)

    assert log.read_bytes() == before
    events, rejected = read(log)
    assert not rejected
    assert len(events) == 1


def test_a_failure_after_the_fsync_is_never_returned_as_a_partial_success(
    tmp_path, monkeypatch
):
    """The directory fsync runs after the batch is durable; its failure must
    still refuse the acknowledgement, and what it leaves behind is the complete
    batch or nothing — never half of one."""

    def fail(directory: Path) -> None:
        raise OSError("injected directory fsync failure")

    monkeypatch.setattr(events_mod, "_fsync_directory", fail)
    with pytest.raises(EventError, match="not acknowledged"):
        append_transaction(tmp_path, [ev(data={"seq": 1}), ev(data={"seq": 2})], lambda p, r, c: None)

    events, rejected = read(_only_log(tmp_path))
    assert not rejected, "no partial JSON line may be left behind"
    assert [event.data["seq"] for event in events] in ([], [1, 2]), (
        "a partial multi-event state is never visible"
    )


def test_a_prefix_read_failure_is_refused_not_treated_as_an_empty_history(
    tmp_path, monkeypatch
):
    """If the accepted prefix cannot be read, the transaction fails rather than
    comparing against an assumed empty history."""
    calls = []

    def spy(prefix, rejections, candidates):
        calls.append((prefix, rejections, candidates))

    def unreadable(path, fd):
        raise OSError("injected read failure")

    monkeypatch.setattr(events_mod, "_read_under_lock", unreadable)
    with pytest.raises(EventError, match="not acknowledged|refused"):
        append_transaction(tmp_path, [ev()], spy)
    assert calls == [], "the validator ran against an unread prefix"
    assert list(tmp_path.glob("*.jsonl")), "the log file itself may exist"
    events, rejected = read(_only_log(tmp_path))
    assert events == [] and rejected == []


def test_plain_append_cannot_bypass_a_registered_domain_rule(tmp_path):
    """`consil record` reaches the log through `append`; a registered rule must
    govern that door too, or the transaction is a boundary nobody has to use."""
    kind = "test.txn.governed.frontdoor"
    seen = []

    def only_one(prefix, rejections, candidates):
        seen.append(len(prefix))
        for event in prefix:
            if event.kind == kind:
                raise EventError("only one governed event is admitted")

    register_transition_validator([kind], only_one)
    log = tmp_path / "governed.jsonl"

    append(log, ev(event=kind, data={"n": 1}))
    with pytest.raises(EventError, match="only one governed event"):
        append(log, ev(event=kind, data={"n": 2}))

    assert seen == [0, 1], "the rule ran against the live prefix both times"
    events, rejected = read(log)
    assert not rejected
    assert [event.data["n"] for event in events] == [1]


def test_append_transaction_runs_registered_rules_alongside_the_caller_validator(
    tmp_path,
):
    """The batch door cannot bypass a registered rule by supplying a permissive
    caller validator of its own."""
    kind = "test.txn.governed.batch"

    def always_refuse(prefix, rejections, candidates):
        raise EventError("the registered rule refuses this kind")

    register_transition_validator([kind], always_refuse)
    with pytest.raises(EventError, match="the registered rule refuses"):
        append_transaction(
            tmp_path, [ev(event=kind)], lambda p, r, c: None
        )
    # The lock needs a descriptor, so the file may exist; what matters is that
    # no byte of the refused batch does — the same residue F01's rollback leaves.
    events, rejected = read(_only_log(tmp_path))
    assert events == [] and rejected == []


def test_registration_refuses_budget_kinds_and_duplicate_kinds():
    with pytest.raises(EventError, match="budget"):
        register_transition_validator(
            [events_mod.BUDGET_STATE_KIND], lambda p, r, c: None
        )
    with pytest.raises(EventError, match="budget"):
        register_transition_validator(
            [events_mod.SPEND_RESERVED_KIND], lambda p, r, c: None
        )

    kind = "test.txn.governed.duplicate"
    register_transition_validator([kind], lambda p, r, c: None)
    with pytest.raises(EventError, match="already"):
        register_transition_validator([kind], lambda p, r, c: None)


def test_a_transaction_requires_at_least_one_candidate_and_one_log(tmp_path):
    with pytest.raises(EventError, match="at least one candidate"):
        append_transaction(tmp_path, [], lambda p, r, c: None)

    today = datetime.now(timezone.utc).date().isoformat()
    with pytest.raises(EventError, match="one log|span"):
        append_transaction(
            tmp_path,
            [ev(), ev(ts="2099-01-01T00:00:00+00:00")],
            lambda p, r, c: None,
        )
    assert list(tmp_path.glob("*.jsonl")) == [], (
        f"a refused transaction created a log in {tmp_path} (today is {today})"
    )

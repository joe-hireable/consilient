"""Whewell's second clause written into the record: a claim must say which class of
facts it came from, and who produced it. A `verification.outcome` carries a verification
identity, a protocol, an artefact digest, a verifier and its version, an
`evidence_class` and a status; the incomplete and ambiguous forms are enumerated field
by field and refused, a non-completion may carry no result, and a smuggled
`human_verdict` or `human_decision` is refused outright. The paired outcomes are
appended and replayed so that all four accept/reject cells and every non-completion
status survive the round trip intact — byte-identical artefacts may still be distinct
attempts. V0-26 is the same rule for multi-contributor events (ADR-0010, CONSILIENCE.md
clause 2): two agents declaring the same evidence class is echo, not consilience, and
case or whitespace variation must not disguise it, while single-actor events — the
overwhelming majority — stay unaffected and a duplicate class is quarantined at read
rather than crashing the reader. The review-queue contract and the verification source
scan sit here because they pin the same property from the other side: the eligible
universe is frozen before any candidate is drawn, and no component outcome may reach a
verdict without going through verification start."""

import json
import sys
import pytest
from consilient import events as events_mod
from consilient import projection
from consilient.events import (
    EventError,
    append,
    canonical,
    read,
    read_all,
    validate,
)
from v0_invariants_helpers import (
    HUMAN,
    _spend_scripts,
    ev,
    now_ts,
)


def verification_outcome(
    verification_id,
    attempt_id,
    artefact_sha256,
    verifier_id,
    verifier_accept,
    *,
    status="completed",
    verifier_version="v1",
):
    data = {
        "verification_id": verification_id,
        "attempt_id": attempt_id,
        "protocol_id": "EXP-81/v1",
        "artefact_sha256": artefact_sha256,
        "verifier_id": verifier_id,
        "verifier_version": verifier_version,
        "evidence_class": "execution",
        "status": status,
    }
    if verifier_accept is not None:
        data["verifier_accept"] = verifier_accept
    return ev(event="verification.outcome", data=data)


def test_verification_outcome_rejects_an_incomplete_or_ambiguous_record():
    valid = verification_outcome("v-1", "a-1", "0" * 64, "pytest", True)
    cases = []
    for field in (
        "verification_id",
        "attempt_id",
        "protocol_id",
        "artefact_sha256",
        "verifier_id",
        "verifier_version",
        "evidence_class",
        "status",
    ):
        candidate = {**valid, "data": dict(valid["data"])}
        candidate["data"].pop(field)
        cases.append((candidate, field))

    for field, value in (
        ("artefact_sha256", "A" * 64),
        ("artefact_sha256", "0" * 63),
        ("artefact_sha256", "g" * 64),
        ("verifier_version", " v1"),
        ("verifier_version", "v1\nbeta"),
        ("status", "passed"),
        ("verifier_accept", "yes"),
    ):
        candidate = {**valid, "data": {**valid["data"], field: value}}
        cases.append((candidate, field))

    completed_without_result = {**valid, "data": dict(valid["data"])}
    completed_without_result["data"].pop("verifier_accept")
    cases.append((completed_without_result, "verifier_accept"))
    for status in events_mod.VERIFICATION_STATUSES - {"completed"}:
        non_completion_with_result = {
            **valid,
            "data": {**valid["data"], "status": status},
        }
        cases.append((non_completion_with_result, "verifier_accept"))

    smuggled_verdict = {
        **valid,
        "data": {**valid["data"], "human_verdict": "accept"},
    }
    cases.append((smuggled_verdict, "human_verdict"))
    smuggled_decision = {
        **valid,
        "actor": HUMAN,
        "data": {
            **valid["data"],
            "human_decision": "verdict",
            "principal": HUMAN,
            "via": "cli",
        },
    }
    cases.append((smuggled_decision, "human_decision"))

    for candidate, field in cases:
        with pytest.raises(EventError, match=field):
            validate(candidate)


def test_paired_verification_outcomes_survive_append_and_replay(tmp_path):
    log_dir = tmp_path / "log"
    path = log_dir / "events.jsonl"
    expected_cells = ((False, False), (False, True), (True, False), (True, True))
    expected_payloads = []
    for index, (first, second) in enumerate(expected_cells, start=1):
        digest = "0" * 64  # byte-identical artefacts may still be distinct attempts
        attempt_id = f"attempt-{index}"
        expected_payloads.append(
            append(
                path,
                verification_outcome(
                    f"v-{index}-a", attempt_id, digest, "pytest", first
                ),
            )
        )
        expected_payloads.append(
            append(
                path,
                verification_outcome(
                    f"v-{index}-b", attempt_id, digest, "mypy", second
                ),
            )
        )

    non_completions = events_mod.VERIFICATION_STATUSES - {"completed"}
    for index, status in enumerate(sorted(non_completions), start=1):
        expected_payloads.append(
            append(
                path,
                verification_outcome(
                    f"v-terminal-{index}",
                    f"terminal-attempt-{index}",
                    "1" * 64,
                    f"planned-verifier-{index}",
                    None,
                    status=status,
                ),
            )
        )

    accepted, rejected = read_all(log_dir)
    conn = projection.build(log_dir, tmp_path / "state.db")
    payloads = [
        json.loads(row[0])
        for row in conn.execute(
            "SELECT payload FROM events WHERE kind='verification.outcome' ORDER BY position"
        )
    ]
    conn.close()
    assert [event.raw for event in accepted] == expected_payloads
    assert payloads == expected_payloads
    assert {
        payload["data"]["status"]
        for payload in payloads
        if payload["data"]["status"] != "completed"
    } == non_completions
    assert all(
        "verifier_accept" not in payload["data"]
        for payload in payloads
        if payload["data"]["status"] != "completed"
    )
    assert [payload["data"]["evidence_class"] for payload in payloads] == [
        "execution"
    ] * len(payloads)
    paired = {}
    for payload in payloads[: len(expected_cells) * 2]:
        data = payload["data"]
        attempt_id = data["attempt_id"]
        paired.setdefault(attempt_id, {})[data["verifier_id"]] = data["verifier_accept"]
    cells = {(pair["pytest"], pair["mypy"]): 1 for pair in paired.values()}

    assert cells == {cell: 1 for cell in expected_cells}
    assert rejected == []
    assert events_mod.bypassed(log_dir) == []


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


if _spend_scripts not in sys.path:
    sys.path.insert(0, _spend_scripts)


def test_verification_start_source_scan_blocks_component_outcome_bypass() -> None:
    from consilient import verification as verification_mod

    assert verification_mod.coverage_gate_passed()
    assert verification_mod.scan_component_outcome_producers() == []


def test_review_queue_opened_freezes_candidate_exposure_contract() -> None:
    queue = {
        "v": events_mod.SCHEMA_VERSION,
        "ts": now_ts(),
        "event": events_mod.REVIEW_QUEUE_OPENED_KIND,
        "actor": "consilient.verification",
        "data": {
            "queue_id": "queue-test",
            "stream_cap": 90,
            "exp105_prefix_n": 30,
            "rejection_target": 30,
            "population": "default-branch",
            "task_family": "repair",
            "protocol_id": "proto-1",
            "verifier_version": "v1",
            "verifier_contract_digest": "a" * 64,
            "start_position": 0,
            "eligible_universe_digest": "b" * 64,
            "selector": "first_matching_trajectory_order",
            "order_rule": "trajectory_position_ascending",
        },
    }
    with pytest.raises(EventError, match="eligible_universe_digest"):
        validate(queue)

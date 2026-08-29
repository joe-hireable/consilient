"""G01 -- structural credit refused on ledger grounds, and the replay oracle (ADR-0081).

Each ref here carries a well-formed acquisition anchor and still earns no credit, for
reasons that have nothing to do with difference of class: the decision was written
before the evidence it cites, the recorded event hash does not match the event, two
verification identities are one slot wearing two channels, or the verifier never reached
a terminal outcome. They are kept apart from the difference-of-class cases because they
fail through the projection's bookkeeping rather than through the anchor comparison, and
a mutation that breaks one is unlikely to touch the other. `_eid` and `_dump` come with
them: writing a log by hand, out of order and without the append path, is the only way
to stage a decision that precedes its own evidence. The last case is the one that gives
the ADR its name -- deleting the state database and rebuilding it from the log must
return an identical report, minority readings and non-qualifying refs included.

Mutation-tested here: treating duplicate verification identities as two slots fails the
duplicate-key test."""

import json
from pathlib import Path
from consilient import events, projection
from consilience_gate_helpers import (
    _browser_acquisition,
    _corpus_acquisition,
    _execution_acquisition,
    _project,
    _ref,
    _source_acquisition,
    decision_event,
    knowledge_event,
    verification_event,
)


def _eid(n: int) -> str:
    return f"00000000-0000-4000-8000-{n:012d}"


def _dump(log_dir: Path, records: list[dict[str, object]]) -> None:
    log_dir.mkdir()
    path = log_dir / "2026-08-24.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            if "event_id" not in record:
                record["event_id"] = events.new_event_id()
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def test_late_and_malformed_refs_do_not_qualify_as_anchors(tmp_path: Path) -> None:
    source = verification_event(
        acquisition=_execution_acquisition(),
        event_id=_eid(1),
        offset=1,
    )
    late_decision = decision_event(
        [_ref(source)],
        event_id=_eid(2),
        offset=0,
    )
    mismatched = decision_event(
        [
            {
                "event_id": str(source["event_id"]),
                "event_kind": events.VERIFICATION_OUTCOME_KIND,
                "event_sha256": "0" * 64,
            }
        ],
        decision_id="decision-2",
        event_id=_eid(3),
        offset=2,
    )
    log_dir = tmp_path / "log"
    _dump(log_dir, [late_decision, source, mismatched])
    conn = projection.build(log_dir, tmp_path / "state.db")
    late_report = projection.consilience_status(conn, "decision-1")
    assert late_report["status"] == "insufficient"
    assert late_report["qualifying_refs"] == []
    assert any("earlier" in reason for reason in late_report["reasons"])
    malformed_report = projection.consilience_status(conn, "decision-2")
    assert malformed_report["status"] == "insufficient"
    assert malformed_report["qualifying_refs"] == []
    assert any(
        "sha256" in reason or "hash" in reason for reason in malformed_report["reasons"]
    )


def test_duplicate_verification_keys_receive_no_structural_credit(
    tmp_path: Path,
) -> None:
    first = verification_event(
        acquisition=_execution_acquisition(observation_anchor="exec:one"),
        verification_id="ver-dup",
        attempt_id="att-dup",
        verifier_id="pytest",
        verifier_version="v1",
    )
    duplicate = verification_event(
        acquisition=_browser_acquisition(observation_anchor="browser:two"),
        verification_id="ver-dup",
        attempt_id="att-dup",
        verifier_id="pytest",
        verifier_version="v1",
        offset=1,
    )
    source = knowledge_event(acquisition=_source_acquisition(), offset=2)
    conn, written = _project(tmp_path, [first, duplicate, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(item) for item in written]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] in {"insufficient", "unmeasured"}
    assert report["qualifying_refs"] == []
    assert any("duplicate" in reason for reason in report["reasons"])


def test_timeout_and_refusal_remain_visible_without_anchor_credit(
    tmp_path: Path,
) -> None:
    timeout = verification_event(
        acquisition=_execution_acquisition(),
        status="timeout",
        verifier_accept=None,
        verification_id="ver-timeout",
    )
    refused = verification_event(
        acquisition=_browser_acquisition(),
        status="refused",
        verifier_accept=None,
        verification_id="ver-refused",
        attempt_id="att-2",
        offset=1,
    )
    conn, written = _project(tmp_path, [timeout, refused])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "insufficient"
    assert report["qualifying_refs"] == []
    joined = " ".join(report["reasons"])
    assert "timeout" in joined
    assert "refused" in joined
    assert len(report["non_qualifying_refs"]) == 2


def test_replay_after_deletion_preserves_status_and_minority_readings(
    tmp_path: Path,
) -> None:
    execution = verification_event(acquisition=_execution_acquisition())
    source = knowledge_event(acquisition=_source_acquisition(), offset=1)
    timeout = verification_event(
        acquisition=_browser_acquisition(),
        status="timeout",
        verifier_accept=None,
        verification_id="ver-timeout",
        attempt_id="att-timeout",
        offset=2,
    )
    unknown = knowledge_event(
        acquisition=_corpus_acquisition(derivation_roots="unknown"),
        uri="https://pypi.org/project/itsdangerous/2.2.0/",
        offset=3,
    )
    conn, written = _project(tmp_path, [execution, source, timeout, unknown])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(item) for item in written]),
    )
    conn.close()
    first = projection.build(tmp_path / "log", tmp_path / "state.db")
    report = projection.consilience_status(first, "decision-1")
    assert report["status"] == "converged"
    assert len(report["qualifying_refs"]) == 2
    visible = " ".join(report["reasons"])
    non_qualifying = json.dumps(report["non_qualifying_refs"])
    assert "timeout" in visible or "timeout" in non_qualifying
    assert "unknown" in visible or "unknown" in non_qualifying
    first.close()
    (tmp_path / "state.db").unlink()
    rebuilt = projection.build(tmp_path / "log", tmp_path / "state.db")
    replayed = projection.consilience_status(rebuilt, "decision-1")
    assert replayed == report

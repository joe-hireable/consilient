"""G01 — replay-only structural acquisition anchors (ADR-0081).

Mutation-tested in this file:
  - dropping channel/anchor/root validation makes the padded-channel and
    unknown-roots cases fail
  - treating duplicate verification identities as two slots fails the
    duplicate-key test
  - inferring independence from a missing acquisition object fails the
    unmeasured-status test
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from consilient import events, projection


CONTRACT = "b" * 64
ARTEFACT = "a" * 64
CONTENT = "c" * 64
RETAINED = "d" * 64
MANIFEST = "e" * 64
ASSEMBLED = "f" * 64


def _ts(offset: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset)).isoformat()


def _envelope(
    kind: str,
    data: dict[str, object],
    *,
    actor: str = "owner",
    offset: int = 0,
    event_id: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "v": events.SCHEMA_VERSION,
        "ts": _ts(offset),
        "event": kind,
        "actor": actor,
        "data": data,
    }
    if event_id is not None:
        record["event_id"] = event_id
    return record


def _eid(n: int) -> str:
    return f"00000000-0000-4000-8000-{n:012d}"


def _common_acquisition(
    channel: str,
    *,
    observation_anchor: str,
    derivation_roots: object,
    alternative: str = "ship",
    conclusion_id: str = "C1",
) -> dict[str, object]:
    return {
        "channel": channel,
        "observation_anchor": observation_anchor,
        "derivation_roots": derivation_roots,
        "conclusion_id": conclusion_id,
        "alternative": alternative,
        "acceptance_contract_digest": CONTRACT,
    }


def _execution_acquisition(
    *,
    observation_anchor: str = "exec:pytest",
    derivation_roots: object = ("fixture:tests/test_x.py",),
    alternative: str = "ship",
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload = _common_acquisition(
        "artefact_execution",
        observation_anchor=observation_anchor,
        derivation_roots=list(derivation_roots)
        if isinstance(derivation_roots, tuple)
        else derivation_roots,
        alternative=alternative,
    )
    payload["environment"] = "cpython-3.13"
    if extra:
        payload.update(extra)
    return payload


def _browser_acquisition(
    *,
    observation_anchor: str = "browser:chromium:login",
    derivation_roots: object = ("fixture:playwright/login.spec",),
    alternative: str = "ship",
) -> dict[str, object]:
    payload = _common_acquisition(
        "browser_observation",
        observation_anchor=observation_anchor,
        derivation_roots=list(derivation_roots)
        if isinstance(derivation_roots, tuple)
        else derivation_roots,
        alternative=alternative,
    )
    payload.update(
        {
            "browser": "chromium",
            "browser_version": "129.0",
            "retained_evidence": "screenshot",
            "retained_evidence_digest": RETAINED,
        }
    )
    return payload


def _source_acquisition(
    *,
    observation_anchor: str = "arxiv:2603.26993",
    derivation_roots: object = ("publisher:arxiv",),
    alternative: str = "ship",
    stance: str = "supports",
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload = _common_acquisition(
        "primary_source_retrieval",
        observation_anchor=observation_anchor,
        derivation_roots=list(derivation_roots)
        if isinstance(derivation_roots, tuple)
        else derivation_roots,
        alternative=alternative,
    )
    payload.update(
        {
            "proposition_id": "P1",
            "stance": stance,
            "locator": "§3",
            "verification_status": "FULL",
        }
    )
    if extra:
        payload.update(extra)
    return payload


def _corpus_acquisition(
    *,
    observation_anchor: str = "corpus:pallets/itsdangerous@2.2.0",
    derivation_roots: object = ("licence:bsd-3-clause",),
    alternative: str = "ship",
    stance: str = "supports",
) -> dict[str, object]:
    payload = _common_acquisition(
        "novel_corpus_observation",
        observation_anchor=observation_anchor,
        derivation_roots=list(derivation_roots)
        if isinstance(derivation_roots, tuple)
        else derivation_roots,
        alternative=alternative,
    )
    payload.update(
        {
            "proposition_id": "P1",
            "stance": stance,
            "locator": "itsdangerous/jws.py:1",
            "corpus_manifest_digest": MANIFEST,
            "provenance": "pypi-public",
            "selection_rule": "pinned-release-2.2.0",
            "assembled_context_digest": ASSEMBLED,
        }
    )
    return payload


def verification_event(
    *,
    acquisition: dict[str, object] | None = None,
    status: str = "completed",
    verifier_accept: bool | None = True,
    verification_id: str = "ver-1",
    attempt_id: str = "att-1",
    protocol_id: str = "EXP-109/v1",
    verifier_id: str = "pytest",
    verifier_version: str = "v1",
    offset: int = 0,
    event_id: str | None = None,
    extra_data: dict[str, object] | None = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "verification_id": verification_id,
        "attempt_id": attempt_id,
        "protocol_id": protocol_id,
        "artefact_sha256": ARTEFACT,
        "verifier_id": verifier_id,
        "verifier_version": verifier_version,
        "evidence_class": "execution",
        "status": status,
    }
    if verifier_accept is not None:
        data["verifier_accept"] = verifier_accept
    if acquisition is not None:
        data["acquisition"] = acquisition
    if extra_data:
        data.update(extra_data)
    return _envelope(
        events.VERIFICATION_OUTCOME_KIND,
        data,
        offset=offset,
        event_id=event_id,
    )


def knowledge_event(
    *,
    acquisition: dict[str, object] | None = None,
    status: str = "ok",
    uri: str = "https://arxiv.org/abs/2603.26993",
    offset: int = 0,
    event_id: str | None = None,
    extra_data: dict[str, object] | None = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "source_id": "scholar",
        "source_url": "https://example.com/licence",
        "licence": "MIT",
        "category": "literature",
        "retrieved_at": _ts(offset),
        "status": status,
        "uri": uri if status == "ok" else "",
    }
    if status == "ok":
        data["content_digest"] = CONTENT
    else:
        data["reason"] = "timeout"
    if acquisition is not None:
        data["acquisition"] = acquisition
    if extra_data:
        data.update(extra_data)
    return _envelope(
        events.KNOWLEDGE_RETRIEVED_KIND,
        data,
        actor=events.KNOWLEDGE_ACTOR,
        offset=offset,
        event_id=event_id,
    )


def _planning(evidence_refs: list[dict[str, str]], decision_id: str = "decision-1") -> dict[str, object]:
    return {
        "decision_id": decision_id,
        "operation_id": f"operation-{decision_id}",
        "ticket": "WORK-1",
        "owner": "owner",
        "actor": "owner",
        "record_level": "minimal",
        "decision": "Use the accepted standard-library path",
        "reasoning": "It is the smallest path satisfying the frozen contract",
        "falsifier": "A required effect cannot be represented",
        "reversal": {"kind": "inverse", "value": "consilient.events.validate"},
        "alternatives": [
            {
                "option": "Add a dependency",
                "rejected_because": "No dependency is needed",
            }
        ],
        "evidence_refs": evidence_refs,
        "acceptance_contract_digest": CONTRACT,
        "protocol": {
            "status": "not_warranted",
            "threshold": {
                "version": "better-than-best.v1",
                "later_reliance": "false",
                "question_open": "true",
                "wrong_costs_more": "true",
            },
        },
        "binding": {"kind": "material_choice"},
    }


def decision_event(
    evidence_refs: list[dict[str, str]],
    *,
    decision_id: str = "decision-1",
    offset: int = 10,
    event_id: str | None = None,
) -> dict[str, object]:
    return _envelope(
        events.DECISION_KIND,
        _planning(evidence_refs, decision_id=decision_id),
        offset=offset,
        event_id=event_id,
    )


def _ref(record: dict[str, object]) -> dict[str, str]:
    return {
        "event_id": str(record["event_id"]),
        "event_kind": str(record["event"]),
        "event_sha256": events.event_sha256(record),
    }


def _append_all(path: Path, records: list[dict[str, object]]) -> list[dict[str, object]]:
    written: list[dict[str, object]] = []
    for record in records:
        written.append(events.append(path, record))
    return written


def _project(
    tmp_path: Path, records: list[dict[str, object]]
) -> tuple[Any, list[dict[str, object]]]:
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    written = _append_all(log_dir / "2026-08-24.jsonl", records)
    conn = projection.build(log_dir, tmp_path / "state.db")
    return conn, written


def _dump(log_dir: Path, records: list[dict[str, object]]) -> None:
    log_dir.mkdir()
    path = log_dir / "2026-08-24.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            if "event_id" not in record:
                record["event_id"] = events.new_event_id()
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


@pytest.mark.parametrize(
    "record",
    (
        verification_event(acquisition=_execution_acquisition()),
        verification_event(acquisition=_browser_acquisition()),
        knowledge_event(acquisition=_source_acquisition()),
        knowledge_event(acquisition=_corpus_acquisition()),
    ),
)
def test_each_channel_anchor_validates(record: dict[str, object]) -> None:
    events.validate(record)


def test_padded_or_cased_channel_cannot_mint_an_anchor() -> None:
    for channel in ("Artefact_execution", " artefact_execution", "artefact_execution "):
        payload = _execution_acquisition()
        payload["channel"] = channel
        with pytest.raises(events.EventError, match="channel"):
            events.validate(verification_event(acquisition=payload))


def test_empty_derivation_roots_cannot_mint_an_anchor() -> None:
    payload = _execution_acquisition(derivation_roots=[])
    with pytest.raises(events.EventError, match="derivation"):
        events.validate(verification_event(acquisition=payload))


def test_legacy_source_without_anchor_metadata_is_unmeasured_status(
    tmp_path: Path,
) -> None:
    source = verification_event()
    conn, written = _project(tmp_path, [source])
    decision = decision_event([_ref(written[0])])
    events.append(tmp_path / "log" / "2026-08-24.jsonl", decision)
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "unmeasured"
    assert report["qualifying_refs"] == []
    assert report["non_qualifying_refs"]
    assert any("unmeasured" in reason for reason in report["reasons"])


def test_different_channel_anchors_report_converged_status(tmp_path: Path) -> None:
    execution = verification_event(acquisition=_execution_acquisition())
    source = knowledge_event(acquisition=_source_acquisition(), offset=1)
    conn, written = _project(tmp_path, [execution, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "converged"
    assert len(report["qualifying_refs"]) == 2
    assert {item["event_kind"] for item in report["qualifying_refs"]} == {
        events.VERIFICATION_OUTCOME_KIND,
        events.KNOWLEDGE_RETRIEVED_KIND,
    }


def test_same_channel_different_anchors_cannot_converge(tmp_path: Path) -> None:
    first = verification_event(
        acquisition=_execution_acquisition(observation_anchor="exec:one"),
        verification_id="ver-one",
    )
    second = verification_event(
        acquisition=_execution_acquisition(
            observation_anchor="exec:two",
            derivation_roots=("fixture:other.py",),
        ),
        verification_id="ver-two",
        attempt_id="att-2",
        offset=1,
    )
    conn, written = _project(tmp_path, [first, second])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "insufficient"
    assert report["qualifying_refs"] == []
    assert any("channel" in reason for reason in report["reasons"])


def test_same_observation_anchor_cannot_converge(tmp_path: Path) -> None:
    execution = verification_event(
        acquisition=_execution_acquisition(observation_anchor="shared-anchor")
    )
    source = knowledge_event(
        acquisition=_source_acquisition(observation_anchor="shared-anchor"),
        offset=1,
    )
    conn, written = _project(tmp_path, [execution, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "insufficient"
    assert report["qualifying_refs"] == []
    assert any("observation_anchor" in reason for reason in report["reasons"])


def test_shared_derivation_roots_are_echo_not_an_anchor_pair(tmp_path: Path) -> None:
    execution = verification_event(
        acquisition=_execution_acquisition(derivation_roots=("root:shared", "root:tests"))
    )
    source = knowledge_event(
        acquisition=_source_acquisition(derivation_roots=("root:shared", "root:arxiv")),
        offset=1,
    )
    conn, written = _project(tmp_path, [execution, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "insufficient"
    assert any("derivation" in reason for reason in report["reasons"])


def test_unknown_derivation_roots_report_unmeasured_status(tmp_path: Path) -> None:
    execution = verification_event(
        acquisition=_execution_acquisition(derivation_roots="unknown")
    )
    source = knowledge_event(acquisition=_source_acquisition(), offset=1)
    conn, written = _project(tmp_path, [execution, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "unmeasured"
    assert report["qualifying_refs"] == []
    assert any("unknown" in reason for reason in report["reasons"])


def test_opposing_stances_report_disagreed_status(tmp_path: Path) -> None:
    execution = verification_event(
        acquisition=_execution_acquisition(),
        verifier_accept=True,
    )
    source = knowledge_event(
        acquisition=_source_acquisition(stance="opposes"),
        offset=1,
    )
    conn, written = _project(tmp_path, [execution, source])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "disagreed"
    assert len(report["qualifying_refs"]) == 2


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
    assert any("sha256" in reason or "hash" in reason for reason in malformed_report["reasons"])


def test_duplicate_verification_keys_receive_no_structural_credit(tmp_path: Path) -> None:
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


def test_timeout_and_refusal_remain_visible_without_anchor_credit(tmp_path: Path) -> None:
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


def test_different_model_same_source_anchor_is_echo(tmp_path: Path) -> None:
    first = knowledge_event(
        acquisition=_source_acquisition(observation_anchor="arxiv:2603.26993"),
        extra_data={"model_family": "claude"},
    )
    second = knowledge_event(
        acquisition=_corpus_acquisition(observation_anchor="arxiv:2603.26993"),
        uri="https://example.com/corpus",
        offset=1,
        extra_data={"model_family": "gpt"},
    )
    conn, written = _project(tmp_path, [first, second])
    events.append(
        tmp_path / "log" / "2026-08-24.jsonl",
        decision_event([_ref(written[0]), _ref(written[1])]),
    )
    conn.close()
    conn = projection.build(tmp_path / "log", tmp_path / "state-2.db")
    report = projection.consilience_status(conn, "decision-1")
    assert report["status"] == "insufficient"
    assert report["qualifying_refs"] == []
    assert any("observation_anchor" in reason for reason in report["reasons"])


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

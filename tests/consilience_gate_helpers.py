"""Builders for the G01 acquisition-anchor fixtures (ADR-0081).

Every test of the consilience gate has to mint an acquisition object on one of the four
channels -- artefact execution, browser observation, primary-source retrieval and novel-
corpus observation -- hang it on a verification or knowledge envelope, append the result
to a day log and rebuild the projection over it. Those builders sit here rather than in
either test module because both halves need all four channels: the difference-of-class
tests to pair unlike anchors, the ledger tests to duplicate, time out and replay
otherwise sound ones. The digest constants are fixed strings rather than computed
values, so the acquisition metadata is the only thing that varies between cases."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
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


def _planning(
    evidence_refs: list[dict[str, str]], decision_id: str = "decision-1"
) -> dict[str, object]:
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


def _append_all(
    path: Path, records: list[dict[str, object]]
) -> list[dict[str, object]]:
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

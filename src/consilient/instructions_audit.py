"""Recording an assembly, re-deriving it layer by layer, and when the protocol is
warranted.

record_assembly appends through the single writer, naming every layer, and it refuses to
write one thing: the omission list. The raise inspects the receipt itself — a copy that
already dropped the key cannot fail, and a chokepoint that cannot fail is not one — and
then inspects the event that would be appended, so spreading omitted onto data.recall
at the append call site cannot land. The compounding receipt that grew the log from
21 KB to 40 MB in six days entered exactly there.

  V0-47  Assemblies are recorded through append() with the identity of every layer,
         and record_assembly is the package's only writer of instructions.assembled.

`reconstruct` is the other half. An instruction set that cannot be reconstructed after
the fact is not auditable, and an unauditable instruction set cannot be proven to have
helped. Drift is reported per layer and never smoothed into a single yes: a core
rendered at a different version says so and names git at the assembly's commit as the
recovery route, a skill whose bytes moved is named, and a replay whose selection receipt
disagrees fails rather than being reconciled.

The decision-protocol proxies sit beside them because they interrogate the same record:
whether a verified answer to this question, at this scope and this version, already
exists, and whether rework costs more than the protocol under a policy version and unit
both ceilings share. Where an input is absent or the versions differ the answer is
unknown, and unknown never becomes a skip."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from . import promote, recall
from .events import (
    SCHEMA_VERSION,
    EventPayload,
    append,
    read_all,
)
from .instructions_vocabulary import (
    ACTOR,
    ASSEMBLED,
    BETTER_THAN_BEST_FILE,
    CORE_VERSION,
    INVARIANT_CORE,
    InstructionError,
    LayerReport,
    _RECEIPT_FIELDS,
    _omission_rows,
    _source_digest,
)

from .instructions_admission import (
    Assembly,
    CostCeiling,
    IndexLookup,
    ProtocolThreshold,
    Reconstruction,
    _later_reliance,
    _omitted_digest,
    _render_core,
    record_adapted,
)

from .instructions_composition import (
    _adapted_from_events,
    _recorded_selection_receipt,
    _select_recall,
    render,
)


__all__ = [
    "ACTOR",
    "ASSEMBLED",
    "Assembly",
    "BETTER_THAN_BEST_FILE",
    "CORE_VERSION",
    "CostCeiling",
    "INVARIANT_CORE",
    "IndexLookup",
    "InstructionError",
    "LayerReport",
    "ProtocolBinding",
    "ProtocolThreshold",
    "Reconstruction",
    "_RECEIPT_FIELDS",
    "_adapted_from_events",
    "_later_reliance",
    "_omission_rows",
    "_omitted_digest",
    "_recorded_selection_receipt",
    "_render_core",
    "_select_recall",
    "_source_digest",
    "protocol_threshold",
    "reconstruct",
    "record_adapted",
    "record_assembly",
    "render",
]


@dataclass(frozen=True)
class ProtocolBinding:
    """Decision-protocol references derived from a threshold and the pinned tree."""

    status: str
    threshold: ProtocolThreshold
    instructions_ref: dict[str, str] | None
    bar_ref: dict[str, str] | None
    search_ref: dict[str, str] | None
    killing_check_ref: dict[str, str] | None


def _question_open(index: IndexLookup | None) -> str:
    if index is None:
        return "unknown"
    matched = any(
        answer.verified
        and answer.question_digest == index.question_digest
        and answer.scope_digest == index.scope_digest
        and answer.version_digest == index.version_digest
        for answer in index.answers
    )
    if matched:
        return "false"
    if not index.complete:
        return "unknown"
    return "true"


def _wrong_costs_more(rework: CostCeiling | None, protocol: CostCeiling | None) -> str:
    if rework is None or protocol is None:
        return "unknown"
    if not rework.policy_version or not protocol.policy_version:
        return "unknown"
    if rework.policy_version != protocol.policy_version:
        return "unknown"
    if rework.unit != protocol.unit:
        return "unknown"
    return "true" if rework.minutes > protocol.minutes else "false"


def protocol_threshold(
    *,
    consumers: Sequence[str] | None = None,
    index: IndexLookup | None = None,
    rework_ceiling: CostCeiling | None = None,
    protocol_cost_ceiling: CostCeiling | None = None,
) -> ProtocolThreshold:
    """Return the three conservative proxies. Unknown never becomes a skip."""

    return ProtocolThreshold(
        later_reliance=_later_reliance(consumers),
        question_open=_question_open(index),
        wrong_costs_more=_wrong_costs_more(rework_ceiling, protocol_cost_ceiling),
    )


def _selection_receipt(selection: recall.Selection) -> dict[str, object]:
    rows = _omission_rows(selection)
    return {
        "selected_event_ids": list(selection.selected_event_ids),
        "selected_digest": selection.selected_digest,
        "omitted_count": len(rows),
        "omitted_digest": _omitted_digest(rows),
        "context_complete": selection.context_complete,
        "continuation": (
            {"event_id": selection.continuation_event_id}
            if selection.continuation_event_id is not None
            else None
        ),
    }


def _reject_inlined_omission(event: Mapping[str, object]) -> None:
    """Refuse an assembled event whose recall layer inlines the omission list.

    Checking the payload after copying only `_RECEIPT_FIELDS` cannot fire:
    omitted is not in those names. Spreading the list at the append call site
    never touched that dict. The event that would be written is the artefact.
    """
    data = event.get("data")
    if not isinstance(data, dict):
        return
    recall = data.get("recall")
    if isinstance(recall, dict) and "omitted" in recall:
        raise InstructionError(
            "instructions.assembled must not inline the omission list"
        )


def record_assembly(
    log_dir: Path,
    assembly: Assembly,
    *,
    task: str,
    pre_run_records: Mapping[str, object] | None = None,
) -> EventPayload:
    """Append the assembly through the single writer, naming every layer (V0-47)."""
    now = datetime.now(timezone.utc)
    receipt = _selection_receipt(assembly.recall_selection)
    # Inspect the receipt, not the payload after a copy that already drops the
    # key. Checking recall_payload after looping `_RECEIPT_FIELDS` cannot fire.
    if "omitted" in receipt:
        raise InstructionError(
            "instructions.assembled must not inline the omission list"
        )
    recall_payload: dict[str, object] = {
        "query": task,
        "limit_chars": assembly.recall_limit_chars,
        "sha256": promote.digest(assembly.recall_pack),
        "source_events": assembly.recall_source_events,
        "source_digest": assembly.recall_source_digest,
    }
    for field in _RECEIPT_FIELDS:
        recall_payload[field] = receipt[field]
    event: EventPayload = {
        "v": SCHEMA_VERSION,
        "ts": now.isoformat(),
        "event": ASSEMBLED,
        "actor": ACTOR,
        "data": {
            "assembly_id": assembly.sha256,
            "core": {
                "version": assembly.core_version,
                "sha256": promote.digest(_render_core(assembly.core_version)),
            },
            "skills": [
                {
                    "name": skill.name,
                    "path": skill.path,
                    "sha256": skill.sha256,
                    "matched": list(skill.matched),
                }
                for skill in assembly.skills
            ],
            "skills_omitted": assembly.skills_omitted,
            "recall": recall_payload,
            "adapted": {
                "status": assembly.adapted.status,
                "sha256": assembly.adapted.sha256,
                "candidate_id": assembly.adapted.candidate_id,
            },
            "recall_receipt": dict(assembly.recall_receipt),
            "capability_manifests": [
                dict(row) for row in assembly.capability_manifests
            ],
            "pre_run_records": dict(pre_run_records or {}),
        },
    }
    _reject_inlined_omission(event)
    return append(log_dir / f"{now.date().isoformat()}.jsonl", event)


def reconstruct(log_dir: Path, skills_dir: Path, assembly_id: str) -> Reconstruction:
    """Re-derive a recorded assembly, layer by layer, and say exactly what drifted.

    An instruction set that cannot be reconstructed after the fact is not auditable,
    and an unauditable instruction set cannot be proven to have helped. The core and
    skills are recovered from the tree and checked by digest; the recall pack is
    replayed over the pinned append-only prefix; the adapted layer is replayed from
    the events that preceded the assembly."""
    events, _ = read_all(log_dir)
    index: int | None = None
    for position, event in enumerate(events):
        if event.kind == ASSEMBLED and event.data.get("assembly_id") == assembly_id:
            index = position
    if index is None:
        return Reconstruction(
            assembly_id,
            False,
            (
                LayerReport(
                    "event", False, "no instructions.assembled event carries this id"
                ),
            ),
        )
    data = events[index].data
    reports: list[LayerReport] = []

    core = data.get("core")
    expected_version = core.get("version") if isinstance(core, dict) else None
    expected_core_sha = core.get("sha256") if isinstance(core, dict) else None
    if expected_version != CORE_VERSION:
        reports.append(
            LayerReport(
                "core",
                False,
                f"the event records core v{expected_version}; this build renders "
                f"v{CORE_VERSION}. The core changed by commit since; recover the "
                "assembled text from git at the assembly's commit.",
            )
        )
    elif promote.digest(_render_core(CORE_VERSION)) != expected_core_sha:
        reports.append(
            LayerReport(
                "core", False, "the rendered core digest does not match the record"
            )
        )
    else:
        reports.append(LayerReport("core", True, f"v{CORE_VERSION} digest matches"))

    recorded_skills = data.get("skills")
    skill_reports_ok = True
    skill_details: list[str] = []
    if isinstance(recorded_skills, list):
        for entry in recorded_skills:
            if not isinstance(entry, dict):
                skill_reports_ok = False
                continue
            name = entry.get("name")
            recorded_sha = entry.get("sha256")
            recorded_path = entry.get("path")
            path = skills_dir / str(name) / BETTER_THAN_BEST_FILE
            if isinstance(recorded_path, str):
                normalised = recorded_path.replace("\\", "/")
                suffix = f"{name}/{BETTER_THAN_BEST_FILE}"
                if not normalised.endswith(suffix):
                    skill_reports_ok = False
                    skill_details.append(f"{name}: path drifted")
                    continue
            if not path.exists():
                skill_reports_ok = False
                skill_details.append(f"{name}: file gone")
                continue
            actual_sha = promote.digest(path.read_text(encoding="utf-8"))
            if actual_sha != recorded_sha:
                skill_reports_ok = False
                skill_details.append(f"{name}: content drifted")
            else:
                skill_details.append(f"{name}: ok")
    reports.append(
        LayerReport(
            "skills",
            skill_reports_ok,
            "; ".join(skill_details) if skill_details else "no skills were selected",
        )
    )

    recall_data = data.get("recall")
    if not isinstance(recall_data, dict):
        reports.append(
            LayerReport("recall", False, "the record carries no recall layer")
        )
    else:
        source_events = recall_data.get("source_events")
        source_digest = recall_data.get("source_digest")
        query = recall_data.get("query")
        limit_chars = recall_data.get("limit_chars")
        recorded_pack_sha = recall_data.get("sha256")
        if not (
            isinstance(source_events, int)
            and isinstance(source_digest, str)
            and isinstance(query, str)
            and isinstance(limit_chars, int)
            and isinstance(recorded_pack_sha, str)
        ):
            reports.append(
                LayerReport("recall", False, "the recall record is malformed")
            )
        elif len(events) < source_events:
            reports.append(
                LayerReport(
                    "recall",
                    False,
                    f"the log holds {len(events)} events, fewer than the "
                    f"{source_events} the pack consumed; the append-only prefix is gone",
                )
            )
        elif _source_digest(events[:source_events]) != source_digest:
            reports.append(
                LayerReport(
                    "recall",
                    False,
                    "the pinned log prefix no longer digests to the record",
                )
            )
        else:
            selection = _select_recall(
                events[:source_events], query=query, limit_chars=limit_chars
            )
            pack = selection.text
            if promote.digest(pack) != recorded_pack_sha:
                reports.append(
                    LayerReport(
                        "recall", False, "the replayed pack does not match the record"
                    )
                )
            elif "omitted_digest" in recall_data and "omitted" in recall_data:
                reports.append(
                    LayerReport(
                        "recall",
                        False,
                        "the recorded receipt inlines omitted next to omitted_digest",
                    )
                )
            elif _selection_receipt(selection) != _recorded_selection_receipt(
                recall_data
            ):
                reports.append(
                    LayerReport(
                        "recall",
                        False,
                        "the replayed selection receipt does not match the record",
                    )
                )
            else:
                reports.append(
                    LayerReport(
                        "recall",
                        True,
                        f"replayed over the pinned prefix of {source_events} event(s)",
                    )
                )

    recorded_adapted = data.get("adapted")
    if not isinstance(recorded_adapted, dict):
        reports.append(
            LayerReport("adapted", False, "the record carries no adapted layer")
        )
    else:
        replayed = _adapted_from_events(events[:index])
        if (
            replayed.status == recorded_adapted.get("status")
            and replayed.sha256 == recorded_adapted.get("sha256")
            and replayed.candidate_id == recorded_adapted.get("candidate_id")
        ):
            reports.append(
                LayerReport("adapted", True, f"{replayed.status} as recorded")
            )
        else:
            reports.append(
                LayerReport(
                    "adapted",
                    False,
                    f"recorded {recorded_adapted.get('status')}/"
                    f"{recorded_adapted.get('sha256')}, replay gives "
                    f"{replayed.status}/{replayed.sha256}",
                )
            )

    return Reconstruction(assembly_id, True, tuple(reports))

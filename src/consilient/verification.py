"""Shared verification-start boundary and frozen review-queue contracts (Q01).

`begin_attempt()` is the sole front door that may emit `candidate.exposed` before any
component `verification.outcome`. It executes no verifier itself.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

from . import events as events_mod
from .events import (
    CANDIDATE_EXPOSED_KIND,
    REVIEW_QUEUE_OPENED_KIND,
    EventError,
    EventPayload,
    append,
    read_all,
)

STREAM_CAP = 90
EXP105_PREFIX_N = 30
SELECTOR = "first_matching_trajectory_order"
ORDER_RULE = "trajectory_position_ascending"

ATTEMPT_REVIEWED_KIND = "attempt.reviewed"
REVIEW_PRESENTATION_FROZEN_KIND = "review.presentation.frozen"

QUEUE_OPENED_FIELDS = frozenset(
    {
        "queue_id",
        "stream_cap",
        "exp105_prefix_n",
        "rejection_target",
        "population",
        "task_family",
        "protocol_id",
        "verifier_version",
        "verifier_contract_digest",
        "start_position",
        "eligible_universe_digest",
        "selector",
        "order_rule",
    }
)
CANDIDATE_EXPOSED_FIELDS = frozenset(
    {
        "queue_id",
        "exposure_id",
        "attempt_id",
        "exposure_ordinal",
        "start_token",
        "artefact_sha256",
        "task_family",
        "protocol_id",
        "verifier_version",
        "verifier_contract_digest",
    }
)
ATTEMPT_REVIEWED_FIELDS = frozenset(
    {
        "queue_id",
        "exposure_id",
        "attempt_id",
        "disposition",
    }
)
REVIEW_PRESENTATION_FROZEN_FIELDS = frozenset(
    {
        "queue_id",
        "exposure_id",
        "attempt_id",
        "contract_digest",
        "artefact_digest",
        "component_rollup_digest",
        "presentation_digest",
    }
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_VERIFICATION_ACTOR = "consilient.verification"

# Paths allowed to reference verification.outcome without going through begin_attempt().
# Tests append outcomes directly; production writers must use the start boundary.
_OUTCOME_REFERENCE_ALLOWLIST = frozenset(
    {
        "events.py",
        "verification.py",
        "projection.py",
    }
)


@dataclass(frozen=True)
class AttemptStart:
    start_token: str
    exposure_id: str
    exposure_ordinal: int


def _now_ts(offset_s: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).isoformat()


def eligible_universe_digest(
    *,
    task_family: str,
    population: str,
    protocol_id: str,
    verifier_version: str,
    verifier_contract_digest: str,
    order_rule: str,
) -> str:
    payload = json.dumps(
        {
            "task_family": task_family,
            "population": population,
            "protocol_id": protocol_id,
            "verifier_version": verifier_version,
            "verifier_contract_digest": verifier_contract_digest,
            "order_rule": order_rule,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _start_token(
    *,
    queue_id: str,
    attempt_id: str,
    exposure_ordinal: int,
    artefact_sha256: str,
) -> str:
    material = f"{queue_id}:{attempt_id}:{exposure_ordinal}:{artefact_sha256}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _unique_id(prefix: str) -> str:
    material = f"{prefix}:{_now_ts()}:{os.urandom(16).hex()}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def open_queue(
    log_path: Path,
    *,
    queue_id: str | None = None,
    task_family: str,
    population: str,
    protocol_id: str,
    verifier_version: str,
    verifier_contract_digest: str,
    rejection_target: int = 30,
    start_position: int = 0,
    actor: str = _VERIFICATION_ACTOR,
) -> EventPayload:
    """Append `review.queue.opened` with the frozen Q01 manifest."""
    if queue_id is None:
        queue_id = _unique_id("queue")
    if not _HEX64.fullmatch(verifier_contract_digest):
        raise EventError("verifier_contract_digest must be 64 lowercase hex characters")
    digest = eligible_universe_digest(
        task_family=task_family,
        population=population,
        protocol_id=protocol_id,
        verifier_version=verifier_version,
        verifier_contract_digest=verifier_contract_digest,
        order_rule=ORDER_RULE,
    )
    event: EventPayload = {
        "v": events_mod.SCHEMA_VERSION,
        "ts": _now_ts(),
        "event": REVIEW_QUEUE_OPENED_KIND,
        "actor": actor,
        "data": {
            "queue_id": queue_id,
            "stream_cap": STREAM_CAP,
            "exp105_prefix_n": EXP105_PREFIX_N,
            "rejection_target": rejection_target,
            "population": population,
            "task_family": task_family,
            "protocol_id": protocol_id,
            "verifier_version": verifier_version,
            "verifier_contract_digest": verifier_contract_digest,
            "start_position": start_position,
            "eligible_universe_digest": digest,
            "selector": SELECTOR,
            "order_rule": ORDER_RULE,
        },
    }
    return append(log_path, event)


def begin_attempt(
    log_path: Path,
    *,
    queue_id: str,
    attempt_id: str,
    artefact_sha256: str,
    actor: str = _VERIFICATION_ACTOR,
) -> AttemptStart:
    """Atomically append `candidate.exposed` and return the verification start token."""
    if not _HEX64.fullmatch(artefact_sha256):
        raise EventError("artefact_sha256 must be 64 lowercase hex characters")
    log_dir = log_path.parent
    events, _rejected = read_all(log_dir)
    queue_event: EventPayload | None = None
    exposure_count = 0
    for event in events:
        if event.kind == REVIEW_QUEUE_OPENED_KIND and event.data.get("queue_id") == queue_id:
            queue_event = event.raw
        if event.kind == CANDIDATE_EXPOSED_KIND and event.data.get("queue_id") == queue_id:
            exposure_count += 1
    if queue_event is None:
        raise EventError(
            f"review.queue.opened for queue_id {queue_id!r} must precede candidate exposure"
        )
    data = cast(dict[str, Any], queue_event["data"])
    exposure_ordinal = exposure_count + 1
    if exposure_ordinal > int(data["stream_cap"]):
        raise EventError(
            f"candidate exposure ordinal {exposure_ordinal} exceeds stream_cap "
            f"{data['stream_cap']}"
        )
    exposure_id = _unique_id("exposure")
    token = _start_token(
        queue_id=queue_id,
        attempt_id=attempt_id,
        exposure_ordinal=exposure_ordinal,
        artefact_sha256=artefact_sha256,
    )
    exposure: EventPayload = {
        "v": events_mod.SCHEMA_VERSION,
        "ts": _now_ts(),
        "event": CANDIDATE_EXPOSED_KIND,
        "actor": actor,
        "data": {
            "queue_id": queue_id,
            "exposure_id": exposure_id,
            "attempt_id": attempt_id,
            "exposure_ordinal": exposure_ordinal,
            "start_token": token,
            "artefact_sha256": artefact_sha256,
            "task_family": data["task_family"],
            "protocol_id": data["protocol_id"],
            "verifier_version": data["verifier_version"],
            "verifier_contract_digest": data["verifier_contract_digest"],
        },
    }
    append(log_path, exposure)
    return AttemptStart(
        start_token=token,
        exposure_id=exposure_id,
        exposure_ordinal=exposure_ordinal,
    )


def verification_outcome_event(
    *,
    verification_id: str,
    attempt_id: str,
    protocol_id: str,
    artefact_sha256: str,
    verifier_id: str,
    verifier_version: str,
    start_token: str,
    evidence_class: str = "measured",
    status: str = "completed",
    verifier_accept: bool | None = True,
    actor: str = _VERIFICATION_ACTOR,
) -> EventPayload:
    """Build a component outcome that carries the required exposure receipt."""
    data: dict[str, object] = {
        "verification_id": verification_id,
        "attempt_id": attempt_id,
        "protocol_id": protocol_id,
        "artefact_sha256": artefact_sha256,
        "verifier_id": verifier_id,
        "verifier_version": verifier_version,
        "evidence_class": evidence_class,
        "status": status,
        "start_token": start_token,
    }
    if verifier_accept is not None:
        data["verifier_accept"] = verifier_accept
    return {
        "v": events_mod.SCHEMA_VERSION,
        "ts": _now_ts(),
        "event": events_mod.VERIFICATION_OUTCOME_KIND,
        "actor": actor,
        "data": data,
    }


def append_component_outcome(log_path: Path, event: EventPayload) -> EventPayload:
    """Append one component outcome through the shared writer."""
    return append(log_path, event)


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def scan_component_outcome_producers() -> list[str]:
    """Return human-readable violations if any producer bypasses begin_attempt()."""
    root = _package_root()
    violations: list[str] = []
    for path in sorted(root.glob("*.py")):
        if path.name in _OUTCOME_REFERENCE_ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8")
        if events_mod.VERIFICATION_OUTCOME_KIND in text or '"verification.outcome"' in text:
            violations.append(f"{path.name} references verification.outcome outside the allowlist")
    scripts = root.parent.parent / "scripts"
    if scripts.is_dir():
        for path in sorted(scripts.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            if events_mod.VERIFICATION_OUTCOME_KIND not in text and '"verification.outcome"' not in text:
                continue
            tree = ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "append":
                    violations.append(
                        f"{path.name} appends verification outcomes without begin_attempt()"
                    )
                    break
    return violations


def coverage_gate_passed() -> bool:
    return not scan_component_outcome_producers()


def queue_manifest_matches(event: EventPayload) -> bool:
    data = event["data"]
    if set(data) != QUEUE_OPENED_FIELDS:
        return False
    recomputed = eligible_universe_digest(
        task_family=cast(str, data["task_family"]),
        population=cast(str, data["population"]),
        protocol_id=cast(str, data["protocol_id"]),
        verifier_version=cast(str, data["verifier_version"]),
        verifier_contract_digest=cast(str, data["verifier_contract_digest"]),
        order_rule=cast(str, data["order_rule"]),
    )
    return (
        int(data["stream_cap"]) == STREAM_CAP
        and int(data["exp105_prefix_n"]) == EXP105_PREFIX_N
        and data["selector"] == SELECTOR
        and data["eligible_universe_digest"] == recomputed
    )

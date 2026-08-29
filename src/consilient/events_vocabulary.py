"""The closed vocabularies an event may draw on.

Every set here names the exact values a field is allowed to take — the acquisition
channels, the consent purposes, the dispatch, manifest and refusal statuses, the
mutation classes of a model change, and the classes of decision reserved to a human or
to the user alone. Beside them sit the field sets that say not only what a record must
carry but what it may not: an escalation attempt, a captured record, a delivery estimate
and an answered feedback event each have a fixed body, and an unrecognised key is
refused rather than accepted and puzzled over later. A vocabulary that quietly grows
cannot be replayed against its own past, which is why none of these is open-ended.

With them are the few primitives that answer to nothing else at all — a fresh event
identity in its one canonical spelling, the single jitter rule every retry site sleeps
by, the cheap fingerprint of a whole trajectory directory, the removal of a failed
append's bytes, and the small readings of an outcome that later code asks for: how long
it ran, whether it completed, whether it was censored.

This file refuses to know anything about the shape of an event. It holds terms, not
rules; the rules that consult them live above."""

from __future__ import annotations
import hashlib
import json
import os
import time
from collections.abc import Mapping
from pathlib import Path
from typing import cast

PROTECTED_DECISION_CLASSES = frozenset(
    {
        "money",
        "credential",
        "external_exposure",
        "unrecoverable_state_loss",
        "principal_authority",
        "preference",
    }
)

_AUTONOMOUS_ADMISSION_CLASSES = frozenset(
    {
        "contained_execution",
        "proof_operation",
        "material_choice",
        "recoverable_mutation",
    }
)

_DECISION_PROTOCOL_MARKERS = frozenset(
    {
        "decision_id",
        "operation_id",
        "ticket",
        "owner",
        "record_level",
        "alternatives",
        "only_admissible",
        "evidence_refs",
        "acceptance_contract_digest",
        "protocol",
        "binding",
        "supersedes",
    }
)

# ADR-0033 section 2: these are the exhaustive classes only the user may decide.
USER_ONLY = frozenset(
    {
        "spend",  # Money leaving an account, or metered spend beyond an authorised cap | Not the harness's money
        "credential",  # A credential, permission or authentication only the user holds | The harness cannot obtain it
        "preference",  # A preferential question no fact settles | No experiment substitutes for a value judgement
        "outside_safety_floor",  # An action outside the safety floor | Reserved by construction
        "beta_verdict",  # The β verdict on an artefact | Human judgement is the ground truth being measured
        "external_exposure",  # Publishing, transmitting or exposing anything beyond the machine | Irreversible and outward-facing
        "gate_or_spec_approval",  # Lifting a gate, or approving a specification | Reserved to the principal
    }
)

DISPATCH_STATUSES = frozenset(
    {"ok", "silent", "failed", "timeout", "refused", "killed", "error"}
)

ACQUISITION_CHANNELS = frozenset(
    {
        "artefact_execution",
        "browser_observation",
        "primary_source_retrieval",
        "novel_corpus_observation",
    }
)

BROWSER_RETAINED_EVIDENCE = frozenset(
    {
        "screenshot",
        "accessibility_tree",
        "dom_runtime",
        "console_network",
        "interaction_receipt",
    }
)

RECORD_CAPTURED_FIELDS = frozenset(
    {
        "record_id",
        "digest",
        "byte_count",
        "media_type",
        "object_locator",
        "source",
        "consent_purpose",
        "retention_class",
        "valid_time",
        "supersedes",
        "invalidates",
    }
)

CAPABILITY_VERSIONED_FIELDS = frozenset(
    {
        "authored_run",
        "content_digest",
        "destination_class",
        "duplicate_of",
        "evidence_class",
        "execution_contract_key",
        "expires_at",
        "identity",
        "interface",
        "licence",
        "permission_boundary",
        "privacy_class",
        "purpose",
        "recheck_at",
        "source_object",
        "status",
        "supersedes",
        "trust_boundary",
        "verifier_semantics",
        "version_digest",
    }
)

CAPABILITY_KIND_ALIASES = frozenset(
    {"capability.version", "capability_versioned", "capabilities.versioned"}
)

MODEL_CHANGE_FIELDS = frozenset(
    {
        "authoring_run",
        "base_model",
        "base_model_digest",
        "change_id",
        "checkpoint",
        "checkpoint_digest",
        "dataset",
        "dataset_digest",
        "failure",
        "licence",
        "mutation_class",
        "privacy_class",
        "procedure",
        "procedure_digest",
        "status",
    }
)

MODEL_CHANGE_KIND_ALIASES = frozenset(
    {"model.changed", "model_change", "models.change"}
)

MODEL_CHANGE_MUTATION_CLASSES = frozenset(
    {"data_driven_training", "non_data_driven_state_change"}
)

CAPABILITY_MANIFEST_STATUSES = frozenset(
    {"active", "inactive", "expired", "superseded", "duplicate", "unmeasured"}
)

ESCALATION_ATTEMPT_FIELDS = frozenset(
    {
        "root_cause",
        "escalation_class",
        "what_stopped",
        "what_it_is_holding",
        "what_i_need",
        "default_if_no_reply",
        "evidence",
        "disposition",
        "refusal_reason",
        "decision_changed",
    }
)

ESCALATION_REFUSAL_REASONS = frozenset(
    {"duplicate_root_cause", "budget_exhausted", "out_of_set_class"}
)

# Decisions that only a human principal may author (V0-18). Recording one under an agent
# actor is the failure EXP-16 measured: a fabricated human-participation claim.
HUMAN_ONLY = frozenset(
    {
        "approval",
        "consent",
        "feedback",
        "gate_lift",
        "spend_authorisation",
        "verdict",
    }
)

CONSENT_PURPOSES = frozenset(
    {"improve-consilient", "train-consilient", "commercial-training"}
)

# feedback-signals.md rules 1–2: no approval-style signal is ever a training target,
# and none is collected at all — response rating is not built. The prohibition lives
# here in the schema, not in prose: validate() rejects these field names on any event.
RESPONSE_RATING_FIELDS = frozenset(
    {
        "rating",
        "response_rating",
        "thumbs",
        "thumbs_up",
        "thumbs_down",
        "satisfaction",
        "helpful",
        "unhelpful",
        "stars",
        "star_rating",
    }
)

# feedback-signals.md: achievement (asked) and efficiency (derived) are separate
# records, permanently. No default composite score exists anywhere, so the answered
# event refuses the fields that would build one — efficiency stays on
# dispatch.outcome, where it is measured, and any composite is an explicit user
# weighting, which is a preferential question the harness must not default.
FEEDBACK_COMPOSITE_FIELDS = frozenset(
    {"score", "composite", "overall", "efficiency", "cost", "duration_s"}
)

ESTIMATE_CAUSES = frozenset(
    {
        "scope_change",
        "route_change",
        "checkpoint_miss",
        "dependency_failure",
        "estimate_error",
    }
)

_ESTIMATE_REQUIRED_FIELDS = frozenset(
    {
        "delivery_id",
        "commitment_id",
        "commitment_digest",
        "plan_digest",
        "estimate_id",
        "revision",
        "predecessor_estimate_id",
        "original_estimate_id",
        "earliest_at",
        "latest_at",
        "issued_at",
        "evidence_class",
        "analogue_ids",
        "sample_size",
        "method",
        "stream_bounds",
        "resource_snapshot_digest",
        "checkpoint_interval_s",
        "recovery_allowance_s",
        "not_included",
        "cohort_key",
        "estimate_digest",
        "cause",
        "notice_preceded_upper_bound",
    }
)


def _content_payload(fields: dict[str, object]) -> dict[str, object]:
    return {
        "authored_run": fields["authored_run"],
        "destination_class": fields["destination_class"],
        "duplicate_of": fields["duplicate_of"],
        "evidence_class": fields["evidence_class"],
        "expires_at": fields["expires_at"],
        "identity": fields["identity"],
        "interface": fields["interface"],
        "licence": fields["licence"],
        "permission_boundary": fields["permission_boundary"],
        "privacy_class": fields["privacy_class"],
        "purpose": fields["purpose"],
        "recheck_at": fields["recheck_at"],
        "source_object": fields["source_object"],
        "supersedes": fields["supersedes"],
        "trust_boundary": fields["trust_boundary"],
        "verifier_semantics": fields["verifier_semantics"],
    }


def new_event_id() -> str:
    """Return the one canonical identity spelling accepted by the trajectory."""
    raw = bytearray(os.urandom(16))
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    text = raw.hex()
    return f"{text[:8]}-{text[8:12]}-{text[12:16]}-{text[16:20]}-{text[20:]}"


def _rollback(fd: int, offset: int) -> None:
    """Best-effort removal of a failed append's bytes. If the truncate itself fails,
    the torn bytes stay and `read()` quarantines them as a rejection — a partial
    line is still never acknowledged."""
    try:
        os.ftruncate(fd, offset)
    except OSError:
        pass


def jittered_sleep(ceiling: float) -> None:
    """Sleep somewhere in [0, ceiling). The one jitter rule, shared by every retry site."""
    spread = (
        ((os.getpid() * 2654435761) ^ time.perf_counter_ns()) % 1_000_003 / 1_000_003
    )
    time.sleep(ceiling * spread)


def _trajectory_fingerprint(directory: Path) -> object:
    """Identity of the whole trajectory, cheap enough to compute on every call.

    Name, SIZE and mtime of each day file. An append always changes the size, so a stale
    hit would need a write that left the byte count identical -- which an append-only log
    cannot do. Costs ten stat() calls against a 1.8 second, 224 MB parse.
    """
    out: list[tuple[str, int, int]] = []
    for path in sorted(directory.glob("*.jsonl")):
        try:
            st = path.stat()
        except OSError:
            return None  # unreadable: refuse to cache rather than cache a guess
        out.append((path.name, st.st_size, st.st_mtime_ns))
    return tuple(out)


def estimate_digest(data: Mapping[str, object]) -> str:
    payload = {key: value for key, value in data.items() if key != "estimate_digest"}
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _cohort_matches(
    candidate: Mapping[str, object], cohort_key: Mapping[str, str]
) -> bool:
    cohort = candidate.get("estimate_cohort")
    if not isinstance(cohort, dict):
        return False
    for field, expected in cohort_key.items():
        value = cohort.get(field)
        if value != expected:
            return False
    return True


def _outcome_duration_s(data: Mapping[str, object]) -> float | None:
    duration = data.get("duration_s")
    if isinstance(duration, (int, float)) and not isinstance(duration, bool):
        return float(duration)
    elapsed = data.get("elapsed_s")
    if isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool):
        return float(elapsed)
    return None


def _outcome_is_censored(data: Mapping[str, object]) -> bool:
    if data.get("timed_out") is True:
        return True
    status = data.get("status")
    return status in {"error", "refused", "timeout"}


def _schedule_stream_bounds(
    plan: Mapping[str, object],
    *,
    lower_s: int,
    upper_s: int,
) -> list[dict[str, object]]:
    streams = cast(list[dict[str, object]], plan["streams"])
    return [
        {
            "stream_id": cast(str, stream["stream_id"]),
            "earliest_s": lower_s,
            "latest_s": upper_s,
        }
        for stream in streams
    ]

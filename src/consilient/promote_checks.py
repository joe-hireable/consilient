"""One question at a time about a candidate, each answered without reference to the
others.

`path_status` is where V0-45 bites: a path is normalised, refused outright if it is
empty or climbs through `..`, then matched against the protected paths before the
allowlist, so the ordering itself is the guarantee — a protected file can never be
reached by also appearing under an admitted prefix. `improved` refuses to call a
candidate improved unless it actually ran, the suite passed and the metric rose; absence
is not evidence. `mechanical_disposition` maps an ADR-0076 class to autonomous,
principal_required, refused or capability_gap, and an unrecognised class falls to
capability_gap rather than to permission. `validate_adverse_table` refuses a table with
a missing or negative row.

The instrument is defended by three of these. `CandidateInstrumentView` exposes the
development tasks and raises on any attempt to reach the hidden items, the instrument
digest or the batch identifier. `reserve_qualification_batch` and `_batch_is_retired`
spend a hidden batch once, so a repeated query against the same lineage and batch is
detectable. `CONTAINMENT_PROBE_SOURCE` is executed through the same callable as the
candidate and is a payload, not a product import — `src/consilient` stays AST-locked.

`reverse` records that a promotion was undone and refuses to write one for a candidate
with no recorded promotion, or without a preimage digest to restore to; the file restore
itself is the script's job. `KINDS` sits here as the closed tuple of events the promoter
may emit. Nothing in this file promotes anything, and nothing here decides."""

from __future__ import annotations
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from .events import SCHEMA_VERSION, append, read_all
from .promote_vocabulary import (
    ACCEPTED,
    ACTIVATION_REFUSED,
    ACTOR,
    ALLOWLIST_PREFIXES,
    AdverseTable,
    CANONICAL_ON_OTHER,
    CONTAINMENT_DENIED,
    CONTAINMENT_SOCKET_ESCAPED,
    CONTAINMENT_SOCKET_PROMPT,
    CONTAINMENT_WRITE_ESCAPED,
    CONTAINMENT_WRITE_PROMPT,
    EVALUATED,
    EvaluationRefusal,
    ExecuteFn,
    ExecutionEvidence,
    IMPACT_CONTRACT_KIND,
    LineageRegistry,
    MISSING_ADVERSE_ROW,
    MechanicalClass,
    NOT_ALLOWLISTED,
    PRIVILEGED_EVALUATION_FIELDS,
    PROMOTER_BETA_RECEIPT_KIND,
    PROTECTED,
    PROTECTED_PREFIXES,
    PromoteError,
    REFUSED,
    REQUIRED_ADVERSE_ROWS,
    REVERSED,
    SealedManifest,
    _canonical_manifest_payload,
    digest,
    normalise_path,
)


__all__ = [
    "ACCEPTED",
    "ACTIVATION_REFUSED",
    "ACTOR",
    "ALLOWLIST_PREFIXES",
    "AdverseTable",
    "CANONICAL_ON_OTHER",
    "CONTAINMENT_DENIED",
    "CONTAINMENT_PROBE_SOURCE",
    "CONTAINMENT_SOCKET_ESCAPED",
    "CONTAINMENT_SOCKET_PROMPT",
    "CONTAINMENT_WRITE_ESCAPED",
    "CONTAINMENT_WRITE_PROMPT",
    "Candidate",
    "CandidateInstrumentView",
    "EVALUATED",
    "EvaluationRefusal",
    "ExecuteFn",
    "ExecutionEvidence",
    "IMPACT_CONTRACT_KIND",
    "ImpactContract",
    "KINDS",
    "LineageRegistry",
    "MISSING_ADVERSE_ROW",
    "MechanicalClass",
    "NOT_ALLOWLISTED",
    "PRIVILEGED_EVALUATION_FIELDS",
    "PROMOTER_BETA_RECEIPT_KIND",
    "PROTECTED",
    "PROTECTED_PREFIXES",
    "PromoteError",
    "REFUSED",
    "REQUIRED_ADVERSE_ROWS",
    "REVERSED",
    "SealedManifest",
    "_canonical_manifest_payload",
    "digest",
    "improved",
    "manifest_digest",
    "mechanical_disposition",
    "normalise_path",
    "path_status",
    "privileged_fields",
    "reserve_qualification_batch",
    "reverse",
    "validate_adverse_table",
]

KINDS = (
    ACCEPTED,
    REFUSED,
    REVERSED,
    EVALUATED,
    IMPACT_CONTRACT_KIND,
    PROMOTER_BETA_RECEIPT_KIND,
    ACTIVATION_REFUSED,
)


@dataclass(frozen=True)
class Candidate:
    identity: str
    path: str
    preimage_sha256: str
    postimage_sha256: str
    evidence: ExecutionEvidence | None = None


@dataclass(frozen=True)
class ImpactContract:
    """Immutable impact contract frozen before first observation (ADR-0076)."""

    experiment_id: str
    target_surface: tuple[str, ...]
    baseline_digests: Mapping[str, str]
    on_confirm: str
    on_kill: str
    on_other: str
    confirm_rule: str
    kill_rule: str
    horizon: str
    largest_effect: str
    safety_floor_version: str
    mechanical_class: str

    def __post_init__(self) -> None:
        if self.on_other.strip().casefold() != CANONICAL_ON_OTHER:
            raise ValueError(
                f"on_other cannot be weakened; must be exactly {CANONICAL_ON_OTHER!r}"
            )
        if self.mechanical_class not in MechanicalClass.ALL:
            raise ValueError(f"unknown mechanical_class {self.mechanical_class!r}")
        for key, value in self.baseline_digests.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("baseline_digests keys must be non-empty strings")
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError(
                    f"baseline_digests[{key!r}] must be a lowercase SHA-256 digest"
                )

    def as_dict(self) -> dict[str, object]:
        return {
            "experiment_id": self.experiment_id,
            "target_surface": list(self.target_surface),
            "baseline_digests": dict(self.baseline_digests),
            "on_confirm": self.on_confirm,
            "on_kill": self.on_kill,
            "on_other": self.on_other,
            "confirm_rule": self.confirm_rule,
            "kill_rule": self.kill_rule,
            "horizon": self.horizon,
            "largest_effect": self.largest_effect,
            "safety_floor_version": self.safety_floor_version,
            "mechanical_class": self.mechanical_class,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> ImpactContract:
        baseline = data.get("baseline_digests", {})
        if not isinstance(baseline, Mapping):
            raise ValueError("baseline_digests must be an object")
        surfaces = data.get("target_surface", [])
        if not isinstance(surfaces, list):
            raise ValueError("target_surface must be a list")
        return cls(
            experiment_id=str(data["experiment_id"]),
            target_surface=tuple(str(item) for item in surfaces),
            baseline_digests={str(k): str(v) for k, v in baseline.items()},
            on_confirm=str(data["on_confirm"]),
            on_kill=str(data["on_kill"]),
            on_other=str(data["on_other"]),
            confirm_rule=str(data["confirm_rule"]),
            kill_rule=str(data["kill_rule"]),
            horizon=str(data["horizon"]),
            largest_effect=str(data["largest_effect"]),
            safety_floor_version=str(data["safety_floor_version"]),
            mechanical_class=str(data["mechanical_class"]),
        )


@dataclass(frozen=True)
class CandidateInstrumentView:
    """Candidate-visible instrument slice; hidden items are unreachable."""

    _manifest: SealedManifest

    @property
    def development_tasks(self) -> tuple[tuple[str, str], ...]:
        return self._manifest.development_tasks

    def __getattr__(self, name: str) -> object:
        if name in {"hidden_items", "instrument_digest", "qualification_batch_id"}:
            raise AttributeError(f"{name} is privileged and unavailable to candidates")
        raise AttributeError(name)


def mechanical_disposition(mechanical_class: str) -> str:
    """Return autonomous, principal_required, refused or capability_gap."""
    match mechanical_class:
        case MechanicalClass.CANDIDATE_ONLY | MechanicalClass.SENSING_ONLY:
            return "autonomous"
        case MechanicalClass.ACTIVE_HARNESS:
            return "principal_required"
        case MechanicalClass.EXACT_ROLLBACK:
            return "autonomous"
        case MechanicalClass.INSTRUMENT | MechanicalClass.EXISTING_PRINCIPAL_EFFECT:
            return "refused"
        case MechanicalClass.UNKNOWN_OR_MIXED:
            return "capability_gap"
        case _:
            return "capability_gap"


def path_status(path: str) -> str:
    """protected, allowlisted, or not_allowlisted. V0-45."""
    normalised = normalise_path(path)
    if not normalised or ".." in normalised.split("/"):
        return NOT_ALLOWLISTED
    for prefix in PROTECTED_PREFIXES:
        if normalised == prefix.rstrip("/") or normalised.startswith(prefix):
            return PROTECTED
    for prefix in ALLOWLIST_PREFIXES:
        if normalised.startswith(prefix):
            return "allowlisted"
    return NOT_ALLOWLISTED


def improved(evidence: ExecutionEvidence) -> bool:
    return (
        evidence.ran
        and evidence.suite_passed
        and evidence.metric_after > evidence.metric_before
    )


def reverse(
    log_dir: Path, candidate_id: str, preimage_sha256: str
) -> dict[str, object]:
    """Record that a promotion was undone. File restore is the script's job."""
    if not candidate_id.strip() or len(preimage_sha256) != 64:
        raise PromoteError("a reversal names the candidate and its preimage digest")
    accepted = [
        event
        for event in read_all(log_dir)[0]
        if event.kind == ACCEPTED and event.data.get("candidate_id") == candidate_id
    ]
    if not accepted:
        raise PromoteError(f"no recorded promotion for {candidate_id}")
    now = datetime.now(timezone.utc)
    return append(
        log_dir / f"{now.date().isoformat()}.jsonl",
        {
            "v": SCHEMA_VERSION,
            "ts": now.isoformat(),
            "event": REVERSED,
            "actor": ACTOR,
            "data": {
                "candidate_id": candidate_id,
                "preimage_sha256": preimage_sha256,
                "reason": "reversed",
            },
        },
    )


def manifest_digest(data: Mapping[str, object]) -> str:
    canonical = json.dumps(_canonical_manifest_payload(data), sort_keys=True)
    return digest(canonical)


def validate_adverse_table(adverse: AdverseTable) -> None:
    for field in REQUIRED_ADVERSE_ROWS:
        value = adverse.as_dict()[field]
        if not isinstance(value, int) or value < 0:
            raise EvaluationRefusal(MISSING_ADVERSE_ROW, detail=field)


def privileged_fields() -> frozenset[str]:
    return PRIVILEGED_EVALUATION_FIELDS


def reserve_qualification_batch(
    registry: LineageRegistry,
    lineage_id: str,
    batch_id: str,
) -> LineageRegistry:
    key = (lineage_id, batch_id)
    if key in registry.retired_batches:
        return registry
    return LineageRegistry(registry.retired_batches | {key})


def _batch_is_retired(
    registry: LineageRegistry,
    lineage_id: str,
    batch_id: str,
) -> bool:
    return (lineage_id, batch_id) in registry.retired_batches


# Executed through the same `execute` callable as the candidate. A contained
# path returns CONTAINMENT_DENIED for both prompts; a socket bind or a write
# outside scratch returns the matching escaped sentinel. This is a payload,
# not a product import: src/consilient stays AST-locked.
CONTAINMENT_PROBE_SOURCE = f"""\
def solve(prompt):
    if prompt == {CONTAINMENT_SOCKET_PROMPT!r}:
        try:
            sock = __import__("socket").socket()
            try:
                sock.bind(("127.0.0.1", 0))
                sock.getsockname()
            finally:
                sock.close()
            return {CONTAINMENT_SOCKET_ESCAPED!r}
        except OSError:
            return {CONTAINMENT_DENIED!r}
    if prompt == {CONTAINMENT_WRITE_PROMPT!r}:
        os_mod = __import__("os")
        tempfile_mod = __import__("tempfile")
        path = os_mod.path.join(
            tempfile_mod.gettempdir(),
            "consilient-promote-escape-probe",
        )
        try:
            handle = open(path, "w", encoding="utf-8")
            try:
                handle.write("escaped")
            finally:
                handle.close()
            if not os_mod.path.isfile(path):
                return {CONTAINMENT_DENIED!r}
            return {CONTAINMENT_WRITE_ESCAPED!r}
        except OSError:
            return {CONTAINMENT_DENIED!r}
        finally:
            try:
                os_mod.remove(path)
            except OSError:
                pass
    return {CONTAINMENT_DENIED!r}
"""


def _execute_and_score(
    execute: ExecuteFn,
    source: str,
    cases: Sequence[tuple[str, str]],
) -> tuple[bool, float]:
    ran, outputs = execute(source, [prompt for prompt, _ in cases])
    if not ran or len(outputs) != len(cases):
        return False, 0.0
    if not cases:
        return True, 0.0
    hits = sum(
        output is not None and output == expected
        for output, (_, expected) in zip(outputs, cases, strict=True)
    )
    return True, hits / len(cases)

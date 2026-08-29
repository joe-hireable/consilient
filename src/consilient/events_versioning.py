"""The two records of the harness changing what it is made of.

`CapabilityManifest` is one versioned capability — a tool, an MCP server, a skill, a
plugin or a connection — addressed by its identity and by immutable digests, so that a
capability referred to a month later is demonstrably the same capability and not merely
the same name.

The model.change contract applies the same discipline to learned state (M06). A change
is typed by its mutation class, as data-driven training or as a non-data-driven state
change, carries its status, and is checked at the writer rather than trusted from
whoever called it. The distinction matters because retrieval over frozen embeddings is
not training, and a system that files it as training loses the ability to say what
actually changed.

Both exist for the same reason: a harness that re-equips itself without recording it has
no comparable history, and a β figure spanning an unrecorded change is a figure about
two different systems reported as one."""

from __future__ import annotations
from dataclasses import dataclass
from .events_vocabulary import (
    CAPABILITY_MANIFEST_STATUSES,
    MODEL_CHANGE_FIELDS,
    MODEL_CHANGE_KIND_ALIASES,
    MODEL_CHANGE_MUTATION_CLASSES,
)

from .events_digests import (
    _nullable_sha256,
    content_digest,
    execution_contract_key,
)

from .events_durability import (
    parse_capability_identity,
)

from .events_fields import (
    _check_uuid4,
    _explicit_disposition,
    _sha256_hex,
    canonical,
)

from .events_kinds import (
    CAPABILITY_VERSIONED_KIND,
    EventError,
    EventPayload,
    MODEL_CHANGE_KIND,
    MODEL_CHANGE_STATUSES,
    RECORD_CAPTURED_KIND,
    _HEX,
)

from .events_references import (
    _check_event_reference,
    version_digest,
)


__all__ = [
    "CAPABILITY_MANIFEST_STATUSES",
    "CAPABILITY_VERSIONED_KIND",
    "CapabilityManifest",
    "EventError",
    "EventPayload",
    "MODEL_CHANGE_FIELDS",
    "MODEL_CHANGE_KIND",
    "MODEL_CHANGE_KIND_ALIASES",
    "MODEL_CHANGE_MUTATION_CLASSES",
    "MODEL_CHANGE_STATUSES",
    "RECORD_CAPTURED_KIND",
    "_HEX",
    "_check_event_reference",
    "_check_uuid4",
    "_explicit_disposition",
    "_nullable_sha256",
    "_sha256_hex",
    "canonical",
    "content_digest",
    "execution_contract_key",
    "parse_capability_identity",
    "version_digest",
]


@dataclass(frozen=True)
class CapabilityManifest:
    """One versioned capability, addressed by identity and immutable digests."""

    identity: str
    kind: str
    name: str
    source_object: dict[str, object]
    authored_run: str
    licence: str
    privacy_class: str
    purpose: str
    interface: dict[str, object]
    permission_boundary: str
    trust_boundary: str
    verifier_semantics: str
    evidence_class: str
    status: str
    destination_class: str
    duplicate_of: dict[str, object] | None
    supersedes: dict[str, object] | None
    expires_at: str | None
    recheck_at: str | None
    content_digest: str
    execution_contract_key: str
    version_digest: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "authored_run": self.authored_run,
            "content_digest": self.content_digest,
            "destination_class": self.destination_class,
            "duplicate_of": self.duplicate_of,
            "evidence_class": self.evidence_class,
            "execution_contract_key": self.execution_contract_key,
            "expires_at": self.expires_at,
            "identity": self.identity,
            "interface": self.interface,
            "licence": self.licence,
            "permission_boundary": self.permission_boundary,
            "privacy_class": self.privacy_class,
            "purpose": self.purpose,
            "recheck_at": self.recheck_at,
            "source_object": self.source_object,
            "status": self.status,
            "supersedes": self.supersedes,
            "trust_boundary": self.trust_boundary,
            "verifier_semantics": self.verifier_semantics,
            "version_digest": self.version_digest,
        }

    @classmethod
    def from_mapping(cls, value: object) -> CapabilityManifest:
        if not isinstance(value, dict):
            raise EventError("capability manifest must be an object")
        record: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise EventError("capability manifest keys must be strings")
            record[key] = item
        kind, name = parse_capability_identity(record.get("identity"))
        status = record.get("status")
        if status not in CAPABILITY_MANIFEST_STATUSES:
            raise EventError(
                f"status must be one of {sorted(CAPABILITY_MANIFEST_STATUSES)!r}"
            )

        def text(field: str) -> str:
            raw = record.get(field)
            if (
                not isinstance(raw, str)
                or not raw
                or raw != raw.strip()
                or not raw.isprintable()
            ):
                raise EventError(f"{field} must be non-empty printable text")
            return raw

        def nullable_text(field: str) -> str | None:
            raw = record.get(field)
            if raw is None:
                return None
            return text(field)

        def mapping(field: str) -> dict[str, object]:
            raw = record.get(field)
            if not isinstance(raw, dict):
                raise EventError(f"{field} must be an object")
            return raw

        def nullable_mapping(field: str) -> dict[str, object] | None:
            raw = record.get(field)
            if raw is None:
                return None
            return mapping(field)

        payload: dict[str, object] = {
            "authored_run": text("authored_run"),
            "destination_class": text("destination_class"),
            "duplicate_of": nullable_mapping("duplicate_of"),
            "evidence_class": text("evidence_class"),
            "expires_at": nullable_text("expires_at"),
            "identity": f"{kind}:{name}",
            "interface": mapping("interface"),
            "licence": text("licence"),
            "permission_boundary": text("permission_boundary"),
            "privacy_class": text("privacy_class"),
            "purpose": text("purpose"),
            "recheck_at": nullable_text("recheck_at"),
            "source_object": mapping("source_object"),
            "status": status,
            "supersedes": nullable_mapping("supersedes"),
            "trust_boundary": text("trust_boundary"),
            "verifier_semantics": text("verifier_semantics"),
        }
        expected_content = content_digest(payload)
        expected_contract = execution_contract_key(payload)
        payload["content_digest"] = expected_content
        payload["execution_contract_key"] = expected_contract
        expected_version = version_digest(payload)
        if "content_digest" in record and record["content_digest"] != expected_content:
            raise EventError("content_digest does not match canonical content")
        if (
            "execution_contract_key" in record
            and record["execution_contract_key"] != expected_contract
        ):
            raise EventError("execution_contract_key does not match canonical contract")
        if "version_digest" in record:
            digest = record["version_digest"]
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in _HEX for character in digest)
            ):
                raise EventError(
                    "version_digest must be 64 lowercase hexadecimal characters"
                )
            if digest != expected_version:
                raise EventError("version_digest does not match canonical version")
        return cls(
            identity=str(payload["identity"]),
            kind=kind,
            name=name,
            source_object=mapping("source_object"),
            authored_run=str(payload["authored_run"]),
            licence=str(payload["licence"]),
            privacy_class=str(payload["privacy_class"]),
            purpose=str(payload["purpose"]),
            interface=mapping("interface"),
            permission_boundary=str(payload["permission_boundary"]),
            trust_boundary=str(payload["trust_boundary"]),
            verifier_semantics=str(payload["verifier_semantics"]),
            evidence_class=str(payload["evidence_class"]),
            status=str(status),
            destination_class=str(payload["destination_class"]),
            duplicate_of=nullable_mapping("duplicate_of"),
            supersedes=nullable_mapping("supersedes"),
            expires_at=payload["expires_at"]
            if payload["expires_at"] is None
            else str(payload["expires_at"]),
            recheck_at=payload["recheck_at"]
            if payload["recheck_at"] is None
            else str(payload["recheck_at"]),
            content_digest=expected_content,
            execution_contract_key=expected_contract,
            version_digest=expected_version,
        )


def _check_model_change_contract(event: EventPayload) -> None:
    """M06: one exact model.change contract at the F02/F03 writer."""
    kind = event["event"]
    if kind != MODEL_CHANGE_KIND:
        if kind in MODEL_CHANGE_KIND_ALIASES:
            raise EventError(
                f"model event kind must be {MODEL_CHANGE_KIND!r}; aliases are not accepted"
            )
        return

    data = event["data"]
    actual = set(data)
    if actual != MODEL_CHANGE_FIELDS:
        missing = sorted(MODEL_CHANGE_FIELDS - actual)
        unexpected = sorted(actual - MODEL_CHANGE_FIELDS)
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if unexpected:
            detail.append(f"unexpected {unexpected}")
        raise EventError(
            f"{MODEL_CHANGE_KIND} body fields are fixed: {'; '.join(detail)}"
        )

    _check_uuid4(data["change_id"], f"{MODEL_CHANGE_KIND} change_id")
    mutation_class = data["mutation_class"]
    if mutation_class not in MODEL_CHANGE_MUTATION_CLASSES:
        raise EventError(
            f"{MODEL_CHANGE_KIND} mutation_class must be one of "
            f"{sorted(MODEL_CHANGE_MUTATION_CLASSES)}"
        )
    status = data["status"]
    if status not in MODEL_CHANGE_STATUSES:
        raise EventError(
            f"{MODEL_CHANGE_KIND} status must be one of {sorted(MODEL_CHANGE_STATUSES)}"
        )

    authoring_run = data["authoring_run"]
    if (
        not isinstance(authoring_run, str)
        or not authoring_run
        or authoring_run != authoring_run.strip()
        or not authoring_run.isprintable()
    ):
        raise EventError(
            f"{MODEL_CHANGE_KIND} authoring_run must be non-empty printable text"
        )

    _sha256_hex(MODEL_CHANGE_KIND, data["base_model_digest"], "base_model_digest")
    _sha256_hex(MODEL_CHANGE_KIND, data["procedure_digest"], "procedure_digest")
    dataset_digest = _nullable_sha256(
        MODEL_CHANGE_KIND, data["dataset_digest"], "dataset_digest"
    )
    checkpoint_digest = _nullable_sha256(
        MODEL_CHANGE_KIND, data["checkpoint_digest"], "checkpoint_digest"
    )
    _explicit_disposition(MODEL_CHANGE_KIND, data["licence"], "licence")
    _explicit_disposition(MODEL_CHANGE_KIND, data["privacy_class"], "privacy_class")

    _check_event_reference(
        data["base_model"], MODEL_CHANGE_KIND, "base_model", RECORD_CAPTURED_KIND
    )
    _check_event_reference(
        data["procedure"], MODEL_CHANGE_KIND, "procedure", CAPABILITY_VERSIONED_KIND
    )

    dataset = data["dataset"]
    checkpoint = data["checkpoint"]
    if (dataset is None) != (dataset_digest is None):
        raise EventError(
            f"{MODEL_CHANGE_KIND} dataset and dataset_digest must be set together"
        )
    if (checkpoint is None) != (checkpoint_digest is None):
        raise EventError(
            f"{MODEL_CHANGE_KIND} checkpoint and checkpoint_digest must be set together"
        )
    if mutation_class == "data_driven_training":
        if dataset is None:
            raise EventError(
                f"{MODEL_CHANGE_KIND} data-driven training requires a dataset record"
            )
        _check_event_reference(
            dataset, MODEL_CHANGE_KIND, "dataset", RECORD_CAPTURED_KIND
        )
    elif dataset is not None:
        raise EventError(
            f"{MODEL_CHANGE_KIND} non-data-driven change must not carry a dataset"
        )

    failure = data["failure"]
    if status == "succeeded":
        if checkpoint is None:
            raise EventError(
                f"{MODEL_CHANGE_KIND} succeeded records require a checkpoint"
            )
        if failure is not None:
            raise EventError(
                f"{MODEL_CHANGE_KIND} succeeded records must not carry a failure"
            )
    elif status in {"failed", "refused"}:
        if (
            not isinstance(failure, str)
            or not failure.strip()
            or failure != failure.strip()
        ):
            raise EventError(
                f"{MODEL_CHANGE_KIND} {status} records require a visible failure reason"
            )
    else:
        if failure is not None:
            raise EventError(
                f"{MODEL_CHANGE_KIND} started records must not carry a failure"
            )
        if checkpoint is not None:
            raise EventError(
                f"{MODEL_CHANGE_KIND} started records must not carry a checkpoint"
            )

    if checkpoint is not None:
        _check_event_reference(
            checkpoint, MODEL_CHANGE_KIND, "checkpoint", RECORD_CAPTURED_KIND
        )

    event_id = event.get("event_id")
    for relation in ("base_model", "dataset", "procedure", "checkpoint"):
        reference = data[relation]
        if isinstance(reference, dict) and reference.get("event_id") == event_id:
            raise EventError(f"{MODEL_CHANGE_KIND} {relation} cannot reference itself")

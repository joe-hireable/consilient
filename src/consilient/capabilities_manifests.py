"""Selection over stored capability manifests, which is a different question from
selecting an allowlist row.

retrieve_manifest returns one stored version by identity and digest, including inactive
predecessors, because a superseded manifest still has to be readable. _select_manifests
resolves requested identities and execution contract keys against active heads and
refuses rather than guesses: a conflict touching the request becomes a refusal, and
anything other than exactly one matching active head becomes an omission. Neither
outcome is silently dropped, and neither is turned into a selection.

It reads its validators from capabilities_parse and is read in turn by
capabilities.select_capabilities, so the dependency runs one way only."""

from .capabilities_parse import (
    CapabilityError,
    _array,
    _hex_digest,
    _inventory_document,
    _object,
    _text,
    parse_identity,
)


__all__ = [
    "CapabilityError",
    "_array",
    "_hex_digest",
    "_inventory_document",
    "_object",
    "_text",
    "parse_identity",
    "retrieve_manifest",
]


def _row_object(value: object, label: str) -> dict[str, object]:
    return _object(value, label)


def _manifest_selection(row: dict[str, object]) -> dict[str, object]:
    return {
        "destination_class": row["destination_class"],
        "evidence_class": row.get("evidence_class"),
        "execution_contract_key": row["execution_contract_key"],
        "identity": row["identity"],
        "manifest_event_id": row.get("event_id") or row.get("manifest_event_id"),
        "permission_boundary": row.get("permission_boundary"),
        "status": row["status"],
        "trust_boundary": row.get("trust_boundary"),
        "version_digest": row["version_digest"],
    }


def retrieve_manifest(
    inventory: object, *, identity: str, version_digest: str
) -> dict[str, object]:
    """Return one stored manifest version, including inactive predecessors."""
    document = _inventory_document(inventory)
    parse_identity(identity)
    digest = _hex_digest(version_digest, "version_digest")
    for index, value in enumerate(
        _array(document.get("manifests", []), "inventory manifests")
    ):
        row = _row_object(value, f"inventory manifests[{index}]")
        if row.get("identity") == identity and row.get("version_digest") == digest:
            return dict(row)
    raise CapabilityError(f"unknown capability manifest: {identity}@{digest}")


def _select_manifests(
    document: dict[str, object], request: dict[str, object]
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    identities = request.get("identities")
    contract_keys = request.get("execution_contract_keys")
    destination = request.get("destination_class")
    if identities is None and contract_keys is None:
        return [], [], []
    wanted_identities = (
        [
            _text(item, f"identities[{index}]")
            for index, item in enumerate(_array(identities, "identities"))
        ]
        if identities is not None
        else []
    )
    wanted_keys = (
        [
            _hex_digest(item, f"execution_contract_keys[{index}]")
            for index, item in enumerate(
                _array(contract_keys, "execution_contract_keys")
            )
        ]
        if contract_keys is not None
        else []
    )
    if destination is not None:
        destination = _text(destination, "destination_class")
    for identity in wanted_identities:
        parse_identity(identity)

    heads = [
        _row_object(item, f"inventory heads[{index}]")
        for index, item in enumerate(
            _array(document.get("heads", []), "inventory heads")
        )
    ]
    conflicts = [
        _row_object(item, f"inventory conflicts[{index}]")
        for index, item in enumerate(
            _array(document.get("conflicts", []), "inventory conflicts")
        )
    ]
    manifests = [
        _row_object(item, f"inventory manifests[{index}]")
        for index, item in enumerate(
            _array(document.get("manifests", []), "inventory manifests")
        )
    ]
    selected: list[dict[str, object]] = []
    refusals: list[dict[str, object]] = []
    omissions: list[dict[str, object]] = []

    def _identity_contract_keys(identity: str) -> tuple[set[str], set[str]]:
        keys: set[str] = set()
        event_ids: set[str] = set()
        for row in manifests:
            if row.get("identity") != identity:
                continue
            contract = row.get("execution_contract_key")
            if isinstance(contract, str):
                keys.add(contract)
            event_id = row.get("event_id")
            if isinstance(event_id, str):
                event_ids.add(event_id)
        return keys, event_ids

    def matching_conflicts(
        identity: str | None, key: str | None
    ) -> list[dict[str, object]]:
        found: list[dict[str, object]] = []
        identity_keys: set[str] = set()
        identity_event_ids: set[str] = set()
        if identity is not None:
            identity_keys, identity_event_ids = _identity_contract_keys(identity)
        for conflict in conflicts:
            if (
                destination is not None
                and conflict.get("destination_class") != destination
            ):
                continue
            contract = conflict.get("execution_contract_key")
            event_ids = conflict.get("event_ids")
            involved = set(event_ids) if isinstance(event_ids, list) else set()
            if key is not None:
                if contract != key:
                    continue
            elif identity is not None:
                if (
                    contract not in identity_keys
                    and conflict.get("identity") != identity
                    and not identity_event_ids.intersection(involved)
                ):
                    continue
            else:
                continue
            found.append(conflict)
        return found

    for identity in wanted_identities:
        hits = matching_conflicts(identity, None)
        if hits:
            refusals.append({"identity": identity, "reason": "active-head conflict"})
            continue
        matches = [
            head
            for head in heads
            if head.get("identity") == identity
            and head.get("status") == "active"
            and (destination is None or head.get("destination_class") == destination)
        ]
        if len(matches) == 1:
            selected.append(_manifest_selection(matches[0]))
        else:
            omissions.append(
                {"identity": identity, "reason": "no selectable active head"}
            )

    for key in wanted_keys:
        hits = matching_conflicts(None, key)
        if hits:
            refusals.append(
                {"execution_contract_key": key, "reason": "active-head conflict"}
            )
            continue
        matches = [
            head
            for head in heads
            if head.get("execution_contract_key") == key
            and head.get("status") == "active"
            and (destination is None or head.get("destination_class") == destination)
        ]
        if len(matches) == 1:
            row = _manifest_selection(matches[0])
            if row not in selected:
                selected.append(row)
        else:
            omissions.append(
                {"execution_contract_key": key, "reason": "no selectable active head"}
            )
    return selected, refusals, omissions

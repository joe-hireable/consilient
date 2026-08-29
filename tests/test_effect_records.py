"""Effect intents and receipts as the log admits them, and the chain that joins them.

These are the cases where a record reaches `validate`, `append` or `append_transaction`
rather than staying in memory, which is why they are apart from the manifest-shape
tests. The intent side pins the two admission discriminants -- a decision-free
observation may carry no `decision_id` and no mutating operation, a material reach must
carry an authority chain -- together with the two supports that keep the observation
predicate honest: `MUTATION_EFFECTS` and `READ_ONLY_EFFECTS` staying disjoint, and
`_intent` still calling `_observation_predicate` rather than an inline effects-only
check, which would miss a mutating operation on a read class. The receipt side pins what
a receipt may not do: persist a provider payload verbatim, record a non-finite
consumption, bind a manifest it was not filed against, fork into two heads claiming
incompatible outcomes, or escape the replayed history through a non-JSONL path. Midnight
is covered explicitly, because a day boundary must not turn one operation into two
receipt chains.

A01's review found
`test_receipt_chain_ignores_a_rejection_unrelated_to_the_effect_chain` failing: a
rejected line of *any* kind sharing the log directory blocked every write-ahead effect
intent, including one with no relation to the effect chain at all. That case and its
opposite -- a rejected `effect.intent` or `effect.receipt` line, which must block -- are
kept side by side so the pair is read together."""

import ast
import hashlib
import inspect
import json
from datetime import datetime, timezone
from math import inf, nan
from pathlib import Path
import pytest
from consilient import effects as effects_mod
from consilient import events_transactions
from consilient.effects import (
    EFFECT_INTENT,
    EFFECT_RECEIPT,
    MUTATION_EFFECTS,
    READ_ONLY_EFFECTS,
    EffectError,
    EffectManifest,
    receipt_chain_validator,
)
from consilient.events import (
    EventError,
    canonical,
    Rejection,
    SCHEMA_VERSION,
    append,
    append_transaction,
    validate,
)
from effect_contract_helpers import (
    broker_reference,
    commitment,
    manifest,
)


def event(
    kind: str, data: dict[str, object], *, ts: str | None = None
) -> dict[str, object]:
    return {
        "v": SCHEMA_VERSION,
        "ts": ts or datetime.now(timezone.utc).isoformat(),
        "event": kind,
        "actor": "effect-contract-test",
        "data": data,
    }


def intent_data(
    manifest_value: EffectManifest, *, observation: bool = False
) -> dict[str, object]:
    return {
        "intent_id": "intent-1",
        "manifest": manifest_value.binding(),
        "disposition": "refused",
        "decision_id": None if observation else "decision-1",
        "admission": (
            {"kind": "observation", "observation_id": "observation-1"}
            if observation
            else {
                "kind": "material",
                "authority_chain": {
                    "kind": "autonomous_decision",
                    "decision_id": "decision-1",
                },
            }
        ),
    }


def receipt_data(
    *, receipt_id: str, status: str, supersedes: str | None = None
) -> dict[str, object]:
    data: dict[str, object] = {
        "receipt_id": receipt_id,
        "intent_id": "intent-1",
        "manifest_digest": manifest().digest,
        "status": status,
        "started_at": "2026-08-23T10:00:00+00:00",
        "ended_at": "2026-08-23T10:00:01+00:00",
        "provider_request": broker_reference("provider-request"),
        "provider_receipt": broker_reference("provider-receipt"),
        "request_commitment": commitment("effect.receipt.request"),
        "response_commitment": commitment("effect.receipt.response"),
        "content_commitment": commitment("effect.receipt.content"),
        "observed_consumption": {"cpu_seconds": 1},
        "post_state": commitment("effect.receipt.post_state"),
        "observed_residuals": ("elapsed_time",),
        "child_operation_ids": (),
    }
    if supersedes is not None:
        data["supersedes"] = supersedes
    return data


def test_effect_events_validate_the_observation_and_material_discriminants() -> None:
    """Production break caught: material reach can omit a decision/authority chain."""
    value = manifest()
    validate(event("effect.intent", intent_data(value, observation=True)))
    validate(event("effect.intent", intent_data(value)))

    invalid = intent_data(value, observation=True)
    invalid["decision_id"] = "decision-1"
    with pytest.raises(EventError, match="observation"):
        validate(event("effect.intent", invalid))

    invalid = intent_data(value)
    invalid["admission"] = {"kind": "material", "authority_chain": []}
    with pytest.raises(EventError, match="authority chain"):
        validate(event("effect.intent", invalid))

    reference = intent_data(value)
    reference["manifest"] = {
        "kind": "reference",
        "reference": broker_reference("manifest"),
        "digest": value.digest,
    }
    validate(event("effect.intent", reference))


def test_receipt_fields_reject_raw_provider_payloads() -> None:
    """Production break caught: a provider response/content payload is persisted verbatim."""
    payload = receipt_data(receipt_id="receipt-unknown", status="unknown")
    payload["provider_receipt"] = {"response": "private reply"}
    with pytest.raises(EventError, match="broker reference|commitment"):
        validate(event("effect.receipt", payload))
    for amount in (nan, inf, -inf):
        payload = receipt_data(receipt_id="receipt-unknown", status="unknown")
        payload["observed_consumption"] = {"cpu_seconds": amount}
        with pytest.raises(EventError, match="finite"):
            validate(event("effect.receipt", payload))
    payload = receipt_data(receipt_id="receipt-unknown", status="unknown")
    payload["observed_consumption"] = {"cpu_seconds": 10**1000}
    validate(event("effect.receipt", payload))


def test_receipt_binds_the_manifest_digest_of_its_intent(tmp_path) -> None:
    """Production break caught: a receipt can be filed against a different manifest."""
    value = manifest()
    path = tmp_path / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    append_transaction(
        tmp_path,
        [event("effect.intent", intent_data(value))],
        lambda prefix, rejections, candidates: None,
    )
    mismatch = receipt_data(receipt_id="receipt-mismatch", status="failed")
    mismatch["manifest_digest"] = "0" * 64
    with pytest.raises(EventError, match="manifest digest"):
        append(path, event("effect.receipt", mismatch))


def test_receipt_chain_allows_one_unknown_resolution_and_refuses_a_fork(
    tmp_path,
) -> None:
    """Production break caught: two receipt heads can claim incompatible outcomes."""
    value = manifest()
    append_transaction(
        tmp_path,
        [
            event("effect.intent", intent_data(value)),
            event(
                "effect.receipt",
                receipt_data(receipt_id="receipt-unknown", status="unknown"),
            ),
        ],
        lambda prefix, rejections, candidates: None,
    )
    append(
        tmp_path / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl",
        event(
            "effect.receipt",
            receipt_data(
                receipt_id="receipt-final",
                status="failed",
                supersedes="receipt-unknown",
            ),
        ),
    )
    with pytest.raises(EventError, match="receipt chain"):
        append(
            tmp_path / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl",
            event(
                "effect.receipt",
                receipt_data(receipt_id="receipt-fork", status="succeeded"),
            ),
        )


def test_mutation_effects_are_disjoint_from_read_only_effects() -> None:
    """A read-only class in MUTATION_EFFECTS makes the observation predicate lie."""
    assert MUTATION_EFFECTS & READ_ONLY_EFFECTS == frozenset()
    assert "data.read" not in MUTATION_EFFECTS
    assert "network.call" not in MUTATION_EFFECTS


@pytest.mark.parametrize("operation", ["write", "plan"])
def test_observation_intent_refuses_a_mutating_operation(operation: str) -> None:
    """Decision-free observation cannot record a mutating provider operation."""
    record = manifest().to_record()
    record["operations"] = [operation]
    value = EffectManifest.from_record(record)
    with pytest.raises(EventError, match="read-only"):
        validate(event("effect.intent", intent_data(value, observation=True)))


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in tree.body if isinstance(tree, ast.Module) else ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} is missing")


def test_intent_calls_observation_predicate() -> None:
    """An inline effects-only check misses a mutating operation on a read class."""
    # Read the file `_intent` actually lives in, not the module it is imported from. It moved to
    # effects_proof.py in the 28 August 2026 split and this test then failed with "_intent is
    # missing", which reads like a deleted function rather than a moved one. Asking the function
    # object where its source is keeps the check pointed at the code it is about.
    source = Path(
        inspect.getsourcefile(effects_mod._intent) or effects_mod.__file__
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {
        node.func.id
        for node in ast.walk(_function_def(tree, "_intent"))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_observation_predicate" in names


def test_receipt_chain_resolves_an_unknown_across_daily_logs(
    tmp_path, monkeypatch
) -> None:
    """Production break caught: midnight turns one operation into two receipt chains."""
    monkeypatch.setattr(events_transactions, "_check_clock", lambda event: None)
    value = manifest()
    first_day = "2026-08-23T10:00:00+00:00"
    second_day = "2026-08-24T10:00:00+00:00"
    append_transaction(
        tmp_path,
        [
            event("effect.intent", intent_data(value), ts=first_day),
            event(
                "effect.receipt",
                receipt_data(receipt_id="receipt-unknown", status="unknown"),
                ts=first_day,
            ),
        ],
        lambda prefix, rejections, candidates: None,
    )
    append(
        tmp_path / "2026-08-24.jsonl",
        event(
            "effect.receipt",
            receipt_data(
                receipt_id="receipt-final",
                status="failed",
                supersedes="receipt-unknown",
            ),
            ts=second_day,
        ),
    )


def test_receipt_chain_refuses_a_rejected_effect_history_line() -> None:
    """Production break caught: a corrupt earlier record is ignored while a new chain is admitted."""
    with pytest.raises(EffectError, match="rejected"):
        receipt_chain_validator(
            (),
            (Rejection("effect.jsonl", 1, "malformed", event_kind=EFFECT_INTENT),),
            (),
        )
    with pytest.raises(EffectError, match="rejected"):
        receipt_chain_validator(
            (),
            (Rejection("effect.jsonl", 1, "malformed", event_kind=EFFECT_RECEIPT),),
            (),
        )


def test_receipt_chain_ignores_a_rejection_unrelated_to_the_effect_chain() -> None:
    """A01's review found this failing: a rejected line of *any* kind sharing the log
    directory blocked every write-ahead effect intent, including one with no relation to
    the effect chain at all."""
    receipt_chain_validator((), (Rejection("log.jsonl", 1, "malformed"),), ())
    receipt_chain_validator(
        (), (Rejection("log.jsonl", 1, "malformed", event_kind="note.made"),), ()
    )


def test_effect_records_require_a_jsonl_authority_path(tmp_path) -> None:
    """Production break caught: a non-JSONL append escapes the replayed chain history."""
    path = tmp_path / "effects.log"
    with pytest.raises(EventError, match="JSONL"):
        append(path, event("effect.intent", intent_data(manifest())))
    assert not path.exists()


# --- Replay of the effect chain, restored from unit A01 -------------------------------------
#
# A01's commit 750f73bd3 (27 August 2026) could not be cherry-picked after the 28 August splits:
# it edits effects.py, events.py and test_effect_contract.py, all three of which became facades,
# so every hunk conflicted. Resolving those conflicts in place would have written the logic back
# into re-export manifests. The behaviour was applied to the files that now hold it -- the three
# manifest refusals to effects_grammar.receipt_chain_validator, the ordered replay to
# events_transactions.read_all, and Event.content_digest to events_durability -- and A01's tests
# live here rather than in test_effect_contract.py, whose docstring says nothing in that module
# touches a log. These do.


def test_replay_quarantines_a_forked_final_receipt(tmp_path) -> None:
    """A second final receipt for one intent is refused at the line, not at the file."""
    path = tmp_path / "2026-08-23.jsonl"
    fork = event(
        "effect.receipt",
        receipt_data(receipt_id="receipt-succeeded", status="succeeded"),
    )
    fork_line = json.dumps(fork, separators=(", ", ": ")) + "\n"
    path.write_text(
        "\n".join(
            (
                canonical(event("effect.intent", intent_data(manifest()))),
                canonical(
                    event(
                        "effect.receipt",
                        receipt_data(receipt_id="receipt-failed", status="failed"),
                    )
                ),
            )
        )
        + "\n"
        + fork_line,
        encoding="utf-8",
    )

    accepted, rejected = events_transactions.read_all(tmp_path)

    assert [item.kind for item in accepted] == ["effect.intent", "effect.receipt"]
    assert [(item.event_kind, item.line) for item in rejected] == [("effect.receipt", 3)]
    assert "receipt chain has conflicting heads" in rejected[0].reason
    # The digest is why Event carries content_digest: the demoted line must still be
    # identifiable by its exact bytes, and re-reading the file to recover it would be a
    # second read of something already parsed.
    assert (
        rejected[0].content_digest
        == hashlib.sha256(fork_line.encode("utf-8")).hexdigest()
    )


def test_replay_quarantines_a_duplicate_inline_operation(tmp_path) -> None:
    """Two intent ids cannot admit one inline operation twice."""
    first_intent = event("effect.intent", intent_data(manifest()))
    duplicate_manifest = EffectManifest.from_record(
        {**manifest().to_record(), "work_item_id": "work-2"}
    )
    duplicate_data = intent_data(duplicate_manifest)
    duplicate_data["intent_id"] = "intent-2"
    duplicate_intent = event("effect.intent", duplicate_data)
    path = tmp_path / "2026-08-23.jsonl"
    path.write_text(
        "\n".join(
            canonical(item)
            for item in (
                first_intent,
                event(
                    "effect.receipt",
                    receipt_data(receipt_id="receipt-final", status="failed"),
                ),
                duplicate_intent,
            )
        )
        + "\n",
        encoding="utf-8",
    )

    accepted, rejected = events_transactions.read_all(tmp_path)

    assert [item.kind for item in accepted] == ["effect.intent", "effect.receipt"]
    assert [(item.event_kind, item.line) for item in rejected] == [("effect.intent", 3)]
    assert "duplicate operation_id" in rejected[0].reason

    append_path = tmp_path / "append" / f"{datetime.now(timezone.utc).date()}.jsonl"
    append(append_path, first_intent)
    with pytest.raises(EventError, match="duplicate operation_id"):
        append(append_path, duplicate_intent)


def test_reference_intent_shape_is_valid_but_chain_is_refused(tmp_path) -> None:
    """A reference manifest passes validation and still cannot prove operation identity."""
    reference_data = intent_data(manifest())
    reference_data["manifest"] = {
        "kind": "reference",
        "reference": broker_reference("manifest"),
        "digest": manifest().digest,
    }
    reference_intent = event("effect.intent", reference_data)
    validate(reference_intent)
    path = tmp_path / "2026-08-23.jsonl"
    path.write_text(canonical(reference_intent) + "\n", encoding="utf-8")

    accepted, rejected = events_transactions.read_all(tmp_path)

    assert accepted == []
    assert [(item.event_kind, item.line) for item in rejected] == [("effect.intent", 1)]
    assert (
        "operation identity cannot be proved from reference manifest"
        in rejected[0].reason
    )

    append_path = tmp_path / "append" / f"{datetime.now(timezone.utc).date()}.jsonl"
    with pytest.raises(
        EventError, match="operation identity cannot be proved from reference manifest"
    ):
        append(append_path, reference_intent)

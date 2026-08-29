"""The canonical form of an effect manifest, and what it refuses before anything is
appended.

Nothing in this module touches a log. Each case builds a record, hands it to
`EffectManifest.from_record`, and asserts either the digest that comes out or the
refusal that should have. Two rules share the file because they are two rules about the
same function: the effect classes are an exact, order-independent set whose digest must
move when a class is truncated, and an outbound `message.send` manifest must carry a
disclosure digest that survives into `canonical()`. The disclosure cases insist on a
hash of pre-rendered bytes rather than prompt-shaped text, because a prompt can be
stripped by injection and a digest cannot; the operation label is not what triggers the
requirement, so `send_push` is refused alongside `send_email` and `send_sms`.

Two findings recorded in the original prose are kept here because they are the evidence.
A01's review found the composite-manifest check passing regardless of truncation: the
only existing composite check compared digests of reversed class order, and those stay
equal after both sides are truncated or after both drop the field the same way, so
`test_a_composite_manifest_retains_every_applicable_effect_class` is the replacement
that fails. And NaN and both infinities survive canonical JSON while changing its
digest, which is why they are refused while an arbitrarily large integer is not."""

from math import inf, nan
import pytest
from consilient.effects import (
    EFFECT_CLASSES,
    OUTBOUND_EFFECTS,
    EffectError,
    EffectManifest,
)
from effect_contract_helpers import (
    commitment,
    manifest,
)

_MISSING = object()

DISCLOSURE_DIGEST = "9" * 64


def outbound_record(
    *,
    operation: str = "send_email",
    disclosure: object = _MISSING,
    **overrides: object,
) -> dict[str, object]:
    record = manifest().to_record()
    record["effects"] = ["message.send"]
    record["operations"] = [operation]
    if disclosure is not _MISSING:
        record["disclosure"] = disclosure
    record.update(overrides)
    return record


def test_effect_classes_are_exact_and_manifest_digest_is_set_canonical() -> None:
    """Production break caught: a padded/case-varied effect could enter the manifest.

    Production break caught: malformed classes or their order change a composite manifest.
    """
    assert EFFECT_CLASSES == frozenset(
        {
            "file.change",
            "data.read",
            "process.run",
            "system.change",
            "network.call",
            "external.change",
            "message.send",
            "content.publish",
            "money.commit",
            "obligation.commit",
            "authority.change",
            "physical.actuate",
        }
    )
    composite = manifest().to_record()
    composite["effects"] = ["data.read", "network.call"]
    composite["operations"] = ["inspect", "read"]
    composite["declared_residuals"] = ["elapsed_time", "logs"]
    reversed_composite = {
        **composite,
        "effects": ["network.call", "data.read"],
        "operations": ["read", "inspect"],
        "declared_residuals": ["logs", "elapsed_time"],
    }
    assert (
        EffectManifest.from_record(composite).digest
        == EffectManifest.from_record(reversed_composite).digest
    )

    for malformed in (
        [],
        ["Data.Read"],
        [" data.read"],
        ["unknown.effect"],
        ["data.read", "data.read"],
        [1],
    ):
        with pytest.raises(EffectError, match="effect|empty|duplicate"):
            EffectManifest.from_record({**manifest().to_record(), "effects": malformed})
    missing = manifest().to_record()
    del missing["effects"]
    with pytest.raises(EffectError, match="missing"):
        EffectManifest.from_record(missing)


def test_a_composite_manifest_retains_every_applicable_effect_class() -> None:
    """A01's review found this failing: truncating a composite manifest's `effects` --
    or dropping `effects` from `canonical()` entirely -- left `python -m pytest
    tests/test_effect_contract.py -q` passing regardless, because the only existing
    composite check compares digests of reversed class order, which stay equal after both
    sides are truncated or after both drop the field the same way."""
    two_classes = EffectManifest.from_record(
        {**manifest().to_record(), "effects": ["data.read", "network.call"]}
    )
    two_classes_effects = two_classes.to_record()["effects"]
    assert isinstance(two_classes_effects, (list, tuple))
    assert set(two_classes_effects) == {"data.read", "network.call"}

    one_class = EffectManifest.from_record(
        {**manifest().to_record(), "effects": ["data.read"]}
    )
    assert two_classes.digest != one_class.digest, (
        "truncating a composite manifest's effect classes -- or dropping 'effects' from "
        "canonical() entirely, which would erase this same difference -- must change its digest"
    )


def test_manifest_rejects_non_finite_ceilings() -> None:
    """Production break caught: NaN/Infinity survives canonical JSON and changes its digest."""
    for ceiling in (nan, inf, -inf):
        value = manifest().to_record()
        value["ceilings"] = {"wall_time_s": ceiling}
        with pytest.raises(EffectError, match="finite"):
            EffectManifest.from_record(value)
    value = manifest().to_record()
    value["ceilings"] = {"wall_time_s": 10**1000}
    assert EffectManifest.from_record(value).to_record()["ceilings"] == {
        "wall_time_s": 10**1000
    }


def test_manifest_rejects_raw_private_values_and_credentials() -> None:
    """Production break caught: caller labels permit secrets or an unkeyed shared commitment."""
    raw = manifest().to_record()
    raw["forward"] = {"credential": "hunter2"}
    with pytest.raises(EffectError, match="broker reference|commitment"):
        EffectManifest.from_record(raw)
    opaque = manifest().to_record()
    opaque["scope"] = {"kind": "broker_reference", "reference": "hunter2"}
    with pytest.raises(EffectError, match="opaque"):
        EffectManifest.from_record(opaque)
    unkeyed = manifest().to_record()
    # Built before it is stored, because `to_record()` returns dict[str, object] and indexing
    # back into a slot of it is `object[...]`, which mypy --strict refuses. This was A01's
    # remaining conflict on 29 August 2026; the assertion is unchanged.
    unkeyed_forward = commitment("effect.manifest.forward")
    unkeyed_forward["algorithm"] = "sha256"
    unkeyed["forward"] = unkeyed_forward
    with pytest.raises(EffectError, match="hmac-sha256"):
        EffectManifest.from_record(unkeyed)
    shared_domain = manifest().to_record()
    shared_domain["start_state"] = commitment("effect.manifest.forward")
    with pytest.raises(EffectError, match="domain"):
        EffectManifest.from_record(shared_domain)


def test_outbound_effects_are_exactly_message_send() -> None:
    """Production break caught: an outbound class drops off the disclosure requirement."""
    assert OUTBOUND_EFFECTS == frozenset({"message.send"})
    assert OUTBOUND_EFFECTS <= EFFECT_CLASSES


@pytest.mark.parametrize("operation", ["send_email", "send_sms"])
def test_outbound_effect_refuses_missing_disclosure(operation: str) -> None:
    """Production break caught: send_email/send_sms can ship with no disclosure hash."""
    with pytest.raises(EffectError, match="disclosure"):
        EffectManifest.from_record(outbound_record(operation=operation))


def test_outbound_effect_refuses_missing_disclosure_for_any_operation_label() -> None:
    """Production break caught: another operation label must not bypass message.send disclosure."""
    with pytest.raises(EffectError, match="disclosure"):
        EffectManifest.from_record(outbound_record(operation="send_push"))


@pytest.mark.parametrize(
    "disclosure",
    [
        "",
        "This call is from an automated system.",
        "G" * 64,
        {"kind": "prompt", "text": "I am an AI"},
    ],
)
def test_outbound_effect_refuses_plaintext_or_malformed_disclosure(
    disclosure: object,
) -> None:
    """Production break caught: a prompt-shaped disclosure can be stripped by injection."""
    with pytest.raises(EffectError, match="disclosure"):
        EffectManifest.from_record(outbound_record(disclosure=disclosure))


def test_outbound_effect_accepts_pre_rendered_disclosure_digest() -> None:
    """A hash of pre-rendered bytes is the only admitted disclosure shape."""
    value = EffectManifest.from_record(outbound_record(disclosure=DISCLOSURE_DIGEST))
    assert value.disclosure == DISCLOSURE_DIGEST
    replayed = EffectManifest.from_record(value.to_record())
    assert replayed.disclosure == DISCLOSURE_DIGEST
    assert replayed.digest == value.digest


def test_non_outbound_manifest_does_not_require_disclosure() -> None:
    """Read-only work is not an outbound effect; disclosure stays optional."""
    value = manifest()
    assert value.disclosure is None
    assert "disclosure" not in value.to_record()


def test_non_outbound_manifest_refuses_a_disclosure_field() -> None:
    """Production break caught: a read-only manifest can carry a prompt-shaped disclosure."""
    record = manifest().to_record()
    record["disclosure"] = DISCLOSURE_DIGEST
    with pytest.raises(EffectError, match="disclosure"):
        EffectManifest.from_record(record)


def test_composite_outbound_effect_still_requires_disclosure() -> None:
    """Production break caught: mixing message.send with a read class drops the requirement."""
    with pytest.raises(EffectError, match="disclosure"):
        EffectManifest.from_record(
            outbound_record(effects=["message.send", "data.read"])
        )


def test_outbound_disclosure_changes_the_canonical_digest() -> None:
    """Production break caught: dropping disclosure from canonical() hides what was played."""
    first = EffectManifest.from_record(outbound_record(disclosure=DISCLOSURE_DIGEST))
    second = EffectManifest.from_record(outbound_record(disclosure="8" * 64))
    assert first.digest != second.digest
    assert "disclosure" in first.canonical()

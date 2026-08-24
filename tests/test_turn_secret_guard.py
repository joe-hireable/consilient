"""The conversation.turn secret guard, which had no test and was therefore backwards.

MEASURED 24 August 2026. `_check_turn_contract` refused a secret hash only when the turn
DECLARED redactions, and stayed silent when it declared none -- so a credential in a turn with
an empty redactions array was accepted and fsync'd into an append-only log that cannot
afterwards be erased. The dangerous case was the one that passed.

No test named the guard. That is not incidental: an untested guard is a guard whose deletion
nobody notices, and this one had been inverted rather than deleted, which is harder to see.
These tests exist so the inversion cannot return silently.
"""

from __future__ import annotations

import pytest

from consilient import work_items
from consilient.events import EventError

_BROKER = [{"kind": "broker_reference", "reference": "broker://secrets/1"}]
_DIGEST = "a" * 64


def _turn(text: str, redactions: list[dict[str, str]] | None = None) -> dict[str, object]:
    data: dict[str, object] = {
        "conversation_id": "c1",
        "turn_id": "t1",
        "root_request_turn_id": "t1",
        "role": "user",
        "text": text,
        "transport": {"authenticated": True, "channel": "cli"},
    }
    if redactions is not None:
        data["redactions"] = redactions
    return data


def test_a_digest_is_refused_when_the_turn_declares_no_redactions() -> None:
    """The regression. This is the case that was accepted, and it is the dangerous one.

    A turn claiming no redactions is claiming it carries nothing secret. A 64-hex digest in it
    is therefore either a leak or a lie, and both are refusals.
    """
    with pytest.raises(EventError, match="secret hashes"):
        work_items._check_turn_contract(_turn(f"token {_DIGEST}"))


def test_a_digest_is_refused_when_the_turn_declares_redactions() -> None:
    with pytest.raises(EventError, match="secret hashes"):
        work_items._check_turn_contract(_turn(f"token {_DIGEST}", _BROKER))


def test_the_original_marker_rule_still_refuses_what_it_always_refused() -> None:
    """Sharpening the discriminator must not drop a refusal the old rule made."""
    with pytest.raises(EventError, match="secret hashes"):
        work_items._check_turn_contract(_turn("we hash with sha256", _BROKER))


def test_discussing_hashing_is_not_a_leak() -> None:
    """Why the guard cannot simply drop its conjunction.

    The marker test matches the STRING "sha256" anywhere in the serialised turn, so refusing on
    it alone would refuse any turn merely discussing hashing -- which is what made the original
    rule noisy, and suppressing that noise is what silenced it. Ordinary talk stays admissible;
    an actual digest does not.
    """
    work_items._check_turn_contract(_turn("we hash with sha256"))


def test_ordinary_prose_is_admitted() -> None:
    work_items._check_turn_contract(_turn("hello there"))


def test_a_digest_embedded_in_a_longer_hex_run_is_not_matched() -> None:
    """The pattern is delimited, so a longer hex blob is not sliced into a false positive."""
    work_items._check_turn_contract(_turn("f" * 80))

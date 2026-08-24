"""Z01 — the selection receipt records a digest, not the whole omission list.

MEASURED 24 August 2026. `.harness/log/` grew 21,137 -> 166,465 -> 792,359 -> 1,069,904 ->
5,865,602 -> 40,771,519 bytes across six days because `_selection_receipt` inlined every
omission into each `instructions.assembled` event. The omission list grows with the log, so
each event is larger than the last, so the log grows faster -- a compounding loop.

One sampled event was 85,442 B of which `data.recall.omitted` was 84,603 B (99%, 454 entries)
while `selected_event_ids` was empty. Dozens of dispatchers then collided on byte-range locks
over a 40 MB file, and `could not be read after 6 attempts: observed access denial` became the
commonest crash signature in driver state, with single units dying that way 77 and 78 times.

The audit property that must survive: a replay producing a DIFFERENT omission set must produce
a different receipt. That is what these tests pin, along with the size and the fold-forward for
events already written in the old shape.
"""

from __future__ import annotations

import json

import pytest

from consilient import instructions


class _Omission:
    """The shape `_selection_receipt` reads off a recall.Selection."""

    def __init__(
        self, event_id: str, event_kind: str, reason: str, protected: bool
    ) -> None:
        self.event_id = event_id
        self.event_kind = event_kind
        self.reason = reason
        self.protected = protected


class _Selection:
    def __init__(self, omissions: list[_Omission]) -> None:
        self.selected_event_ids: tuple[str, ...] = ()
        self.selected_digest = "digest-of-selection"
        self.omissions = omissions
        self.context_complete = False
        self.continuation_event_id = None


def _selection(count: int, *, reason: str = "budget") -> _Selection:
    return _Selection(
        [
            _Omission(f"evt-{index:04d}", "conversation.turn", reason, False)
            for index in range(count)
        ]
    )


def test_the_receipt_no_longer_carries_the_omission_list() -> None:
    receipt = instructions._selection_receipt(_selection(454))
    assert "omitted" not in receipt, (
        "the full omission list is back in the receipt; that is the compounding loop that "
        "took the trajectory to 40 MB"
    )
    assert receipt["omitted_count"] == 454
    assert isinstance(receipt["omitted_digest"], str)
    assert receipt["omitted_digest"]


def test_a_receipt_that_used_to_be_110kb_is_now_tiny() -> None:
    """The measured event was 85,442 B with 454 omissions. Hold it well under 8 KB."""
    receipt = instructions._selection_receipt(_selection(454))
    size = len(json.dumps(receipt).encode("utf-8"))
    assert size < 8192, (
        f"receipt is {size} B; the point of this unit was to make it small"
    )


def test_a_different_omission_set_still_produces_a_different_receipt() -> None:
    """The audit property. A digest is only acceptable if it still discriminates."""
    base = instructions._selection_receipt(_selection(10))
    more = instructions._selection_receipt(_selection(11))
    other_reason = instructions._selection_receipt(_selection(10, reason="privileged"))

    assert base != more, "a different omission COUNT must change the receipt"
    assert base != other_reason, "a different omission REASON must change the receipt"
    assert base["omitted_digest"] != other_reason["omitted_digest"]


def test_the_same_omission_set_produces_the_same_receipt() -> None:
    """Replay determinism: the digest must not depend on anything but the omissions."""
    assert instructions._selection_receipt(
        _selection(37)
    ) == instructions._selection_receipt(_selection(37))


def test_an_event_recorded_in_the_old_fat_shape_still_verifies() -> None:
    """Back-compatibility. Events already in the trajectory carry the full list."""
    selection = _selection(12)
    fresh = instructions._selection_receipt(selection)

    legacy_record = {
        "selected_event_ids": [],
        "selected_digest": "digest-of-selection",
        "omitted": [
            {
                "event_id": omission.event_id,
                "event_kind": omission.event_kind,
                "reason": omission.reason,
                "protected": omission.protected,
            }
            for omission in selection.omissions
        ],
        "context_complete": False,
        "continuation": None,
    }
    folded = instructions._recorded_selection_receipt(legacy_record)
    assert folded == fresh, (
        "an event recorded before this change no longer verifies; the fold-forward must "
        "digest the list it stored"
    )


def test_an_old_record_with_a_tampered_omission_list_does_not_verify() -> None:
    """The fold-forward must not become a way to pass verification with anything."""
    selection = _selection(12)
    fresh = instructions._selection_receipt(selection)
    tampered = {
        "selected_event_ids": [],
        "selected_digest": "digest-of-selection",
        "omitted": [
            {
                "event_id": "evt-9999",
                "event_kind": "conversation.turn",
                "reason": "budget",
                "protected": False,
            }
        ],
        "context_complete": False,
        "continuation": None,
    }
    assert instructions._recorded_selection_receipt(tampered) != fresh


def test_a_record_in_the_new_shape_verifies_directly() -> None:
    fresh = instructions._selection_receipt(_selection(5))
    assert instructions._recorded_selection_receipt(dict(fresh)) == fresh


def test_key_order_in_a_legacy_row_cannot_change_the_digest() -> None:
    """`canonical` sorts, and the fold-forward must rely on that rather than on row order."""
    rows_a = [
        {"event_id": "e1", "event_kind": "k", "reason": "budget", "protected": False}
    ]
    rows_b = [
        {"protected": False, "reason": "budget", "event_kind": "k", "event_id": "e1"}
    ]
    assert instructions._omitted_digest(rows_a) == instructions._omitted_digest(rows_b)


def test_an_empty_omission_set_is_distinguishable_from_a_missing_one() -> None:
    receipt = instructions._selection_receipt(_selection(0))
    assert receipt["omitted_count"] == 0
    assert isinstance(receipt["omitted_digest"], str) and receipt["omitted_digest"]
    assert (
        receipt["omitted_digest"]
        != instructions._selection_receipt(_selection(1))["omitted_digest"]
    )


@pytest.mark.parametrize("count", [0, 1, 454, 2000])
def test_receipt_size_does_not_grow_with_the_omission_count(count: int) -> None:
    """The whole defect was that it did. Size must be flat in the number of omissions."""
    receipt = instructions._selection_receipt(_selection(count))
    size = len(json.dumps(receipt).encode("utf-8"))
    assert size < 512, f"{count} omissions produced a {size} B receipt; it must be flat"

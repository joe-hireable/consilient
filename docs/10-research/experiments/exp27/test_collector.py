"""Checks for the EXP-27 longitudinal collector.

The collector is allowed to notice that a vendor changed something. It is never allowed to
touch resource state — only an authenticated account read may credit headroom. That is
ADR-0029's whole point, and these tests exist so it is enforced rather than promised.

Run: python -m pytest docs/10-research/experiments/exp27/test_collector.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import collector as C  # noqa: E402
from change_record import validate_change_record  # noqa: E402


def test_every_emitted_record_declares_no_headroom_mutation():
    """The invariant the collector asserts on every record it writes."""
    record = {
        "harness": "claude-code",
        "effect": {
            "actions": ["invalidate_cached_capability"],
            "headroom_mutation_permitted": False,
        },
    }
    assert validate_change_record(record) is True


@pytest.mark.parametrize(
    "action",
    ["increase_headroom", "decrease_used", "move_reset", "mark_headroom_usable"],
)
def test_a_change_feed_may_never_credit_resource_state(action):
    """A vendor saying 'limits increased' must not move the ledger.

    This is the stopping rule EXP-27 registered: any change event that increases headroom,
    changes reset state or admits unknown resource state stops the run and makes the monitor
    notification-only.
    """
    with pytest.raises(ValueError, match="cannot mutate resource state"):
        validate_change_record(
            {"effect": {"actions": [action], "headroom_mutation_permitted": False}}
        )


def test_silence_about_headroom_is_not_permission():
    """Omitting the flag must fail, not default to allowed."""
    with pytest.raises(ValueError, match="explicitly false"):
        validate_change_record(
            {"effect": {"actions": ["invalidate_cached_capability"]}}
        )


def test_status_incidents_are_keyed_by_upstream_id():
    body = json.dumps(
        {
            "incidents": [
                {
                    "id": "abc123",
                    "name": "Elevated errors",
                    "status": "investigating",
                    "updated_at": "2026-08-20T09:00:00Z",
                }
            ],
            "scheduled_maintenances": [],
        }
    ).encode("utf-8")
    events = C.extract_events({"harness": "codex", "kind": "status"}, body)
    assert len(events) == 1 and events[0]["upstream_id"] == "abc123"


def test_atom_entries_are_frozen_by_id_and_content_hash():
    body = (
        b"<feed><entry><id>tag:v1.2.3</id><title>Release 1.2.3</title></entry>"
        b"<entry><id>tag:v1.2.4</id><title>Release 1.2.4</title></entry></feed>"
    )
    events = C.extract_events({"harness": "codex", "kind": "release"}, body)
    assert [e["upstream_id"] for e in events] == ["tag:v1.2.3", "tag:v1.2.4"]
    assert all(e["content_sha256"] for e in events)


def test_an_unparseable_document_still_yields_a_detectable_change():
    """Cursor's changelog is HTML with no feed. A whole-page hash still detects change.

    Silence here would be the dangerous outcome: a source that cannot be parsed would look
    identical to a source that never changes.
    """
    one = C.extract_events(
        {"harness": "cursor", "kind": "release-html"}, b"<html>a</html>"
    )
    two = C.extract_events(
        {"harness": "cursor", "kind": "release-html"}, b"<html>b</html>"
    )
    assert len(one) == 1 and one[0]["upstream_id"] is None
    assert one[0]["content_sha256"] != two[0]["content_sha256"]


def test_event_keys_are_stable_and_distinguish_sources():
    src_a = {"harness": "codex", "kind": "release"}
    src_b = {"harness": "cursor", "kind": "release"}
    ev = {"upstream_id": "tag:v1"}
    assert C.event_key(src_a, ev) == C.event_key(src_a, dict(ev))
    assert C.event_key(src_a, ev) != C.event_key(src_b, ev)


def test_a_source_that_fails_is_an_observation_not_a_crash():
    """A dead endpoint must be recorded, not raised. Thirty days cannot survive an exception."""
    result = C.fetch(
        {"url": "http://127.0.0.1:9/nothing", "harness": "x", "kind": "status"}, {}
    )
    assert result["status"] is None and result["error"]

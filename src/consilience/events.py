"""Authoritative trajectory events.

The append-only JSONL log is the record; everything else is a projection of it (ADR-0006).

Invariants enforced here, each with a test in the same commit:
  V0-01  every event is schema-versioned and append-only.
  V0-18  a human decision is valid only when the human principal authored it.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

SCHEMA_VERSION = 1

REQUIRED = ("v", "ts", "event", "actor", "data")

# RFC3339 with an explicit offset or Z. A naive timestamp is rejected: replay across machines
# must not depend on the reader's timezone.
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")

# Decisions that only a human principal may author (V0-18). Recording one under an agent
# actor is the failure EXP-16 measured: a fabricated human-participation claim.
HUMAN_ONLY = frozenset(
    {
        "approval",
        "gate_lift",
        "spend_authorisation",
        "verdict",
    }
)


class EventError(ValueError):
    """An event was rejected before it reached the log."""


@dataclass(frozen=True)
class Event:
    raw: dict

    @property
    def kind(self) -> str:
        return self.raw["event"]

    @property
    def actor(self) -> str:
        return self.raw["actor"]

    @property
    def data(self) -> dict:
        return self.raw["data"]


def validate(event: dict) -> dict:
    """Reject anything that must never reach the log. Returns the event unchanged."""
    if not isinstance(event, dict):
        raise EventError("event must be an object")

    missing = [k for k in REQUIRED if k not in event]
    if missing:
        raise EventError(f"missing required field(s): {', '.join(missing)}")

    if event["v"] != SCHEMA_VERSION:
        raise EventError(
            f"unsupported schema version {event['v']!r}; this build writes v{SCHEMA_VERSION}"
        )

    if not isinstance(event["ts"], str) or not TS.match(event["ts"]):
        raise EventError(
            f"ts must be RFC3339 with an explicit offset, got {event['ts']!r}"
        )

    for field in ("event", "actor"):
        if not isinstance(event[field], str) or not event[field].strip():
            raise EventError(f"{field} must be a non-empty string")

    if not isinstance(event["data"], dict):
        raise EventError("data must be an object")

    _check_human_authority(event)
    return event


def _check_human_authority(event: dict) -> None:
    """V0-18: an agent may never author a human's decision.

    `principal` names whose authority is being exercised. It is not itself an authority
    grant, so it can never convert an agent-authored event into the human's decision.
    """
    decision = event["data"].get("human_decision")
    verdict = event["data"].get("human_verdict")

    # A human verdict IS a human decision, and until 20 Aug 2026 it was the way round this
    # check. `_check_human_authority` returned early whenever `human_decision` was absent,
    # while `projection._apply_outcome` read `human_verdict` straight off an
    # `attempt.outcome` event and wrote it to the table beta is computed from. So an agent
    # could author the human verdict that beta is measured against, and V0-18 — the
    # invariant that exists to prevent exactly that — never fired. Found by Cursor
    # (Gemini 3.7 Flash) auditing code Claude wrote; a second path to a guarded state is
    # the `jobboard-v2` failure this project was founded on.
    if verdict is not None:
        if verdict not in ("accept", "reject"):
            raise EventError(
                f"human_verdict must be 'accept' or 'reject', got {verdict!r}"
            )
        if decision is None:
            decision = "verdict"
        elif decision != "verdict":
            raise EventError(
                f"event carries a human_verdict but declares human_decision {decision!r}; "
                "a human verdict is a verdict and may not be filed as anything else (V0-18)"
            )

    if decision is None:
        return
    if decision not in HUMAN_ONLY:
        raise EventError(
            f"unknown human_decision {decision!r}; expected one of {sorted(HUMAN_ONLY)}"
        )

    principal = event["data"].get("principal")
    if principal is None:
        raise EventError("a human_decision event must name its principal")
    if event["actor"] != principal:
        raise EventError(
            f"human_decision {decision!r} is attributed to principal {principal!r} but was "
            f"authored by {event['actor']!r}; only the principal may author their own "
            f"decision (V0-18)"
        )
    if not event["data"].get("via"):
        raise EventError(
            f"human_decision {decision!r} must record `via`, the channel it arrived through"
        )


def canonical(event: dict) -> str:
    """One event, one line, stable key order so a replay hash is reproducible."""
    return json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def append(path: Path, event: dict) -> dict:
    """Validate and append. The only writer of the log."""
    validate(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(canonical(event) + "\n")
    return event


def read(path: Path) -> list[Event]:
    """Every valid event in file order. A malformed line is an error, never a skip."""
    if not path.exists():
        return []
    events = []
    with path.open(encoding="utf-8") as fh:
        for number, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EventError(f"{path}:{number} is not valid JSON: {exc}") from exc
            try:
                validate(raw)
            except EventError as exc:
                raise EventError(f"{path}:{number} {exc}") from exc
            events.append(Event(raw))
    return events


def read_all(directory: Path) -> list[Event]:
    """Every event across every daily file, ordered by filename then position."""
    events: list[Event] = []
    for path in sorted(directory.glob("*.jsonl")):
        events.extend(read(path))
    return events


def prefix_digest(path: Path, count: int) -> str:
    """Digest of the first `count` lines — the append-only check.

    Appending must never change an earlier position. A test asserts the digest of the
    committed prefix survives an append and that an in-place edit is detected.
    """
    lines = []
    with path.open(encoding="utf-8") as fh:
        for number, line in enumerate(fh):
            if number >= count:
                break
            lines.append(line.rstrip("\n"))
    if len(lines) < count:
        raise EventError(
            f"{path} has {len(lines)} lines, cannot digest a prefix of {count}"
        )
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()

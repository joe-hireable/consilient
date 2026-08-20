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
from datetime import datetime, timezone
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
class Rejection:
    """A line the reader refused, kept so refusal is reported rather than fatal.

    The log is append-only, so a line that should never have been written cannot be
    removed. If the reader raises on it, one bad append destroys the readability of the
    whole record — the instrument's failure mode becomes "stop working" instead of "report
    the problem", and every downstream number disappears with it.

    This project had already worked that out and then walked into it anyway.
    `test_reading_a_historical_log_does_not_depend_on_when_it_is_read` says in as many
    words that if `validate` enforced clock skew "every log would become unreadable as it
    aged". The reasoning was applied to one rule and never generalised into a property of
    the reader, so when V0-18 was tightened at 03:52 on 20 August 2026 and three events
    were appended at 09:41-09:56 that it forbids, `replay` and `beta` both died on the
    real trajectory. [measured]

    A rejection is never silently dropped: it is excluded from the projection AND carried
    back to the caller, and every CLI command reports the count.
    """

    path: str
    line: int
    reason: str


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


MAX_CLOCK_SKEW_S = 15 * 60


def _check_clock(event: dict) -> None:
    """An appended event must be stamped from a clock, not from an author's belief.

    Added 20 Aug 2026 after the orchestrator wrote six consecutive trajectory events with
    invented timestamps, drifting to 2h15m ahead of the wall clock, while documenting
    instrument-integrity defects in other people's work. Nothing caught it: `validate`
    checked the *format* of `ts` and its offset, which were impeccable, and never asked
    whether the value was true.

    A format check on a timestamp is not a check on a timestamp.

    This runs at append only, never in `validate`, because reading a historical log must
    not depend on when it is read — which is the same reason `ts` requires an explicit
    offset in the first place.
    """
    stamped = datetime.fromisoformat(event["ts"])
    skew = abs((datetime.now(timezone.utc) - stamped).total_seconds())
    if skew > MAX_CLOCK_SKEW_S:
        raise EventError(
            f"event ts {event['ts']} is {skew / 60:.0f} minutes from the current clock, "
            f"beyond the {MAX_CLOCK_SKEW_S // 60}-minute tolerance. Stamp events from the "
            "clock rather than writing the time you believe it to be. To record something "
            "that happened earlier, put the occurrence time in `data` and let `ts` record "
            "when it was written."
        )


def append(path: Path, event: dict) -> dict:
    """Validate and append. The only writer of the log."""
    validate(event)
    _check_clock(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(canonical(event) + "\n")
    return event


def read(path: Path) -> tuple[list[Event], list[Rejection]]:
    """Every valid event in file order, and every line that was refused.

    A refused line is never silently skipped — it comes back in the second element, and
    the caller must decide what to say about it. The two-tuple is deliberate: it makes the
    quarantine impossible to ignore by accident, which a logged warning would not.
    """
    if not path.exists():
        return [], []
    events: list[Event] = []
    rejected: list[Rejection] = []
    with path.open(encoding="utf-8") as fh:
        for number, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                rejected.append(Rejection(str(path), number, f"not valid JSON: {exc}"))
                continue
            try:
                validate(raw)
            except EventError as exc:
                rejected.append(Rejection(str(path), number, str(exc)))
                continue
            events.append(Event(raw))
    return events, rejected


def read_all(directory: Path) -> tuple[list[Event], list[Rejection]]:
    """Every event across every daily file, ordered by filename then position."""
    events: list[Event] = []
    rejected: list[Rejection] = []
    for path in sorted(directory.glob("*.jsonl")):
        file_events, file_rejected = read(path)
        events.extend(file_events)
        rejected.extend(file_rejected)
    return events, rejected


def bypassed(directory: Path) -> list[tuple[str, int]]:
    """Lines that did not come through `append()`.

    `append` is documented as the only writer and is the only place `validate` runs. On
    20 August 2026, 92 of the 93 events in the real trajectory — 98.9% — had been written
    straight to the file by something else, which is how three events V0-18 forbids came
    to be in an authoritative record whose sole writer rejects them. [measured]

    That is `AGENTS.md` working principle 3 reproduced inside the artefact the principle
    was written about: a documented single boundary fragments into several access paths
    because no check bans the bypass.

    ponytail: canonical form is a proxy, not a boundary. It catches hand-written JSON,
    which is the failure that actually happened; it would not catch a writer that
    formatted its output correctly. The upgrade path if that ever matters is a per-event
    digest of the previous line, which cannot be applied retroactively to history.
    """
    out: list[tuple[str, int]] = []
    for path in sorted(directory.glob("*.jsonl")):
        with path.open(encoding="utf-8") as fh:
            for number, line in enumerate(fh, start=1):
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                try:
                    if canonical(json.loads(line)) != line:
                        out.append((str(path), number))
                except json.JSONDecodeError:
                    out.append((str(path), number))
    return out


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

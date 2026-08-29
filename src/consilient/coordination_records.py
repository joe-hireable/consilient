"""The vocabulary a dispatch claim is written in: its record types, its constants, and
the pure reads over them.

Nothing here writes to the trajectory or reads a file from disk. `_normpath` and
`paths_overlap` are string grammar — overlap is equality or containment at a path
boundary, in either direction — and the normaliser is hand-written because the product
capability allowlist in `test_budget.py` does not grant this package the `os` import.
`_parse_ts` declines a stamp carrying no explicit offset rather than assuming UTC, so a
naive timestamp can never be compared as though it knew its own zone.

`native_readiness_refusal` is the largest thing here and it is a refusal function by
design. It returns the reason a native item may not be claimed — absent, superseded by a
newer revision, commitment-paused, pathless, its binding count out of step with its
frozen dependencies, or bound to a predecessor whose artefact and receipt digests are
not sealed in the trajectory — and `None` only once every one of those checks has
passed. Readiness is proved from the event prefix; it is never taken from the item's own
say-so.

`DISPATCH_ACTOR` restates `harness.DISPATCH_ACTOR` for that same allowlist reason, with
a test pinning the equality so the two cannot drift apart. The lease constants sit
beside it: `LEASE_TTL_S` is the 30 s session a live holder renews within, and
`CLAIM_GRACE_S` the historical additive bound an acquire falls back to when no explicit
lease is asked for. `_windows_process_still_running` completes the set — the process
query `os.kill(pid, 0)` cannot answer on Windows, returning `None` wherever the answer
is genuinely unknown rather than reporting a live process dead."""

from __future__ import annotations
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from . import work_items
from .events import (
    Event,
    EventError,
    EventPayload,
)

# Plan unit ids: F01, T01, T01B, AA, etc.
_PLAN_UNIT_ID = re.compile(r"\b([A-Z][A-Z0-9]*)\b")

_PLAN_UNIT_HEADING = re.compile(
    r"^## ([A-Z][A-Z0-9]*) [—-] (.*?)\n(.*?)(?=^## |\Z)", re.M | re.S
)

_LANE_TABLE_MARKER = "## Parallelism and claim lanes"

# Restates harness.DISPATCH_ACTOR: the product capability allowlist in
# test_budget.py forbids importing the registry module from product code, and a
# test pins the equality so the two cannot drift apart.
DISPATCH_ACTOR = "consilient.dispatch"

CLAIM_TICKET_PREFIX = "dispatch:"

# One Chubby-style session: short enough that a killed holder is reclaimable in the
# BU-3 fixture (≤30 s), long enough that a live process can renew before expiry.
# timeout_s on open_claim remains the run bound; it is not the claim bound.
LEASE_TTL_S = 30

# Historical additive: open_claim still uses timeout_s + CLAIM_GRACE_S when the
# caller does not pass lease_s. That default is what the commit-gate clock
# fixture pins. BU-3's 30 s lease is the lease_s=LEASE_TTL_S path; replacing
# the default needs tests/test_commit_gate.py, which this unit was not given.
CLAIM_GRACE_S = 300

# The in-flight table is context-window spend. It is bounded for the same reason the
# recall pack is bounded: an unbounded coordination section crowds out the task.
IN_FLIGHT_LIMIT_CHARS = 2000

_TERMINAL_DISPATCH_KINDS = frozenset(
    {"dispatch.outcome", "dispatch.refused", "dispatch.fanout"}
)


class StaleEpoch(ValueError):
    """A write whose fencing token is behind the live claim's epoch."""


@dataclass(frozen=True)
class Claim:
    """One live dispatch claim, projected from its `work_item.opened` event."""

    ticket: str
    run_id: str
    actor: str
    cwd: str
    paths: tuple[str, ...]
    harness: str | None
    opened_at: str
    expires_at: str
    # BU-3's fencing token. Defaults to 1 so a claim written before fencing
    # existed still projects as a live holder at the lowest epoch rather than
    # as an unfenced None; nothing may outrank it without a real acquire.
    fencing_epoch: int = 1


class ClaimReadyError(EventError):
    """Native work failed readiness, revision, predecessor or path admission."""


@dataclass(frozen=True)
class ExposureAdmission:
    """Whether a candidate may reach the frozen composite verifier.

    A refusal records no exposure: this object is the decision, not an event.
    """

    admitted: bool
    reason: str
    n_attempt_max: int | None
    recorded_exposure: bool = False


def _normpath(text: str) -> str:
    """os.path.normpath without the os import, which the product capability
    allowlist (test_budget.py) does not grant this package. Posix-style only:
    duplicate slashes and `.` collapse, `..` pops one component, a drive-letter
    root (`c:`) behaves like `/` — nothing pops past it.
    """
    rooted = text.startswith("/") or (len(text) >= 2 and text[1] == ":")
    parts: list[str] = []
    for part in text.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            drive_root = len(parts) == 1 and rooted and parts[0].endswith(":")
            if parts and parts[-1] != ".." and not drive_root:
                parts.pop()
            elif not rooted:
                parts.append(part)
            continue
        parts.append(part)
    if not parts:
        return "/" if text.startswith("/") else "."
    body = "/".join(parts)
    return "/" + body if text.startswith("/") else body


def paths_overlap(first: str, second: str) -> bool:
    """Overlap is equality or containment at a path boundary, either direction."""
    if first == second:
        return True
    return second.startswith(first + "/") or first.startswith(second + "/")


def _parse_ts(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        stamped = datetime.fromisoformat(value)
    except ValueError:
        return None
    if stamped.tzinfo is None or stamped.utcoffset() is None:
        return None
    return stamped.astimezone(timezone.utc)


def _is_dispatch_claim_payload(data: Mapping[str, object]) -> bool:
    return isinstance(data.get("run_id"), str) and isinstance(data.get("paths"), list)


@dataclass(frozen=True)
class ClaimRelease:
    """Outcome of one attempted claim release for a start_failed dispatch."""

    run_id: str
    released: bool
    reason: str


def _windows_process_still_running(pid: int) -> bool | None:
    """Query the Windows process status that ``os.kill(pid, 0)`` cannot report."""
    winapi = sys.modules.get("_winapi")
    if winapi is None:
        return None
    query_limited_information = 0x1000
    still_active = 259
    try:
        handle = int(winapi.OpenProcess(query_limited_information, False, pid))
    except OSError as exc:
        return False if exc.winerror == 87 else None
    if not handle:
        return None
    try:
        return int(winapi.GetExitCodeProcess(handle)) == still_active
    except OSError:
        return None
    finally:
        winapi.CloseHandle(handle)


def _native_items_from_prefix(
    prefix: Sequence[Event],
) -> dict[tuple[str, int], EventPayload]:
    items: dict[tuple[str, int], EventPayload] = {}
    for event in prefix:
        data = event.data
        if (
            event.kind != work_items.OPENED
            or data.get("item_schema") != work_items.NATIVE_SCHEMA
        ):
            continue
        ticket = data.get("ticket")
        revision = data.get("revision")
        if (
            isinstance(ticket, str)
            and isinstance(revision, int)
            and not isinstance(revision, bool)
        ):
            items[(ticket, revision)] = data
    return items


def _predecessor_sealed(
    prefix: Sequence[Event], ticket: str, revision: int
) -> dict[str, object] | None:
    sealed: dict[str, object] | None = None
    for event in prefix:
        data = event.data
        if event.kind != work_items.COMPLETED or data.get("ticket") != ticket:
            continue
        if data.get("revision") not in (None, revision):
            continue
        artefacts = data.get("artefacts")
        receipts = data.get("verifier_receipts")
        if not isinstance(artefacts, list) or not artefacts:
            continue
        if not isinstance(receipts, list) or not receipts:
            continue
        sealed = data
    return sealed


def native_readiness_refusal(
    prefix: Sequence[Event],
    *,
    ticket: str,
    revision: int,
    predecessor_bindings: Sequence[Mapping[str, object]],
    cwd: Path,
) -> str | None:
    """Why this native item cannot be claimed, or None when it is ready."""
    items = _native_items_from_prefix(prefix)
    item = items.get((ticket, revision))
    if item is None:
        return f"unready: native item {ticket!r} revision {revision} is absent"
    newer = [
        rev for (item_ticket, rev) in items if item_ticket == ticket and rev > revision
    ]
    if newer:
        return f"stale-revision: {ticket!r} revision {revision} is superseded by {max(newer)}"
    paused = any(
        event.kind == work_items.NATIVE_COMMITMENT_PAUSED
        and event.data.get("ticket") == ticket
        and event.data.get("revision") == revision
        for event in prefix
    )
    if paused:
        return f"unready: {ticket!r} revision {revision} is commitment_paused"
    owned = item.get("owned_paths")
    if not isinstance(owned, list) or not owned:
        return "pathless mutable item is not claimable"
    dependencies = item.get("dependencies")
    if not isinstance(dependencies, list):
        return "unready: native dependencies are unreadable"
    if len(predecessor_bindings) != len(dependencies):
        return (
            "predecessor-mismatched: binding count does not match frozen dependencies"
        )
    bindings_by_ticket = {
        str(binding.get("ticket")): binding for binding in predecessor_bindings
    }
    for dependency in dependencies:
        dep_ticket = str(dependency.get("ticket"))
        dep_revision = dependency.get("revision")
        binding = bindings_by_ticket.get(dep_ticket)
        if binding is None:
            return f"predecessor-mismatched: missing binding for {dep_ticket}"
        if binding.get("revision") != dep_revision:
            return f"predecessor-mismatched: revision for {dep_ticket} is not the frozen one"
        if binding.get("handoff_contract_digest") != dependency.get(
            "handoff_contract_digest"
        ):
            return f"predecessor-mismatched: hand-off digest for {dep_ticket} does not match"
        sealed = _predecessor_sealed(
            prefix,
            dep_ticket,
            int(dep_revision) if isinstance(dep_revision, int) else 0,
        )
        if sealed is None:
            return f"unready: predecessor {dep_ticket} is not evidence-closed"
        artefacts = sealed.get("artefacts")
        receipts = sealed.get("verifier_receipts")
        artefact_items = artefacts if isinstance(artefacts, list) else []
        receipt_items = receipts if isinstance(receipts, list) else []
        artefact_digests = [
            item.get("digest") for item in artefact_items if isinstance(item, Mapping)
        ]
        receipt_digests = [
            item.get("digest") for item in receipt_items if isinstance(item, Mapping)
        ]
        if binding.get("artefact_digest") not in artefact_digests:
            return f"predecessor-mismatched: artefact digest for {dep_ticket} is not sealed"
        if binding.get("receipt_digest") not in receipt_digests:
            return (
                f"predecessor-mismatched: receipt digest for {dep_ticket} is not sealed"
            )
    del cwd
    return None


@dataclass(frozen=True)
class PlanUnit:
    """One build-plan unit's declared claims and dependency edges."""

    unit_id: str
    title: str
    paths: tuple[str, ...]
    depends: tuple[str, ...]
    plan: str

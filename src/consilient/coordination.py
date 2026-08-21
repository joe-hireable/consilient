"""Dispatch claims: what each live run intends to touch, and refusal on overlap.

The trajectory is the only registry. A claim is a `work_item.opened` event whose ticket
is `dispatch:<run_id>`, written through the single `append()` writer like everything
else. It is released by any of three independent events, checked at read time:

1. `work_item.completed` on the same ticket (the dispatcher released it);
2. the run's own `dispatch.outcome` or `dispatch.refused` (the run ended, whatever the
   release path forgot to write);
3. its own `expires_at` passing — opened time plus the run timeout plus a grace margin.

The third is the one that matters: a crashed or SIGKILLed dispatcher cannot hold a claim
forever. The stale `.budget.lock` measured on this machine refuses forever after a
SIGKILL because it is a file; a claim is a projection over events with a clock, so the
passage of time alone releases it. No lock file exists to go stale.

A claim with no declared paths conflicts with nothing and protects nothing — it exists
so the run is visible in the work-item stream, not to exclude others. The refusal
invariant only covers declared paths; that limit is stated in the dispatch payload and
in the design report, not hidden.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import work_items
from .events import Event, EventPayload

# Restates harness.DISPATCH_ACTOR: the product capability allowlist in
# test_budget.py forbids importing the registry module from product code, and a
# test pins the equality so the two cannot drift apart.
DISPATCH_ACTOR = "consilient.dispatch"

CLAIM_TICKET_PREFIX = "dispatch:"
# Added to the run timeout to form the claim TTL. A run cannot legitimately outlive its
# timeout (the runner kills the process tree at the deadline), so anything beyond it is
# grace for the recording path, not for the work.
CLAIM_GRACE_S = 300
# The in-flight table is context-window spend. It is bounded for the same reason the
# recall pack is bounded: an unbounded coordination section crowds out the task.
IN_FLIGHT_LIMIT_CHARS = 2000

_TERMINAL_DISPATCH_KINDS = frozenset(
    {"dispatch.outcome", "dispatch.refused", "dispatch.fanout"}
)


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


def claim_ticket(run_id: str) -> str:
    return f"{CLAIM_TICKET_PREFIX}{run_id}"


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


def canonical_path(path: str, *, cwd: Path | None = None) -> str:
    """One spelling for one file, across this machine's Windows/WSL boundary.

    Claims are recorded by dispatchers running on both sides of that boundary, so
    `C:\\x\\y` and `/mnt/x/y` must compare equal or the same file claimed twice is not
    an overlap. Relative paths resolve against the dispatch cwd. This is string
    normalisation only; it never touches the filesystem.
    """
    text = path.strip().replace("\\", "/")
    if len(text) >= 3 and text[1] == ":" and text[2] == "/":
        text = text[0].lower() + text[1:]
    elif text.startswith("/mnt/") and len(text) > 6 and text[6] == "/":
        text = f"{text[5]}:{text[6:]}"
    if not (len(text) >= 2 and text[1] == ":") and not text.startswith("/"):
        base = cwd if cwd is not None else Path.cwd()
        text = str(base).replace("\\", "/").rstrip("/") + "/" + text
        if len(text) >= 3 and text[1] == ":" and text[2] == "/":
            text = text[0].lower() + text[1:]
    return _normpath(text).casefold()


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


def _claim_from_event(ticket: str, event: Event) -> Claim | None:
    """Project one claim event. A claim that does not parse is not live.

    Claims are written by one writer with validation, so a claim-shaped event without
    parseable fields is either hand-written or from another schema version; the
    projection declines both rather than guess at an expiry.
    """
    data = event.data
    run_id = data.get("run_id")
    expires_at = _parse_ts(data.get("expires_at"))
    opened_at = _parse_ts(data.get("opened_at"))
    paths_raw = data.get("paths")
    if (
        not isinstance(run_id, str)
        or not run_id.strip()
        or expires_at is None
        or opened_at is None
        or not isinstance(paths_raw, list)
        or not all(isinstance(item, str) for item in paths_raw)
    ):
        return None
    harness = data.get("harness")
    cwd = data.get("cwd")
    return Claim(
        ticket=ticket,
        run_id=run_id,
        actor=event.actor,
        cwd=cwd if isinstance(cwd, str) else "",
        paths=tuple(paths_raw),
        harness=harness if isinstance(harness, str) else None,
        opened_at=str(data["opened_at"]),
        expires_at=str(data["expires_at"]),
    )


def live_claims(events: Iterable[Event], *, now: datetime) -> tuple[Claim, ...]:
    """Claims still held at `now`, in the order they were opened.

    Liveness is decided entirely from the event stream: opened, not completed, the run
    has no terminal dispatch event, and the claim has not expired. A projection, so
    reading it writes nothing and cannot itself hold anything.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must carry an explicit offset")
    now_utc = now.astimezone(timezone.utc)
    opened: dict[str, Event] = {}
    released_tickets: set[str] = set()
    ended_runs: set[str] = set()
    for event in events:
        data = event.data
        if event.kind == work_items.OPENED:
            ticket = data.get("ticket")
            if isinstance(ticket, str) and ticket.startswith(CLAIM_TICKET_PREFIX):
                opened[ticket] = event
        elif event.kind == work_items.COMPLETED:
            ticket = data.get("ticket")
            if isinstance(ticket, str):
                released_tickets.add(ticket)
        elif event.kind in _TERMINAL_DISPATCH_KINDS:
            run_id = data.get("run_id")
            if isinstance(run_id, str):
                ended_runs.add(run_id)
    live: list[Claim] = []
    for ticket, event in opened.items():
        claim = _claim_from_event(ticket, event)
        if claim is None:
            continue
        if ticket in released_tickets or claim.run_id in ended_runs:
            continue
        expires = _parse_ts(claim.expires_at)
        if expires is None or expires <= now_utc:
            continue
        live.append(claim)
    return tuple(live)


def conflict(
    paths: Sequence[str], live: Sequence[Claim], *, cwd: Path
) -> tuple[Claim, str, str] | None:
    """The first live claim overlapping any requested path, with the offending pair.

    A dispatch that declares no paths conflicts with nothing: the refusal invariant
    covers declared surfaces only, and an undeclared dispatch says so in its payload
    rather than claiming protection it does not have.
    """
    for requested in paths:
        canonical_requested = canonical_path(requested, cwd=cwd)
        for claim in live:
            for held in claim.paths:
                if paths_overlap(canonical_requested, held):
                    return claim, canonical_requested, held
    return None


def open_claim(
    log: Path,
    *,
    run_id: str,
    paths: Sequence[str],
    cwd: Path,
    timeout_s: int,
    harness: str | None = None,
    task: str | None = None,
    now: datetime | None = None,
) -> EventPayload:
    """Record the claim through work_items, i.e. through the single append() writer."""
    opened = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires = opened + timedelta(seconds=timeout_s + CLAIM_GRACE_S)
    canonical = [canonical_path(path, cwd=cwd) for path in paths]
    extra: dict[str, object] = {
        "run_id": run_id,
        "paths": canonical,
        "cwd": str(cwd),
        "opened_at": opened.isoformat(),
        "expires_at": expires.isoformat(),
    }
    if harness is not None:
        extra["harness"] = harness
    return work_items.open_item(
        log,
        ticket=claim_ticket(run_id),
        accountable=DISPATCH_ACTOR,
        actor=DISPATCH_ACTOR,
        text=task[:500] if task else None,
        extra=extra,
    )


def close_claim(log: Path, *, run_id: str) -> EventPayload:
    """Release by completion. Expiry and the run's terminal event back this up."""
    return work_items.complete_item(
        log, ticket=claim_ticket(run_id), actor=DISPATCH_ACTOR
    )


def render_in_flight(
    live: Sequence[Claim], *, now: datetime, limit_chars: int = IN_FLIGHT_LIMIT_CHARS
) -> str:
    """The bounded in-flight table for a dispatch brief. Verbatim fields, no summary.

    The bound is the point: a coordination section that grows without limit crowds the
    task out of the context window, which is the failure the principal named. Rows are
    dropped from the render (never from the trajectory) with an omitted count.
    """
    if limit_chars < 1:
        raise ValueError("limit_chars must be at least 1")
    stamp = now.astimezone(timezone.utc).isoformat()
    if not live:
        return f"## In flight right now\n\nNo live dispatch claims at {stamp}.\n"
    header = f"## In flight right now\n\n{len(live)} live dispatch claim(s) at {stamp}:\n"
    rows = []
    for claim in live:
        paths = ", ".join(f"`{path}`" for path in claim.paths) or "(no paths declared)"
        harness = claim.harness or "unknown harness"
        rows.append(
            f"- `{claim.run_id}` ({claim.actor}, {harness}) claims {paths}; "
            f"opened {claim.opened_at}, claim expires {claim.expires_at}"
        )

    def build(included: list[str], omitted: int) -> str:
        text = header + "\n" + "\n".join(included) + "\n"
        if omitted:
            text += (
                f"\n_{omitted} further claim(s) omitted to fit the in-flight limit "
                f"of {limit_chars} characters._\n"
            )
        return text

    # The incremental check is exact: the candidate build counts the footer with the
    # omitted number this row would leave, which is precisely the omitted count if the
    # loop breaks next iteration. A trailing fix-up loop would be dead code — a mutant
    # removing it survived the suite, which is how this was found.
    included: list[str] = []
    for row in rows:
        remaining = len(rows) - len(included) - 1
        if len(build(included + [row], remaining)) <= limit_chars:
            included.append(row)
        else:
            break
    text = build(included, len(rows) - len(included))
    if len(text) > limit_chars:
        # The bound wins over the header itself at a pathological limit: no row was
        # ever checked for the empty inclusion, so the degenerate render is clamped.
        # The trailing-newline courtesy below would otherwise re-exceed the bound.
        text = build([], len(rows))[:limit_chars]
        if not text.endswith("\n"):
            text = text[:-1] + "\n"
        return text
    return text if text.endswith("\n") else text + "\n"

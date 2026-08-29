"""Reading the world into values: an event into a claim, a pid record into liveness,
plan markdown into units, and live claims back into one bounded table.

None of these functions writes an event. `_claim_from_event` declines a claim-shaped
event whose fields do not parse rather than guess at an expiry — claims are written by
one validating writer, so an unparseable one is either hand-written or from another
schema version, and a claim that does not project is not live.
`admit_composite_exposure` is a decision and not an event either: a refusal records no
exposure, and it refuses a proxy or mutation estimand, an unauthenticated row, a missing
projection, a scope that does not match the frozen composite-verifier contract, and any
candidate ordinal past the measured ceiling.

`canonical_path` gives one spelling to one file across this machine's Windows/WSL
boundary, by string normalisation alone; it never asks the filesystem what exists. Drive
and `/mnt` folding happen after a relative path is joined to its cwd rather than before,
so a WSL-side claim and a Windows-side claim on the same file compare equal — found by
tests/test_commit_gate.py, 21 August 2026. `parse_plan_units` and
`parse_build_plan_lanes` read the hand-maintained build-plan markdown, its unit
headings, its `**Claim exactly:**` path lists and its lane table, dropping any
dependency id no parsed unit defines so the corpus stays closed under its own
references.

Liveness is the fail-closed half. `worker_gone_from_pid_record` reads
`runs_dir/<run_id>/process.json` and answers `True` only when the recorded pid is
confirmed gone, `False` when it is still running, and `None` whenever the mapping or the
query cannot be completed. Artefact silence is not consulted: a slow worker and a dead
one look identical from outside, and only one of them may have its path handed to
somebody else. `render_in_flight` closes the file with the opposite discipline — a
bounded render, because a coordination section that grows without limit crowds the task
out of the context window, so rows are dropped from the render, never from the
trajectory, with an omitted count."""

from __future__ import annotations
import json
import os
import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from . import beta, routing
from .events import (
    Event,
)
from .coordination_records import (
    Claim,
    ExposureAdmission,
    IN_FLIGHT_LIMIT_CHARS,
    PlanUnit,
    _LANE_TABLE_MARKER,
    _PLAN_UNIT_HEADING,
    _PLAN_UNIT_ID,
    _normpath,
    _parse_ts,
    _windows_process_still_running,
)


__all__ = [
    "Claim",
    "ExposureAdmission",
    "IN_FLIGHT_LIMIT_CHARS",
    "PlanUnit",
    "_LANE_TABLE_MARKER",
    "_PLAN_UNIT_HEADING",
    "_PLAN_UNIT_ID",
    "_normpath",
    "_parse_ts",
    "_windows_process_still_running",
    "admit_composite_exposure",
    "canonical_path",
    "parse_build_plan_lanes",
    "parse_plan_units",
    "render_in_flight",
    "worker_gone_from_pid_record",
]


def canonical_path(path: str, *, cwd: Path | None = None) -> str:
    """One spelling for one file, across this machine's Windows/WSL boundary.

    Claims are recorded by dispatchers running on both sides of that boundary, so
    `C:\\x\\y` and `/mnt/x/y` must compare equal or the same file claimed twice is not
    an overlap. Relative paths resolve against the dispatch cwd. This is string
    normalisation only; it never touches the filesystem.
    """
    text = path.strip().replace("\\", "/")
    if not (len(text) >= 2 and text[1] == ":") and not text.startswith("/"):
        base = cwd if cwd is not None else Path.cwd()
        text = str(base).replace("\\", "/").rstrip("/") + "/" + text
    # Drive/mnt normalisation applies after any join, not before it: a relative
    # path resolved against a /mnt/c base must land on the same spelling as an
    # absolute /mnt/c input, or a WSL-side claim and a Windows-side claim on one
    # file compare unequal (found by tests/test_commit_gate.py, 21 August 2026).
    if len(text) >= 3 and text[1] == ":" and text[2] == "/":
        text = text[0].lower() + text[1:]
    elif text.startswith("/mnt/") and len(text) > 6 and text[6] == "/":
        text = f"{text[5]}:{text[6:]}"
    return _normpath(text).casefold()


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
    epoch_raw = data.get("fencing_epoch")
    # Missing or unparseable is epoch 1, not a dropped claim: a claim written
    # before fencing existed still excludes, and refusing to project it would
    # hand the path to a second dispatcher, which is the failure fencing exists
    # to stop. `_next_fencing_epoch` then outranks it from 2 upwards.
    fencing_epoch = (
        epoch_raw
        if isinstance(epoch_raw, int)
        and not isinstance(epoch_raw, bool)
        and epoch_raw >= 1
        else 1
    )
    return Claim(
        ticket=ticket,
        run_id=run_id,
        actor=event.actor,
        cwd=cwd if isinstance(cwd, str) else "",
        paths=tuple(paths_raw),
        harness=harness if isinstance(harness, str) else None,
        opened_at=str(data["opened_at"]),
        expires_at=str(data["expires_at"]),
        fencing_epoch=fencing_epoch,
    )


def _process_still_running(pid: int) -> bool | None:
    """Return whether the recorded process is running, or ``None`` if unknown."""
    if os.name == "nt":
        return _windows_process_still_running(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        return None
    return True


def worker_gone_from_pid_record(runs_dir: Path, run_id: str) -> bool | None:
    """Map a run to its recorded pid and confirm the worker is not running.

    Reads ``runs_dir/<run_id>/process.json`` for ``{"pid": <int>}``. Returns
    ``True`` when the pid is confirmed gone, ``False`` when it is still running,
    and ``None`` when the mapping or liveness check cannot be completed — the
    fail-closed case. Artefact silence alone is not consulted here.
    """
    record_path = runs_dir / run_id / "process.json"
    try:
        payload = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    pid = payload.get("pid") if isinstance(payload, dict) else None
    if not isinstance(pid, int) or pid < 1:
        return None
    running = _process_still_running(pid)
    return None if running is None else not running


def admit_composite_exposure(
    *,
    candidate_ordinal: int,
    task_family: str,
    protocol_id: str,
    protocol_version: str,
    epsilon: float,
    estimate: beta.Beta | None = None,
    estimand_kind: str | None = None,
    auth_status: str | None = None,
) -> ExposureAdmission:
    """Refuse every automatic composite-verifier exposure that S-01 / ADR-0077 refuse.

    Only a sufficient authenticated, trajectory-derived human_verdict_beta
    projection bound to the same task family and frozen composite-verifier
    protocol/version may admit a candidate. Proxy, mutation, missing or
    mismatched scope, an unwired router and a routing refusal all refuse, and
    none of them writes an exposure event.
    """
    del protocol_id
    if not task_family.strip() or not protocol_version.strip():
        return ExposureAdmission(False, "composite verifier scope is missing", None)
    if estimand_kind is not None and estimand_kind != beta.HUMAN_VERDICT_BETA:
        return ExposureAdmission(
            False,
            f"estimand {estimand_kind!r} is not an authenticated human_verdict_beta",
            None,
        )
    if auth_status is not None and auth_status != beta.AUTHENTICATED_AUTH_STATUS:
        return ExposureAdmission(
            False,
            f"auth_status {auth_status!r} is not authenticated; proxy and declared-principal rows refuse",
            None,
        )
    if estimate is None:
        return ExposureAdmission(
            False,
            "routing has no scoped human_verdict_beta projection; candidate exposure is refused",
            None,
        )
    if (
        estimate.task_family != task_family
        or estimate.verifier_version != protocol_version
    ):
        return ExposureAdmission(
            False,
            "human_verdict_beta scope does not match the frozen composite-verifier contract",
            None,
        )
    ceiling = routing.candidates_ceiling(estimate, epsilon)
    if isinstance(ceiling, routing.RoutingRefusal):
        return ExposureAdmission(False, ceiling.reason, None)
    if ceiling.n_attempt_max is None or ceiling.n_attempt_max < 1:
        return ExposureAdmission(
            False,
            "measured ceiling admits no automatic composite-verifier exposure",
            ceiling.n_attempt_max,
        )
    if candidate_ordinal > ceiling.n_attempt_max:
        return ExposureAdmission(
            False,
            f"candidate {candidate_ordinal} exceeds n_attempt_max {ceiling.n_attempt_max}",
            ceiling.n_attempt_max,
        )
    return ExposureAdmission(
        True,
        "scoped human_verdict_beta admits this candidate",
        ceiling.n_attempt_max,
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
    header = (
        f"## In flight right now\n\n{len(live)} live dispatch claim(s) at {stamp}:\n"
    )
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


def parse_plan_units(plans: Mapping[str, str]) -> dict[str, PlanUnit]:
    """Parse stream-plan markdown into unit records.

    Each plan file may define multiple units. ``depends`` lists only ids that
    appear in the same parsed corpus; external references are dropped.
    """
    units: dict[str, PlanUnit] = {}
    for plan_name, text in plans.items():
        for match in _PLAN_UNIT_HEADING.finditer(text):
            unit_id, title, body = match.group(1), match.group(2), match.group(3)
            claim_match = re.search(r"\*\*Claim exactly:\*\*\n((?:\n- .*)+)", body)
            paths = tuple(
                re.findall(r"`([^`]+)`", claim_match.group(1)) if claim_match else ()
            )
            dep_match = re.search(r"\*\*Depends on:\*\*(.*)", body)
            raw_deps = _PLAN_UNIT_ID.findall(dep_match.group(1)) if dep_match else []
            depends = tuple(sorted({d for d in raw_deps if d != unit_id}))
            units[unit_id] = PlanUnit(
                unit_id=unit_id,
                title=title.strip(),
                paths=paths,
                depends=depends,
                plan=plan_name,
            )
    known = set(units)
    return {
        uid: PlanUnit(
            unit_id=unit.unit_id,
            title=unit.title,
            paths=unit.paths,
            depends=tuple(d for d in unit.depends if d in known),
            plan=unit.plan,
        )
        for uid, unit in units.items()
    }


def parse_build_plan_lanes(build_plan_text: str) -> dict[str, tuple[str, ...]]:
    """Read the hand-maintained lane table from a build-plan markdown body."""
    if _LANE_TABLE_MARKER not in build_plan_text:
        return {}
    section = build_plan_text.split(_LANE_TABLE_MARKER, 1)[1]
    lanes: dict[str, tuple[str, ...]] = {}
    for line in section.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        lane_file = cells[0].strip("`")
        order = tuple(_PLAN_UNIT_ID.findall(cells[1]))
        if order:
            lanes[lane_file] = order
    return lanes

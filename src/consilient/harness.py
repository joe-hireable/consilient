"""Harness registry, pool selection and dispatch recording.

Policy lives here. Process execution does not: `src/consilient/` is AST-locked against
`subprocess`, sockets and credentials. `scripts/dispatch.py` is the runner.

Selection prefers the pool with the most remaining headroom and never silently spends an
exhausted pool. Refusing with a reason is the success path when the scarce resource is
the only thing left.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .events import SCHEMA_VERSION, EventPayload, append

# Operator observation, 21 August 2026. Claude weekly is "nearly exhausted"; no precise
# counter was supplied, so it is flagged exhausted rather than given an invented percent.
EXHAUSTED_USED_PERCENT = 90.0
DISPATCH_ACTOR = "consilient.dispatch"
REFUSED_KIND = "dispatch.refused"
DISPATCH_OUTCOME_KIND = "dispatch.outcome"
FANOUT_KIND = "dispatch.fanout"

Status = Literal["ok", "silent", "failed", "timeout", "refused"]
DecisionKind = Literal["run", "refuse"]
VerdictKind = Literal["agree", "disagree", "incomparable"]

SILENT_MARKERS: tuple[str, ...] = (
    "workspace trust required",
    "untrusted workspace",
    "trust this workspace",
)


@dataclass(frozen=True)
class Harness:
    """One installed-or-installable coding harness and the pool it draws on."""

    id: str
    family: str
    pool: str
    binary: str


@dataclass(frozen=True)
class PoolState:
    """Known headroom for one quota pool. `used_percent` is None when unknown."""

    name: str
    used_percent: float | None
    exhausted: bool
    note: str
    observed_at: str
    source: str


@dataclass(frozen=True)
class Probe:
    """Result of probing whether a harness is actually reachable. Produced by the runner."""

    harness_id: str
    installed: bool
    version: str | None
    detail: str


@dataclass(frozen=True)
class Decision:
    kind: DecisionKind
    harness: Harness | None
    reason: str
    considered: tuple[str, ...]


@dataclass(frozen=True)
class FanoutDecision:
    kind: DecisionKind
    first: Harness | None
    second: Harness | None
    reason: str
    considered: tuple[str, ...]


HARNESSES: tuple[Harness, ...] = (
    Harness(id="claude", family="anthropic", pool="claude-weekly", binary="claude"),
    Harness(
        id="cursor-composer",
        family="cursor",
        pool="cursor-models",
        binary="cursor-agent",
    ),
    Harness(id="grok", family="xai", pool="grok-weekly", binary="grok"),
    Harness(id="codex", family="openai", pool="codex-weekly", binary="codex"),
)

DEFAULT_OBSERVED_AT = "2026-08-21T00:00:00+00:00"
DEFAULT_SOURCE = "operator observation, 21 August 2026"

DEFAULT_POOLS: tuple[PoolState, ...] = (
    PoolState(
        name="claude-weekly",
        used_percent=None,
        exhausted=True,
        note="nearly exhausted",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="cursor-models",
        used_percent=1.0,
        exhausted=False,
        note="Cursor Models (composer)",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="cursor-other",
        used_percent=58.0,
        exhausted=False,
        note="avoid — Cursor Other Models (claude-*/gpt-*/gemini-*)",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="grok-weekly",
        used_percent=2.0,
        exhausted=False,
        note="SuperGrok Heavy weekly",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
    PoolState(
        name="codex-weekly",
        used_percent=None,
        exhausted=False,
        note="unknown",
        observed_at=DEFAULT_OBSERVED_AT,
        source=DEFAULT_SOURCE,
    ),
)

CURSOR_OTHER_PREFIXES: tuple[str, ...] = ("claude-", "gpt-", "gemini-")


def harness_by_id(
    harness_id: str, harnesses: tuple[Harness, ...] = HARNESSES
) -> Harness | None:
    for item in harnesses:
        if item.id == harness_id:
            return item
    return None


def pool_by_name(name: str, pools: tuple[PoolState, ...]) -> PoolState | None:
    for item in pools:
        if item.name == name:
            return item
    return None


def probe_by_id(harness_id: str, probes: Sequence[Probe]) -> Probe | None:
    for item in probes:
        if item.harness_id == harness_id:
            return item
    return None


def cursor_pool_for_model(model: str) -> str:
    """Composer draws on Cursor Models; vendor aliases draw on the avoided Other pool."""
    lowered = model.strip().casefold()
    for prefix in CURSOR_OTHER_PREFIXES:
        if lowered.startswith(prefix):
            return "cursor-other"
    return "cursor-models"


def _is_exhausted(pool: PoolState) -> bool:
    if pool.exhausted:
        return True
    return pool.used_percent is not None and pool.used_percent >= EXHAUSTED_USED_PERCENT


def _blocked(
    pool: PoolState, *, allow_exhausted: bool, require_known_headroom: bool
) -> str | None:
    """Why this pool cannot be spent, or None if it can.

    Exhausted is a hard stop unless the operator names `--allow-exhausted`. Unknown
    headroom is a hard stop for automatic selection; an explicit `--harness` may
    proceed because that is attended, not a silent fallback.
    """
    if _is_exhausted(pool) and not allow_exhausted:
        note = f" ({pool.note})" if pool.note else ""
        if pool.used_percent is not None and pool.used_percent >= EXHAUSTED_USED_PERCENT:
            return (
                f"{pool.name} is at {pool.used_percent:g}% used "
                f"(threshold {EXHAUSTED_USED_PERCENT:g}%){note}"
            )
        return f"{pool.name} is exhausted{note}"
    if require_known_headroom and pool.used_percent is None:
        if allow_exhausted and _is_exhausted(pool):
            return None
        return f"{pool.name} headroom is unknown"
    return None


def remaining_percent(pool: PoolState) -> float | None:
    """The counter, not the gate. Exhaustion is `_blocked`; this is ranking input."""
    if pool.used_percent is None:
        return None
    return 100.0 - pool.used_percent


def _ineligible(
    harness: Harness,
    probe: Probe | None,
    pool: PoolState | None,
    *,
    allow_exhausted: bool,
    require_known_headroom: bool,
) -> str | None:
    if probe is None or not probe.installed:
        detail = probe.detail if probe is not None else "not probed"
        return f"{harness.id}: not installed ({detail})"
    if pool is None:
        return f"{harness.id}: pool {harness.pool} has no headroom snapshot"
    blocked = _blocked(
        pool,
        allow_exhausted=allow_exhausted,
        require_known_headroom=require_known_headroom,
    )
    if blocked is not None:
        return f"{harness.id}: {blocked}"
    return None


def _rank_key(harness: Harness, pool: PoolState) -> tuple[float, str]:
    remaining = remaining_percent(pool)
    # Higher remaining headroom first; unknown sorts last. harness.id breaks ties.
    score = remaining if remaining is not None else -1.0
    return (-score, harness.id)


def select(
    *,
    probes: Sequence[Probe],
    pools: Sequence[PoolState],
    requested: str | None = None,
    allow_exhausted: bool = False,
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> Decision:
    """Pick one harness. Never returns an exhausted pool unless `allow_exhausted`."""
    pool_tuple = tuple(pools)
    considered: list[str] = []

    if requested is not None:
        harness = harness_by_id(requested, harnesses)
        if harness is None:
            known = ", ".join(item.id for item in harnesses)
            return Decision(
                kind="refuse",
                harness=None,
                reason=f"unknown harness {requested!r}; known: {known}",
                considered=(),
            )
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        reason = _ineligible(
            harness,
            probe,
            pool,
            allow_exhausted=allow_exhausted,
            require_known_headroom=False,
        )
        if reason is not None:
            return Decision(
                kind="refuse",
                harness=None,
                reason=reason,
                considered=(reason,),
            )
        assert pool is not None
        remaining = remaining_percent(pool)
        headroom = (
            f"{remaining:g}% remaining"
            if remaining is not None
            else pool.note or "headroom unknown"
        )
        return Decision(
            kind="run",
            harness=harness,
            reason=f"{harness.id} on {harness.pool} ({headroom})",
            considered=(),
        )

    ranked: list[tuple[Harness, PoolState]] = []
    for harness in harnesses:
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        reason = _ineligible(
            harness,
            probe,
            pool,
            allow_exhausted=allow_exhausted,
            require_known_headroom=True,
        )
        if reason is not None:
            considered.append(reason)
            continue
        assert pool is not None
        ranked.append((harness, pool))

    if not ranked:
        detail = "; ".join(considered) if considered else "no harnesses in the registry"
        return Decision(
            kind="refuse",
            harness=None,
            reason=(
                "no eligible harness: every pool is exhausted, unknown, or not installed. "
                f"{detail}"
            ),
            considered=tuple(considered),
        )

    ranked.sort(key=lambda pair: _rank_key(pair[0], pair[1]))
    harness, pool = ranked[0]
    remaining = remaining_percent(pool)
    headroom = (
        f"{remaining:g}% remaining"
        if remaining is not None
        else pool.note or "headroom unknown"
    )
    return Decision(
        kind="run",
        harness=harness,
        reason=f"{harness.id} on {harness.pool} ({headroom})",
        considered=tuple(considered),
    )


def select_fanout(
    *,
    probes: Sequence[Probe],
    pools: Sequence[PoolState],
    allow_exhausted: bool = False,
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> FanoutDecision:
    """Two harnesses from different families, each eligible, most headroom first."""
    pool_tuple = tuple(pools)
    considered: list[str] = []
    eligible: list[tuple[Harness, PoolState]] = []
    for harness in harnesses:
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        reason = _ineligible(
            harness,
            probe,
            pool,
            allow_exhausted=allow_exhausted,
            require_known_headroom=True,
        )
        if reason is not None:
            considered.append(reason)
            continue
        assert pool is not None
        eligible.append((harness, pool))

    eligible.sort(key=lambda pair: _rank_key(pair[0], pair[1]))
    if not eligible:
        return FanoutDecision(
            kind="refuse",
            first=None,
            second=None,
            reason=(
                "fan-out refused: no eligible harness. " + "; ".join(considered)
            ),
            considered=tuple(considered),
        )

    first, first_pool = eligible[0]
    second_pair: tuple[Harness, PoolState] | None = None
    for harness, pool in eligible[1:]:
        if harness.family != first.family:
            second_pair = (harness, pool)
            break
    if second_pair is None:
        families = {item.family for item, _ in eligible}
        return FanoutDecision(
            kind="refuse",
            first=None,
            second=None,
            reason=(
                "fan-out refused: need two different model families; "
                f"eligible families: {', '.join(sorted(families)) or 'none'}"
            ),
            considered=tuple(considered),
        )

    second, second_pool = second_pair
    first_left = remaining_percent(first_pool)
    second_left = remaining_percent(second_pool)
    first_h = (
        f"{first_left:g}% remaining" if first_left is not None else first_pool.note or "unknown"
    )
    second_h = (
        f"{second_left:g}% remaining"
        if second_left is not None
        else second_pool.note or "unknown"
    )
    return FanoutDecision(
        kind="run",
        first=first,
        second=second,
        reason=(
            f"{first.id} ({first.family}, {first_h}) and "
            f"{second.id} ({second.family}, {second_h})"
        ),
        considered=tuple(considered),
    )


def parse_status(value: str) -> Status:
    mapping: dict[str, Status] = {
        "ok": "ok",
        "silent": "silent",
        "failed": "failed",
        "timeout": "timeout",
        "refused": "refused",
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"unknown dispatch status {value!r}") from exc


def classify_artefact(
    *,
    exit_code: int | None,
    stdout: str,
    stderr: str,
    output_bytes: int,
    diff_bytes: int,
    timed_out: bool,
) -> tuple[Status, str]:
    """Verify by artefact, never by exit code. Empty exit-0 is `silent`."""
    combined = f"{stdout}\n{stderr}"
    lowered = combined.casefold()
    for marker in SILENT_MARKERS:
        if marker in lowered:
            return (
                "silent",
                f"harness produced no work: {marker!r} (exit {exit_code})",
            )
    if timed_out:
        return "timeout", f"timed out (exit {exit_code})"
    produced = output_bytes > 0 or diff_bytes > 0 or bool(stdout.strip() or stderr.strip())
    if not produced:
        return (
            "silent",
            f"exit {exit_code} with empty transcript and no diff",
        )
    if exit_code is None:
        return "failed", "process exited without a code"
    if exit_code != 0:
        return "failed", f"exit {exit_code}"
    return "ok", "produced an artefact"


def judge_fanout(first_text: str, second_text: str, first_ok: bool, second_ok: bool) -> VerdictKind:
    if not first_ok or not second_ok:
        return "incomparable"
    left = " ".join(first_text.split()).casefold()
    right = " ".join(second_text.split()).casefold()
    if not left or not right:
        return "incomparable"
    if left == right:
        return "agree"
    return "disagree"


def now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id(ts: str, task: str, label: str) -> str:
    stamp = ts.replace("-", "").replace(":", "").replace("+", "Z")[:15]
    digest = hashlib.sha256(f"{ts}\n{label}\n{task}".encode()).hexdigest()[:10]
    return f"{stamp}-{digest}"


def _event(kind: str, ts: str, data: dict[str, object]) -> EventPayload:
    return {
        "v": SCHEMA_VERSION,
        "ts": ts,
        "event": kind,
        "actor": DISPATCH_ACTOR,
        "data": data,
    }


def record_refusal(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    task: str,
    cwd: str,
    reason: str,
    considered: Sequence[str],
) -> EventPayload:
    return append(
        log_dir / f"{ts[:10]}.jsonl",
        _event(
            REFUSED_KIND,
            ts,
            {
                "run_id": run_id,
                "task": task,
                "cwd": cwd,
                "status": "refused",
                "reason": reason,
                "considered": list(considered),
            },
        ),
    )


def record_outcome(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    task: str,
    cwd: str,
    harness: Harness,
    status: Status,
    reason: str,
    exit_code: int | None,
    artefact_bytes: int,
    diff_bytes: int,
    timed_out: bool,
    duration_s: float,
    command: Sequence[str],
) -> EventPayload:
    return append(
        log_dir / f"{ts[:10]}.jsonl",
        _event(
            DISPATCH_OUTCOME_KIND,
            ts,
            {
                "run_id": run_id,
                "task": task,
                "cwd": cwd,
                "harness": harness.id,
                "family": harness.family,
                "pool": harness.pool,
                "status": status,
                "reason": reason,
                "exit_code": exit_code,
                "artefact_bytes": artefact_bytes,
                "diff_bytes": diff_bytes,
                "timed_out": timed_out,
                "duration_s": duration_s,
                "command": list(command),
            },
        ),
    )


def record_fanout(
    log_dir: Path,
    *,
    ts: str,
    run_id: str,
    task: str,
    cwd: str,
    first: Harness,
    second: Harness,
    first_status: Status,
    second_status: Status,
    verdict: VerdictKind,
    first_run_id: str,
    second_run_id: str,
) -> EventPayload:
    contributors = [
        {
            "logical_identity": first.id,
            "evidence_class": f"family:{first.family}",
            "status": first_status,
            "run_id": first_run_id,
        },
        {
            "logical_identity": second.id,
            "evidence_class": f"family:{second.family}",
            "status": second_status,
            "run_id": second_run_id,
        },
    ]
    return append(
        log_dir / f"{ts[:10]}.jsonl",
        _event(
            FANOUT_KIND,
            ts,
            {
                "run_id": run_id,
                "task": task,
                "cwd": cwd,
                "status": verdict,
                "reason": (
                    "independent families answering the same task; "
                    "agreement is evidence, disagreement is the finding"
                ),
                "contributors": contributors,
                "first": first.id,
                "second": second.id,
            },
        ),
    )


def _as_percent(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("used_percent cannot be a boolean")
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        if value != value:  # NaN
            raise ValueError("used_percent is not a number")
        return value
    raise ValueError(f"used_percent must be a number, got {type(value).__name__}")


def pools_from_mapping(raw: object) -> tuple[PoolState, ...]:
    """Parse an operator headroom snapshot. Missing pools fall back to the default."""
    if not isinstance(raw, dict):
        raise ValueError("headroom snapshot must be an object")
    observed_at = raw.get("observed_at", DEFAULT_OBSERVED_AT)
    source = raw.get("source", "headroom file")
    if not isinstance(observed_at, str) or not observed_at.strip():
        raise ValueError("observed_at must be a non-empty string")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")
    pools_raw = raw.get("pools")
    if not isinstance(pools_raw, dict):
        raise ValueError("headroom snapshot must carry a pools object")

    by_name: dict[str, PoolState] = {item.name: item for item in DEFAULT_POOLS}
    for name, body in pools_raw.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("pool name must be a non-empty string")
        if not isinstance(body, dict):
            raise ValueError(f"pool {name} must be an object")
        used = _as_percent(body.get("used_percent"))
        note_raw = body.get("note", "")
        if note_raw is None:
            note = ""
        elif isinstance(note_raw, str):
            note = note_raw
        else:
            raise ValueError(f"pool {name} note must be a string")
        exhausted_raw = body.get("exhausted")
        if exhausted_raw is None:
            exhausted_flag = False
        elif isinstance(exhausted_raw, bool):
            exhausted_flag = exhausted_raw
        else:
            raise ValueError(f"pool {name} exhausted must be a boolean")
        exhausted = exhausted_flag or (
            used is not None and used >= EXHAUSTED_USED_PERCENT
        )
        by_name[name] = PoolState(
            name=name,
            used_percent=used,
            exhausted=exhausted,
            note=note,
            observed_at=observed_at,
            source=source,
        )
    # Keep default order, then any extra pools.
    ordered = [by_name[item.name] for item in DEFAULT_POOLS]
    extras = [
        by_name[name] for name in by_name if name not in {item.name for item in DEFAULT_POOLS}
    ]
    return tuple(ordered + extras)


def load_pools(path: Path | None) -> tuple[PoolState, ...]:
    if path is None or not path.exists():
        return DEFAULT_POOLS
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"headroom file {path} is unreadable: {exc}") from exc
    return pools_from_mapping(raw)


def snapshot_mapping(pools: Sequence[PoolState]) -> dict[str, object]:
    first = pools[0] if pools else None
    return {
        "observed_at": first.observed_at if first is not None else DEFAULT_OBSERVED_AT,
        "source": first.source if first is not None else DEFAULT_SOURCE,
        "pools": {
            item.name: {
                "used_percent": item.used_percent,
                "exhausted": item.exhausted,
                "note": item.note,
            }
            for item in pools
        },
    }


def describe_registry(
    *,
    probes: Sequence[Probe],
    pools: Sequence[PoolState],
    harnesses: tuple[Harness, ...] = HARNESSES,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    pool_tuple = tuple(pools)
    for harness in harnesses:
        probe = probe_by_id(harness.id, probes)
        pool = pool_by_name(harness.pool, pool_tuple)
        remaining = remaining_percent(pool) if pool is not None else None
        rows.append(
            {
                "id": harness.id,
                "family": harness.family,
                "pool": harness.pool,
                "binary": harness.binary,
                "installed": probe.installed if probe is not None else False,
                "version": probe.version if probe is not None else None,
                "probe": probe.detail if probe is not None else "not probed",
                "used_percent": pool.used_percent if pool is not None else None,
                "exhausted": pool.exhausted if pool is not None else False,
                "remaining_percent": remaining,
                "note": pool.note if pool is not None else "",
            }
        )
    return rows



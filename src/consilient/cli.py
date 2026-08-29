"""`consil` — the observe-only increment.

It records, projects and reports. It never routes, never blocks and never accepts an
artefact. Routing and blocking are Stage 3 and need Gate B (ADR-0015); nothing here can
be made to do them by a flag.

V0-14: every command has one JSON contract, and human output is a rendering of the same
result rather than a second semantics.

The commands that compose the whole surface stay in this file -- `doctor`, `dashboard`,
`require_trajectory`, the parser and `main`. Four siblings hold the rest, each
referencing only the ones below it: `cli_replay.py` has the replay command, the
pinned-prefix digest and every constant the family pins to; `cli_measurements.py` has
the `record`, `usage` and `beta` commands with the trajectory-state reader and the
condition and gate shapes; `cli_readout.py` has the experiment-register conditions A1,
B1 and B2 and the human rendering of every command result; and `cli_conditions.py` has
the conditions decided from the trajectory -- A2, A3, B3 and B4 -- together with the
wrong-tree refusal.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Literal
from . import dashboard as dashboard_mod
from . import events as events_mod
from . import projection
from . import usage as usage_mod
from .events import EventError, read_all
from .events import jittered_sleep as _jittered_sleep
from .cli_replay import (
    CommandResult,
    _DB_BUSY_BACKOFF,
    _DB_BUSY_RETRIES,
    _trajectory_refusal,
    cmd_replay,
)

from .cli_conditions import (
    _capture_condition,
    _fallback_condition,
    _foreign_tickets,
    _foreign_tree,
    _replay_condition,
    _structural_condition,
)

from .cli_measurements import (
    CAPTURE_REFUSAL_BASELINE,
    CODE_TREE,
    DEFAULTS,
    _command_needs_trajectory,
    _condition,
    _experiment_entry,
    _gate,
    cmd_beta,
    cmd_record,
    cmd_usage,
    is_this_repository,
    trajectory_state,
)

from .cli_readout import (
    _experiment_conditions,
    render,
)

from .cli_replay import (
    B4_TICKETS_REQUIRED,
    CRITIC_BETA,
    DEFAULT_DASHBOARD,
    DEFAULT_DB,
    DEFAULT_LOG,
    EXP01_BETA,
    EXPECTED_FALLBACK_COMMAND,
    EXPERIMENT_REGISTER,
    FALLBACK_MAX_AGE_DAYS,
    FALLBACK_RESULT,
    FALLBACK_RUNNER_IDENTITY,
    GATE_B2_ADR,
    GATE_B4_ADR,
    GATE_B_CIRCULARITY,
    HISTORICAL_REFUSAL_DIGESTS,
    READ_TRAJECTORY_COMMANDS,
    REQUIREMENTS,
    THIS_REPOSITORIES,
    THIS_REPOSITORY,
    TrajectoryState,
    _copy_event_prefix,
    _digest_of_pinned_prefix,
)

__all__ = [
    "B4_TICKETS_REQUIRED",
    "CAPTURE_REFUSAL_BASELINE",
    "CODE_TREE",
    "CRITIC_BETA",
    "CommandResult",
    "DEFAULTS",
    "DEFAULT_DASHBOARD",
    "DEFAULT_DB",
    "DEFAULT_LOG",
    "EXP01_BETA",
    "EXPECTED_FALLBACK_COMMAND",
    "EXPERIMENT_REGISTER",
    "FALLBACK_MAX_AGE_DAYS",
    "FALLBACK_RESULT",
    "FALLBACK_RUNNER_IDENTITY",
    "GATE_B2_ADR",
    "GATE_B4_ADR",
    "GATE_B_CIRCULARITY",
    "HISTORICAL_REFUSAL_DIGESTS",
    "READ_TRAJECTORY_COMMANDS",
    "REQUIREMENTS",
    "THIS_REPOSITORIES",
    "THIS_REPOSITORY",
    "TrajectoryState",
    "_DB_BUSY_BACKOFF",
    "_DB_BUSY_RETRIES",
    "_capture_condition",
    "_command_needs_trajectory",
    "_condition",
    "_copy_event_prefix",
    "_digest_of_pinned_prefix",
    "_experiment_conditions",
    "_experiment_entry",
    "_fallback_condition",
    "_foreign_tickets",
    "_foreign_tree",
    "_gate",
    "_replay_condition",
    "_structural_condition",
    "_trajectory_refusal",
    "build_parser",
    "cmd_beta",
    "cmd_dashboard",
    "cmd_doctor",
    "cmd_record",
    "cmd_replay",
    "cmd_usage",
    "is_this_repository",
    "main",
    "render",
    "require_trajectory",
    "trajectory_state",
]


def require_trajectory(log: Path) -> Literal["empty", "present"]:
    """Refuse when the log directory is absent. Upward search was rejected: it would let a
    command silently read a parent checkout's trajectory while the user believes they are
    elsewhere — the wrong-worktree hazard this project was already bitten by. Explicit
    --log and the provenance block on `doctor` are the supported ways to see which path
    answered.
    """
    state = trajectory_state(log)
    if state == "missing":
        raise EventError(_trajectory_refusal(log))
    return state


def cmd_doctor(args: argparse.Namespace) -> CommandResult:
    log, db = Path(args.log), Path(args.db)
    # Replay must inspect prior state before anything rebuilds the projection; rebuilding
    # first would recreate the tautological A2 check repaired on 20 August 2026. The beta
    # read that used to follow here fed Gate B2's throughput threshold, withdrawn by
    # ADR-0045.
    # A contended database is the NORMAL case here, not an exceptional one. This repository
    # runs twenty-odd agents appending to the trajectory and rebuilding the projection, and a
    # gate check that gives up the moment a writer holds the file cannot be trusted on a live
    # system -- which is the same defect as the A2 race it exists to decide. MEASURED 24 August
    # 2026: `doctor` exited 2 with "state database is locked or busy" whenever a writer thread
    # was mid-append, so the verdict depended on timing rather than on state.
    #
    # Bounded exponential retry, matching the precedent already set for trajectory reads in
    # events.py. It fails CLOSED after the last attempt: a lock we never got is reported, never
    # silently treated as a pass.
    replay = None
    for attempt in range(_DB_BUSY_RETRIES):
        try:
            replay = cmd_replay(args)
            break
        except PermissionError as exc:
            if attempt == _DB_BUSY_RETRIES - 1:
                raise EventError(
                    f"state database is locked or busy at {db} after "
                    f"{_DB_BUSY_RETRIES} attempts; close any process using it, "
                    "then run consil doctor again"
                ) from exc
            # Full jitter, for the same reason as events._retry_sleep: the SQLite state
            # database is contended by the same ~20 concurrent agents, and a lockstep retry
            # schedule makes every evicted waiter collide again at every step. Shared helper,
            # so there is one jitter rule rather than two that can drift apart.
            _jittered_sleep(_DB_BUSY_BACKOFF * (2**attempt))
    if replay is None:  # pragma: no cover - the loop either breaks or raises
        raise EventError(f"state database at {db} could not be read")
    a1, b1, b2 = _experiment_conditions()
    gates = {
        "A": _gate([a1, _replay_condition(replay, log, db), _capture_condition(log)]),
        "B": _gate([b1, b2, _fallback_condition(), _structural_condition(log)]),
    }
    expected = {"A": {"A1", "A2", "A3"}, "B": {"B1", "B2", "B3", "B4"}}
    enabled = all(
        {condition["id"] for condition in gates[name]["conditions"]} == identifiers
        and all(
            condition["status"] == "pass" for condition in gates[name]["conditions"]
        )
        for name, identifiers in expected.items()
    )
    return {
        "gates": gates,
        # Which code answered, and which directory it answered about. Unconditional: the
        # refusal below cannot fire when the measured directory is an ordinary repository,
        # and there this is the whole defence.
        "provenance": {
            "code": str(CODE_TREE),
            "data": str(Path.cwd().resolve()),
            "log": str(log.resolve()),
        },
        "routing_orchestration_enabled": enabled,
    }


def cmd_dashboard(args: argparse.Namespace) -> CommandResult:
    """Render the observability surface to one self-contained file (ADR-0053).

    Every authoritative figure is taken from the command that already owns it — `cmd_doctor`
    for the gates, `cmd_beta` for beta, `render` for beta's own sentence — and copied through
    untouched. This function performs no arithmetic on any of them. That is what makes it
    impossible for the page and the CLI to disagree, rather than merely unlikely (V0-30).
    """
    log = Path(args.log)
    # Order matters: doctor runs replay, which must inspect the state already on disk before
    # anything rebuilds it. Computing beta first would rebuild the projection and destroy the
    # subject of the A2 comparison — the exact defect repaired in `cmd_replay` on 20 Aug 2026.
    doctor = cmd_doctor(args)
    beta_result = cmd_beta(args)
    events, rejections = read_all(log)
    windows, note = dashboard_mod.read_usage(events)
    payload = dashboard_mod.build_payload(
        events,
        rejections,
        doctor,
        beta_result,
        render("beta", beta_result),
        len(events_mod.bypassed(log)),
        windows,
        note,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dashboard_mod.render_html(payload), encoding="utf-8", newline="\n")
    return {**payload, "written": str(out)}


def build_parser() -> argparse.ArgumentParser:
    # Shared options are attached to the root and to every subcommand, so `--json` works
    # on either side of the command name. `consil beta --json` is the form people type.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="machine-readable output",
    )
    common.add_argument("--log", default=argparse.SUPPRESS)
    common.add_argument("--db", default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(
        prog="consil",
        parents=[common],
        description="Observe-only. Records trajectory events and computes beta.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser(
        "record", parents=[common], help="append one validated event"
    )
    record.add_argument("--event", required=True, help="the event, as JSON")
    record.set_defaults(handler=cmd_record)

    replay = sub.add_parser(
        "replay",
        parents=[common],
        help="rebuild the projection and check it is stable",
    )
    replay.set_defaults(handler=cmd_replay)

    b = sub.add_parser(
        "beta",
        parents=[common],
        help="report beta with its sample count and interval",
    )
    b.add_argument("--task-family")
    b.add_argument("--verifier-version")
    b.set_defaults(handler=cmd_beta)

    usage = sub.add_parser(
        "usage",
        parents=[common],
        help="usage, limits and spend across every configured provider",
    )
    usage.add_argument(
        "--payloads",
        default=str(usage_mod.DEFAULT_PAYLOADS),
        help="directory an out-of-tree probe drops provider payloads into",
    )
    usage.add_argument(
        "--limits",
        default=str(usage_mod.DEFAULT_LIMITS),
        help="the instance spend-limit configuration; never committed",
    )
    usage.add_argument(
        "--record", action="store_true", help="append the snapshot to the trajectory"
    )
    usage.add_argument(
        "--fake",
        action="store_true",
        help="a fabricated snapshot for building a view against; records nothing",
    )
    usage.set_defaults(handler=cmd_usage)

    doctor = sub.add_parser(
        "doctor",
        parents=[common],
        help="report measured Gate A and Gate B status",
    )
    doctor.set_defaults(handler=cmd_doctor)

    dash = sub.add_parser(
        "dashboard",
        parents=[common],
        help="render the local observability surface to one self-contained HTML file",
    )
    dash.add_argument("--out", default=argparse.SUPPRESS)
    dash.set_defaults(handler=cmd_dashboard)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for name, value in DEFAULTS.items():
        if not hasattr(args, name):
            setattr(args, name, value)
    refusal = _foreign_tree()
    if refusal is not None:
        print(
            json.dumps({"error": refusal}) if args.json else f"error: {refusal}",
            file=sys.stderr,
        )
        return 2
    log = Path(args.log)
    try:
        if _command_needs_trajectory(args):
            require_trajectory(log)
        result = args.handler(args)
    except (EventError, projection.ProjectionError) as exc:
        print(
            json.dumps({"error": str(exc)}) if args.json else f"error: {exc}",
            file=sys.stderr,
        )
        return 2
    if log.is_dir():
        result["trajectory_source"] = {
            "path": str(log.resolve()),
            "state": trajectory_state(log),
        }
    print(
        json.dumps(result, ensure_ascii=False, sort_keys=True)
        if args.json
        else render(args.command, result)
    )
    if args.command == "doctor":
        # ADR-0015's Enforcement clause calls `consil doctor` the authority on gate status
        # and "Not advisory". Until 21 August 2026 it printed `Gate A: FAIL` and
        # `Gate B: FAIL` and exited 0 [measured], so `consil doctor && <next step>` ran the
        # next step and any caller reading `$?` was told the gates were open. That is B9 in
        # this repository's own catalogue -- a failing gate reporting success through a
        # discarded status -- made structural rather than accidental. The payload was
        # always honest; the exit code now agrees with it.
        return 0 if result["routing_orchestration_enabled"] else 1
    return 0 if result.get("identical", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

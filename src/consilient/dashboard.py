"""The observability surface (ADR-0053). A rendering of the record, never a second record.

`consil dashboard` writes one self-contained HTML file. There is no server, no port, no
auth, no bundler and no frontend dependency — ADR-0007's objections to a local web server
all survive, and this form costs none of them. There is also no JavaScript: view switching
uses CSS `:checked` sibling selectors over radio inputs, and expert detail uses `<details>`.
Both are platform features, so the page has no runtime to break.

Two rules govern everything here.

**Never recompute an authoritative number.** β and the gate conditions arrive as the exact
result dicts `cmd_beta` and `cmd_doctor` produced, and the β line is `Beta.render()`'s own
output. This module may lay them out; it may not do arithmetic on them. V0-14 says human
output is a rendering of one result rather than a second semantics, and a dashboard that
computed its own β would be a second semantics wearing the same name. V0-30 tests it.

**Never render an absence as a value.** The trajectory does not record who spawned whom,
what an agent read, whether it is still running, or who was informed of a result. Those are
reported as named gaps in `schema_gaps`, in the place the answer would have gone. An
invented graph is worse than no graph, and it is the precise failure this project exists to
measure.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .events import CAPABILITY_GAP_KIND, Event, Rejection

# Every panel's payload is a differently-shaped JSON object at the render boundary, exactly
# as `cli.CommandResult` is. Values are escaped at emit, never trusted here.
Payload = dict[str, Any]

# Fields the record would need before the corresponding question could be answered from it.
# Each is checked against the real trajectory rather than assumed absent: `build_payload`
# counts occurrences, so a gap closes itself the moment events start carrying the field.
SPAWN_FIELDS = ("parent", "parent_id", "spawned_by", "session_id")
LIFECYCLE_FIELDS = ("started_at", "finished_at", "heartbeat_at", "state")
READ_FIELDS = ("reads", "inputs", "depends_on")
RACI_FIELDS = ("accountable", "consulted", "informed", "responsible")
WORK_ITEM_FIELDS = ("work_item", "ticket", "decision_id")

# --------------------------------------------------------------------------------------
# Plain language. [asserted] throughout — these are this author's readings of each
# condition, written for the accessibility requirement Joe set on 21 Aug 2026 ("average
# plus intelligence"). They restate; they never soften. A failing condition reads as failing
# in both registers. ADR-0055 is being written concurrently on which concepts a competent
# non-expert actually needs, and its answer supersedes these strings if the two disagree.
# --------------------------------------------------------------------------------------
PLAIN_CONDITIONS: dict[str, str] = {
    "A1": "The error-rate measurement has been run on two different codebases.",
    "A2": "Rebuilding the database from the log produces exactly the same result.",
    "A3": "The log has recorded seven days in a row with nothing lost.",
    "B1": "Adding a second agent tool did not force the interface to be redesigned.",
    "B2": "We have measured how often the automatic reviewer approves bad work.",
    "B3": "A tested fallback exists for when the harness itself breaks.",
    "B4": "Twenty real jobs on other projects finished without a human stepping in.",
}

PLAIN_STATUS: dict[str, str] = {
    "pass": "Done",
    "fail": "Not yet",
    "unknown": "Never run",
    "structurally_unsatisfiable": "Cannot pass as written",
}

# Form as well as colour: each state carries a distinct glyph, so the page is readable in
# greyscale and by anyone who does not distinguish red from green.
STATUS_GLYPH: dict[str, str] = {
    "pass": "✓",
    "fail": "✗",
    "unknown": "?",
    "structurally_unsatisfiable": "⊘",
}


@dataclass(frozen=True)
class UsageWindow:
    """One provider's consumption against one ceiling, over one resetting window.

    **This is the consumer side of an interface another agent owns.** The usage and limits
    data layer was being built concurrently on 21 Aug 2026 and had committed nothing to
    `wt/usage` when this was written [measured: `git diff wt/observability wt/usage` was
    empty]. Rather than build a second set of collectors — which would guarantee two
    disagreeing numbers — this declares the shape the dashboard consumes and reads the only
    source already in the record.

    To supply real data, provide windows with these fields. Nothing here opens a socket,
    reads a credential or shells out; if a provider needs a credential it is that provider's
    problem to solve locally, and an unsupplied window renders as "not connected" rather
    than as zero. `used` and `ceiling` are strings because they are money and because
    `events.py` already carries money as Decimal strings.
    """

    provider: str
    plan: str
    window: str
    used: str
    ceiling: str | None
    unit: str
    resets_at: str | None
    observed_at: str
    source: str

    def as_dict(self) -> Payload:
        d: Payload = {
            "provider": self.provider,
            "plan": self.plan,
            "window": self.window,
            "used": self.used,
            "ceiling": self.ceiling,
            "unit": self.unit,
            "resets_at": self.resets_at,
            "observed_at": self.observed_at,
            "source": self.source,
            "fraction": None,
        }
        if self.ceiling is not None:
            try:
                limit = float(self.ceiling)
                if limit > 0:
                    d["fraction"] = min(1.0, max(0.0, float(self.used) / limit))
            except (TypeError, ValueError):
                d["fraction"] = None
        return d


def read_usage(events: list[Event]) -> tuple[list[UsageWindow], str]:
    """Usage windows from the record alone. No network, no credential, no collector.

    `budget.state` events already carry `weekly_spent`, `monthly_spent`, `observed_at` and a
    validated provider and currency (`events._check_budget_contract`), so where they exist
    this is a projection in exactly the sense the SQLite database is. Where they do not, the
    honest answer is an empty list and a reason — not a zero, which would read as "nothing
    spent" when it means "nothing observed".
    """
    latest: Event | None = None
    for event in events:
        if event.kind == "budget.state":
            latest = event
    if latest is None:
        return [], (
            "No budget.state events in the trajectory, so no metered spend has been "
            "observed. This is an absence of observation, not an observation of zero."
        )
    data = latest.data
    provider = str(data.get("provider", "unknown"))
    observed = str(data.get("observed_at", latest.raw["ts"]))
    windows = [
        UsageWindow(
            provider=provider,
            plan="metered",
            window=name,
            used=str(data.get(field, "0")),
            ceiling=(str(data[cap]) if cap in data else None),
            unit=str(data.get("currency", "USD")),
            resets_at=(str(data[reset]) if reset in data else None),
            observed_at=observed,
            source=f"{latest.path}:{latest.line}",
        )
        for name, field, cap, reset in (
            ("weekly", "weekly_spent", "weekly_cap", "weekly_resets_at"),
            ("monthly", "monthly_spent", "monthly_cap", "monthly_resets_at"),
        )
        if field in data
    ]
    return (
        windows,
        f"Projected from the latest budget.state event, observed {observed}.",
    )


def _agent_key(event: Event) -> str:
    runtime = event.data.get("runtime_identity")
    if isinstance(runtime, str) and runtime.strip():
        return runtime.strip()
    return event.actor


def _as_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []


def _is_path(value: str) -> bool:
    """Is this `artefacts` entry actually a file, or prose that landed in the field?

    `artefacts` is free-form, and on the real trajectory 4 of its 69 distinct values are not
    files: two bare commit identifiers, and two sentences ("private handoff memo only" and a
    description of a remote-control environment). [measured]

    Drawing those as though they were directories is a small lie of exactly the kind this
    surface exists not to tell — the reader would see a node named `6088e3e` and conclude
    the agent wrote to a directory of that name. They are counted and reported separately
    under their own honest heading instead of being silently dropped, because a dropped
    value is a different lie.
    """
    head = value.split("#")[0].strip().replace("\\", "/")
    if not head or " " in head:
        return False
    return "/" in head or re.fullmatch(r"[\w.-]+\.[A-Za-z0-9]{1,6}", head) is not None


def _artefact_group(path: str) -> str:
    """Collapse an artefact path to its top two segments so the graph stays legible.

    65 file paths across 11 groups on the real trajectory [measured]. Drawing 65 nodes
    produces a hairball that shows less than 11 nodes do; the full list stays in the table
    view, so nothing is hidden, only summarised.
    """
    head = path.split("#")[0].strip().replace("\\", "/")
    parts = [p for p in head.split("/") if p]
    if not parts:
        return "(unknown)"
    return "/".join(parts[:2]) if len(parts) > 1 else parts[0]


def _disambiguate(agents: list[Payload]) -> None:
    """Give every agent a label that names one agent.

    Three separate runtimes share the logical identity `orchestrator-root` on the real
    trajectory. Labelling all three "orchestrator-root" drew what looked like one agent
    doing three unrelated things, or three agents that were actually one. Where a logical
    identity is not unique, the runtime identity's distinguishing tail is appended.
    """
    seen: dict[str, int] = {}
    for agent in agents:
        name = str(agent["logical_identity"] or agent["key"])
        seen[name] = seen.get(name, 0) + 1
    for agent in agents:
        name = str(agent["logical_identity"] or agent["key"])
        if seen[name] > 1:
            tail = str(agent["key"]).split("/")[-1]
            agent["label"] = f"{name} · {tail}"
        else:
            agent["label"] = name


def _count_field(events: list[Event], fields: tuple[str, ...]) -> dict[str, int]:
    return {f: sum(1 for e in events if f in e.data) for f in fields}


def _capability_gaps(events: list[Event]) -> Payload:
    """Capability gaps ranked by repetition — the strongest signal a gap carries.

    Grouping is by the policy-normalised triple (failure, repair, attempted), never by
    the verbatim detail, which embeds run-specific text. Two events with the same triple
    are the same gap hit again; the view counts and orders, and performs no other
    arithmetic. Per-user repetition — the same gap hit by several users — is the other
    half of the ranking rule and is NOT recorded today: the trajectory has one
    principal and gap events carry no user field. That absence is stated, not filled in.
    """
    groups: dict[tuple[str, str, str], Payload] = {}
    total = 0
    for event in events:
        if event.kind != CAPABILITY_GAP_KIND:
            continue
        total += 1
        data = event.data
        key = (
            str(data.get("failure", "")),
            str(data.get("repair", "")),
            str(data.get("attempted", "")),
        )
        row = groups.setdefault(
            key,
            {
                "failure": key[0],
                "repair": key[1],
                "attempted": key[2],
                "closure": str(data.get("closure", "")),
                "count": 0,
                "first_seen": event.raw["ts"],
                "last_seen": event.raw["ts"],
                "latest_asked": "",
                "latest_detail": "",
                "sources": [],
            },
        )
        row["count"] += 1
        if event.raw["ts"] < row["first_seen"]:
            row["first_seen"] = event.raw["ts"]
        if event.raw["ts"] >= row["last_seen"]:
            row["last_seen"] = event.raw["ts"]
            row["latest_asked"] = str(data.get("asked", ""))
            row["latest_detail"] = str(data.get("detail", ""))
            row["closure"] = str(data.get("closure", ""))
        source = str(data.get("source", ""))
        if source and source not in row["sources"]:
            row["sources"].append(source)

    rows = list(groups.values())
    # Stable two-pass: recency order within an equal count, repetition dominating.
    rows.sort(key=lambda r: str(r["last_seen"]), reverse=True)
    rows.sort(key=lambda r: int(r["count"]), reverse=True)
    return {
        "total": total,
        "distinct": len(rows),
        "rows": rows,
        "boundary": {
            "retry": (
                "The system may attempt these itself, and every attempt is recorded: a "
                "pool window resetting, a live claim expiring, or one recorded "
                "re-dispatch of a loudly failed run."
            ),
            "escalate": (
                "A human must act: silent runs (the measured laundering path), "
                "capabilities that are not implemented, and every refusal the policy "
                "does not recognise. The record is the deliverable — an honest "
                "escalation beats a quiet failure to self-heal."
            ),
            "per_user": (
                "Repetition across several users is not recorded: the trajectory has "
                "one principal and gap events carry no user field. Counts below are "
                "per-installation."
            ),
        },
    }


def _gap(
    question: str, fields: tuple[str, ...], counts: dict[str, int], fix: str
) -> Payload:
    present = {f: n for f, n in counts.items() if n}
    return {
        "question": question,
        "answerable": bool(present),
        "fields_searched": list(fields),
        "fields_found": present,
        "fix": fix,
    }


def build_payload(
    events: list[Event],
    rejections: list[Rejection],
    doctor: Payload,
    beta_result: Payload,
    beta_line: str,
    bypassed: int,
    usage_windows: list[UsageWindow] | None = None,
    usage_note: str | None = None,
) -> Payload:
    """The one JSON contract this command has. The HTML is a rendering of exactly this.

    `doctor` and `beta_result` are passed in already computed and are copied through
    untouched. That is the point: this module cannot disagree with `consil doctor` because
    it never forms an opinion of its own.
    """
    agents: dict[str, Payload] = {}
    edges: dict[tuple[str, str], int] = {}
    artefacts: dict[str, int] = {}
    annotations: dict[str, int] = {}

    for event in events:
        key = _agent_key(event)
        data = event.data
        agent = agents.setdefault(
            key,
            {
                "key": key,
                "runtime_identity": data.get("runtime_identity"),
                "logical_identity": data.get("logical_identity"),
                "actor": event.actor,
                "models": [],
                "harnesses": [],
                "plans": [],
                "roles": [],
                "leases": [],
                "artefacts": [],
                "events": 0,
                "first_seen": event.raw["ts"],
                "last_seen": event.raw["ts"],
                "kinds": [],
                "is_principal": event.actor == data.get("principal"),
                "observed_as": "actor",
            },
        )
        agent["events"] += 1
        agent["last_seen"] = event.raw["ts"]
        if event.raw["ts"] < agent["first_seen"]:
            agent["first_seen"] = event.raw["ts"]
        for field, bucket in (
            ("model", "models"),
            ("harness", "harnesses"),
            ("work_role", "roles"),
            ("write_lease", "leases"),
        ):
            value = data.get(field)
            if isinstance(value, str) and value.strip() and value not in agent[bucket]:
                agent[bucket].append(value)
        if event.kind not in agent["kinds"]:
            agent["kinds"].append(event.kind)

        for artefact in _as_list(data.get("artefacts")) + _as_list(
            data.get("artefact")
        ):
            if not _is_path(artefact):
                annotations[artefact] = annotations.get(artefact, 0) + 1
                continue
            artefacts[artefact] = artefacts.get(artefact, 0) + 1
            if artefact not in agent["artefacts"]:
                agent["artefacts"].append(artefact)
            edges[(key, _artefact_group(artefact))] = (
                edges.get((key, _artefact_group(artefact)), 0) + 1
            )

        # Contributors carry the richest identity in the schema — harness, plan and a
        # declared evidence class — but only on 9 of 108 events, so they widen the roster
        # without being able to carry it.
        contributors = data.get("contributors")
        if isinstance(contributors, list):
            for contributor in contributors:
                if not isinstance(contributor, dict):
                    continue
                runtime = contributor.get("runtime_identity")
                sub_key = (
                    runtime if isinstance(runtime, str) and runtime.strip() else None
                )
                if sub_key is None:
                    continue
                sub = agents.setdefault(
                    sub_key,
                    {
                        "key": sub_key,
                        "runtime_identity": sub_key,
                        "logical_identity": contributor.get("logical_identity"),
                        "actor": event.actor,
                        "models": [],
                        "harnesses": [],
                        "plans": [],
                        "roles": [],
                        "leases": [],
                        "artefacts": [],
                        "events": 0,
                        "first_seen": event.raw["ts"],
                        "last_seen": event.raw["ts"],
                        "kinds": [],
                        "is_principal": False,
                        "observed_as": "contributor",
                    },
                )
                sub["last_seen"] = max(sub["last_seen"], event.raw["ts"])
                for field, bucket in (
                    ("model", "models"),
                    ("harness", "harnesses"),
                    ("plan", "plans"),
                    ("role", "roles"),
                ):
                    value = contributor.get(field)
                    if (
                        isinstance(value, str)
                        and value.strip()
                        and value not in sub[bucket]
                    ):
                        sub[bucket].append(value)

    roster = sorted(agents.values(), key=lambda a: (-int(a["events"]), str(a["key"])))
    _disambiguate(roster)
    stamps = sorted(e.raw["ts"] for e in events)

    spawn_counts = _count_field(events, SPAWN_FIELDS)
    life_counts = _count_field(events, LIFECYCLE_FIELDS)
    read_counts = _count_field(events, READ_FIELDS)
    raci_counts = _count_field(events, RACI_FIELDS)
    item_counts = _count_field(events, WORK_ITEM_FIELDS)

    schema_gaps = [
        _gap(
            "Which agent spawned which?",
            SPAWN_FIELDS,
            spawn_counts,
            "Add `parent_runtime_identity` (or null for a root) and a `session_id` to every "
            "event. Without one of them the roster is a set, and a set has no edges.",
        ),
        _gap(
            "What is running right now?",
            LIFECYCLE_FIELDS,
            life_counts,
            "Emit `agent.started` / `agent.heartbeat` / `agent.finished` events carrying a "
            "status. Every event in the log today is a completion note written after the "
            "fact, so the record has no concept of in-progress.",
        ),
        _gap(
            "What did each agent read?",
            READ_FIELDS,
            read_counts,
            "Add `reads` alongside the existing `artefacts` (which records writes only). "
            "Reads are what make the graph a dependency graph rather than an output list.",
        ),
        _gap(
            "Who was Accountable, Consulted and Informed for a piece of work?",
            RACI_FIELDS + WORK_ITEM_FIELDS,
            {**raci_counts, **item_counts},
            "ADR-0020 attaches the matrix to a decision, not to an agent, so the missing "
            "piece is first a stable work-item identifier on every event, then "
            "`accountable` (exactly one), `consulted` (each declaring its evidence class) "
            "and `informed`.",
        ),
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trajectory": {
            "events": len(events),
            "quarantined": len(rejections),
            "not_written_by_append": bypassed,
            "first_ts": stamps[0] if stamps else None,
            "last_ts": stamps[-1] if stamps else None,
            "distinct_agents": len(roster),
            "distinct_artefacts": len(artefacts),
        },
        "gates": doctor["gates"],
        "routing_orchestration_enabled": doctor["routing_orchestration_enabled"],
        "beta": beta_result,
        "beta_line": beta_line,
        "agents": roster,
        "artefacts": [
            {"path": p, "writes": n}
            for p, n in sorted(artefacts.items(), key=lambda kv: -kv[1])
        ],
        "edges": [
            {"agent": a, "group": g, "writes": n}
            for (a, g), n in sorted(edges.items(), key=lambda kv: -kv[1])
        ],
        "spawn_edges": [],
        "annotations": [
            {"value": v, "count": n}
            for v, n in sorted(annotations.items(), key=lambda kv: -kv[1])
        ],
        "raci": _build_raci(events, roster, raci_counts, item_counts),
        "capability_gaps": _capability_gaps(events),
        "usage": {
            "windows": [w.as_dict() for w in (usage_windows or [])],
            "note": usage_note or "",
            "configured_runtimes": sorted(
                {str(a["key"]) for a in roster if not a["is_principal"]}
            ),
        },
        "schema_gaps": schema_gaps,
        "timeline": [
            {
                "ts": e.raw["ts"],
                "agent": _agent_key(e),
                "kind": e.kind,
                "lease": e.data.get("write_lease"),
                "role": e.data.get("work_role"),
            }
            for e in events
        ],
    }


def _build_raci(
    events: list[Event],
    roster: list[Payload],
    raci_counts: dict[str, int],
    item_counts: dict[str, int],
) -> Payload:
    """RACI as far as the record supports it, and a refusal past that point.

    ADR-0020 replaced RACI with Owner / Contributor / Evidence / Informed / Escalation and
    attached the matrix **to a decision, not to an agent**. That is what makes this
    unanswerable today rather than merely sparse: there is no stable work-item identifier
    on events, so there are no rows to build a matrix over. What can be honestly produced
    is a per-agent role tally and a coverage report saying which of the four letters the
    record can currently support.
    """
    responsible = sum(1 for e in events if e.data.get("work_role"))
    principals = {
        e.data["principal"] for e in events if isinstance(e.data.get("principal"), str)
    }
    consulted = sum(
        1
        for e in events
        if e.data.get("contributors") or e.data.get("auditor") or e.data.get("found_by")
    )
    with_class = sum(1 for e in events if e.data.get("evidence_class"))
    total = len(events) or 1

    letters = [
        {
            "letter": "R",
            "name": "Responsible",
            "meaning": "did the work",
            "derivable": "partial",
            "coverage": responsible,
            "of": len(events),
            "detail": (
                f"`work_role` appears on {responsible} of {len(events)} events, but it is "
                "free text with 28 distinct values on the real trajectory, several of them "
                "compound ('orchestrator and reviewer'). It can be tallied; it cannot be "
                "joined on."
            ),
        },
        {
            "letter": "A",
            "name": "Accountable",
            "meaning": "answerable, exactly one per work item",
            "derivable": "trivial-only",
            "coverage": sum(1 for e in events if e.data.get("principal")),
            "of": len(events),
            "detail": (
                "`principal` is present and constant — "
                + (", ".join(sorted(principals)) or "none")
                + ". So the only accountable party the record knows is the human, for "
                "everything. No event names an accountable *agent* for a piece of work, "
                "which is the cardinality ADR-0020 says must be enforced rather than "
                "conventional."
            ),
        },
        {
            "letter": "C",
            "name": "Consulted",
            "meaning": "two-way, and must declare a distinct class of facts",
            "derivable": "partial",
            "coverage": consulted,
            "of": len(events),
            "detail": (
                f"Something consultation-shaped appears on {consulted} of {len(events)} "
                f"events across three differently-named fields (`contributors`, `auditor`, "
                f"`found_by`), and only {with_class} carry the `evidence_class` ADR-0020 "
                "requires before a participant counts as Evidence at all."
            ),
        },
        {
            "letter": "I",
            "name": "Informed",
            "meaning": "one-way, receives the record",
            "derivable": "no",
            "coverage": 0,
            "of": len(events),
            "detail": (
                "No field records who was notified of a result. Not sparse — absent. "
                "Searched: " + ", ".join(RACI_FIELDS) + "."
            ),
        },
    ]

    rows = [
        {
            "agent": a["key"],
            "logical": a.get("label") or a["logical_identity"],
            "roles": a["roles"],
            "events": a["events"],
            "artefacts": len(a["artefacts"]),
            "accountable": "joe-brown" if not a["is_principal"] else "—",
            "informed": None,
        }
        for a in roster
        if a["events"]
    ]

    return {
        "derivable": False,
        "headline": (
            "A RACI matrix cannot be derived from this trajectory, and none has been drawn."
        ),
        "why": (
            "RACI is a matrix over pieces of work. ADR-0020 says so explicitly — the matrix "
            "attaches to a decision, not to an agent. This trajectory has no stable "
            "work-item identifier on its events ("
            + ", ".join(f"`{f}`: {n}" for f, n in item_counts.items())
            + "), so there are no rows to build it over. What follows is a role tally per "
            "agent, which is a different and weaker thing, plus exactly which of the four "
            "letters the record can support."
        ),
        "letters": letters,
        "rows": rows,
        "coverage_pct": {
            "R": round(100 * responsible / total),
            "A": round(100 * sum(1 for e in events if e.data.get("principal")) / total),
            "C": round(100 * consulted / total),
            "I": 0,
        },
    }


# --------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------


def _e(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _short(value: object, limit: int = 46) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  color-scheme:dark light;
  --ground:#0C0E12; --surface:#14171E; --raised:#1C202A;
  --ink:#F0F2F5; --ink-2:#C4C9D4; --muted:#8B93A5; --rule:#2A2F3D;
  --accent:#E2B340; --accent-soft:#2A2412;
  --pass:#2E9E66; --pass-bg:#11261C;
  --fail:#E05349; --fail-bg:#2D1617;
  --unknown:#DDA136; --unknown-bg:#2B2012;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
  --sans:"Plus Jakarta Sans",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
  --serif:"Syne","Cabinet Grotesk",ui-sans-serif,system-ui,-apple-system,sans-serif;
  --mono:"Space Mono","Fragment Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
}
@media (prefers-color-scheme:light){:root:not([data-theme="dark"]){
  --ground:#F6F7F9; --surface:#FFFFFF; --raised:#ECEEF2;
  --ink:#0C0E12; --ink-2:#3D4453; --muted:#6F778A; --rule:#D6DAE2;
  --accent:#B88714; --accent-soft:#FAF2DE;
  --pass:#23864F; --pass-bg:#E9F6EF;
  --fail:#C53030; --fail-bg:#FDE8E8;
  --unknown:#B57414; --unknown-bg:#FCF4E4;
  --shadow:0 1px 2px rgba(12,14,18,.04),0 8px 20px -8px rgba(12,14,18,.12);
}}
:root[data-theme="dark"]{
  --ground:#0C0E12; --surface:#14171E; --raised:#1C202A;
  --ink:#F0F2F5; --ink-2:#C4C9D4; --muted:#8B93A5; --rule:#2A2F3D;
  --accent:#E2B340; --accent-soft:#2A2412;
  --pass:#2E9E66; --pass-bg:#11261C;
  --fail:#E05349; --fail-bg:#2D1617;
  --unknown:#DDA136; --unknown-bg:#2B2012;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
}
:root[data-theme="light"]{
  --ground:#F6F7F9; --surface:#FFFFFF; --raised:#ECEEF2;
  --ink:#0C0E12; --ink-2:#3D4453; --muted:#6F778A; --rule:#D6DAE2;
  --accent:#B88714; --accent-soft:#FAF2DE;
  --pass:#23864F; --pass-bg:#E9F6EF;
  --fail:#C53030; --fail-bg:#FDE8E8;
  --unknown:#B57414; --unknown-bg:#FCF4E4;
  --shadow:0 1px 2px rgba(12,14,18,.04),0 8px 20px -8px rgba(12,14,18,.12);
}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:32px 24px 96px}
h1,h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:-.011em;margin:0}
h1{font-size:31px;line-height:1.2}
h2{font-size:21px;margin:0 0 4px}
h3{font-size:16px;margin:0 0 2px}
p{margin:0 0 12px;max-width:68ch}
a{color:var(--accent)}
code,.mono{font-family:var(--mono);font-size:.87em;font-variant-numeric:tabular-nums}
td.num,.stat .n{font-variant-numeric:tabular-nums}
.muted{color:var(--muted)}
.eyebrow{font-family:var(--sans);font-size:11px;font-weight:650;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted)}
header.top{border-bottom:1px solid var(--rule);padding-bottom:20px;margin-bottom:24px}
header.top .sub{color:var(--muted);font-size:13.5px;margin-top:6px}

/* ---- verdict: the single sentence that must be true ---- */
.verdict{border:1px solid var(--rule);border-left:4px solid var(--fail);
  background:var(--surface);border-radius:10px;padding:18px 20px;margin:0 0 12px;
  box-shadow:var(--shadow)}
.verdict.is-on{border-left-color:var(--pass)}
.verdict .line{font-family:var(--serif);font-size:20px;line-height:1.35}
.verdict .because{color:var(--ink-2);font-size:14px;margin-top:8px;max-width:70ch}

/* ---- tabs, CSS only ---- */
.tabs>input{position:absolute;opacity:0;pointer-events:none}
.tabbar{display:flex;gap:2px;flex-wrap:wrap;border-bottom:1px solid var(--rule);
  margin:28px 0 20px}
.tabbar label{padding:9px 14px;font-size:13.5px;font-weight:550;color:var(--muted);
  cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;
  border-radius:6px 6px 0 0;transition:color .12s,background .12s}
.tabbar label:hover{color:var(--ink);background:var(--raised)}
.panel{display:none}
#t-fleet:checked~.tabbar label[for=t-fleet],
#t-agents:checked~.tabbar label[for=t-agents],
#t-raci:checked~.tabbar label[for=t-raci],
#t-usage:checked~.tabbar label[for=t-usage],
#t-capgaps:checked~.tabbar label[for=t-capgaps],
#t-gaps:checked~.tabbar label[for=t-gaps]{color:var(--ink);border-bottom-color:var(--accent)}
#t-fleet:checked~.panels>#p-fleet,
#t-agents:checked~.panels>#p-agents,
#t-raci:checked~.panels>#p-raci,
#t-usage:checked~.panels>#p-usage,
#t-capgaps:checked~.panels>#p-capgaps,
#t-gaps:checked~.panels>#p-gaps{display:block}

/* ---- view-style switch inside the agents panel ---- */
.views>input{position:absolute;opacity:0;pointer-events:none}
.segbar{display:inline-flex;background:var(--raised);border:1px solid var(--rule);
  border-radius:8px;padding:3px;gap:2px;margin:0 0 18px}
.segbar label{padding:6px 13px;font-size:13px;font-weight:550;color:var(--muted);
  cursor:pointer;border-radius:6px;transition:background .12s,color .12s}
.segbar label:hover{color:var(--ink)}
.view{display:none}
#v-graph:checked~.segbar label[for=v-graph],
#v-time:checked~.segbar label[for=v-time],
#v-table:checked~.segbar label[for=v-table]{background:var(--surface);color:var(--ink);
  box-shadow:var(--shadow)}
#v-graph:checked~.views-body>#w-graph,
#v-time:checked~.views-body>#w-time,
#v-table:checked~.views-body>#w-table{display:block}

/* ---- cards ---- */
.card{background:var(--surface);border:1px solid var(--rule);border-radius:10px;
  padding:18px 20px;margin:0 0 14px}
.grid{display:grid;gap:14px}
.grid.k3{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.stat{background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:14px 16px}
.stat .n{font-family:var(--mono);font-size:26px;font-weight:600;letter-spacing:-.02em;
  line-height:1.1;display:block}
.stat .k{font-size:12px;color:var(--muted);margin-top:3px}

/* ---- condition rows: state in glyph + border + fill, never colour alone ---- */
.cond{display:grid;grid-template-columns:26px 1fr auto;gap:12px;align-items:start;
  padding:13px 15px;border:1px solid var(--rule);border-left-width:3px;
  border-radius:8px;margin-bottom:8px;background:var(--surface)}
.cond.s-pass{border-left-color:var(--pass);background:var(--pass-bg)}
.cond.s-fail{border-left-color:var(--fail);background:var(--fail-bg)}
.cond.s-unknown{border-left-color:var(--unknown);background:var(--unknown-bg)}
.cond.s-structurally_unsatisfiable{border-left-color:var(--fail);background:var(--fail-bg)}
.glyph{font-family:var(--mono);font-size:15px;font-weight:700;text-align:center;
  line-height:1.5}
.s-pass .glyph{color:var(--pass)} .s-fail .glyph{color:var(--fail)}
.s-unknown .glyph{color:var(--unknown)}
.s-structurally_unsatisfiable .glyph{color:var(--fail)}
.cond .plain{font-size:14.5px;line-height:1.45}
.cond .id{font-family:var(--mono);font-size:11px;color:var(--muted)}
.chip{font-size:11.5px;font-weight:650;padding:3px 9px;border-radius:20px;
  white-space:nowrap;border:1px solid currentColor}
.s-pass .chip{color:var(--pass)} .s-fail .chip{color:var(--fail)}
.s-unknown .chip{color:var(--unknown)}
.s-structurally_unsatisfiable .chip{color:var(--fail)}

/* ---- disclosure: the expert layer ---- */
details{margin-top:10px;border-top:1px dashed var(--rule);padding-top:9px}
summary{cursor:pointer;font-size:12.5px;font-weight:600;color:var(--accent);
  list-style:none;display:inline-flex;align-items:center;gap:6px;
  padding:3px 8px;margin-left:-8px;border-radius:6px}
summary:hover{background:var(--accent-soft)}
summary::-webkit-details-marker{display:none}
summary::before{content:"\\25B8";font-size:10px;transition:transform .15s}
details[open]>summary::before{transform:rotate(90deg)}
details .body{font-size:13.5px;color:var(--ink-2);padding:10px 0 2px}

/* ---- wide content scrolls in its own container, never the page ---- */
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--rule);
  border-radius:10px;background:var(--surface)}
table{border-collapse:collapse;width:100%;min-width:640px;font-size:13.5px}
th,td{text-align:left;padding:9px 13px;border-bottom:1px solid var(--rule);
  vertical-align:top}
th{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  font-weight:650;position:sticky;top:0;background:var(--raised)}
tbody tr:last-child td{border-bottom:none}
td.num{font-family:var(--mono);text-align:right}

/* ---- meters ---- */
.meter{height:7px;border-radius:4px;background:var(--raised);overflow:hidden;
  border:1px solid var(--rule)}
.meter>span{display:block;height:100%;background:var(--accent)}
.meter.hot>span{background:var(--fail)}

/* ---- timeline ---- */
.lane{display:grid;grid-template-columns:190px 1fr;gap:12px;align-items:center;
  padding:5px 0;border-bottom:1px solid var(--rule)}
.lane:last-child{border-bottom:none}
.lane .who{font-size:12px;color:var(--ink-2);overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.track{position:relative;height:22px;background:var(--raised);border-radius:5px;
  min-width:520px}
.track i{position:absolute;top:4px;width:5px;height:14px;border-radius:2px;
  background:var(--accent);transform:translateX(-2px)}
.axis{display:grid;grid-template-columns:190px 1fr;gap:12px;font-size:11px;
  color:var(--muted);padding-top:6px}
.axis .ends{display:flex;justify-content:space-between;min-width:520px}

/* ---- graph ---- */
svg.graph{display:block;min-width:660px}
svg.graph text{font-family:var(--sans);font-size:11px;fill:var(--ink-2)}
svg.graph text.n{font-weight:600;fill:var(--ink)}
svg.graph .node{fill:var(--surface);stroke:var(--accent);stroke-width:1.4}
svg.graph .node.grp{stroke:var(--muted)}
svg.graph .edge{stroke:var(--accent);fill:none;opacity:.4}

.banner{border:1px solid var(--unknown);background:var(--unknown-bg);border-radius:10px;
  padding:15px 18px;margin:0 0 16px}
.banner strong{color:var(--unknown)}
.empty{border:1px dashed var(--rule);border-radius:10px;padding:28px 20px;text-align:center;
  color:var(--muted);font-size:14px;background:var(--surface)}
.letters{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(215px,1fr))}
.letter{border:1px solid var(--rule);border-radius:10px;padding:14px 16px;background:var(--surface)}
.letter .L{font-family:var(--serif);font-size:30px;font-weight:600;line-height:1}
.letter.d-no{border-left:3px solid var(--fail)}
.letter.d-partial{border-left:3px solid var(--unknown)}
.letter.d-trivial-only{border-left:3px solid var(--unknown)}
.tag{font-family:var(--mono);font-size:10.5px;padding:2px 6px;border-radius:4px;
  background:var(--raised);color:var(--muted);border:1px solid var(--rule)}
footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--rule);
  font-size:12.5px;color:var(--muted)}
@media (max-width:640px){
  .wrap{padding:20px 14px 64px}
  h1{font-size:25px}
  .lane,.axis{grid-template-columns:110px 1fr}
}
"""


def _cond_row(condition: Payload) -> str:
    status = str(condition["status"])
    plain = PLAIN_CONDITIONS.get(str(condition["id"]), str(condition["requirement"]))
    return f"""
<div class="cond s-{_e(status)}">
  <div class="glyph" aria-hidden="true">{_e(STATUS_GLYPH.get(status, "?"))}</div>
  <div>
    <div class="plain">{_e(plain)}</div>
    <div class="id">{_e(condition["id"])} &middot; {_e(condition["requirement"])}</div>
    <details>
      <summary>Why this says {_e(PLAIN_STATUS.get(status, status)).lower()}</summary>
      <div class="body">
        <p>{_e(condition["reason"])}</p>
        <p class="muted">Evidence: <span class="mono">{
        _e(", ".join(str(x) for x in condition["evidence"]) or "none")
    }</span></p>
      </div>
    </details>
  </div>
  <div class="chip">{_e(PLAIN_STATUS.get(status, status))}</div>
</div>"""


def _graph_svg(payload: Payload) -> str:
    """Bipartite agent -> artefact-group graph, laid out deterministically in Python.

    There are no spawn edges because the record has none (`schema_gaps`). Drawing an agent
    hierarchy here would mean inventing one, so the graph draws only the relation the log
    actually carries: who wrote into what.
    """
    groups: list[str] = []
    for edge in payload["edges"]:
        if edge["group"] not in groups:
            groups.append(str(edge["group"]))
    groups = groups[:12]
    # Pick the groups first, then only agents that actually reach one of them. Selecting
    # agents independently drew nodes whose every edge pointed at a group outside the cut,
    # so they appeared in the graph as agents that had written nothing.
    reaching = {str(e["agent"]) for e in payload["edges"] if str(e["group"]) in groups}
    agents = [a for a in payload["agents"] if str(a["key"]) in reaching][:12]
    if not agents or not groups:
        return '<div class="empty">No write edges in the trajectory yet.</div>'

    keys = [str(a["key"]) for a in agents]
    row, top = 38, 44
    height = max(len(agents), len(groups)) * row + top + 30
    lx, rx = 250, 430
    ay = {k: top + i * row for i, k in enumerate(keys)}
    gy = {g: top + i * row for i, g in enumerate(groups)}
    maxw = max((int(e["writes"]) for e in payload["edges"]), default=1)

    parts = [
        f'<svg class="graph" viewBox="0 0 700 {height}" height="{height}" '
        f'role="img" aria-label="Agents and the directories they wrote to">',
        f'<text x="{lx}" y="22" text-anchor="end" class="n">Agent</text>',
        f'<text x="{rx}" y="22" class="n">Wrote into</text>',
    ]
    for edge in payload["edges"]:
        a, g = str(edge["agent"]), str(edge["group"])
        if a not in ay or g not in gy:
            continue
        y1, y2 = ay[a] + 5, gy[g] + 5
        width = 1 + 2.5 * (int(edge["writes"]) / maxw)
        parts.append(
            f'<path class="edge" d="M{lx + 8} {y1} C{lx + 80} {y1} {rx - 80} {y2} '
            f'{rx - 8} {y2}" stroke-width="{width:.2f}"/>'
        )
    for a in agents:
        k = str(a["key"])
        y = ay[k]
        parts.append(f'<circle class="node" cx="{lx}" cy="{y + 5}" r="4.5"/>')
        parts.append(
            f'<text x="{lx - 12}" y="{y + 9}" text-anchor="end">'
            f"{_e(_short(a.get('label') or a['logical_identity'] or k, 34))}</text>"
        )
    for g in groups:
        y = gy[g]
        parts.append(f'<circle class="node grp" cx="{rx}" cy="{y + 5}" r="4.5"/>')
        parts.append(f'<text x="{rx + 12}" y="{y + 9}" class="mono">{_e(g)}</text>')
    parts.append("</svg>")
    return '<div class="scroll">' + "".join(parts) + "</div>"


def _timeline(payload: Payload) -> str:
    rows = payload["timeline"]
    first, last = payload["trajectory"]["first_ts"], payload["trajectory"]["last_ts"]
    if not rows or not first or not last:
        return '<div class="empty">No events to place on a timeline.</div>'
    try:
        t0 = datetime.fromisoformat(str(first)).timestamp()
        t1 = datetime.fromisoformat(str(last)).timestamp()
    except ValueError:
        return '<div class="empty">Timestamps could not be placed on a scale.</div>'
    span = (t1 - t0) or 1.0

    lanes: dict[str, list[float]] = {}
    for row in rows:
        try:
            at = datetime.fromisoformat(str(row["ts"])).timestamp()
        except ValueError:
            continue
        lanes.setdefault(str(row["agent"]), []).append(100 * (at - t0) / span)

    order = sorted(lanes, key=lambda k: -len(lanes[k]))
    out = ['<div class="scroll" style="padding:14px 16px">']
    for key in order:
        marks = "".join(f'<i style="left:{p:.3f}%"></i>' for p in lanes[key])
        out.append(
            f'<div class="lane"><div class="who" title="{_e(key)}">{_e(_short(key, 30))}</div>'
            f'<div class="track">{marks}</div></div>'
        )
    out.append(
        f'<div class="axis"><div></div><div class="ends"><span>{_e(first)}</span>'
        f"<span>{_e(last)}</span></div></div></div>"
    )
    return "".join(out)


def _agent_table(payload: Payload) -> str:
    if not payload["agents"]:
        return '<div class="empty">No agents in the trajectory.</div>'
    rows = []
    for a in payload["agents"]:
        rows.append(
            "<tr>"
            f"<td><strong>{_e(a.get('label') or a['key'])}</strong>"
            f'<div class="muted mono" style="font-size:11px">{_e(_short(a["key"], 44))}</div></td>'
            f"<td>{_e(', '.join(str(m) for m in a['models']) or '—')}</td>"
            f"<td>{_e(_short(', '.join(str(r) for r in a['roles']) or '—', 52))}</td>"
            f'<td class="num">{_e(a["events"])}</td>'
            f'<td class="num">{_e(len(a["artefacts"]))}</td>'
            f'<td class="mono" style="font-size:11.5px">{_e(a["last_seen"])}</td>'
            "</tr>"
        )
    return (
        '<div class="scroll"><table><thead><tr><th>Agent</th><th>Model</th>'
        "<th>Roles recorded</th><th>Events</th><th>Files</th><th>Last seen</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
    )


def _usage_panel(payload: Payload) -> str:
    usage = payload["usage"]
    windows = usage["windows"]
    head = (
        "<h2>Usage, subscriptions and limits</h2>"
        '<p class="muted">Every configured runtime and what is known about its consumption, '
        "in one place.</p>"
    )
    if not windows:
        configured = usage["configured_runtimes"]
        listed = "".join(
            f'<tr><td class="mono">{_e(c)}</td><td class="muted">not connected</td>'
            f'<td class="muted">—</td><td class="muted">—</td></tr>'
            for c in configured
        )
        return (
            head
            + '<div class="banner"><strong>No usage data.</strong> '
            + _e(usage["note"])
            + " The usage and limits collector is a separate component; this surface consumes "
            "its output and does not gather any itself, so nothing here reads a credential "
            "or opens a network connection.</div>"
            + (
                '<div class="scroll"><table><thead><tr><th>Configured runtime</th>'
                "<th>Usage</th><th>Ceiling</th><th>Resets</th></tr></thead><tbody>"
                + listed
                + "</tbody></table></div>"
                if configured
                else '<div class="empty">No runtimes observed in the trajectory.</div>'
            )
        )
    rows = []
    for w in windows:
        frac = w["fraction"]
        bar = ""
        if isinstance(frac, float):
            hot = " hot" if frac >= 0.8 else ""
            bar = (
                f'<div class="meter{hot}"><span style="width:{frac * 100:.1f}%"></span></div>'
                f'<div class="muted" style="font-size:11px;margin-top:3px">'
                f"{frac * 100:.0f}% of ceiling</div>"
            )
        rows.append(
            "<tr>"
            f'<td><strong>{_e(w["provider"])}</strong><div class="muted" '
            f'style="font-size:11.5px">{_e(w["plan"])} &middot; {_e(w["window"])}</div></td>'
            f'<td class="num">{_e(w["used"])} {_e(w["unit"])}</td>'
            f'<td class="num">{_e(w["ceiling"] or "no ceiling recorded")}</td>'
            f'<td style="min-width:170px">{bar or "<span class=muted>—</span>"}</td>'
            f'<td class="mono" style="font-size:11.5px">{_e(w["resets_at"] or "not recorded")}</td>'
            "</tr>"
        )
    return (
        head + '<div class="scroll"><table><thead><tr><th>Provider</th><th>Used</th>'
        "<th>Ceiling</th><th>Headroom</th><th>Resets</th></tr></thead><tbody>"
        + "".join(rows)
        + f'</tbody></table></div><p class="muted" style="margin-top:10px">{_e(usage["note"])}</p>'
    )


def _raci_panel(payload: Payload) -> str:
    raci = payload["raci"]
    letters = "".join(
        f'<div class="letter d-{_e(letter["derivable"])}">'
        f'<div class="L">{_e(letter["letter"])}</div>'
        f"<h3>{_e(letter['name'])}</h3>"
        f'<p class="muted" style="font-size:12.5px;margin:2px 0 8px">{_e(letter["meaning"])}</p>'
        f'<span class="tag">{_e(letter["coverage"])} / {_e(letter["of"])} events</span>'
        f"<details><summary>What the record has</summary>"
        f'<div class="body">{_e(letter["detail"])}</div></details></div>'
        for letter in raci["letters"]
    )
    rows = "".join(
        "<tr>"
        f"<td><strong>{_e(r['logical'] or r['agent'])}</strong></td>"
        f"<td>{_e(_short(', '.join(str(x) for x in r['roles']) or 'not recorded', 54))}</td>"
        f"<td>{_e(r['accountable'])}</td>"
        f'<td class="muted">not recorded</td>'
        f'<td class="num">{_e(r["events"])}</td>'
        "</tr>"
        for r in raci["rows"]
    )
    return (
        "<h2>RACI</h2>"
        f'<div class="banner"><strong>{_e(raci["headline"])}</strong><br>'
        f'<span style="font-size:13.5px">{_e(raci["why"])}</span></div>'
        f'<div class="letters">{letters}</div>'
        '<h3 style="margin:26px 0 8px">Role tally per agent</h3>'
        '<p class="muted" style="font-size:13.5px">This is not a RACI matrix. It is what a '
        "matrix degrades to when the work items it should be indexed by are not recorded: a "
        "count of the roles each agent has been described as holding, across all work.</p>"
        + (
            '<div class="scroll"><table><thead><tr><th>Agent</th><th>Roles recorded (R)</th>'
            "<th>Accountable (A)</th><th>Informed (I)</th><th>Events</th></tr></thead>"
            "<tbody>" + rows + "</tbody></table></div>"
            if rows
            else '<div class="empty">No agents in the trajectory.</div>'
        )
    )


def _capability_gaps_panel(payload: Payload) -> str:
    gaps = payload["capability_gaps"]
    head = (
        "<h2>Capability gaps</h2>"
        "<p>What users asked for that the harness could not do, recorded at the boundary "
        "that detected it. Ranked by repetition: the same gap hit again outranks a novel "
        "one. Each names what would close it and which side of the self-healing boundary "
        "it sits on.</p>"
    )
    boundary = (
        '<div class="card" style="border-left:3px solid var(--accent)">'
        "<h3>The self-healing boundary</h3>"
        f'<p style="font-size:13.5px"><strong>May retry:</strong> {_e(gaps["boundary"]["retry"])}</p>'
        f'<p style="font-size:13.5px"><strong>Must escalate:</strong> {_e(gaps["boundary"]["escalate"])}</p>'
        f'<p class="muted" style="font-size:12.5px">{_e(gaps["boundary"]["per_user"])}</p>'
        "</div>"
    )
    if not gaps["rows"]:
        return (
            head
            + boundary
            + '<div class="empty">No capability gaps recorded. That is an absence of '
            "records, not proof none occurred — a gap is only visible where a boundary "
            "already detects it.</div>"
        )
    rows = []
    for row in gaps["rows"]:
        closure = str(row["closure"])
        chip_colour = "--unknown" if closure == "retry" else "--fail"
        rows.append(
            "<tr>"
            f'<td class="num"><strong>{_e(row["count"])}</strong></td>'
            f'<td><span class="chip" style="color:var(--fail)">{_e(row["failure"])}</span></td>'
            f"<td>{_e(row['attempted'])}</td>"
            f"<td>{_e(_short(row['repair'], 72))}</td>"
            f'<td><span class="chip" style="color:var({chip_colour})">{_e(closure)}</span></td>'
            f'<td class="mono" style="font-size:11.5px">{_e(row["last_seen"])}</td>'
            f"<td>{_e(_short(row['latest_detail'], 88))}"
            f"<details><summary>latest ask</summary>"
            f'<div class="body mono" style="font-size:12px">{_e(_short(row["latest_asked"], 400))}</div>'
            f"</details></td>"
            "</tr>"
        )
    return (
        head
        + boundary
        + f'<p class="muted" style="font-size:13px">{_e(gaps["total"])} gap event(s), '
        + _e(gaps["distinct"])
        + " distinct gap(s). The full record is the trajectory; this view ranks and "
        "points.</p>"
        + '<div class="scroll"><table><thead><tr><th>Times</th><th>Failure</th>'
        "<th>Attempted</th><th>What closes it</th><th>Closure</th><th>Last seen</th>"
        "<th>Latest detail</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def _gaps_panel(payload: Payload) -> str:
    cards = []
    for gap in payload["schema_gaps"]:
        found = gap["fields_found"]
        state = "answerable" if gap["answerable"] else "not recorded"
        cards.append(
            f'<div class="card" style="border-left:3px solid var({"--unknown" if gap["answerable"] else "--fail"})">'
            f"<h3>{_e(gap['question'])}</h3>"
            f'<p><span class="chip" style="color:var({"--unknown" if gap["answerable"] else "--fail"})">'
            f"{_e(state)}</span></p>"
            f'<p style="font-size:13.5px">{_e(gap["fix"])}</p>'
            f'<p class="muted" style="font-size:12px">Searched: <span class="mono">'
            f"{_e(', '.join(str(f) for f in gap['fields_searched']))}</span> &middot; found: "
            f'<span class="mono">{_e(json.dumps(found) if found else "none")}</span></p></div>'
        )
    notes = payload["annotations"]
    tail = ""
    if notes:
        rows = "".join(
            f'<tr><td class="mono">{_e(_short(n["value"], 88))}</td>'
            f'<td class="num">{_e(n["count"])}</td></tr>'
            for n in notes
        )
        tail = (
            '<h3 style="margin:26px 0 8px">Values recorded as artefacts that are not files</h3>'
            f'<p style="font-size:13.5px">{len(notes)} of the values in the `artefacts` field '
            "are not file paths — commit identifiers and free prose. They are excluded from "
            "the graph and the file count, because drawing them as directories would invent "
            "a fact, and listed here, because dropping them silently would hide one. The fix "
            "is to type the field rather than to clean the data: paths in `artefacts`, "
            "everything else in a field of its own.</p>"
            '<div class="scroll"><table><thead><tr><th>Value</th><th>Times</th></tr></thead>'
            f"<tbody>{rows}</tbody></table></div>"
        )
    return (
        "<h2>What this record cannot tell you</h2>"
        "<p>Each question below was asked of the trajectory and could not be answered from "
        "it. They are listed rather than filled in. Every one names the exact field that "
        "would close it, so the fix is a schema change of known size rather than an "
        "open question.</p>" + "".join(cards) + tail
    )


def render_html(payload: Payload) -> str:
    """One self-contained page. No script tag, no external URL, no font download."""
    traj = payload["trajectory"]
    beta = payload["beta"]
    enabled = bool(payload["routing_orchestration_enabled"])

    conditions = [c for gate in payload["gates"].values() for c in gate["conditions"]]
    failing = [c for c in conditions if c["status"] != "pass"]
    n_pass = len(conditions) - len(failing)

    if enabled:
        line = "Consilient is routing and orchestrating work."
        because = (
            f"All {len(conditions)} readiness checks pass. It will select models and act on "
            "its own judgement within the limits recorded below."
        )
    else:
        line = "Consilient is watching, not acting."
        because = (
            f"{len(failing)} of {len(conditions)} readiness checks have not passed "
            f"({n_pass} have). Until every one passes, it records what happens and computes "
            "its error rate — it never picks a model, approves work or blocks anything. "
            "That is a deliberate stop, not a fault."
        )

    if beta["verdict"] == "measured":
        b_head = f"{float(beta['point']) * 100:.1f}%"
        b_plain = (
            "of the work a human rejected, the automatic checks had approved. That is the "
            "number this whole project exists to drive down."
        )
    else:
        b_head = "Not yet measured"
        b_plain = (
            f"This needs {30 - int(beta['n_rejected'])} more pieces of work that a human "
            f"looked at and rejected; there have been {int(beta['n_rejected'])} so far. "
            "Until then nobody — including Consilient — knows how far its checks can be "
            "trusted, and it says so rather than guessing."
        )

    gate_blocks = "".join(
        f'<h3 style="margin:20px 0 9px">Gate {_e(name)} '
        f'<span class="muted" style="font-weight:400;font-size:13px">'
        f"&middot; {_e(str(gate['status']).replace('_', ' '))}</span></h3>"
        + "".join(_cond_row(c) for c in gate["conditions"])
        for name, gate in payload["gates"].items()
    )

    stats = "".join(
        f'<div class="stat"><span class="n">{_e(v)}</span><div class="k">{_e(k)}</div></div>'
        for k, v in (
            ("events recorded", traj["events"]),
            ("agents seen", traj["distinct_agents"]),
            ("files written", traj["distinct_artefacts"]),
            ("lines the log refused", traj["quarantined"]),
        )
    )

    return f"""<title>Consilient Observatory</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{CSS}</style>
<div class="wrap">
<header class="top">
  <div class="eyebrow">Consilient &middot; observability</div>
  <h1>What is happening, and can it be trusted?</h1>
  <div class="sub">Rendered from the append-only trajectory and its projection.
    {_e(traj["events"])} events, {_e(traj["first_ts"] or "—")} to {_e(traj["last_ts"] or "—")}.
    Generated {_e(payload["generated_at"])}.</div>
</header>

<div class="verdict{" is-on" if enabled else ""}">
  <div class="line">{_e(line)}</div>
  <div class="because">{_e(because)}</div>
</div>

<div class="card" style="border-left:3px solid var(--accent)">
  <div class="eyebrow"><span style="text-transform:none;font-size:13px">&beta;</span> &middot; how often the checks approve bad work</div>
  <div style="font-family:var(--serif);font-size:25px;margin:5px 0 4px">{_e(b_head)}</div>
  <p style="font-size:14px;margin:0">{_e(b_plain)}</p>
  <details>
    <summary>The statistical detail</summary>
    <div class="body">
      <p class="mono">{_e(payload["beta_line"])}</p>
      <p>{_e(beta["caveat"])}</p>
      <p class="muted">Sample: {_e(beta["n_false_accept"])} false accepts over
        {_e(beta["n_rejected"])} human rejections. Lower bound on joint error claimed:
        {_e("yes" if beta["lower_bound_on_joint_error"] else "no")}.
        Lines the log refused: {_e(traj["quarantined"])}; lines not written through
        append(): {_e(traj["not_written_by_append"])}.</p>
    </div>
  </details>
</div>

<div class="tabs">
  <input type="radio" name="tab" id="t-fleet" checked>
  <input type="radio" name="tab" id="t-agents">
  <input type="radio" name="tab" id="t-raci">
  <input type="radio" name="tab" id="t-usage">
  <input type="radio" name="tab" id="t-capgaps">
  <input type="radio" name="tab" id="t-gaps">
  <div class="tabbar">
    <label for="t-fleet">Readiness</label>
    <label for="t-agents">Agents</label>
    <label for="t-raci">RACI</label>
    <label for="t-usage">Usage &amp; limits</label>
    <label for="t-capgaps">Capability gaps</label>
    <label for="t-gaps">Blind spots</label>
  </div>
  <div class="panels">

    <section class="panel" id="p-fleet">
      <div class="grid k3" style="margin-bottom:22px">{stats}</div>
      <h2>The seven readiness checks</h2>
      <p>Each must pass before Consilient is allowed to route work by itself. They are shown
        as they are, including the ones that fail.</p>
      {gate_blocks}
    </section>

    <section class="panel" id="p-agents">
      <h2>Agents</h2>
      <p>Who did what, from the record. The same run, three ways.</p>
      <div class="banner" style="border-color:var(--rule);background:var(--raised)">
        <strong>Live state is not recorded.</strong> Every event in this log is a completion
        note written after the fact, so &ldquo;last seen&rdquo; is the honest strongest claim
        &mdash; not &ldquo;running&rdquo;. Spawn relationships are not recorded either, so
        the graph shows what each agent <em>wrote</em>, which the log does carry, rather than
        an invented hierarchy. See <em>Blind spots</em>.
      </div>
      <div class="views">
        <input type="radio" name="view" id="v-graph" checked>
        <input type="radio" name="view" id="v-time">
        <input type="radio" name="view" id="v-table">
        <div class="segbar">
          <label for="v-graph">Graph</label>
          <label for="v-time">Timeline</label>
          <label for="v-table">Table</label>
        </div>
        <div class="views-body">
          <div class="view" id="w-graph">{_graph_svg(payload)}</div>
          <div class="view" id="w-time">{_timeline(payload)}</div>
          <div class="view" id="w-table">{_agent_table(payload)}</div>
        </div>
      </div>
    </section>

    <section class="panel" id="p-raci">{_raci_panel(payload)}</section>
    <section class="panel" id="p-usage">{_usage_panel(payload)}</section>
    <section class="panel" id="p-capgaps">{_capability_gaps_panel(payload)}</section>
    <section class="panel" id="p-gaps">{_gaps_panel(payload)}</section>
  </div>
</div>

<footer>
  A rendering of the record, never a second record (ADR-0053, ADR-0035 &sect;1). Every figure
  here is produced by <span class="mono">consil doctor</span> and
  <span class="mono">consil beta</span> and copied through unchanged; this page performs no
  arithmetic of its own. Plain-language readings of the checks are
  <span class="mono">[asserted]</span> by the author of ADR-0053.
</footer>
</div>
"""

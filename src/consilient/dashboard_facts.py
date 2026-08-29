"""What can honestly be read out of the trajectory, and where the reading stops.

Every helper here answers one question of the record and returns a named gap when the
record cannot answer it. `_count_field` is the mechanism the whole no-invented-graph
rule rests on: it counts how often a field actually appears, so `_gap` can report which
fields were searched and which were found, and a gap closes itself the moment events
start carrying the field.

`_is_path` is the guard that keeps commit identifiers and prose out of the artefact
graph while still reporting them to the reader — excluded from the graph, but not lost.
`_disambiguate` does the same job for agent labels.

`_capability_gaps` groups by the policy-normalised triple (failure, repair, attempted)
rather than by free text, because repetition is the strongest signal a gap carries and
grouping by wording would split one gap into several.

`_build_raci` sits here rather than with the renderer for the same reason: it is RACI as
far as the record supports it, and a refusal past that point. The refusal is a fact
about the trajectory, not a presentation choice."""

import re
from .events import CAPABILITY_GAP_KIND, Event
from .dashboard_types import (
    Payload,
    RACI_FIELDS,
)

from .dashboard_css import (
    CSS,
)


__all__ = [
    "CSS",
    "Payload",
    "RACI_FIELDS",
]


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

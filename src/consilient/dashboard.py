"""The observability surface (ADR-0053). A rendering of the record, never a second
record.

`consil dashboard` writes one self-contained HTML file. There is no server, no port, no
auth, no bundler and no frontend dependency — ADR-0007's objections to a local web
server all survive, and this form costs none of them. There is also no JavaScript: view
switching uses CSS `:checked` sibling selectors over radio inputs, and expert detail
uses `<details>`. Both are platform features, so the page has no runtime to break.

Two rules govern everything in this family.

**Never recompute an authoritative number.** Beta and the gate conditions arrive as the
exact result dicts `cmd_beta` and `cmd_doctor` produced, and the beta line is
`Beta.render()`'s own output. This module may lay them out; it may not do arithmetic on
them. V0-14 says human output is a rendering of one result rather than a second
semantics, and a dashboard that computed its own beta would be a second semantics
wearing the same name. V0-30 tests it.

**Never render an absence as a value.** The trajectory does not record who spawned whom,
what an agent read, whether it is still running, or who was informed of a result. Those
are reported as named gaps in `schema_gaps`, in the place the answer would have gone. An
invented graph is worse than no graph, and it is the precise failure this project exists
to measure.

What remains here is the pair of entry points the rest of the repository calls:
`build_payload`, which turns a trajectory into the one payload, and `render_html`, which
turns that payload into the one page. Neither is called by anything else inside the
family — measured, both have no in-family callers — which is why the split could put
them here without dragging the helpers back with them. The helpers live in
`dashboard_types`, `dashboard_cards`, `dashboard_usage`, `dashboard_facts`,
`dashboard_css` and `dashboard_html`, and none of those imports this module.

`__all__` is explicit rather than incidental: `cli.py` and three test modules import
from this path, strict mypy does not re-export implicitly, and a name that quietly
stopped being importable here would be a broken caller found late.
"""

from __future__ import annotations
from datetime import datetime, timezone
from .events import Event, Rejection
from .dashboard_types import (
    LIFECYCLE_FIELDS,
    Payload,
    RACI_FIELDS,
    READ_FIELDS,
    SPAWN_FIELDS,
    WORK_ITEM_FIELDS,
)

from .dashboard_cards import (
    CardRefusal,
    ProposalCardFacts,
    _promotion_card_payload,
    project_proposal_card,
    render_proposal_card,
)

from .dashboard_css import (
    CSS,
)

from .dashboard_facts import (
    _agent_key,
    _artefact_group,
    _as_list,
    _build_raci,
    _capability_gaps,
    _count_field,
    _disambiguate,
    _gap,
    _is_path,
)

from .dashboard_render import (
    render_html,
)


from .dashboard_usage import (
    UsageWindow,
    read_usage,
)

__all__ = [
    "CSS",
    "CardRefusal",
    "LIFECYCLE_FIELDS",
    "Payload",
    "ProposalCardFacts",
    "RACI_FIELDS",
    "READ_FIELDS",
    "SPAWN_FIELDS",
    "UsageWindow",
    "WORK_ITEM_FIELDS",
    "_agent_key",
    "_artefact_group",
    "_as_list",
    "_build_raci",
    "_capability_gaps",
    "_count_field",
    "_disambiguate",
    "_gap",
    "_is_path",
    "_promotion_card_payload",
    "build_payload",
    "project_proposal_card",
    "read_usage",
    "render_html",
    "render_proposal_card",
]


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
        "promotion_card": _promotion_card_payload(events),
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

"""The HTML fragments, and the words the page says.

Everything here escapes at emit — `_e` is the single boundary, and every fragment goes
through it rather than trusting a value that reached it from the trajectory.

The plain-language strings live here rather than with the payload because they are how
the page reads, not what it knows. They are [asserted] throughout — this author's
readings of each condition, written for the accessibility requirement Joe set on 21
August 2026 ("average plus intelligence"). They restate; they never soften. A failing
condition reads as failing in both registers. ADR-0055 is being written concurrently on
which concepts a competent non-expert actually needs, and its answer supersedes these
strings if the two disagree. Form as well as colour: each state carries a distinct
glyph, so the page is readable in greyscale and by anyone who does not distinguish red
from green.

`_rejection_reason_list` renders parser and relational refusals as reasons rather than
as a pooled integer (T12) — a count would tell the reader that something was refused
while withholding the only part they could act on.

Each panel takes a payload and returns a fragment. None of them decides anything; the
deciding was done before the payload was built."""

from __future__ import annotations
import html
import json
from datetime import datetime
from .dashboard_types import (
    Payload,
)

from .dashboard_css import (
    CSS,
)


__all__ = [
    "CSS",
    "PLAIN_CONDITIONS",
    "PLAIN_STATUS",
    "Payload",
    "STATUS_GLYPH",
]

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

# --------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------


def _e(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _rejection_reason_list(beta: Payload) -> str:
    """Parser and relational refusals as reasons, not a pooled integer (T12)."""
    rows: list[object] = []
    rows.extend(beta.get("rejection_reasons") or [])
    rows.extend(beta.get("relational_quarantine") or [])
    if not rows:
        return ""
    items = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        items.append(
            '<li class="mono">'
            f"{_e(row.get('path'))}:{_e(row.get('line'))} {_e(row.get('reason'))}"
            "</li>"
        )
    if not items:
        return ""
    return "<p>Refusal reasons</p><ul>" + "".join(items) + "</ul>"


def _short(value: object, limit: int = 46) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


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


def _promotion_card_panel(payload: Payload) -> str:
    card = payload.get("promotion_card")
    if not isinstance(card, dict):
        return ""
    if card.get("refused") is True:
        reason = _e(card.get("reason") or "missing_bound_fact")
        return (
            '<div class="card">'
            '<div class="eyebrow">Promotion proposal</div>'
            f'<p class="muted">No owner card. {reason}.</p>'
            "</div>"
        )
    text = card.get("text")
    if not isinstance(text, str) or not text.strip():
        return ""
    sentences = "".join(f"<p>{_e(sentence)}</p>" for sentence in text.split("\n"))
    return (
        '<div class="card" style="border-left:3px solid var(--accent)">'
        '<div class="eyebrow">Promotion proposal</div>'
        '<p class="muted">Four sealed sentences. Approve or refuse the exact candidate; '
        "a summary, family or future tag is ineligible.</p>"
        f"{sentences}"
        "</div>"
    )

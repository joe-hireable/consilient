"""Turning a built payload into the page.

Separated from build_payload on 28 August 2026 for a plain reason: with both in one file
the module came to 524 lines against a 500-line cap, and they are in any case two
subjects -- one gathers the facts, the other decides how they look. The gathering half
keeps the module name because every caller asks dashboard for a payload; rendering is
re-exported from there, so nothing outside this family notices the move."""

from .dashboard_types import (
    Payload,
)

from .dashboard_css import (
    CSS,
)

from .dashboard_html import (
    _agent_table,
    _capability_gaps_panel,
    _cond_row,
    _e,
    _gaps_panel,
    _graph_svg,
    _promotion_card_panel,
    _raci_panel,
    _rejection_reason_list,
    _timeline,
    _usage_panel,
)


__all__ = [
    "CSS",
    "Payload",
    "_agent_table",
    "_capability_gaps_panel",
    "_cond_row",
    "_e",
    "_gaps_panel",
    "_graph_svg",
    "_promotion_card_panel",
    "_raci_panel",
    "_rejection_reason_list",
    "_timeline",
    "_usage_panel",
    "render_html",
]


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

{_promotion_card_panel(payload)}

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
      {_rejection_reason_list(beta)}
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

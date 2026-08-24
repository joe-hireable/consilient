"""Render the build board from a snapshot. Regenerate, then republish to the same URL.

A published page cannot reach this machine, so there is no live feed: the board is a snapshot
and it says so, prominently and continuously. A dashboard that looks live while showing stale
numbers is the exact failure this repository keeps measuring, so the age is rendered as a
running counter rather than a timestamp somebody has to read carefully.
"""

from __future__ import annotations

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / ".harness" / "board-snapshot.json"
OUT = ROOT / ".harness" / "build-board.html"

STATE_ORDER = ["running", "conflict", "ready", "blocked", "done"]
STATE_LABEL = {
    "running": "In flight",
    "conflict": "Cannot merge",
    "ready": "Queued",
    "blocked": "Blocked",
    "done": "Done",
}


def esc(value: object) -> str:
    """Escape for HTML, and strip replacement characters.

    Driver logs are written through a cp1252 console on this machine, so an em dash arrives as
    U+FFFD. Publishing rejects unpaired/invalid sequences outright, and a lone replacement
    character in a log line is not worth failing a deploy over.
    """
    text = str(value).replace(chr(0xFFFD), "-")
    keep = (chr(10), chr(9))
    text = "".join(c for c in text if c in keep or ord(c) >= 32)
    return html.escape(text, quote=True)


def build() -> str:
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    units = snap["units"]
    counts = snap["counts"]
    total = snap["total"]
    done = counts.get("done", 0)
    verified = snap["verified"]
    gates = snap["gates"]
    overall = snap.get("overall", {})
    pct = round(done * 100 / total) if total else 0
    vpct = round(verified * 100 / done) if done else 0

    gatekeepers = sorted(
        [u for u in units if u["state"] != "done" and u["gates"] > 0],
        key=lambda u: -u["gates"],
    )[:10]
    max_gates = max([g["gates"] for g in gatekeepers], default=1)

    arms: dict[str, dict[str, int]] = {}
    for u in units:
        if u["state"] == "running" and u["arm"]:
            a = arms.setdefault(u["arm"], {"running": 0, "done": 0})
            a["running"] += 1
    for u in units:
        if u["state"] == "done" and u.get("built_by"):
            arms.setdefault(u["built_by"], {"running": 0, "done": 0})["done"] += 1

    rows = []
    for u in sorted(
        units, key=lambda x: (STATE_ORDER.index(x["state"]), -x["gates"], x["id"])
    ):
        detail = []
        if u["state"] == "running" and u["elapsed"] is not None:
            frac = min(100, round(u["elapsed"] * 100 / max(1, u["leash"] or 60)))
            detail.append(
                f'<div class="leash"><div class="leash-fill" style="width:{frac}%"></div></div>'
                f'<span class="mono dim">{u["elapsed"]}m of {u["leash"]}m leash</span>'
            )
        if u["out_status"] and u["out_status"] != "running":
            cls = "ok" if u["out_status"] == "ok" else "bad"
            detail.append(f'<span class="pill {cls}">{esc(u["out_status"])}</span>')
        if u["undone"]:
            detail.append(
                '<span class="dim">waits on</span> '
                + " ".join(f'<span class="dep">{esc(d)}</span>' for d in u["undone"])
            )
        if u["reason"]:
            detail.append(f'<div class="reason">{esc(u["reason"])}</div>')
        claims = "".join(
            f'<span class="claim">{esc(c.split("/")[-1])}</span>'
            for c in u.get("claims", [])
        )
        badge = (
            '<span class="vfy" title="cross-family verified">✓ verified</span>'
            if u["verified"]
            else ""
        )
        gate_badge = (
            f'<span class="gates" title="units blocked behind this one">{u["gates"]} downstream</span>'
            if u["gates"]
            else ""
        )
        rows.append(f"""<article class="unit s-{u["state"]}" data-state="{u["state"]}" data-id="{esc(u["id"])}" data-text="{esc((u["id"] + " " + u["title"]).lower())}">
  <header>
    <span class="uid mono">{esc(u["id"])}</span>
    <h3>{esc(u["title"])}</h3>
    <span class="arm mono">{esc(u["arm"] or "—")}</span>
  </header>
  <div class="meta">{badge}{gate_badge}{claims}</div>
  <div class="detail">{"".join(detail)}</div>
</article>""")

    gate_cards = "".join(
        f"""<div class="gate g-{g["status"].lower()}">
  <span class="gid mono">{esc(g["id"])}</span>
  <span class="gstatus">{esc(g["status"])}</span>
  <p>{esc(g["text"])}</p>
</div>"""
        for g in gates
    )

    keeper_rows = "".join(
        f"""<div class="keeper">
  <span class="mono kid">{esc(k["id"])}</span>
  <div class="bar"><div class="bar-fill" style="width:{round(k["gates"] * 100 / max_gates)}%"></div></div>
  <span class="mono kn">{k["gates"]}</span>
  <span class="kt">{esc(k["title"])}</span>
  <span class="pill s-{k["state"]}">{STATE_LABEL[k["state"]]}</span>
</div>"""
        for k in gatekeepers
    )

    arm_cards = "".join(
        f"""<div class="arm-card">
  <span class="arm-name">{esc(name)}</span>
  <span class="arm-run mono">{v["running"]}</span><span class="arm-lbl">in flight</span>
  <span class="arm-done mono">{v["done"]}</span><span class="arm-lbl">built</span>
</div>"""
        for name, v in sorted(arms.items(), key=lambda kv: -kv[1]["running"])
    )

    log_lines = "".join(
        f'<div class="logline">{esc(line)}</div>' for line in snap.get("log", [])[-40:]
    )

    counters = "".join(
        f"""<button class="chip c-{s}" data-filter="{s}">
  <span class="cn mono">{counts.get(s, 0)}</span>{STATE_LABEL[s]}</button>"""
        for s in STATE_ORDER
    )

    return f"""<title>Consilient Build Board</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --ink:#191b23; --ink-2:#4a4f60; --ink-3:#767d92;
  --ground:#f6f5f2; --panel:#fffefc; --line:#e2e0da;
  --iris:#4f46c9; --iris-soft:#eceafb;
  --run:#a8620a; --run-bg:#fbf0e2;
  --done:#1d6f52; --done-bg:#e6f2ec;
  --block:#6b7185; --block-bg:#edeef1;
  --bad:#a63523; --bad-bg:#fae9e6;
  --radius:9px;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --ink:#e8e7ee; --ink-2:#a7a8b8; --ink-3:#75778c;
    --ground:#111219; --panel:#191b24; --line:#2a2d3a;
    --iris:#9d96f5; --iris-soft:#23213c;
    --run:#e0a250; --run-bg:#2e2418;
    --done:#5cbf95; --done-bg:#12291f;
    --block:#8b90a4; --block-bg:#212430;
    --bad:#e58575; --bad-bg:#2e1c19;
  }}
}}
:root[data-theme="dark"] {{
  --ink:#e8e7ee; --ink-2:#a7a8b8; --ink-3:#75778c;
  --ground:#111219; --panel:#191b24; --line:#2a2d3a;
  --iris:#9d96f5; --iris-soft:#23213c;
  --run:#e0a250; --run-bg:#2e2418;
  --done:#5cbf95; --done-bg:#12291f;
  --block:#8b90a4; --block-bg:#212430;
  --bad:#e58575; --bad-bg:#2e1c19;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,sans-serif;
  font-size:15px; line-height:1.55; -webkit-font-smoothing:antialiased;
}}
.mono {{ font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,monospace; font-variant-numeric:tabular-nums; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:28px 20px 80px; }}

header.top {{ display:flex; flex-wrap:wrap; gap:16px; align-items:baseline; justify-content:space-between; margin-bottom:6px; }}
h1 {{ font-family:"Fraunces",Georgia,serif; font-weight:600; font-size:clamp(28px,4.5vw,42px);
  letter-spacing:-.02em; margin:0; text-wrap:balance; }}
.age {{ font-size:13px; color:var(--ink-3); }}
.age b {{ color:var(--run); font-weight:600; }}
.sub {{ color:var(--ink-2); max-width:62ch; margin:0 0 26px; }}

.progress-band {{ background:var(--panel); border:1px solid var(--line); border-radius:var(--radius);
  padding:20px 22px; margin-bottom:22px; }}
.big {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }}
.big .n {{ font-family:"Fraunces",Georgia,serif; font-size:44px; font-weight:600; line-height:1;
  font-variant-numeric:tabular-nums; }}
.big .of {{ color:var(--ink-3); font-size:15px; }}
.track {{ height:10px; border-radius:99px; background:var(--block-bg); overflow:hidden; display:flex; margin:14px 0 6px; }}
.track i {{ display:block; height:100%; }}
.t-done {{ background:var(--done); }}
.t-run {{ background:var(--run); }}
.t-conflict {{ background:var(--bad); }}
.legend {{ display:flex; gap:18px; flex-wrap:wrap; font-size:12.5px; color:var(--ink-2); }}
.legend span::before {{ content:""; display:inline-block; width:9px; height:9px; border-radius:3px; margin-right:6px; }}
.l-done::before {{ background:var(--done); }} .l-run::before {{ background:var(--run); }}
.l-conflict::before {{ background:var(--bad); }} .l-block::before {{ background:var(--block-bg); border:1px solid var(--line); }}

.grid2 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:18px; margin-bottom:26px; }}
section.card {{ background:var(--panel); border:1px solid var(--line); border-radius:var(--radius); padding:18px 20px; }}
h2 {{ font-family:"Fraunces",Georgia,serif; font-weight:600; font-size:19px; margin:0 0 4px; letter-spacing:-.01em; }}
.note {{ font-size:13px; color:var(--ink-3); margin:0 0 14px; }}

.arm-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; }}
.arm-card {{ border:1px solid var(--line); border-radius:7px; padding:11px 13px;
  display:grid; grid-template-columns:auto 1fr; gap:2px 8px; align-items:baseline; }}
.arm-name {{ grid-column:1/-1; font-weight:600; font-size:13.5px; margin-bottom:4px; }}
.arm-run {{ font-size:21px; color:var(--run); font-weight:500; }}
.arm-done {{ font-size:21px; color:var(--done); font-weight:500; }}
.arm-lbl {{ font-size:12px; color:var(--ink-3); }}

.keeper {{ display:grid; grid-template-columns:46px 1fr 34px; gap:8px; align-items:center; padding:7px 0;
  border-bottom:1px solid var(--line); }}
.keeper:last-child {{ border-bottom:0; }}
.kid {{ font-size:13px; font-weight:500; }}
.bar {{ height:7px; background:var(--block-bg); border-radius:99px; overflow:hidden; }}
.bar-fill {{ height:100%; background:var(--iris); border-radius:99px; }}
.kn {{ font-size:13px; text-align:right; color:var(--ink-2); }}
.kt {{ grid-column:2/3; font-size:12.5px; color:var(--ink-3); }}
.keeper .pill {{ grid-column:3/4; justify-self:end; }}

.gates-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:10px; }}
.gate {{ border:1px solid var(--line); border-left-width:3px; border-radius:7px; padding:10px 13px; }}
.gate p {{ margin:5px 0 0; font-size:12.5px; color:var(--ink-2); }}
.gid {{ font-weight:500; font-size:13px; }}
.gstatus {{ float:right; font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }}
.g-pass {{ border-left-color:var(--done); }} .g-pass .gstatus {{ color:var(--done); }}
.g-fail {{ border-left-color:var(--bad); }} .g-fail .gstatus {{ color:var(--bad); }}
.g-unknown {{ border-left-color:var(--block); }} .g-unknown .gstatus {{ color:var(--block); }}

.controls {{ display:flex; gap:9px; flex-wrap:wrap; align-items:center; margin:0 0 16px; }}
.chip {{ font:inherit; font-size:13px; cursor:pointer; background:var(--panel); color:var(--ink-2);
  border:1px solid var(--line); border-radius:99px; padding:6px 13px 6px 9px;
  display:inline-flex; align-items:center; gap:7px; transition:.13s; }}
.chip:hover {{ border-color:var(--iris); color:var(--ink); }}
.chip[aria-pressed="true"] {{ background:var(--iris-soft); border-color:var(--iris); color:var(--ink); }}
.chip .cn {{ font-size:12px; font-weight:600; padding:1px 6px; border-radius:99px; background:var(--block-bg); }}
.c-running .cn {{ background:var(--run-bg); color:var(--run); }}
.c-done .cn {{ background:var(--done-bg); color:var(--done); }}
.c-conflict .cn {{ background:var(--bad-bg); color:var(--bad); }}
input[type=search] {{ font:inherit; font-size:13px; padding:7px 12px; border-radius:99px;
  border:1px solid var(--line); background:var(--panel); color:var(--ink); min-width:190px; flex:1; max-width:280px; }}
input[type=search]:focus-visible, .chip:focus-visible {{ outline:2px solid var(--iris); outline-offset:2px; }}

.units {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); gap:11px; }}
.unit {{ background:var(--panel); border:1px solid var(--line); border-left-width:3px;
  border-radius:7px; padding:12px 14px; }}
.unit.s-running {{ border-left-color:var(--run); }}
.unit.s-done {{ border-left-color:var(--done); }}
.unit.s-conflict {{ border-left-color:var(--bad); }}
.unit.s-blocked {{ border-left-color:var(--block); }}
.unit.s-ready {{ border-left-color:var(--iris); }}
.unit header {{ display:flex; gap:8px; align-items:baseline; }}
.uid {{ font-size:12.5px; font-weight:500; color:var(--iris); }}
.unit h3 {{ font-size:13.5px; font-weight:500; margin:0; flex:1; line-height:1.4; }}
.arm {{ font-size:11px; color:var(--ink-3); }}
.meta {{ display:flex; gap:6px; flex-wrap:wrap; margin-top:7px; }}
.vfy {{ font-size:11px; color:var(--done); background:var(--done-bg); padding:1px 7px; border-radius:99px; }}
.gates {{ font-size:11px; color:var(--iris); background:var(--iris-soft); padding:1px 7px; border-radius:99px; font-weight:500; }}
.claim {{ font-size:10.5px; color:var(--ink-3); font-family:"IBM Plex Mono",monospace;
  background:var(--block-bg); padding:1px 6px; border-radius:4px; }}
.detail {{ margin-top:8px; display:flex; flex-direction:column; gap:5px; }}
.dim {{ color:var(--ink-3); font-size:11.5px; }}
.dep {{ font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-2);
  background:var(--block-bg); padding:0 5px; border-radius:4px; }}
.pill {{ font-size:11px; padding:1px 8px; border-radius:99px; font-weight:500; }}
.pill.ok {{ background:var(--done-bg); color:var(--done); }}
.pill.bad {{ background:var(--bad-bg); color:var(--bad); }}
.pill.s-running {{ background:var(--run-bg); color:var(--run); }}
.pill.s-blocked {{ background:var(--block-bg); color:var(--block); }}
.pill.s-conflict {{ background:var(--bad-bg); color:var(--bad); }}
.pill.s-ready {{ background:var(--iris-soft); color:var(--iris); }}
.reason {{ font-size:11.5px; color:var(--bad); background:var(--bad-bg); padding:6px 9px;
  border-radius:5px; font-family:"IBM Plex Mono",monospace; line-height:1.45;
  overflow-x:auto; white-space:pre-wrap; word-break:break-word; }}
.leash {{ height:4px; background:var(--block-bg); border-radius:99px; overflow:hidden; }}
.leash-fill {{ height:100%; background:var(--run); }}

.logbox {{ max-height:320px; overflow:auto; background:var(--ground); border:1px solid var(--line);
  border-radius:7px; padding:11px 13px; }}
.logline {{ font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--ink-2);
  white-space:pre-wrap; word-break:break-word; line-height:1.6; }}
footer {{ margin-top:34px; padding-top:18px; border-top:1px solid var(--line);
  font-size:12.5px; color:var(--ink-3); }}
.empty {{ padding:26px; text-align:center; color:var(--ink-3); font-size:13.5px; }}
@media (prefers-reduced-motion:reduce) {{ * {{ transition:none !important; animation:none !important; }} }}
</style>

<div class="wrap">
<header class="top">
  <h1>Consilient Build Board</h1>
  <div class="age">snapshot taken <b id="age">just now</b> · {esc(snap["taken_iso"])}</div>
</header>
<p class="sub">A published page cannot reach the machine this build runs on, so this is a
snapshot rather than a feed. The counter above is the honest one — read it before you trust
anything below it.</p>

<div class="progress-band">
  <div class="big">
    <span class="n">{done}</span><span class="of">of {total} units complete · {pct}%</span>
    <span class="of" style="margin-left:auto">{verified} cross-family verified ({vpct}% of complete)</span>
  </div>
  <div class="track">
    <i class="t-done" style="width:{done * 100 / total:.1f}%"></i>
    <i class="t-run" style="width:{counts.get("running", 0) * 100 / total:.1f}%"></i>
    <i class="t-conflict" style="width:{counts.get("conflict", 0) * 100 / total:.1f}%"></i>
  </div>
  <div class="legend">
    <span class="l-done">{done} done</span>
    <span class="l-run">{counts.get("running", 0)} in flight</span>
    <span class="l-conflict">{counts.get("conflict", 0)} cannot merge</span>
    <span class="l-block">{counts.get("blocked", 0)} blocked by dependencies</span>
  </div>
</div>

<div class="grid2">
  <section class="card">
    <h2>Harness arms</h2>
    <p class="note">Who is carrying work right now, and who built what has landed.</p>
    <div class="arm-grid">{arm_cards}</div>
  </section>
  <section class="card">
    <h2>What is holding up the most</h2>
    <p class="note">Units ranked by how many others cannot start until they land. This is the
    critical path — finishing the top of this list buys more than finishing anything else.</p>
    {keeper_rows or '<div class="empty">Nothing is gating downstream work.</div>'}
  </section>
</div>

<section class="card" style="margin-bottom:26px">
  <h2>Gate conditions</h2>
  <p class="note">Gate A: {esc(overall.get("Gate A", "?"))} · Gate B: {esc(overall.get("Gate B", "?"))}.
  These govern whether orchestration may be depended on. Entering the stage did not pass them.</p>
  <div class="gates-grid">{gate_cards}</div>
</section>

<h2 style="margin-bottom:4px">Every unit</h2>
<p class="note">Filter by state or search by name. {total} units total.</p>
<div class="controls">
  <button class="chip" data-filter="all" aria-pressed="true"><span class="cn mono">{total}</span>All</button>
  {counters}
  <input type="search" id="q" placeholder="Search units…" aria-label="Search units">
</div>
<div class="units" id="units">{"".join(rows)}</div>
<div class="empty" id="none" hidden>No units match.</div>

<section class="card" style="margin-top:26px">
  <h2>Driver activity</h2>
  <p class="note">The tail of the build loop, newest last.</p>
  <div class="logbox">{log_lines or '<div class="logline">No activity recorded yet.</div>'}</div>
</section>

<footer>Consilient measures β — the rate at which automated checks accept a bad artefact.
A unit counted complete is not the same as a unit verified: {done} are complete and {verified}
have survived cross-family review. The gap is the point, not an oversight.</footer>
</div>

<script>
(function () {{
  var taken = {snap["taken"]} * 1000;
  var el = document.getElementById('age');
  function tick() {{
    var s = Math.max(0, Math.round((Date.now() - taken) / 1000));
    var t = s < 60 ? s + 's ago'
      : s < 3600 ? Math.floor(s / 60) + 'm ago'
      : Math.floor(s / 3600) + 'h ' + Math.floor((s % 3600) / 60) + 'm ago';
    el.textContent = t;
  }}
  tick(); setInterval(tick, 1000);

  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var units = Array.prototype.slice.call(document.querySelectorAll('.unit'));
  var none = document.getElementById('none');
  var q = document.getElementById('q');
  var filter = 'all';
  function apply() {{
    var term = q.value.trim().toLowerCase();
    var shown = 0;
    units.forEach(function (u) {{
      var okState = filter === 'all' || u.dataset.state === filter;
      var okText = !term || u.dataset.text.indexOf(term) !== -1;
      var show = okState && okText;
      u.hidden = !show;
      if (show) shown++;
    }});
    none.hidden = shown > 0;
  }}
  chips.forEach(function (c) {{
    c.addEventListener('click', function () {{
      filter = c.dataset.filter;
      chips.forEach(function (o) {{ o.setAttribute('aria-pressed', String(o === c)); }});
      apply();
    }});
  }});
  q.addEventListener('input', apply);
}})();
</script>
"""


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")

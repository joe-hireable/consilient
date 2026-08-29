"""The stylesheet, and the only place in the package that names a colour.

Measured 28 August 2026: every hex value in the original `dashboard.py` sat on eighteen
lines inside this one constant, and none appeared anywhere else in the file. That is why
the stylesheet is its own module — it makes the boundary the design-token lockdown
polices (ADR-0060, `.github/scripts/check_design_tokens.py`) a file boundary rather than
a convention, so a colour invented in a panel helper has nowhere to hide.

The page has no JavaScript, so this file carries more of the behaviour than a stylesheet
usually would: view switching is `:checked` sibling selectors over radio inputs, and
expert detail is `<details>`. Both are platform features, so there is no runtime to
break."""

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  color-scheme:light dark;
  --ground:#F6F7F9; --surface:#FFFFFF; --raised:#ECEEF2;
  --ink:#0C0E12; --ink-2:#3D4453; --muted:#6F778A; --rule:#D6DAE2;
  --accent:#B88714; --accent-soft:#FAF2DE;
  --pass:#23864F; --pass-bg:#E9F6EF;
  --fail:#C53030; --fail-bg:#FDE8E8;
  --unknown:#B57414; --unknown-bg:#FCF4E4;
  --shadow:0 1px 2px rgba(26,26,24,.05),0 8px 24px -12px rgba(26,26,24,.18);
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --serif:ui-serif,Georgia,"Times New Roman",serif;
  --mono:ui-monospace,SFMono-Regular,"Cascadia Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ground:#0C0E12; --surface:#14171E; --raised:#1C202A;
  --ink:#F0F2F5; --ink-2:#C4C9D4; --muted:#8B93A5; --rule:#2A2F3D;
  --accent:#E2B340; --accent-soft:#2A2412;
  --pass:#2E9E66; --pass-bg:#11261C;
  --fail:#E05349; --fail-bg:#2D1617;
  --unknown:#DDA136; --unknown-bg:#2B2012;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px -14px rgba(0,0,0,.7);
}}
:root[data-theme="dark"]{
  --ground:#0C0E12; --surface:#14171E; --raised:#1C202A;
  --ink:#F0F2F5; --ink-2:#C4C9D4; --muted:#8B93A5; --rule:#2A2F3D;
  --accent:#E2B340; --accent-soft:#2A2412;
  --pass:#2E9E66; --pass-bg:#11261C;
  --fail:#E05349; --fail-bg:#2D1617;
  --unknown:#DDA136; --unknown-bg:#2B2012;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px -14px rgba(0,0,0,.7);
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

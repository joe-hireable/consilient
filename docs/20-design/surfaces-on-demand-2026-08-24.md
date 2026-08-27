# Surfaces on demand — a fixed ambient budget, and a record of every question asked

**Date:** 24 August 2026 (reconstructed 26 August 2026; the unit that would have written this
on the 24th was lost to a concurrent write of `.harness/plan-units.json`).
**Status:** design. Nothing here authorises a dashboard framework, a widget registry, a
layout engine or a plugin system.
**Document class:** W.
**Falsifier:** a generated surface is promoted to the ambient set on recollection, on a
designer's prediction, or on any evidence other than recorded `surface.request` events; or
an element is added to the ambient set without removing one and without renaming the
budget test.
**Review by:** 2026-09-24, or immediately after EXP-108 reports, or after `dashboard.py`
is wired to this contract.

The principal, 24 August 2026:

> we can also have custom dashboards built on-demand and/or on-request WITHOUT
> OVERWHELMING THE USER WITH UNNECESSARY INFORMATION OR INFORMATION THEY HAVE NOT
> ASKED FOR. Again AI can do all of this on-demand for the user as well as in the
> deterministic ways we are building.

---

## 1. Thesis

A fixed dashboard is a **prediction** about which questions will recur. A generated
surface answers the question that was actually asked. Both are needed. The design
problem is the boundary between them.

The rule: **a surface becomes fixed only after the question it answers has been asked
repeatedly.** Promotion is earned by observed demand, never by anticipation. The only
admissible evidence of demand is a trajectory event recording the question, when, and
by whom.

That is not a product preference. The principal is one reviewer and his attention is
the binding constraint on the whole project (`work-modes.md`; `findings.md` §5). A
surface that costs thirty seconds and answers nothing is a real debit. A dashboard
that shows ten numbers derived from one source is not ten pieces of evidence — it is
one, displayed ten times, which is echo wearing the costume of thoroughness.

---

## 2. What already exists (the bar, retrieved)

Searched 26 August 2026:

- `docs/20-design/` — every dated design note, `DESIGN.md`, `work-modes.md`,
  `surfaces-and-who-they-serve.md`, `frontend-concepts-kimi-2026-08-20.md`,
  `observability-steering-and-embodiment-2026-08-23.md`,
  `documentation-and-surfaces-plan-2026-08-23.md`.
- `docs/00-context/design-bar-2026-08-23.md` — the frozen visual/density bar.
- `docs/decisions/index.md` and ADRs 0007, 0035, 0053, 0089, 0096, 0098.
- `docs/40-spec/v0-draft.md` §2 (non-goals) and §10 (CLI surface).
- `docs/10-research/findings.md` §5; experiment register headings EXP-08, EXP-19,
  EXP-42, EXP-108.
- `docs/10-research/bibliography.md` — no Shneiderman 1996 entry. **This unit's
  claim list does not include the bibliography**, so the source is recorded here
  rather than promoted into that file.
- Public retrieval of the visualisation incumbent (Shneiderman, CS-TR-3665).

| Incumbent | What it already decides | What this note does with it |
|---|---|---|
| ADR-0053 (ACCEPTED) | Exactly one observability surface: `consil dashboard`, a self-contained HTML file that **renders** the record and never decides. No server, no review UI. | Keep. This note does not replace it and does not add a second renderer. |
| ADR-0007, superseded in part by 0053 and 0098 | No TUI, no desktop app, no local web *server*, no diff-review surface. | Survives. On-demand generation is not a review UI and is not a server. |
| ADR-0098 (ACCEPTED) | Permit **one** authenticated local surface: chat as resting state, a settings control, and one entry to observability. Graphical actions must have a chat equivalent. | The ambient set is that one surface's information budget, not a family of dashboards. |
| ADR-0035 (PROVISIONAL) | Visibility is a user-controlled rendering of the record, never a second record. EXP-42 decides whether a dial earns more than `--quiet`. | Demand events are part of the record. Generated surfaces remain projections of it. The dial is out of scope. |
| ADR-0089 (PROPOSED) | One front door; preserve native specialist surfaces when the working medium would be lost. | Orthogonal. Specialist hand-off is not ambient promotion. |
| ADR-0096 (PROVISIONAL) | Record-derived graphs without generated explanations, on the existing dashboard only. | Orthogonal. This unit adds no graph and no second renderer. |
| `dashboard.py` | The shipping ADR-0053 renderer. Default page already lays out gate state, β, a promotion card, trajectory stats, and tabbed fleet / agents / RACI / usage / capability-gap / schema-gap panels. [measured: `src/consilient/dashboard.py`] | **Over budget relative to this rule.** This unit does not rewrite it — that path is not claimed. The budget lives here so later wiring has a check that fails. |
| `docs/20-design/DESIGN.md` §5 | Four horizontal bands: header & system state; β-meter; autonomous work registry; unavoidable asks. [asserted] | The first, second and fourth map onto `gates`, `beta`, `needs_you`. The work registry is the original job of ADR-0053 and is **not** ambient here: fleet visibility is available on request. Three, not four. |
| `docs/00-context/design-bar-2026-08-23.md` | Names **Datadog / Grafana** as the density incumbent: tiered dashboards (heartbeat → triage → deep dive), 12-column grid, colour reserved for alarm, a 3-second health read at Tier 1. Maps DESIGN.md's four bands onto Grafana Tier 1–2. Refuses the "god dashboard" of forty same-sized charts. [cited: that document, retrieved 26 August 2026] | Grafana tells you **how to read** a heartbeat. This note decides **which questions earn** the heartbeat slot. They compose. A 3-second health read of a predicted set is still a prediction. |
| `docs/20-design/surfaces-and-who-they-serve.md` | A frontend earns its place only by reducing `T_effective_review` without raising β. Gated on EXP-08 / EXP-19. | Still the outcome test for any *review* surface. This note is not a review surface. |
| `docs/20-design/frontend-concepts-kimi-2026-08-20.md` §2 | Twelve refusals, each cited or invariant-backed. R8 refuses a wall-of-agents dashboard. Concept 1 already draws three bands at rest: instrument, work, needs-you. | Adopted. An element budget is how R8 is enforced as a count rather than a taste. Concept 1's work band is the same prediction the work-registry band is; it stays off the ambient tuple until demanded. |
| `docs/20-design/observability-steering-and-embodiment-2026-08-23.md` | A ten-rung surface ladder (S1–S10) designed in advance. | **This is the prediction the rule refuses.** Those rungs may be *generated on request*. None of them is ambient until `surface.request` events say so. |
| `docs/20-design/documentation-and-surfaces-plan-2026-08-23.md` | Resting state: "NEEDS YOU nothing". | That sentence is the job of the `needs_you` slot. |
| EXP-108 | Does an available-but-unpushed live surface change trust or intervention? `BLOCKED`. | Do not ship a live push. Demand is pull: a recorded request. |
| EXP-42 | Visibility dial vs a quiet flag. `BLOCKED`. | Out of scope. |
| EXP-08 / EXP-19 | Critic recall and verdict-prompt completion. Both `BLOCKED`. | They gate a *review* surface. They do not gate a demand recorder. |
| Shneiderman, 1996, *The Eyes Have It*, IEEE Symposium on Visual Languages, DOI 10.1109/VL.1996.545307; author's TR CS-TR-3665 / ISR-TR-96-66. Retrieved and read 26 August 2026 from https://www.cs.umd.edu/hcil/trs/96-13/96-13.html (full HTML of the technical report). | Visual Information-Seeking Mantra, stated in the abstract and repeated ten times in §2: "Overview first, zoom and filter, then details-on-demand." §3 Overview: "information visualization interfaces support some overview strategy, or should." Seven tasks, of which History is "keep a history of actions to support undo, replay, and progressive refinement." [cited] | The mantra is the visualisation bar for on-demand *detail*. It still assumes the designer already knows the overview. The Consilient addition is that the overview itself is earned. The demand record is his History task, used as promotion evidence rather than as undo. |

v0-draft §2 still excludes "a graphical review surface, TUI, web server". This unit stays
inside that boundary: a library contract, no new `consil` command, no server, no review
UI. Stage 3 permits building; it does not pass Gate A or Gate B. [measured: `AGENTS.md`]

---

## 3. The two mechanisms, and nothing else

### 3.1 A named element budget

The ambient surface holds a frozen tuple of element identifiers. The test that guards it
**names the count in the test name**, and reads the expected count back out of that name.
Editing a constant in two places together is not a budget; renaming
`test_ambient_surface_element_budget_is_3` is a visible decision in the diff.

The initial fill is the observe-only increment that already ships and is already used,
not a forecast of widgets:

- `gates` — `consil doctor`: is the system stopped
- `beta` — `consil beta`: the false-accept rate, with sample and interval, never a composite
- `needs_you` — the reserved-class items waiting for the principal, or the fact that none are

Three is the budget. Adding a fourth requires removing one, or renaming the test. Usage,
fleet, RACI, capability gaps, schema gaps and the work registry are available *on
request*; they are not ambient. [asserted: the initial fill is the already-shipping CLI
plus the resting-state sentence, not a new prediction. The honest residual is that those
three questions were not themselves recorded as `surface.request` events, because the
recorder did not exist. New elements do not get that charity. The work registry is the
larger residual: ADR-0053 authorised it as the reason a visibility surface exists at
all, and this budget still leaves it off the ambient set until someone asks.]

### 3.2 A demand record

Every surface request is appended through `events.append` — the single writer — as
`surface.request`. The body is the question asked. The event timestamp is when. The
event actor is who. That record is the **only** admissible evidence for promoting a
generated surface into the ambient set. A recollection, a design document, a ranked
list of "what users want", or an event of any other kind does not count.

"Repeatedly" means at least two recorded requests for the same question (exact match
after strip). One ask is a request. Two is the smallest demand. Paraphrase-merging is
refused: that would be a framework.

Promotion here is a **predicate** over the log (`promotion_admissible`). It does not
mutate the ambient tuple. A later human edit of the tuple, with the budget test
renamed if the count changes, is the promotion. An agent may not approve it (V0-18).

### 3.3 Freshness

Any surface rendering data it cannot refresh must display its age as a **running
counter**. A timestamp of generation is not a counter; a "stale" badge is not a
counter. [measured, 24 August 2026: a published artefact cannot reach this machine, so
every published surface is a snapshot, and one that looks live is the failure this
repository most often measures in itself.] This module has no refresh path, so every
ambient render carries elapsed age, including `0h 0m 0s`.

---

## 4. What is not built

No dashboard framework. No widget registry. No layout engine. No plugin system. No
second renderer beside `dashboard.py`. No new CLI command. No write path that decides
anything. No live push (EXP-108 is blocked). None of these can be justified before the
demand record holds anything; a framework built in advance is the opposite of the
thesis.

---

## 5. Evidence against

- **Shneiderman's overview is itself a prediction.** His §3 Overview treats "an
  overview of the entire collection" as a criterion a visualisation *should* support.
  The mantra is right that detail should be on demand. It is silent on how the
  overview was chosen. Treating "overview first" as a licence to ship a large default
  dashboard is the failure this note is for. The 23 August ten-rung ladder is that
  failure in this repository.
- **Grafana's heartbeat is a designed overview, and this repository already adopted
  it.** The frozen design bar maps four DESIGN.md bands onto Grafana Tier 1–2 and
  wants a 3-second health read. [cited: `design-bar-2026-08-23.md`] An empty ambient
  set would hide even `consil doctor`. The three-element fill is the heartbeat; the
  fourth band (work registry) is the place this rule is stricter than the design bar.
  If fleet questions dominate the demand record, the work registry earns its slot by
  renaming the budget test, not by this note anticipating it.
- **An empty ambient set would be more faithful to "never anticipate".** It would also
  hide the observe-only increment the principal already uses. The residual charity on
  the initial three is recorded in §3.1 rather than denied.
- **ADR-0053's dashboard already exceeds three elements.** Shipping a budget that the
  live renderer does not consult is a check that does not yet bite the page. Wiring
  `dashboard.py` is later work; shrinking it in this unit would claim an unclaimed path.
- **Miller's 7±2** is the near-miss everyone reaches for. It is a short-term memory
  figure, not a dashboard-density result, and it is not the bar. [asserted]
- **Recording requests could itself become a nag.** The recorder is a library call,
  not a prompt. Asking the user "did you want a dashboard?" would be the satisfaction
  prompt `frontend-concepts-kimi` R6 already forbids.
- **Two identical asks is a low bar.** A worker can append twice. The predicate is
  evidence of demand, not proof of it; the human still has to edit the tuple. Raising
  the threshold before any demand exists would be another prediction.

---

## 6. The check that would kill this

`tests/test_surfaces.py::test_ambient_surface_element_budget_is_3` fails if the ambient
tuple grows without the test being renamed.
`tests/test_surfaces.py::test_recollection_is_not_promotion_evidence` fails if promotion
accepts anything other than trajectory events.
`tests/test_surfaces.py::test_a_single_request_does_not_admit_promotion` fails if one
ask is treated as demand.

If those three are green and a generated surface still appears ambient on a designer's
say-so, the predicate was bypassed and the bypass is the bug.

---

## 7. Historical theory and density context

The visualisation bar is Shneiderman 1996: overview first, details on demand. [cited]
The product-density bar, frozen in this repository, is Grafana's heartbeat dashboard
as adopted by `design-bar-2026-08-23.md` and DESIGN.md's four bands. [cited] The
in-repo construction bar is ADR-0053's one renderer plus ADR-0098's one surface. This
is better than those in one respect only: **the overview is not designed in advance**.
Detail on demand is necessary and not sufficient; without a demand record, "on demand"
collapses into "the designer guessed you would demand it". Grafana remains the bar for
*how* a heartbeat reads; it is not the bar for *which facts* sit in it. The measurement
that would show the improvement is a later census: the fraction of ambient elements
that have two or more `surface.request` ancestors. If that fraction is zero after the
recorder has been live, the initial fill was anticipation and should be evicted.

---

## 8. Current implementation bar, bounded delta and recheck

The current implementation bar is Omni Agent and Google Looker, not the older
Shneiderman and Grafana material above. [cited]

- **Omni Agent:** its [official chat documentation](https://docs.omni.co/ai/chat),
  retrieved 26 August 2026, describes searching existing dashboards and tiles before
  generating a query, live previews, prompt-to-dashboard creation, saved and shared
  chat sessions, and stale-result warnings with a rerun option. Its documented gaps for
  this unit are no numeric running age and no actor-plus-timestamp request audit.
- **Google Looker:** its official [Conversational Analytics](https://docs.cloud.google.com/looker/docs/conversational-analytics-overview),
  [Natural-language Explore](https://docs.cloud.google.com/looker/docs/conversational-analytics-looker-data),
  [saved dashboards](https://docs.cloud.google.com/looker/docs/creating-user-defined-dashboards),
  [Content Guardrails](https://docs.cloud.google.com/looker/docs/admin-panel-performance-center-content-guardrails),
  [System Activity](https://docs.cloud.google.com/looker/docs/system-activity-dashboards),
  [user consent](https://docs.cloud.google.com/looker/docs/user-account), and
  [dashboard freshness](https://docs.cloud.google.com/looker/docs/viewing-dashboards)
  were retrieved 26 August 2026. Looker supports natural-language tables or
  visualisations, saved dashboards, query-tile limits, consented question/user/time
  administration data, and relative update age. Its limit is editable and query-tile
  only, does not repair existing dashboards, starts question collection only after
  consented enablement, refreshes System Activity daily while excluding Gemini
  Enterprise conversations, and does not document a continuously running age counter.

In the bounded retrieval of those official materials, no exact rule requiring repeated,
recorded demand before promotion was found. That is a bounded search finding, not a
universal absence claim. This unit's fixed tuple, append-before-eligibility demand
record, and elapsed age counter address only those narrow gaps. It does **not** beat
either incumbent end-to-end: it has no production caller, actual renderer, generator,
reuse path, consent model, or dashboard administration.

The falsifier and measurement are a later census: every ambient element must have at
least two valid recorded `surface.request` ancestors, and every snapshot's age must
increase with elapsed time. Zero valid ancestors or a static age falsifies this local
claim. Recheck the official links and census by 2026-09-24 or when a production renderer
is proposed. To raise or otherwise change the fixed budget, edit `AMBIENT_ELEMENTS` and
rename `test_ambient_surface_element_budget_is_3` in the same review; no unseen
configuration value may change it.

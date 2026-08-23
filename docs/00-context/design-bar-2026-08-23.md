# Design: external bar frozen before implementation review

**Frozen:** 2026-08-23T13:51:00Z, before any dashboard or prototype revision is judged against it.
This artefact is the review yardstick; findings belong in a separate file and must not rewrite this
bar after seeing a proposal. [measured]

**Correction to the dispatch brief.** `docs/00-context/the-machine-2026-08-22.md` records the
principal's desire for **one interface instead of eight** (Claude Code, Cowork, Claude design, Figma,
SuperGrok, Grok bot, Cursor, ChatGPT Work) and a **single chat interface** as the primary response
surface for organised superintelligence — but it does **not** verbatim record *"chat to create in
Open Design and view results there."* That flow is inferred from ADR-0060 (Joe installed the Open
Design desktop on 21 August 2026) and the `using-open-design` skill (agents author `DESIGN.md`;
the desktop is optional). Treat the inferred flow as `[asserted]` until the principal confirms it.
Human-labelled β remains unestimated: one human rejection recorded, minimum thirty required.
`routing_orchestration_enabled` stays `false`; this bar changes no gate condition. [measured]

## Decision this bar makes

A proposed surface clears the bar only if it **beats the cited incumbents on the tasks Consilient
actually performs** — offline inspection of an append-only trajectory, verifier truth, bounded human
asks, and pull-based observability for a non-hands-on principal — while surviving ADR-0053 (one
self-contained HTML file, no bundler, no framework dependency) and ADR-0060's token contract.
Distinction must be **observable in structure and interaction**, not merely asserted in prose;
taste claims that cannot be held to token, contrast, density, or timed task evidence remain
`[asserted]` and are settled by EXP-95's critique protocol or principal verdict, not by model
agreement. [asserted]

## 1. The incumbent bar — what is actually good, product by product

Each row names **what specifically earns imitation** versus what is **copied without being good**.
Sources were retrieved 2026-08-23 unless noted.

| Product | What is specifically good | What is imitated without being good | Bar for Consilient |
|---|---|---|---|
| **Linear** | Near-black surface ladder (`#0f1011`–`#141516` class), **13–15px body at 1.4–1.6 lh** on a **4px grid**, **32–40px row rhythm**, **tabular numerics**, **custom Inter Variable stops (510/590/680)** for machined weight, **keyboard command surface (⌘K)**, empty states that are one sentence not marketing. [cited] | **Indigo-on-charcoal dev-tool skin** as a default "serious SaaS" costume; **Inter** as a stand-in for thought; density copied onto marketing pages where novices need breathing room. [asserted] | Match **density discipline and keyboard affordances** on the operator bridge; **refuse Inter/Geist** and the indigo accent cluster (ADR-0060 ban list). [asserted] |
| **Vercel / Geist** | **Single-family typography (Geist Sans + Mono)**, **scale prop** that co-scales spacing and type, **high-contrast neutral palette**, **grid-forward marketing**, Swiss-poster restraint on public pages. [cited] | **Geist/Inter as "we are developers"** without a measured reason; **monochrome + one accent** mistaken for identity. [asserted] | Adopt **one coherent type scale and materials spec**; do not adopt Geist — it is on the ban list. [asserted] |
| **Stripe (docs + dashboard)** | **Typography-led hierarchy** (large metrics, light display weights on Söhne at 300–400), **tabular figures (`tnum`) for money**, **narrow semantic colour** (status colours mean something; sparklines stay monochrome), **dense data inside generous chrome**, microcopy that states what happened and what to do. [cited] | **Gradient mesh marketing** pasted onto products that are not Stripe; **purple/indigo CTA** as generic fintech; **lightweight headlines** without the underlying table discipline. [asserted] | **Reserve colour for verifier semantics** (valid / attention / fault / pending human action); **always pair metrics with n and intervals**; never gradient hero decoration. [asserted] |
| **Raycast** | **Keyboard-first with inline shortcut discovery**, **<50ms launch target**, **surface ladder without drop shadows**, **native macOS vibrancy**, **action panel (⌘K) for context commands**, fuzzy search with match highlighting. [cited] | **Dark utilitarian chrome** without the speed budget; **Inter + ss03 "g"** as costume; command palette as a **second app** instead of the primary navigation model. [asserted] | **Inline shortcuts and action panel patterns** on desktop bridge; **no decorative shadows** (DESIGN.md Level 0 default). [asserted] |
| **Arc** | **Sidebar-first workspace** replacing horizontal tabs; **Spaces** as context containers with colour themes; **pinned vs ephemeral tabs** with auto-archive; **vertical list scan** faster than horizontal tab bars for long lists. [cited] | **Frosted glass + pastel gradient** as 2023–2025 "modern app" wallpaper; **coloured letter avatars** on every row; **backdrop-blur** (explicitly banned in DESIGN.md). Product entered **maintenance mode May 2025** (Browser Company letter) — the chrome froze but the **spatial model** remains the reference. [cited] | **Spatial fleet / capability views** in prototypes, not browser chrome cosplay; **no backdrop-filter blur**. [asserted] |
| **Things 3** | **95% neutral palette** with colour only for semantic dates (Today, Evening, deadlines); **SF system type** with weight/size hierarchy; **Areas → Projects → Tasks** cognitive model; **generous whitespace** on a consumer task surface; **keyboard-first on Mac**, tactile completion on iOS. [cited] | **"Apple Design Award minimalism"** without the hierarchy underneath; white cards on grey without information density when copied to operational tools. [asserted] | **Calm resting state** and **one focal accent** (Electric Ochre for human decisions only); hierarchy mirrors **trajectory → run → event**, not chat threads. [asserted] |
| **Observable / Plot** | **Reactive cells** (change propagates like a spreadsheet); **Plot** for concise chart grammar; **inputs wired to marks** for scrubbing; **dataflow graph** visible to the author; **fork/merge** for exploration. [cited] | **Notebook-as-dashboard** without reactive discipline; D3 soup without scale discipline. [asserted] | **Time-scrubbable trajectory** and **causality graph** (prototype B) beat chat scroll — **state manipulation**, not narrative streaming. [asserted] |
| **Datadog / Grafana** | **Tiered dashboards** (heartbeat → triage → deep dive); **12-column grid**; **grouped widgets**; **template variables**; **high-density mode** for wall displays; **colour reserved for alarm states**; **3-second health read** at Tier 1. [cited] | **God dashboards** with forty same-sized charts; **rainbow time series**; **auto-refresh everything** (self-DOS). [asserted] | **Four bands** in DESIGN.md (header state, β-meter, work registry, asks) map to Tier 1–2; observatory is Tier 3. **Max one attention colour per region.** [asserted] |
| **Claude Cowork / ChatGPT Work** | **Autonomous file/browser task execution** behind a simple task box; **cross-device session continuity** (Cowork side panel ↔ desktop); **integrations depth** (M365 read/write on Cowork). [cited] | **Chat column + left history sidebar + bottom input** as the **entire** product metaphor; **mode toggle** (Chat vs Cowork) on the same conversational shell; **"thinking" streaming theatre**. [cited] | **Reject chat column as primary** (ADR-0007, DESIGN.md); keep **task dispatch and fleet state** as resting UI. [asserted] |
| **Hermes Agent / Gemini Spark** | **Kanban-style coordination** (non-clashing agents, visible queue) cited by the principal as worth beating; **plugin/tool surfaces** for extended capability. [asserted] | **Agent persona cards** and **streaming token UI** without measured routing; board UI without atomic claims. [asserted] | Take **coordination primitives** (`coordination.py`, `work_items.py`) not **kanban ceremony**; surface **claims, ceilings, and verifier outcomes**. [asserted] |

Primary sources retrieved 2026-08-23:

- Linear aesthetic and density: [Build MVP Fast, Linear decoded](https://www.buildmvpfast.com/blog/linear-aesthetic-tokens-density-keyboard-first-ux-2026), [DesignMD Linear benchmark](https://designmd.cc/benchmarks/linear). [cited]
- Stripe dashboard and type: [925 Studios breakdown](https://www.925studios.co/blog/stripe-dashboard-design-breakdown), [Open Design Stripe plugin](https://open-design.ai/plugins/design-system-stripe/), [DesignMD Stripe benchmark](https://designmd.cc/benchmarks/stripe). [cited]
- Vercel Geist: [Geist introduction](https://vercel.com/geist/introduction), [geist-font repository](https://github.com/vercel/geist-font/). [cited]
- Raycast: [Raycast design guide](https://blakecrosley.com/guides/design/raycast), [Raycast keyboard manual](https://manual.raycast.com/keyboard-shortcuts). [cited]
- Arc: [Arc Spaces help](https://resources.arc.net/hc/en-us/articles/19228064149143-Spaces-Distinct-Browsing-Areas), [Open Design Arc plugin](https://open-design.ai/plugins/design-system-arc/), [SupaSidebar 2026 explainer](https://supasidebar.com/blog/what-is-arc-browser-sidebar-2026). [cited]
- Things 3: [Blake Crosley Things guide](https://blakecrosley.com/guides/design/things), [DesignMD Things reference](https://designmd.santiagoalonso.com/things). [cited]
- Observable: [Observable notebooks documentation](https://observablehq.com/documentation/notebooks/), [Observable Plot API](https://observablehq.com/plot/api). [cited]
- Grafana / Datadog density: [DEV Community Grafana density tiers](https://dev.to/futhgar/grafana-dashboards-information-density-vs-readability-2j6k), [DevOpsil SRE dashboard principles](https://devopsil.com/articles/2026-03-21-grafana-dashboard-design-sre-principles), [DataDog effective-dashboards guidelines](https://github.com/DataDog/effective-dashboards/blob/main/guidelines.md). [cited]
- AI workspaces: [ChatGPT Work vs Claude Cowork comparison](https://www.developersdigest.tech/blog/chatgpt-work-vs-claude-cowork-2026), [FakeAIChat UI comparison 2026](https://www.fakeaichat.com/blog/ai-chat-ui-comparison-2026.html), [Anthropic Cowork Chrome side panel](https://claude.com/blog/cowork-chrome-side-panel). [cited]
- High-performance HMI (scientific/operations analogue): [ISA-101 standards page](https://www.isa.org/standards-and-publications/isa-standards/isa-101-standards), [PLC Programming ISA-101 summary](https://plcprogramming.io/blog/high-performance-hmi-isa-101). [cited]
- Convergence phenomenon (text modality): Doshi & Hauser, *Science Advances* 10(28), 2024, DOI [10.1126/sciadv.adn5290](https://doi.org/10.1126/sciadv.adn5290). [cited]

## 2. What "better than best" means for *this* product

Consilient is **not** a SaaS dashboard selling seats. It is an **offline, append-only record renderer**
for machine reasoning — `.harness/log` projected through `consil --json` into a surface a principal
who is **deliberately not hands-on** can pull when needed. [measured: ADR-0053, DESIGN.md]

The nearest analogues are therefore **instrument panels and scientific visualisation**, not product
marketing pages:

1. **ISA-101 high-performance HMI** — visually calm normal state; **abnormal conditions immediately
   recognizable**; colour reserved for deviation; numeric clutter suppressed until needed. Maps to
   *"nothing needs you"* when gates are green and β is within envelope. [cited] [asserted]
2. **Tiered observability dashboards** — heartbeat at a glance, triage on drill, forensic depth on
   demand. Maps to bridge → observatory prototype split. [cited] [asserted]
3. **Observable-style reactive inspection** — manipulate time and filters; the view updates from
   recorded state, not from a narrator summarising state. [cited] [asserted]

**Better than best** here means: **at least as disciplined as Linear/Raycast on density and keyboard
pathways**, **at least as honest as Stripe on numeric presentation**, **at least as tiered as
Grafana on operational reading**, and **structurally unlike Cowork/ChatGPT Work** — no chat column,
no streaming tokens, no thinking theatre — while **passing `check_design_tokens.py`** and rendering
only data the JSON contract actually carries. [asserted]

Imitation targets that **do not transfer**: Stripe's marketing gradient mesh, Arc's glass blur,
Linear's indigo accent, Vercel's Geist family, and any **confidence ring / thumbs feedback** pattern.
[asserted]

Repository prototypes (`bridge-command-post`, `trajectory-observatory`, `mobile-signer`) already
encode this direction under DESIGN.md tokens; the contributor token checker found **thirty undeclared
colours in the production dashboard** — evidence the bar was real and the implementation missed it.
[measured: brief; critique-report.md]

## 3. Does the "2023 chat-column metaphor" claim survive scrutiny?

**Partially — and the partial truth is enough to act on.**

**What survives (cited):**

- Major AI products in 2026 still use **left sidebar history + centred message column + bottom
  input** as the default layout; multiple independent UI comparisons describe convergence on that
  pattern. [cited: FakeAIChat 2026 comparison]
- Claude explicitly merges **Chat and Cowork inside the same conversational window** with a mode
  toggle in the message box. [cited: Impactiv8 Cowork merge article; Anthropic help centre]
- ChatGPT Work and Cowork compete on **autonomous execution** but retain **browser-native or
  chat-native shells** rather than supervisory-control layouts. [cited: Developers Digest 2026]

**What the claim overstates (`[asserted]`):**

- Cowork/Work are **not only** chat — they add file-system depth, browser virtualisation, and
  scheduled pipelines; the metaphor is **shell**, not entire capability.
- **Hermes kanban**, **Cursor's IDE layout**, and **Figma** are counterexamples within the same
  "AI workspace" cluster — the field is not monolithic.
- Arc, Raycast, Linear, and Grafana **never were** chat products; citing them as victims of the same
  metaphor is mixing categories.

**Verdict:** The `pioneering-concepts-spec.md` claim is **directionally right for the AI-workspace
incumbents named** (Cowork, ChatGPT Work, Gemini Spark-class shells) and **wrong as a universal law**.
Consilient's differentiation is **not** "we noticed chat exists" — it is **supervisory control for
agent fleets**, which is a **different class of layout** with fifty years of operations evidence
behind it. [asserted]

## 4. Measurable vs irreducibly judgement — and how disagreement is settled

| Class | What can be held to evidence | Mechanism | Tag |
|---|---|---|---|
| **Token conformance** | Hex roles in DESIGN.md only; no undeclared colours in governed CSS/HTML | `.github/scripts/check_design_tokens.py` in CI | [measured] |
| **Contrast** | WCAG AA minimum on declared pairs (DESIGN.md documents 17.2:1 / 11.8:1 / 6.3:1 for dark palette) | Automated contrast audit on locked pairs; manual for new pairs | [measured] / [asserted] |
| **Type scale adherence** | Declared px/weight/lh in DESIGN.md §3 | Lint or snapshot test on computed styles in prototypes | [asserted] — check not yet shipped for typography |
| **Information density** | Rows per viewport, bands per screen, characters of telemetry per band | Named fixture + pixel snapshot or DOM query on prototype HTML | [asserted] |
| **Time-to-answer** | Seconds to answer frozen questions: "Are gates open?", "What is β and n?", "Is there an ask?" | Pre-registered task timing with N≥10 principal or proxy sessions (EXP not yet registered) | [asserted] |
| **Accessibility** | WCAG 2.1 AA on shipped surfaces; keyboard path for asks | axe or equivalent on offline HTML; keyboard-only walkthrough | [asserted] |
| **Data honesty** | No invented metrics; JSON contract match | Tests that dashboard reads fixture `consil --json` output only | [measured: ADR-0053 direction] |
| **Taste / atmosphere** | "Laboratory calm", "not ridiculous", "distinct without costume" | **Not measurable** — judgement | [asserted] |
| **Innovation / distinction** | Whether the surface looks like median AI-SaaS | Critique dimension 5; EXP-95 inter-rater reliability across model families | [asserted] until EXP-95 fires |
| **Composition / beauty** | Syne vs Cabinet, ochre vs amber balance, spacing "feel" | **Not measurable** — judgement | [asserted] |

**Who settles judgement:**

1. **Principal verdict** — authoritative for brand direction (Joe, 21 August 2026, recorded in
   ADR-0060). V0-18: approvals cannot be proxied. [measured]
2. **EXP-95 critique protocol** — two model families score rendered fixtures on five dimensions;
   Kendall $\bar{\tau}$ and Krippendorff $\alpha$ thresholds pre-registered in ADR-0060. Agreement
   between reviewers reading the same HTML is **echo**; **different model families** are a
   different class for *mechanical* defect detection, not for taste. [cited: Nielsen & Molich 1990
   via bibliography.md; ADR-0060]
3. **Bar document** — this file freezes yardstick claims; implementation reviews cite it, do not
   silently rewrite it.

**Plain statement:** Taste is not measurable; **pretending a critique score is a measurement is
forbidden** (working principle 5). The honest split is: **ship the linter for tokens; register the
timing experiment for tasks; run EXP-95 for critique signal; reserve atmosphere for the principal.**

## 5. Figma and Open Design — boundary and flow

| Tool | What it is for | What it cannot carry | Portability cost |
|---|---|---|---|
| **Open Design `DESIGN.md`** | Portable **9-section contract** agents execute; ban list; critique protocol; token lock; works in every harness via files (ADR-0060). | Pixel-perfect component specs across breakpoints without prose; rich animation choreography; principal's gestural "make it feel warmer" without translation. | **Travels** — plain text in repo; ADR-0084 compile target for harness instructions. [measured] |
| **Open Design desktop** | Optional **local visual editor** reading the same `DESIGN.md`; principal or designer inspects rendered direction without npm install. | Not a runtime dependency; unprobed on this machine as of 21 Aug 2026 except Joe's install report. | Low if outputs remain `DESIGN.md` + exported HTML prototypes in repo. [asserted] |
| **Figma** | **Human inspection canvas** — spacing tweaks, marketing compositions, stakeholder screenshots, component libraries for **connected** web/mobile builds that bundle fonts (DESIGN.md §3 offline exception). | Agent-executable truth without export; offline single-file dashboard (ADR-0053); secrets or metered cloud as source of truth. | **High** — binary `.fig` is not in git; Figma MCP OAuth has been broken for Claude Design→Code flows (ADR-0060 cites GitHub issues). Anything that **only** exists in Figma **does not travel** per ADR-0084 without a text export path. [cited: ADR-0060] |

**Recommended flow (`[asserted]` — inferred, not verbatim from the-machine):**

1. **Author or revise `docs/20-design/DESIGN.md`** (Open Design contract) — creation can start in
   chat with an agent, but the **artefact that ships is the file**, not the conversation.
2. **Prototype in repo** as single-file HTML under `docs/20-design/prototypes/` — passes token check.
3. **Optional Figma** for principal visual review or marketing — export **token table and screenshots
   back into DESIGN.md or ADR**, never let Figma alone be the spec.
4. **Optional Open Design desktop** to preview the same `DESIGN.md` the agents read.
5. **Critique** (EXP-95 when run) → **principal verdict** on judgement dimensions.

**What Figma adds:** faster spatial iteration for a human eye, shared component vocabulary with the
rest of the industry, plugin ecosystem (icons, illustration). **What it costs:** portability,
agent legibility, and CI enforceability unless every decision is **re-encoded** in `DESIGN.md` and
checks.

## 6. Pre-registered review tests

The incoming surface will be assessed against these questions, fixed before reading it:

1. **Contract.** Does a governing `DESIGN.md` exist and does `check_design_tokens.py` pass?
2. **ADR-0053.** One self-contained HTML file, no bundler, no framework import, offline-capable?
3. **Honesty.** Does every number on screen come from `consil --json` or a checked fixture?
4. **Metaphor.** Is the primary layout **state/trajectory**, not chat column + streaming tokens?
5. **Calm normal.** When healthy, does the resting screen say **nothing needs you** without hiding
   faults?
6. **Ask affordability.** Do active asks show artefact pointer, what was tried, default on expiry,
   and direct actions (ADR-0033 §3)?
7. **Colour discipline.** At most **one attention signal colour per region** excluding ask affordances?
8. **Tier read.** Can a principal answer gate/β/ask status in **≤3 seconds** on the bridge fixture?
9. **Keyboard.** Are primary actions reachable without mouse on desktop bridge?
10. **Incumbent bar.** Does it beat **Linear/Raycast** on density path, **Stripe** on numeric honesty,
    **Grafana** on tier read, and **Cowork** on structural non-chat layout — on the named tests above,
    not on vibes?

## 7. The single design decision that would most differentiate this product

**Decision:** Make **time-scrubbable trajectory inspection** the default resting surface — not a
chat transcript, not a kanban board, not a bento KPI grid — with **verifier-linked event causality**
as the primary visual object.

**Reasoning:**

- It is the only layout that treats **the append-only log as source of truth** (CONSILIENCE.md
  provenance clause; ADR-0062 command post not meta-harness). Chat UIs treat **model output** as
  truth; that is the β failure mode. [asserted]
- It imports a **different class of facts** — industrial HMI and observability tiering — rather
  than another chat skin. [cited: ISA-101; Grafana tier docs]
- It is **testable**: frozen log fixture + scrub interaction + timed questions on causality and β
  beats a chat scroll baseline. [asserted]
- Prototypes already exist (`trajectory-observatory.html`); the decision is **product priority**, not
  unexplored novelty.

**Killing check:** If timed tasks show principals **faster and more accurate** on a **well-designed
chat summary** than on trajectory scrub for the same frozen log, demote scrub to secondary and record
the failure — do not keep distinction for fashion. [asserted]

## 8. Evidence against — the serious case that design differentiation is the wrong investment

**The competence-not-distinction argument.** A renders-never-decides surface for one non-technical
principal earns **trust through correctness and quiet delivery** (ADR-0071), not through looking
unlike ChatGPT. If the JSON is wrong, **Syne and ochre make it worse** — they signal craft where
the oracle failed. The principal's success test for unification is **behavioural**: stop opening the
other seven tools — not "admire the dashboard." [measured: the-machine § job to be done]

**The fashionable-metaphor argument.** "Chat UI is dead" is **2026 discourse**, easy to write and
hard to prove. Cowork and Work are **growing execution depth** inside conversational shells; users
may prefer **one familiar column** over learning supervisory-control idioms. Arc's ambitious spatial
model **did not drive mass adoption** despite praise (Product Salon critique). [cited]

**The measurement-hypocrisy argument.** A project that refuses unfalsifiable claims cannot crown
**"more beautiful"** without becoming what it criticises. EXP-95 is not yet run; critique scores in
`critique-report.md` are **single-family `[asserted]`**. Until inter-rater reliability lands,
**distinction claims are as hollow as the README superlative this repo already had to retract.**
[measured]

**Response (not concession):**

- **Do not fund decoration ahead of contract enforcement.** Token check first; typography linter
  next; timed tasks registered — distinction follows discipline, not precedes it.
- **Do not argue taste wins users.** Argue **layout follows epistemology**: trajectory-first is honest
  about what Consilient knows (events), chat-first is honest about what a model said (narrative).
  That is architectural, not aesthetic — but it must **win timed tasks** or revert.
- **Accept partial defeat on "beauty"** if the principal stops opening other tools while the UI looks
  merely competent — **unification beats distinction** in his stated job-to-be-done. [asserted]

If timed-task evidence and behavioural unification both fail, **design differentiation is the wrong
investment** and resources should return to gate evidence and β measurement only.

## 9. Search and exclusion record

Searches covered: Linear, Vercel/Geist, Stripe dashboard and docs, Raycast, Arc, Things 3,
Observable/Plot, Datadog/Grafana operational patterns, Claude Cowork, ChatGPT Work, Gemini-class
UI comparisons, ISA-101 HMI, Open Design and Figma roles in ADR-0060/0084, repository DESIGN.md and
prototypes.

**Preferred:** primary product docs, regulator and standards pages, DesignMD/Open Design captured
benchmarks, academic DOIs, Anthropic/OpenAI product posts.

**Excluded:** screenshot-only mood boards without retrievable token tables; consultancy "UI trends
2026" without citations; training-recall claims without URL; **`../hireable-3.0` and
`../jobboard-v2`** (boundary).

**Negative searches:** No independent timed-task study comparing chat-first vs trajectory-first for
agent orchestration was found; absence is the boundary of this review, not proof of absence.
[measured]

## 10. Plain answer and delta

**Plain answer:** Lock `DESIGN.md`, pass token check, tier the offline dashboard like an operations
console, reject chat-column AI shells, use Open Design text for portability and Figma only as an
optional human canvas, and settle taste through principal verdict plus EXP-95 — not model enthusiasm.

**Delta from plain answer:** Named **per-product bars** with retrievable citations; classified **what
survives of the 2023-metaphor claim**; mapped **measurable vs judgement** with settlement rules;
specified **Figma/Open Design boundary** against ADR-0084; named **one prioritised differentiating
decision** (trajectory scrub default) with a killing check; and recorded **Evidence against** without
pretending taste is a metric.

**ADR note:** This bar does **not** propose changing ADR-0060's nine-section contract. No new ADR
required. Next free decision number in repo is **0097** (0095–0096 occupied); verified 2026-08-23.
[measured]

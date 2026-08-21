# 0060. Adopt Open Design's portable contract and critique for design work; the desktop app is an optional local tool, not a runtime dependency

- **Status:** PROVISIONAL — pending EXP-95 (critique inter-rater reliability)
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (the direction, the brand thesis, the installation, the instruction
  that the ADR is needed); cloud agent (the mechanism and the distillation)
- **Inquiry tier reached:** T1 ground — a format and tooling adoption, no unknown parameter
- **Executable model:** none — a tooling choice with no free parameter to optimise.

## Context

Four forces converged on 21 August 2026.

### 1. The design gap is the widest gap in the harness

`harness-capabilities.md` records that design work is supplied by MCP servers (Figma) or
local bridges, and that no harness here has a native design capability. `[measured]`
ADR-0054 names "design with Figma plugins or OpenDesign" as a capability to route to;
naming is not integration. The result: every UI-generating task falls back to whatever the
model's pretraining median looks like. `[asserted]`

### 2. The orchestration gap between Claude Design, Cowork and Claude Code is documented

Claude Design's built-in MCP server OAuth flow has been broken — `anthropics/claude-code`
issues #69317 (closed), #77620 (open as of 21 Aug 2026), #84798 (closed). `[cited]` Two
community workarounds exist (`kuatecno/mcp-design`, `e-brokenc0de/claude-design-mcp`);
neither is installed. Joe reported this as a concrete pain point: design work done in Claude
Design cannot easily flow into Claude Code or Cowork sessions. Open Design, by contrast,
works through files (`DESIGN.md`) that every harness can already read — a structural
advantage for a meta-harness that orchestrates across vendors. `[asserted]`

### 3. Joe installed the Open Design desktop on 21 August 2026

`[asserted]` — not re-probed; the binary, version and reachable harnesses are unknown until
a probe runs. ADR-0007's supersession note states that "the prohibitions on a TUI, a
desktop app and a local web server survive intact." That prohibition is on *this project
building* a surface, not on a third-party tool being present on the operator's machine.
The desktop is present, not built by us, and unprobed. `[asserted]`

### 4. The brand thesis: outlier, not median

Joe's direction, 21 August 2026, distilled from three messages. The organisation is the
agent's; the words in the verbatim quotation are Joe's.

In the age of AI coding and design agents making every website, frontend and piece of
content look "great" but identical, **distinction is the scarce resource, not quality.**
Attention spans are short. Trust in online media is low. Every AI product uses the same
fonts, the same layouts, the same "thinking theatre." The pretraining median is now the
visible floor, and the floor is crowded.

Consilient's brand is pushing the boundaries of artificial and human intelligence — not
relying on pretraining to produce the "current right thing" but pushing the very idea of
what the best looks like. The brand, the design, the product all need to reflect that.

The frontend is not just a CLI. Consilient needs full web and mobile app designs — its
equivalent of Claude Cowork, Hermes Agent, ChatGPT Work and Gemini Spark — but its
architecture is fundamentally different: more autonomous, needs less frontend, and what
frontend it has must be more beautiful, more unique, and emphatically not the same stuff
every AI model spits out.

> "minimalist is good — overwhelm is real so differentiation without just looking
> ridiculous is a fine balance but we need to find it."
> — Joe, 21 August 2026

That thesis is `[asserted]` — it is a brand direction, not a measurement. But the
underlying observation — that AI-assisted output converges, raising individual quality
while reducing collective diversity — has been measured in an adjacent modality:

- `[cited]` Doshi & Hauser, *Science Advances* 10(28), 2024,
  DOI 10.1126/sciadv.adn5290: AI-assisted stories rated more creative individually while
  being measurably more similar to each other. Individual quality up, collective diversity
  down, described by the authors as a social dilemma.
- `[cited]` Kleinberg & Raghavan, PNAS 118(22), 2021, *Algorithmic monoculture and social
  welfare* — the formal model. Already cited in this repository as reference 17 of
  `docs/50-publications/P3-echo.md`.
- `[cited]` The "AI-slop median" scoring band (Innovation dimension, 0–4: "Generic AI-slop
  median") in the upstream Open Design critique skill names the same phenomenon from the
  design-craft side. The ban list is **not** from upstream — it is original to this
  repository.

One independent design pass exists (`frontend-concepts-kimi-2026-08-20.md`); a concurrent
pass was commissioned and is not in the repository; no comparison has been performed. The
frontend concept is unsettled. `[asserted]`

## Decision

### 1. The DESIGN.md contract is the portable design method

All design work in this repository uses the Open Design 9-section `DESIGN.md` format
(Visual Theme & Atmosphere, Color Palette & Roles, Typography Rules, Component Stylings,
Layout Principles, Depth & Elevation, Do's and Don'ts, Responsive Behavior, Agent Prompt
Guide).

**Tokens are the intended palette once locked.** An agent generating artefacts under a
locked `DESIGN.md` should not invent hex values, font stacks, or spacing outside the
declared palette. Deviation is reviewable, and the CI check that would enforce this is
owed — see Enforcement. Until that check ships, this is guidance carried by the skill,
not an enforced invariant, and the deviation is logged in `gate-bypass-log.md`.

The skill is `.agents/skills/using-open-design/`, carrying the template and a vendored
critique with provenance.

### 2. The 5-dimension critique is a structured observation, not a verifier

The critique (Philosophy consistency, Visual hierarchy, Detail execution, Functionality,
Innovation) draws on HCI literature and design-craft tradition.

**What the critique is.** A structured review that produces scored, evidence-cited
observations. It is more informative than "looks good" and less informative than a
deterministic instrument (a layout engine, a raster diff, a schema linter).

**What the critique is not.** It is not a verifier, not an acceptance signal, and not a
different class of facts in the strong sense of ADR-0010. A model assigning 0–10 scores to a
rendered page is still a model's judgement, and `design-capability-assessment-2026-08-20.md`
§5 explicitly rejected "LLM design critique harness" as echo without ground truth —
listing persona-prompted design critics among CUT structures. `[measured]` — read from the
committed file. `interface-beta-2026-08-20.md` item 6 refuses visual-LLM judges as
acceptance signals. `[cited]`

The skill requires critiques to be tagged `[asserted]`. A second critique from a different
model family is an optional upgrade, not a consilience — because the judgement is still the
model's, and different families sharing no ground truth do not escape the prior assessment's
objection.

**The narrow window where the critique adds a genuinely different signal:** when it
identifies mechanical defects observable only on the rendered surface — broken click targets,
unreadable contrast, orphaned layout elements, navigation failures. Those are implicit-
oracle observations in the sense of `qa-automation-and-the-anchor-problem.md`, and they are
the same class that `design-capability-assessment-2026-08-20.md` §1 permits (layout engine,
raster diff). The skill's Functionality dimension overlaps this window; the other four
dimensions do not.

### 3. The ban list is a default, and the brand thesis is its justification

The AI-SaaS visual cluster (Instrument Serif, IBM Plex, Inter/Geist paired with serif,
cyan–violet gradient, chat-column-as-product, bento-grid KPIs, thinking theatre, confidence
rings) is refused by default. A banned element may appear with a comment stating why the
context makes it appropriate.

The ban list is `[asserted]` — it names the observed pretraining median in the visual
modality, but no systematic measurement of that median exists here. Doshi & Hauser 2024
measured convergence in text; visual convergence is the same thesis applied to a different
modality and remains `[asserted]` until measured. The brand thesis (§4) provides the
directional justification: an outlier's visual identity cannot be the mode of its own
training distribution.

### 4. The brand direction: outlier identity, anti-median, boundary-pushing

Consilient's visual identity derives from its intellectual position:

- **The product measures whether tests can be trusted.** The brand is honest measurement,
  not reassuring theatre. A UI that shows "thinking…" animations, confidence rings, or
  streaming-token shimmer is presenting *process* as *product* — the exact inversion of
  what the harness does (ADR-0034: detect stalls by artefact progress, never by process
  identity). `[asserted]`
- **The product is autonomous.** The resting state is "nothing needs you." A design language
  that fills the screen with activity, notifications, chat messages and presence indicators
  contradicts the architecture. The UI's job is to be **quiet when nothing is owed and
  unmistakable when something is.** `[asserted]`
- **The product refuses echo.** A visual identity that could be produced by asking any
  frontier model "design me an AI product" is the definition of echo — the model reproducing
  shared training data, not introducing a different signal. The brand must be recognisably
  *not that*. `[asserted]`
- **The product pushes boundaries.** Not incrementally better within the current idiom, but
  questioning the idiom itself. The design question is not "which Inter weight?" but "why
  would we use a font that signals membership in the cluster we exist to outperform?"
  `[asserted]`

**The tension that decides the shape.** Distinction without absurdity. Minimalism is good —
overwhelm is real, attention is short, trust is low, and the pretraining median is already
"polished". But anti-median does not mean anti-usable, and different-for-its-own-sake is
just another kind of noise. The design problem is a fine balance: recognisably *not the
cluster*, but also recognisably *good*. Quiet enough to reward low attention spans, honest
enough to survive low trust, distinctive enough that a screenshot is attributable.
`[asserted]`

**What this does not settle.** It does not name the typeface, the palette, the layout
system, or the motion language. Those belong in the product's `DESIGN.md`, which is the
next deliverable after this ADR. It settles the *constraints* on that DESIGN.md:

- **The Anti-Median Rule:** the result must not be producible by a zero-shot frontier
  prompt. If you can get there by asking Claude or GPT "design me an AI product", it is
  echo.
- **The Outlier Principle:** distinction is the goal, not polish. Polish is table stakes;
  the pretraining median is already polished.
- **The Honesty Principle:** the design must reflect the architecture's actual behaviour —
  autonomous, quiet, evidence-over-narrative — not a reassuring fiction about it.
- **The Minimalism Constraint:** less, not more. Overwhelm is the failure mode of every
  dashboard product. The resting state is calm. Distinction comes from what is *absent* and
  what *remains*, not from adding spectacle.
- **The Ridiculous Test:** if the result looks like it was chosen to be contrarian rather
  than to serve the user, it has failed. Anti-median is a direction, not a licence to ignore
  craft.

### 5. The Open Design desktop is an optional local tool, not a runtime dependency

The distinction matters under ADR-0016 and `AGENTS.md`:

- **No `pip install`, `npm install`, or registry resolution** is added. The skill and its
  references are plain markdown files. No harness needs the desktop to function.
  `[measured]` — the skill file is readable without any binary.
- **The desktop, when installed, is an optional local tool** that reads the same `DESIGN.md`
  files the skill produces. It is not a dependency this project builds, maintains, or
  requires. ADR-0007's prohibition on building a desktop app is not engaged — the
  prohibition is on *this project* building a surface, not on a third-party tool being
  present. Joe's installation is `[asserted]` until probed; its capabilities are subject to
  ADR-0042's probe-before-trust rule. `[asserted]`
- **The relationship to upstream is ADR-0036's.** Adopt, contribute, never silently fork.
  Open Design (nexu-io/open-design) is Apache-2.0, actively maintained (~90 k stars,
  PRs merged on 21 August 2026), and has a documented contribution path
  (`CONTRIBUTING.md`, `od-contribute` skill). `[cited]` Improvements found here — to the
  critique, to the DESIGN.md format, to the skill protocol — are offered upstream per
  ADR-0036 §2. A fork is debt, logged and paid (ADR-0036 §4). **Note the tension:**
  ADR-0036 §2 says "not a vendored copy"; ADR-0016 §1 requires vendoring third-party skills
  ("read in full and committed… pin by content, not by registry reference"). This PR follows
  ADR-0016 for the skill content and ADR-0036 for the upstream relationship. The upstream
  URL is recorded in the vendored file. `[asserted]`

### 6. The frontend concept requires its own DESIGN.md before any artefact is generated

Consilient's frontend — web, mobile, the equivalent of Claude Cowork / Hermes Agent /
ChatGPT Work / Gemini Spark — is a different product and needs a different design:

- **Not a chat client.** ADR-0007 §2 and `frontend-concepts-kimi` §1 refuse the chat box;
  the centre is the trajectory record, not a conversation. `[asserted]`
- **More autonomous, less interactive.** ADR-0033 decides by default; the resting state is
  "nothing needs you" (`frontend-concepts-kimi` §3). `[asserted]`
- **Visually distinctive from every competitor.** Not a reskin of Cowork with a different
  logo. The ban list (§3) is the floor; the brand thesis (§4) is the aspiration. The
  DESIGN.md for the frontend must be something no frontier model would produce unprompted.
  `[asserted]`
- **Full web and mobile surfaces.** ADR-0053 authorised one local observability surface (a
  self-contained HTML file); the hosted web app and mobile verdict surface are the next two,
  gated on measurement (`frontend-concepts-kimi` §7, concepts C1–C3). `[asserted]`

**This ADR does not produce that DESIGN.md.** It provides the method (Open Design
contract), the brand constraints (§4), the upstream relationship (§5), and the review method
(the critique as a structured observation). The next step is a design brief under those
constraints, followed by a DESIGN.md authored under this skill's method, followed by the
critique as a second reader.

## Evidence

- `[measured]` No Open Design binary was found on this machine on 21 August 2026; the
  portable skill exists and is readable without one.
- `[cited]` Doshi & Hauser, *Science Advances* 10(28), 2024 — AI-assisted output raises
  individual quality while reducing collective diversity. The convergence claim in the brand
  thesis has been measured in text; visual convergence remains `[asserted]`.
- `[cited]` Kleinberg & Raghavan, PNAS 118(22), 2021 — the formal model of algorithmic
  monoculture. Already in this repository's bibliography (P3-echo ref. 17).
- `[cited]` Open Design is Apache-2.0, nexu-io/open-design, ~90 k stars, actively
  maintained. `CONTRIBUTING.md` documents the contribution path.
- `[cited]` Claude Design's built-in MCP server OAuth has been broken (anthropics/claude-code
  #69317 closed, #77620 open, #84798 closed as of 21 Aug 2026).
- `[cited]` ADR-0036 §2 governs the upstream relationship.
- `[cited]` `design-capability-assessment-2026-08-20.md` §5 rejected LLM design critique as
  echo; §1 requires aesthetic output labelled `unverified`. This ADR's §2 narrows the
  critique accordingly and does not claim it as a verifier.
- `[asserted]` Joe's brand thesis: outlier identity, anti-median, push the idea of what the
  best looks like. Distilled from three messages on 21 August 2026.
- `[asserted]` The ban list names the observed pretraining median in the visual modality. No
  systematic measurement of visual convergence exists.
- `[asserted]` Joe installed Open Design on his desktop on 21 August 2026.

## Evidence against

- **The brand thesis is taste, not measurement.** "We are the outliers" is a positioning
  statement. Doshi & Hauser 2024 measured the convergence phenomenon in text, not in visual
  design; extrapolating to the visual modality is `[asserted]`. The risk: a brand thesis
  adopted without measurement becomes an unfalsifiable preference. `[asserted]`
- **"Anti-median" can produce anti-quality.** Refusing the pretraining median does not
  guarantee the replacement is better. The critique's Functionality and Hierarchy dimensions
  are the checks against novelty-for-its-own-sake. `[asserted]`
- **The critique is weaker than §2's framing implies.** `design-capability-assessment` §5
  rejected LLM design critics as echo. `interface-beta-2026-08-20.md` item 6 refuses
  visual-LLM judges as acceptance signals — and a model assigning 0–10 scores to a rendered
  page is a visual-LLM judge. This ADR narrows the critique to structured observation, but
  the prior rejection is not formally superseded. `[cited]`
- **The ban list is taste.** No systematic measurement of model design output distributions
  exists in the visual modality. `[asserted]`
- **Open Design is one project's convention, not a standard.** Mitigated by vendored copy
  and simple markdown format. `[asserted]`
- **The token-lockdown guidance has no shipped check.** Logged in `gate-bypass-log.md` as a
  deviation from I1. `[asserted]`
- **The desktop installation is unprobed.** `[asserted]` until a probe runs.
- **The critique has no measured inter-rater reliability.** EXP-95 is registered to test
  this. `[asserted]`
- **The frontend concept is unsettled.** This ADR provides the method but not the result.
  The escape: the DESIGN.md template is quick to fill, and filling it *is* the design
  decision. `[asserted]`
- **ADR-0016 and ADR-0036 pull in opposite directions on vendoring.** ADR-0016 §1 requires
  vendoring skills; ADR-0036 §2 says "not a vendored copy." This PR follows ADR-0016 for
  skill content and ADR-0036 for the upstream relationship. The tension is named, not
  resolved. `[asserted]`

## Consequences

**Positive.** Design work now has a method that produces a lockable contract rather than
ad hoc prompts. The brand thesis is recorded and traceable rather than implied. The contract
is portable across all four harnesses. The critique provides a structured second reading.
Upstream contributions are documented.

**Negative.** One more skill to maintain. The token-lockdown check is owed. The ban list
may need revision as pretraining distributions shift. The desktop installation is unprobed.
The brand thesis is `[asserted]` and could calcify into dogma if not tested.

**Neutral but load-bearing.** The frontend DESIGN.md is now explicitly the next step, and
it cannot be skipped by generating UI directly. Every agent workflow and prompt that touches
design work should respect the ban list and the brand constraints.

## Enforcement

- **Token-lockdown check:** owed, not shipped. The check would verify that colour hex
  values, font-family declarations, and border-radius values in governed files match the
  declared palette. When shipped, it goes in the same commit as the implementation (I1).
  Until then, the deviation is logged in `docs/00-context/gate-bypass-log.md`.
- **Fails CI:** not yet.
- **Added in the same commit:** no — owed. This is an acknowledged I1 deviation.

## What would overturn this

- **EXP-95 (critique inter-rater reliability):** two model families score the same five
  rendered artefacts on the five dimensions. If scores do not correlate (Kendall τ < 0.3
  across dimensions), the critique is noise. If they correlate, the critique is a weak but
  real signal and §2's framing is vindicated.
- **A systematic measurement of visual output convergence** across frontier models on a
  design-generation task. Doshi & Hauser measured text; if visual output does not converge,
  the ban list loses its empirical motivation. If it does converge on different elements than
  the ban list names, the list needs revision.
- **Open Design going unmaintained** or its format fragmenting.
- **The brand thesis being tested against real users** and found to repel.

## Publication candidate?

Possibly, but the novelty claim must be narrowed. The convergence phenomenon (individual
quality up, collective diversity down) is already published — Doshi & Hauser 2024 in text,
Kleinberg & Raghavan 2021 as the formal model. What may be novel is the narrow mapping:
anti-median aesthetics as an instance of Whewell's second clause (different class of facts
applied to visual identity). That is a smaller claim than previously stated, and it is
`[asserted]` — no measurement exists of whether the mapping holds.

# 0060. Adopt Open Design's portable contract and critique for design work; the desktop app is a supported composition element, not a runtime dependency

- **Status:** PROVISIONAL
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
model's pretraining median looks like, and that median converges on a recognisable cluster
— Instrument Serif, IBM Plex, Inter/Geist, cyan–violet, bento KPIs, thinking theatre —
that users identify as "every AI product looks the same". `[asserted]`

### 2. The orchestration gap between Claude Design, Cowork and Claude Code is measured

Claude Design's built-in MCP server OAuth flow is broken as of 21 August 2026
(anthropics/claude-code#69317, #77620, #84798; the `/authorize` endpoint returns HTTP 410).
`[cited]` Two community workarounds exist (`kuatecno/mcp-design`,
`e-brokenc0de/claude-design-mcp`); neither is installed. Joe reported this as a concrete
pain point: design work done in Claude Design cannot easily flow into Claude Code or
Cowork sessions. Open Design, by contrast, works through files (`DESIGN.md`) that every
harness can already read — a structural advantage for a meta-harness that orchestrates
across vendors. `[asserted]`

### 3. Joe installed the Open Design desktop on 21 August 2026

`[asserted]` — not re-probed; the binary, version and reachable harnesses are unknown until
a probe runs. This makes it a composition element on his machine, and composition elements
need a recorded decision about their relationship to the harness.

### 4. The brand thesis: outlier, not median

Joe, 21 August 2026 (distilled from three messages; the words below are the agent's
organisation of his direction, not a verbatim transcript):

> In the age of AI coding and design agents making every website, frontend and piece of
> content look "great" but identical, **distinction is the scarce resource, not quality.**
> Attention spans are short. Trust in online media is low. Every AI product uses the same
> fonts, the same layouts, the same "thinking theatre." The pretraining median is now the
> visible floor, and the floor is crowded.
>
> Consilient's brand is **pushing the boundaries of artificial and human intelligence** —
> not relying on pretraining to produce the "current right thing" but pushing the very idea
> of what the best looks like. **We are the outliers.** The brand, the design, the product
> all need to reflect that.
>
> The frontend is not just a CLI. Consilient needs **full web and mobile app designs** —
> its equivalent of Claude Cowork, Hermes Agent, ChatGPT Work and Gemini Spark — but its
> architecture is fundamentally different: more autonomous, needs less frontend, and what
> frontend it has must be **more beautiful, more unique, and emphatically not the same stuff
> every AI model spits out.**

That thesis is `[asserted]` — it is a brand direction, not a measurement. But it is
consistent with two things already in evidence:

- `[cited]` The pretraining-median convergence is observable. Open Design's own ban list and
  "AI-slop median" scoring band (Innovation dimension, 0–4) name the same phenomenon from
  the design-craft side.
- `[asserted]` `CONSILIENCE.md` clause 2 already requires **different**, and the different-
  class rule (ADR-0010) already refuses echo. A visual identity that is the pretraining
  median is echo in a literal sense — the model reproducing its training distribution rather
  than introducing a new signal. The brand thesis is an instance of the exogenous-signal
  rule applied to aesthetics.

The two design concept documents (`frontend-concepts-kimi-2026-08-20.md` and any concurrent
pass) are a `[simulated]` tie with overlapping CIs. The frontend concept is unsettled and
needs further work — but this ADR now provides the method, the brand constraint, and the
upstream relationship by which that work proceeds.

## Decision

### 1. The DESIGN.md contract is the portable design method

All design work in this repository uses the Open Design 9-section `DESIGN.md` format
(Visual Theme & Atmosphere, Colour Palette & Roles, Typography Rules, Component Stylings,
Layout Principles, Depth & Elevation, Do's and Don'ts, Responsive Behaviour, Agent Prompt
Guide).

**Tokens are non-negotiable once locked.** An agent generating artefacts under a locked
`DESIGN.md` must not invent hex values, font stacks, or spacing outside the declared
palette. A violation is a defect, not a style choice.

The skill is `.agents/skills/using-open-design/`, carrying the template and a vendored
critique with provenance. It is procedure, not an invariant; the token rule is enforceable
by a CI check on files governed by a `DESIGN.md`, but that check is owed, not shipped in
this commit.

### 2. The 5-dimension critique is a different class of facts

The critique (Philosophy consistency, Visual hierarchy, Detail execution, Functionality,
Innovation) draws on HCI literature and design-craft tradition. Under ADR-0010's
exogenous-signal rule, it qualifies as a different induction from source-code review and
from `[simulated]` user studies, provided it runs on a **rendered artefact**. A critique of
source is echo.

The critique is not an acceptance signal. It is a structured observation that raises or
lowers confidence. Acceptance remains a human verdict (working principle 5,
`interface-beta-2026-08-20.md` item 6).

### 3. The ban list is a default, and the brand thesis is its justification

The AI-SaaS visual cluster (Instrument Serif, IBM Plex, Inter/Geist paired with serif,
cyan–violet gradient, chat-column-as-product, bento-grid KPIs, thinking theatre, confidence
rings) is refused by default. A banned element may appear with a comment stating why the
context makes it appropriate.

The ban list was `[asserted]` when it named the pretraining median. It now has a second
leg: Joe's brand thesis says Consilient is an outlier, and an outlier's visual identity
cannot be the mode of its own training distribution. That is still `[asserted]` — no
measurement of the median exists — but the direction is recorded and adopted.

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
enough to survive low trust, distinctive enough that a screenshot is attributable. Joe,
21 August 2026: "minimalist is good — overwhelm is real so differentiation without just
looking ridiculous is a fine balance but we need to find it." `[asserted]`

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

### 5. The Open Design desktop is a supported composition element, not a runtime dependency

The distinction matters under ADR-0016 and `AGENTS.md`:

- **No `pip install`, `npm install`, or registry resolution** is added. The skill and its
  references are plain markdown files. No harness needs the desktop to function.
  `[measured]` — the skill file is readable without any binary.
- **The desktop, when installed, is a composition element** in ADR-0027's sense: it reads
  the same `DESIGN.md` files the skill produces, and its capabilities are subject to the
  same probe-before-trust rule as any other composition element (ADR-0042, ADR-0054). Joe's
  installation is `[asserted]` until probed.
- **The relationship to upstream is ADR-0036's.** Adopt, contribute, never silently fork.
  Open Design (nexu-io/open-design) is Apache-2.0, actively maintained (~90 k stars,
  811 open issues, PRs merged on 21 August 2026), and has a documented contribution path
  (`CONTRIBUTING.md`, `od-contribute` skill). `[cited]` Improvements found here — to the
  critique, to the DESIGN.md format, to the skill protocol — are offered upstream per
  ADR-0036 §2. A fork is debt, logged and paid (ADR-0036 §4).

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
(the 5-dimension critique as a different class of facts). The next step is a design brief
under those constraints, followed by a DESIGN.md authored under this skill's method,
followed by the critique as a second reader.

## Evidence

- `[measured]` No Open Design binary was found on this machine on 21 August 2026; the
  portable skill exists and is readable without one.
- `[cited]` Open Design is Apache-2.0, nexu-io/open-design, ~90 k stars, actively
  maintained. `CONTRIBUTING.md` documents the contribution path.
- `[cited]` Claude Design's built-in MCP server OAuth is broken as of 21 August 2026
  (anthropics/claude-code#69317, #77620, #84798). The file-based `DESIGN.md` contract
  avoids this class of integration failure entirely.
- `[cited]` ADR-0036 §2: "When an adopted dependency needs to change, the default is a
  pull request upstream."
- `[asserted]` Joe's brand thesis: outlier identity, anti-median, push the idea of what the
  best looks like. Distilled from three messages on 21 August 2026.
- `[asserted]` The ban list names the observed pretraining median. No systematic measurement
  exists.
- `[asserted]` The critique qualifies as a different class of facts under ADR-0010, with the
  rendered-artefact caveat.
- `[asserted]` Joe installed Open Design on his desktop on 21 August 2026.

## Evidence against

- **The brand thesis is taste, not measurement.** "We are the outliers" is a positioning
  statement. It does not follow from any evidence in this repository. The claim that
  distinction is the scarce resource in the age of AI-generated design is plausible and
  widely observed but is `[asserted]` here. The risk: a brand thesis adopted without
  measurement becomes an unfalsifiable preference that resists correction. Mitigated by §4's
  explicit `[asserted]` tags and by the design critique providing a structured second opinion
  on whether a result actually achieves distinction. `[asserted]`
- **"Anti-median" can produce anti-quality.** Refusing the pretraining median does not
  guarantee the replacement is better. A typeface chosen *because* no AI would pick it may be
  a bad typeface. The critique's Functionality dimension (does it *work*?) and the Hierarchy
  dimension (can a stranger read it?) are the checks against novelty-for-its-own-sake. The
  brand thesis says "push boundaries", not "ignore usability". `[asserted]`
- **The ban list is taste.** Same as the previous draft's objection: no systematic
  measurement of model design output distributions exists. `[asserted]`
- **Open Design is one project's convention, not a standard.** The 9-section format is not
  an ISO, a W3C spec, or even a broadly-adopted community norm outside Open Design's
  ecosystem. Adopting it couples us to their format decisions. Mitigated: the format is
  simple markdown, the sections are sensible, and the vendored copy insulates against
  upstream drift. `[asserted]`
- **"Tokens are non-negotiable" is an invariant stated without a shipped check.** Per
  ADR-0014, a skill saying "always do X" is a prompt pretending to be enforcement. The
  token-lockdown rule needs a CI check. That check is owed and not shipped. `[asserted]`
- **The desktop installation is unprobed.** `[asserted]` until a probe runs.
- **The critique is one reviewer's judgement.** No inter-rater reliability measurement
  exists for these five dimensions. `[asserted]`
- **The frontend concept is unsettled, and this ADR risks becoming a gate that delays it.**
  "We can't design until we have a DESIGN.md" can stall indefinitely. The escape: the
  DESIGN.md template is quick to fill, and filling it *is* the design decision, not a
  prerequisite to one. `[asserted]`

## Consequences

**Positive.** Design work now has a method that produces a lockable contract rather than
ad hoc prompts. The brand thesis is recorded and traceable rather than implied. The contract
is portable across all four harnesses. The critique provides a structured second reading.
Upstream contributions are documented. The frontend direction is constrained by the brand
without being prematurely settled.

**Negative.** One more skill to maintain. The token-lockdown check is owed. The ban list
may need revision as pretraining distributions shift. The desktop installation is unprobed.
The brand thesis is `[asserted]` and could calcify into dogma if not tested against real
user response.

**Neutral but load-bearing.** The frontend DESIGN.md is now explicitly the next step, and
it cannot be skipped by generating UI directly. Every agent workflow and prompt that touches
design work must respect the ban list and the brand constraints. That is a
gate-before-generation constraint, which is the point.

## Enforcement

The DESIGN.md token-lockdown rule is stated but not yet enforced by a CI check. The check
would: for any HTML/CSS file that names a governing `DESIGN.md` (via a comment or
metadata), verify that colour hex values, font-family declarations, and border-radius
values match the declared palette. Owed; not shipped in this commit. When shipped, it goes
in the same commit as the implementation it checks (I1).

The brand constraints (§4) are procedure, carried by the skill, not a CI-enforceable
invariant. The critique is the review mechanism; the skill's ban list is the prompt-level
guard. This is an acknowledged weakness: a prompt-level guard is exactly what ADR-0014
warns against. The honest answer is that aesthetic invariants are harder to lint than
structural ones, and the critique is the best instrument available until a visual-
regression tool (e.g. a screenshot-diff that flags banned-font usage) is built. `[asserted]`

## What would overturn this

- **A systematic measurement of model design output distributions** showing the ban list is
  wrong.
- **The brand thesis being tested against real users** and found to repel rather than
  attract. Distinction is only valuable if people want what is distinct; "different" and
  "good" are not synonyms.
- **Open Design going unmaintained** or its format fragmenting. The vendored copy insulates;
  a format migration would be owed.
- **The critique having no inter-rater reliability.**
- **A better design method emerging** that subsumes the markdown contract.

## Publication candidate?

Possibly. The brand thesis — that the pretraining median is the new floor and distinction is
the scarce resource — is an observation with broad applicability. If the ban list is ever
measured rather than asserted, the measurement and the method would be worth a short post.
The "anti-median as an instance of the exogenous-signal rule" argument is, if correct,
genuinely novel and connects aesthetics to `CONSILIENCE.md` in a way that has not been
written elsewhere. `[asserted]`

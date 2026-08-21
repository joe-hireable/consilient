---
name: using-open-design
description: >
  Use before generating UI, choosing a visual direction, prototyping a frontend,
  or reviewing any design artefact in this repository. Covers authoring a
  DESIGN.md contract (the 9-section Open Design format), the ban list that
  refuses the AI-SaaS visual cluster, running the 5-dimension critique as a
  different class of facts, and why the Open Design desktop app is optional.
  Trigger on "design system", "DESIGN.md", "visual direction", "design review",
  "critique", "design tokens", "pick a look", "frontend prototype", "UI style",
  or any request to generate a user-facing surface.
---

# Using Open Design — portable design contracts for agentic harnesses

Open Design is a local-first, agent-driven design method. The portable contract
is `DESIGN.md` — a 9-section file that locks visual tokens before any artefact
is generated. Coding agents (Codex, Cursor, Grok CLI, Claude Code) become the
design engine; the 400 MB desktop app and Open Design Cloud are optional and are
**not** required by this skill. The desktop app was not found on this machine on
21 August 2026 `[measured]`; Joe reported installing it later that day
`[asserted]` — not re-probed.

## When to use this skill

- **Before generating any UI.** Lock a `DESIGN.md` first. An artefact generated
  without one inherits whatever the model's pretraining median looks like, and
  that median has a name — see the ban list.
- **When choosing a visual direction** for a product, prototype, or experiment.
- **When reviewing a design artefact** — run the 5-dimension critique
  (`references/critique-upstream.md`) as a structured review.
- **When a brief says "make it look good"** without stating what "good" means.
  The DESIGN.md contract forces the nine decisions a designer makes before any
  pixel is placed.

## What you produce

### 1. A DESIGN.md contract

Copy the template from `references/DESIGN-TEMPLATE.md` and fill every section.
The nine sections are:

1. **Visual Theme & Atmosphere** — mood, density, what the design is *not*.
2. **Color Palette & Roles** — named roles + hex values. No unnamed colours.
3. **Typography Rules** — font stacks, scale, line-height, family count limit.
4. **Component Stylings** — buttons, cards, inputs, links, with state
   transitions.
5. **Layout Principles** — grid, max-width, gutters, section spacing.
6. **Depth & Elevation** — shadow specification per level.
7. **Do's and Don'ts** — concrete constraints.
8. **Responsive Behavior** — breakpoints, column counts, stacking rules.
9. **Agent Prompt Guide** — the non-negotiable token rule.

**Tokens are non-negotiable once locked.** Section 9 must state: *do not invent
hex values outside this palette*. An agent that needs a colour the palette does
not carry must produce a warning, not a silent invention.

### 2. A 5-dimension critique (when reviewing)

Run the critique from `references/critique-upstream.md`. Score across:

1. Philosophy consistency — one direction, or three styles in a trench coat?
2. Visual hierarchy — can a stranger read it in order?
3. Detail execution — alignment, leading, kerning, spacing edge cases.
4. Functionality — does it work for its use?
5. Innovation — does it push past the median?

Each dimension is scored 0–10 with **cited evidence** — element names, line
numbers, class names. Numbers without evidence are rejected. Produce Keep / Fix
/ Quick-wins lists.

## The ban list — the AI-SaaS visual cluster

The pretraining median of every frontier model converges on a recognisable
cluster. Refuse it by name:

- **Instrument Serif** as the display face in a product that is not a magazine.
- **IBM Plex** as the default "serious" stack.
- **Inter / Geist** paired with a serif display as if that is a design decision.
- **Cyan–violet gradient** as the accent palette.
- **Chat-column-as-product** layout (single scrolling column, no information
  architecture).
- **Bento-grid KPI cards** as the hero of a landing page.
- **"Thinking theatre"** — animated dots, streaming-text shimmer, pulsing orbs
  presented as features rather than loading states.
- **Confidence rings / radial gauges** as the primary data visualisation.

None of these is wrong in the right context. All of them are wrong as the
*default*, because "every AI product looks the same" is a real user complaint
and the pretraining median is the mechanism.

An artefact that uses a banned element must carry a comment stating why the
context makes it appropriate. Silence is not consent; it is the median.

## The brand direction — outlier, not median

ADR-0060 records the brand thesis. The short version:

In the age of AI agents making everything look "great" but identical,
**distinction is the scarce resource, not quality.** The pretraining median is
the visible floor, and the floor is crowded. Consilient's brand is pushing the
boundaries of what the best looks like — not relying on pretraining to produce
the "current right thing" but questioning the idiom itself.

Five constraints on any `DESIGN.md` authored for this project:

1. **Anti-Median Rule.** The result must not be producible by a zero-shot
   frontier prompt. If asking Claude or GPT "design me an AI product" would
   get you there, it is echo.
2. **Outlier Principle.** Distinction is the goal, not polish. Polish is table
   stakes.
3. **Honesty Principle.** The design reflects the architecture: autonomous,
   quiet, evidence-over-narrative. No reassuring fictions.
4. **Minimalism Constraint.** Less, not more. Overwhelm is the failure mode.
   Distinction comes from what is *absent* and what *remains*, not from
   spectacle.
5. **Ridiculous Test.** If the result looks contrarian rather than considered,
   it has failed. Anti-median is a direction, not a licence to ignore craft.

These are `[asserted]` — brand direction from the principal, not measured. The
critique's Functionality and Hierarchy dimensions are the checks against
novelty-for-its-own-sake.

## What the critique is and is not

The 5-dimension critique is a **structured observation**, not a verifier and not
an acceptance signal. `design-capability-assessment-2026-08-20.md` §5 rejected
LLM design critics as echo without ground truth; `interface-beta-2026-08-20.md`
item 6 refuses visual-LLM judges. A model assigning 0–10 scores to a rendered
page is a visual-LLM judge, and this skill does not claim otherwise.

**What it adds over "looks good":** scored dimensions with cited evidence,
reproducible across reviewers, and a structured action list. That is more
informative than an unstructured opinion and less informative than a
deterministic instrument (a layout engine, a raster diff, a schema linter).

**The narrow window where it adds a genuinely different signal:** when it
identifies mechanical defects observable only on the rendered surface — broken
click targets, unreadable contrast, orphaned layout elements, navigation
failures. Those are implicit-oracle observations. The Functionality dimension
overlaps this window; the other four dimensions are the model's judgement.

All critique scores are tagged `[asserted]`. Acceptance remains a human
verdict (working principle 5). The critique raises or lowers confidence; it
does not gate.

## What this skill does not do

- **Does not pick a Consilient frontend winner.** The frontend concept is
  undecided. This skill provides the contract format and the review method; it
  does not collapse that into one DESIGN.md "for the product". That decision
  belongs to the principal.
- **Does not install the Open Design desktop, daemon, or `od` CLI.** The harness
  uses `DESIGN.md` + critique as files. If the desktop app is installed
  separately, it reads the same `DESIGN.md`; nothing here depends on it.
- **Does not add a runtime dependency.** No npm package, no pip install, no
  registry resolution. ADR-0016 and `AGENTS.md` both forbid it.
- **Does not route design work to a specific harness.** ADR-0054 routes by
  measured capability, not by label. Which harness generates UI is a dispatch
  question, not a skill question.

## Workflow

### Starting a new surface

1. Decide whether an existing DESIGN.md in this repository applies. If yes,
   reference it. If no, copy `references/DESIGN-TEMPLATE.md` to the
   appropriate location.
2. Fill every section. Do not leave placeholders; unfilled sections are
   decisions deferred, and deferred decisions are the median.
3. Run the ban-list check against your filled DESIGN.md. If any banned element
   appears without a justifying comment, revise.
4. Lock the file. From this point, agents generating artefacts under this
   system treat the tokens as non-negotiable.

### Reviewing an existing artefact

1. Identify the governing DESIGN.md (or note its absence — that is finding #1).
2. Open the rendered artefact (HTML in a browser, not source in an editor).
3. Score each of the 5 dimensions per `references/critique-upstream.md`.
4. Produce Keep / Fix / Quick-wins.
5. Tag the review `[asserted]` — it is one reviewer's judgement, not a
   measurement. A second reviewer from a different model family upgrades it to
   a small consilience.

### Pasting the portable core for harnesses that cannot read this file

Codex, Cursor, and Grok CLI read `AGENTS.md`, not `.agents/skills/`. When
dispatching design work to one of those harnesses, paste the following into
the brief:

> **Design contract:** before generating any UI, lock a DESIGN.md with 9
> sections (Visual Theme, Color Palette & Roles, Typography, Component
> Stylings, Layout Principles, Depth & Elevation, Do's and Don'ts, Responsive
> Behavior, Agent Prompt Guide). Tokens are non-negotiable once locked. Do not
> invent hex values outside the palette. Refuse the AI-SaaS cluster by default:
> Instrument Serif, IBM Plex, Inter/Geist paired with serif, cyan–violet
> gradient, chat-column layout, bento KPIs, thinking theatre, confidence rings.
> Brand constraints: the result must not be producible by a zero-shot frontier
> prompt (anti-median rule); distinction over polish; design reflects the
> architecture (autonomous, quiet, honest); minimalism — less, not more;
> anti-median is not anti-usable.
> After generating, score the artefact on 5 dimensions (Philosophy consistency,
> Visual hierarchy, Detail execution, Functionality, Innovation) each 0–10 with
> cited evidence. Produce Keep / Fix / Quick-wins lists.

## Harness support

Portable core: everything above. The skill is procedure, not a tool call, and
is deliberately harness-agnostic.

- **Claude Code** reads it via the `.claude/skills/` symlink into `.agents/skills/`.
- **Codex, Cursor, Grok CLI** reach it through `AGENTS.md`, which points at
  this directory. For dispatched briefs, paste the portable core above.
- **OpenHarness, DeepSeek Harness** read `SKILL.md` natively.
- **Open Design desktop** (if installed separately) reads the same `DESIGN.md`
  files; nothing here depends on it.

## Adapted from

`nexu-io/open-design` (Apache-2.0, Open Design contributors) — the 9-section
`DESIGN.md` contract format and the 5-dimension critique skill. The ban list is
original to this repository, derived from the instruction's observation that
frontier-model pretraining produces a convergent visual median. Scoring bands
and evidence-citation discipline are from the upstream critique skill; the
different-class-of-facts argument and the "critique is not an acceptance signal"
constraint are from this repository's existing doctrine (`CONSILIENCE.md`,
ADR-0010, `interface-beta-2026-08-20.md`).

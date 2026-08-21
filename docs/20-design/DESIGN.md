# Consilient Design System

> Status: `[asserted]` — official design system contract for Consilient web and mobile surfaces.
> Authored 21 August 2026 under ADR-0060 and the `using-open-design` skill.
> Governed by the Anti-Median Rule, Outlier Principle, Honesty Principle,
> Minimalism Constraint, and Ridiculous Test.

## 1. Visual Theme & Atmosphere

- **Mood:** Laboratory-grade precision meets editorial calm. Think Braun Dieter Rams
  hardware meets an unhurried scientific journal. Pure functional confidence with zero
  theatre.
- **Atmosphere:** Deeply quiet at rest. Dense with signal when inspected. Never noisy,
  never conversational, never begging for attention. The resting screen is a finished
  statement, not an open question.
- **What it is NOT:**
  - NOT a chat window (ADR-0007 / `frontend-concepts-kimi` §1). No streaming tokens,
    no typing bubbles, no conversational avatar.
  - NOT AI-SaaS (ADR-0060 ban list). No purple-cyan neon, no dark-mode glassmorphism,
    no bento KPI grids, no spinning orbs, no fake-confidence radial gauges.
  - NOT decorative minimalism. Every pixel carries data or creates spatial hierarchy.
    Whitespace is an information-density separator, not fashion.

## 2. Color Palette & Roles

<!-- American spelling in heading for Open Design validator interop.
     British English in body prose per AGENTS.md §7.
     Custom, desaturated laboratory tones derived from charcoal and ochre ramps;
     strictly avoids default Tailwind/bootstrap saturated triads (Anti-Median Rule). -->

### Dark Mode (Default / Primary)

- **Canvas (Ground):** `#0C0E12` (Deep Charcoal Black — neutral, un-tinted)
- **Surface 0 (Base Container):** `#14171E` (Dark Slate Surface — cards, resting containers)
- **Surface 1 (Elevated / Raised):** `#1C202A` (Focused / active element surface)
- **Surface 2 (Border / Divider):** `#2A2F3D` (1px boundary lines and structural rules)
- **Foreground Primary (Ink):** `#F0F2F5` (High-contrast pure neutral off-white; 17.2:1 contrast)
- **Foreground Secondary (Ink 2):** `#C4C9D4` (Clear secondary readable text; 11.8:1 contrast)
- **Foreground Muted:** `#8B93A5` (Labels, metadata, units; 6.3:1 contrast)
- **Foreground Tertiary:** `#8B93A5` (Timestamps, hashes, secondary annotations; passes WCAG AA on both Canvas and Surface 0 containers)

### Semantic Signal Colours (Used surgically; max 1 signal role per screen region)

- **Signal Action / Decision (Electric Ochre):** `#E2B340` (Primary interaction affordance, pending verdict)
  - Surface Tint: `#2A2412`
- **Signal Valid / Measured (Laboratory Green):** `#2E9E66` (Check passed, exact match, measured β; desaturated ~55%)
  - Surface Tint: `#11261C`
- **Signal Attention / Defect (Warm Ochre Amber):** `#DDA136` (Unmeasured gap, stopping rule near threshold, draft; desaturated ~65%)
  - Surface Tint: `#2B2012`
- **Signal Fault / Hard Failure (Terracotta Crimson):** `#E05349` (Verifier failed, bypass detected, secret violation; desaturated ~60%)
  - Surface Tint: `#2D1617`

### Light Mode (Secondary / High-Ambient)

- **Canvas (Ground):** `#F6F7F9`
- **Surface 0 (Base Container):** `#FFFFFF`
- **Surface 1 (Elevated / Raised):** `#ECEEF2`
- **Surface 2 (Border / Divider):** `#D6DAE2`
- **Foreground Primary (Ink):** `#0C0E12`
- **Foreground Secondary (Ink 2):** `#3D4453`
- **Foreground Muted:** `#6F778A`
- **Foreground Tertiary:** `#868F9F`
- **Signal Action (Light):** `#B88714` (Tint: `#FAF2DE`)
- **Signal Valid (Light):** `#23864F` (Tint: `#E9F6EF`)
- **Signal Attention (Light):** `#B57414` (Tint: `#FCF4E4`)
- **Signal Fault (Light):** `#C53030` (Tint: `#FDE8E8`)

*Rule: Never use saturated gradients. Never tint background black with purple or blue glow.*

## 3. Typography Rules

<!-- Strictly refuses Inter, Geist, IBM Plex, and Instrument Serif defaults.
     Pairs an ultra-crisp technical grotesk with high-readability scientific monospace. -->

- **Display & Headings:** `Syne`, `Cabinet Grotesk`, or fallback `ui-sans-serif, system-ui, -apple-system, sans-serif`
  - Weight: 600 (Semi-Bold) or 700 (Bold)
  - Scale: H1 = 31px (line-height 1.2, tracking -0.02em); H2 = 21px (1.25); H3 = 16px (1.3)
- **Body & UI Text:** `Plus Jakarta Sans`, or fallback `ui-sans-serif, system-ui, -apple-system, sans-serif`
  - Weight: 400 (Regular) and 500 (Medium)
  - Scale: Body = 14px / 15px (line-height 1.55); Meta/Label = 12px (line-height 1.4)
- **Data, Numbers & Telemetry (Mono):** `Space Mono` or `Fragment Mono`, fallback `ui-monospace, SFMono-Regular, Menlo, monospace`
  - Used for: β values, confidence intervals, sample counts (n=...), hashes, timestamps,
    command strings, code references.
  - Scale: 12px / 13px tabular numbers (`font-variant-numeric: tabular-nums`).
- **Font families permitted:** 3 dedicated roles (1 Display Sans + 1 Body Sans + 1 Data Mono).
- **Offline & Self-Contained Fallback Policy:** Per ADR-0053, offline single-file HTML dashboards
  render via local system fonts (`system-ui` / `ui-monospace`) when web fonts are not locally
  installed. Connected web/mobile builds bundle the primary typefaces via self-hosted assets.

## 4. Component Stylings

- **Telemetry & Status Cards:**
  - Flat `#14171E` background, 1px solid `#2A2F3D` border.
  - Radius: 8px–10px (structural, clean geometry; no bubbly 16px+ roundings or pills).
  - Internal padding: 16px 20px.
- **Buttons / Action Affordances:**
  - **Primary (Verdict / Action):** `#E2B340` background, `#0C0E12` dark text, weight 600, radius 6px, padding 8px 16px.
  - **Secondary (Inspect / View):** Transparent fill, 1px solid `#2A2F3D` border, `#F0F2F5` text.
  - **Destructive / Reject:** Transparent fill, 1px solid `#E05349` border, `#E05349` text.
  - Active state: scale(0.99) tactile push. No glowing box-shadows.
- **Data Tables & Metric Rows:**
  - Borderless horizontal divider layout with 1px `#1C202A` row separators.
  - Labels left-aligned in Foreground Muted; values right-aligned in Mono Tabular.
- **Asks & Verdict Prompts (ADR-0033 / ADR-0053 / §9):**
  - Contained modal block with 2px solid `#E2B340` top accent border.
  - Mandatory 4-part structure satisfying ADR-0033 §3 affordability requirements:
    1. *Artefact pointer & context* (branch, diff, boundary, verifier check outcomes)
    2. *What was already tried* (admitted local attempts, fallback executions)
    3. *Default action & consequence if expired* (e.g. task waits, no spend incurred)
    4. *Direct human action affordances* (Accept, Reject with comment, Authorise)

## 5. Layout Principles

- **Grid:** 12-column layout (max-width 1180px–1280px) on desktop; single-column stacked on mobile.
- **Bands over Bento:** The layout is divided into clear horizontal functional bands:
  1. *Header & System State* (Integrity, gates, current visibility level)
  2. *The β-Meter & Verifier Truth* (headline reliability measurement)
  3. *Autonomous Work Registry* (active runs, ceiling derivation, artefact timestamps)
  4. *Unavoidable Asks* (zero or one active action card)
- **Section Spacing:** 28px–32px between primary bands; 14px–16px between interior cards.
- **Rule of Restraint:** A screen region may contain at most ONE attention colour (`#E2B340` or `#E05349`), excluding explicit human decision affordances within an active ask container. All other elements must sit in the monochrome/slate hierarchy.

## 6. Depth & Elevation

- **Level 0 (Default / Flat):** 0px offset, no shadow. Background and 1px border create separation.
- **Level 1 (Elevated / Modal / Active Asks / Summary Cards):** `0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.6)`, 1px `#2A2F3D` border.
- *Strictly prohibited:* Glow shadows, coloured halo lights, frosted-glass backdrop blur (no `backdrop-filter: blur()`).

## 7. Do's and Don'ts

- ✅ **DO** show exact sample counts ($n$) and confidence intervals alongside any metric.
- ✅ **DO** state "nothing needs you" as a positive resting status when the system is healthy.
- ✅ **DO** use tabular monospace numbers for all telemetry, timestamps, and digests.
- ✅ **DO** link directly to local editor/worktree for code inspection.
- ❌ **DON'T** show streaming tokens, animated typing dots, or "thinking" pulses.
- ❌ **DON'T** use conversational chat bubbles as the primary interface.
- ❌ **DON'T** use Inter, Geist, IBM Plex, or Instrument Serif.
- ❌ **DON'T** use purple, violet, or cyan accent gradients.
- ❌ **DON'T** show thumbs-up/down or subjective satisfaction prompts.
- ❌ **DON'T** hide unmeasured uncertainty or round up low-sample estimates.

## 8. Responsive Behavior

<!-- American spelling in heading for Open Design validator interop. -->

- **Desktop (≥ 1024px):** 3-band layout, metrics horizontal, dual-column telemetry inspector.
- **Tablet (768px – 1023px):** Compact telemetry inspector, stacked work cards.
- **Mobile (< 768px):** Single vertical stream.
  - Prioritises **Hardware-Attested Verdicts** (C3 in `frontend-concepts-kimi` §7) and floor alerts.
  - Telemetry collapses into expandable single-line digests.
  - Action buttons (Accept/Reject/Authorise) occupy full-width tap targets (min height 48px).

## 9. Agent Prompt Guide

When writing frontends (web or mobile) for Consilient:
- Lock to the colour palette above. Do NOT invent new hex colours.
- Build clean, dense, data-honest components. State over narrative.
- Render what the `consil --json` contract produces; never invent mock statistics.
- If an ask is displayed, render the three mandatory affordability fields (ADR-0033 §3):
  1. What was tried
  2. Default action if expired
  3. Direct cost or consequence
- Refuse all AI-SaaS tropes by construction. If asked to add a conversational chat box, explain that Consilient's core is the append-only trajectory record and render the trajectory projection instead.

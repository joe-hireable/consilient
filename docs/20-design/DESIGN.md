# Consilient Design System

> The official DESIGN.md for Consilient web and mobile surfaces.
> Authored 21 August 2026 under ADR-0060 and the using-open-design skill.
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
     Palette designed around low-saturation, high-contrast, high-trust scientific tones. -->

- **Background (Canvas):** `#0C0E12` (Deep Charcoal Black — neutral, not blue-tinted)
- **Surface 0 (Base Layer):** `#14171E` (Dark Slate Surface — cards, resting containers)
- **Surface 1 (Elevated):** `#1C202A` (Focused / active element surface)
- **Surface 2 (Border / Divider):** `#2A2F3D` (Subtle boundary lines, 1px solid)
- **Foreground Primary (Text/Number):** `#F0F2F5` (High-contrast pure neutral off-white)
- **Foreground Secondary (Labels/Units):** `#8B93A5` (Cool slate muted metadata)
- **Foreground Tertiary (Muted):** `#535B6D` (Timestamps, digests, secondary annotations)

### Semantic Signal Colors (Used surgically, max 1 accent role per screen region)

- **Signal Valid / Measured (Green):** `#22C55E` (Check passed, exact match, measured beta)
- **Signal Attention / Defect (Amber):** `#F59E0B` (Unmeasured gap, stopping rule near threshold, draft state)
- **Signal Action / Decision (Electric Ochre):** `#E2B340` (Primary interaction affordance, pending verdict)
- **Signal Fault / Hard Failure (Red):** `#EF4444` (Verifier failed, bypass detected, secret violation)

*Rule: Never use saturated gradients. Never tint background black with purple or blue glow.*

## 3. Typography Rules

<!-- Strictly refuses Inter, Geist, and Instrument Serif defaults.
     Pairs an ultra-crisp technical grotesk with a high-readability scientific monospace. -->

- **Display & Headings:** `Syne`, `Cabinet Grotesk`, or fallback `-apple-system, system-ui, sans-serif`
  - Weight: 600 (Semi-Bold) or 700 (Bold)
  - Scale: H1 = 32px (line-height 1.2, tracking -0.02em); H2 = 22px (1.25); H3 = 16px (1.3)
- **Body & UI Text:** `Plus Jakarta Sans` or fallback `system-ui, sans-serif`
  - Weight: 400 (Regular) and 500 (Medium)
  - Scale: Body = 14px (line-height 1.5); Meta/Label = 12px (line-height 1.4)
- **Data, Numbers & Telemetry (Mono):** `Space Mono` or `Fragment Mono`, fallback `ui-monospace, monospace`
  - Used for: β values, confidence intervals, sample counts (n=...), hashes, timestamps,
    command strings, code references.
  - Scale: 12px / 13px tabular numbers (`font-variant-numeric: tabular-nums`).
- **Maximum font families permitted:** 2 (1 Sans + 1 Mono). Monospace is the workhorse.

## 4. Component Stylings

- **Telemetry & Status Cards:**
  - Flat `#14171E` background, 1px solid `#2A2F3D` border.
  - Radius: 6px (sharp, structural, no pill cards, no bubbly 16px+ roundings).
  - Internal padding: 16px 20px.
- **Buttons / Action Affordances:**
  - **Primary (Verdict / Action):** `#E2B340` background, `#0C0E12` dark text, weight 600, radius 4px, padding 8px 16px.
  - **Secondary (Inspect / View):** Transparent fill, 1px solid `#2A2F3D` border, `#F0F2F5` text.
  - **Destructive / Reject:** Transparent fill, 1px solid `#EF4444` border, `#EF4444` text.
  - Active state: scale(0.99) tactile push. No glowing box-shadows.
- **Data Tables & Metric Rows:**
  - Borderless horizontal divider layout with 1px `#1C202A` row separators.
  - Labels left-aligned in Foreground Secondary; values right-aligned in Mono Tabular.
- **Asks & Verdict Prompts (ADR-0033 / ADR-0053):**
  - Contained modal block with 2px solid `#E2B340` top accent border.
  - Explicit layout: (1) Artefact pointer, (2) Checks breakdown, (3) Default if expired, (4) Direct action buttons.

## 5. Layout Principles

- **Grid:** 12-column layout (max-width 1280px) on desktop; single-column stacked on mobile.
- **Bands over Bento:** The layout is divided into clear horizontal functional bands:
  1. *Header & System State* (Integrity, gates, current visibility level)
  2. *The β-Meter & Verifier Truth* (headline reliability measurement)
  3. *Autonomous Work Registry* (active runs, ceiling derivation, artefact timestamps)
  4. *Unavoidable Asks* (zero or one active action card)
- **Section Spacing:** 32px between primary bands; 16px between interior cards.
- **Rule of Restraint:** A screen region may contain at most ONE attention color (`#E2B340` or `#EF4444`). All other elements must sit in the monochrome/slate hierarchy.

## 6. Depth & Elevation

- **Level 0 (Default / Flat):** 0px offset, no shadow. Background and 1px border create separation.
- **Level 1 (Modal / Active Asks / Context Sheets):** `0px 8px 24px rgba(0, 0, 0, 0.45)`, 1px `#2A2F3D` border.
- *Strictly prohibited:* Glow shadows, colored halo lights, frosted-glass backdrop blur (no `backdrop-filter: blur()`).

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
- Lock to the color palette above. Do NOT invent new hex colors.
- Build clean, dense, data-honest components. State over narrative.
- Render what the `consil --json` contract produces; never invent mock statistics.
- If an ask is displayed, render the three mandatory affordability fields:
  1. What was tried
  2. Default action if expired
  3. Direct cost or consequence
- Refuse all AI-SaaS tropes by construction. If asked to add a conversational chat box, explain that Consilient's core is the append-only trajectory record and render the trajectory projection instead.

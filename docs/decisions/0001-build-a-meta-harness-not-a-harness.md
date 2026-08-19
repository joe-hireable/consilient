# 0001. Build a meta-harness above existing coding agents, not a standalone harness

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — the decision turns on competitive and maintenance facts, not
  on a parameter whose value is unknown. Gate G4 (formalizability) is not satisfied.

## Context

The stated goal was "the best harness in the world", orchestrating Claude Code, OpenCode,
Codex and Antigravity CLI in parallel. That framing contains a category error: orchestrating
*whole agents* is a layer above a harness, not a harness. The decision is whether to build
at the harness layer (competing with well-funded incumbents and one very popular free one)
or the layer above it (a category with two early entrants and no owner).

This is close to a one-way door: the adapter surface, the ticket schema and the trajectory
format all follow from it.

## Decision

Build a meta-harness. Orchestrate existing coding agents through adapters; do not
reimplement tool loops, sandboxes, session stores or permission prompts.

## Evidence

- `[cited]` DeepSeek Harness shipped 13 Aug 2026 under MIT with an everything-is-a-plugin
  Cordis kernel; ~135k GitHub stars within four days. The harness layer now has a free,
  frontier-lab-maintained entrant.
- `[cited]` **HKUDS/OpenHarness** (MIT, 14.8k stars, v0.1.9) is a second full harness with
  43 tools, skills, plugins, hooks, permission modes, MCP and subagent coordination — plus
  `ohmo`, which already ships credential bridging to existing Claude Code / Codex
  subscriptions and Feishu/Slack/Telegram/Discord gateways. Two independent, well-starred,
  MIT harnesses now occupy this layer. See `../10-research/competitive-landscape.md`.
- `[cited]` Claude Code, Codex CLI, opencode and Antigravity CLI are all actively maintained
  with substantial teams. opencode alone is ~193–198k stars.
- `[cited]` The meta-harness category exists but is unclaimed: Omnigent (Databricks,
  Apache 2.0, Jun 2026) and Vercel AI SDK v7's HarnessAgent API (Jun 2026) are the only
  entrants found.
- `[cited]` DeepSeek Harness orchestrates *models*, not agents — so it is a candidate
  orchestratee, not a competitor at this layer.
- `[asserted]` A meta-harness runs on subscriptions already paid for (Max plan), rather than
  metered API spend. Materially changes the economics for a solo unfunded project.

## Evidence against

- `[cited]` **Meta-Harness** (Lee, Nair, Zhang, Lee, Khattab & Finn — Stanford/KRAFTON/MIT,
  COLM 2026, arXiv:2603.28052) automates harness design end-to-end and reports a **6×
  performance gap** achievable by changing the harness around a fixed model. If that gap is
  real and capturable, the harness layer may be where the value is, and building above it
  forfeits access. **This is not resolved.** See `../00-context/open-questions.md` Q1.
- `[asserted]` Adapter surfaces across four independently-evolving CLIs are a permanent
  maintenance tax with no ceiling. One vendor changing its session model breaks us.
  Open as Q5.
- Single reviewer, one session, declared conflict of interest (the reviewer's maker
  publishes one of the four target agents).

## Consequences

**Positive.** Inherit four teams' engineering, model access and release cadence for free.
Compete only on routing policy, verification, memory and the permission model. Economics
work on existing subscriptions.

**Negative.** Permanently downstream of four vendors' decisions. Cannot fix a bug in the
agent layer — only route around it. Every new agent is new adapter work.

**Neutral but load-bearing.** Fixes the ticket schema as the interface, and makes the
trajectory record an aggregation across heterogeneous agents rather than a native artefact.

## Enforcement

None required — this is a scope decision, not an invariant.

## What would overturn this

- Q5 resolves badly: a minimum viable adapter interface across the four CLIs turns out to be
  unmaintainable by one person.
- Meta-Harness's 6× claim proves capturable at the harness layer specifically, and
  inaccessible from above it.
- A vendor closes their agent to external orchestration.
- **Open alternative (added 2026-08-19):** shipping the β-meter as a *plugin to an existing
  harness* rather than as a standalone meta-harness. OpenHarness has the right integration
  surface (PreToolUse/PostToolUse hooks, plugin system, tool registry) and a nonzero user
  base. This is not the same as the rejected DeepSeek-plugin option and deserves an explicit
  argument in the brainstorm rather than rejection by analogy.

## Publication candidate?

No. This is a project-scoping decision with no general result.

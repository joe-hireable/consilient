# 0098. Permit one authenticated local surface, superseding the blanket prohibition

- **Status:** ACCEPTED
- **Date:** 2026-08-23
- **Deciders:** Joe Brown (principal), orchestrator
- **Supersedes:** 0007 in part — the prohibition on a local surface. Its reasoning about the chat metaphor survives intact.
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — the decision variable is a prohibition, and no unknown parameter separates the options.

## Context

ADR-0007 forbids a terminal UI, a desktop application and a local web server. ADR-0053 permits
exactly one artefact: a single offline HTML file, with no server and no authentication. That was a
good decision for a product whose only job was to render a record after the fact.

It cannot carry what the principal specified on 23 August 2026. A `file://` page cannot stream live
state and cannot authenticate a write. Under the existing prohibition, **live observability,
steering a running agent, generated session interfaces and live voice are all forbidden by our own
decision record** — not by difficulty, and not by any safety argument that was ever made about them.

This is a one-way door. Once a local authenticated surface exists it becomes the thing users depend
on, and withdrawing it later is not a real option.

## Decision

We permit **one** local surface, authenticated, and supersede ADR-0007's prohibition to that extent.
It is a single surface, not a family: one chat as the resting state, a settings control, and one
entry point to the observability layer. Every capability it exposes must also be reachable by
talking to the chat, so the graphical surface is a view onto what the conversation can already do
and never the only route to an action.

ADR-0007's substantive reasoning is **not** overturned. Its refusals of the chat-window metaphor —
streaming token theatre, typing bubbles, a conversational avatar, an interface that begs for
attention — remain binding, and `../20-design/DESIGN.md` continues to enforce them.

## Evidence

- `[measured]` The prohibition blocks the principal's stated requirements. Recorded in
  `../20-design/observability-steering-and-embodiment-2026-08-23.md`, which reached D1 as a gate it
  could not resolve: a `file://` page cannot stream state or authenticate a write.
- `[measured]` ADR-0053's offline single-file dashboard exists and works for rendering. The gap is
  writes and liveness, not rendering.
- `[asserted]` The principal, 23 August 2026: "users can click to perfect interfaces for
  observability, governing, steering etc for users that want more fine grained control at any time",
  with the zero-click default being chat plus voice.
- `[asserted]` One authenticated surface is a smaller change than the three the prohibition
  currently forces: CLI-only steering, a render-only observability layer, and no sessions at all.

## Evidence against

- `[cited]` `../20-design/frontend-concepts-kimi-2026-08-20.md` section 2 lists twelve interface
  refusals, each with a citation or an invariant behind it. That analysis is why ADR-0007 exists and
  it is good work. **This ADR narrows the prohibition; it does not dismiss the argument.**
- `[asserted]` The honest risk is drift. A permitted surface accumulates features, and the thing
  ADR-0007 protected against arrives gradually rather than at once. The Enforcement section is the
  answer, and it is a weaker answer than a flat prohibition was.
- `[measured]` ADR-0083 records that `append()` has no cross-process serialisation and the
  trajectory already contains malformed concurrent lines. **A surface accepting writes before
  write-ordering is repaired would silently lose commands**, which is worse than no surface. The
  Enforcement section sequences them for that reason.

## Consequences

**Positive** — live observability, steering, sessions and voice become buildable. The design work
completed on 23 August 2026 stops being blocked by a prohibition that never contemplated it.

**Negative** — authentication on a local surface is real work with real failure modes and is now on
the critical path. A local listener is also an attack surface that a `file://` page is not.

**Neutral but load-bearing** — every future interface question now argues against this ADR rather
than against a flat prohibition, which is a lower bar. The chat-parity rule is what keeps that bar
meaningful, and it is the part to defend.

## Enforcement

- Check: `.github/scripts/check_surface_parity.py` — refuses a surface action with no documented
  chat equivalent, so the graphical surface cannot become the only route to a capability.
- Check: the surface refuses writes while `events.append` lacks cross-process serialisation, gated
  on ADR-0083's repair landing first. It ships render-only until then.
- Fails CI: yes, both.
- Added in the same commit as the implementation: yes. **Neither check exists today**, and until
  they run in `invariants.yml` this ADR's constraints are prose rather than chokepoints.

## What would overturn this

A measured finding that the surface is used as a substitute for the chat rather than a view onto it
— specifically, actions taken through the surface with no chat equivalent — would mean the parity
rule failed and the prohibition was right. Reverting means deleting the listener and returning to
ADR-0053's offline file, which stays supported for exactly that reason.

# 0058. Build dispatch as a script and reserve the `consil` surface

- **Status:** ACCEPTED
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (principal)
- **Inquiry tier reached:** T1 ground - direct principal authority plus repository constraints
- **Executable model:** none - this is a reversible interface boundary, not an optimisation
  with an unknown parameter

## Context

Joe Brown authorised working orchestration after finding that the paid harnesses still had to be
routed by hand: **"I WANT TO BE ABLE TO USE CONSILIENT MYSELF TO PROPERLY ORCHESTRATE ALL THE
HARNESSES WITHOUT HAVING TO SHOUT AT YOU WITH ALL OF THIS FRICTION ... WE HAVE NEARLY $1000 OF
MONTHLY MAX SUBSCRIPTIONS AND WE CAN'T BUILD A SIMPLE CLI?"** [cited] - principal instruction,
21 August 2026.

Stage 3 permits supervised construction under ADR-0039, while Gate B still blocks unattended or
default dependence. [cited] - ADR-0039. The product tree is refuse-only and the shipped `consil`
surface remains pinned to `record`, `replay`, `beta`, and `doctor`. [measured]

## Decision

Build supervised dispatch now as `scripts/dispatch.py`. Keep registry, fail-closed selection and
event validation in `src/consilient/`; keep process execution in `scripts/`. Do not add a `consil`
subcommand, and do not change `routing_orchestration_enabled`; Joe reserves that public-surface
decision. Every attempt records supervision through `events.append()`.
While Gate B is closed, the runner refuses working directories outside this checkout. [cited] -
ADR-0039.

Model-family fan-out is useful disagreement sampling, but shared task facts do not become a
different evidence class merely because two model families read them. [asserted]

## Evidence

- `[cited]` The principal explicitly requested a working command and specified the script boundary.
- `[measured]` The existing AST guard rejects subprocess capability under `src/consilient/`.
- `[measured]` The CLI parser and its guard still expose exactly four observe-only commands.

## Evidence against

- `[asserted]` A standalone script is less discoverable than a `consil dispatch` command.
- `[asserted]` Dated user-attested percentages embedded in the registry will become stale, and
  percentages from weekly and monthly pools do not express equal quantities of work. This MVP can
  make a wrong choice after the snapshot changes even while its ordering code is correct.
- `[asserted]` Installation probing is weaker than authenticated capability and live quota probing.

## Consequences

**Positive** - supervised subscription dispatch, capture, and fan-out are usable without opening
the public CLI or the gates.

**Negative** - headroom changes require a registry update; `silent` detects absence, not artefact
quality.

**Neutral but load-bearing** - fan-out results remain separate observations, not a consilience
claim.

## Enforcement

- Check: `tests/test_dispatch.py` plus the existing CLI-surface and product-capability guards
- Fails CI: yes
- Added in the same commit as the implementation: yes

## What would overturn this

Joe choosing a `consil` command, or a subscription runtime exposing a safe live headroom endpoint,
replaces the corresponding temporary boundary without changing the trajectory contract.

## Publication candidate?

No.

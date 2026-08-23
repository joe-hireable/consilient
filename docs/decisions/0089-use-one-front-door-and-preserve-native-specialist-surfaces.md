# 0089. Use one front door and preserve native specialist surfaces

**Correction:** Hermes has a documented Figma MCP route, Claude Dispatch already routes between
Cowork and Code, and several named products expose cross-surface integrations. The decision cannot
rest on "no incumbent can"; it rests on a bounded search finding no documented all-eight
affordance-preserving surface and on refusing to call generic screen access equivalence. [cited:
`../00-context/subscription-reach-2026-08-22.md`] [asserted: bounded official-source search,
2026-08-22]

- **Status:** PROPOSED — the retirement behaviour is unmeasured and EXP-129 is specified in the
  companion document but deliberately unwritten in the experiment register. [measured]
- **Date:** 2026-08-22. [measured]
- **Deciders:** Joe Brown supplied the singular-interface requirement recorded in
  `../00-context/the-machine-2026-08-22.md`; Codex dispatch
  `20260822T165007-c1c47652e5` proposes this mechanism. Principal adoption is not claimed.
  [measured]
- **Inquiry tier reached:** T1 ground — current source, trajectory aggregates, local teardowns and
  retrieved incumbent surfaces were inspected; the behavioural comparison has not run. [measured]
- **Executable model:** none — transport/affordance support is categorical and the unknown outcome
  is observed direct opening, owned by the unwritten EXP-129 candidate. [asserted]

## Context

The principal wants one interface instead of separately choosing among Claude Code, Cowork, Claude
Design, Figma, SuperGrok, Grok Bot, Cursor and ChatGPT Work. The product criterion is behavioural:
whether direct opening of those surfaces falls. [measured:
`../00-context/the-machine-2026-08-22.md`] [asserted]

The premise supplied with that criterion overreached. The pinned Hermes source includes a Figma MCP
recipe; the 2026-08-22 official-source sweep also retrieved partial unifiers including Claude
Dispatch, ChatGPT Work plus Codex, OpenHands Agent Canvas, Hermes, Ruflo and Grok Bot. No retrieved
source demonstrated native control of all eight, but a bounded failure to find is not universal
absence. [cited: `../00-context/subscription-reach-2026-08-22.md`;
`../00-context/ruflo-teardown-2026-08-22.md`] [asserted]

The current Consilient path has exactly four CLI arms: Claude, Cursor, Grok and Codex. Cursor and
Grok have produced local dispatch artefacts; Claude is executable but has no accepted dispatch
outcome canary. Cowork, Claude Design, Figma's canvas, Grok Bot and ChatGPT Work have no explicit
arm. [measured: `../../src/consilient/harness.py`; `../../scripts/dispatch.py`; local trajectory
projection, 2026-08-22]

Capability selection is not capability use. `capabilities.py` returns metadata that `dispatch.py`
places in brief prose; no endpoint, native configuration, credential reference or connection handle
is bound into the child. Ambient MCP names may be present, but no task-scoped pass-through has been
demonstrated. [measured: `../../src/consilient/capabilities.py:171-194`;
`../../scripts/dispatch.py:1248-1272`]

ADR-0070 already owns conversation-to-commitment compilation, ADR-0074 owns durable capability
identity/recall, and ADR-0084 owns per-harness binding and semantic refusal. Re-specifying any of
them here would create another source of truth. [cited: ADR-0070; ADR-0074; ADR-0084]

## Decision

Consilient will present one front door over the existing trajectory and dispatcher, while preserving
native specialist surfaces whenever their working medium or authority boundary would be lost.
[asserted]

1. **Share intake, not every renderer.** User words, commitment, bounded recall, authority,
   capability receipts, work-item state, spend/headroom and outcome provenance are shared. Code
   terminals/editors, design canvases, research browsers, artefact viewers and native permission
   prompts may remain distinct. [asserted]
2. **Reuse the existing selection path.** ADR-0070 compiles the request; required capability and
   different evidence class filter eligible compositions; existing headroom/family selection
   chooses among them; `routing.py` constrains attempts when measured beta permits; `dispatch.py`
   invokes. No UI router, task store or orchestrator is added. [asserted]
3. **Make native hand-off a typed outcome.** A task that needs a native surface returns a hand-off
   carrying its commitment/work-item reference, bounded context digest, reason, expected artefact
   and retained principal authority. It never appears as completion. [asserted]
4. **Do not use screen access as an equivalence claim.** Browser/computer use may execute a proved
   canary, but does not retire a native surface until task outcome, manual takeover, authority and
   lost-affordance checks pass. [asserted]
5. **Adopt the retirement table in the companion specification.** Claude Code and Cursor agent work
   are retireable for their recorded headless task classes; SuperGrok, Claude Design and Cowork are
   partially absorbable; Figma, ChatGPT Work and Grok Bot cannot presently be replaced. SuperGrok
   becomes a third retirement only under the narrower Grok Build task class. [measured] [asserted]
6. **Use three specific retirements as the build threshold.** Claude Code, Cursor agent work and
   Grok Build work are the low-cost candidate set. EXP-129 must show the reduction; a count of three
   unrelated products does not satisfy the decision. [asserted]
7. **Keep privacy and authority absolute.** Measurement records command-post hand-offs, eight
   weekly fixed task-class occurrence/direct-open pairs and one minimal task-completion receipt for
   each eligible baseline or candidate task. The receipt contains only opaque identity, fixed class,
   expected artefact reference, pre-existing verifier/result and adverse outcome. No task text or
   process/window surveillance is collected. Missing self-report means `unknown`; a class that did
   not occur supplies no retirement evidence. Agents may propose but may not author verdict,
   consent, approval, gate lift or spend. [cited: ADR-0057] [asserted]
8. **Keep the current safety state.** `routing_orchestration_enabled` remains `false`; Gate A and
   Gate B do not change. While human-labelled beta is unestimated, one Owner may prepare one
   candidate but automatic verifier exposure is zero. Additional evidence roles require
   decision-changing different classes of facts but do not each consume candidate exposure; the
   first or any later independently acceptable candidate requires the exact authenticated
   human-labelled candidate-exposure projection required by ADR-0077. [cited: ADR-0067, ADR-0077;
   verdict-supply §§ 2, 4-5] [measured] [asserted]

The complete retirement rows, loss ledger, policy, hand-off shape, search record and unwritten
experiment candidate are fixed in
`../superpowers/specs/2026-08-22-one-surface.md`. [asserted]

## Evidence

- `[measured]` Current executable probes reached Claude Code, Cursor Agent, Grok and Codex; the
  current source contains a concrete invocation branch for each.
- `[measured]` The local trajectory contains 38 Cursor outcomes (20 `ok`) and 29 Grok outcomes
  (five `ok`), with refusals, timeouts and killed runs retained. These establish transport/artefact
  production, not accepted quality.
- `[measured]` Claude Code and Cursor are present in recoverable repository-origin records; Cowork's
  original record is partial; Joe-specific Figma, Work and direct consumer-SuperGrok task classes
  are not recoverable and remain asserted.
- `[measured]` Capability selection has no runtime consumer beyond brief-text injection. This is the
  exact advisory-type-without-consumer failure ADR-0084 records.
- `[cited]` ADR-0060 preserves a portable `DESIGN.md` contract while retaining the distinction
  between design artefact and native visual work.
- `[cited: ../00-context/product-bar-2026-08-22.md;
  ../00-context/hermes-teardown-2026-08-22.md;
  ../00-context/ruflo-teardown-2026-08-22.md]` The frozen product bar and local teardowns establish
  substantial partial unifiers and specialist advantages; the all-eight claim is not an evidenced
  novelty claim.
- `[asserted]` A shared record plus explicit specialist hand-off is the smallest design that can
  reduce tool choice without pretending that a conversation reproduces a canvas or IDE.

## Evidence against

**Unification may be the wrong goal.** Specialised products preserve domain state precisely because
their work differs: spatial selection and multiplayer context in Figma, continuous code navigation
in Cursor, project/schedule state in Cowork, and artefact preview/annotation in Work. A common chat
can be worse at all of them while looking administratively neat. [asserted]

**The abstraction tax may exceed the switch.** The command post adds natural-language compilation,
capability negotiation, receipts, delivery projection and a hand-off card. If the end state is still
"open Figma", the user may have paid more attention than opening Figma directly. No local timing
measurement shows otherwise. [asserted]

**The market already supplies partial front doors.** Claude Dispatch routes Cowork/Code, ChatGPT's
desktop contains Work/Codex, Agent Canvas drives several coding agents, and Hermes combines broad
tools, MCP and computer use. Building comparable polish before measuring the remaining gap risks
duplicating moving incumbents. [asserted: bounded official-source retrieval, 2026-08-22]

**A single-harness product would ship sooner.** Going deep on Claude Dispatch would inherit Cowork,
Code, connectors, computer use and Figma reach with less adapter maintenance. It would also abandon
Cursor/SuperGrok subscription use and make Consilient's evidence/authority record subordinate to a
vendor surface. Whether the latter costs more than four adapters is unmeasured. [asserted]

**A native launcher may be the complete product.** A thin router that opens the correct tool with a
bound context card could capture most of the switching benefit without absorbing any specialist.
This ADR chooses that architecture now: absorb evidenced headless work and hand off the rest. If
EXP-129 shows no direct-open reduction, stop there. [asserted]

## Consequences

**Positive** — Joe gets one place to state intent and recover the record; dispatchable work can stay
behind it; specialist hand-offs preserve the medium and make incomplete reach visible. [asserted]

**Positive** — Capability metadata cannot masquerade as a live connection, and screen access cannot
masquerade as native equivalence. [asserted]

**Negative** — The result is not literally one application. Some tasks still open native products,
and the hand-off record adds friction. [asserted]

**Negative** — The two retirement verdicts are task-class scoped. A later interactive debugging or
visual-editing workload can require reopening Claude Code or Cursor and must be reported as a failed
retirement week, not explained away. [asserted]

**Neutral but load-bearing** — ADR-0070 owns intake, ADR-0074 memory/manifest identity, ADR-0084
binding, `events.py` the record, `work_items.py` lifecycle, `coordination.py` claims,
`routing.py` beta ceilings, `budget.py` spend, and `dispatch.py` invocation. This ADR adds no second
implementation of them. [cited: ADR-0070; ADR-0074; ADR-0084] [asserted]

## Enforcement

This PROPOSED ADR changes no product behaviour. Current CI does not prove the front-door or hand-off
contract. Each authorised implementation increment must add its smallest central check in the same
commit: [measured] [asserted]

- a source ratchet keeps chat out of `dispatch.py` parsing and keeps selection in the existing
  capability/headroom/routing path; [asserted]
- every selected capability records `applied`, explicit `degraded` or pre-launch `refused`; prompt
  prose cannot satisfy an MCP/connection requirement; [asserted]
- Figma, Work and Grok Bot fixtures cannot reach `completed` through an unsupported or screen-only
  path; a valid native hand-off remains awaiting external work; [asserted]
- hand-off records bind commitment/work-item/context digests and cannot mint or replay principal
  authority; [asserted]
- measurement stores hand-off identity, the eight fixed occurrence/direct-open pairs and the same
  minimal task-completion receipt in both arms; rejects window/process/task-text telemetry; and
  treats a missing required receipt, missing self-report or non-occurrence as insufficient evidence;
  [asserted]
- the command set, both gate conditions and `routing_orchestration_enabled` remain unchanged.
  [measured] [asserted]

- **Check:** future focused work-item/capability/handoff/privacy tests plus existing V0 invariants.
  [asserted]
- **Fails CI:** no for the future checks today; this is a specification decision. [measured]
- **Added with implementation:** required for every later increment. [asserted]

## What would overturn this

EXP-129 is not registered. Once written unchanged to the experiment register and run, it overturns
the retirement goal unless all three named task classes have qualifying baseline/candidate
occurrences, each changes from a direct baseline opening to no direct candidate opening, verified
completion by the companion specification's same-class rate does not fall, surveillance beyond the
fixed pairs/receipts/hand-offs is unnecessary, and no agent-authored principal act occurs. Missing
class occurrences or receipts produce insufficient evidence, not a pass. [asserted]

Before implementation, an eight-row artefact canary against Claude Dispatch and Hermes should record
transport, authentication/manual takeover, latency, artefact, authority and native-affordance loss;
Grok Bot and Agent Canvas follow if either exposes a supported entry point. A competitor that passes
all eight with lower switching/review cost should be adopted as the front door under ADR-0065 rather
than rebuilt. [asserted]

If a thin native launcher achieves the same direct-open reduction as absorbed execution, delete the
absorption layer and retain the launcher plus shared record. If fewer than the three named low-cost
surfaces are active in ordinary work, the count criterion is invalid and outcome-weighted switching
must replace it before a build decision. [asserted]

## Publication candidate?

**No.** The broad incumbent claim required correction, the mechanism is unimplemented, newly
retrieved sources await bibliography promotion, and EXP-129 is unwritten and unrun. [measured]

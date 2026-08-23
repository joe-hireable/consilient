# 0092. Classify durable work and stop deliberation at an external threshold

- **Status:** PROVISIONAL — EXP-135 can remove threshold stopping as a quality claim while retaining
  the taxonomy and honest handovers
- **Date:** 2026-08-23
- **Deciders:** Codex dispatch `20260823T102440-daf985aa65` for the provisional mechanism. Joe
  Brown's verbatim 23 August product direction is input, not authorship of this decision.
- **Inquiry tier reached:** T1 ground; T3 pre-registered as EXP-135, not run
- **Executable model:** none — whether the threshold is measurable and improves accepted artefacts
  requires matched real work; assumed scores would manufacture both unknowns
- **Supersedes:** ADR-0090 only for category definitions, transition admission and threshold/give-up
  semantics; ADR-0090 retains modes, profiles and effort allocation

## Context

The principal specified three semantic phases: locate the best existing bar; determine and achieve a
markedly better answer through research, debate, simulation, experimentation and assessment; then
realise and deliver it. He also corrected the earlier 80/20 illustration: the transition is a
better-than-best threshold, not a configured ratio. [measured:
`../00-context/the-machine-2026-08-22.md`, "The phase transition is a threshold, not a ratio"]

His later 23 August correction requires every category to be executable as a native agent and
separates worker method from subject-matter expertise. The in-flight ADR-0093 stream is responsible
for that agent catalogue, fact contracts, portable assembly, open-data/adoption requirements and
training boundary; this ADR remains the owner of the work meanings and phase transition and does not
claim those controls exist. [measured: `../00-context/the-machine-2026-08-22.md`,
"Categories are agents, not labels; and two axes, not one"; ADR-0093] [asserted]

ADR-0090 owns modes, profiles, aggregate request budgets, phase/category charges, `exceed_cap`,
`realisation_reserve`, forecasts and hard-total exhaustion. Its in-flight draft also defined the
taxonomy and transition while this companion was being written, despite the briefs assigning those
concerns here. This decision therefore reuses its `phase`, `effort.transition` and status names but
supersedes their overlapping meanings; it does not add a second state machine or budget ledger.
[measured] [asserted]

ADR-0081 specifies, but does not implement, a consilience gate for mechanically full or protected
conclusions. It gives model/provider family, role, persona, confidence, vote and repeated context zero
structural credit; qualifying anchors must use different acquisition channels, distinct observation
identities and known disjoint derivation roots. The incoming brief's family-only evidence premise is
therefore wrong. [measured]

ADR-0077 makes beta bound shippable candidate exposure under a dependence-robust union bound; ADR-0067
separately makes one Owner the default and requires an unavailable decision-relevant anchor before a
role is added. The incoming iid logarithmic squad-size formula is diagnostic, not governing policy.
[measured] [algebra]

Current `work_items.py` has open/comment/complete events but no category, semantic phase or handover;
the generic `events.py` boundary does not validate such a contract. `events.py` remains the sole
append-only writer, and the existing dispatch, coordination, recall, instruction, routing and budget
paths are the substrates to extend. [measured: source inspection, 2026-08-23]

The full protocol is specified in
[`2026-08-23-work-taxonomy.md`](../superpowers/specs/2026-08-23-work-taxonomy.md). [measured]

## Decision

Consilient will use a closed v1 `work_category` taxonomy for every new durable full-mode work unit:
`framing`, `discovery`, `research`, `experiment`, `simulation`, `debate`, `innovation`, `synthesis`,
`assessment`, `planning`, `implementation`, `verification` and `delivery`. There is no free-text or
`other` category. The first ten are pre-doing; the final three are doing. Extensions require a
versioned schema change and successor decision; missing historical categories remain `unavailable`.
[asserted]

Each unit also carries one immutable, compatible ADR-0090 `phase`: `locate`, `exceed` or `realise`.
A unit whose purpose crosses a category boundary closes with its artefact and opens a linked unit; it
is never relabelled in place. This protocol applies only to `full + better-than-best`; light has no
durable work item, and full+fast makes no better-than-best claim. [asserted]

Categories are not passive labels: ADR-0093 maps each category one-to-one to a native task-scoped
worker profile and separately composes subject expertise. This ADR does not define those roles. One
Owner remains the default, and an additional runtime or assessor must name a decision-relevant fact
unavailable to the Owner or non-overlapping artefact scope; reading the same artefact under another
title or family is echo. [measured: ADR-0067; ADR-0081; ADR-0093] [asserted]

Hypotheses remain frozen artefacts inside experiment, simulation or innovation; mathematical
modelling is a simulation/instrument mode; data science is classified by the purpose of the data
operation; and specification is synthesis/planning unless the specification itself is the requested
implementation artefact. These do not enlarge the closed work enum. [asserted: ADR-0093]

`locate` produces a content-addressed bar package: incumbent identity and scope, retrieved citations
and digests, its demonstrated achievement, search log and near misses, limitations, comparison
procedure, a candidate-independent material delta and non-regression constraints. It exits to
`exceed` only through an `effort.transition` carrying `bar_located`. If retrieval cannot establish a
citable bar, it returns terminal `bar_unresolved` and no better-than-best threshold exists. This
supersedes ADR-0090's in-flight clause allowing `bar_unresolved` to enter `exceed`. [asserted]

`exceed` freezes its threshold before candidate results. `bar_beaten` requires a matched executed
comparison to the bar's own achievement, improvement of at least the frozen material delta, every
must-pass constraint, and a convergent ADR-0081 pair under the same frozen contract. A different
model family contributes nothing unless it acquires a qualifying world anchor; opinion, confidence,
vote, shared-corpus agreement, shared derivation roots, snippets and unvalidated simulations cannot
open the transition. The mechanically derived assessment carries the bar/candidate digests,
comparison receipts and qualifying references. [asserted]

The principal's "any means necessary" direction means any existing capability admitted by the
frozen authority, safety, spend, privacy, gate and effect boundaries; it grants no credential,
metered call, publication, unsafe action or gate bypass. [measured] [asserted]

Before `exceed` begins, ADR-0090's `effort.plan` freezes `exceed_cap`, a finite ordered set of
acquisition/assessment steps with costs and largest plausible effects, `realisation_reserve` and the
selection rule for the best safe candidate. Give-up fires at the first of: `exceed_cap`; exhaustion
of the step set; the next step not fitting while preserving `realisation_reserve`; or, after an
executed comparison produced a numeric gap, every remaining step being incapable of closing it. An
unavailable gap cannot fire the last branch. The `effort.transition` records `bar_not_beaten`, which
means superiority was not demonstrated, plus the measured gap or `unavailable`; it is not an
affirmative measured loss. The best safe candidate carries forward when ordinary authority, safety
and budget permit. Hard-total exhaustion remains ADR-0090's `incomplete` outcome and starts no
implementation. [asserted]

`effort.transition` hands `realise` the candidate digest, `bar_beaten|bar_not_beaten`, measured gap or
`unavailable`, comparison and anchor receipts, dissent, rejected alternatives, plan, verifier,
authority, budget and reversal. `realise` implements without reopening the goal or verifier,
executes terminal verification, and delivers only within existing authority. Delivery must retain
`bar_not_beaten`; it cannot advertise better-than-best. [asserted]

The record extends `work_items.py` through `events.py`, the universal writer. Category, phase and
handover validation live at that universal boundary rather than only in helper constructors.
ADR-0090's `effort.charge` carries the same work-item identity and phase/category snapshot; the writer
rejects a mismatch. ADR-0093's role request must reference that same immutable category. No new
store, writer, orchestrator, router, budget ledger, CLI command, gate condition or
principal-authority path is introduced. [asserted]

## Evidence

- `[measured]` The principal's recorded words require the taxonomy, three phases and threshold rather
  than a ratio, while the same context records the infinite-deliberation danger and
  `bar_not_beaten` give-up outcome.
- `[measured]` His later recorded correction makes each category executable as a native agent and
  separates worker method from subject expertise; ADR-0093 consumes this taxonomy and owns that
  composition without changing these work meanings.
- `[measured]` ADR-0090 owns the total effort envelope and record names; this ADR explicitly
  supersedes its overlapping category and transition meanings rather than leaving two validators.
- `[measured]` ADR-0081 admits only execution, browser observation, fetched primary sources and a
  novel corpus/public API as structural acquisition channels; family-only agreement gets zero
  credit, and the proposed gate is not implemented.
- `[measured]` Current work-item and event schemas have no category, semantic phase or handover
  transition, so every operational clause here remains future work.
- `[measured]` EXP-16's nearest local organisation comparison favoured the single-agent arm in 9 of
  12 substituted blind judgements; the Owner meeting won 2 of 12 while using 4.8 times the tokens
  and 3.7 times the wall time. It is not a threshold experiment, but it makes overhead adverse.
- `[cited]` Wang et al. (2024), *Executable Code Actions Elicit Better LLM Agents*, PMLR 235;
  Yang et al. (2024), *SWE-agent*, doi:10.52202/079017-1601; and Huang et al., *Large Language Models
  Cannot Self-Correct Reasoning Yet*, show that external execution/interface feedback can add facts
  intrinsic reflection lacks in some settings; they do not establish universal superiority or
  verifier reliability.
- `[cited]` OpenHands (arXiv:2407.16741) and MetaGPT (arXiv:2308.00352) already execute code and
  exchange artefacts. Execution by itself is therefore an incumbent capability, not a unique
  Consilient differentiator; the narrower governed-threshold delta remains a hypothesis.
- `[asserted]` A closed taxonomy, cited bar, external threshold, durable handover and explicit miss
  will improve accepted outcomes more often than their overhead harms them. EXP-135 is the killing
  check for threshold stopping only; ADR-0093/EXP-136 separately tests category-agent profiles.

## Evidence against

The strongest objection is that the threshold is unmeasurable in practice. "Markedly better than the
best existing answer" may depend on integration, migration, browser behaviour, deployment and user
response that do not exist until the candidate is built. A Phase 2 benchmark then measures a proxy,
not the artefact that matters. Honest assessment cannot say the threshold passed, so the protocol
runs every planned step to its ceiling and becomes a fixed budget wearing a threshold's clothes.
The labels, anchor ceremony and handover digests add cost without changing the stop. [asserted]

Contemporary agent systems already run tools, and strong extended reasoning is genuinely effective
when the relevant facts and objective are already in context. Retrieval and execution can introduce
latency, instrument failure, environment drift, proxy gaming and lossy handoffs; more world contact
is not automatically more truth. [cited] [asserted]

ADR-0081's two-channel rule is itself unmeasured. Structural difference is not statistical
independence: a test and browser can share a mistaken requirement, while one strong compiler error or
signed primary authority can dominate two weak anchors. Requiring a pair can turn a correct answer
into a refusal. [measured: ADR-0081 status and evidence against] [asserted]

The objection is conceded wherever the bar package records `threshold_testability: unavailable` or
the valid measure requires the final artefact. Such work can never record `bar_beaten`; it reaches
the bounded `bar_not_beaten` path with `gap: unavailable`. That status says superiority was not
demonstrated, not that an executed comparison measured a loss. On that scope the design is a budget
plus honest provenance, not a demonstrated intelligence advantage. [asserted]

The decision remains provisional because that scope may be most real work. EXP-135 separately
reports prospectively testable and build-dependent tasks. If treatment runs mostly hit the ceiling,
or threshold stopping fails to improve joint accepted outcomes over the fixed-budget control, a
successor ADR removes threshold stopping as a quality claim and retains only the taxonomy and honest
handover record. [asserted]

## Consequences

**Positive** — phase use becomes measurable; no candidate proposer can self-certify superiority;
each transition has a durable artefact; and an honest threshold miss can still realise the best safe
candidate without laundering it into a win. ADR-0093 can consume the taxonomy without redefining
its phases. [asserted]

**Negative** — full better-than-best work gains schema, comparison and handover overhead; some tasks
will predictably run to the ceiling; and an externally grounded threshold can still optimise the
wrong proxy. [asserted]

**Neutral but load-bearing** — ADR-0090 owns modes, profiles, effort charges, `exceed_cap` and
`realisation_reserve`; ADR-0081 owns anchor admission; ADR-0077 owns candidate exposure and fusion;
ADR-0093 owns native category-agent composition; principal authority, Gate A, Gate B,
`routing_orchestration_enabled` and the six-command CLI do not change. [measured] [asserted]

## Enforcement

This specification-only commit adds no product behaviour. Future implementation must extend the
existing event/work-item/dispatch/coordination/recall/instruction/budget/routing boundaries and ship
the invariant checks with the fields. [measured] [asserted]

- Check: reject a new durable full work item with missing, unknown, mutable or phase-incompatible
  category data at the universal event boundary. [asserted]
- Check: prove every native ADR-0093 worker profile references exactly one immutable category from
  this enum and cannot create a second taxonomy. [asserted]
- Check: reject phase transition without the required content-addressed handover and refuse
  `bar_located` without retrievable citations and a frozen comparison contract. [asserted]
- Check: reject `bar_beaten` without the material delta, matched executed comparison, must-pass
  results and ADR-0081-qualified pair; family/role/confidence/shared-root variants fail. [asserted]
- Check: prove give-up records `bar_not_beaten` with a measured gap or `unavailable`, cannot enlarge
  ADR-0090's total and cannot start implementation after hard-total exhaustion. [asserted]
- Check: prove delivery preserves the miss and no threshold result can author a principal decision,
  change a gate or raise candidate exposure. [asserted]
- Check: prove all writes use `events.py` and no second task store, ledger, router, orchestrator or
  CLI path exists. [asserted]
- Fails CI: no — no implementation ships here. These are same-commit requirements on future
  implementation. [measured] [asserted]
- Added in the same commit as implementation: required; no implementation is added here. [asserted]

## What would overturn this

EXP-135 removes threshold stopping as a claimed quality advantage if the threshold arm fails its
pre-declared accepted-outcome margin, incurs more critical faults, or reaches its ceiling on at least
three quarters of assigned tasks. An efficiency-only result does not establish better outcomes.
[asserted]

Even if EXP-135 wins, it validates only the frozen task bank, composition, bar procedures and
threshold contracts. A successor ADR must state that scope; no result relaxes ADR-0081, changes a
gate, configures an effort ratio or grants publication/spend authority. [asserted]

If implementation cannot enforce category/phase immutability and handover admission through the
single writer, the taxonomy remains documentation and must not be used for measurement. [asserted]

## Publication candidate?

**No.** The threshold and two-anchor admission are provisional, execution is not unique, and the
central outcome comparison has not run. A publication candidate would require EXP-135 to beat the
fixed-budget control with complete adverse, missingness, cost and task-stratum reporting. [asserted]

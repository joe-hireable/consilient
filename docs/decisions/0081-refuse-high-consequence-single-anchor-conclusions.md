# 0081. Refuse high-consequence single-anchor conclusions and acquire another anchor

- **Status:** PROVISIONAL — EXP-109 can remove the hard consilience gate
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (product direction: “We need to beat all of it without requiring me”,
  quoted in the dispatch brief); Codex dispatch `20260822T135325-cecc1df0a3` (provisional
  mechanism)
- **Inquiry tier reached:** T1 ground; T3 pre-registered as EXP-109, not run
- **Executable model:** none — the admission predicate is exact; EXP-109 measures the unknown
  outcome, refusal and cost effects

## Context

Section 7 of `../superpowers/specs/2026-08-22-decision-protocol.md` correctly separates evidence
tags from truth-relevant anchors, stores immutable references, makes repeated classes and shared
anchors visible, and returns `unmeasured` rather than infer independence. It deliberately treats a
repeated class as a flag rather than a rejection. Nothing then stops a high-consequence conclusion
which rests on one anchor from reaching ADR-0079's specified action boundary. [measured]

ADR-0077 owns verification class, calibration, correlation and fusion; ADR-0075 owns recovery and
the six protected classes; ADR-0078 owns typed effect reach; ADR-0079 owns the pre-action decision
chain; and ADR-0067 owns one accountable Owner. A new fusion table, consequence score, coordinator,
writer or approval path would duplicate an existing authority. [measured] [asserted]

The existing action boundary is a specification, not running code. Current `run_harness()` reaches
`run_process()` without a decision lookup, and current family fan-out judges normalised stdout
equality rather than independent facts. The capability inventory also lacks a validated acquisition-
channel/anchor contract, and recall-packed briefs lack the sealed assembled-context digest this rule
needs. This ADR authorises documentation and future same-commit enforcement only. [measured]

No verified source in the repository establishes that two structurally different acquisition
channels are sufficient or universally necessary. Ao, Gao and Simchi-Levi establish only that new
exogenous signals can move the information boundary; Kim et al. establish task-dependent gains and
losses from collaboration. The fixed two-anchor threshold is this ADR's `[asserted]` hypothesis,
not their result. [cited] [asserted]

## Decision

Consilient will refuse a conclusion at ADR-0079's single action-and-decision admission when its
mechanically derived `record_level` is `full`, or ADR-0075 returns `protected_covered` or
`protected_uncovered`, unless the conclusion's immutable `evidence_refs` resolve to a convergent
pair of structurally distinct observation anchors. Every other valid `minimal` decision proceeds on
its available anchor and records that it did. [asserted]

The only countable acquisition channels are: [asserted]

1. a frozen artefact execution recorded by `verification.outcome` or a linked attempt receipt;
2. an executed real-browser observation with retained runtime evidence;
3. a fetched primary source with canonical locator and content digest; and
4. a non-derived corpus or public-API response proven absent from the deciding context and carrying
   provenance, licence, selection rule and content digest.

A qualifying pair uses different channels, different observation-anchor identities, known disjoint
derivation roots, terminal completed outcomes and the same frozen conclusion/acceptance contract.
The two sealed outcomes must support the same alternative. The common truth target may be the same;
shared source, fixture, generated expectation, peer output or derivation root may not. Missing data
is `unmeasured` and cannot count. [asserted]

Model/provider family, role, persona, prompt, confidence, vote, evidence-tag inequality, repeated
context, unexecuted opinion, source snippet and unvalidated algebra/simulation receive zero
structural credit. Family metadata stays available to ADR-0077 for correlation measurement, but
its error discount is unmeasured and no family-only fan-out can open the gate. [asserted]

Human preference and authority remain first-party facts, not acquired verification. The system does
not ask the principal to manufacture a second objective anchor. Convergence is necessary but never
sufficient for protected action: exact first-party authority and every ADR-0075/0078/0079, budget,
beta, law and gate check still apply. [asserted]

If the pair is absent, the Owner first opens one bounded acquisition work item for the cheapest
available countable channel whose possible outcome could change the action. The implementation
reuses `capabilities.py` for fail-closed selection, `work_items.py` and `coordination.py` for work
and claims, `instructions.py` and bounded `recall.py` for sealed context, `dispatch.py` for execution,
`budget.py` and `routing.py` for their existing ceilings, and `events.py` as the sole append-only
writer. It records execution/browser observations as `verification.outcome` and source/corpus
observations as `knowledge.retrieved`, appends a superseding decision with the new immutable refs
rather than rewriting the insufficient decision, then re-enters the same admission. A second
orchestrator or CLI command is forbidden. [asserted]

The child is independently limited to observation or contained execution and receives no handle to
the parent effect. Anything broader is a capability gap, preventing recursive acquisition gates.
[asserted]

When distinct anchors disagree, both sealed readings, scopes, estimands, limits and consequence
branches remain in the trajectory. The Owner checks scope, then acquires one discriminating world
observation or runs a reversible probe when its outcome can change the action and budget permits.
Otherwise it records `disagreed_unresolved` and refuses the high-consequence action. A vote, average,
minority deletion or third model reading the same anchors is not resolution. [asserted]

The complete protocol and channel contracts are specified in
`../superpowers/specs/2026-08-22-consilience-gate.md`. [measured]

## Evidence

- `[measured]` Section 7 already specifies exact immutable references, shared-anchor reporting and
  an `unmeasured` state, but says a repeated class is not an automatic rejection.
- `[measured]` ADR-0079 specifies one pre-action admission and a work-item readiness binding, but
  the current source implements neither the decision lookup nor the universal effect boundary.
- `[measured]` `capabilities.py`, `dispatch.py`, `coordination.py`, `work_items.py`, `recall.py`,
  `routing.py`, `budget.py`, `instructions.py` and `events.py` already supply the substrates this
  mechanism must extend.
- `[measured]` Current generic family fan-out supplies labels and normalised answer equality, not a
  verified different anchor.
- `[cited]` Ao, Gao and Simchi-Levi (2026), arXiv:2603.26993, show that a delegated network with the
  same exogenous signals cannot improve the ideal central decision; external verification can move
  the information boundary. `[FULL]` in the bibliography.
- `[cited]` Kim et al. (2026), doi:10.1038/s42256-026-01268-y, find task-dependent collaboration
  gains and losses across matched configurations. `[FULL]` in the bibliography.
- `[asserted]` A high-consequence refusal plus bounded acquisition will improve independently
  checked decisions more than section 7's flag-only rule. EXP-109 is the killing test.

## Evidence against

- `[asserted]` Structural channel difference is not statistical independence. Execution, browser,
  source and corpus channels can share a mistaken requirement, upstream source or selection bias;
  a valid enum can turn unmeasured dependence into false assurance.
- `[asserted]` Many real decisions legitimately rest on one strong anchor. A deterministic
  counterexample or authoritative primary record can dominate multiple weaker observations, so the
  second-anchor rule can reduce competence and make availability part of correctness.
- `[measured]` EXP-16's single-agent arm reached the same substantive decision as its structured
  multi-agent arm in four of six cases with lower token and wall-time cost; blinded decision-quality
  grading remains outstanding. Added organisation can recreate that overhead under a more
  respectable name.
- `[cited]` Kim et al.'s matched comparison contains substantial multi-agent degradation, so no
  universal value attaches to another reader or acquisition path.
- `[cited]` Wurzel Gonçalves et al. (2022), doi:10.1007/s10664-022-10123-8, found no general
  effectiveness gain from explicit review strategies and lower effectiveness for one controlled
  change after controls; its novice-heavy human setting limits transfer but directly challenges
  compulsory structure.
- `[asserted]` A refusal gate can lower false acceptance by refusing everything. It can be gamed
  with schema-valid derivation metadata, delay a correct time-sensitive action and turn an absent
  browser/source/corpus into denial of service.

The strongest case is that this gate is **superstition with a schema**: it treats an unmeasured
independence claim as a safety property, then rewards itself for refusing. That objection is not
answered by confidence. It is conceded unless EXP-109 shows fewer bad actuations without materially
reducing correct completion, merely increasing refusals or exceeding the frozen cost ceiling.
Tiering, autonomous acquisition and visible `unmeasured` states limit the wager; they do not prove
it. [asserted]

## Consequences

**Positive** — high-consequence echo becomes structurally refusable; routine reversible work remains
single-anchor; missing anchors trigger bounded autonomous observation rather than a human approval
request; disagreement remains information. [asserted]

**Negative** — the action path gains an availability dependency on event resolution and a second
acquisition; correct single-source decisions may be delayed or refused; structural metadata can be
wrong; acquisition adds compute, latency and storage. [asserted]

**Neutral but load-bearing** — ADR-0077 still owns fusion, ADR-0075 recovery/protection, ADR-0078
effect reach, ADR-0079 action admission, ADR-0067 the Owner, `events.py` the record and `dispatch.py`
the outer runner. The routing flag remains false and the CLI remains six commands. [asserted]

## Enforcement

This documentation commit implements no gate and changes no product code or gate condition.
[measured]

- **Check:** the implementation commit adds
  `tests/test_decision_protocol.py::test_high_consequence_admission_refuses_single_structural_anchor`.
  It proves one anchor, two labels/families over one anchor, shared roots and missing dependence
  refuse before fake reach, while a minimal recovery-proved decision records one anchor and proceeds.
  [asserted]
- **Bypass check:** ADR-0079's
  `tests/test_v0_invariants.py::test_no_effect_path_bypasses_action_and_decision_admission` remains
  the universal executable-tree and sandbox ratchet; no second action boundary is allowed.
  [asserted]
- **Acquisition/disagreement checks:** future fixtures prove bounded dispatch through existing work
  items, sealed peer context, terminal adverse outcomes, re-entry through the same admission, no
  human tie-break and no actuation on unresolved disagreement. [asserted]
- **Fails CI:** no — no implementation ships in this commit. [measured]
- **Added in the same commit as the implementation:** required. [asserted]

## What would overturn this

EXP-109 removes the hard consilience gate if the treatment merely raises refusals without a material
reduction in bad actuation, reduces correct completion beyond its frozen non-inferiority margin,
exceeds its cost ceiling, or permits one high-consequence action without a qualifying pair. Section
7's visibility projection, ADR-0077's correlation data and the low-consequence one-anchor path
remain. [asserted]

A cheaper counterexample blocks activation immediately: a family/label change opens the gate; two
events sharing a derivation root count twice; missing metadata is inferred as independence; an
unresolved disagreement actuates; or acquisition bypasses the one action boundary. [asserted]

Passing EXP-109 would establish only a benefit on its frozen task mixture. It would not establish
statistical independence, universal necessity, legal correctness, principal authority, a gate pass
or permission to expose more candidates. [asserted]

## Publication candidate?

**No.** The threshold is asserted, the action boundary is unimplemented and the experiment has not
run. [measured] [asserted]

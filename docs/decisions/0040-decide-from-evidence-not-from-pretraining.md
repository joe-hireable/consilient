# 0040. The harness decides from evidence, not from pretraining — and runs the experiment when it has none

- **Status:** DEPRECATED 20 August 2026. [asserted] The tested trajectory and commit rules
  provide no mechanically complete decision-and-provenance discriminator. [algebra]
- **Date:** 2026-08-20
- **Deciders:** Joe Brown (the principle), Claude Opus 5 (the mechanism and the objections)
- **Inquiry tier reached:** T1 ground — a principle plus a day of measured instances, none of
  them controlled.
- **Executable model:** none yet. The decision variable is *when* to spend an experiment, and
  its parameter — the cost of being wrong — is exactly what β measures and β is not measured.

## Update: 2026-08-20 — proposed EXP-46 cannot be instrumented; this ADR is deprecated

The feasibility audit for the proposed experiment tested all three candidate definitions before
changing the schema. [measured]

- **A new event kind:** `validate()` accepts any non-empty kind and there is no event-kind
  registry, so a new kind would leave the legacy log unchanged. [measured] A decision omitted
  from that kind is invisible, so the resulting ratio measures recording diligence rather than
  decision practice. [algebra]
- **A `decision` data field:** the 96 retained lines have 96 distinct kinds. Only three carry
  `data.decision`; five kinds contain `decid`, one other event carries `final_decision`, and one
  carries `judgement`. No line carries `evidence_ref`, `evidence_reference` or
  `decided_from_priors`. [measured] A validator limited to those explicit fields would add three
  quarantines; treating heterogeneous fields such as `artefacts` or `local_measurements` as
  evidence references instead requires an unrecorded semantic mapping. [algebra] There is no
  uniform provenance field on which the check can operate without either interpretation.
  [measured]
- **Commit messages:** at the pre-result baseline `d579beedd0d88aeebee75666e0a4db89f2c3ac5d`,
  the branch had 150 uniquely reachable commits, 127 author-dated 20 August. Under the fixed
  case-sensitive uppercase-token rule, 40 carried both `REVERSAL` and `FALSIFIER`; a stricter
  exact-heading rule (`^REVERSAL:` and `^FALSIFIER:`) found both in 36. [measured] No message
  recorded a `decided_from_priors: true` or
  `decided_from_priors: false` value; one merely mentions the absent field. Of the 40
  uppercase-token candidates, 39 carried neither `evidence-derived` nor `prior-derived`, while
  the remaining message carried both as the description of the proposed EXP-46. [measured]
  The corpus therefore has no mechanical provenance discriminator from which to derive the
  required ratio. [algebra]

An exactly-one check could require either a non-empty evidence reference or literal
`decided_from_priors: true`, so setting the latter to `false` would fail. [algebra] It would
still be satisfied by omitting the decision event or field altogether, which schema validation
cannot observe. [algebra] No such guard was built, no ratio was added to `doctor`, and no
EXP-46 entry was added to the register; the register did not contain one before this audit.
[measured] The proposed experiment's mechanical-identification precondition therefore failed.
[algebra]

**Decision.** ADR-0040 is deprecated rather than promoted or left aspirational. [asserted]
The alternative retained for future work is an explicit event kind, but only after an
independent capture boundary can measure omitted decisions; without that boundary it is a
denominator over self-reports. [asserted]

**Evidence against deprecation.** An explicit kind plus the exactly-one union would make the
provenance of decisions that were recorded mechanically reportable. [algebra] That is useful
prospective telemetry, but it does not satisfy this ADR's claim about consequential decisions
because the current boundary cannot distinguish a complete record from an empty one. [asserted]

**Why omission kills this check and not V0-18, since both are bypassable by not writing an
event.** The distinction is what the invariant is *about*. V0-18 is conditional: *if* an event
claims a human decision, the human must have authored it. Omitting the event omits the claim
too, so nothing false is asserted and the invariant is not evaded — it simply has no subject.
This ADR's check is a *census*: it needs every consequential decision to appear in order to
report a ratio over them. Omission does not remove a claim, it silently biases a denominator,
and a rate computed over the decisions someone chose to record measures diligence while looking
like practice. **A conditional invariant survives an incomplete log; a rate does not.** [asserted]

That distinction is worth keeping beyond this ADR: any future metric derived from the trajectory
is a census and inherits the same defect, while any future invariant that fires only on a
present claim does not.

**Reversal:** `git revert (git log -1 --format=%H --fixed-strings --grep="Deprecate ADR-0040")`
restores the provisional status and removes this result.

**Falsifier:** reopen this decision if a deterministic rule fixed before corpus inspection
identifies consequential decisions independently of their self-report, distinguishes their
provenance, and has its omission and classification errors measured against independent ground
truth. [asserted]

The original provisional text below is retained unchanged as history. Its statements that the
ADR is provisional and that EXP-46 was registered are superseded by the measured update above.
[measured]

## Context

Joe, 20 August 2026:

> *"We need to build a harness designed specifically for how I've been working with AI. Not
> relying on pretraining for decisions but instead on evidence and research and real experiments
> and collaboration with other projects and inspiration and adoption and upstream
> contributions."*

The evidence discipline in this repository — evidence tags, pre-registered stopping rules, an
experiment register, superseded rather than edited decisions — has so far been a **development
practice**. Something we do while building the harness.

**He is proposing it as a property of the harness itself.** That is a different and much larger
claim, and it is the first thing said in this project that no other harness does.

## Decision

**When the harness faces a consequential decision it cannot answer from recorded evidence, it
registers an experiment, runs it, and decides on the result — rather than asking a model.**

Every other harness answers such a question by consulting a model's priors. That is fast,
usually adequate, and **unfalsifiable**: the answer carries no evidence and cannot be checked
later. This harness's distinguishing behaviour is that it treats its own architectural questions
the way it treats a repository's verification quality — as something to measure.

### The gate, because otherwise this is paralysis

An experiment is spent only when **all four** hold. Otherwise the harness decides from priors,
records that it did so, and records the reversal path.

1. **Consequential** — the decision constrains later work, per ADR-0038's test for an ADR.
2. **Expensive to reverse** — if one `git revert` undoes it, decide and move (ADR-0033).
3. **An affordable experiment exists.** Measured today: mining a public repository end to end
   is **32.9 s**; a 30-repository panel is **16.5 minutes**; a retro-verification commit pair is
   **~1.5 s**. [measured] The cost objection is weaker than it sounds, and where it is not, this
   condition simply fails.
4. **The result would change the action.** Howard's expected value of clairvoyance, already
   adopted by ADR-0033 for asks: *when no possible answer changes the chosen action, asking is
   strictly irrational, not merely expensive.* [cited] It generalises from asks to experiments
   unchanged.

### What it forbids

- **Deciding an architectural question by model consensus.** Several agents agreeing is echo
  (ADR-0010), and today it was measured producing a *false* agreement: two families reported β
  within 0.0085 of each other while differing on 16 of 75 labels, an apparent convergence that
  was arithmetic cancellation and 14× narrower than their inputs warranted. [measured]
- **Citing a model's fluency as evidence.** A confident explanation is the same induction
  restated, which working principle 5 already bans for confidence scores.
- **Building before measuring where measurement is cheap.** Ordering follows cost.

## Evidence

All from 20 August 2026, all `[measured]`, all cases where a model prior was wrong and running
it was right:

- **The retro-verifier's real limit was not the one predicted.** The anticipated flaw was
  survivorship bias. The pilot found something larger and unanticipated: it cannot evaluate a
  commit that adds a new component, and **72.8–75.9% of merges do exactly that.**
- **An apparent cross-family agreement was arithmetic.** See above. Reasoning about it would
  have endorsed it; recomputing under every cross combination refuted it.
- **A leak was found only by a search the author could not have run.** The orchestrator searched
  for repository-prefixed paths; the leak was the same paths written bare. A different model
  family searching differently found two publication blockers in the initial commit.
- **Two auditors reported EXP-01's raw data absent.** It was on disk, gitignored. Both had
  reasoned from the tracked tree.
- **EXP-44's registered era boundaries were contradicted by its own corpus.** The design expected
  10–40% AI authorship in 2023–2024; measurement found **0.0%**, identical to the pre-AI
  baseline.

In each case the model-derived answer was plausible, confidently held, and wrong.

## Evidence against

- **The sample is one operator, one project, one day, and it is not controlled.** There is no
  comparison arm in which decisions were made from priors and the outcomes compared. The
  instances above are selected by salience — the cases where running it *changed* something are
  exactly the ones anyone would remember. **Publication bias, applied to one's own day.**
  [asserted]
- **Experiments have their own error rates, and this project measured one today.** Without a
  parent-commit control, the retro-verifier would have reported **β = 1.0** — maximally alarming
  and entirely wrong. [measured] An experiment is a test; tests have error rates; the harness's
  own thesis applies to its own instrument, and running more experiments is not automatically
  running better ones.
- **The register itself has been wrong.** EXP-44's era partition was imposed and refuted, and
  Gate B contained one condition that could never fail and one that could never pass. **A
  pre-registered protocol is only as good as its author's priors, which is the very thing this
  ADR distrusts.** [measured]
- **Cost is understated.** Today's measured per-experiment costs exclude the orchestration
  around them: roughly fifteen agent dispatches, several failed launches, two near-misses, and a
  full session of a human's attention. Quoting 32.9 s per repository as the cost of an
  evidence-first decision is the same error as quoting model latency and ignoring the harness.
  [asserted]
- **It may simply be slower, and slower may lose.** A competitor deciding from priors ships
  while this one measures. Nothing here establishes that measured decisions are *better* often
  enough to pay for the delay — only that they are sometimes different. [asserted]

## Consequences

**Positive.** Decisions carry evidence, so they can be checked, superseded and learned from.
The register becomes the harness's memory of why it is shaped as it is.

**Negative.** Slower, and visibly so. Some decisions will be measured that did not need to be,
and the gate's four conditions are judgement calls that will be got wrong in both directions.

**Neutral but load-bearing.** This makes the experiment register a **runtime** artefact rather
than a development one. It has to be readable and writable by the harness, not only by a person,
and that is a schema commitment nobody has designed yet.

## Enforcement

Every rule ships with its check (I1). None of these exist yet, and the ADR is PROVISIONAL
partly because of it:

- **Check:** a decision event records either its evidence reference or an explicit
  `decided_from_priors: true` with a reversal path. A decision with neither fails schema
  validation. *Without this, "decide from evidence" is a slogan and nothing distinguishes a
  measured decision from a confident one.*
- **Check:** the four gate conditions are recorded per experiment, so that a spent experiment
  can be audited against condition 4 — did the result actually change the action?
- **Check:** the ratio of decisions-from-evidence to decisions-from-priors is derivable from the
  trajectory alone, so this ADR can be evaluated rather than believed.

## What would overturn this — EXP-46

Registered before any of this is built. **Measure the decisions.** Over a fixed window, classify
every consequential decision as prior-derived or evidence-derived, and record whether it was
later reversed.

- If evidence-derived decisions are reversed at the same rate as prior-derived ones, the
  discipline is costing time and buying nothing, and this ADR should be cut rather than kept for
  tidiness.
- If experiments are spent on decisions that condition 4 would have excluded — where no result
  could have changed the action — the gate is not working and needs teeth rather than prose.
- If the ratio never moves off prior-derived, the harness is not doing this and the ADR is
  aspirational documentation, which is worse than none.

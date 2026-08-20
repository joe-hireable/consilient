# 0011. Replace the "meeting" primitive with an evidence merge

- **Status:** **SUPERSEDED by 0020** (19 Aug 2026)
- **Superseded because:** this ADR removed the meeting primitive on the grounds that
  participants sharing a ticket context hold no distinct class of facts. Joe's RACI framing
  resolved the underlying problem more cleanly: the theorem forbids *deciding by conferring*,
  not *one accountable owner deciding after gathering evidence from holders of distinct
  classes*. `0020` restores meetings with single-Owner authority, which is structural rather
  than the declaration gate proposed here. The declared-vs-measured evidence-class weakness
  noted below survives into `0020` and remains unfixed.
- **Date:** 2026-08-19
- **Deciders:** Joe Brown (original requirement), Claude (revision)
- **Inquiry tier reached:** T1 ground
- **Executable model:** none.

## Context

Q8. Joe's requirement: agent communication should run through a project management system,
with dedicated bounded **meetings** possible but no open-ended conversation. A meeting
primitive was sketched: named caller, stated question, exit artifact, token budget, turn
cap, quorum rule, durable transcript.

Applying `0010` to that sketch breaks it. **A meeting between agents sharing the same
ticket context has no different class of facts.** It is precisely the relay structure
measured degrading gpt-4.1-mini from 90.7% to 22.5%. The primitive did not survive its own
rule.

## Decision

Rename and re-gate it. There is no "meeting". There is an **evidence merge**:

1. **Convocation declares evidence.** Each participant states the `evidence_class` it
   brings — a repository state, a test run, a source it read, an execution trace.
2. **Convocation is rejected if two participants declare the same class.** Mechanically
   checkable, at configuration time.
3. **If convocation fails, the orchestrator does the work itself.** Which is what the
   theorem says is optimal anyway — this is not a fallback, it is the correct answer.
4. **Named exit artifact.** The merge terminates when the artifact exists, not when
   participants feel finished.
5. **Hard token budget and turn cap.** Exceeded means the merge fails and escalates to the
   human, never runs on.
6. **No recursion.** A merge may not convene a merge. Depth is capped at one.
7. **Durable transcript**, attached to the ticket, replayable from the trajectory log.

## Evidence

- `[cited]` `0010`'s full evidence base applies. Structured relay lost 2.8 points per stage
  even in the *better* interface condition.
- `[cited]` The MIT result recasts optimising a multi-agent DAG under a finite
  communication budget as "choosing how to compress and pass along the shared signal" —
  i.e. a lossy channel design problem. A merge of *different* evidence is not that problem.
- `[measured]` Joe's prior codebase assessment is an evidence merge that worked, and it
  passed rule 2 without anyone stating the rule: discovery agents read different sources,
  verifiers re-derived from primary evidence.
- `[cited]` Budget primitives are not optional: 63 confirmed production budget-overrun
  incidents across 21 **subprojects** and 18 ecosystems, 2023–2026 (arXiv:2606.04056).
  *Corrected 2026-08-20: this read "21 orchestration frameworks". The source counts
  subprojects, not frameworks, and it is a convenience failure-confirming sample rather
  than a prevalence estimate — as the bibliography entry already recorded.*

## Evidence against

- Rule 2 is crude. Two agents could declare different `evidence_class` labels while holding
  substantially overlapping evidence, and the check would pass. It is a *declaration* gate,
  not a measurement. A stronger version would measure evidence overlap directly — currently
  out of scope, and a real weakness.
- Banning recursion may be over-cautious. Nested merges over genuinely disjoint evidence are
  not obviously harmful; the ban is a simplicity choice, not a derived result.
- Losing the word "meeting" loses an intuitive handle for users. "Evidence merge" is
  accurate and duller.

## Consequences

**Positive.** The primitive now passes its own project's rule. The failure mode — agents
conferring about a shared brief — is blocked at configuration rather than discovered in
production.

**Negative.** Fewer situations qualify than the original sketch implied. In many workflows
the answer will be "no merge, orchestrator handles it", which will feel like the feature is
missing.

**Neutral but load-bearing.** Makes `evidence_class` a first-class concept in the ticket
schema, not just orchestrator config.

## Enforcement

- Check: convocation validator rejects duplicate `evidence_class`. Unit test with a
  same-class pair asserting rejection. Same commit as the feature (I1).
- Check: recursion depth assert; a merge attempting to convene a merge fails loudly.
- Check: budget and turn caps enforced in the loop, not advisory. Test that an
  over-budget merge terminates and escalates rather than continuing.

## What would overturn this

- Evidence-overlap measurement becomes cheap enough to replace the declaration gate, at
  which point rule 2 should be upgraded from declared to measured.
- Nested merges over disjoint evidence show value in practice, retiring rule 6.

## Publication candidate?

No.

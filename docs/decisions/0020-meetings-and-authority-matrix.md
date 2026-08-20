# 0020. Meetings, and the Owner/Evidence authority matrix

- **Status:** CUT (meeting mechanism) / RETAINED (matrix as schema) — see the 2026-08-20 update — **supersedes `0011`** (evidence merge)
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground
- **Executable model:** none yet. Strong T2 candidate once meeting logs exist — the
  termination and quorum parameters are exactly the kind of thing a model settles.

## Update: 2026-08-19 — evidence overlap is an implementation gate

An origin-alignment audit confirmed that the declared-class weakness below is still open.
[measured] A class label is provenance metadata, not proof that two participants actually
hold different facts. [asserted] No product meeting primitive may therefore rely on the
declaration-only gate: it remains research-only until an evidence manifest and measured
source-overlap check have passed the EXP-14 protocol. [asserted]

## Update: 2026-08-20 — EXP-16 stopping rule 1 fired. The convened meeting is CUT.

**Status of the meeting mechanism: CUT.** **Status of the authority matrix as a schema:
retained.**

The rule, pre-registered before EXP-16 ran: *"If Arm B does not beat Arm A at matched budget →
meetings are ceremony; ADR-0020 and the authority matrix are cut."*

Eighteen decisions were graded blind — labels stripped, randomised independently per decision —
by **two different model families**, neither of which wrote any option and neither of which saw
the other. Twelve judgements, mapped through the sealed key only after both were recorded:

| | best | worst |
|---|---|---|
| **Arm A — single agent** | **9** | **1** |
| Arm B — this ADR's Owner meeting | 2 | 3 |
| Arm C — free-form group | 1 | **8** |

[measured] At **4.8× the tokens and 3.7× the wall-clock** already measured for Arm B. The rule
fires.

**The substitution, stated plainly.** The registration names *Joe's* judgement as ground truth
and it has not been obtained; an agent grading the multi-agent structure is the echo failure this
project is named for, so grading it here was not available. Cross-family blind grading answers a
**different question** — whether independent readers of another lineage prefer the outputs. **Joe's
grading supersedes this whenever he wants it**, and the pack is intact.

**What is cut:** convening a meeting — Owner plus Evidence agents assembling — to produce a
decision. Several times the cost, worse output on this evidence.

**What is retained:** the **Owner / Evidence / Informed / Escalation matrix as a record format**
for who decided what, on which evidence. Writing down accountability was never on trial; what
failed is convening a meeting to manufacture it.

**The result that is not about structure at all:** Arm C, free-form group discussion, was worst
in **eight of twelve** — and it is the arm that recorded no dissent on any of the six decisions.
That is the strongest single number in the set.

**The strongest argument against this cut, unanswered:** the graders scored decision quality *at
the moment of decision*. Arm B's distinctive product was preserved dissent, whose value is that it
survives to be useful later. No snapshot grading can see that, and this result does not address
it. See `../10-research/experiments/exp16/grading-result-2026-08-20.md`.

## Context

`0011` replaced Joe's "meeting" with an evidence merge, gated by a declared-evidence-class
check. Joe's revision (19 Aug 2026): agents must genuinely be able to convene — pairwise for
a targeted, non-looping conversation, and in larger groups where several agents hold
authority over different areas. Plus a RACI-like structure, and the user must be
includable as a participant.

`0011`'s gate was crude. It asked "do two participants declare the same evidence class?" —
a declaration check, not a structural one, and I flagged it as a real weakness at the time.

**Joe's RACI instinct resolves it properly, and the reason is worth stating precisely.**

## Why authority assignment is theorem-compliant

Ao, Gao & Simchi-Levi (arXiv:2603.26993) show a delegated network cannot beat a centralised
Bayes decision maker with the same information. The failure mode it punishes is **many agents
jointly deciding one thing by talking about shared evidence.**

RACI does not have that shape. Under RACI, **exactly one party is Accountable for a given
decision** — and that party *is* the centralised decision maker for that decision. Others
supply inputs. So:

> The theorem forbids *deciding by conferring*. It does not forbid *one agent deciding after
> gathering evidence from agents who hold different evidence*.

Authority partitions the decision space; it does not delegate a single decision to a
committee. That is the escape, and it is cleaner than `0011`'s declaration gate because it is
structural rather than declared.

## Decision

### 1. The authority matrix — Owner / Contributor / Evidence / Informed / Escalation

RACI adapted, with three deliberate improvements.

| Role | Meaning | Cardinality |
|---|---|---|
| **Owner** | Decides. Accountable. Writes the decision record. | **Exactly one. Enforced, not conventional.** |
| **Contributor** | Does work under the Owner's direction. | 0..n |
| **Evidence** | Must be consulted, **and declares the class of facts it brings**. | 0..n, all distinct |
| **Informed** | Receives the decision record. No input. | 0..n |
| **Escalation** | Named *in advance*; receives the decision if the Owner cannot resolve it. | Exactly one |

**Improvements over RACI:**

1. **"Consulted" becomes "Evidence", and must declare its class.** RACI's worst failure mode
   is Consulted-as-rubber-stamp — parties present for politics, not information. Here, a
   participant with no distinct evidence class **is not a participant**. This carries
   `0011`'s check forward but attaches it to a role rather than to a convocation.
2. **Escalation is named in advance, not discovered when stuck.** RACI has no escalation
   concept, which is why real projects deadlock. Every decision knows where it goes if
   unresolved — usually the user, for preferential questions (`0018` decision 4).
3. **Decision scope is explicit**, so authority cannot leak. An Owner of "retrieval strategy"
   does not thereby own "database choice".

The matrix is attached to **decisions**, not to agents. One agent may own some decisions and
merely hold evidence for others.

### 2. Meetings

A **meeting** is convened by an Owner, about a specific decision they own, to gather evidence
they lack.

- **Called by the Owner.** No self-convening, no ambient meetings.
- **Participants are the Evidence holders for that decision**, and are required to hold
  distinct classes.
- **The Owner decides at the end. Not the meeting.** There is no consensus mechanism, no
  vote, no averaging. This is the theorem-compliance point and it is not negotiable: a
  meeting gathers, an Owner decides.
- **Terminates on** the named artifact existing, budget exhaustion, turn cap, or the Owner
  declaring sufficiency. Whichever comes first.
- **Budget and turn cap are hard**, enforced in the loop. Exhaustion escalates; it never
  runs on. (63 documented budget-overrun incidents — arXiv:2606.04056.)
- **Recursion is bounded at depth 1** and a meeting may not convene its own Owner's decision
  recursively.
- **Pairwise is the common case.** Two agents, one goal, terminating. Larger meetings are
  permitted where several agents genuinely own adjacent areas.

### 3. The user is a participant, not an interrupt

The user is an **evidence class** in their own right — preferential facts, permissions,
credentials, and context the system does not have.

Agents may add the user to a meeting when:
- the question is **preferential** (`0018`) — the answer is the user's to give;
- **permission or credentials** are required (`0019`);
- the question is **epistemic but expensive to test** (`0018` case 3);
- the user is the named **Escalation** for the decision.

Practical constraints:
- **Async by default.** The meeting parks and resumes; the user is never required to be
  present live. A blocked meeting is a ticket state, not a spinning loop.
- The user may be **Owner** of any decision, at which point agents supply evidence and the
  user decides.
- **Joining is cheap, being summoned is not.** A meeting that adds the user must state the
  question, what was already tried, and what it would cost to resolve without them.

### 4. Observability

- **Retrospective observability is mandatory.** Every meeting is fully recorded in the
  append-only trajectory log (`0006`) and is replayable: participants, declared evidence
  classes, transcript, artifact, budget consumed, and the Owner's decision with its
  reasoning.
- **Live observability is optional and one-way.** The user may watch; watching does not make
  them a participant. Joining is an explicit act, because a silent observer who is assumed to
  have consented is the worst of both.

## Evidence

- `[cited]` Ao, Gao & Simchi-Levi, arXiv:2603.26993 — the constraint, and the reason single-
  Owner authority escapes it. `[ABS]` — **priority read** (bibliography).
- `[cited]` Tran & Kiela (arXiv:2604.02460) predict multi-agent becomes competitive precisely
  when a single agent's context utilisation degrades. Distinct-evidence-class participants
  are exactly that regime. `[SNIP]`
- `[cited]` The MIT result measured interface form: structured posterior-style relay lost
  2.8 points per stage, prose relay 8.5. **Meeting exchanges should be structured, not
  prose.** `[2ND] — verify.`
- `[measured]` Joe's own prior codebase assessment is this structure already: discovery agents
  as Evidence holders on separate sources, an orchestrator as Owner, independent verification
  as a distinct class, one fabrication caught in 197 leads.
- `[cited]` Gödel Agent's pre-application verification agent is the same pattern at a
  different scope. `[SNIP]`

## Evidence against

- **The Owner may simply be wrong**, and the structure gives no recourse short of escalation.
  Consensus mechanisms exist partly to catch a bad decider. We are trading that for
  theorem-compliance and accepting the risk.
- **Distinct evidence classes remain declared, not measured.** Two agents may claim different
  classes while holding overlapping evidence. Measuring overlap directly is the proper fix
  and is out of scope. This was `0011`'s weakness and it survives into `0020`.
- Depth-1 recursion is a simplicity choice, not a derived result.
- **Async user participation may not work in practice.** A meeting parked for two days
  holding a worktree is an operational problem nobody in the literature has solved.
- No prior art was checked for RACI-style authority in agent systems specifically. **Search
  before implementing** — this has probably been tried.

## Consequences

**Positive.** Agents genuinely collaborate, with a structure the theorem permits. The user is
a first-class participant rather than an interrupt. Authority is explicit, so "who decided
this?" is always answerable from the log.

**Negative.** More machinery than `0011`. Requires a decision registry with owners, which is
a new persistent object.

**Neutral but load-bearing.** Makes the *decision* — not the ticket — the unit that carries
authority. The ticket store (`0006`) must model decisions as first-class, which is a schema
change and therefore a public-interface change.

## Enforcement

- Check: exactly one Owner and exactly one Escalation per decision. Rejected at write time.
- Check: no two Evidence participants share a declared class. Carried from `0011`.
- Pre-implementation check: each Evidence participant supplies an immutable manifest of the
  source identifiers it actually read; the validator measures pairwise overlap and applies
  the threshold fixed by EXP-14 before the run. [asserted] The manifest validator, threshold
  fixtures and bypass check must ship in the same implementation commit. [asserted]
- Check: **meeting outcome writes are attributed to the Owner only.** A meeting that produces
  a decision from consensus, vote or averaging fails validation — this is the check that
  keeps the theorem-compliance real rather than aspirational. Same commit (I1).
- Check: budget and turn caps enforced in the loop; a test asserts an over-budget meeting
  terminates and escalates.
- Check: every meeting appears in the trajectory log with full replay. A meeting absent from
  the log fails the replay invariant (`0006`), i.e. breaks CI rather than merely being
  unobservable.
- Check: recursion depth assert.

## What would overturn this

- **EXP-14 (new):** run identical decisions through (a) single agent with all evidence,
  (b) Owner + distinct-class Evidence meeting, (c) consensus vote among the same agents, at
  matched token budget. If (b) does not beat (a), meetings are ceremony and should be cut. If
  (c) beats (b), the theorem's applicability here is wrong and this ADR is wrong.
- Prior art shows RACI-for-agents already exists and works differently.

## Publication candidate?

**Possibly.** "Single-owner authority partitioning as a theorem-compliant multi-agent
structure" is a small, clean claim with an obvious experiment (EXP-14) — and the field is
currently oscillating between naive swarms and single agents with little in between. Bundle
with the β work rather than standing alone.

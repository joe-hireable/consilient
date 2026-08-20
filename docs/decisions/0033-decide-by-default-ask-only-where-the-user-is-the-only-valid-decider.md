# 0033. Decide by default; ask only where the user is the only valid decider

- **Status:** PROVISIONAL — rests on human-subject evidence from adjacent populations; EXP-33
  measures it here
- **Date:** 2026-08-20
- **Deciders:** Joe Brown (the principle), Claude Opus 5 (the mechanism)
- **Inquiry tier reached:** T1 ground — a principle plus published measurements, none of them
  on this system
- **Executable model:** none. The thresholds are preferential and are named as such.

## Context

Joe, 20 August 2026: *"We don't want to make users impotent by removing decision making
authority — but we must in many cases be decisive. The user must be free to only make the
irreversible calls that really have no clear answer. Or potentially destructive actions like
making a payment, handling a sensitive credential."*

Both failure modes are real and the repository already leans on one of them. ADR-0021 gives
the harness a pushback protocol, ADR-0020 §3 makes the user a participant, ADR-0018 separates
preferential from epistemic questions, and ADR-0019 puts paid acquisition behind four
conditions. What none of them says is **when not to ask**, and the evidence gathered on
20 August says the cost of asking is larger and less evenly distributed than it looks.

## The evidence that changes the shape of this

- **Asking has a measured cost and it is regressive.** Cognitive forcing cut over-reliance
  from 64% to 48% (p=.003), and the authors report plainly that people over-relied less under
  conditions they *"found more difficult, preferred less, and trusted less"*, with the benefit
  accruing disproportionately to high Need-for-Cognition participants — an
  intervention-generated inequality. [cited]
- **An ask the user cannot cheaply answer is answered badly, and paying them does not help.**
  Over-reliance is rational effort allocation, not a bias: explanations moved it from ~70% to
  ~68%, and raising the monetary bonus moved it from ~58% to ~57%. The only manipulation that
  worked was making verification genuinely cheap, which dropped it to ~28%. [cited]
- **Earned trust reduces scrutiny, so asks decay in value as the harness improves.** Higher
  confidence in the AI associated with less critical engagement at b=−0.69 log-odds
  (p<0.001), the strongest effect in that model. [cited]
- **Removing authority is not the safe alternative.** Autonomy was the strongest Job Resource
  contributor against developer burnout under generative AI, while organisational pressure to
  adopt sat on the demands side (B=0.41 with organisation size; autonomy B=−0.13, both
  p<.001). [cited] Both over-asking and under-asking are costs; there is no neutral setting.
- **Self-report cannot be used to tune this.** Developers reported a 20% speedup after a
  measured 19% slowdown. [cited] "Was that too many prompts?" is not an instrument.

## Decision

### 1. The default is to decide, record, and make reversal cheap

For any decision not in §2, the harness decides, records the decision with its evidence, and
**records how to reverse it**. Kozyrkov's test — *"as long as you can change your mind for
free, no decision has been made yet"* — is already ADR-0021's basis. [cited] Its design
consequence is the part this project had not drawn: **the engineering work goes into lowering
the cost of being wrong, not into transferring the choice.**

**A decision with no recorded reversal path is not an autonomous decision. It is an ask.**

### 2. The user-only classes, and they are exhaustive

The harness asks when, and only when, the decision falls in one of these. Adding a class
requires an ADR.

| Class | Why only the user | Source |
|---|---|---|
| Money leaving an account, or metered spend beyond an authorised cap | Not the harness's money | ADR-0019, ADR-0026 |
| A credential, permission or authentication only the user holds | The harness cannot obtain it | ADR-0019 |
| A preferential question no fact settles | No experiment substitutes for a value judgement | ADR-0018 D4 |
| An action outside the safety floor | Reserved by construction | ADR-0022 |
| The β verdict on an artefact | Human judgement is the ground truth being measured | ADR-0002 |
| Publishing, transmitting or exposing anything beyond the machine | Irreversible and outward-facing | ADR-0024, publication policy |
| Lifting a gate, or approving a specification | Reserved to the principal | V0-18 |

### 3. The affordability test, which is the part the evidence adds

Falling in a class is necessary but **not sufficient**. The harness asks only if the user can
answer *better than the harness can*, at a cost they can afford in that moment. An ask must
carry what makes it answerable: what was already tried, what the default action is if no
answer arrives, and what it would cost to resolve without them (ADR-0020 §3 already requires
the last of these for meetings; it is generalised here).

**An unaffordable ask is worse than no ask.** It does not transfer the decision — it launders
an agent decision as a human one, which is exactly the failure V0-18 exists to prevent,
arriving through the front door with the user's consent. EXP-16 already measured the
machine-side version of this: a fabricated human-participation claim in a meeting no human
joined. [measured] The behavioural version has the user actually present and still not
deciding.

### 4. Rubber-stamps are recorded as unread, not as verdicts

An approval is evidence only if it was affordable. Approval latency is recorded on every ask.
An approval returned faster than a floor proportional to what was being approved is marked
`unread` and **does not satisfy a V0-18 human decision**; the harness must either make the
ask cheaper or stop asking. Sub-second approval of a large diff is an unambiguous complacency
signal available to the harness for free. [cited]

The floor is a preferential parameter, set by the user, not derived. Naming it as preferential
is deliberate: ADR-0021 fixed a pushback count and left its quality unmeasured, and this ADR
should not repeat that by pretending a threshold is a finding.

### 5. An ask budget, spent per period and reported

Interrupts are a finite resource. The harness records every ask with its class and outcome,
and reports the rate. EXP-19 already sets a friction budget for outcome-feedback prompts;
this generalises it to every interrupt. Breaching the budget is a defect in the harness, not
in the user.

## Consequences

**Positive.** The user's attention goes to the decisions that are actually theirs. Agency is
preserved by *scope* — they own a small set of decisions completely — rather than by volume.

**Negative.** The harness will decide wrongly in the reversible cases, visibly, and the user
will see it. That is the trade being made deliberately: a cheap wrong decision that can be
undone beats an expensive question that gets rubber-stamped.

**Neutral but load-bearing.** Every autonomous decision now carries a reversal path in its
event record. That is a schema commitment, and a public interface under ADR-0023 T2.

## Evidence against

- **Every study cited is from an adjacent population**: crowdworkers on mazes, nutrition and
  hotel reviews; developers surveyed on burnout. None is a solo maintainer supervising agents
  on their own repository, and none measured an ask budget. [asserted]
- **The exhaustive class list is asserted, not derived.** It is assembled from existing ADRs
  and Joe's sentence. A class that turns out to be missing will be discovered by something
  going wrong. [asserted]
- **The latency floor is a preferential parameter dressed in a mechanism.** A user who learns
  the floor can defeat it by waiting, exactly as ADR-0021's two-pushback cap is trainable.
  This is the same objection, unresolved for the same reason. [asserted]
- **"Make reversal cheap" is easy to write and expensive to build.** Worktrees and an
  append-only log make some reversals cheap; a published artefact, a spent token and a sent
  message are not reversible at any price, which is why they are in §2. Components whose
  reversal path is expensive will be under pressure to claim they have one. [asserted]
- **This ADR increases the harness's authority**, and it was written by the harness. Q19's
  rule applies: the party that produced the material cannot certify what it missed.
  [asserted]

## Enforcement

Every rule below ships with its check in the same commit as the code that implements it (I1).

- Check: an ask whose declared class is not in §2 is rejected at the boundary, at
  configuration load rather than at runtime.
- Check: an autonomous decision event without a `reversal` field fails schema validation.
- Check: an approval whose recorded latency is below the configured floor is stored with
  `unread: true` and a fixture proves it cannot satisfy a V0-18 human decision.
- Check: the ask-rate report is derivable from the trajectory alone, so the budget cannot be
  evaluated from memory.

## What would overturn this

**EXP-33**, registered before any of this is built. If asks are rare and none is rubber-stamped
under the current, simpler arrangement, this machinery is unnecessary and should be cut rather
than kept for tidiness. If the rubber-stamp rate is high, the affordability test is doing real
work. If the user reports loss of agency while the ask rate is low, the class list is wrong
rather than the budget.

# 0033. Decide by default; ask only where the user is the only valid decider

- **Status:** PROVISIONAL — rests on human-subject evidence from adjacent populations; EXP-33
  measures it here
- **Date:** 2026-08-20
- **Deciders:** Joe Brown (the principle), Claude Opus 5 (the mechanism)
- **Inquiry tier reached:** T1 ground — a principle plus published measurements, none of them
  on this system
- **Executable model:** none. The thresholds are preferential and are named as such.

## Update: 2026-08-20 — attribution corrected, and evidence that cuts against this ADR

**The reversibility framing is Bezos, not Jobs.** [cited] Its primary source is Amazon's 2015
letter to shareholders: *"Some decisions are consequential and irreversible or nearly
irreversible — one-way doors … We can call these Type 1 decisions. But most decisions aren't
like that — they are changeable, reversible — they're two-way doors."* The same letter names
the failure mode this ADR exists to prevent: organisations applying the heavy Type 1 process
to Type 2 decisions, producing *"slowness, unthoughtful risk aversion, failure to experiment
sufficiently, and consequently diminished invention."* [cited]

Two further corrections. "70% of the information" and "disagree and commit" are from the
**2016** letter, not the 2015 one, and citing 2015 for them is a common error. [cited] And
Bezos's Type 1 / Type 2 is his own coinage in that passage — it is **not** Kahneman's System 1
and System 2 and must never be written as though it were. [cited]

**A stopping rule this ADR lacked.** Kozyrkov's line restates the decision-analysis definition
of a decision, whose foundations are Ronald Howard's. [cited] Howard supplies what §3's
affordability test was reaching for without naming: the **expected value of clairvoyance** is
the upper bound on what any information-gathering is worth, so **when no possible answer would
change the chosen action, asking is strictly irrational, not merely expensive.** [cited] That
is a sharper test than affordability and it subsumes it: an ask that cannot change the action
fails before cost is considered.

**The evidence against, and it is strong.** Preferring reversibility is a documented human
bias, not only a heuristic. Shin & Ariely measured participants spending real money to keep
options open where expected values were identical, and attribute it to loss aversion rather
than any genuine value of flexibility. [cited] Gilbert & Ebert found that people who could
change their minds about which photograph to keep **liked their result less** than those who
could not — and most still preferred the changeable option, mispredicting their own cost.
[cited]

So a harness that maximises reversibility amplifies two measured errors: over-investment in
keeping doors open, and reduced commitment to the result. It also compounds tonight's finding
that higher self-reported confidence in the AI is associated with less critical engagement
(b = −0.69): **perpetually reversible output invites perpetual non-commitment.** [asserted]

**Corrected 2026-08-20.** This previously read "earned trust *reduces* critical engagement" and
was tagged `[cited]`. The source is a **cross-sectional self-report association**, and a
cross-sectional coefficient carries no causal direction, no longitudinal "earning", and no
measure of objective scrutiny or artefact quality. [measured] The association is real and is
still worth naming; the mechanism built on top of it is this project's inference, so the
inference is now tagged `[asserted]` while the coefficient stays `[cited]`. Recording a reversal path is therefore a safety
property, **not** a goal to maximise, and §1 should be read as "make the reversal available",
never "prefer the reversible option". [asserted]

**Reversibility is currently declared, not measured** — the same defect ADR-0020 records for
evidence classes. [asserted] V0-24 closes it: a recorded reversal must be *executable*, and a
sampler periodically executes recorded reversals in a scratch worktree and publishes the
misclassification rate as a measured number. A reversal path nobody has ever run is a claim.

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
ask cheaper or stop asking. Sub-second approval of a large diff is treated here as a
complacency signal available to the harness for free. [asserted]

**Corrected 2026-08-20.** This read "an *unambiguous* complacency signal" and was tagged
`[cited]`. **No source in the bibliography validates a sub-second threshold for code review**, and
none supplies the observed positive and negative counts from which its sensitivity or specificity
could be computed. [measured] It is a plausible heuristic and it is ours, so it is tagged as
ours. "Unambiguous" is withdrawn: a fast approval of a diff the user had already read in their
editor is not complacency, and the rule cannot currently tell the two apart. Whether the signal
discriminates at all is an empirical question nobody here has asked, and it should be registered
before the floor is given any weight.

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

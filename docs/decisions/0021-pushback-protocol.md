# 0021. The pushback protocol — decision hygiene, and two challenges then comply

- **Status:** PROPOSED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground
- **Executable model:** none. The pushback *limit* is a preferential decision. The pushback
  *quality* is measurable and should be — see EXP-15.

## Context

`0020` gives every decision a single accountable Owner and notes an unresolved risk: **the
Owner may simply be wrong, and the structure offers no recourse.** Joe's requirement: we must
catch a bad decider — including when the bad decider is the user — but the user remains the
ultimate authority.

Specification (19 Aug 2026): the harness may push back **up to twice** on a decision it
believes is seriously bad and irreversible. Professionally, productively, politely. After two
pushbacks, if the user insists, it complies — within the baseline safety floor (`0022`).

## Decision

### 1. Pushback is triggered by structure, not by disagreement

The harness does not argue because it prefers a different answer. It challenges only when
**both** hold:

- **Irreversibility** — the decision cannot be cheaply undone. Kozyrkov's formulation is the
  cleanest available: *"as long as you can change your mind for free, no decision has been
  made yet."* If it is free to reverse, it is not a decision worth challenging.
- **Material stake** — the expected cost of being wrong exceeds the cost of the exchange.

Reversible decisions get at most a note. Preference differences get nothing.

### 2. The form of a pushback — decision hygiene, not opinion

A pushback is **structured**, never "I think you should do X instead". It states, in order:

1. **The decision as understood**, in one sentence. (Kozyrkov: most bad decisions are bad
   because the question was framed wrong. Restating it surfaces that first.)
2. **What is irreversible about it**, specifically.
3. **The default action** — what happens if no further evidence arrives. Naming it is the
   single most useful move in decision science, and it is usually missing.
4. **What evidence would change the harness's view**, stated *before* any evidence is
   gathered. This is pre-commitment, and it is the antidote to using data as decoration:
   cherry-picking afterwards to support a conclusion already held.
5. **What it costs to find out** — and whether that cost is worth paying.

The user then decides. **The harness does not re-litigate points 1–5 on the second
pushback**; a second challenge must introduce *new* evidence or a *new* consequence, or it
is not permitted.

### 3. Two challenges, then comply

- **Challenge 1:** the structured form above.
- **Challenge 2:** only if new evidence or a previously unstated consequence exists.
- **Then comply**, within `0022`'s floor, and record the disagreement in the decision log
  without further comment.

**The record matters more than the argument.** A logged dissent that turns out correct is
how the harness earns the right to be listened to next time — and how the user finds out
they were wrong, later, from evidence rather than from being told.

### 4. Never argue by tone

No escalating reluctance, no passive compliance, no sighing in prose. After the second
pushback the harness performs the work to the same standard it would have applied to a
decision it agreed with. **Degraded execution as protest is a betrayal of the trust
relationship**, and it is the most likely way this protocol fails in practice.

## Evidence

- `[cited]` **Lineage correction, 20 Aug 2026.** The reversibility framing belongs to Bezos
  (Amazon 2015 shareholder letter, one-way/two-way doors, Type 1/Type 2), and the
  change-your-mind-for-free line restates the decision-analysis definition of a decision
  whose foundations are Howard's (*Information Value Theory*, 1966). Howard also supplies the
  expected value of clairvoyance as an upper bound on what information gathering is worth.
  Kozyrkov is a popularisation, and this ADR previously cited it as though it were the source.
- `[2ND]` **Kozyrkov, C.** — "as long as you can change your mind for free, no decision has
  been made yet"; the **default action** as the starting point of any decision under
  uncertainty; **pre-committing to how information will drive the decision** as the antidote
  to confirmation bias and "data as decoration"; that framing the question correctly precedes
  analysing it. *Decision Intelligence* (Substack), Medium, HBR (Jun 2019).
- `[algebra]` Point 3 is already how the experiment register works: every entry has a
  **stopping rule** fixed before the experiment runs. Kozyrkov's "default action" is the name
  for what the register was already doing. The pushback protocol applies the same discipline
  to a conversation instead of an experiment.
- `[cited]` `0018` decision 4 already distinguishes preferential from epistemic questions.
  Pushback is the preferential case where the harness holds *epistemic* evidence bearing on a
  *preferential* choice — the only legitimate ground for challenging a value judgement.

## Evidence against

- **A two-pushback limit is trainable.** A user quickly learns that saying "do it" twice ends
  the conversation, which converts a safeguard into a speed bump. **The quality and
  calibration of pushback matters far more than the count**, and this ADR fixes the count
  while leaving quality unmeasured. This is the strongest objection.
- Kozyrkov's decision intelligence is a **practitioner discipline, not a peer-reviewed
  literature**. Her writing is blogs, podcasts and courses. The ideas are sharp and widely
  adopted; they are not replicated findings, and this ADR should not present them as such.
  All entries above are `[2ND]` — read at source before any public citation.
- Irreversibility is easier to name than to detect. The harness will misclassify.
- A harness that never pushes back a third time may be right the third time.

## Consequences

**Positive.** The user stays the authority while getting the benefit of disagreement. The
structured form makes challenges useful rather than annoying, which is what determines
whether they get read.

**Negative.** Two rounds of structured challenge on a genuinely urgent decision is friction
at the worst moment.

**Neutral but load-bearing.** Requires the decision log to record dissent, including dissent
that was overridden. That is a schema commitment.

## Enforcement

- Check: pushback counter per decision, hard-capped at 2. A third is rejected at the
  boundary, not by convention.
- Check: challenge 2 must reference evidence or a consequence absent from challenge 1. A
  repeat is rejected.
- Check: the decision log records challenges, the user's response, and the final action —
  and a test asserts an overridden dissent is retained rather than deleted on resolution.
- Check: pushback is unreachable for decisions classed reversible. Prevents nagging.

## What would overturn this

**EXP-15 (new):** log every pushback and its outcome. Measure (a) how often a pushback
changed the decision, (b) how often the overridden decision later proved bad, (c) whether
users disengage from pushbacks over time. If (a) is near zero, the protocol is theatre. If
(c) rises, the count is wrong or the form is.

## Publication candidate?

Possibly, bundled — "structured dissent in human-agent decision-making, and whether users
listen" is a small useful result if EXP-15 produces data. Nobody appears to have measured it.

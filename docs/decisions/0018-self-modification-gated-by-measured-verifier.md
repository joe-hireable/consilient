# 0018. Self-modification is gated by measured verifier reliability, and the verifier is not self-modifiable

- **Status:** PROPOSED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown (vision), Claude (the gate)
- **Inquiry tier reached:** T1 ground
- **Executable model:** none yet — but this is a strong T2 candidate: the compounding-error
  dynamic below is exactly the kind of thing a model settles and argument does not.

## Context

Joe's requirement: the harness should be living — developing itself, learning, building
knowledge and memory, synthesising tools and MCPs it lacks, personalising, and reasoning
scientifically rather than by pattern-match.

The field is mature. See `../20-design/living-system.md` for the full prior-art table:
Darwin Gödel Machine (ICLR 2026), SICA, Huxley–Gödel Machine, HyperAgents, Gödel Agent,
Live-SWE-agent, AFlow, AlphaEvolve, The AI Scientist, SkillOpt, ACE, plus a 2026 survey.
Reported gains are real — DGM 20.0% → 50.0% on SWE-bench, SICA 17% → 53% on a Verified
subset.

**Every one of them accepts a self-modification when a test says it is better. None measures
how often that test is wrong.**

## Decision

**1. No self-modification is accepted on an unmeasured acceptance signal.** A modification is
promoted only when the verifier that judged it has a measured β and that β is below the
threshold implied by the change's blast radius.

**2. The verification layer is not self-modifiable — PROVISIONALLY, pending EXP-12.**

In scope for self-modification: skills, synthesised tools, prompts, routing configuration,
memory organisation.

Out of scope **by default, until evidence says otherwise:** the verifier suite, the β-meter,
budget primitives, the permission model, the trajectory log schema, and this list.

Joe's decision (19 Aug 2026): forbid it now, revisit when EXP-12 reports. **Note the limit
of that experiment** — EXP-12 answers *"does verifier quality affect self-improvement
outcomes?"* It does **not** answer *"can a system safely improve its own verifier?"* Those
are different questions and the second needs **EXP-13**. A positive EXP-12 result argues for
keeping the restriction; a negative one does not by itself license lifting it.

Budget primitives and the permission model stay out of scope regardless of either
experiment. Nothing in EXP-12 or EXP-13 bears on them.

**3. Synthesised tools are disposable by default, promoted by evidence.** Session-scoped on
creation; persistent only after usage count and success rate clear a threshold, computed
retrospectively from the trajectory log — never from a projected business case (see `0012`
and the RoL critique in `../30-source-material/gemini-session-critique.md`).

**4. Escalation to the human distinguishes three cases**, not two.

| Case | Example | Behaviour |
|---|---|---|
| **Preferential** — the answer is the user's to give | "MIT or AGPL?" | **Ask immediately.** No experiment substitutes for a value judgement. |
| **Epistemic and cheap to test** | "is this retrieval path faster?" | **Do not ask. Run it.** Asking here is a failure of the ladder. |
| **Epistemic and expensive to test** | "which of these three architectures scales better?" | **Ask** (Joe, 19 Aug 2026). |

The third case is the Inquiry tier's own stopping rule applied honestly: if the expected
regret of being wrong is smaller than the cost of the inquiry, do not inquire. When the
experiment is expensive and the human is cheap, asking *is* the efficient move — the human
is a genuinely different class of facts (`0010`), holding context the system lacks.

**"Expensive" must be defined, not felt.** Proposed threshold, to be calibrated: an inquiry
is expensive when its estimated cost exceeds either a per-decision token budget or a
wall-clock bound the user set. Below that, run it. Above it, ask — and **state what you would
have run and what it would have cost**, so the user can say "go ahead anyway".

## Evidence

- `[cited]` Schmidhuber's Gödel machine required a **proof** that a self-modification
  increases expected utility. DGM's stated contribution is replacing the intractable proof
  with **empirical validation**. That substitution is the field's foundation and its
  unexamined premise is that the validator is sound.
- `[cited]` **Huxley–Gödel Machine (ICLR 2026) already rejects** the assumption that higher
  benchmark scores correspond to greater self-improvement capacity — independent evidence
  that the acceptance signal is the weak point. HGM proposes a different *measure*; it does
  not measure the *error rate* of the signal.
- `[algebra]` Compounding: in a single-shot decision a false accept costs one bad artefact.
  In an archive-based self-improving system, each generation is selected by the same signal
  from a population seeded by earlier accepts. Errors are not independent across
  generations — they are inherited. A ratchet with a slipping pawl runs backwards while
  appearing to advance.
- `[cited]` **Gödel Agent (ACL 2025)** already uses a verification agent that checks
  modifications against safety invariants before applying them. Precedent for the pattern;
  it does not measure the verifier.
- `[cited]` HyperAgents' own risk list: bypassing alignment safeguards through
  self-modification, harmful behaviour in unexpected areas, co-evolving systems that are
  harder to audit. Field-converged mitigations: restrict what can self-modify, stage through
  sandboxes, human approval for high-impact changes, log all modifications.
- `[cited]` **Live-SWE-agent** synthesises tools at runtime from a minimal scaffold when the
  toolchain falters, optimising empirical success rate and execution cost — precedent for
  decision 3, and for triggering synthesis on observed failure rather than on planning.
- `[cited]` The compounding argument passes `0010`: the verification agent runs the checks,
  so it holds a genuinely different class of facts from the agent proposing the change.

## Evidence against

- **The gate may be unaffordable.** β needs 50–200 human-labelled artefacts per verifier
  (`0002`). If every synthesised tool needs its own measured β before promotion, nothing gets
  promoted. A cheaper tiering — measured β for high-blast-radius changes, coarse heuristics
  for session-scoped tools — is probably necessary and is **not yet designed**.
- The published systems get real gains *without* this gate. Their benchmark improvements are
  not obviously corrupted. The compounding argument is `[algebra]` under an assumed error
  model and **has not been demonstrated empirically** — it may be a small effect at realistic
  β. This is the strongest objection and the reason this ADR is PROPOSED.
- "The verifier is not self-modifiable" forecloses a real capability. If the test suite is
  the bottleneck, a system that cannot improve its own tests is capped. The counter is that
  a system which *can* improve its own tests can improve them into agreement with itself —
  but the trade is real and this ADR takes the conservative side.
- No deployed system does recursive self-improvement; the whole discussion may be premature.

## Consequences

**Positive.** Turns the project's existing thesis into the safety property of a much larger
ambition — the two are one idea at different levels, which is a stronger position than two
features. Gives a principled answer to "how far do we let it modify itself".

**Negative.** Slower self-improvement than the published systems, by design. If the
compounding effect is small, that cost buys little.

**Neutral but load-bearing.** Makes the trajectory log, verdict prompt and β-meter
prerequisites for *any* self-extension. Which is the right build order regardless.

## Enforcement

- Check: a hard allowlist of self-modifiable paths. Anything outside it is rejected at the
  write boundary, not by convention. Same commit (I1).
- Check: a test asserts the verifier suite, β-meter and this allowlist are themselves outside
  the allowlist. **Self-referential and deliberately so.**
- Check: every promotion event in the trajectory log records the β of the verifier that
  approved it, and its sample size. A promotion with an unmeasured verifier fails.
- Check: synthesised tools run in the quarantine sandbox tier until promoted.

## What would overturn this

**The decisive experiment (proposed as EXP-12):** run an archive-based self-improvement loop
twice on the same task set — once with a deliberately weakened verifier (high β), once with a
strong one — and measure whether the weak-verifier archive degrades over generations while
appearing to improve. If it does not degrade measurably, the compounding argument is wrong
and this gate is unnecessary caution.

That experiment is also the paper.

## Publication candidate?

**Yes — potentially the strongest one in the project.** "Self-improving agent systems accept
modifications on unmeasured acceptance signals, and here is what that costs" addresses a
named foundation of an active, well-cited field, with a clean experimental design and a
falsifiable claim. Clears G2 (novel — no prior art found), G3 (useful to everyone building
these), and G4 if the limits are stated. Needs G1: run EXP-12 first.

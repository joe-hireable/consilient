# 0003. Ship no learned routing policy in v0

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T2 model
- **Executable model:** `../10-research/experiments/simulations.py` (exp 3, 4a)

## Context

The original plan included "dynamic model selection and orchestration" learned from a
proprietary trajectory corpus, with that corpus intended as the commercial moat. This is
the obvious design and the literature is full of learned routers. It deserved a check
before a year went into it.

## Decision

No learned routing policy in v0. Route cheap-first and escalate on verifier failure.
Revisit only when the wasted-work multiplier on a failed cheap attempt is measured at ≥2×.

## Evidence

- `[simulated]` Thompson sampling over per-task-class routing needs **~5,000 trajectories to
  merely draw level** with plain always-cheap-then-escalate, and gains nothing after
  (25,000 trajectories: −0.0008 vs best fixed). Mechanism: escalation-on-verifier-failure
  *is already adaptive routing*; the learned prior has little left to add.
- `[simulated]` Headroom appears only when failed cheap attempts are expensive in
  wall-clock, not just tokens: multiplier 1.0× → +0.002 (noise); 2.0× → +0.024;
  5.0× → +0.123.
- `[asserted]` A solo developer will not generate 5,000 labelled trajectories quickly.
- `[cited]` Consistent with Dekoninck, Baader & Vechev (ICML 2025), which shows optimal
  serving lies on a continuum between pure routing and pure cascading — the cascade end is
  a legitimate point on that continuum, not a degenerate case.

## Evidence against

- `[cited]` FrugalGPT reports matching the best single model at up to 98% cost reduction
  using learned confidence thresholds; RouteLLM and Hybrid LLM both report real gains from
  learned routing. Our simulation says the gains are largely recovered by the cascade alone
  — **that is a claim about our simulated regime**, and those papers measured real systems.
- Our task-class competence vector was invented. A more dispersed real-world competence
  profile would give a learned prior more to exploit.
- This decision also removed the intended commercial moat. There is a motivated-reasoning
  risk in the opposite direction: a result that simplifies the roadmap is one we wanted.

## Consequences

**Positive.** Removes the largest chunk of speculative ML work from v0. Removes the need to
accumulate a corpus, which removes the telemetry consent flow, which is consistent with
`0004` (full OSS, local-first).

**Negative.** If the wasted-work multiplier is high in practice, we leave measurable value
on the table until we notice.

**Neutral but load-bearing.** The trajectory record is now for *measuring β and diagnosis*,
not for training a policy. That changes what it needs to contain.

## Enforcement

None required. This is an omission, and omissions do not need enforcement — but see
`0002`'s enforcement note: no config key may set routing depth directly.

## What would overturn this

Measure the wasted-work multiplier on real runs. If a failed cheap attempt costs ≥2× the
frontier run in wall-clock the user actually cares about, reopen. Instrument for this from
day one so the answer is available rather than argued.

**Update 2026-08-19:** a local cheap tier on the RTX 5090 rig makes this materially more
likely. A failed local attempt costs wall-clock on a single serialising GPU rather than
tokens, which plausibly pushes the multiplier past the 2× threshold. See
`../10-research/local-experimentation.md`. **Measure it before assuming either way** — this
is the named trigger to reopen this ADR.

## Publication candidate?

**Possibly, bundled.** "Escalation-on-verification recovers most of the benefit of learned
routing in the coding domain" is a modest, useful negative result — but only if reproduced
against real traces (T3), not from our simulation alone. Would belong inside the β paper
rather than standing alone.

# Pull request

> Gates are proportional to blast radius, not to effort or diff size.
> Full rules: `docs/decisions/0023-pr-review-gates.md`.
> **Unsure of the tier? Ask on the issue before writing code.** Nobody should discover T3 after.

## Tier

- [ ] **T0 — Trivial** · typos, formatting, dead links, doc clarity
- [ ] **T1 — Local** · bug fix, refactor within a module, tests
- [ ] **T2 — Interface** · schema, public API, new dependency, adapter behaviour
- [ ] **T3 — Load-bearing** · routing, β computation, verifier, budget or permission
      primitives, self-modification allowlist, safety floor

*A PR that changes tier during review restarts at the higher tier.*

## What this does

<!-- One paragraph. What changes and why. -->

## Evidence

<!--
Tag EVERY factual claim:
  [measured]  observed in a real system we ran
  [simulated] output of a model with assumed functional forms
  [cited]     from a named source — cite the source that MEASURED it, never a blog
  [algebra]   exact derivation from stated assumptions
  [asserted]  judgement, no evidence yet — HONEST AND ACCEPTED

An untagged or mistagged claim is a request for changes.
-->

## Evidence against — **required at T2 and above**

<!--
What would make this wrong. What you searched and did NOT find. Which existing ADR this
cuts against. If you searched and found nothing against, say what you searched.

A PR presenting only supporting reasoning is advocacy and will be sent back regardless of
code quality.
-->

## Prior art — **required at T2 and above**

<!--
What you searched, what you found. "Someone already built this, MIT-licensed" has been the
correct answer three times on this project. Finding that it exists is a VALUED contribution,
not a wasted PR — say so and we adopt instead.
-->

## Checklist — all tiers

- [ ] Every commit signed off (`git commit -s`) — see `CONTRIBUTING.md`
- [ ] CI green
- [ ] **If this declares an invariant, boundary or chokepoint, the check that enforces it is
      in this same commit** (invariant I1 — non-negotiable at every tier)
- [ ] I can explain every line. Agent-assisted work is expected and fine; unexamined agent
      output is not.

## T1 and above

- [ ] A failing test that now passes — or a stated reason no test is possible

## T2 and above

- [ ] Linked ADR in this diff
- [ ] What breaks, and the migration path

## T3 only

- [ ] Measurement on real data
- [ ] Linked entry in `docs/10-research/experiment-register.md`
- [ ] A stopping rule a reviewer can apply

## Experiment, research or evaluation PRs

Held to the **same** standard, not a lower one. Negative results are welcomed and reviewed
identically — a PR showing a feature is ceremony is worth more than one adding a feature.

- [ ] Runnable code, fixed seed, pinned versions
- [ ] **Stopping rule was fixed before the run.** A stopping rule written after seeing the
      result is not a stopping rule.
- [ ] Bibliography promotions (`[SNIP]` → `[FULL]`): source read, date recorded, and anything
      we got wrong corrected. **Correcting our errors is the highest-value contribution
      form.**

---

*Reciprocity: rejections name the specific rule and the specific gap, and say what evidence
would land it. The maintainer's own PRs meet these gates. A rule the maintainer exempts
himself from is not a rule.*

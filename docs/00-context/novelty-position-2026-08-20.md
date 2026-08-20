# The honest novelty position

**20 August 2026.** `CLAUDE.md` names this as a standing job: *"Check the novelty claim…
Establish honestly what is left that is genuinely new."* Four adversarial assessments, each
independently refuted by a skeptic instructed to default to "overstated", then synthesised.

**Provenance, and it limits what follows.** Repository claims were verified by grep or script and
are `[measured]`. Claims marked `[cited-web]` were fetched **at abstract level only** — treat them
as `[ABS]`, not read. Anything from training memory is `[cited, unfetched]` and **may not enter an
ADR's `[cited]` line** without being fetched. That distinction is the whole reason the earlier
"no prior art found" claim failed, and repeating it here would be absurd.

---

## The paragraph

> Consilience is a well-engineered instance of a known idea, carried by an unusual evidence
> discipline. Measuring a verifier's false-accept rate and spending verification effort
> accordingly is old: acceptance sampling names it consumer's risk (Neyman–Pearson, 1933);
> mutation testing measures it per repository, label-free, and **already fails your build on it** —
> PIT's `mutationThreshold`, Stryker's `thresholds.break` `[cited-web]`; selective prediction gives
> the risk–coverage form; and by mid-2026 at least four preprints derive routing depth or
> repair-loop stopping from an imperfect verifier's measured error rate `[cited-web]`. β has also
> already been measured on agent-emitted artefacts — SWE-Bench+ found 31.08% of passed patches
> suspicious, and this repository's own `[FULL]` survey records maintainer merge rates 24.2
> percentage points below grader scores. What four adversarial searches could **not** place in the
> literature is the same quantity estimated **per repository and per check class, against the fault
> distribution a coding agent actually emits, labelled by the person who bears the cost**, in a
> deployment where the oracle is deterministic and the human reference standard has already seen
> the oracle's verdict. **That is a measurement programme, not an architecture — and it has not
> been run.** The meter is built (789 lines, 47 tests, `mypy --strict` clean) and has received
> **zero rows**.

**Why it is still worth building.** The measurement is precisely the expense every neighbouring
literature exists to avoid, and it is the only thing that settles whether the routing conclusion
holds on a real repository. Both outcomes are worth having. The discipline — evidence tags,
read-depth flags, invariants shipping with their checks, an audit that catches its own author —
is the part that is real today, and it is craft rather than research.

## The three-part test, applied honestly

For *"we measure β"* to be a contribution, three things must hold: **(a)** nobody measures it,
**(b)** measuring it changes a decision, **(c)** this project can measure it.

- **(a) is narrower than claimed.** ADR-0002 states its own identity — *"Critic recall ≡ 1 − β…
  This identity is the whole claim."* You cannot fail to find prior art for `1 − x = 1 − x`. With
  mutation testing occupying label-free per-repository measurement of the same false-negative
  rate, the residual reduces to one empirical question: **does the check suite's false-negative
  rate against the faults an LLM agent actually emits differ from its rate against synthetic
  mutants?**
- **(b) is currently false.** Gate B2 is the only gate condition whose value depends on β, and it
  cannot fail. β\* appears zero times in the specification and zero times in `src/`. **β gates
  nothing.** [measured]
- **(c) is currently false.** Zero `attempt.outcome` events; the only empirical β is on the
  transposed axis; proxy labels are inadmissible to `compute()` by design and no pipeline joins
  the two; and at true β ≥ 0.111 no sample size clears β\*, while both corrected EXP-01 estimates
  are 0.12 and 0.14. [measured]

## Where this leaves the positioning

**Consilience is Meta-Harness's missing precondition, not its rival.** Meta-Harness optimises
harness code against an objective signal and already knows that signal is gameable — it audits for
regex leakage — but it mitigates leakage while ignoring *weakness*. β is the other half of that
mitigation. `[cited-web]`

That is an honest and defensible place to stand. It also has an uncomfortable implication worth
stating rather than burying: **a contribution to somebody else's loop argues for a paper or a
plugin, not necessarily a standalone orchestrator maintaining adapters for four evolving CLIs.**
`competitive-landscape.md` already makes the plugin case. That is a strategy question, not an
evidence question, and it is Joe's.

## Genuinely defensible, ranked

1. **α on this corpus.** The other off-diagonal cell, needing the verdicts β discards, with both
   columns already stored. Measurable today where β provably is not. **Not novel** — the
   flaky-test literature owns it, and this bibliography contains **zero** flaky-test entries
   [measured] — but honest, ours, and it moves every threshold.
2. **Per-check β against agent-produced faults.** Survives mutation testing only through the
   unanswered coupling question. The repository already holds a hint that agent faults do *not*
   couple to mutants: EXP-05's OpenCode run passed functional tests while creating an unrequested
   file.
3. **V0-24, the reversibility misclassification sampler.** β applied to a *different*
   self-declared property. No prior art was named against it by any of four runs. Unimplemented.
4. **ADR-0018's admissibility gate on the objective signal.** A genuine conceptual wedge into
   Meta-Harness's loop, which optimises against `r` and never studies `r`. Attached to nothing
   executable.

## Drop or downgrade — with locations

- **`literature-review.md:189`** — *"the identity β ≡ 1 − critic recall … No prior art found"*.
  **Delete.** ADR-0002 self-tags it `[algebra]`; absence of prior art for a definition proves
  nothing.
- **`literature-review.md:188`** — the parallelism-ceiling half is dead (`n_max ≥ 3.125` for every
  β including 1.0); the routing-depth half is refuted `[cited-web]`.
- **`ADR-0002` § no-prior-art** — the eight sources searched are **all LLM-routing**; zero
  software-engineering or statistics venues. The bibliography has zero hits for mutation testing,
  flaky tests, acceptance sampling, selective prediction or defect-removal efficiency [measured].
  **Downgrade from "none found" to "not searched".**
- **`ADR-0002` § largest open risk** — arXiv:2605.00663, marked *"Not read"*. Fetched twice
  independently: it is visual affordance grounding and gates on self-consistency without labels
  `[cited-web]`. **Close it.**
- **`docs/decisions/index.md`** — ADR-0018 as *"the project's likely novel contribution"*. Its
  bibliography section is 0 `[FULL]` / 2 `[ABS]` / 11 `[SNIP]` [measured]. That is a title scan,
  not a comparison. **Downgrade the claim, not the ADR.**
- **ADR-0010 / `CONSILIENCE.md` clause 2** — `evidence_class` appears **zero times in `src/` and
  `tests/`** [measured]. Not a weak check: **no check.** Against working principle 3, in the rule
  the project is named for.
- **Gate B2** — mark **non-discriminating**, not merely unmet.
- **α = 0.03** in `simulations.py` — label **invented** at every use.

## One structural finding

**EXP-41 — the cheapest available test of this project's central novelty — is not registered.**
The register states *"Numbers are allocated here and nowhere else"*; EXP-41 exists only as a draft
in `manufacturing-oracles.md`. Worse, **every one of its stopping rules is written to admit or
kill the proxy; none is written to retire β.** If mutation score reproduces the per-check
ordering, that is simultaneously the best operational outcome — no thirty human rejections needed
— and the worst novelty outcome. **The register as written cannot record the second reading.**

## What would tell Joe the thesis is wrong

Run EXP-41's cheap half — PIT or `mutmut` on this repository, per check. **If mutation score
reproduces the per-check β ordering, the instrument was already free, off-the-shelf and
forty-eight years old, and Consilience is an orchestration front-end for mutation testing.**

Two smaller falsifiers with the same force:
- If α lands near the measured 0.12–0.24, β\* is dominated by the flaky-test rate and the headline
  quantity belongs to someone else's literature.
- If the first thirty rows put β̂ anywhere near EXP-01's corrected 0.12–0.14, **no sample size ever
  clears β\* = 0.088** and the routing claim the architecture rests on is dead on arrival — which
  is a real result and should be published as one.

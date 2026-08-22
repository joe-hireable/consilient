# Answer quality: one useful answer with checks that touched the world

**Correction:** all 17 pre-existing specifications named by the brief were read; none specifies the final
user-visible answer or measures perceived quality against a strong single-model answer, but several
do specify internal mechanisms that could improve quality, so the broader claim that none explains
why an answer could be better is false. [measured: `docs/superpowers/specs/`, 2026-08-22]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; [ADR-0087](../../decisions/0087-return-one-answer-with-decision-relevant-checks.md)
  is PROPOSED. [measured]
- **Experiment state:** `EXP-128` was verified free by exact case-insensitive search across the
  register, tracked project paths and relevant hidden/untracked paths before this file named it.
  Its proposed entry is written below but deliberately absent from
  `docs/10-research/experiment-register.md`; it is **not pre-registered** until the register owner
  writes it. [measured]
- **Dependency state:** the brief names ADR-0077 as fusion owner, but no tracked ADR-0077 exists in
  this commit. Fusion remains undefined here; this proposal cannot advance to ACCEPTED or
  implementation until ADR-0077 or an accepted equivalent assigns one fusion/exposure owner.
  [measured] [asserted]
- **Scope:** the one primary response a user reads, the checks that may justify it, when to answer
  directly, and the blind comparison that could support a visible-quality claim. [asserted]
- **Non-goals:** another orchestrator, another fusion rule, another action boundary, a seventh CLI
  command, visible reasoning, or a claim that more agents are intrinsically better. [asserted]

## 1. Answer first

Consilient returns one answer from one accountable Owner. The answer leads with the useful outcome,
then shows a compact `Checked` line containing only source-bound claims, executed results and real
comparisons that occurred. A material recommendation also names the observation that would change
it. If no unavailable, decision-changing fact is worth acquiring, the Owner answers directly and
says that no extra check was warranted. [asserted]

This is not yet a demonstrated quality advantage. It is a response policy whose claimed benefit is
that a user can distinguish generated prose from claims checked against the world without reading a
committee transcript. `EXP-128`, once registered and run, can confirm or defeat the perceived-quality
claim on a frozen prompt mixture. [asserted]

## 2. The bar and the surviving delta

The frozen product review names ChatGPT Work as the strongest existing whole product for general
delegated work, with medium confidence, because its single surface spans long tasks, tools, files,
browser work and finished artefacts. The same review found no independently labelled product-level
accepted-outcome or verifier false-accept result. [measured:
`../../00-context/product-bar-2026-08-22.md:14-37`]

Hermes already supplies delegation, checkpoints, persistent goals and memory, while Ruflo already
supplies a Claude/Codex execution path, shared persistent memory and an evaluation flywheel. Neither
inspected system establishes a matched user-visible answer-quality win. [measured:
`../../00-context/product-bar-2026-08-22.md:90-99`;
`../../00-context/ruflo-teardown-2026-08-22.md:15-26,115-201,388-396,413-419`]

The three easy differentiators are therefore unavailable: cross-harness memory, broad subscription
reach and verifier self-evaluation exist elsewhere. [measured:
`../../00-context/ruflo-teardown-2026-08-22.md:115-143,175-201`;
`../../00-context/subscription-reach-2026-08-22.md:1-20`;
`../../00-context/product-bar-2026-08-22.md:144-160`]

The surviving delta is narrower: bind each material check to the claim it tested, show the resulting
receipt in the answer, retain adverse outcomes, and spend on another evidence path only when it can
change the decision. A well-tooled single model can also do all of this. The comparison must
therefore be against that strong single Owner, not against an untooled chat caricature. [asserted]

### Search record and near misses

| Evidence set read | What changed the design |
|---|---|
| The 17 pre-existing specifications | Evidence fusion, consilience gating, expertise acquisition, model qualification and delivery already constrain internal quality; none defines this final response or a preference test. [measured] |
| ChatGPT Work product bar | Breadth and usability, not a public reliability result, make it the whole-product incumbent. [measured] |
| Tracked product bar and Ruflo teardown | Delegation, durable coordination, shared memory and self-evaluation are incumbents, not differentiators. [measured] |
| ADR-0067 and ADR-0081 | Composition and high-consequence anchor admission already have owners; the brief's ADR-0077 fusion owner is absent from the tracked tree, so fusion remains a prerequisite rather than material to copy here. [measured] [asserted] |
| Ao, Gao and Simchi-Levi; Kim et al.; Jwalapuram et al.; Kraidia et al.; Zhou | The strongest retrieved evidence places the burden on convergence and exposes judge gaming and debate degradation. All cited entries are `[FULL]` in the bibliography, read 2026-08-22. [cited] |

No retrieved source established that a compact evidence-bearing response is preferred to the
strongest same-budget single-model response on general delegated prompts. Absence is bounded to the
named search and is the reason for `EXP-128`, not evidence that no such result exists. [measured]
[asserted]

## 3. What can genuinely improve the answer

A **material claim** is one whose falsity could change the answer, recommendation or action. A
source count, role count or check unrelated to a material claim receives no credit. [asserted]

Let `T0` and `K0` be direct-answer wall time and total model tokens. For an admitted check `j`, let
`t_j` be its measured elapsed time and `k_j` the tokens used to acquire, bind and synthesise its
result. Then `T = T0 + critical_path(t_j)` and `K = K0 + sum(k_j)`: parallel checks can reduce wall
time, but token cost still sums. Missing usage is `unknown`, never zero. [algebra] [asserted]

| Candidate mechanism | Mechanical path to a better answer | Latency and token cost | Honest limit |
|---|---|---|---|
| **Claim checked against a retrieved primary source** | Retrieve after the request; bind the material claim to a canonical locator, retrieval time and content digest; check that the source entails the rendered claim. The user can open the exact support. [asserted] | Adds retrieval and checking time `t_source`; adds bounded source/excerpt and verdict tokens `k_source`. Independent fetches may overlap in wall time, but `sum(k_source)` remains. [algebra] | This improves traceability and can catch stale or invented claims. A primary source may still be wrong, irrelevant or misread; citation presence alone is not correctness. [asserted] |
| **Artefact executed before delivery** | Freeze the acceptance contract, run the code, calculation, browser flow or other real oracle, and bind the terminal result to the artefact digest. [asserted] | Adds execution time `t_run` and bounded contract/log tokens `k_run`; deterministic computation itself need not consume model tokens. [algebra] | A passing check establishes only its contract. Its beta, coverage and transfer remain limits; a launcher exit code is not the result. [asserted] |
| **A competing approach tried and lost** | Run the strongest viable alternative against the same material acceptance contract, preserve both results, and state the decision-relevant reason it lost. [asserted] | Adds alternative construction, execution and comparison: `t_alt + t_compare` and `k_alt + k_compare`. [algebra] | It is real only when the alternative was viable and the same oracle decided. Two acceptance-eligible candidates count against the accepted exposure ceiling; an unexecuted list of options is decoration. [asserted] |
| **A genuinely different anchor converges** | Consume ADR-0081's admitted observation channels and the accepted fusion owner's rule; one Owner synthesises after sealed acquisition. [measured] [asserted] | Adds the selected acquisition's `t_anchor`, its bounded return `k_anchor`, and one Owner synthesis `t_fuse`, `k_fuse`. [algebra] | Structural difference is not statistical independence. Outcome benefit is unmeasured, so convergence is never displayed as proof. [asserted] |
| **A specific falsifier or reversal condition** | Name the observation that would change the answer and the action to take if it occurs. This makes a decision updateable instead of falsely final. [asserted] | Usually one short clause and no new acquisition; its token cost is small but non-zero. [asserted] | It improves usefulness and honesty, not present correctness. “More evidence” or another generic caveat is theatre. [asserted] |

Fok and Weld's review found complementary human-AI performance mainly where an explanation reduced
the cost of checking the answer; that supports executable or source-bound receipts rather than
narrated reasoning. The review does not establish this response policy on delegated work. [cited:
Fok and Weld (2024), arXiv:2305.07722, retrieved 2026-08-22]

### What only looks like quality

| Visible signal | Verdict |
|---|---|
| Agent, role or model count | Never evidence of answer quality. A different family reading the same facts is still echo. [cited: Ao, Gao and Simchi-Levi (2026), arXiv:2603.26993] [asserted] |
| Majority agreement or debate | Never shown as support. Unknown dependence and shared priors make agreement uninterpretable; debate has measured degradation settings. [cited: Kraidia et al. (2026), doi:10.1038/s41598-026-42705-7; Wynn, Satija and Hadfield (2025), arXiv:2509.05396] |
| Self-reported confidence | Never shown as evidence or used as a weight. [measured: working principle 5] |
| Streaming tokens, “thinking”, animated work or raw transcripts | Performance of diligence, not an independently checkable result. [asserted] |
| Citations not bound to the claim they entail | Decoration; a source list may be accurate while the answer is unsupported. [asserted] |
| “We considered alternatives” without a sealed competing result | Decoration; it costs prose and establishes nothing. [asserted] |
| A reference-free judge pass | Not a truth receipt. Zhou's stated GSM8K/Qwen3-4B condition raised judge acceptance from `0.716` to `0.938 ± 0.016` while hidden normalised exact-match accuracy moved from `0.209` to `0.202 ± 0.005`. [cited: Zhou (2026), arXiv:2607.05904v1, retrieved 2026-08-22] |

## 4. The single primary response

### Always present

1. **The answer or finished artefact first.** It is written for use, not as a process report.
   [asserted]
2. **One mode line.** It says either `Direct answer` or `Checked`, and never implies checks that did
   not run. [asserted]
3. **For a material recommendation, one `Could change this` line.** It names a concrete falsifier,
   not boilerplate uncertainty. A mechanical transformation with no decision may omit it. [asserted]

`Checked` contains only applicable items: material claims with source receipts, an executed
acceptance result, a genuinely tried losing alternative, a refusal, or unresolved disagreement. A
missing class is omitted rather than shown as a zero or decorative grey badge. [asserted]

### Available on demand

The user may open claim-to-source excerpts and digests, full execution receipts, the losing
alternative, preserved dissent, adverse outcomes, model/harness provenance, elapsed time, tokens,
tool calls and cost. These details remain in the trajectory and do not compete with the answer.
[asserted]

### Never shown as support

Chain of thought, hidden reasoning, worker transcripts, votes, role-play, model confidence,
agreement percentages, celebratory milestones and streaming-token theatre are never evidence in the
primary response. Harness and model names may appear in provenance details, not as quality badges.
[asserted]

### One-screen demonstration

```text
Recommendation: choose A — [the useful answer and its shortest decisive reason].

Checked · 3/3 material claims linked to primary sources · acceptance check passed [receipt]
Compared · B failed the same requirement: [decision-relevant reason]
Could change this · [specific future observation and reversal]
```

For direct work the second line is instead: [asserted]

```text
Direct answer · no unavailable decision-changing check was worth its cost.
```

The sceptic sees what source was checked, what artefact ran and what alternative actually lost. A
single model with tools can structurally offer the same things; an ungrounded single-pass token
answer cannot offer evidence acquired after the prompt and bound to the delivered claim. The
commercial comparison is therefore empirical, not a novelty claim. [asserted]

## 5. Decide before spending

ADR-0067 already sets one Owner and the smallest evidence-grounded composition. ADR-0081 already
requires a second structural anchor for full or protected conclusions and permits a valid minimal
decision to proceed on one. The brief's named ADR-0077 fusion owner is absent from the tracked tree;
this specification does not recreate it or pretend that its ownership has landed. [measured]
[asserted]

Before generation, the Owner freezes the material claim or acceptance contract, consequence tier,
available anchors, hard budget and whether a possible new observation could change the answer. It
then records exactly one response mode: [asserted]

| Mode | Pre-spend admission | User-facing behaviour |
|---|---|---|
| `direct` | No high-consequence gate requires acquisition, and either the Owner already has the relevant sources/tools or no available different observation could change the scoped answer within budget. [asserted] | Answer directly; say no extra check was warranted. [asserted] |
| `checked` | One available source or executable observation could change a material claim and its conservative value exceeds its acquisition cost. [asserted] | Acquire that one observation, bind its receipt, then answer. [asserted] |
| `converged` | ADR-0081 requires another structural anchor, or a future accepted fusion owner admits one or more sealed readings. Optional convergence remains unavailable until that owner lands. [measured] [asserted] | Use the smallest admitted composition, one Owner and one candidate; show checks, not the organisation. [asserted] |

Difficulty, importance-sounding language, user enthusiasm, role availability and remaining prepaid
quota do not admit another member. The mode is fixed before outcome inspection; it cannot be changed
after a disappointing direct answer merely to manufacture evidence of effort. [asserted]

The current human-labelled beta is unestimated, so the honest operational default remains one Owner
and one candidate. `routing_orchestration_enabled` remains false, and this document changes no gate.
[measured]

## 6. Measuring perceived quality

Correctness and preference are different outcomes. A checked answer can be more correct and less
liked; a polished answer can be preferred and false. `EXP-128` records both and never lets preference
erase a correctness loss. [asserted]

### Verified-free reservation; proposed entry is unwritten

The following is the exact proposed register entry. It is **unwritten and not pre-registered** because
this dispatch was forbidden to edit the experiment register. No arm may run and no result may be
inspected until the register owner writes the entry unchanged or records a superseding protocol.
[measured] [asserted]

### EXP-128 · Do users prefer the evidence-bearing primary response to the strongest single-model answer on the same prompt? `BLOCKED: register entry, accepted fusion owner, frozen banks, comparator qualification, implemented policy and consented blinded raters`

**Decides:** whether this answer-quality policy may become the default for the frozen prompt mixture
and be described as visibly better than the strongest same-budget single-model response. Failure to
confirm retains one strong Owner with the same tools as the default. EXP-80 continues to own its
coding joint-success question; EXP-128 owns perceived quality of the primary response. [asserted]

**Precondition:** before viewing qualification outcomes, enumerate and freeze every one-Owner
configuration available through the existing permitted local or subscription harness inventory that
needs no new credential or metered call and fits the confirmatory ceiling. Bind each exact model,
harness, instruction, tool and source revision in its own configuration digest, then bind the
complete set in a candidate-set manifest digest. Freeze a disjoint 40-prompt qualification set, ten
prompts per confirmatory stratum.
Every task-native correctness rubric has a positive maximum;
divide its raw score by that maximum to place correctness in `[0, 1]`. A missing response or timeout
scores `0`; a refusal receives the score its rubric fixed before execution. Each rubric also freezes
its critical-error conditions. A fabricated citation or execution receipt is always critical; any
other critical factual error is a false material claim that the rubric says could change the user's
action in a safety, security, privacy, financial, credential, publication or irreversible domain.
Where no deterministic oracle decides that label, at least two of three blinded correctness judges
must agree. Disqualify a candidate with any critical qualification error; among the remainder select
the highest mean normalised correctness, breaking ties by fewer unsupported material claims, lower
mean tokens, lower mean wall time, then lexicographically smaller configuration digest. If none
remains, do not run. Then freeze 220 unseen, real-world prompts from consented target users or
permissively licensed sources, split equally across simple/direct questions, source-dependent
synthesis, executable work and consequential recommendations. Freeze the rubrics; presentation;
seed `1280087`; and equal per-prompt token/tool/spend ceilings. Record consent or licence, provenance
and retrieval date for every prompt, and verify no overlap with qualification. Collect three
consented target-user ratings per primary pair and use a separate three-judge blinded correctness
panel where no deterministic oracle exists. A preference rater sees only one pair. Freeze a 14-day
response window for every rating and correctness verdict; any missing correctness verdict makes the
run inconclusive and is not replaced. Any external spend requires the principal's approval before
launch. [asserted]

**Procedure:** on every prompt, run arm A as the frozen single model with all allowed retrieval,
browser, execution and self-checking tools but no delegation. Run arm B as the frozen answer-quality
policy, which may choose `direct`, `checked` or `converged` only through section 5. Neither arm sees
the other. Randomise execution and presentation order with seed `1280087`; remove product, model,
harness, role and process labels, but retain real user-visible citations and execution receipts
because they are part of the treatment. Each of three target-user raters makes a forced choice about
which response they would rather use: A, B or `no material difference`. A prompt is a primary B
success only when at least two raters choose B; every other complete pattern is non-B. Seal
deterministic or blinded domain correctness before unblinding. Preserve every refusal, timeout,
missing response, quarantine and missing verdict; replace none. [asserted]

**Measures:** the primary measure is the number of 220 prompt-level material-preference majorities
for B. Secondary measures are A majorities, `no material difference` and split patterns;
task-native correctness and paired B-minus-A difference; unsupported material claims, invalid
citations and false execution receipts; direct/check/converged decisions by stratum; total
input/output/cache tokens, tool calls, wall time, external spend and human review minutes; and every
adverse or missing outcome. Report prompt as the clustered unit and all four strata separately. For
correctness and cost bounds, use 20,000 paired bootstrap resamples with seed `1280087`, drawing 55
prompts with replacement within each frozen stratum on every replicate. Sort the 20,000 replicate
statistics and define the non-interpolated empirical quantile as
`Q(p) = x_(ceil(p × 20,000))` in one-indexed ascending order. A one-sided 95% lower bound is
`Q(0.05)` and an upper bound is `Q(0.95)`. Each cost statistic is the ratio of mean per-prompt arm-B
to arm-A totals. Missing arm-B cost makes its ratio `+infinity` and therefore loses; missing arm-A
cost or a non-positive arm-A denominator makes the run inconclusive. Missing cost is never imputed as
zero. [asserted]

**Stopping rule:** stop after exactly 220 terminal prompt pairs and their frozen ratings, or 120
calendar days after the first confirmatory arm starts, whichever comes first. Do not peek, replace a
prompt or stop for efficacy. A prompt is terminal when its three assigned preference ratings are
sealed or their frozen 14-day windows expire; a missing rating is non-B and is not replaced. A
missing B response, including both responses missing, is also non-B; an A-missing, B-present pair is
rated normally. Confirm visible preference only if B wins at least 123 of 220
prompt-level majorities, the one-sided lower correctness bound `Q(0.05)` is at least `-0.05`, no
arm-B critical factual error, fabricated citation or fabricated execution receipt occurs, at least
50 of 55 simple prompts route direct, and the upper cost bounds `Q(0.95)` are at most `1.25×` for
tokens and `2.00×` for wall time. Under a binomial null of `p = 0.5`, 123 wins has a one-sided tail
of `0.04583`; `n = 220` gives `0.90398` power at `p = 0.60`. [algebra] Lose if B wins at most 110
majorities, the one-sided upper correctness bound `Q(0.95)` is below `-0.05`, any arm-B critical factual error,
fabricated citation or fabricated execution receipt occurs, or either upper cost bound exceeds its
ceiling. Counts 111–122, an administrative stop or any other unmet confirmatory condition are
`inconclusive`; operationally they also retain A as the default. Opposing confirm and loss conditions
resolve to loss. [asserted]

The committed stdlib producer for the two binomial figures is: [algebra]

```powershell
python -c "from math import comb; n=220; k=123; print(sum(comb(n,i)*.5**n for i in range(k,n+1))); print(sum(comb(n,i)*.6**i*.4**(n-i) for i in range(k,n+1)))"
```

**Largest plausible effect:** the B material-preference success rate is bounded by `[0, 1]`, and the
paired correctness difference by `[-1, +1]`; the policy could win none or all of the prompt-level
judgements. EXP-128 can activate or kill the default and visible-quality claim for this frozen
mixture. It cannot block the one-response surface, the direct single-Owner path, evidence receipts,
or existing orchestration substrates. [algebra] [asserted]

### If correctness and preference disagree

| Result | Product decision |
|---|---|
| Preferred and correctness non-inferior | Activate only for the frozen covered mixture if every cost and safety condition also passes. [asserted] |
| More correct but less preferred | Record the perceived-quality claim as lost. Retain required checks for consequential work, use the direct Owner elsewhere, simplify presentation, and test the new surface in a new registered experiment. [asserted] |
| Preferred but less correct | Reject the policy. Preference never licenses a correctness regression. [asserted] |
| Neither preferred nor more correct, or inconclusive | Keep one excellent model with the same tools as the ordinary default. [asserted] |

## 7. Evidence against: one excellent model may be the honest product

The strongest objection is that the entire convergence layer is avoidable. Current frontier product
surfaces expose browsing, tools and execution to a one-Owner configuration that can supply external
checks; giving one Owner the same sources, browser and budget can preserve context that delegation
loses. Every visible feature in section 4 can be produced by that one Owner. [cited: OpenAI, *ChatGPT Work and
Codex*, and Anthropic, *How Claude Code works*, retrieved 2026-08-22] [asserted]

The objection has direct support: [asserted]

- EXP-16's single-agent arm won 9 of 12 substituted blind model-grader best calls, while the Owner
  meeting won 2 of 12 at `4.8×` the tokens and `3.7×` the wall time. The experiment's registered
  human ground truth was not obtained, so this is evidence about independent model readers, not the
  maintainer's preference. [measured]
- Ao, Gao and Simchi-Levi prove weak dominance by an ideal central decision-maker when delegated
  agents receive no new exogenous signal; the theorem does not establish that one bounded model can
  realise that ideal centre. [cited: arXiv:2603.26993, retrieved 2026-08-22]
- Kim et al. found every tested multi-agent architecture degraded on SWE-bench Verified in their
  matched 260-configuration study, while effects in other domains varied. [cited:
  doi:10.1038/s42256-026-01268-y, retrieved 2026-08-22]
- Jwalapuram et al. found generic multi-agent systems losing to a strong single-agent comparator;
  their positive specialist result used a deliberately separable synthetic task. [cited:
  arXiv:2606.13003, retrieved 2026-08-22]
- Kraidia et al. and Wynn, Satija and Hadfield report settings in which debate degrades accuracy;
  neither supports a universal anti-debate claim. [cited: doi:10.1038/s41598-026-42705-7 and
  arXiv:2509.05396, retrieved 2026-08-22]
- Zhou demonstrates that a judge can become much easier to satisfy while hidden accuracy does not
  improve. An impressive receipt produced by the wrong judge is worse than no receipt because it
  manufactures trust. [cited: arXiv:2607.05904v1, retrieved 2026-08-22]

Frontier products already expose search, tools and execution to one Owner, and the inspected product
bar contains no evidence that adding a committee improves the answer a person prefers under an equal
budget. [cited] [measured]

This specification concedes the objection unless `EXP-128` defeats it. One excellent Owner is the
default; extra readers receive no credit for identity or agreement; the user sees checks rather than
headcount; and failure or ambiguity leaves the simpler product in place. [asserted]

## 8. Reuse, never rebuild

| Existing component | Answer-quality responsibility |
|---|---|
| `scripts/dispatch.py` | Runs an admitted acquisition or execution; it remains the only outer orchestrator. [asserted] |
| `coordination.py` | Owns path claims and collision refusal. [measured] |
| `recall.py` | Supplies bounded verbatim context; it does not become evidence of truth. [measured] |
| `work_items.py` | Carries the bounded check and its terminal adverse state. [asserted] |
| `routing.py` | Continues to own candidate exposure and beta refusal, not response decoration. [measured] |
| `budget.py` | Refuses work outside the frozen token, time and spend ceiling and records missing usage as adverse. [asserted] |
| `instructions.py` | Carries the response contract to the selected harness. [asserted] |
| `events.py` | Remains the single append-only writer for source, execution, decision and delivery references. [measured] |

ADR-0067 owns one-Owner composition, ADR-0081 owns the high-consequence anchor gate, and the existing
chat/delivery specifications own conversation and completion. Fusion and exposure need one accepted
owner; the brief's ADR-0077 owner is absent from the tracked tree. If implementation needs another
field, extend the owning record and its validator in the same commit; do not add another coordinator,
writer or response state store. [measured] [asserted]

## 9. Checks required with implementation

No product implementation ships in this documentation commit. The later implementation commit must
leave the smallest runnable checks that prove: [measured] [asserted]

1. a simple prompt chooses `direct` before dispatch and renders no invented check; [asserted]
2. every visible source or run receipt resolves to an existing immutable event/artefact and the
   displayed claim is the one it checked; [asserted]
3. a role count, family label, vote, confidence or transcript can never enter `Checked`; [asserted]
4. only one Owner emits the primary response and every material refusal or disagreement remains
   reachable on demand; [asserted]
5. token, latency and adverse-outcome fields never render missing as zero; and [asserted]
6. no second orchestration, writer or CLI path bypasses the existing owners. [asserted]

The killing checks are simpler: a source badge that cannot resolve, an execution receipt for an
artefact that did not run, a second acceptance-eligible candidate outside the accepted exposure
ceiling, or a high-consequence action bypassing ADR-0081 invalidates the implementation immediately.
[asserted]

## 10. Plain answer and delta

The plain answer is one excellent model with good tools. The only defensible addition is to make
decision-changing contact with the world visible at the claim it supports, while refusing to spend
on contact that cannot change the answer. [asserted]

The delta is therefore not a committee. It is one useful answer with source-bound claims, executed
results, a real losing alternative when one was actually tested, and a specific falsifier; everything
else stays behind the answer or is cut as theatre. Whether people prefer that answer remains
unmeasured until the unwritten `EXP-128` entry is registered and run. [asserted]

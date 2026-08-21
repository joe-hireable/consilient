# QA automation, synthetic users, and the anchor problem

**Answers the three gating questions in Q32 (`../00-context/open-questions.md`). No design
follows from it, and none is proposed here — Q32 forbids that until these are answered.**
[asserted]

**Status:** one-session literature pass, 20 August 2026. Fourteen sources were read at
abstract or listing depth via arXiv; **none was read in full.** [measured] That is a
materially thinner evidence base than
`human-success-and-the-human-side-of-beta.md` (65 sources, 44 in full), and every citation
below is therefore `[ABS]` in the bibliography sense and **may not be promoted to a `[cited]`
line in an ADR until fetched and read.** [asserted] Nothing in this file is a Consilient
measurement except where it quotes EXP-01. [asserted]

---

## Verdict

1. **Q32.1 — yes, but narrowly.** A synthetic user introduces a genuinely different class of
   facts, and that class is the **input sequence and the implicit oracle**, never the
   expectation. [cited] Where the synthetic user's expectation is generated from the same
   repository by the same model family, it is not a different class and ADR-0010 cuts it.
   [asserted] EXP-01's confirmed escapes contain one instance of exactly the defect class a
   driving agent reaches and a unit suite cannot. [measured]

2. **Q32.2 — no, and that is worse news, not better.** Generated-test acceptance is not β
   renamed. It is a mechanism that drives β toward 1 in a region where the check *cannot
   fail*, by construction rather than by bad luck. [algebra] The distinguishing fact is
   available cheaply: every strong fault-detection number in the literature comes from the
   **bug-known** condition, and the bug-unknown condition yields either proxies that
   anchoring corrupts or low absolute numbers. [asserted] Coverage will not show this and
   mutation score shows only half of it. [cited]

3. **Q32.3 — cannot be answered yet, and the blocker is already named.** The three entry
   points for the human verdict are enumerable with confidence; the price of each is
   unmeasured. [asserted] Every route to answering Q32.2 or Q32.3 runs through the same
   artefact — a fixed, human-labelled bad-artefact holdout that the generator never saw —
   which EXP-13 already requires and which does not exist. [measured] It is the cheapest
   thing in this note and everything else waits on it. [asserted]

---

## 1. Q32.1 — what different class of facts does a synthetic user introduce?

ADR-0010 asks the structure to name its new evidence. The right axis for naming it is not the
technique (property-based, metamorphic, record-and-replay, model-based) but the **anchor** —
where the expected value comes from. Canedo supplies the vocabulary directly:
*specification-anchored* expectations take their value from outside the code;
*state-anchored* expectations take it from the code under test. [cited]

Sorted by anchor, the available classes are:

| Anchor | Different class? | What it buys |
|---|---|---|
| The code itself (state-anchored) | **No** — same class as the generator | Nothing. Echo. |
| Implicit oracle: crash, hang, 5xx, memory error, dead affordance | **Yes** — supplied by the runtime, not by anyone's belief | Cheap, high-precision, narrow |
| Specification / documentation / requirements, authored independently of the code | **Yes** — if genuinely independent | The strongest class, and the rarest |
| Domain metamorphic relation between two executions | **Yes** — if the relation comes from the domain | Works without a per-input expectation |
| Independent reference implementation (differential) | **Yes** | On Canedo's system it killed *exactly* what specification anchoring killed [cited] |
| Real user traces | **Yes** | Not available pre-launch, which is the whole difficulty |

Against that table, a synthetic user contributes on two rows and not the others.

**What it genuinely adds — the input distribution.** Multi-step, stateful, cross-boundary
interaction sequences are a class of facts a unit suite does not contain. This is not a
theoretical point in this repository. EXP-01's two audit-confirmed β escapes, described
abstractly in `experiments/exp01/findings-exp01.md`, are (i) *a shipped feature losing a
user-visible affordance after reload, checks green*, and (ii) *shipped configuration
referencing non-existent resources that validation accepted*. [measured] The first is
structurally unreachable by a unit suite — the state that breaks it exists only after a
reload in a driven session — and structurally reachable by an agent driving the application.
n=2 confirmed escapes total, so this is an **existence proof for the defect class, not a
rate**. [asserted]

**What it genuinely adds — the implicit oracle.** The defect-finding results in the
synthetic-user literature come overwhelmingly from oracles the runtime supplies free.
PersonaTester triggered *100+ crashes and 11 functional bugs*; the ten-to-one ratio is the
finding, not the totals. [cited] Quality-assured fuzz-harness generation reports a 4.8%
false-positive rate with 29 of 42 bugs fixed upstream — high precision, because a sanitiser
trap is not an opinion. [cited]

**What it does not add — the expectation.** If the synthetic user's assertion about what
*should* have happened is written by the same model family from the same repository, it is
state-anchored and it is echo. This is sharper than an analogy: exposure-aware evaluation
measures that models reproduce buggy lines far more often than fixes, with bug-exposed
examples amplifying the tendency. [cited] Generator and test-writer share a prior, so
independence fails at the model level even before it fails at the anchor level. [asserted]

**Where the literature is silent.** Two absences matter more than any of the numbers above.

- The LLM-UI-agent testing literature measures **execution accuracy, not fault detection**.
  HxAgent reports 97.4% exact-match on MiniWoB++ and 83.8% on a 350-task web dataset — that
  is "can the agent carry out the described scenario", which is a prerequisite for testing and
  is not testing. [cited]
- The synthetic-user/persona literature validates **behavioural fidelity against human
  traces**, not defect discovery. PAARS reports personas improving performance while "a gap
  remains to human behaviour". [cited] Nothing found here measures whether synthetic users
  find the defects real users hit.

And the transfer question is open in the one field that has studied it longest: the
virtual-versus-physical study of driving systems finds critical shortcomings contributing to a
reality gap, with some configurations transferring and others not. [cited] A synthetic user is
a simulator of a user, and simulators have reality gaps.

**Answer to Q32.1.** Yes — the different class is *the input sequence plus the implicit
oracle*. It survives ADR-0010 only under a discipline that records, per check, which anchor
supplied its expectation, and treats state-anchored expectations as carrying no evidential
weight. [asserted]

---

## 2. Q32.2 — is generated-test acceptance simply β under another name?

**No. It is a distinct and more dangerous object, and conflating the two would hide it.**
[asserted]

β is `P(checks accept | artefact bad)` — an empirical rate over a population of bad
artefacts, with a distribution and an interval. The generated-check hazard is not a rate at
all in the region where it bites. Canedo states the identity plainly: *a test oracle that
obtains its expected value from the system it is judging cannot fail; if a fault moves
measurement and expectation together the comparison cancels exactly, and no generated input
will reveal it.* [cited] For the fault classes an anchored oracle covers, acceptance of a bad
artefact is **certain**, not probable. That is `[algebra]`: a cancellation identity, not a
measured frequency.

So the honest restatement is: **generated-test acceptance is a mechanism that creates a
degenerate region of β, where β = 1 by construction and the measurement is uninformative
because the instrument cannot register a failure.** [algebra] A β number computed over checks
containing such a region is not wrong so much as diluted — it averages a real error rate with
a structural blind spot, and reports a single number for both.

Three lines of evidence say this is not a hypothetical.

**(a) The industrial acceptance filter is agreement with current behaviour.** Meta's
TestGen-LLM admits a generated test if it builds, *passes reliably*, and increases coverage:
75% built, 57% passed reliably, 25% increased coverage, 73% of recommendations accepted by
engineers. [cited] "Passes reliably" means "passes on the code as it stands". The filter
therefore cannot distinguish *the test is wrong* from *the code is wrong*, and discards both
identically. [asserted] This is the state of the art, deployed at scale, with explicit
assurance claims — and its assurance is an assurance of non-disagreement with the present.

**(b) Prevalence is real, and re-anchoring recovers defects.** On an air-traffic-control
simulator — 12 property suites, 4 modules, 366 mutants — re-anchoring recovered 8 of 46
mutants, a state-anchoring debounce oracle cost 4 of 19, two ablated instances that sized
their comparison carried 11 of 12 recovered mutants, and rewriting oracles exposed 2 defects
deployment had not surfaced. [cited] n=1 system, single author, preprint three days old: this
is the load-bearing empirical citation of the section and it is thin. [asserted]

**(c) The dashboards do not show it.** Coverage is worthless here: a suite has been measured
at 100% coverage and 4% mutation score. [cited] Mutation score is better — it is in fact the
instrument that *detects* anchoring, as Canedo used it — but it is not sufficient, because
LLM-generated tests **significantly outperform** search-based and symbolic-execution tools on
mutation score while performing **worse than both on real fault detection**, on GitBug Java.
[cited] Mutation score is sensitive to anchoring and blind to misspecification: a suite can
kill every mutant of the wrong specification. [asserted]

**The clean discriminator.** Sorting the literature by whether the fault was known to the
test-writer separates it almost completely:

| Condition | Reported capability |
|---|---|
| **Bug-known** (issue text, bug report, or bug-relevant retrieval supplied) | 78.9% fail-to-pass on SWE-bench Verified [cited]; 43.6% F→P [cited]; 28% plausible bug-reproducing tests at Google [cited]; 33% on Defects4J [cited] |
| **Bug-unknown** (code and docs only) | Proxies that anchoring corrupts (coverage, mutation score), or worse-than-SBST real fault detection [cited] |

The synthesis is mine and is `[asserted]`: **a test written with knowledge of the fault is a
fault-localisation aid, not an oracle.** It confirms a diagnosis; it cannot license an
acceptance. The QA-automation opportunity in Q32 lives entirely in the bug-unknown column,
and that is the column where the numbers are proxies.

**The one class that escapes cleanly, and its price.** Specification-anchored generation is
the exception, and PBT-Bench isolates precisely the skill — *deriving a semantic invariant
from documentation, then constructing an input-generation strategy precise enough to make a
random search reveal the violation* — over 100 problems, 40 Python libraries, 365 semantic
bugs, with bug recall of 42.1%–83.4% under a PBT-guided prompt against 31.4%–76.7%
open-ended. [cited] Read carefully, that result is an argument for the anchor discipline
rather than against it: it works because the documentation is a class of facts distinct from
the code, and it presupposes documentation precise enough to yield an invariant. Most
repositories do not have that, and this one has not tested whether its own do. [asserted]

**Relation to EXP-13.** EXP-13 pre-registers the multi-generation form of this hazard —
whether the verifier's β rises across generations when the loop may modify its own suite,
measured against a fixed human-labelled holdout. Q32.2 is the **single-generation** form of
the same hazard, and EXP-13 has already identified the correct instrument. [asserted] The
instrument is the holdout, not the loop. Nothing about generated-check quality can be measured
without it, and it does not exist. That is the finding, and it is unglamorous.

---

## 3. Q32.3 — where does the human verdict enter a synthetic-user loop?

EXP-01 measured the constraint. Its label audit covered 15 of 128 flagged pairs and its
corrected estimate — jobboard-v2 β̂ ≈ 0.12, honest interval [0.02, 0.42] — is *audit-limited,
not history-limited*; its own next-step note records that "Joe spot-checking even 5 verdicts
would materially harden it". [measured] Separately, 33% of jobboard-v2 PRs merged with red CI:
on that repository the human **is** the acceptance gate and CI is advisory. [measured] And
`human-success-and-the-human-side-of-beta.md` establishes that the human verdict is itself an
error-prone test whose errors correlate with the checks it grades. [cited]

A synthetic-user loop does not consume one verdict budget; it consumes three, with different
economics.

1. **Oracle admission** — *is this generated property or assertion a true statement of
   intent?* One verdict per check, amortised across every future run of that check. Cheap per
   use, and it is the only point where a human can supply the specification anchor that
   section 2 says is scarce. [asserted]
2. **Failure triage** — *is this reported failure real?* One verdict per reported failure,
   recurring, scaling linearly with the size of the synthetic-user fleet. This is the entry
   point that can consume the whole budget. Rates that bear on its cost: 84.6% valid issues
   and 15.4% false positives for LLM-guided issue generation [cited]; 4.8% false positives
   for a quality-assured fuzz harness [cited]; and PersonaTester's 100+ crashes against 11
   functional bugs, an implied triage ratio near ten to one even where every report is a
   genuine crash [cited].
3. **Holdout labelling** — the fixed bank of known-bad artefacts that EXP-13 and any β
   measurement require. Near-one-off, and the scarcest of the three because it must be labelled
   by someone who is not the system. [asserted]

**The economic claim, stated so it can be killed.** Verdict budget should be spent where it
amortises — (1) and (3) — and entry point (2) must be made cheap by implicit oracles or it
consumes the other two. [asserted] This is falsifiable by measuring verdict-minutes per
confirmed defect at each entry point, and it has never been measured here or, as far as this
pass reached, anywhere. [asserted]

**What the field does instead, and why it does not help.** The field's answer to verdict
scarcity is to replace the human with more models: requirements-augmented oracle generation
reports a 3.91/5 oracle quality score, qualified or marginal in 82% of cases, with reliability
quantified through **simulated expert agreement** and a 98.8% cascade accuracy. [cited] Under
`CONSILIENCE.md` clause 2 a panel of simulated experts scoring a generated oracle is echo
unless those experts hold different facts, and the abstract does not establish what the 98.8%
is accuracy *against*. [asserted] It is named here so that nobody imports the number as a
solution to Q32.3.

**Answer to Q32.3.** Not answerable quantitatively today. The entry points are enumerable with
confidence; the price is unknown; and the blocking artefact is the same human-labelled holdout
that section 2 ends on. [asserted]

---

## 4. What would decide these — candidate experiments, not yet registered

Both carry stopping rules and a cannot-decide section fixed before any result exists, per
`AGENTS.md`. Neither is a design. Both block on the prerequisite below.

**Prerequisite (blocks EXP-13, and both candidates).** A fixed, human-labelled bad-artefact
holdout the generator never saw. EXP-01's two audit-confirmed escapes are the seed; the
enumerable path to more is already written in `experiments/exp01/findings-exp01.md`
(reference-based labels, full-pair audit). Build this before anything else in this note.
[asserted]

### Candidate A · The anchor audit

**Decides:** Q32.2 operationally — whether generated checks may ever be admitted as an
acceptance oracle, or only as a diagnostic aid.
**Procedure:** for each holdout fixture, generate checks under two conditions —
*bug-unknown* (code and documentation only) and *bug-known* (defect description supplied).
Classify each generated check's anchor as specification, implicit, metamorphic, reference, or
state. Measure kill rate on the known-bad artefact in each condition, and the proportion of
generated checks that are state-anchored.
**Measures:** kill rate by condition with Wilson 95% intervals; state-anchored fraction;
per-anchor kill rate.
**Stopping rule, fixed before collection:** stop at 40 fixtures or 200 generated checks,
whichever first. A bug-unknown kill rate more than **30 percentage points** below bug-known
means generated checks are a fault-localisation aid and may not be admitted as an acceptance
oracle. Within **10 points**, anchoring is not the dominant effect for that fixture family and
the restriction may be relaxed for it. Between 10 and 30, report insufficient data. Thresholds
are `[asserted]` and may not be moved after collection begins.
**Cannot decide:** whether the specification itself is right — a suite anchored to a wrong
specification passes this audit cleanly. Nothing about fixture families not used. Nothing about
the price of a human verdict. Nothing about synthetic users, which it does not involve.

### Candidate B · Verdict economics of a synthetic-user loop

**Decides:** Q32.3 — whether the verdict budget survives contact with a synthetic-user fleet
at solo-founder volume.
**Procedure:** run a driven-session loop against a fixture application with an implicit-oracle
gate only. Record wall-clock human verdict time at each of the three entry points, and whether
each verdict confirmed a defect.
**Measures:** verdict-minutes per confirmed defect, per entry point; triage precision;
defects per session-hour.
**Stopping rule, fixed before collection:** stop at 30 confirmed defects or 20 hours of human
verdict time, whichever first. If failure-triage verdict-minutes exceed oracle-admission plus
holdout-labelling by **3× or more**, an ungated synthetic-user loop is unaffordable here and
only implicit-oracle-gated reporting may proceed. Under **1×**, the affordability objection is
dead. Between, insufficient data. Thresholds `[asserted]`.
**Cannot decide:** whether the defects found are ones anyone would pay to fix — the value side
is out of scope. Nothing about β, which needs the holdout. Nothing about generalisation beyond
the fixture application, n=1.

---

## Evidence against this note

Reported as prominently as the support, per `AGENTS.md`.

- **The strongest single result cuts against section 2.** LLM-generated tests with
  retrieval-augmented context detected faults in **69%** of cases against **17.2%** for
  general-purpose human-written tests (Fisher's exact p<0.001, Cohen's h=1.10), with
  near-identical coverage — 84.8% vs 88.5% line, 75.2% vs 82.1% branch. [cited] If that
  replicates in the bug-unknown condition, the bug-known/bug-unknown discriminator that
  section 2 rests on is wrong. **My classification of it as bug-known is an inference** from
  the phrase "supplies bug-relevant context at generation time" and is `[asserted]`, not the
  authors' claim. n=29 real bugs, one model (Gemini 2.5 Flash), Python only.
- **The load-bearing anchoring citation is n=1.** Canedo is a single-author preprint from
  17 August 2026, one air-traffic-control simulator, 366 mutants, read at abstract depth only.
  The *identity* is `[algebra]` and safe; the *prevalence* in ordinary web repositories is
  entirely unestablished. [asserted]
- **Mutation-score gains are large and real.** Tracking-aware objectives report +37.66
  percentage points of mutation score, mutation-guided reinforcement learning +28.5% with 19.3%
  fewer tests, adversarial test-versus-mutant agents +8.56% fault detection over the best prior
  LLM methods. [cited] If mutation score tracks real fault detection more closely than Test
  Wars found, section 2's "the dashboards do not show it" weakens considerably.
- **Specification anchoring may be more available than section 2 implies.** PBT-Bench's top
  bug recall is 83.4% from documentation alone. [cited] If ordinary repository documentation
  supports invariant derivation at anything near that rate, the caution here is overpriced.
  Nobody has checked whether this repository's corpora do.
- **The synthetic-user case rests on one measured instance.** EXP-01 has two confirmed escapes;
  one of them is affordance-after-reload. A single instance cannot establish that this defect
  class is frequent enough to justify anything. [measured]
- **Absence of evidence, not evidence of absence.** No source found here measures whether
  synthetic users find the defects real users hit, and none measures verdict cost. Both
  conclusions that depend on those absences — the reality-gap caution and the verdict-economics
  claim — are `[asserted]`.
- **This pass is thin and was single-reader.** Fourteen sources, all at abstract or listing
  depth, one session, one reader, arXiv only. No ACM DL, no IEEE, no pre-2022 foundational
  literature on the oracle problem, metamorphic testing or property-based testing was read at
  source. [measured] By the standard `human-success-and-the-human-side-of-beta.md` set, this
  note is a first pass and should be re-run by a reader who did not see it. [asserted]
- **The Q19 caveat applies in full.** This synthesis was produced by the same model family as
  everything else in the project, reading abstracts summarised by another model. [asserted]

---

## Publication disposition

**None.** [asserted] This is an internal gating note. The anchoring identity is Canedo's, not
this project's; the bug-known/bug-unknown discriminator is a synthesis over abstracts and would
need the underlying papers read in full and a documented novelty search before it could be
claimed as a contribution (G2). [asserted] If Candidate A runs and the anchor discipline turns
out to move measured β on repository history, *that* is a publishable result and it belongs to
the β paper, not to a QA paper. [asserted]

---

## Sources added to the bibliography

All `[ABS]` — abstract or arXiv listing read directly, none read in full, 20 August 2026.
**None of these may be cited on an ADR `[cited]` line until fetched and read.**

| Status | Source |
|---|---|
| [ABS] | **Canedo, A.** *Oracles That Cannot Fail: Anchoring and the Expectation That Moves With the Fault.* arXiv:2608.17214 (17 Aug 2026). Specification- vs state-anchored expectations; ATC simulator, 12 property suites, 366 mutants; re-anchoring recovered 8/46 mutants. **The load-bearing citation for §2 and the source of the anchor vocabulary.** Single author, preprint, n=1 system. |
| [ABS] | **Alshahwan, N. et al.** *Automated Unit Test Improvement using Large Language Models at Meta.* arXiv:2402.09171 (14 Feb 2024). TestGen-LLM; 75% built, 57% passed reliably, 25% increased coverage; 11.5% of classes improved, 73% accepted. The acceptance filter requires passing on current code. |
| [ABS] | **Abdullin, A., Derakhshanfar, P. & Panichella, A.** *Test Wars: A Comparative Study of SBST, Symbolic Execution, and LLM-Based Approaches to Unit Test Generation.* arXiv:2501.10200 (17 Jan 2025). GitBug Java; LLM ahead on mutation score, behind on coverage **and on real fault detection**. The mutation-score/fault-detection dissociation. |
| [ABS] | **Vathana, et al.** *LLM vs. Human Unit Tests: Fault Detection on Real Python Bugs.* arXiv:2606.08588 (June 2026). 69% vs 17.2% fault detection, p<0.001, h=1.10; coverage near-identical. **The strongest counter-evidence in this note.** 29 BugsInPy bugs, Gemini 2.5 Flash, retrieval supplies bug-relevant context. |
| [ABS] | **Jing, L., Wang, X., Zhang, L. & Du, S. S.** *PBT-Bench: Benchmarking AI Agents on Property-Based Testing.* arXiv:2605.15229 (13 May 2026). 100 problems, 40 libraries, 365 semantic bugs; recall 42.1–83.4% (PBT-guided) vs 31.4–76.7% (open-ended). Isolates invariant-derivation-from-documentation. |
| [ABS] | **Al-Kaswan, A. et al.** *Model See, Model Do? Exposure-Aware Evaluation.* arXiv:2601.10496 (Jan 2026). ManySStuBs4J + Data Portraits over Stack-V2; 67% of examples had neither variant in training; models reproduce buggy lines far more often than fixes. Shared-prior evidence. |
| [ABS] | **Yu, S., Ling, Y., Fang, C., Chen, Z. & Chen, C.** *Towards Automated Crowdsourced Testing via Personified-LLM.* arXiv:2603.24160, FSE 2026. PersonaTester; 100+ crashes, 11 functional bugs; 117.86–126.23% over baseline. No false-positive rate in the abstract. |
| [ABS] | **Sheng, et al.** *Quality-Assured Fuzz Harness Generation.* arXiv:2605.21824 (May 2026). 4.8% false-positive rate; 29 of 42 bugs fixed upstream. Implicit-oracle precision. |
| [ABS] | **Nguyen, T. et al.** *HxAgent: Iterative Agent Planning for End-to-End Web Application Testing.* arXiv:2608.15491 (15 Aug 2026). 97.4% exact-match MiniWoB++; 83.8%/91.8% on 350 web tasks. **Measures execution accuracy, not fault detection.** |
| [ABS] | **Mansour, et al.** *PAARS: Persona Aligned Agentic Retail Shoppers.* arXiv:2503.24228 (Mar 2025). Personas improve fidelity; "a gap remains to human behaviour". |
| [ABS] | **Stocco, A., Pulfer, B. & Tonella, P.** *Mind the Gap! A Study on the Transferability of Virtual vs Physical-world Testing of Autonomous Driving Systems.* arXiv:2112.11255. Reality gap between simulator and physical twin; some configurations transfer, others do not. |
| [ABS] | **Wang, F. et al.** *Requirements-Augmented Generation for Trustworthy Acceptance Testing of LLM-Based Software.* arXiv:2608.12970 (13 Aug 2026). REAG; 3.91/5 oracle quality, 82% qualified or marginal; 98.8% cascade accuracy via **simulated expert agreement**. Named here as the echo hazard, not as a solution. |
| [ABS] | **Wang, G., Xu, Q., Briand, L. & Liu, K.** *Mutation-Guided Unit Test Generation with a Large Language Model.* arXiv:2506.02954 (June 2025). A suite at 100% coverage and 4% mutation score. |
| [ABS] | **Bug-known reproduction cluster**, cited only for the discriminator in §2: Tan et al. arXiv:2607.19843 (78.9% F→P, SWE-bench Verified); Khatib et al. *AssertFlip* arXiv:2507.17542 (43.6% F→P); Cheng et al. arXiv:2502.01821 (28% plausible BRTs at Google); Kang et al. arXiv:2311.04532 (33% on Defects4J). |

**Cross-references.** `experiment-register.md` EXP-01, EXP-13 · `../decisions/index.md`
ADR-0002, ADR-0010, ADR-0012, ADR-0018 · `human-success-and-the-human-side-of-beta.md` §1 ·
`../00-context/open-questions.md` Q19, Q24, Q32.

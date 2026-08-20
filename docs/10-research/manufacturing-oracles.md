# Manufacturing oracles: what works without a human writing the expected output

**Intended location:** `docs/10-research/manufactured-oracles.md`
**Status:** survey and pre-registration. No Consilience measurement of any technique below
exists yet. [asserted]
**Date:** 20 August 2026.

---

## 0. Verification status — read this before quoting any number below

The repository rule is that no `[SNIP]` or `[2ND]` source may be cited in an ADR's
`[cited]` line or any public claim (`bibliography.md`). This note was written under a
degraded research budget: the session's web-search allowance was already exhausted before
this workstream started, and the arXiv and Semantic Scholar APIs returned HTTP 429
throughout. **Thirteen sources were fetched and read in full on 20 August 2026** and carry
`[cited]`. Everything else that I could name from memory — Csmith's headline bug count, the
EMI/Orion result, Knight–Leveson on correlated N-version failures, Just et al. on
mutant/real-fault coupling, Polikarpova et al. on Daikon-inferred versus programmer-written
contracts, the Quviq AUTOSAR result, and every published neural-oracle precision figure —
**is recorded as `[asserted]` and listed in §11 as a verification queue.** Those leads are
almost certainly real. They are not evidence until fetched.

This matters more than usual here, because the whole question is "which oracles are cheap
and which are folklore", and folklore is exactly what unverified recall produces.

**Sources fetched in full, 20 Aug 2026 — promote to `[FULL]` in `bibliography.md`:**
SWE-Bench+ (arXiv:2410.06992) · OSS-Fuzz README · Daikon project page · Daikon manual
(*Enhancing Daikon output*) · Csmith README · Clang AddressSanitizer docs · Clang
ThreadSanitizer docs · Diffy README (opendiffy/diffy) · GitHub Scientist README ·
GraphicsFuzz README · Hypothesis tutorial · pitest.org · Crossref metadata for Chen et al.,
*Metamorphic Testing*, ACM Computing Surveys 2018, DOI 10.1145/3143561 (metadata and partial
abstract only — `[ABS]`).

---

## 1. Why this question is the load-bearing one

β is defined in `src/consilience/beta.py` as the rate at which the automated verifier
accepts an artefact **the human rejected**. The human is the reference oracle, `MIN_REJECTIONS`
is 30, and EXP-01's first pass produced β̂ ≈ 0.12 with a 95% interval of [0.02, 0.42] — an
interval the register records as *audit-limited, not history-limited*. [measured] The
instrument is starved of labels, and the label supply is the maintainer's own attention.

Manufacturing an oracle attacks that on two fronts at once:

1. **It lowers β** by adding a check whose blind spots differ from the test suite's.
2. **It supplies labels.** An oracle that fires *downstream of acceptance* converts a class
   of would-be human rejections into machine-detected false accepts, without adding human
   load. That is the scarce quantity in EXP-01. [algebra]

The second is the more valuable and the less obvious, and §8 states its limit precisely.

That a test-suite oracle really does accept bad artefacts at material rates is now a
measured fact of the field, not a conjecture: on SWE-bench, 32.67% of successful patches
involved solution leakage and **31.08% of passed patches were suspicious because the test
cases were too weak**; correcting for both dropped SWE-Agent+GPT-4 from 12.47% to 3.97%.
[cited] (SWE-Bench+, arXiv:2410.06992, read 20 Aug 2026.) That is a β-shaped result on the
benchmark the whole coding-agent field grades itself against.

---

## 2. The ordering principle

The ranking in this note is not a taste judgement. It falls out of `CONSILIENCE.md` clause 2.

> An oracle is worth adding in proportion to how **exogenous** its evidence is to the test
> suite it backstops.

`ADR-0012` establishes the algebra: composite β is the product of per-check rates *only*
under conditional independence, and because dependence is certainly present, the product is
a **lower bound** — it fails in the dangerous direction. [algebra] So the useful axis is not
"how many checks" but "how correlated is check *n+1* with checks *1..n*".

Ordered by exogeneity, most different to least:

| Rank | Evidence source | Different class of facts? |
|---|---|---|
| 1 | Real production traffic | Yes — the world, not the program |
| 2 | A second implementation (including *the previous revision of this repo*) | Yes — another program's behaviour |
| 3 | Runtime instrumentation (sanitizers, crash, resource limits) | Yes — machine-level facts the assertions never observe |
| 4 | New inputs to the same program (metamorphic, property-based) | Partly — same program, different sample |
| 5 | Properties inferred *from* the program (invariant mining, LLM assertion inference) | **No — echo** |

Rank 5 is the one that looks most like free automation and is worth least. It is the same
induction restated, which is precisely what `CONSILIENCE.md` names as echo.

---

## 3. The survey table

"Cannot catch" means *structurally* cannot — the blind spot is a property of the mechanism,
not a matter of effort. "FP burden" reports what is *measured*; "unmeasured" is the honest
entry almost everywhere and is itself a finding.

| Technique | Catches | Structurally cannot catch | Measured FP burden | Human must author |
|---|---|---|---|---|
| **Differential vs. a second implementation** | Any divergence between two independent implementations on the same input | Faults **common to both** implementations — the oracle *is* disagreement, so agreement is the blind spot. Correlated failure in N-version programming is the classical result here [asserted] | Unmeasured in general. Nondeterminism is the FP source | Nothing per property. Requires a second implementation to exist |
| **Differential vs. the previous revision** (same repo, old commit vs new) | Unintended behaviour change: silent regressions, scope creep, deletion-avoidance, changed error paths | The *intended* change (by definition — every real diff produces true divergences that need adjudicating), and any bug present in both revisions | Unmeasured here; **Diffy measures it in band** by construction (see below) | Nothing per property. Needs a callable boundary and input capture |
| **Record–replay against production traffic** | Divergence on inputs real users actually sent — the most exogenous class in this survey | Anything on traffic that never occurred; and it cannot *adjudicate* — it says "different", never "wrong" | Diffy's primary/secondary noise floor is a live measurement of its own FP rate [cited]; Scientist requires hand-written `ignore` blocks [cited] | Nothing per property. Requires production traffic, side-effect isolation, PII handling |
| **Crash / sanitizer oracles** | ASan: out-of-bounds heap/stack/globals, use-after-free/return/scope, double-free, invalid free, leaks. TSan: data races. Plus panics, unhandled exceptions, OOM, timeout [cited] | **Every silent wrong answer.** No listed class is a logic error. Nothing that returns cleanly | ASan: "not expected to produce false positives"; container-overflow detection "prone to false positives" [cited]. TSan: FPs when not all code is instrumented, and from ignorelists/attributes [cited] | Nothing. A compiler flag |
| **Metamorphic relations** | Faults that break a stated relation between a source and follow-up execution (idempotence, permutation invariance, commutativity, semantics-preserving transformation) | Faults that **preserve the chosen relation** — if `f` is wrong but `R(f(x), f(t(x)))` still holds, the technique is silent. Finding the relation is the hard part | Unmeasured. In principle near-zero when the relation is genuinely necessary; each mis-stated relation is a permanent FP generator | **Yes — one relation per property, forever.** This is the technique's real cost |
| **Property-based testing / property inference** | Faults violating a stated property over generated inputs | Faults not expressible as a property over the tested unit; anything requiring integration state | Unmeasured. Flaky-shrink noise on stateful code | **Yes.** "Property-based testing is a powerful *addition* to unit testing. It is not always a replacement." [cited] |
| **Round-trip / self-consistency** | Encode↔decode, serialise↔deserialise, parse↔print, migrate↔rollback mismatches | **Compensating faults**: if `decode∘encode = id` while both use the same wrong charset, the round trip passes. Symmetric wrongness is invisible | Unmeasured; anecdotally low | Yes, but ~one line each, and the pairs are mechanically discoverable by name. "tend to be both powerful and easy to write" [cited] |
| **Invariant mining (Daikon and successors)** | Likely invariants over observed executions — ranges, orderings, nullity, linear relations [cited] | Any defect **present in the runs it mined from** — that behaviour is canonised as an invariant. It reports what *was* true, never what *should* be | No published rate on either fetched page. The burden is visible in the architecture: five named filters (Derived­Parameter, Obvious, Parent, Simplify, Unjustified), a `confidence_limit` defaulting to 0.99, and a theorem-prover redundancy pass [cited] | Nothing to author — but **everything to triage**, and the triage is the cost |
| **Assertion inference (neural / LLM)** | Assertions that look plausible for the code under test | Any defect the model **shares with the code** — which, when the code was written by the same model family, is the class of interest | **Unmeasured in this note.** Published precision figures I recall could not be fetched; see §11 | Nothing to author, everything to trust |
| **Mutation testing** *(not an oracle — the meter for oracles)* | Weakness in the *checks*: a surviving mutant is a fault your suite would not have detected | Nothing about the artefact. It grades the verifier, not the diff | n/a — a surviving mutant may be equivalent, which is the classical undecidable-equivalence cost | Nothing |

---

## 4. Per-technique notes worth having in prose

**Differential testing is the mechanism behind the field's flagship results.** Csmith states
its own design in one line: "a random generator of C programs. It's primary purpose is to
find compiler bugs with random programs, **using differential testing as the test oracle**."
[cited] GraphicsFuzz is the metamorphic twin — "randomized metamorphic testing" applying
semantics-preserving transformations to shaders, with defects found across Apple, ARM,
Qualcomm, Nvidia, Intel, AMD and Imagination. [cited] Both work because a *second thing that
should agree* exists for free: another compiler, or the untransformed shader.

**The free second implementation for an application repo is its own previous revision.** Git
supplies it at zero cost. This is what Scientist does in-process — wrap `use` around the old
behaviour, `try` around the new, run both, publish mismatches [cited] — and what Diffy does
across service instances. Nobody has to author an expected output; the expected output is
*what the code did yesterday*. For an agentic harness, this targets exactly the failure the
repo has already observed: EXP-05's OpenCode artefact passed its functional tests while
adding an unrequested duplicate test file [measured], and `unnecessary-scope-and-fanout.md`
records deletion-avoidance where passing patches retained targeted code behind a guard
[cited]. A test suite is silent on both. A behaviour diff against the parent commit is not.

**Diffy is the only technique here that measures its own false-alarm rate in band.** Three
instances: candidate, primary, secondary — where primary and secondary both run known-good
code. "Since both run known-good code, you should expect them to agree. Where they don't,
your service is exhibiting non-deterministic behavior — Diffy treats that signal as noise",
and it "measures how often primary and secondary disagree with each other vs. how often
primary and candidate disagree." [cited] That is a live α-estimate built into the
instrument. It is the single design idea in this survey most worth stealing, and it is
directly the shape of what this project is trying to do for β.

**Sanitizers are the cheapest oracle in existence and the least applicable here.** Zero
authoring, a compiler flag, 2× slowdown for ASan, and the tool's authors state it is "not
expected to produce false positives". [cited] TSan costs 5–15× time and 5–10× memory and has
documented FP conditions. [cited] OSS-Fuzz — fuzzing plus sanitizers at Google scale — has
"helped identify and fix over 13,000 vulnerabilities and 50,000 bugs across 1,000 projects"
[cited]. **But every class ASan and TSan list is memory- or concurrency-shaped, and neither
exists for Python or TypeScript.** The honest managed-language analogue is much thinner:
uncaught exception, `faulthandler`, `-X dev`, `PYTHONWARNINGS=error`, `pytest -W error`,
Node `--throw-deprecation`, strict mode, process exit code, wall-clock timeout, and a memory
ceiling. That set is worth turning on — it is rung 3 of the ladder, stdlib and runtime flags,
zero code — but it will not carry a β programme on its own.

**Invariant mining is the technique to be most sceptical of, and the scepticism is cheap to
justify.** Daikon has been available since 1999, detects properties in C, C++, C#, Eiffel,
F#, Java, Perl and Visual Basic [cited], and is close to absent from ordinary industrial
practice twenty-seven years on. It reports "**likely** program invariants" — "properties
that were true over the observed executions" [cited]. Its manual documents five output
filters, a statistical `confidence_limit` defaulting to 0.99, and a Simplify-based
`--suppress_redundant` pass [cited]. A tool that ships five filters and a significance
threshold is telling you what its raw output looks like. Neither fetched page publishes a
precision figure. And the structural blind spot is fatal for this use case: mine invariants
from executions of the current code and **any defect already present becomes an invariant**.
It reports what *was* true, never what *should be*.

**Neural assertion inference is the one to refuse.** It fails `CONSILIENCE.md` clause 2
twice: the assertion is an induction over the same class of facts as the code, and if it
then feeds β, β becomes a measure of the model's agreement with itself. `ADR-0012`'s algebra
makes this concrete — dependence between checks makes the product a lower bound that fails
in the dangerous direction, and a model-authored oracle over model-authored code is the
maximally dependent case. [algebra] I could not fetch any published precision figure for
neural oracle generation this session and will not quote one from memory (§11).

**Mutation testing is not an oracle and is the most useful thing on this list anyway.**
Coverage "does not check that your tests are actually able to detect faults in the executed
code"; a mutant is "killed" if tests fail and "lived" if they pass; mutation testing is
"the gold standard against which all other types of coverage are measured". [cited] That is
a self-description by the tool's own site — an interested party — and mutation score is
**not** 1−β. But it is a label-free measurement of verifier strength, and this project's
entire thesis is measuring verifier strength. It should be running before any new oracle
class is added, because it says *which* existing check is the weak one.

---

## 5. Ranking for a solo-maintainer coding harness

Criteria, in order: (R1) does it yield false-accept labels for β; (R2) is its evidence a
different class of facts; (R3) authoring cost — zero, once, or forever; (R4) false-alarm
burden and whether it is measurable in band; (R5) does it apply to ordinary application code
rather than compilers.

**Adopt now — cheap, zero per-property authoring:**

1. **Differential against the previous revision.** Best R1–R3 of anything here. Yields β
   labels directly (a diff the suite accepted that changed behaviour outside the intended
   blast radius). Cost is a callable boundary and captured inputs, not invention. Steal
   Diffy's noise floor by running the *parent revision against itself* to establish the
   nondeterminism baseline before reading any candidate divergence.
2. **Mutation testing as the verifier meter.** Not an oracle; the diagnostic that says which
   check is weak. Zero authoring, cost is CPU, and the RTX 5090 rig / local-compute principle
   (AGENTS.md 8) makes CPU the cheapest input this project has.
3. **The runtime-flag crash oracle set.** One config change. Thin in Python/TS, but free.

**Adopt conditionally:**

4. **Round-trip / self-consistency properties** on encode/decode-shaped pairs. One line each,
   and the pairs are discoverable by name-matching. Named blind spot: compensating faults.
5. **Record–replay against production traffic** — ranked #1 on evidence class and unavailable
   without a live service. If the maintainer has one, it outranks everything above. If not,
   it is not a fallback, it is absent.
6. **Generic metamorphic relations only** — idempotence, permutation invariance of set-like
   inputs, commutativity of independent operations, monotonicity. The general technique's cost
   is *inventing the relation*, which a solo maintainer cannot pay per function. The generic
   subset is affordable; the technique is not.

**Do not build on:**

7. **Invariant mining.** Hypothesis generator at best, and only ever mined from a revision
   *other than* the one under test. Not an oracle.
8. **LLM-authored assertions as an acceptance input.** Echo. See §6 and the proposed invariant
   in §9.

---

## 6. What cuts hardest against everything above

Reported as prominently as the case for it, per the working principles.

**(a) The transfer is not established, and the best evidence is the worst evidence for it.**
Csmith, GraphicsFuzz, OSS-Fuzz and syzkaller are the strongest published demonstrations that
manufactured oracles find defects experts missed. All four operate in domains with a
*reference semantics or a second implementation* (multiple C compilers, a shader's
untransformed self, a kernel ABI), industrial compute, and dedicated teams. A solo
maintainer's TypeScript service has no second implementation, no reference semantics, and no
budget for 5–15× TSan. **The mechanism is proven; its transfer to application code is
`[asserted]` and this note does not establish it.** The version-differential proposal in §5
is my attempt to manufacture the missing second implementation out of git — that is a
hypothesis, not a result.

**(b) Twenty-seven years of Daikon non-adoption is evidence about something.** Either the
false-positive burden is fatal or the value is low. "Automated oracle inference is cheap" is
not obviously true, and the tool most cited for it is the tool least used.

**(c) These oracles are not independent of the test suite in the way the β algebra wants.**
A metamorphic relation over the same function shares that function's blind spot. Round-trip
properties share the type's blind spot. Adding correlated checks lowers *measured* β without
lowering *true* joint error — which is `ADR-0012`'s dangerous direction, one level up.

**(d) The label argument has a bias I must state before anyone uses it (see §8).**

**(e) A version-differential oracle's true-positive rate is dominated by intended changes.**
Every real diff produces divergence; that is what a diff *is*. Unless the harness can bound
the intended blast radius, the oracle degenerates into "this commit changed something",
which is noise. This is the most likely way the §5 recommendation fails, and EXP-40 is
designed to fire on it.

**(f) I could not verify most of the numbers I wanted.** §0 and §11.

---

## 7. Consilience check on each technique

Required by `ADR-0010`: name the different class of facts, or cut it.

| Technique | Different class of facts it introduces | Verdict |
|---|---|---|
| Record–replay on production traffic | Inputs real users sent | **Consilient** |
| Differential vs. second implementation | Another program's behaviour | **Consilient** |
| Differential vs. previous revision | The pre-change program's behaviour, unobserved by the new tests | **Consilient** |
| Sanitizer / crash oracle | Machine-level memory and scheduling facts | **Consilient** |
| Metamorphic relation | New inputs to the same program — a different *sample*, same program | Weakly consilient |
| Round-trip property | The inverse function's behaviour | Weakly consilient |
| Property-based testing | Generated inputs; the property itself is human, not new evidence | Weakly consilient |
| Invariant mining on the code under test | **None** — it reads the same program | **Echo** |
| LLM assertion inference | **None** — same induction, restated | **Echo** |
| Mutation testing | n/a — it is a meter, not a witness | Not an oracle |

---

## 8. What this changes for β — stated precisely

Let `A` be the primary verifier (tests, types, build, lint) and `M` a manufactured oracle run
**after** `A` accepts.

1. Each artefact `A` accepted and `M` rejects is a **measured false accept of `A`**, obtained
   without a human verdict. This is the label-supply gain. [algebra]
2. It is only a false accept *within `M`'s defect class*. The numerator counts what `M` can
   see; the denominator does not shrink correspondingly. **The resulting figure is a lower
   bound on β and must be reported as one** — the same discipline `src/consilience/beta.py`
   already applies with `lower_bound_on_joint_error: True`. [algebra]
3. If `M` is later moved *upstream* into the acceptance gate, it stops producing labels and
   starts producing acceptances. **An oracle cannot be both a gate and a meter for the same
   artefact.** Any design that promotes a manufactured oracle into the gate must record that
   it has retired a label source. [algebra]
4. `M`'s own false-alarm rate must be measured before its rejections are believed. Diffy's
   primary/secondary construction is the cheapest known way to do that in band. [cited]
5. `M` must not be model-authored, or β degenerates into model self-agreement. [algebra]

Point 3 is not obvious and is the kind of thing that gets lost. It belongs in an ADR.

---

## 9. Proposed invariant, with its check (I1)

**V0-26.** No oracle whose verdict was produced by a language model may contribute to a β
numerator or denominator, and any oracle promoted from diagnostic to acceptance gate records
that promotion as the retirement of a label source.

**Same-commit check.** A contract test constructs a β input from an oracle record whose
`producer` field is a model identity and asserts it is rejected; a second test asserts that
moving an oracle id from the diagnostic set to the gate set without a corresponding
`label_source_retired` event fails the projection. Both live beside the existing V0-21
self-report rejection tests, which already ban self-reported confidence as a routing input.

Proposed alongside — not a new invariant, an extension of `V0-12`'s reporting discipline: a
β computed against a manufactured oracle carries the oracle's class identifier, so no caller
can present a class-restricted lower bound as composite β.

---

## 10. Two experiments, pre-registered

Drafted for `docs/10-research/experiment-register.md` (highest existing entry is EXP-35).
Stopping rules and "what it cannot decide" are written here **before any result exists**, as
required. Both are `BLOCKED` on ADR-0015 Gate A — neither may run while the increment is
observe-only, and neither routes, blocks or accepts anything.

### EXP-40 · Does differential-against-parent-revision produce usable signal, or just "this commit changed something"?

**Decides:** whether the §5 rank-1 recommendation survives contact with a real diff, and
whether it can supply β labels. If it fails, the cheapest manufactured oracle available to
this project is folklore and §5 must be rewritten.
**Precondition:** Gate A trajectory capture; a repository with a callable boundary and
recorded inputs; a fixed intended-blast-radius declaration per task, written **before** the
agent runs.
**Procedure:** for each completed task, execute the parent revision and the candidate
revision against the same captured inputs. First establish the noise floor by executing the
parent revision **against itself** on the same inputs (Diffy's construction) [cited]. Then
classify every candidate divergence as `intended` (inside the declared blast radius),
`unintended`, or `nondeterministic` — classification by a reader who did not write the diff,
before seeing whether the tests passed.
**Measures:** noise-floor divergence rate; unintended-divergence rate among artefacts the
primary verifier **accepted** (this is the β-label yield); adjudication cost in minutes per
task; proportion of tasks with no callable boundary at all.
**Stopping rules, fixed before the run:**
- The oracle earns its place only if, across at least 25 accepted artefacts, unintended
  divergences appear in at least 10% **and** the noise floor is below 2%. [asserted]
- If the noise floor exceeds 10%, the technique is rejected for this repository regardless of
  yield — a signal below its own noise cannot generate labels. [asserted]
- If more than half of tasks have no callable boundary, the verdict is "not applicable to
  this codebase", recorded as such, and §5's ranking is demoted rather than defended.
  [asserted]
- Fewer than 25 accepted artefacts, or unintended divergence between 2% and 10%, is
  `insufficient evidence`. Do not lower the threshold after seeing the distribution.
  [asserted]
- Adjudication cost above 10 minutes per task median means the oracle is a human-labour
  transfer, not an automated oracle, and is reported that way. [asserted]
**What it cannot decide:** whether unintended divergences are *defects* — divergence is not
wrongness, and this experiment deliberately does not adjudicate severity; whether the
blast-radius declarations were correct, since the same person writes the task and the
declaration; anything about repositories other than the ones measured; and β itself, because
the divergence oracle's own false-accept rate is unmeasured — the label yield is a lower
bound on β, per §8.

### EXP-41 · Does mutation testing rank the checks the same way measured per-check β does?

**Decides:** whether mutation score is usable as a **label-free proxy** for verifier
strength, which would let this project estimate oracle weakness without waiting for 30 human
rejections. This is a consilience check in `ADR-0010`'s sense: two inductions from different
classes of facts (synthetic faults vs. human rejections) about the same quantity.
**Precondition:** EXP-01 producing per-check diagnostics; a mutation tool for the repository
language.
**Procedure:** compute per-check mutation scores and per-check β diagnostics on the same
codebase and window. Compare only the **ordering** of checks, never the values.
**Measures:** rank correlation between per-check mutation score and per-check β; count of
surviving mutants that no check kills; count of equivalent mutants excluded, with the
exclusion rule fixed in advance.
**Stopping rules, fixed before the run:**
- Mutation score is admitted as a proxy only if the check ordering agrees on at least 4 of 5
  check classes across at least two repositories. [asserted]
- Any disagreement on the **weakest** check kills the proxy outright, whatever the overall
  correlation — the weakest check is the only one the proxy would be used to identify.
  [asserted]
- One repository, or fewer than four check classes with a usable β diagnostic, is
  `insufficient evidence`. [asserted]
- Agreement is never reported as "mutation score estimates β". It estimates *ordering*, and
  the register entry says so. [asserted]
**What it cannot decide:** whether mutants resemble the faults agents actually produce — the
mutant/real-fault coupling literature is in §11's verification queue and is not yet evidence
here; the *magnitude* of β; and whether a check that kills mutants would catch a defect the
maintainer cares about, since severity is not measured.

---

## 11. Verification queue — leads, not citations

Each of these is a claim I can state from memory and could not fetch this session. **None may
appear as `[cited]` anywhere until read at source and promoted in `bibliography.md`.** They
are listed so the next session can spend its search budget well, in priority order.

1. **Csmith's total bug count** (Yang, Chen, Eide & Regehr, PLDI 2011). The README confirms
   the *mechanism* [cited]; the headline count is unverified. [asserted]
2. **Equivalence Modulo Inputs** (Le, Afshari & Su, PLDI 2014) — the strongest evidence that a
   *manufactured* metamorphic relation finds defects a mature test suite missed. Unverified.
   [asserted]
3. **Knight & Leveson on correlated failures in N-version programming** — the load-bearing
   citation for the "differential testing cannot catch common faults" column. Unverified.
   [asserted]
4. **Just et al., FSE 2014, mutant/real-fault coupling** — decides whether EXP-41 is worth
   running at all. Unverified. [asserted]
5. **Papadakis et al. on mutation score vs. real fault detection with suite size controlled**
   — the counter-evidence to (4), and must be fetched *with* it. Unverified. [asserted]
6. **Polikarpova, Ciupa & Meyer, ISSTA 2009** — programmer-written vs. Daikon-inferred
   contracts; the closest thing to a measured precision figure for invariant mining.
   Unverified. [asserted]
7. **Any published precision figure for neural test-oracle generation** (TOGA and its
   re-evaluations). This note's §5 rejection of LLM assertion inference currently rests on
   `[algebra]` from `ADR-0012` and `CONSILIENCE.md`, not on a measured precision. That is
   sufficient for the decision but should be strengthened. [asserted]
8. **Chen et al., ACM Computing Surveys 2018, DOI 10.1145/3143561** — metadata confirmed via
   Crossref [ABS]; full text not read. The "identifying relations is the hard part" framing in
   §4 is mine, not yet the survey's. [asserted]
9. **Quviq QuickCheck on AUTOSAR / Ericsson** — the standard industrial property-based-testing
   result. Unverified. [asserted]

---

## 12. Limitations and negative results

This note surveys techniques; it measures none of them. [asserted] No Consilience number for
any oracle class exists, and the ranking in §5 is an argument from evidence class and
authoring cost, not from measured yield. [asserted]

The ranking is also repository-shaped. A codebase with no callable boundary makes rank 1
inapplicable; a systems codebase makes rank 3 the best thing on the list; a live service makes
rank 5 the best thing on the list. §5 should be read as "in this order, subject to
availability", never as a general result. [asserted]

Three ways this note is wrong that I would bet on, in order:

1. **Version-differential drowns in intended change.** EXP-40 is built to detect exactly this
   and reports it as the primary failure mode rather than a footnote. [asserted]
2. **The whole framing over-rates automation.** EXP-01's unplanned finding — that a third of
   merges overrode red CI, so the human is the real acceptance gate [measured] — suggests the
   binding constraint may be the maintainer's willingness to be stopped, not the oracle's
   ability to stop them. A better oracle that gets overridden is not an improvement.
3. **Manufactured oracles lower measured β without lowering true joint error**, because their
   blind spots correlate with the suite's. §6(c). This is the failure mode that would make the
   project's headline number *look* like it is improving while nothing has. [algebra]

If EXP-40 returns a null, the honest conclusion is that the cheap manufactured oracles are
not available to this repository and β's label supply stays human-bound — which makes
EXP-01's audit cost, not the harness, the project's binding constraint. That verdict is
recorded here in advance so it cannot later be narrated as something else. [asserted]

## 13. Publication disposition

**Lane A research note; not a paper candidate.** [asserted] The survey itself is not novel —
metamorphic testing, differential testing and invariant mining each have mature literature. A
plausible narrow contribution exists and is not established here: **ranking oracle classes by
exogeneity of evidence and reporting the resulting β as an explicitly class-restricted lower
bound.** [asserted] That needs EXP-40 and EXP-41 to return non-null, a primary-source novelty
matrix, and the entire §11 queue promoted to `[FULL]` before it clears G1. [asserted] Under
the §0 verification state this note cannot be published outside the repository as it stands.
[asserted]


---

## Renumbering note, 20 August 2026

The two experiments drafted above were written as **EXP-36** and **EXP-37**. Both numbers had
already been taken in `experiment-register.md` — EXP-36 by the behavioural-plugin experiment and
EXP-37 by the β* competence-curve sweep — so each identifier named two different experiments at
once, and two cross-references in this file resolved to the wrong one. Found by the review pass
over the overnight batch. [measured]

They are now **EXP-40** and **EXP-41**. Nothing about either design changed; only the labels.

The rule that prevents a recurrence is in the register: **numbers are allocated in the register
and nowhere else.** A draft in a research note is a proposal for an experiment, not a claim on an
identifier — which is exactly the mistake made here, twice, in a single file. [asserted]

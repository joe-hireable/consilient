# 0055. Simulated users produce runs, not verdicts — and the same run is how we test whether a non-expert can use this

- **Status:** PROVISIONAL
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (principal); drafted by the agent commissioned on the night of 20–21 August 2026 to establish whether "simulate different user types" and "accessible to anyone with average-plus intelligence" are one job or two.
- **Inquiry tier reached:** T1 ground
- **Executable model:** none. The skill's gate is conjunctive — a one-way door **and** dispersed priors **and** formalizable. This is not a one-way door: the default is refusal, admission is a later and separate decision, and reversing it is deleting a conjunct from a predicate. A model would dress a reversible default in arithmetic.

## Context

Two instructions arrived together, verbatim:

> "We are aiming to bring superintelligence and make it accessible for anyone wkth average plus
> intelligence. We also need more focus on simulating different user types."

They read as two programmes. The question this ADR exists to settle is whether they are, because
if they share a mechanism the project builds one thing, and if they do not it builds two and
should say so.

**What already constrains this, and it is more than the commission assumed.** The obvious move —
a fleet of simulated personas doing QA — is not an open question here. It has been examined and
partly refused:

- `qa-automation-and-the-anchor-problem.md` answers Q32.1 **yes, but narrowly**: a synthetic user
  introduces a different class of facts, and that class is *the input sequence and the implicit
  oracle*, **never the expectation**. Where the expectation is generated from the same repository
  by the same model family, ADR-0010 cuts it.
- `interface-beta-2026-08-20.md` §4 lists "simulated personas, visual-LLM *does this look right*,
  snapshot tests used as an acceptance oracle" as **explicitly not in the stack**, and §6 says a
  simulated-user β "would be the same shape of mistake, with a worse oracle."
- V0-19 already forbids a persona from being an authority, capability, admission or routing input,
  with a property test asserting that changing a display name changes no decision.
- V0-05 already restricts acceptance to verifier and human outcomes — but does not say what makes
  something a verifier, and that silence is the hole this ADR closes.

This ADR overturns none of those. It names the boundary all four of them imply, and gives it a
check, because a boundary with no rule banning bypass is not a boundary and this repository has
thirteen catalogued instances of exactly that failure.

The second instruction is a live defect, not an aspiration. To use this project today a person
must hold Wilson score intervals, seven gate conditions, ADR supersession trails, five evidence
tags and pre-registered stopping rules. `dreamers-and-the-bootstrap-problem-2026-08-20.md` already
recorded the sharpest version of the risk: *a system that cites evidence to someone who cannot
check the citation is indistinguishable from one that fabricates it.* The discipline is not the
problem. The quantity of it a user must hold in their head to get value is.

**This is not a one-way door.** Every clause below is a default that a measurement can lift.

## Decision

**A simulated user is a run, not an opinion, and a run is admitted for what it found and never
for what it approved.** Concretely:

1. **A user type is a run specification.** It has an `id`, a `task`, an artefact-checkable
   `success_criterion`, an `information_boundary` (what the operator is permitted to read), an
   `interface` (how it drives the artefact — CLI, HTTP, browser), the `oracle_kinds` it may
   invoke, and the `harness` that drives it. It has **no personality, no demographic, and no
   prose character sketch.** What operationally distinguishes a novice from an expert is what
   they know and what they try; those are the information boundary and the task, and they are
   measurable. "Acts frustrated" is decoration, it is what V0-19 already forbids from entering a
   decision, and it is refused here at the type level rather than at the decision boundary.

2. **A run's output is a finding, not a verdict.** Each finding carries the observed discrepancy,
   the **anchor** that supplied the expectation — implicit (crash, hang, traceback, non-zero exit,
   dead affordance), specification (the log, the `--json` contract), metamorphic, reference, or
   state (the code) — and a **reproduction**: the input sequence that produces it. A
   state-anchored finding is recorded with zero evidential weight rather than discarded, so that
   the proportion is measurable.

3. **The load-bearing clause: an unmeasured verifier's *pass* is not evidence; only its *fail*
   is.** A simulated user may reject, flag, or report. It may never accept. Generalised to the
   root cause rather than special-cased to personas: **no verifier whose own β is
   `insufficient_data` may appear as a disjunct in, or a substitution for, any part of the
   acceptance predicate.** It may be added only as an additional conjunct, where its pass licenses
   nothing on its own.

   The asymmetry is principled and not merely cautious. **A finding carries its own verification —
   re-run the reproduction. An approval carries nothing.** That is why a negative result from an
   execution with an unknown error rate is admissible and a positive one is not.

4. **The same instrument tests whether a competent non-expert can use this harness.** A run whose
   *subject* is the harness rather than the artefact, whose `information_boundary` is the minimum
   concept set below, and whose `success_criterion` is an artefact the run either produced or did
   not. **One mechanism, two subjects.** That is the answer to the commission: the two instructions
   are one job.

5. **Simulated accessibility results are one-sided, by the same rule as clause 3.** A simulated
   operator's **failure** is evidence that a person would also fail. A simulated operator's
   **success is not** evidence that a person would succeed, and may not be reported as an
   accessibility result. The simulated operator reads faster, never tires, never fears looking
   foolish and pays nothing to abandon; every one of those biases points toward over-success. The
   rule is fixed in EXP-71 before collection and only EXP-73 can lift it.

6. **The concept budget is five, and the record keeps everything.** A competent non-expert needs
   exactly:

   | # | Concept | Why it is load-bearing for the user |
   |---|---|---|
   | 1 | **The job** — what you asked for, and what counts as done | without it nothing else has a subject |
   | 2 | **Checked or not** — whether the thing was verified, and by what | the difference between a result and a claim |
   | 3 | **How often that check is wrong** — as a frequency, in words | the trust interface for a system nobody can audit |
   | 4 | **What it will not decide without you** — money, credentials, publishing, irreversible deletion, genuine preference | consent |
   | 5 | **Undo** — how to get back | recovery |

   2 and 3 do not collapse into one another: "it was checked" and "the check is wrong a third of
   the time" are precisely the pair that stops false trust, and dropping either produces a
   confident system.

   **Hidden from the user surface, retained in full in the record:** the Wilson estimator and every
   interval; α, k, Δ and the closed form; composite-versus-per-check β and per-check diagnostics;
   the seven gate condition identifiers, replaced at the surface by one derived state and the
   single thing that would change it; ADR numbers and supersession trails; the five evidence tags,
   collapsed at the surface into two acted-upon states, *measured here, n = N* and *not measured
   yet*; pre-registered stopping rules; the trajectory, the projection and the append-only
   mechanics.

   **β itself is never hidden.** Hiding the rate would be the actual dilution, because the rate is
   the only thing a user who cannot follow the reasoning can check. What is hidden is the
   estimator, not the number.

7. **The boundary with ADR-0054.** ADR-0054 (concurrent, not read here) routes work by measured
   capability rather than by label: it decides **who gets the work**. This ADR decides **whose
   verdict counts**, from measured verifier error. A capability measurement is not a β and may
   never be substituted for one — a backend measured excellent at *doing* a task tells you nothing
   about its false-accept rate when *judging* one. Where the two ADRs meet is the single fact that
   both refuse a label as an input; they do not otherwise overlap, and neither subsumes the other.

## PRODUCT and INSTANCE

| Clause | Label | Note |
|---|---|---|
| The run specification (1), findings (2), the unmeasured-verifier rule (3) | **PRODUCT** | ships open source, serves anyone, no account |
| The self-application instrument (4) and the one-sided rule (5) | **PRODUCT** | any project can point it at its own docs |
| The five-concept budget (6) and the hidden list | **PRODUCT** | the default surface for every user |
| EXP-70, EXP-71, EXP-72 | **PRODUCT** | measure the shipped harness |
| Joe as user type #1 — his tasks, his tolerance for review time, his phone-first input, his named subscriptions | **INSTANCE** | lives in his own configuration, never in this repository, and **carries no secret** |
| Which harnesses and accounts drive a run on this machine | **INSTANCE** | a run specification names an `interface` and a `harness` *kind*; the credential and the account are configuration and never enter the trajectory (V0-16) |
| EXP-73's recruitment, consent and payment | **INSTANCE input to a PRODUCT measurement** | Joe-only under ADR-0033 |

The test that keeps them apart: **if removing Joe from the project would delete it, it is
INSTANCE.** Nothing in clauses 1–7 fails that test.

## Evidence

- `[measured]` This project's own check suite accepts a bad artefact **0.3132 [0.2926, 0.3346]**
  of the time — 1,931 mutants in 104 s, EXP-47. Any new verifier is competing against a known
  number, which is the only reason clause 3's threshold can be stated at all.
- `[measured]` `cli.py` alone yielded **1,104 mutants, 440 composite survivors, 400 classified
  true defects**, surviving because the suite asserts JSON rather than stdout (EXP-47). The
  bad-artefact population EXP-70 needs already exists, is mechanically labelled, and is confirmed
  *not caught* by the existing checks. This is what lets EXP-70 run without the human-labelled
  holdout that has blocked every previous route to this question.
- `[measured]` The research instruments that produce this project's figures have β = **0.6825**
  [0.6700, 0.6948] — twice as permissive as the code they grade (EXP-49). An oracle nobody
  measured was worse than the thing it was grading. That is clause 3 stated as a fact rather than
  a principle.
- `[measured]` EXP-01's two audit-confirmed escapes include *a shipped feature losing a
  user-visible affordance after reload, checks green*. Structurally unreachable by a unit suite;
  structurally reachable by an agent driving the application. **n = 2 confirmed escapes in total —
  an existence proof for the defect class, not a rate.**
- `[measured]` The human-readable CLI path drops `quarantined` where `--json` reports it
  (`interface-beta-2026-08-20.md` §3). The surface a person actually reads is the least-guarded
  path in the product, which is where clause 6's check has to live.
- `[measured]` `src/consilient/cli.py` in this worktree, 21 Aug 2026: exactly **two** `print(`
  call sites and **one** `render(command, result) -> str`. The vocabulary chokepoint for clause 6
  exists and is singular, so its check is a denylist over one function plus a lint on one call
  site.
- `[measured]` Joe could not adjudicate 55 contested labels **in his own repository** because the
  artefacts were produced entirely by AI orchestration (`ground-truth-evaporates-2026-08-20.md`).
  The human verdict is not merely scarce here; for some questions it is unavailable. Clause 3
  cannot therefore be discharged by "ask a person every time", and that is why it has to be a
  rule about verifiers rather than a routing preference.
- `[algebra]` Clause 3's asymmetry is exact under conjunctive acceptance. Adding a verifier as a
  further conjunct cannot raise β — every extra check is another chance to reject — but it raises
  the false-rejection rate, and that cost is real. Adding one **disjunctively**, or substituting it
  for an existing check, removes a rejection path, and with its β unknown the resulting composite β
  has no upper bound the system can compute. The rule follows from the predicate's shape, not from
  caution.
- `[algebra]` A finding is re-verifiable by replaying its reproduction. An approval has no
  artefact to replay. Under Whewell's first clause — a conclusion carries its provenance — a
  finding participates in consilience and an approval from an unmeasured judge cannot.
- `[algebra]` Where a run's expectation is supplied by the runtime (exit status, traceback, hang,
  absent affordance) the induction is over facts the builder's induction did not contain, which is
  Whewell's second clause satisfied. Where the expectation is generated from the same source the
  builder read, the two classes coincide and the structure is echo. This is a statement about
  which facts entered, not about anyone's confidence.
- `[cited]` Ao, Gao & Simchi-Levi (2026), arXiv:2603.26993 — without new exogenous signals a
  delegated network is decision-theoretically dominated by a single decision-maker with the same
  information. This is why clause 1 makes the *information boundary* a field of the type rather
  than a convention.
- `[cited]` Ratchet, arXiv:2605.22148v3 — the only prior-art self-extending system that reports
  its judge's error rate: false-pass ≈ **0.01** (n = 210), false-fail ≈ **0.95** (n = 42, 95% CI
  0.84–0.99). A measurable judge is achievable, and the number that hurt was the false-*fail*.
  EXP-70 measures α_sim for that reason and not for symmetry.
- `[cited]` ADR-0033's synthesis: higher confidence in the AI is associated with less critical
  engagement, b = −0.69 log-odds, p < 0.001. Clause 6 must not become an explanation panel;
  explanations raised relative reliance from 29.59% to 38.87% while leaving the ability to reject
  statistically unchanged.
- `[cited]` METR: experienced developers reported a 20% speedup after a measured 19% slowdown. The
  accessibility claim cannot be measured by asking anyone — including a simulated anyone — whether
  it felt usable. Clause 5's outcomes are artefacts.
- `[asserted]` The unification in clause 4. Both jobs reduce to *an operator with a restricted
  information boundary drives a real interface to a mechanically decidable outcome*; only the
  subject under test differs. This is judgement, it is the specific thing the commission asked me
  to establish, and see the conflict-of-interest note below.
- `[asserted]` Five as the size of the concept budget. It is a defensible list, not a derived
  number, and EXP-71 and EXP-72 exist because of that.

**Sources deliberately not cited on an evidence line.** The synthetic-user and test-generation
literature this ADR's reasoning leans on — Canedo's anchoring identity, TestGen-LLM, PBT-Bench,
PersonaTester, Test Wars, HxAgent, PAARS — is read at abstract depth only, fourteen sources, one
reader, one session, and `qa-automation-and-the-anchor-problem.md` states that **none may be
promoted to a `[cited]` ADR line until fetched and read.** That rule is honoured here: none of them
appears above, and this ADR does not rest on any of them. Canedo's cancellation identity survives
as `[algebra]` because it is a derivation, not a report.

## Evidence against

- **This repository has already refused most of what clause 1 authorises, and it may be right.**
  `interface-beta-2026-08-20.md` §4 excludes simulated personas from the QA stack outright, and §6
  says a simulated-user β "would be the same shape of mistake, with a worse oracle." This ADR
  survives that note only because it refuses the acceptance role the note was refusing. **If a
  reader takes clause 1 as licence to build a persona fleet, the note is right and this ADR is the
  error.**
- **The commission's strongest premise is not supported in this repository, and there is a
  counterexample.** I was given, as a strong prior to test, that *every offline or reflective phase
  producing a durable verified gain had an execution boundary in it*. **No such finding exists in
  these docs** — `grep` over `docs/` returns nothing for it — and the nearest prior-art file
  contains a counterexample: Live-SWE-agent creates *task-local executable tools*, an execution
  boundary by any reading, and it **cut GPT-5-Nano success from 44% to 14% and induced loops.**
  `[cited]` An execution boundary is therefore necessary for the evidence class and demonstrably
  **not sufficient** for a gain. Clause 3 is what stands between the two, and if clause 3 is
  weakened this ADR reproduces Live-SWE-agent's result.
- **Ratchet's false-fail rate is the likeliest killer, and it is not β.** ≈0.95 `[cited]`. A driven
  session admitted as an extra conjunct cannot raise β and can still make the system unusable by
  rejecting nearly everything good. EXP-70's α_sim may be the number that ends this, and it would
  end it for a reason clause 3 does not protect against.
- **Mutants are not real defects.** EXP-70's population is mechanically labelled, which is its
  whole advantage and its whole weakness. Test Wars found LLM-generated tests **outperform** SBST
  and symbolic execution on mutation score while performing **worse than both** on real fault
  detection — exactly the dissociation that would make EXP-70's result fail to transfer. That
  citation is abstract-depth and unpromotable, which makes the objection harder to size, not
  weaker.
- **n = 2.** The entire empirical case that a driven session reaches a defect class unit tests
  cannot rests on one affordance-after-reload escape in one repository. One instance is not a rate
  and could be a property of that codebase.
- **The one-sided rule is suspiciously convenient, and this is the weakest point in the ADR.** It
  permits simulation to produce only bad news, which makes the method unfalsifiable in the
  direction that would embarrass it: if every simulated success is discarded in advance, the
  method can never be shown to over-claim. EXP-73 is the only thing that repairs this and it is
  `BLOCKED` on a decision only Joe can make. Until it runs, clause 5 is a safeguard that is also a
  shield.
- **Conflict of interest, stated plainly.** I was asked to establish whether two instructions share
  one mechanism, and I concluded that they do. An agent asked to find a unification and returning
  one is weak evidence for the unification. The strongest disconfirming reading is that clause 4 is
  a rhetorical bridge between two unrelated programmes, and that the honest split is: build the
  driven session for artefacts, and test accessibility with people only.
- **Q32 forbids what this partly does.** `open-questions.md` Q32 says *do not write a QA design
  document before these are answered*, and Q32.3 — where the human verdict enters — is answered
  "cannot be answered yet". This ADR designs the **object** and the **measurement** and
  deliberately does not design the **loop economics**, but that is a line I drew, and a stricter
  reader would say Q32 forbids the whole document.
- **The concept budget is my judgement with no evidence behind the number five.** I have not cited
  a working-memory result and will not manufacture one. Any of the five could be wrong and the
  hidden list could be hiding something load-bearing; EXP-72's dangerous cell is the check on
  exactly that.
- **What I searched and did not find.** I searched this repository's `docs/` for any measurement of
  whether simulated users find the defects real users hit, and found none; the absence is recorded
  independently in `qa-automation-and-the-anchor-problem.md`. **No web search and no metered call
  was made**, so "nobody has measured this" is a claim about this repository's evidence base and
  not about the world.

## Consequences

**Positive.** The project gets one instrument instead of two, and it is the instrument it already
believes in: an execution that produces a mechanically decidable outcome. Clause 3 closes a real
hole — V0-05 restricted acceptance to "verifier or human" without ever saying what makes something
a verifier, and any driving agent could have walked through that word. The accessibility claim
stops being a slogan and becomes seven tasks with artefact-checkable outcomes. EXP-70 becomes
runnable *today*, with no new dependency and no human labelling, because EXP-47's survivors are
already a labelled bad-artefact population — which is the first time this question has had a route
that does not wait on the holdout.

**Negative.** Clause 3 raises the false-rejection rate by construction, and Ratchet says that cost
may be severe; the project will feel this as work being rejected that was fine. Clause 6 creates a
second surface discipline to maintain, and a denylist is a maintenance burden that will be
circumvented the first time someone wants to print a gate identifier "just for debugging" — which
is why the lint on `print(` matters more than the denylist itself. Clause 5 means the accessibility
programme can produce failures for months and never produce a publishable success. And the ADR
declares three invariants whose checks are **specified but not written**, which is itself the
failure mode working principle 3 exists to prevent (see Enforcement).

**Neutral but load-bearing.** Every future verifier — a critic tier, a static analyser, a
connector, a browser-driving harness — now inherits clause 3 and must arrive with a β or arrive as
a conjunct. That is a bigger constraint than the persona case that motivated it, and it is
deliberate: one guard where all verifiers route through is a smaller thing to maintain than a
special case per verifier. It also means `routing_orchestration_enabled` stays `false` and is
untouched by this ADR: nothing here passes a gate, and nothing here points at any repository other
than this one.

## Enforcement

Three invariants. Each is checkable, each has been confirmed buildable against the code as it
stands, and none is written, for the reason stated at the end.

**V0-27 · An unmeasured verifier's pass is not an acceptance.**
A verifier whose β is `insufficient_data` may contribute a rejection and may never appear as a
disjunct in, or a substitution for, the acceptance predicate.
- Check: `tests/test_v0_invariants.py::test_an_unmeasured_verifier_cannot_accept` — seed a verifier
  record with n < `MIN_REJECTIONS`, assert the acceptance fails closed with reason
  `verifier_beta_unmeasured`; plus a Ruff/AST lint banning construction of an accepting `Outcome`
  from a verifier record carrying no β reference.
- Buildable today: `beta.py` already enforces `MIN_REJECTIONS = 30` inside the object, and the
  acceptance path already exists in `events.py` and `projection.py`. `[measured]`
- Fails CI: **yes**, via `.github/workflows/invariants.yml`.
- Added in the same commit as the implementation: **yes** (see debt below).

**V0-28 · Every ask is answerable by someone who has not read the code.**
`dreamers-and-the-bootstrap-problem-2026-08-20.md` states this as a design instruction with no
check. This gives it one.
- Check: a test over the registered ask templates asserting that none contains a file path, an
  identifier matching a code symbol, a line reference, an ADR number, or a gate condition
  identifier.
- Buildable today: V0-23 already loads an enumerated set of ask classes and rejects unlisted ones,
  so the templates are already a finite, addressable set. `[measured]`
- Fails CI: **yes**. Same commit: **yes**.

**V0-29 · The human surface speaks only the admitted concepts.**
- Check: a denylist assertion over everything `cli.render()` can emit — `wilson`, `interval`,
  `alpha`/`α`, gate identifiers `A1`–`B4`, `ADR-`, the five bracketed evidence tags, `stopping
  rule`, `supersede` — with the `--json` payload and `docs/` explicitly exempt, because the
  discipline must survive in the record and only the surface is being simplified; plus a lint
  banning `print(` outside the single `main()` call site so the chokepoint cannot fragment the way
  `jobboard-v2`'s `llm()` boundary did.
- Buildable today and verified: `cli.py` has exactly **two** `print(` call sites and **one**
  `render()`. `[measured, 21 Aug 2026]`
- Fails CI: **yes**. Same commit: **yes**.

**The debt, stated rather than buried.** None of the three checks is written in this commit,
because `src/consilient/` and `tests/` are owned by concurrent agents tonight and editing them
would collide. **An invariant declared without its check is the exact failure this repository has
catalogued thirteen times, and this is the fourteenth until it is paid.** The debt is: three tests
and two lint rules, in the same commit as the first code that could violate them. Nothing in this
ADR may be cited as an enforced boundary until then, and if the checks are not written the honest
response is to delete clauses 3 and 6 rather than keep a rule nobody enforces.

## What would overturn this

- **EXP-70 stopping rule 2 fires** — the driven session's marginal yield has a Wilson upper bound
  below 0.10. It finds nothing the suite and the static verifier miss, clauses 1 and 2 are dead
  weight, and the correct response is to write more checks and delete the object.
- **EXP-70 stopping rule 4 fires** — arm C's findings are ≥50% state-anchored, or within 10 points
  of the bug-known control. It was echo in a costume, exactly as `CONSILIENCE.md` clause 2
  predicts, and clause 1's information boundary failed to do its job.
- **EXP-70 returns α_sim near Ratchet's 0.95.** Admissible in principle, unaffordable in practice;
  the conjunct is removed and only implicit-oracle-gated reporting survives.
- **EXP-71 shows arm B completing ≥6 of 7 tasks at ≥80%.** The current documentation is not the
  barrier, the second instruction was aimed at a problem that does not exist, and clause 6 should
  be withdrawn rather than tuned.
- **EXP-72's dangerous cell exceeds 10%.** Collapsing five tags to two loses information people act
  on. The tags go back to the surface and the concept budget is wrong.
- **EXP-73 shows P(person fails | simulation failed) < 0.5.** Simulated failure does not transfer
  either. Clause 4's unification is then false, clause 5 measures nothing about people, and the
  honest statement — *only real humans can answer this* — replaces the accessibility half of this
  ADR entirely.
- **Anyone measures the overlap between defects simulated users find and defects real users hit.**
  Nobody has, anywhere this project has looked. A published result either way would move this ADR
  more than any experiment registered here.

## Publication candidate?

**No**, per the default. One thing could change that: if EXP-70 returns a β_sim and an α_sim for a
UI-driving agent used as a verifier, on a mechanically labelled population, that would be — as far
as this repository's evidence base reaches — the first reported false-accept rate for a simulated
user acting as an oracle, and every prior-art system surveyed reports none. It would belong to the
β paper as a section, not to a new QA paper, and only after a documented novelty search. Until the
number exists there is nothing to publish and saying so now would be the "describe unbuilt
capability in the present tense" failure `how-this-gets-believed-2026-08-20.md` names.

## Cross-references

`CONSILIENCE.md` clauses 1–3 · ADR-0002, ADR-0010, ADR-0012, ADR-0015, ADR-0033, ADR-0041,
ADR-0049, ADR-0050, ADR-0054 (boundary, clause 7) · V0-05, V0-14, V0-16, V0-18, V0-19, V0-21,
V0-23 · EXP-01, EXP-13, EXP-47, EXP-49, **EXP-70, EXP-71, EXP-72, EXP-73** ·
`../10-research/qa-automation-and-the-anchor-problem.md` ·
`../10-research/interface-beta-2026-08-20.md` ·
`../10-research/self-extension-prior-art-2026-08-20.md` ·
`../00-context/dreamers-and-the-bootstrap-problem-2026-08-20.md` ·
`../00-context/open-questions.md` Q32 · `../20-design/surfaces-and-who-they-serve.md`

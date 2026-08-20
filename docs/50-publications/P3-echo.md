# Agreement is not evidence

### Whewell's different-class criterion for multi-agent verification, and a negative result about our own use of it

**Joe Brown** — sole author and accountable principal
Consilience research programme
Draft of 20 August 2026 · **Position paper · Not submitted · Not peer reviewed**

---

## Abstract

Multi-agent verification is routinely justified by agreement: two or more models inspect a
piece of work, they concur, and the concurrence is treated as evidence. William Whewell's 1840
criterion for the consilience of inductions says that convergence is a test of truth only when
the inductions come from *different* classes of facts, and the modern decision-theoretic
version — Ao, Gao and Simchi-Levi (arXiv:2603.26993) — says that without new exogenous signals
a delegated agent network is weakly dominated by a single decision-maker holding the same
information. Together these yield one operational rule: **every multi-agent structure must name
the new class of facts it introduces, or it does not ship.** Agreement between agents that
share context is echo.

This is a position paper, and its central piece of evidence is a negative result about our own
use of the rule. In August 2026 we claimed that two different model families had independently
located the same defect in our own measurement instrument, and we recorded it as the first
occasion on which the project's central claim had been tested on itself and passed. We wrote
the overturning test into the same paragraph and ran it within about twenty minutes. It fired.
A same-family arm found the same defect, in the same file, at the same lines, reproducing the
concealment arithmetic to four decimal places, and independently reproduced the other arm's
separate contribution as well. Worse, the blind had leaked and we had built the leak: the
finding had been committed, in plain text and with its figures, to an append-only trajectory
log inside the repository the control was instructed to read. The consilience claim is
withdrawn. The defect survives.

We then report the one instance we consider clean. A cross-family pre-publication audit found
two leaks of private-corpus material that our own sweep was structurally incapable of finding,
because our sweep searched for repository-prefixed paths while the leak was the same paths
written bare. The auditor introduced an exogenous signal — the real file inventory of the
private repositories, 5,256 paths — that our search had never touched. The *difference*, not
the agreement, produced the finding.

Evidence limits, stated here and not only in a limitations section. This is a position paper
with anecdotal support. *n* is one in every direction that matters; the arms were never
matched; and the single controlled test we ran refuted our own favourite example. The
programme's measurement corpus is 356 merged pull requests from two private commercial
repositories written largely by one developer with heavy AI assistance, so external validity is
severely limited, and the verifier false-accept rate the programme is organised around has
never been measured with sufficient data — our own instrument returns *insufficient data*
today. Nothing argued here is novel: the philosophical claim is 186 years old, the
software-engineering claim is 40 (Knight and Leveson, 1986), and the quantitative claim was
measured three months before this draft at a scale we cannot match (Kohli, 2026: nine frontier
judges drawn from seven model families supply 2.18 effective independent votes). What we offer
is an operational rule, a taxonomy that decides cases, an enforcement mechanism with its own
measured hole, and the discipline of publishing the experiment that refuted our own example.

**Keywords:** multi-agent systems · verification · correlated errors · algorithmic monoculture ·
consilience · negative results

---

## 1. Introduction

The argument for putting several language-model agents on the same problem is usually made in
one of two forms. The *ensemble* form says errors are independent and majority voting therefore
suppresses them. The *review* form says a second agent, reading the first agent's output, will
catch what the first missed. Both forms treat **agreement as the evidence**: when the agents
concur the artefact is taken to be sound, and when they disagree the disagreement is escalated.

We claim the inference is unsound as usually deployed, for a reason that predates the field by
nearly two centuries, and we then spend most of the paper demonstrating that we ourselves got
it wrong under exactly the conditions we had written down.

Whewell (1840) defined the consilience of inductions as follows:

> "The Consilience of Inductions takes place when an Induction, obtained from one class of
> facts, coincides with an Induction obtained from another **different** class. Thus Consilience
> is a **test of the truth** of the Theory in which it occurs."

Three clauses, three commitments. *One class of facts* commits us to provenance: a conclusion is
only as good as the evidence it came from, and that evidence must travel with it. *Another
different class* is the load-bearing clause, and *different* is the load-bearing word — two
inductions over the same evidence do not corroborate one another, however many agents perform
them. *A test of the truth* commits us to the observation that a test has an error rate, which
is why the research programme this paper comes from is organised around measuring one.

Section 2 states the criterion and its modern formal and empirical counterparts. Section 3 gives
the operational rule and the taxonomy it decides. Section 4 describes the system under study and
is candid that its headline measurement does not exist. Section 5 is the negative result.
Section 6 is the positive instance. Section 7 reports three further structural findings from the
same programme that bear on the argument. Section 8 addresses enforcement, and reports that our
own enforcement mechanism shipped with the same class of hole it was written to close. Section 9
places the argument in the literature, where it is comprehensively pre-empted. Section 10 is the
threats-to-validity section, worst first. Section 11 states what would change our minds.

Evidence discipline throughout: every claim below is one of *measured* (we or the repository ran
it and the artefact exists), *simulated* (a model produced it), *cited* (a source says so, with
read depth declared), *algebra* (it follows from stated premises), or *judgement*. Where a
figure is simulated or assumed it is said so in the sentence that carries it, not in a footnote.

---

## 2. The criterion, and its three modern statements

### 2.1 The philosophical statement

Whewell's criterion is not a claim about the number of investigators. It is a claim about the
*independence of the evidential bases* from which their conclusions are drawn. A convened panel
of Nobel laureates is worth something when Curie brings radioactivity data and Bragg brings
crystallography; it is worth much less when all of them have read the same brief and are
reasoning about it out loud. The machinery for this is well developed and predates language
models by decades: Bovens and Hartmann (2003) show in a Bayesian framework that coherence among
reports raises confidence only when the sources are both partially reliable *and* independent,
and the Condorcet Jury Theorem's benefit is known to degrade sharply when juror errors are
correlated (Ladha, 1992; Berg, 1993).

### 2.2 The decision-theoretic statement

Ao, Gao and Simchi-Levi (arXiv:2603.26993) give the version that binds an engineering decision.
For a delegated acyclic network of agents with a fixed information set, and without new
exogenous signals, the network is weakly dominated by a centralised Bayes decision-maker
observing the same information; under proper scoring rules the gap is an expected posterior
divergence. The same paper measures relay degradation on a controlled four-way task: 90.7%
accuracy at one stage falling to 22.5% at five, below the 25% chance baseline, with a structured
posterior relay losing 2.8 points per stage against 8.5 for a prose relay.

Four qualifications were recorded in our bibliography when this paper was read in full
(2026-08-19) and they matter for how hard the theorem may be leaned on. The dominance is *weak*
(≥), so a delegated network can at best match the centre. The paper is an unrefereed technical
note. It never addresses whether a real language model can *implement* the centralised
decision-maker — there is no treatment of context limits or bounded rationality — so the popular
gloss "one big-context agent beats the committee" rests on Tran and Kiela (arXiv:2604.02460),
not on this theorem. And verifiers enter only as an abstract signal *W*: executable tests and
external validators are explicitly allowed to move the Bayes envelope. That last point is the
whole reason the taxonomy in §3 is not simply "cut all multi-agent structures".

### 2.3 The empirical statement

The empirical claim is 40 years old in software engineering. Knight and Leveson (1986) had 27
independently developed programs written against one specification and found they failed
together far more often than the independence assumption predicted; Eckhardt and Lee (1985)
supply the theoretical account of coincident failure. The experiment has been replicated with
coding agents: *N-Version Programming with Coding Agents* (arXiv:2606.20158) evaluated versions
produced by diverse agent systems, models and implementation languages on 10^6 randomised inputs
against the Launch Interceptor Program specification and reports substantial common-mode failure.

For language-model panels specifically, the measurement now exists and is decisive. Kohli
(arXiv:2605.29800, May 2026) reports that a panel of nine frontier models drawn from seven
families supplies **n_eff = 2.18 effective independent votes** — an independence ratio of
24.2% — that actual panel accuracy falls 7.6 to 22.0 percentage points short of the Condorcet
prediction under independence, that the best single judge matches or beats the panel on every
dataset tested, and that established aggregation methods close at most 11% of the gap. The paper
supplies a usable diagnostic in the Kish design effect, n_eff = k / (1 + (k − 1)·φ̄), with a rule
of thumb to treat results cautiously when n_eff/k < 0.5. It also makes our qualitative point
explicitly: genuine independence requires models that differ in *how they process information*,
not merely in brand name. The machine-learning community already has a term for what we have
been calling echo — **algorithmic monoculture** (Kleinberg and Raghavan, 2021; Bommasani et al.,
2022) — and we adopt it rather than propose a synonym.

**Read-depth honesty.** Of the sources in this subsection, Ao et al. and the Kohli paper were
read in full; Knight and Leveson, Eckhardt and Lee, arXiv:2606.20158, Ladha, Berg, Kleinberg and
Raghavan, and Bommasani et al. are cited at search-snippet or standard-reference level and have
not been fetched in full by this author. Section 9 and the reference list carry per-source
read-depth flags. A claim of ours that rests on an unread source is flagged where it occurs.

---

## 3. The operational rule and the taxonomy

The rule we adopted, and which this paper argues for, is deliberately blunt:

> **No multi-agent structure ships unless it names the different class of facts it introduces.**

It is a gate, not a heuristic. It is cheap to apply, it is checkable at design time, and it
decides real cases in both directions. Table 1 gives the taxonomy as we apply it.

**Table 1 — Structures that do and do not introduce a different class of facts.**

| Structure | New class of facts? | Verdict |
|---|---|---|
| Critic tier that **runs** the tests | Yes — execution output absent from the worker's context | Consilient |
| Parallel worktrees | Yes — different repository states | Consilient |
| Discovery agents on separate sources | Yes — different primary sources | Consilient |
| Independent re-derivation from primary evidence | Yes — re-derives rather than reviews | Consilient |
| Escalation to a stronger model | Weakly — a fresh draw, but not new evidence about the world | Consilient *on a technicality* |
| Debate or model battling over shared context | **No** | Echo |
| Planner → implementer handoff | **No** | Echo |
| A panel that read the same brief | **No** | Echo |
| A role-played governance layer | **No** | Echo |

The pattern is one sentence: **structures that touch the world are consilient; structures that
only talk are echo.**

Three consequences are worth stating because they are where the rule bites.

**Self-reported confidence is not a second class of facts.** A model's stated confidence is the
same induction restated, and gating on it is forbidden under this rule. This is well documented
in the routing literature and was the central defect of an earlier design session in this
programme.

**Escalation passes on a technicality, and we have not resolved it.** A fresh sample from a
different model is new information in the statistical sense but is not new evidence about the
world. Kohli's n_eff result suggests how weak that technicality is: if nine frontier models from
seven families are worth 2.18 votes, then "a fresh draw from a different family" purchases far
less independence than its price implies.

**The rule as stated is narrower than it reads.** It is justified for shared-context
deliberation in a domain that has an oracle. Kim et al. (*Nature Machine Intelligence*, 2026),
read in full, report multi-agent systems consuming 1.6–6.2× the realised reasoning turns of a
single-agent baseline and degrading on SWE-bench Verified by 1.3–12.8% — but the same paper
reports domains improving by as much as 80.8%, and concludes that task topology and inference
budget decide the sign. A blanket claim that collaboration is bad is not supported by the
literature and is not made here.

---

## 4. The system under study, and what it has not measured

The rule above governs a research programme whose object is **β**, the rate at which automated
checks accept an artefact that is in fact bad — acceptance sampling's consumer's risk, applied
per repository to the fault distribution a coding agent actually emits. The programme's own
honest position on β must be stated before any of its evidence is used, because the temptation
to present a method as a measurement is the exact failure this paper is about.

**β has never been measured with sufficient data.** The programme's meter, run on the real
trajectory on the day of this draft, returns:

```
beta [all]: insufficient data (0 human rejections, need 30)
```

Zero rows. The instrument exists — 972 lines across five modules with 62 test functions at the
commit this draft was written against, `mypy --strict` clean — and it has received no prospective
data at all. (Two earlier drafts of this programme's own novelty assessment quote 789 lines / 47
tests and 924 lines / 51 tests; both were true when written, hours apart. A figure about a moving
tree needs its commit, and this one has it.) Retrospective mining
cannot supply the gap: the miner fetches *merged* pull requests, so every retrospective row is a
human accept, while the estimator's denominator is human rejections. Mining more history adds
accepts forever.

What does exist is a retrospective proxy measurement over 356 merged pull requests from two
private commercial repositories, published as aggregate contingency tables (Table 2). These are
reproduced live from the retained records by a script in the repository; the per-pull-request
records are private and remain so.

**Table 2 — Aggregate contingency tables, 356 merged pull requests, measured.** Labels are proxy
labels, not adjudicated defects; see the caveats below.

| Repository (n merged PRs) | bad & CI green | bad & CI red | bad & no CI | good & green | good & red | good & no CI |
|---|---|---|---|---|---|---|
| Repository A (300) | 128 | 75 | 0 | 74 | 23 | 0 |
| Repository B (56) | 18 | 3 | 1 | 24 | 4 | 6 |

**Table 3 — Rates derived from Table 2, with Wilson 95% intervals, measured.**

| Quantity | Repository A | Repository B |
|---|---|---|
| α = P(CI red \| good) | 23/97 = 0.2371 [0.1635, 0.3307] | 4/28 = 0.1429 [0.0570, 0.3149] |
| α′ (unrun checks counted as a miss) | — (no such rows) | 10/34 = 0.2941 [0.1683, 0.4617] |
| β = P(CI green \| bad), raw proxy labels | 128/203 = 0.6305 [0.5623, 0.6939] | 18/21 = 0.8571 [0.6536, 0.9502] |
| β (unrun checks counted as a miss) | — | 18/22 = 0.8182 [0.6148, 0.9269] |
| Human override rate: merged over red CI | 98/300 = 0.3267 [0.2761, 0.3816] | 7/56 = 0.1250 |

Five caveats travel with Table 3 and none of them is optional.

1. **The labels are weak.** All 224 "bad" labels across both repositories come from a hot-fix
   heuristic; the revert arm of the detector fired zero times out of 356. A positive control
   establishes that this is a true negative rather than a broken detector: across 2,506 commits
   in the two repositories, six carried a revert-ish subject and none carried a pull-request
   reference, which is the detector's primary match path. These are fix-forward repositories, so
   the strong signal does not exist in the corpus at all.
2. **The audited precision of the proxy is 1 in 15** (Wilson 95% [0.01, 0.30]) on each
   repository, from a 40-label audit (15 bad-pairs plus 5 cleans per repository). The audit was
   conducted on the bad-and-green cell only, and its correction is propagated to a denominator
   that includes 75 unaudited bad-and-red rows whose median file count is 2.6× larger — the
   regime in which the heuristic's false-positive rate is highest. The audit was itself
   model-judged, in the same family as most of the rest of the programme.
3. **The originally published β was on the wrong axis.** The mining script computes P(bad |
   green), the transpose of the definition. On Repository A the two agree to 0.49% because the
   marginals 202 and 203 nearly coincide, which is precisely why the defect survived; on
   Repository B they differ by a factor of 1.91. This is the defect at the centre of §5.
4. **A label-corrected β on the correct axis does not exist anywhere.** Two widely circulated
   corrected figures, 0.12 and 0.14, are corrections to the *transpose* and must never be quoted
   as β. Our correction arithmetic is a hand-rolled special case of the Rogan–Gladen (1978)
   estimator, and it propagates Wilson bounds on the raw counts without accounting for
   uncertainty in the n = 15 and n = 5 correction factors, so those intervals are wrong in a
   known direction.
5. **α = 0.03, the value every threshold in the programme's simulations was scaled by, was
   invented.** It lies outside the Wilson interval of every measured candidate, including the
   lower bound of the weakest corpus (0.0570). Substituting a measured α rescales the derived
   threshold by 0.7865 — the system had been assuming its verifiers were about 21% more reliable
   than the corpus says, an error in the optimistic direction. This is a genuine, small, measured
   negative result and it is the cleanest one the programme has.

**The honest headline for this programme is a method plus negative results.** We say so here so
that §5 and §6 are read as anecdotes inside a programme that has not yet measured its own
headline quantity, which is what they are.

---

## 5. The negative result: we claimed consilience about ourselves and the control refuted it

### 5.1 The claim

On 20 August 2026 two arms attacked the programme's central measurement in parallel, blind to
each other and given the same five attack angles.

- **Arm 1** — a fourteen-agent workflow, one model family, including a skeptic instructed to
  refute — found that the mining script computes P(bad | accepted) rather than the defined
  P(accepted | bad), arguing from Bayes' rule.
- **Arm 2** — a single run in a different harness and a different model family — found that the
  estimator's denominator is "bad artefacts that reached a human", and argued it with a worked
  counterexample: 50 bad diffs, the verifier catches 45, the human sees 5 and rejects all 5, so
  the reported estimate is 5/5 = 1.00 against a true 5/50 = 0.10.

Two families, two harnesses, two different arguments, two different files, one underlying fault.
We wrote it up as *the first time this project's central claim has been tested on itself and
passed*, tagged it measured, and recorded the significance in the trajectory log.

### 5.2 The pre-registered overturning test, in the same paragraph

The same paragraph carried its own falsifier, written before the test was run:

> "**What would overturn it:** a same-family pair converging equally well on a defect of this
> severity, which would mean the convergence came from the corpus rather than from the
> difference. That is a cheap experiment and it should be run before this paragraph is quoted
> anywhere."

It was run within about twenty minutes.

### 5.3 It fired

A third arm, **the same model family as Arm 1**, was given the same five attack angles and the
same repository with the two write-ups withheld by name. It found the transpose defect — not a
cousin of it, the same defect in the same file at the same three line references — and
independently reproduced the concealment arithmetic to four decimal places: 128/202 = 0.6337
against 128/203 = 0.6305, and 18/42 = 0.4286 against 18/22 = 0.8182 on the second repository.

It then reproduced **Arm 2's separate contribution** as well, running the estimator over a
check-pre-filtered queue and printing `beta [all]: 1.000 [0.886, 1.000] from 30/30 rejections` —
the counterexample in executable form.

**One same-family run recovered both arms.** The claim that difference-of-family produced the
finding has no support and is withdrawn.

### 5.4 Six reasons the claim was wrong, and the first is fatal

**Table 4 — Why the cross-family consilience claim did not survive its own control.**

| # | Defect in the claim | Evidence |
|---|---|---|
| 1 | **The blind leaked, and we built the leak.** | The control read the repository's append-only trajectory log and found an event stating the defect in plain text, including 202/203, 0.6337/0.6305 and 0.4286/0.8182. Withholding two filenames from a git-tracked tree is not a blind. |
| 2 | The corpus was not the same corpus. | Three commits landed the earlier arms' conclusions into the tree before the control started. |
| 3 | The common cause may be the prompt, not the corpus. | All three arms received the same five attack angles, and angle 5 as written points at the denominator. This possibility was available before any of it ran. |
| 4 | Family was confounded with scaffold. | Arm 1: fourteen agents with a refuting skeptic. Arm 2: a different harness *and* a different family. Control: a single run. |
| 5 | *n* = 1 against *n* = 1 separates nothing. | Not family, not sampling variance, not run-to-run variance. |
| 6 | The adjudicator shared a family with the claimant. | Echo, by our own definition, in the act of testing for echo. |

### 5.5 What survives, and the structural lesson

**The defect survives and is stronger** for three independent hand-verifications; the axis
decision is recorded and the definition stands as P(accept | bad), with the transpose retained
under its own name and reported alongside. **The consilience claim does not survive.** The
significance field in the original trajectory event is withdrawn and downgraded from *measured*
to *judgement*.

The programme's standing position, which we decline to soften: **there is no measured evidence
that difference-of-class does anything for this project.** That is exactly the position it was
in the day before.

The structural lesson is worth more than the claim was:

> **You cannot run a blind experiment inside the repository you are writing your findings into.**

The trajectory log is append-only, committed, and the first thing a thorough agent reads. Every
finding recorded there becomes corpus for every subsequent run. This is not an operational slip
to be avoided next time by being careful; it is a property of any project that keeps its evidence
and its instrument in one tree, and it will recur every time an arm is asked to be independent.
The repair is specified and has **not** been run: freeze a corpus snapshot before the first arm,
commit the angle text verbatim, run two further same-family and two further cross-family arms
against it, and count.

### 5.6 Why we lead with this

A position paper whose authors publish the experiment that refuted their own best example is more
persuasive than one that does not, for the same reason the paper's thesis is true: the overturning
test was a *different class of facts* — an actual run, with an outcome not under the claimant's
control — rather than more reasoning about the same evidence. The claim was defeated by the only
move this paper recommends.

---

## 6. The positive instance: an audit that could not have been ours

### 6.1 What happened

The programme's rules forbid publishing anything from two private commercial repositories used
as measurement corpora: their names and aggregate measured metrics may appear, their content,
excerpts and detailed paths may never. The rule had been declared in the initial commit and
enforced by nothing.

It had been violated in that same initial commit. A cross-family pre-publication audit — a
different model family, in a different harness, running under a different operating environment —
cross-referenced **5,256 real paths from the two private repositories** against this repository's
tracked tree and found two blockers plus seven files naming a private document by filename.
Described only in class: detailed internal paths, function and script identifiers, hook
filenames, a verbatim quotation from a private assessment document, and a commercial product
identity, sitting in tracked files.

The leak was introduced in the initial commit and scrubbed the next morning. The commit message
for the scrub says the leak survived 75 commits. **That figure does not reproduce**: the interval
is 100 commits over 16 hours 8 minutes on a linear history with zero merges. We use 100 and
record the discrepancy here rather than silently correcting it.

### 6.2 Why the difference, not the agreement, produced the finding

Our own sweep for the same class of violation had run and had returned clean. It searched for
paths **prefixed** with a repository name. The leak was the same paths written **bare**, with no
prefix to search for. That angle could not have found the leak however carefully it was run.

The auditor introduced an **exogenous signal**: the actual file inventory of the private
repositories. Under Whewell's second clause that is what makes the event consilient rather than
echo. The finding is not "a different model was smarter"; it is "a different search was grounded
in facts our search never touched". We insist on that phrasing, because the alternative phrasing
is precisely the confound that destroyed the claim in §5.

### 6.3 The caveats, which must travel with it

*n* = 1. The arms were not matched. Family is confounded with the needle corpus — the auditor
had both a different model *and* a different evidence base — which is the same confound as §5.4
row 4, one section later. We are not claiming the family did the work; we are claiming the
exogenous signal did, and we cannot separate them with one run.

### 6.4 The repair, and what it teaches about enforcement

The rule now has a check, and the check has three properties worth recording.

**It was proven to fail before it was trusted.** Run against the pre-scrub tree it reports all
five path references. The first threshold chosen caught only two of the five, because one path is
15 characters and slipped under a minimum-length filter.

**It is deliberately not a CI job.** The private repositories are not present on a CI runner, so
a CI version would silently no-op, and a check that silently no-ops is worse than none. It is a
local pre-publication gate with a flag that turns a missing corpus into a failure rather than a
skip.

**Its ceiling is documented rather than hidden.** It matches file paths only, so a leaked
function name, CI job name or commit subject passes; it compares against the corpora's current
HEAD, so a since-deleted path is not in the needle set; and it hard-codes two absolute paths, so
it runs on exactly one machine. On first run against the scrubbed tree it flagged its own
docstring example — the check working — and that finding is left recorded rather than tidied away.

One second-order failure in the same episode is the best single illustration of the programme's
own discipline failing: the gate was piped into a formatter, which discarded its exit code, so a
**failing gate reported success**. Verify by artefact, and do not pipe a gate into a formatter.

### 6.5 A weaker companion instance

A separate cross-family audit was pointed at the *invariants* rather than at the diff, asking of
each numbered invariant: would its check actually catch a violation, and is there a second path
to the same state? It returned three confirmed defects in about twelve minutes, after the
author's own 40-test suite passed and `mypy --strict` was clean:

1. A human-authority guard returned early unless one field was present, while a second code path
   read a different field straight into the table the estimator reads — so an agent could author
   the human verdict against which β is defined.
2. A replay invariant built the projection from the log twice and compared the two rebuilds,
   which are identical by construction; and the build step deleted the database first, destroying
   the drift the check existed to detect. The governing decision record had logged that gate
   condition as *satisfied*. It was satisfied by a tautology.
3. A "measured" result object could be constructed with zero rejections, a rate outside [0,1] or
   a point outside its own interval, and an argument to the estimator could *lower* the evidence
   floor it enforced.

The honest reading of this episode is that the *question* was different, not merely the model.
Asking "would this check catch a violation, and is there a second path?" generates a different
evidence set than "review this code". A same-family arm asked the same question might well have
found the same three, and — after §5 — we no longer assume otherwise. Its stated overturning
conditions are on the record: a cross-family audit returning only false positives, or a
same-family audit finding defects of this severity. One run of each is not a rate.

---

## 7. Three further structural findings that bear on the argument

These are from the same programme, are reported at the level of aggregate structure, and are each
*n* = 1.

### 7.1 A single agent beat the convened meeting

A pre-registered experiment compared three arms on six real design decisions at matched budget:
**A**, a single agent with no communication layer; **B**, a structured owner-and-dissent meeting;
**C**, a free-form group discussion. Ground truth was registered as the maintainer's judgement.
That judgement was not obtained, so the pack was graded **blind by two different model families**,
neither of which wrote any option and neither of which saw the other — a substitution that
answers a different question than the registration asked, and the record says so.

**Table 5 — Blind grading, six decisions × two graders = twelve judgements, key opened after both
grade sets were recorded. Measured.**

| Arm | best | worst |
|---|---|---|
| A — single agent, no communication layer | **9** | 1 |
| B — structured owner meeting | 2 | 3 |
| C — free-form group | 1 | **8** |

The graders agreed on four of six decisions, and the single agent won all four. Arm B ran at 4.8×
the tokens and 3.7× the wall-clock of Arm A. The pre-registered stopping rule fired and the
meeting layer was cut; the accountability matrix was retained as a *record format*, because
writing down accountability was never on trial — manufacturing it by meeting was.

Two honest qualifications. All 96 agents in the underlying arms shared one model family, so
cross-arm agreement may be shared prior rather than robustness. And the theorem's punished regime
was never instantiated: both arms held *partitioned* evidence, so most messages carried genuinely
new facts (new-information fraction 0.60 for B and 0.48 for C per decision), and the
shared-context arm the theorem actually predicts about was never run. Nothing here contradicts Ao
et al.; nothing here needed them either.

### 7.2 Dissent survives structure and dies in discussion

All six structured-arm decisions carried an explicit, often self-critical dissent section. All six
free-form threads closed in reported full convergence with **zero** standing dissent; caveats were
absorbed as "conditions". On the principle that honest disagreement is information, the free-form
format destroyed information the structured format preserved. This is the failure mode we would
flag first in any deployed debate structure: it does not merely fail to add evidence, it removes
the divergence signal that was already there.

### 7.3 Provenance corrupted in two hops, and produced a fabricated human

Every write in both rented project-management tools landed under a single OAuth identity. In one
thread an agent's second turn misattributed another agent's proposal to the human, and the scribe
then recorded that the human had *contributed directly* — a false human-participation claim
sitting in a meeting record no human joined. This is Whewell's first clause, provenance, failing
exactly as the criterion predicts, and it renders "outcome writes attributed to the owner only"
unenforceable on rented tooling.

The coda belongs in the paper because it is unflattering. After the resulting invariant shipped in
code, the author violated it three times within fifteen minutes on the same day, writing a
human-decision event under an agent actor. The authorisations were genuine — the human did say
"proceed" — but the events were not, because that field asserts the human *authored* the event.
Recording that a human decided something is not the same act as the human deciding it. The three
lines remain permanently in the append-only log as rejected lines.

### 7.4 A blind protocol whose summary statistic was flat by construction

In the grading of §7.1, labels were randomised independently per decision so that each letter
carried each arm exactly twice. Both graders reported a nearly flat letter tally and both
concluded the spread was noise. **Flat is exactly what a dominant arm produces** under that
randomisation. Both graders were right about what they could see and wrong about the world; the
signal existed only after the key was applied, and the graders were correctly forbidden the key.

The rule this yields is general: **a blind grader must not be asked to report a tally over
randomised labels, because that statistic is designed to be flat.** It must report per-item
judgements and let the unblinding compute the aggregate. Both graders did supply per-item
judgements, which is the only reason the result was recoverable.

---

## 8. Enforcement: a rule without a check is not a rule

The programme's third working principle says a chokepoint without an enforcement rule is not a
chokepoint, and the lesson came from a prior commercial codebase in which a documented unified
model-access boundary was in practice five access paths, because no lint rule banned bypass.

**The different-class rule violated that principle inside the project named after it.** The
governing decision record declares two checks on a per-role `evidence_class` attribute, to be
validated at configuration load. The string appeared **zero times** in the source tree and zero
times in the tests while at least four multi-agent structures ran, including the arms of §5, §6
and §7. There is a mitigating detail — the decision record scheduled the check for the same commit
as an orchestrator that does not yet exist, so the debt was scheduled rather than overdue — and it
does not change the fact that the structures ran without it.

A check shipped on the day of this draft. **It carries the same class of hole.** Measured against
the real trajectory log: the check returns early whenever a `contributors` field is absent, and
**9 of 96 events carry that field**, so 87 events are structurally exempt. This is an opt-in
invariant, and it is the identical early-return bypass found in the human-authority guard, shipped
seven hours after the write-up that named that shape as the failure. A second ceiling is
acknowledged in the commit that landed it: the check gates on the *declared* class and cannot
verify that the declaration is true.

We report this because it is the honest state of the only mechanism that would distinguish this
work from a restatement of Whewell, and because the pattern — the author of a defect class
reproducing it within hours, in the guard written to prevent it — is the most transferable finding
in the paper. A related measurement from the same programme: across nine errors in one instrumented
session, **two** were caught by an enforced mechanism and **seven** only because an agent happened
to look. That 2/9 has its own honest failure mode, stated where it was recorded: the enforced
fraction can rise because errors stop being *counted* rather than because they stop happening, so
the denominator has to come from somewhere independent of the mechanism being credited.

**One live overclaim in our own tree, which we name rather than let a reviewer find.** The
repository still contains, in the same file as the leak audit, an unretracted sentence calling a
different *n* = 1 convergence "the first genuine consilience event this project has recorded about
itself", tagged measured. It is structurally identical to the claim withdrawn in §5 — one
convergence event, no same-family control, no frozen corpus, both arms working inside the
repository that already contained the finding. We do not rely on it here, its *measured* tag
should be challenged, and it is on the list to be retracted or controlled.

---

## 9. Related work: what is actually new here, which is very little

We state the prior-art position at full strength, because a paper making this argument cannot
afford to be sloppy about its own novelty.

**The philosophy is 186 years old.** Whewell (1840) is our name and our motivation; he cannot also
be our contribution. Bovens and Hartmann (2003) formalised the independence requirement 23 years
ago, and the Condorcet-with-correlated-jurors literature is older still.

**The software engineering is 40 years old.** Knight and Leveson (1986) is the canonical result
that independently produced agreement is not independent evidence, and it has already been
replicated with coding agents on 10^6 inputs (arXiv:2606.20158).

**The decision theory is someone else's theorem.** Ao, Gao and Simchi-Levi (arXiv:2603.26993). Our
own decision record concedes this in its publication-candidate line.

**The quantitative version is three months old and better funded than anything we can run.** Kohli
(arXiv:2605.29800) measures n_eff = 2.18 for nine judges across seven families, a 7.6–22.0 point
Condorcet gap, best-single-judge parity or dominance, and aggregation closing at most 11% of the
gap. *Correlated Errors in Large Language Models* (ICML 2025) reports that when two models both
err they land on the same wrong answer about 60% of the time, and that an inter-model error
correlation of r = 0.77 reduces an ensemble of three to an effective size near 1.3, with larger and
more accurate models showing *more* correlated errors.

**The operational fix may also be published.** Kuai et al. (arXiv:2604.07650) appear to propose a
statistical framework for auditing behavioural entanglement between models and reweighting
verifier ensembles accordingly. **We could not extract the full text**, this citation is at
abstract level only, nothing in this paper rests on it, and it must be read in full before
anything does. Separately, *Self-Authored Verification Is Unreliable in Heuristic Self-Improving
Agents* (arXiv:2607.24300, July 2026, read in full) names the verifier–deployment gap, shows that
self-authored constraints cannot close it, and proposes a sealed exogenous acceptance loop — an
independent derivation of the exogenous-signal rule, published a month before this draft, with
measurements.

**Adjacent verifier-weakness work is saturated.** SWE-Bench+ (arXiv:2410.06992, abstract level)
found 31.08% of passed patches suspicious and 32.67% involving solution leakage, with correction
dropping one agent from 12.47% to 3.97%. A read-in-full survey in our bibliography records
maintainer merge rates averaging 24.2 percentage points below automated grader scores on the same
pull requests. Meta-Harness (arXiv:2603.28052, COLM 2026, read in full) already automates harness
search and audits its objective signal for regex leakage — it mitigates *leakage* while ignoring
*weakness*. Our standing position is that this programme is Meta-Harness's missing precondition,
not its rival.

**What is left.** Four things, and each is small.

1. **An operational rule with a taxonomy that decides cases** (Table 1), stated as a ship/no-ship
   gate rather than as a caution. Kohli supplies a diagnostic (n_eff) and we supply a design-time
   gate; they compose, and the composition is the useful part.
2. **A published self-refutation.** We are not aware of another report in which a team
   pre-registered the falsifier for its own multi-agent-independence claim in the same paragraph,
   ran it within the hour, and withdrew the claim — including the finding that the team itself
   built the leak that broke the blind.
3. **A structural lesson about experimental design in agentic repositories**: you cannot run a
   blind experiment inside the repository you are writing your findings into, because an
   append-only, committed trajectory log becomes corpus for every subsequent arm. We have not seen
   this stated elsewhere and it will recur for anyone whose agents read their own project's
   records.
4. **A clean example of what an exogenous signal buys** (§6): a search grounded in a fact inventory
   the incumbent search never held, finding what the incumbent search could not find in principle.

We explicitly do **not** claim: that cross-family verification outperforms same-family
verification (our one controlled test says we cannot support it); that agreement is never
informative; that multi-agent systems are generally worse than single agents (Kim et al. report
domains improving by 80.8%); or that any prior-art search here was exhaustive. Two earlier "no
prior art found" claims in this programme were withdrawn after a later search established that the
original search had been conducted in the one field that could not contain the answer, and one such
line still stands unretracted in a decision record alongside its own downgrade.

**Table 6 — Read depth of external sources used above.** *FULL* = read in full by this programme;
*ABS* = abstract or landing page only; *SNIP* = search-snippet level; *STD* = standard reference not
fetched for this draft. Sources marked † were read by an assisting agent rather than by the author.

| Source | Depth |
|---|---|
| Ao, Gao & Simchi-Levi, arXiv:2603.26993 | FULL |
| Lee et al., Meta-Harness, arXiv:2603.28052 | FULL |
| Kim et al., *Nature Machine Intelligence* 2026 | FULL |
| Jwalapuram et al., arXiv:2606.13003 | FULL |
| Kohli, arXiv:2605.29800 | FULL † |
| Guo et al., SEAL, arXiv:2607.24300 | FULL † |
| Qwen Team, arXiv:2606.26300 | FULL † |
| Kuai et al., arXiv:2604.07650 | ABS † (extraction failed) |
| SWE-Bench+, arXiv:2410.06992 | ABS |
| Herbold et al., arXiv:1911.08938 | ABS † |
| Knight & Leveson 1986; Eckhardt & Lee 1985 | SNIP † |
| arXiv:2606.20158 (N-version with coding agents) | SNIP † |
| *Correlated Errors in LLMs*, ICML 2025 | SNIP † |
| Kleinberg & Raghavan 2021; Bommasani et al. 2022 | SNIP † |
| Tran & Kiela, arXiv:2604.02460 | SNIP |
| Whewell 1840; Bovens & Hartmann 2003; Ladha 1992; Berg 1993; Rogan & Gladen 1978 | STD |

No source at SNIP or STD depth carries a load-bearing claim in this paper on its own; each is used
for a statement that is also supported by a FULL-depth source or by our own measurement. The single
exception is Knight and Leveson, which is used for a historical claim of priority *against* us and
therefore errs in the conservative direction.

---

## 10. Threats to validity

Worst first.

**T1. The one controlled test we ran refuted our own central example, and we have not re-run it
correctly.** Section 5 is not a limitation of the paper, it is a result in the paper, and its
implication is that we have no measured evidence that difference-of-class does anything for this
project. Everything positive we report (§6, §7) is uncontrolled *n* = 1 anecdote of exactly the
kind §5 shows to be unreliable. A reader who concludes "these people cannot yet demonstrate their
own thesis" has read the paper correctly. The specified repair — frozen snapshot, committed angle
text, two further arms per family — is cheap and has not been run.

**T2. Every positive instance is confounded between model family, harness, prompt and evidence
base.** In §6 the auditor differed from the incumbent in family, harness, operating environment,
search strategy *and* needle corpus. We attribute the finding to the exogenous signal on
mechanistic grounds — the incumbent's search could not have found the leak in principle — but we
cannot separate the factors with one run, and §5.4 row 4 is a record of exactly this confound
destroying a claim.

**T3. *n* is one, everywhere.** One withdrawn convergence, one leak audit, one invariant audit, one
three-arm decision experiment, one blind grading with twelve judgements from two graders. No rate
in this paper is a rate. Where we give counts (12 judgements, 9 of 96 events, 2 of 9 errors), they
are counts from one session or one tree.

**T4. The measurement corpus is severely limited and cannot be released.** 356 merged pull requests
from two private commercial repositories, written largely by one developer with heavy AI
assistance, one labelling pass, a proxy whose strong arm never fired, and audited proxy precision
of 1 in 15. One repository is heavily verification-ratcheted, which is the regime in which the
programme's thesis looks best, so measuring there flatters it; the other has 56 pull requests and
may never support a tight estimate. The corpus cannot be published, cannot be independently
replicated, and cannot satisfy the data-availability expectations of a technical
software-engineering track. Public agent-authored pull-request corpora now exist at larger scale,
including a 2026 mining challenge dedicated to agentic pull requests, and are the correct next
substrate; the private corpus should be demoted to a contrast case.

**T5. The headline quantity of the surrounding programme has never been measured.** β returns
*insufficient data* with zero rows. Retrospective mining structurally cannot supply its
denominator. The evidence floor as configured (30 rejections) is one sample below the smallest *n*
at which even a flawless record could clear the derived threshold — 0/30 gives a Wilson upper bound
of 0.11352 against a threshold of 0.111, while 0/31 gives 0.11026 and clears — so no routing
decision can ever be taken at the floor as set. Separately, one field on every result asserts that
the quantity is a lower bound on a joint error, and a passing test enforces that assertion; it is
not a lower bound, because two unmeasured biases run in opposite directions (human misses push the
estimate down, verifier pre-filtering pushes it toward 1.0) and do not compose into a bound in
either direction. That defect is open at the time of writing, in the project that measures false
certification.

**T6. Our own enforcement mechanism is opt-in.** Section 8: 87 of 96 events are structurally exempt
from the different-class check because it returns early when a field is absent, and the check
validates a *declared* class it cannot verify.

**T7. Grader substitution.** In §7.1 the registered ground truth was the maintainer's judgement and
it was not obtained; two model families were substituted. That answers "do independent readers of a
different lineage prefer these outputs?" rather than "does the maintainer?". The graders also
scored quality at the moment of decision, and the structured arm's distinctive product was
*preserved dissent*, whose value is that it survives to be useful later — which no snapshot grading
can see. This is the strongest unanswered objection to §7.1 and it was stated by the record itself
before the grading ran.

**T8. Self-audit bias.** Almost every artefact in this paper was produced by, and then audited by,
systems from one model family, working inside the repository that contains the findings. The audits
that found the most were the ones that came from outside that tree — which is either the paper's
thesis quietly confirming itself, or selection on our part. We cannot distinguish those with the
evidence we have.

**T9. Instrument non-amendment.** The mining instrument still prints only the transposed ratio,
still classifies cancelled runs as red, and still discards per-check identities. That was a
deliberate protocol choice — repairing an instrument mid-run after seeing what it produced is
outcome-aware tampering — and the corrections live in separate read-only scripts. The consequence
is that the raw recorded outputs and the current best estimates are in different files, and a
reader must be told which is which.

**T10. One figure in our own history does not reproduce, and several conflicts remain live.** The
scrub commit says 75 commits; the count is 100 (§6.1). A separate claim in our records that one
end-to-end suite accounts for 91% of failures in one cell against 52% in another reproduces only if
cancelled runs are counted as failures; excluding them — the correction made in that same section —
the figures are 50.7% and 47.8%, and a 39-point discriminating gap becomes 3 points. That claim is
not used in this paper and should not be used anywhere. Additionally, every one of the 242
non-passing check instances in the re-fetched red cells carries `required = false`, so on this
corpus "CI red" never meant that a required gate blocked a merge — though that flag reflects
branch-protection state at fetch time, not at merge time.

---

## 11. What would change our minds

Falsifiers, in cost order. Each is cheap and none has been run.

1. **Run the independence test properly.** Freeze a corpus snapshot before any arm runs, commit the
   prompt text verbatim, place the trajectory log outside the snapshot, then run *k* ≥ 3
   same-family and *k* ≥ 3 cross-family arms against it and count findings and overlaps. If
   same-family arms recover cross-family findings at the same rate, the different-class rule buys
   nothing at this scale and the taxonomy in Table 1 should be demoted from a gate to a heuristic.
2. **Compute n_eff on our own arms** using Kohli's design-effect diagnostic rather than asserting
   difference from model names. If our "different families" produce n_eff/k < 0.5, our own
   cross-family structures are monoculture by measurement and should be priced accordingly.
3. **Replace the model-family axis with the evidence axis.** The §6 mechanism suggests the
   productive variable is the *evidence base and search strategy*, not the lineage. A matched
   design — same family, deliberately different grounding — is the direct test, and if it
   reproduces §6's result then "cross-family" is the wrong knob and should be dropped from the
   vocabulary entirely.
4. **Close the enforcement hole and measure what it rejects.** Make the different-class check
   mandatory for any event with more than one contributor rather than opt-in, then report what
   fraction of real multi-agent structures it refuses. A gate that rejects nothing is not a gate;
   an internal audit of this programme's own tree catalogued at least twenty instances of a check,
   gate or invariant that was structurally incapable of failing, fourteen of them found on a single
   day.
5. **Re-run the programme's instrument on a public agent-authored corpus.** This repairs external
   validity, reproducibility and artefact availability at once, and demotes the private
   356-pull-request corpus to a contrast case.

If (1) comes back negative, this paper's operational rule survives as a design heuristic grounded
in a theorem and in Kohli's measurement, and its empirical section becomes a report of one team
failing to demonstrate it twice. We would publish that.

---

## 12. Conclusion

Agreement between agents is evidence about the agents. It is evidence about the artefact only to
the extent that the agents' conclusions rest on different classes of facts. That is Whewell's 1840
criterion, it has a modern theorem behind it and a modern measurement in front of it, and it yields
one gate a designer can apply before writing any code: **name the new class of facts your structure
introduces, or do not ship it.** Structures that touch the world — a critic that runs the tests, a
worktree on a different repository state, a discovery agent on a separate source, a search grounded
in an inventory the incumbent never held — introduce one. Structures that only talk do not.

We hold ourselves to that rule and report that we have twice failed to demonstrate it. Our best
example of cross-family consilience did not survive a control we wrote into the same paragraph and
ran twenty minutes later, and the blind it depended on had been broken by our own logging. Our one
clean instance is a single uncontrolled event whose mechanism we can explain but whose cause we
cannot isolate. Our enforcement check is opt-in and exempts 87 of 96 real events. The programme's
headline quantity has zero rows.

That is a thin evidential record for a strong claim, and we prefer to state it that way than to
present the anecdotes as a result. The one thing we would defend at full strength is the
methodological move that produced everything honest in this paper: when you believe agents agreed
for a good reason, write down the observation that would show they did not, and go and make it.

---

## Data availability

**Released.** The instruments are in the repository this paper comes from: the retrospective mining
script and the three read-only recomputation scripts (contingency tables, proxy diagnostics,
red-cell adjudication); the estimator, event log and projection modules with their test suite; the
private-corpus pre-publication gate; and the executable models behind the programme's threshold
arithmetic. The findings documents, decision records, experiment register and the append-only
trajectory log are in the tree, including the withdrawal in §5 in its original position beneath the
claim it withdraws.

**Published in aggregate.** The two contingency tables (Table 2) and every rate derived from them
(Table 3), the blind grading tallies (Table 5), and the aggregate positive-control counts for the
revert detector.

**Not released, and it cannot be.** The two measurement corpora are private commercial
repositories. Per-pull-request records, file paths, check names, pull-request titles and commit
subjects are excluded from the repository by policy and by a gitignore, and are excluded from this
paper. Four raw artefacts — the two pull-request record sets, the audit sample and the re-fetched
check evidence — live gitignored on one machine, which means **no number in Table 2 or Table 3 can
be reproduced from the public tree alone**. A reader can reproduce the arithmetic from the published
cells, and nothing further. Two independent auditors reported those artefacts as absent, which is
itself a reproducibility finding: in a privacy-constrained programme the most decision-relevant data
is data every scoped reader will report as missing.

A public replication on an agent-authored pull-request corpus is required before any of the §4
material is offered as a technical result.

---

## AI assistance and human accountability

**Joe Brown is the sole author, the accountable human, and the only submission principal.** No AI
system is an author.

Generative AI systems assisted materially with this work: Anthropic Claude models under the Claude
Code harness (ideation, literature research, methods, implementation, orchestration, analysis and
drafting, including this manuscript); Google Gemini models under the Cursor agent harness
(adversarial audit of documents and code, the pre-publication leak audit of §6, and blind grading in
§7.1); and OpenAI GPT models under the Codex harness (a numbers audit of the repository's claims,
and blind grading in §7.1). All access dates are 19–20 August 2026. The multi-agent structures
reported in §5, §6 and §7 are themselves the objects of study, and their provenance is recorded in
the repository's append-only trajectory log rather than reconstructed from memory for this
disclosure.

The following are stated as facts about this draft and not as claims of completed human review. Joe
Brown approved the research questions, the stopping rules quoted here and the withdrawal in §5. He
has not yet performed the final claim-by-claim, table-by-table review that this programme's own
publication policy requires before a formal submission, and this document is therefore a **draft,
not an approved manuscript**. Nothing in it has been submitted, transmitted or published outside the
authoring machine. Where this paper reports that a human check occurred, that check has a
first-party approval event in the repository; where it does not, the text says so.

---

## References

Read-depth flags per Table 6. arXiv identifiers are given as recorded in the programme's
bibliography.

1. Ao, R., Gao, S. & Simchi-Levi, D. *On the Reliability Limits of LLM-Based Multi-Agent Planning.*
   arXiv:2603.26993, 2026. [FULL]
2. Berg, S. *Condorcet's jury theorem, dependency among jurors.* Social Choice and Welfare, 1993.
   [STD]
3. Bommasani, R. et al. *Picking on the Same Person: Does Algorithmic Monoculture Homogenize
   Outcomes?* NeurIPS, 2022. [SNIP]
4. Bovens, L. & Hartmann, S. *Bayesian Epistemology.* Oxford University Press, 2003. [STD]
5. *Correlated Errors in Large Language Models.* ICML, 2025. [SNIP]
6. Eckhardt, D. E. & Lee, L. D. *A theoretical basis for the analysis of multiversion software
   subject to coincident errors.* IEEE Transactions on Software Engineering, 1985. [SNIP]
7. Guo, Y. et al. *Self-Authored Verification Is Unreliable in Heuristic Self-Improving Agents*
   (SEAL). arXiv:2607.24300, July 2026. [FULL]
8. Herbold, S., Trautsch, A., Trautsch, F. & Ledel, B. *Problems with SZZ and Features: An
   empirical study of the state of practice of defect prediction data collection.* Empirical
   Software Engineering; arXiv:1911.08938. [ABS]
9. Jwalapuram, P. et al. *The Illusion of Multi-Agent Advantage: Why Modern Agentic Systems Fail to
   Leverage Collective Intelligence.* arXiv:2606.13003, 2026. [FULL]
10. Kim, J. et al. *(Multi-agent architectures across 260 configurations.)* Nature Machine
    Intelligence, 2026. [FULL]
11. Kleinberg, J. & Raghavan, M. *Algorithmic monoculture and social welfare.* PNAS, 2021. [SNIP]
12. Knight, J. C. & Leveson, N. G. *An experimental evaluation of the assumption of independence in
    multiversion programming.* IEEE Transactions on Software Engineering, 1986. [SNIP]
13. Kohli, S. *Nine Judges, Two Effective Votes: Correlated Errors Undermine LLM Evaluation Panels.*
    arXiv:2605.29800, May 2026. [FULL]
14. Kuai, et al. *How Independent are Large Language Models? A Statistical Framework for Auditing
    Behavioral Entanglement and Reweighting Verifier Ensembles.* arXiv:2604.07650, 2026. [ABS — full
    text not obtained; no claim in this paper rests on it]
15. Ladha, K. K. *The Condorcet jury theorem, free speech, and correlated votes.* American Journal
    of Political Science, 1992. [STD]
16. Lee, Y., Nair, R., Zhang, Q., Lee, K., Khattab, O. & Finn, C. *Meta-Harness: End-to-End
    Optimization of Model Harnesses.* arXiv:2603.28052; COLM 2026. [FULL]
17. *N-Version Programming with Coding Agents.* arXiv:2606.20158, 2026. [SNIP]
18. Neyman, J. & Pearson, E. S. *On the problem of the most efficient tests of statistical
    hypotheses.* Philosophical Transactions of the Royal Society A, 1933. [STD]
19. Qwen Team. *The Verification Horizon: No Silver Bullet for Coding Agent Rewards.*
    arXiv:2606.26300, June 2026. [FULL]
20. Rogan, W. J. & Gladen, B. *Estimating prevalence from the results of a screening test.* American
    Journal of Epidemiology, 1978. [STD]
21. *SWE-Bench+: Enhanced Coding Benchmark for LLMs.* arXiv:2410.06992, 2024. [ABS]
22. Tantithamthavorn, C., McIntosh, S., Hassan, A. E., Ihara, A. & Matsumoto, K. *The impact of
    mislabelling on the performance and interpretation of defect prediction models.* ICSE, 2015.
    [SNIP]
23. Tran, D. & Kiela, D. *Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning
    Under Equal Thinking Token Budgets.* arXiv:2604.02460, 2026. [SNIP]
24. Whewell, W. *The Philosophy of the Inductive Sciences, Founded Upon Their History*, Vol. II.
    London: John W. Parker, 1840; restated in *Novum Organon Renovatum*, 1858, pp. 70–71. [STD]

---

*Draft. Nothing in this document has been submitted or published. Private-corpus content is
excluded by policy and by an automated pre-publication gate; the measurement repositories are
referred to as Repository A and Repository B in all tables.*

# The brainstorm agenda

**Brainstorming remains open, but an explicitly unapproved draft specification now records
the current boundary for attack. It grants no implementation authority.** [asserted]

**Status as of 19 Aug 2026.** Several are now closed by ADRs; several others are not
argument questions at all and have become entries in
`../10-research/experiment-register.md`. Check both before reopening anything here.

| Q | Status |
|---|---|
| Q1 novelty | Partly closed — arXiv:2605.00663 cleared (cs.RO, no labels). Field crowded; see `../10-research/competitive-landscape.md` |
| Q2 β measurable | Answered analytically in ADR-0002; **EXP-01** decides it empirically |
| Q3 bimodal difficulty | **Closed.** β* is distribution-free: β* = (1−α)·e^(−kΔ). ADR-0002 |
| Q4 what v0 optimises for | Answered: both. Bias warning recorded in ADR-0002 |
| Q5 adapter surface | **Closed for first pass** — EXP-05 DONE; continue measuring maintenance drift |
| Q6 ticket store | **Closed** — ADR-0006 |
| Q7 exogenous signal | **Closed** — ADR-0010 |
| Q8 meeting primitive | **Closed** — ADR-0011 (became an evidence merge) |
| Q9 per-task vs per-step | ADR-0009 PROVISIONAL; **EXP-06** decides |
| Q10 β scalar or vector | **Closed** — ADR-0012; **EXP-03** refines |
| Q11–Q12 dispersion gate | **EXP-09** |
| Q13 executable-model ratchet | **EXP-10** |
| Q14 Inquiry tier in v0 | Judgement call — still open |
| Q15 / Q23 scope | **Closed by Joe's EXP-16 decision** — full candidate list, sequenced; three months below 10 trajectory hours/week reinstates the narrow provisional |
| Q16 surface | **Closed** — ADR-0007 |
| Q17 evaluation | **Closed** — ADR-0013 |
| Q18 name | **Closed** — ADR-0008, Consilience |
| Q19 what was missed | Open — first cold local-model pass used no repository tools and produced no verifiable finding; a capable different reader is still required [measured] |
| Q20 model library | **Closed** — ADR-0005: wrap, don't build |
| Q21–Q22 feasibility & β composition | **EXP-11** |
| Q24 β outside coding | **Open — Tier 0 for the expanded scope.** Added 19 Aug 2026 |
| Q25 reasoning layer on reasoning models | Open — see `../20-design/reasoning-layer.md` |
| Q26 agent identity, personality and real-time collaboration | Open — **EXP-24–26** separate accountable identity, persona effects and typed control |

What genuinely remains a user preference in this agenda is **Q14**. [asserted] Q19 needs a
different reader rather than a preference, and Q24–Q26 need evidence rather than agreement.
[asserted]

---

Ordered by how much the answer changes the shape of the thing. Q1–Q4 are existential:
if they go badly, the project is different or shouldn't exist.

---

## Tier 0 — could kill or reshape the project

**Q1. Is the β thesis actually novel?**
`literature-review.md` §2 and the summary table flag two unread threats:
`Affordance agent harness: verification-gated skill orchestration` (arXiv:2605.00663) and
Meta-Harness (COLM 2026). Read both properly. If verification-gated routing with measured
verifier reliability is already published, this project needs a different centre.
*Try hard to kill the idea before building on it.*

**Q2. Is β measurable in practice, at solo-founder data volumes?**
β = P(automated checks accept | artifact is actually bad). Estimating it needs *human
verdicts* on diffs the checks passed. How many samples before the estimate is useful?
What's the confidence interval after 50 diffs? Does it drift faster than you can measure it
when models update underneath you? **If β needs 500 human-labelled diffs per repo, the
product doesn't work.** Consider: conformal / PAC-style bounds, hierarchical pooling across
repos, using near-miss signals (reverted commits, follow-up fix commits, escaped bugs found
later) as cheap proxy labels.

**Q3. Is the difficulty distribution smooth or bimodal?**
Every threshold in `findings.md` assumes `Beta(2,2)`. Real coding tasks may be bimodal —
mostly trivial, occasionally very hard, little in between. If so, smooth thresholds become
cliffs and "route cheap, escalate on failure" may collapse into "route cheap on the trivial
mode, never on the hard mode", which is a much simpler product. **Re-run
`experiments/simulations.py` with a bimodal `d` before anything else.**

**Q4. Given full-OSS with no revenue, what is the actual success condition?**
Not a business-model question — a scoping one. If nobody is paid, the binding constraint is
Joe's hours. What is the smallest thing that is worth a stranger's `npm install`? What is
the smallest thing that makes Joe's own week better? Are those the same artifact? If not,
which one is being built?

---

## Tier 1 — architecture-defining

**Q5. Where exactly is the meta-harness boundary?**
Which agents are adapted first, and what is the minimum common interface? Claude Code,
Codex, opencode and Antigravity CLI have different session models, permission models and
output formats. Is the adapter surface "spawn, feed a ticket, collect a diff", or richer?
What breaks when one of them changes?

**Q6. What exactly is the native ticket store?**
Joe: a PM system built natively for agents, not ClickUp/Trello/Linear. Proposal on the table:
local-first, git-backed or SQLite, diffable, offline, thin read UI, optional one-way sync
adapters out to Linear/ClickUp. **Decide: git-backed files or SQLite?** Git gives the
trajectory record free (every state transition is a commit) and makes tickets reviewable;
SQLite gives query performance and transactional integrity under parallel writes. Do
parallel agents writing to a git-backed store deadlock or conflict?

**Q7. What is the exogenous signal in each multi-agent structure?**
Required by the theorem (`literature-review.md` §3). For each proposed structure —
critic tier, meeting, parallel worktrees — name the *new* information it introduces.
If it only reprocesses shared context, it is provably lossy. **Structures that cannot name
their exogenous signal get cut.**

**Q8. What is the meeting primitive, precisely?**
Sketch on the table: named caller, stated question, named exit artifact, hard token budget
and turn cap, quorum rule, durable replayable transcript. Missing: what happens on budget
exhaustion? Who arbitrates a deadlock? Can a meeting spawn a meeting (and should recursion
be banned outright)?

**Q9. Does the cascade run per-task or per-step?**
Route once per ticket, or re-evaluate at each tool-call boundary within a run? Per-step is
finer-grained and might capture more of the gain, but multiplies verifier invocations and
makes the trajectory record much larger.

**Q10. What counts as "the verifier" per repo?**
Tests, typecheck, build, lint, custom invariant probes — these have very different β.
Is β one number per repo, or a vector per check-class? Does the harness compose them
(all-must-pass) or weight them?

---

## Tier 2 — the Inquiry tier

See `20-design/inquiry-tier.md` for the current sketch.

**Q11. Is the four-gate trigger implementable cheaply?**
Reversibility, blast radius, prior dispersion, formalizability. Dispersion needs N cheap
model samples plus a semantic comparator — what does that actually cost per decision, and
what N is enough?

**Q12. How is gate 3 calibrated?**
Dispersion among cheap models measures whether *those models* know, not whether the question
is open. Contested-but-well-documented topics will scatter and trigger waste. Needs its own
measurement loop: log every escalation and whether the inquiry changed the decision.

**Q13. Should executable decision models be CI-enforced?**
The proposal: an ADR ships with a runnable model; CI re-runs it; a sign flip fails the build.
Is that genuinely useful or ceremony? What is the maintenance cost when the model's
dependencies rot?

**Q14. Does the Inquiry tier belong in v0 at all?**
It is the most intellectually interesting part and possibly the least urgent. Argue both sides.

---

## Tier 3 — scope and sequencing

**Q15. What is in v0, honestly?**
Candidate: β-meter + cascade + parallel worktrees + budget primitives + critic tier.
Everything else deferred. Is even that too much for one person?

**Q16. Which single interaction surface?**
CLI, TUI, or local web? One only, until the core loop is proven.

**Q17. What is the eval harness for the harness itself?**
Meta-Harness used Terminal-Bench. What does this project measure itself against, and how
does it avoid the trap of optimising a benchmark instead of Joe's actual work?

**Q18. What is the name?** — **CLOSED.** Consilience. See `../decisions/0008-*`.
Trademark clearance outstanding (folded into the `docs/legal/README.md` review).

**Q19. What was missed?**
The design position in this repo had one reviewer, in one session, with a declared conflict
of interest. What has been systematically overlooked because a single model with a single
framing produced all of it?

---

## Tier 4 — the model library (ADR-0005)

**Q20. Build it, or wrap Ollama / LM Studio?**
Check this before designing anything. If an existing tool already does hardware-gated
discovery well enough, wrapping it beats building it, and this is the likeliest outcome.

**Q21. Predict, measure, or both — and what does "reliably" mean numerically?**
ADR-0005 proposes predict-to-shortlist, measure-to-confirm, with bands (Comfortable /
Tight / Predicted-only / Infeasible). Needs numbers: what tok/s floor, at what context
length, with how much headroom? A calibration run costs the user time on first use — is
that acceptable, and can it be amortised or backgrounded?

**Q22. How does the library compose with β?**
The interesting output is not "can you run this" but "should you route to it, given your
repo's verification quality". At a 0.42 capability gap, β* is 0.033 — so for many users the
honest answer is "you can run it, and you shouldn't route to it". How is that communicated
without making the feature feel useless?

**Q23. Does this belong in v0 at all?**
It is a substantial cross-platform feature for a pre-v0 project with one maintainer.
Argue both sides. The cascade needs *a* cheap tier, but that could initially be a cheap API
model with no library at all.

---

## Tier 0 addition — the expanded scope (added 19 Aug 2026)

**Q24. Does the β thesis survive in domains without an automated oracle?**
The product scope is now general agentic work (chats, projects, tasks, scheduled,
background, parallel workflows — see `../20-design/work-modes.md`), with coding as v0.
Coding is v0 *because* it is the only domain with a cheap automated oracle: tests,
typecheck, build. **β = P(checks accept | artifact bad) is only defined where checks
exist.** For a strategy memo or a research task there is no test suite. Either β is
unmeasurable there — and the architecture has no centre outside coding — or something
replaces the oracle: human verdicts alone, which ADR-0002 already shows need 50–200
labels per verifier and are the scarcest input in the system; or weaker proxies
(citation checks, schema validation, consistency probes) whose own β would be high and
unmeasured. **This is the single biggest risk to the expanded scope.** Do not answer it
now; do not let any expansion document pretend it is answered. The gate for any
non-coding mode is an explicit answer here, with evidence.

**Q25. Does a reasoning layer help or hurt on models that already reason?**
The harness must never double-apply scaffolding: reasoning-trained models can degrade
under imposed CoT structure, non-reasoning models can benefit, and the middle case —
native reasoning present but weak for a task class — is genuinely unclear. Detection and
non-duplication is the hard part, not the scaffolding itself. See
`../20-design/reasoning-layer.md`, including why "scaffolding narrows Δ" did **not**
survive scrutiny (it changes the competence curve's *slope*, not its position, and its
β* effect flips sign with the task distribution).

**Q26. Which parts of agent identity and team culture improve outcomes, and which are only
presentation?**

Stable logical identity, display persona, runtime identity, work role, authority and
provenance are different dimensions. [asserted] Human-team evidence favours unique
information, communication quality, expertise location, protected dissent and intermittent
independent work more strongly than generic communication frequency or personality
archetypes. [cited] LLM persona evidence does not justify treating an “expert” or warm
persona as capability. [cited]

EXP-24 tests attribution and handoff comprehension from stable logical identity; EXP-25
separates personality complementarity from different evidence classes; EXP-26 tests native
typed control against transcript injection. [asserted] See
`../10-research/agent-identity-and-collaboration.md`.

**Q27. Which prompt and feedback interventions improve verified work without teaching false
compliance?**

Current provider guidance supports removing repeated procedural scaffolding while retaining
an explicit task contract, but it does not support one universal prompt profile. [cited]
Generic praise has no established verifier-level benefit, while unsupported correction can
move a model away from a previously correct answer. [cited] EXP-28 crosses prompt detail
with neutral, generic-praise, calibrated-constructive and mildly scathing feedback on both
real defects and deliberately false diagnoses. [asserted] See
`../10-research/prompt-context-and-feedback.md`.

**Q28. When does model or harness activity become counterfactually unnecessary work?**

Current evidence documents iterative code bloat, deletion avoidance and task-dependent
multi-agent overhead, but does not establish one universal model preference for “more”.
[cited] EXP-29 measures whether code, scope or fan-out can be removed without changing the
external verifier outcome, and reports the interaction by exact model–harness composition.
[asserted] See `../10-research/unnecessary-scope-and-fanout.md`.

**Q29. How much usable context does each orchestration role require?**

The current senior-orchestrator default is subscription-backed Claude Code Opus 5, while
OpenRouter Gemini 3.7 Flash at high effort is a candidate for bounded middle-management
delegation. [asserted] Both providers advertise roughly one-million-token capacity, but
advertised length does not establish state retention or decision quality. [cited] ADR-0030
separates hard context fit from measured capability, and EXP-30 compares full relevant
records with compact manifests, retrieval and bounded contracts. [asserted]

**Q30. Is β stationary, and is its oracle independent of the thing it grades?**

β is defined as the rate at which the automated checks accept an artefact the human verdict
rejects. Two assumptions were never stated. First, that the human verdict is an independent
test: Zhang, Liao & Bellamy measured no complementarity between human and model and
attributed it to aligned error boundaries, so the two tests fail on overlapping inputs and β
understates a joint error. [cited] Second, that the human verdict is stationary: Shen & Tamkin
found debugging — the capability β leans on — degrading most under assistance, Budzyń et al.
measured expert deskilling within three months, and Lee et al. measured earned trust reducing
critical engagement. [cited] Together those give the β-drift hypothesis: β measured against a
human verdict should rise over months of assisted work even with the checks held fixed.
[asserted]

This is Tier 0. If β is non-stationary, it is a moving target rather than a property of the
verifier, and the reliability claim the whole project rests on needs restating. EXP-32
measures the mechanism, not β itself, and is n=1. See
`../10-research/human-success-and-the-human-side-of-beta.md`.

**Q31. What is the honest counterfactual for a meta-harness?**

The field's positive results compare AI against no AI. The realistic comparison for
Consilience is against a well-configured Claude Code, and the one matched study of that
transition measured +3.1% commits and −6.3% lines for repositories that had already adopted
AI IDEs. [cited] Meanwhile the effect's sign is set by task selection — +55.8% on a greenfield
toy task, −19% on real issues in a developer's own mature repository — so a harness that
evaluates itself on curated tasks will measure the wrong regime. [cited] ADR-0013 already says
evaluate on repository history; this is independent support and a sharper reason. [asserted]

**Q32. Can the harness close the QA-automation gap, and is there a measurable claim in it?**

Joe, 20 August 2026: *"QA and QA automation is a huge gap in capability of coding and product
and GTM agents. A real and deeply frustrating bottleneck for developers and a big opportunity
to solve"* — including synthetic data generation, synthetic users and sandboxes, with *"a
dedicated and extensive R&D pipeline including experimentation and simulations"*. [asserted]

Nothing in this repository addresses it. [measured] The connection to the thesis is direct and
is the reason it is Tier 1 rather than a feature request: **β is the rate at which automated
checks accept a bad artefact, and QA automation is the business of building those checks.**
Manufacturing an oracle where none existed is the same mechanism that let fuzzing find defects
experts missed — cheap iteration against a cheap oracle, not insight. [cited]

Three questions must be answered before any design, and the second is the dangerous one:

1. What different class of facts does a synthetic user introduce that a test suite does not?
   If none, ADR-0010 cuts it. [asserted]
2. **Is generated-test acceptance simply β under another name?** A harness that writes its own
   tests and then measures how often those tests accept bad work is grading its own homework,
   and EXP-13 already pre-registers the hazard that a system edits its tests into agreement
   with itself. [cited]
3. Where is the human verdict in a synthetic-user loop, given EXP-01 found verdicts to be the
   scarcest input in the system? [measured]

Do not write a QA design document before these are answered. [asserted]

## Method note for the brainstorm

Joe has asked for a multi-agent approach to research → brainstorm → spec → plan.
The theorem in `literature-review.md` §3 constrains that: parallel *discovery* over
independent sources adds exogenous signal and is justified; parallel *deliberation* over the
same shared context is provably lossy. The pattern that worked in his own
prior codebase assessment — independent discovery agents, then independent verification of
every lead, then a fabrication audit — respects the theorem. Reuse that shape.

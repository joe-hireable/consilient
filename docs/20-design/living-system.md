# The living system — self-extension, self-improvement, and scientific reasoning

Status: `[asserted]` design position, 19 Aug 2026. Grounded in the prior art below.
This document formalises Joe's requirement that the harness be "living, breathing" — that it
develops itself, learns, builds knowledge and memory, personalises, creates capabilities it
lacks, and reasons the way a scientist does rather than the way "reasoning" currently means
in LLM marketing.

---

## The short version

The vision is legitimate and largely unoriginal in its parts. Self-improving agents are a
mature 2026 field with strong published results. **But every system in that literature
validates its self-modifications against a benchmark, and none of them measures whether that
benchmark can be trusted.**

That is β. Which means the project's existing thesis is not a separate feature from the
living-system vision — **it is the missing safety property of the entire self-improving-agent
literature**, and the two are one idea at different levels.

---

## What already exists (do not rebuild)

| System | What it does | Acceptance signal |
|---|---|---|
| **Darwin Gödel Machine** (Zhang, Hu, Lu, Lange, Clune — ICLR 2026) | Agent rewrites its own source; archive of descendants; open-ended tree search | SWE-bench 20.0% → 50.0%; Polyglot 14.2% → 30.7% |
| **SICA** (Bristol / iGent, arXiv:2504.15228) | No meta/target distinction — agent edits its own codebase for score, cost and speed | 17% → 53% on a SWE-bench Verified subset |
| **Huxley–Gödel Machine** (ICLR 2026) | Argues benchmark score ≠ self-improvement capacity; introduces a qualitative measure | tree search over descendants |
| **HyperAgents / DGM-H** (Meta, arXiv:2603.19461) | The *meta*-level process is itself editable | archive, population-based |
| **Gödel Agent** (ACL 2025) | Runtime self-modification by monkey-patching; **a Verification agent checks modifications against safety invariants before applying** | high-level objectives |
| **Live-SWE-agent** (Xia et al.) | Starts from a shell-only scaffold and **synthesises new tools at runtime** when the toolchain falters | empirical success rate + execution cost |
| **AFlow** (ICLR 2025 Oral) | MCTS over agentic workflow space | benchmark |
| **AlphaEvolve** (DeepMind) | Coding agent for scientific and algorithmic discovery | evaluator functions |
| **The AI Scientist v1/v2** (Sakana) | Automated open-ended scientific discovery; agentic tree search | workshop-level review |
| **SkillOpt** (arXiv:2605.23904) | Skill document as external state of a frozen agent; edits accepted only on held-out validation improvement | held-out score |
| **ACE** (ICLR 2026) | Generator / Reflector / Curator; context as evolving playbook, no gradient updates | +10.6% agent, +8.6% finance |
| Survey | *Self-Improvements in Modern Agentic Systems* (arXiv:2607.13104) | — |

**Conclusion: build none of these.** Curate them.

---

## The gap, stated precisely

Schmidhuber's original Gödel machine required a **proof** that a self-modification increases
expected utility. DGM's contribution was to concede that such proofs are intractable and
substitute **empirical validation**.

That substitution is the whole field's foundation, and it has an unexamined premise:

> **Empirical validation is only as reliable as the validator.**

Every system above accepts a self-modification when a test says it is better. None measures
the rate at which that test says "better" about something worse. In a self-improving system
that error does not merely occur — **it compounds**, because each generation builds on an
archive selected by the same faulty signal. A ratchet with a slipping pawl runs backwards
while appearing to advance.

HGM already gestures at this from a different angle: it explicitly rejects the assumption
that higher benchmark scores correspond to greater self-improvement capacity. It does not,
however, measure the acceptance signal's error rate.

**Consilience's contribution, if it has one: self-modification gated by a *measured* verifier
false-accept rate.** β is not a feature alongside self-improvement. It is the property that
makes self-improvement safe rather than merely fast.

This is also why `CONSILIENCE.md`'s third clause matters — *"a test of the truth"*. A
project named after a test of truth, building a system that improves itself by testing its
own changes, is obliged to measure the test.

---

## The four capabilities Joe described, mapped

### 1. Self-extension — building tools and MCPs it lacks

Precedent: Live-SWE-agent synthesises tools at runtime from a minimal scaffold when the
toolchain falters. Voyager built skill libraries. This is established.

Design position:
- **Tool synthesis is triggered by failure, not by planning.** A tool is written when the
  current toolchain demonstrably cannot do the thing — which is an observation, not a guess.
- **Disposable by default, promoted by evidence.** A synthesised tool starts session-scoped.
  It is promoted to persistent only when its usage count and success rate clear a threshold.
  This is `0012`'s retrospective-RoL pattern, applied to tools: gate on evidence, not on a
  pitch.
- **Custom MCPs are the same mechanism at a different scope** — a persistent tool with a
  network boundary. Same promotion rule, plus the credential rule below.
- **Every synthesised tool ships with the test that proves it works** (invariant I2). A tool
  the system cannot verify does not get promoted.

### 2. Credentials and accounts

Joe's constraint: get users to create accounts or provide credentials only where strictly
required and unachievable autonomously.

- **Never in chat** (`0004` neighbourhood; the earlier Gemini design got this wrong). OS
  keychain or OAuth device flow.
- **Ask once, at the boundary, with the reason.** "I need a Companies House API key to do X;
  here is where to get one" — not a generic credential prompt.
- Autonomous account creation is out of scope. It is prohibited by most terms of service and
  it is the kind of capability that turns a useful tool into a liability.

### 3. Native capability — code, files, spreadsheets, experiments

Table stakes, and already solved. Claude Code and every comparable agent execute code and
write files; the `anthropics/skills` ecosystem covers docx/xlsx/pdf. Under `0016` these are
**consumed, not built**. The only thing worth building here is the *decision* about when to
run an experiment rather than answer — which is the Inquiry tier.

### 4. Scientific reasoning — hypothesise, experiment, prove or disprove

This is `docs/20-design/inquiry-tier.md`, and Joe's framing sharpens it. The tier already
specifies: T0 assert → T1 ground → T2 model → T3 measure, gated by reversibility, blast
radius, **prior dispersion** (do independent samples disagree — a measurable proxy for "the
training data doesn't cover this") and formalizability.

What Joe's framing adds, and it should be written in: **the escalation ladder ends at the
user, and the user is the last resort — except where their opinion is constitutive.**

Two different reasons to ask a human, and conflating them is a design error:

| Reason | Example | Correct behaviour |
|---|---|---|
| **Epistemic** — the system does not know | "which retrieval strategy is faster?" | **Do not ask.** Run T2/T3. Asking is a failure of the ladder. |
| **Preferential** — the answer is the user's to give | "should this project be MIT or AGPL?" | **Ask immediately.** No amount of experiment substitutes for a value judgement. |

A system that asks epistemic questions is lazy. A system that answers preferential ones is
overreaching. The router between them is a first-class component, not a prompt.

---

## Personalisation — the weakest-evidenced part

Joe wants it to personalise its communication, capabilities and specialisms to its user.

**Honest position:** this is the least supported claim in the whole vision. The
self-improving literature optimises against benchmarks; there is no benchmark for "suits
this user better", and the obvious proxies — user acceptance, thumbs-up — are exactly the
signals that produce sycophancy when optimised against.

What is defensible now:
- **Personalise from the verdict data we already collect.** `0007`'s merge-time verdict
  (accepted / edited / rejected) is a real behavioural signal about this user's standard,
  and it is already the β label. Reuse it; do not invent a preference channel.
- **Personalise the routing, not the personality.** Learning that this user's repo has low β
  and tolerates cheap-tier routing is genuine personalisation with a measurable target.
  Learning to phrase things the way they like is not measurable and invites drift.
- **Do not optimise for user approval.** State this as a prohibition. A system that learns
  what its user likes to hear becomes worse at telling them what they need to hear, and this
  project's value is disproportionately in the second.

---

## Safety constraints, taken from the literature rather than invented

HyperAgents' own risk list, and the mitigations the field converged on:

1. **Restrict what can self-modify.** Not everything is in scope. Proposal:
   skills, tools, prompts, routing config — **yes**. Verification layer, budget primitives,
   permission model, the β-meter itself — **no, ever**. A system that can edit its own
   verifier can edit away the evidence that it is getting worse.
2. **Stage through sandboxes.** Synthesised tools run in the quarantine tier (`0005`'s
   sandbox model, kept from the Gemini session).
3. **Human approval for high-impact changes**, defined by the reversibility gate already in
   the Inquiry tier.
4. **Log every modification with version history.** The append-only trajectory record
   (`0006`) already provides this; self-modifications are just another event class.
5. **Gödel Agent's pattern is the right one**: a verification agent checks modifications
   against safety invariants *before* applying. Note this passes `0010` — it runs the checks,
   so it holds a different class of facts.

And one honest limit, from the literature:

> **No deployed system does recursive self-improvement.** What ships is single-level: a fixed
> improvement operator makes the task layer better, but the operator does not itself get
> smarter. HyperAgents attempts the second level; results are early.

Consilience should not claim otherwise, in documentation or marketing.

---

## What this means for scope

Nothing in this document belongs in v0. `0015`'s gates come first, `findings.md`'s β
measurement comes first, and the experiment register's EXP-01 and EXP-05 come first.

But it changes what v0 is *for*. The trajectory log, the verdict prompt and the β-meter are
not just a routing feature — **they are the substrate a self-improving system needs in order
to improve safely.** Building them first is the correct order regardless of how far the
living-system ambition goes.

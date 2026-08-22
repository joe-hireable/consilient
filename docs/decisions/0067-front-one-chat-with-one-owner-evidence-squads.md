# 0067. Front one chat with one-owner squads whose added roles bring distinct evidence

- **Status:** PROVISIONAL — EXP-80 can kill it and can confirm only its frozen v0 task mixture
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (product direction only, quoted in the dispatch brief); Codex dispatch
  `20260822T111814-b49738fe69` (provisional mechanism pending EXP-80)
- **Inquiry tier reached:** T2 model; T3 registered as EXP-80, not run
- **Executable model:** `0067-model.py` — encodes the sign and regime boundaries; it does not
  estimate the world values that EXP-80 must measure

## Update: 2026-08-22 — composition-and-beta clause superseded in part by ADR-0077

[ADR-0077](0077-separate-candidate-exposure-from-verifier-fusion-and-measure-both.md) preserves this
ADR's one-Owner and distinct-anchor composition rule but corrects candidate sizing. Component
verifier passes on one bad artefact form an intersection; independently shippable candidate failures
form a union. Until candidate dependence is measured under a frozen protocol, routing uses the
distribution-free ceiling `n_attempt_max = floor(epsilon / q_upper)`, setting
`q_upper := beta_upper` when candidate badness is unmeasured. [algebra] The current result at
`epsilon = 0.40` remains one candidate; below `beta_upper` it is zero, not one. [measured] [algebra]

## Context

A different model family is **not**, by itself, a different class of facts. ADR-0054 attaches
evidence credit to the truth-relevant external anchor, never to a vendor or model name; a
cross-family replication is computational diversity until each arm independently reaches a
different anchor. [cited]

Joe Brown specified the product direction on 22 August 2026: one chat should front an organisation
of collaborating specialists rather than one model. He did not specify the mechanism below; that is
this dispatch's provisional design. [measured]

Naive multiplication is unsafe. EXP-16's single agent won 9 of 12 blind judgements while its Owner
meeting won 2 of 12 at 4.8 times the tokens and 3.7 times the wall-clock, and the current
`--fan-out` runs children sequentially in one working directory and calls case-normalised stdout
equality agreement. [measured] A useful squad must therefore add facts, preserve independence, and
produce one accountable candidate rather than recreate a meeting or a vote. [asserted]

This is a protocol and future schema decision with a wide blast radius, but not yet a product
implementation decision. [asserted] The implementation remains blocked on the registered
measurement because a failed result would remove squad-specific orchestration rather than merely
tune it. [asserted]

### Incumbent bar and search

Primary sources were searched on 22 August 2026 across arXiv, *Nature Machine Intelligence*, METR
and Anthropic using, among others, `multi-agent specialist agents single agent equal budget
benchmark 2026 expert decomposition`, `multi-agent SWE-bench Verified single-agent`, and
`SWE-bench maintainer verdict human evaluation passing PRs merge 2026`. [measured]

The strongest controlled comparison located was Kim et al. (2026): 260 configurations with prompts,
tools and maximum per-system compute matched. It found task-dependent gains and losses, every tested
multi-agent architecture degraded on SWE-bench Verified, and realised reasoning turns were 1.6 to
6.2 times the single-agent baseline. [cited] The strongest specialist result inspected was
Jwalapuram et al.'s context-isolated, deterministically synthesised Expert-MAS on a deliberately
separable synthetic task; their generic automatic multi-agent comparators generally lost to a
strong single-agent baseline. [cited]

Kim et al. did not collect a blind maintainer verdict, and Jwalapuram et al.'s positive specialist
result was not real repository work. [cited] METR separately found automated SWE-bench scores about
24 percentage points above normalised maintainer merge judgements, so verifier success cannot stand
in for human acceptance. [cited] No inspected source combined matched realised budget, a strongest
single baseline, isolated specialist anchors, an executable verifier and a blind human verdict in
the bounded search above. [measured] The bar is therefore that composite, and EXP-80 tests whether this
protocol clears it rather than asserting that it does. [asserted]

## Decision

Consilient will present one conversational front door backed by the **smallest evidence-grounded
squad** needed for the task. One accountable Owner produces one candidate; other members may acquire
facts but do not vote on the answer. The default composition is one. A member is added only when its
frozen manifest names a truth-relevant anchor unavailable to the current composition and the fact
could change the scoped decision. [asserted]

### Role contracts

These are allowed contracts, not a mandatory seven-member team. A task uses only the smallest
subset whose evidence manifests pass the composition rule. [asserted]

| role | what it does | distinct class of facts it brings | what it may never decide |
|---|---|---|---|
| **Owner** | freezes the brief, authority, budget and verifier; synthesises one candidate | the task contract and authority record; this is governance provenance, **not** consilient evidence | may not invent evidence, erase dissent, change the verifier after results, cross a gate, or decide a principal-only matter [asserted] |
| **Domain specialist** | answers a bounded domain question | a named primary source, corpus, database or public API that no other member reads | may not accept the final candidate or extrapolate beyond the named source [asserted] |
| **Executing verifier** | exercises the artefact rather than reviewing its prose | observed test, compiler, browser, sensor or other executable-oracle output under a frozen contract | may not alter the oracle after seeing an outcome or decide human preference [asserted] |
| **Adversary** | tries to refute one material claim | executed counterexamples, negative tests, mutations or hostile inputs absent from the author path | may not veto by rhetoric, rewrite the objective or count an unexecuted objection as evidence [asserted] |
| **Replicator** | independently reacquires a claimed result | a second truth-relevant anchor acquired in an isolated directory and hidden from the first arm; model family is metadata only | may not see another arm before freezing its result or adjudicate between arms [asserted] |
| **Experimenter** | pre-registers and runs a decisive comparison | controlled-arm measurements produced after a frozen procedure and stopping rule | may not move the stopping rule, omit adverse outcomes or turn a result into authority it did not measure [asserted] |
| **Principal** | supplies preference, permission, credentials or ground truth only a person can supply | the person's own preference or authority, where that person is the sole valid source | may never be impersonated; no agent may launder its choice into the principal's name [asserted] |

An asserted label, a job title, a different prompt, or a different model family does not satisfy the
third column. [cited] The Owner's governance record also does not count as an independent induction
about the artefact. [asserted]

The default one-harness composition co-holds Owner and generalist evidence-acquisition contracts and
receives every allowed source and tool. It is the strongest baseline, not a claim of consilience;
co-holding two labels never creates a second induction. [asserted] A separate member is justified
only when structural isolation around a material anchor is required. [asserted]

### Composition and beta

Composition is decided once per task and verifier contract. Start with one Owner. Add one role only
when its manifest passes all three tests: its anchor is concrete, no existing member has access to
that anchor during independent acquisition, and its possible finding would change the decision.
Two members therefore require one additional material anchor; five require four. If any added role
can be removed without changing accessible facts, remove it. [asserted]

Every assigned anchor is identified before execution by its kind, canonical URI or verifier-contract
identifier, and content SHA-256; dynamic responses add acquisition time and response SHA-256. The
shared frozen brief is governance input and is not an anchor. Two roles are not independent when an
assigned identifier or content hash overlaps, one anchor is derived from the other, or an access
record shows either role read the other's source or output before sealing. [asserted]

Headcount and verifier exposure are different quantities. Evidence-acquisition members may feed one
Owner, one candidate and one verifier exposure. If multiple candidates can independently pass and
ship, each is an attempt and, under ADR-0051's independent-attempt assumption, the existing ceiling
applies:

`P(bad ships) = 1 - (1 - beta)^n`, so
`n_max = floor(log(1 - epsilon) / log(1 - beta_upper))`. [algebra]

At EXP-47's measured beta interval, `n_max = 1` for every exposure ceiling at or below `0.40`.
[measured] [algebra] An unmeasured beta remains a refusal in `routing.py`, not permission to assume a
safe value. [measured] This ADR therefore authorises no automated multi-candidate acceptance; a
squad may have several evidence roles only while it emits one supervised candidate against one
frozen verifier contract. [asserted] Beta conditions candidate exposure, not headcount. [algebra]
Role count remains governed by distinct anchors and EXP-80's measured value/cost result. [asserted]
Positive correlation between candidate false accepts can make the independence formula conservative,
but arbitrary dependence is not licensed; a candidate ceiling is valid only for the verifier
contract and dependence assumption under which beta was measured. [algebra] [asserted]

### Collaboration and disagreement

1. **Freeze.** The Owner records the task, authority, expiry default, total budget, verifier,
   candidate ceiling, required roles, evidence anchors and owned paths before work begins.
   [asserted]
2. **Acquire independently.** Each non-Owner works from a separate directory or immutable snapshot,
   receives only its assigned sources and tools, and sees no other member's context, recall or output.
   Refusal and timeout are retained outcomes. [asserted]
3. **Seal.** Each member returns a position, evidence references, artefact or check output, limits and
   refusal state. The raw return is appended before synthesis. [asserted]
4. **Synthesise once.** Only after all returns are sealed does the Owner receive them and produce
   one candidate. The Owner must attach a disposition to every material conflict; it may not average,
   vote away or silently omit one. [asserted]
5. **Stop.** A squad may stop only when every required role has returned, refused or expired; the
   verifier result and budget are recorded; and each material conflict is marked
   `resolved_by_evidence`, `escalated`, or `recorded_unresolved`. [asserted]

If a required role refuses, expires or cannot acquire its anchor, the Owner may return an explanatory
report but no acceptance-eligible candidate. The work item terminates adverse, incomplete or
escalated; the missing role cannot silently become optional after the freeze. [asserted]

When members disagree, run a pre-registered experiment if a decisive test fits the remaining budget;
escalate if the unresolved fact is a principal-only choice, authority boundary or irreversible
action; otherwise return both positions and the consequence of each as unresolved. Dissent remains
in the trajectory after the Owner chooses. [asserted]

### Conversational surface

The chat reports the organisation in ordinary language: how many independent checks ran, what each
checked, what each found, whether anyone refused, and which disagreement remains. Model and harness
names stay in details; the visible distinction is the source or test, not the brand. [asserted]

The existing prototype grammar is reused behind the conversation: a calm workstream row for goal,
composition, state and last artefact; a causal timeline for evidence and refusals; and the four-part
human-action card for artefact/checks, what was tried, expiry default and cost without the user.
Those patterns exist in the repository prototypes. [measured] Applying them to squads is this ADR's
design choice. [asserted] No existing prototype implements intra-squad dissent, so the disagreement
summary is a new bounded view, not a claim about what the prototypes already provide. [measured]

### Reuse boundary

Future implementation must extend `scripts/dispatch.py`, `src/consilient/work_items.py`,
`coordination.py`, `recall.py` and `routing.py`; it must not create another orchestrator or a new
`consil` subcommand. [asserted] Existing work-item authority, path claims, bounded verbatim recall,
trajectory outcomes and beta ceiling are retained. [measured] Current `--fan-out` is a research
primitive, not a compliant squad, because its shared directory, sequential execution and exact-text
agreement cannot prove independent acquisition or preserve semantic dissent. [measured]

## Evidence

- `[measured]` EXP-16's strongest single-agent arm won 9/12 blind judgements; the Owner meeting won
  2/12 at 4.8 times the tokens and 3.7 times the wall-clock. The meeting mechanism was cut.
- `[measured]` The 21 August Cursor/Grok run used separate directories, recorded shared conclusions
  and preserved a later disagreement for the principal; it also exposed a shared blind spot in the
  mutation operator set.
- `[measured]` Source inspection on 22 August found reusable work-item, path-claim, recall,
  trajectory, fan-out and beta-ceiling primitives, but no isolated role manifests or dissent schema.
- `[algebra]` Additional people do not increase `n` when they feed one candidate; additional
  independently acceptable candidates do, under `1 - (1 - beta)^n`.
- `[cited]` Ao, Gao & Simchi-Levi (2026), *On the Reliability Limits of LLM-Based Multi-Agent
  Planning*, arXiv:2603.26993, show that delegation with the same information cannot beat the ideal
  central decision-maker; exogenous signals can move that boundary.
- `[cited]` Kim et al. (2026), *Capable language models can outgrow the benefits of collaboration*,
  *Nature Machine Intelligence*, tested 260 matched configurations and found task-dependent gains
  and degradation, with single-agent capability the most robust predictor recorded here.
- `[cited]` Jwalapuram et al. (2026), *The Illusion of Multi-Agent Advantage*, arXiv:2606.13003,
  found generic automatic multi-agent systems generally worse than a strong single-agent comparator,
  while explicit isolated specialist decomposition helped on a separable synthetic task.
- `[asserted]` Distinct anchors, sealed acquisition, one Owner and preserved dissent will transfer
  those bounded specialist gains to real coding work. EXP-80 is the killing test.

## Evidence against

- `[measured]` The best direct evidence in this repository favours one strong agent: EXP-16's single
  arm beat both group structures while using a fraction of their time and tokens. A squad may simply
  rename the failed meeting and add coordination loss.
- `[cited]` Ao, Gao & Simchi-Levi's bound makes the strongest theoretical objection: if the manifests
  do not introduce exogenous information, the organisation cannot beat a central decision-maker
  with the same facts.
- `[cited]` Kim et al. found every tested multi-agent architecture degraded on SWE-bench Verified,
  while Jwalapuram et al. found generic frameworks could cost roughly ten times a strong single-agent
  comparator. The positive specialist result was synthetic and deliberately separable.
- `[measured]` Independent families in this project still shared the same mutation-tool blind spot;
  directory isolation does not remove common training priors or common source defects.
- `[asserted]` An Owner can become the loudest-member bottleneck, manifests can falsely imply source
  independence, and a polished chat summary can manufacture trust while hiding review debt.
- `[asserted]` The evidence base is small, partly model-graded and drawn from this repository. It
  cannot justify a universal squad default, so one remains the default even if EXP-80 succeeds on
  the tested task families.

## Consequences

**Positive** — users get one conversational surface with visible provenance, refusal and dissent;
specialists are justified by new facts rather than headcount; beta constrains acceptance exposure.
[asserted]

**Negative** — isolation, evidence manifests, one-way sealing and human-readable disagreement add
latency, storage, implementation work and review burden. Most tasks should pay none of that cost.
[asserted]

**Neutral but load-bearing** — the Owner owns the candidate, not truth; model family is provenance
metadata; disagreement is a terminally recordable outcome; the six-command CLI and
`routing_orchestration_enabled = false` remain unchanged. [asserted]

## Enforcement

This commit records the protocol, its executable regime model, the index row and EXP-80 only; it
changes no gate, CLI or product code. [measured]

- Check: future implementation must add tests at the existing dispatch/work-item chokepoints for
  exactly one Owner, concrete non-overlapping evidence manifests, isolated pre-seal acquisition, the
  beta-derived candidate ceiling, and a terminal disposition for every material dissent. Those tests
  must also prove that only the Owner can write the candidate and outcome, no vote/average transition
  exists, actual source hashes and access records decide overlap, and no second orchestration path
  bypasses `dispatch.py` and work items. [asserted]
- Fails CI: no — no implementation ships in this commit. [measured]
- Added in the same commit as the implementation: no implementation is added; the checks above are
  a same-commit condition on any later implementation. [asserted]

Until those checks ship and EXP-80 fires, current `--fan-out` must not be described as implementing
this ADR. [asserted]

## What would overturn this

EXP-80 kills the squad-specific protocol for its frozen task mixture if the operational-invalidity
threshold fires. A safety-margin failure cuts automatic acceptance, and a gain against the normal-
budget single but not the matched-budget single attributes the gain to compute. Any other failure to
confirm remains unresolved rather than being narrated as equivalence or a kill. [asserted]

EXP-52 overturns the evidence-manifest premise for its mutation population if shared-evidence
consensus materially lowers beta. [asserted] If EXP-80 fails, retain the chat, trajectory, tools and
one accountable agent; do not build squad-specific routing, schema or disagreement UI. [asserted]

## Publication candidate?

**No.** The protocol is provisional and its central benefit is asserted. Reconsider only after
EXP-80 reports the full human-by-verifier table, adverse outcomes and matched-budget cost. [asserted]

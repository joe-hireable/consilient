# 0026. Admit only budget- and hardware-feasible backends to routing

- **Status:** PROVISIONAL — superseded in part by ADR-0028's subscription-allocation rule
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Supersedes:** ADR-0005
- **Inquiry tier reached:** T3 measure
- **Executable model:** none — the new rules restrict the feasible action set with
  Boolean vetoes; EXP-21 measures their false-admit and false-refusal rates.

## Update: 2026-08-20 — unknown headroom disqualifies *unbounded* work, not bounded work

The rule below excludes a backend from unattended routing whenever its headroom lower bound is
unknown. Applied literally on 20 August it idled a paid Cursor subscription all night while the
maintainer slept, because Cursor exposes a plan tier and no remaining allowance. [measured]

That is over-broad, and the reason is a confusion between two different risks. The danger an
unknown lower bound creates is **exhausting an allowance mid-task and failing in an
unrecoverable state**. Where the work is bounded such that its worst case cannot plausibly
exhaust the allowance — a fixed corpus, a read-only pass, a capped number of turns with no
retry loop — the unknown is not load-bearing, because the worst case is bounded by the *task*
rather than by the meter. [asserted]

**Amendment.** A backend whose headroom lower bound is unknown remains excluded from unbounded
unattended work. It is admissible for **bounded unattended work** where all of the following
hold and are recorded before dispatch: [asserted]

1. the work has a fixed, enumerable input — a named document set, a fixed fixture list — not a
   loop whose length depends on what it finds;
2. a hard turn or attempt cap is set and enforced in the loop, with exhaustion escalating
   rather than retrying;
3. the task is read-only, or its writes are confined to a scratch location outside the
   repository;
4. failure of the backend mid-task loses only that task, with no partial state to reconcile;
5. the composition's authenticated identity is confirmed at dispatch, since that check does not
   depend on headroom.

Where any of the five is false, the original exclusion stands unchanged. [asserted]

**Enforcement.** A dispatch to a backend with unknown headroom that does not carry all five
recorded conditions is rejected at the admission boundary, not by convention. A bounded task
that exceeds its recorded cap is a defect in the cap, and is logged as one. [asserted]

**What would overturn this.** A bounded task exhausting an allowance despite its cap, which
would mean the bound was never real and the original blanket exclusion was right. [asserted]

## Update: 2026-08-20 — EXP-07 replicated, and a composition can pass admission and still emit nothing

EXP-07 ran at n=30 on 20 August and settled three things this ADR asserted. [measured]

**The n=1 caution in § *Evidence against* was right, and is recorded as vindicated.** The
19 August pilot's 5.6× single-attempt wasted-work multiplier did not reproduce: the
single-attempt median over 30 attempts is 1.69×, three of the five fixtures sit between 1.20×
and 1.69×, and the pre-registered verdict is `insufficient_evidence` rather than a crossing.
[measured] The 2× trigger crosses only with the serial best-of-five retry layer, at a clamped
median of 16.75×. [measured] The bullet has been rewritten to say so rather than to repeat a
caution that has since been tested.

**ADR-0003 was not reopened.** The § *Consequences* sentence asserting that it "remains reopened
for EXP-07" is false and has been corrected in place.

**A composition satisfied every admission term in this ADR and produced no artefact at all.**
The new § *Evidence* bullet records it. The local composition was hardware-feasible, spent
nothing metered and consumed no subscription headroom — `available(m, x, t)` as written in
§ *Decision* would have admitted it on all 25 attempts, and it returned no file edit on any of
them while consuming real tokens throughout. [measured]

That is an admission observation, not a routing one. Routing chooses among candidates; a
candidate that cannot emit a diff should not be in the set to choose from, and no β-centred
choice rescues one that is. [asserted]

**What this ADR does not do about it yet, stated rather than implied.** `available(m, x, t)`
gains no capability term here and no check enforces one, because two inputs are missing:
whether the floor belongs to the model or to the composition is unestablished — EXP-31 is
running to decide it — and there is no measured rate at which admitted compositions emit
nothing, so any threshold set now would be invented. The admission reading above holds under
either EXP-31 outcome, because the thing admission would exclude is the composition, which is
what was observed. [asserted]

**What would close it.** EXP-31's result, plus an emit/no-emit outcome recorded per dispatch in
the trajectory log, which would supply the rate a threshold needs. Until both exist, this is a
named gap in the admission predicate and not a rule. [asserted]

## Context

The first comparable backend run produced two frontier successes in 20.4–25.6 seconds and
one failed local attempt in 114.2 seconds. [measured] The local process completed but made
no change, and the verifier rejected it. [measured]

The decider holds three roughly £200/month subscriptions and has exhausted one provider's
included allowance during this design work. [asserted] A backend with sufficient
capability but no remaining allowance is not an available action. [asserted]

ADR-0002 describes routing safety as a `(Δ, α, β, ρ)`-plus-structure surface: capability
gap, verifier false-rejection, verifier false-acceptance, model-failure correlation, and
structural terms. [algebra] Subscription allowance, metered budget and local hardware fit
do not change those probabilities; they determine whether a candidate action exists at
the time of routing. [asserted]

ADR-0005 correctly required hardware gating but incorrectly described LLM Checker as open
source and left the selected wrapper unresolved. [measured] Its current NPDL-1.0 licence
prohibits paid distribution and monetised hosted use. [cited] Current LM Studio tooling can
estimate memory before load but only for a model already present locally, so it is too late
to be the sole download gate. [cited]

## Decision

Routing has two stages. First, a central admission boundary constructs the feasible
candidate set for the task and current time. Second, the existing β-centred router chooses
only within that set. [asserted]

For backend `m`, task `x` and time `t`, admission requires:

```text
available(m, x, t)
  = headroom(m, t) >= reserved_usage(m, x)
  ∧ period_budget_remaining(m, t) >= reserved_cost(m, x)
  ∧ (remote(m) ∨ hardware_feasible(m, x, local_machine))
```

Terms that do not apply to a backend evaluate true; for example, a local backend has no
subscription-headroom requirement. [asserted]

For subscriptions, `reserved_usage` is a conservative upper bound in that provider's
native window units, learned from comparable completed tasks in the trajectory log. With no
usable observation, the bound is unknown rather than zero. [asserted]

The reservation is charged before dispatch and released or reconciled from provider
usage after completion. Concurrent tasks and retries consume the same ledger. [asserted]
Unknown or stale data cannot produce a positive availability result for unattended
routing. [asserted]

### This is a constraint layer, not a fifth safety axis

The operator-facing decision has four immediately visible inputs: capability gap `Δ`,
verifier reliability `β`, remaining headroom and hardware feasibility. [asserted]
`α` and `ρ` remain inside ADR-0002's safety calculation; they are not discarded.
[algebra]

Headroom and hardware feasibility neither collapse into `Δ` nor extend the
`(Δ, α, β, ρ)` quality-safety surface. They are structural constraints that remove
actions before that surface is evaluated. [asserted] A constrained-out frontier model has
zero routing value at that moment even if the unconstrained safety calculation prefers it.
[asserted]

### Subscription headroom

Each subscription adapter reports provider-native windows rather than pretending that
three vendors share one quota unit. [asserted]

| backend | machine-readable source | limitation | v0 rule |
|---|---|---|---|
| Claude Code | Status-line JSON provides five-hour and seven-day `used_percentage` and `resets_at`. [cited] | Fields appear only for subscribers after a response and can be stale across concurrent sessions. [cited] | Persist the last observation, reserve the worst recent comparable percentage increment until reset, and exclude Claude from unattended routing when no conservative lower bound remains. [asserted] |
| Codex | App-server `account/rateLimits/read` returns used percentage, reset time and window duration; a local authenticated query returned the structured windows. [measured] | The ordinary top-level CLI help has no quota command. [measured] | Read app-server headroom immediately before reservation and record the snapshot in the trajectory log. [asserted] |
| Cursor | Installed CLI `status` reports authentication and `about` reports product information; neither exposed individual usage. [measured] | Official individual-plan material reviewed on 19 August exposes usage in the dashboard, while the documented Admin API is for teams. [cited] | Use the last user/dashboard snapshot plus trajectory-log accounting and the billing reset window; mark the estimate explicitly. Exclude Cursor from unattended routing when the lower bound is unknown. [asserted] |
| Antigravity | CLI status-line JSON can expose `plan_tier` and per-bucket `remaining_fraction`, `reset_time` and `reset_in_seconds`; `/usage` refreshes the interactive quota view. [cited] | The installed 1.1.15 CLI authenticated a saved Google business/GCP profile and listed models, but its print-mode probe failed before inference; plan tier and usable headroom remain unverified. [measured] | Require a fresh live plan/quota snapshot, a successful structured execution probe and `useG1Credits=false`. Treat Plus, Pro, Ultra and unknown as reported tiers, not inferred entitlements; exclude the composition while any field is unknown. [asserted] |

Local accounting never upgrades an estimate to provider truth because usage outside the
harness can consume the same subscription. [asserted] The trajectory log stores source,
observation time, provider window, reset time, used amount and whether the value is direct
or estimated. [asserted]

### Metered-provider budgets

Every metered task has both a per-task cap and a per-period cap. Reaching either is a hard
stop, not a warning. [asserted]

OpenRouter exposes live credits and management-key fields for limit, remaining limit and
daily/weekly/monthly reset policies. [cited] A provider-enforced scoped key is the outer
boundary; a concurrency-safe harness reservation is the inner boundary that prevents two
tasks from independently spending the same remainder. [asserted]

For unattended OpenRouter work, the harness creates a task-scoped key whose provider limit
is the lower of the task cap and the unreserved period remainder. [asserted] The local
ledger permits task-key limits whose sum cannot exceed the configured period cap, so
concurrent worst-case spend remains bounded. [algebra] The management API reviewed exposes
a limit per key rather than a nested task/period budget object. [cited]
The task key is disabled after completion and is never reused across period resets.
[asserted]

Retries, verifier calls and recovery attempts charge the originating task's cap.
[asserted] Automatic top-up and automatic movement to a more expensive metered model are
off by default. [asserted] If a provider cannot enforce the configured monetary scope, it
is unavailable to unattended metered routing. [asserted]

### Hardware-gated local models

Consilience will wrap an installed fit provider rather than build and maintain a model
catalogue. [asserted] The first candidate is `llmfit`: its MIT-licensed CLI detects
RAM, CPU, GPU/VRAM and execution backends and emits pre-download recommendations as JSON.
[cited] Selecting it as a dependency still requires the separate approval demanded by
`AGENTS.md`; this ADR adds no dependency. [measured]

LM Studio's `lms load --estimate-only` is an optional second, pre-load confirmation after
download, not the pre-download gate. [cited] LLM Checker may be used only as a
user-installed external tool pending legal review; it must not be bundled or labelled open
source. [cited]

The gate keys feasibility by model revision, quantisation, context length, execution engine
and detected hardware profile. [asserted] The default local policy requires the selected
quantisation and context to fit both system and accelerator memory with reserved headroom.
An accelerator backend defaults to full accelerator residency; CPU offload is admitted
only when the user explicitly selects an offload policy. A CPU-only backend is evaluated
against system RAM. [asserted]

A model classified infeasible or unknown cannot be downloaded or executed through the
harness. It remains selectable through a remote backend. [asserted] This boundary governs
harness-initiated downloads and execution; it cannot stop a user invoking `ollama pull`
or another tool outside Consilience. [asserted]

The project does not host or redistribute weights. Downloads resolve to an upstream
provider, surface upstream licence terms before transfer, reject executable pickle-style
formats, and verify a published content hash when one is available. [asserted]

## Evidence

- `[measured]` EXP-05 separated backend process completion from verifier acceptance and
  measured a 4.5–5.6× latency penalty for one failed local attempt.
- `[measured]` EXP-07 (n=30, 20 August) recorded a composition that satisfied every admission
  term in this ADR and still produced nothing. `qwen3:8b` served by Ollama through the Codex
  `--oss --local-provider ollama` control path, at its Ollama default reasoning mode, against
  the five frozen EXP-07 fixtures and the functional-plus-changed-file verifier, returned
  `changed_files: []` on all 25 attempts; one rejected run spent 30,243 input and 10,664 output
  tokens to change nothing. This is recorded as a property of **that composition**, not of a
  tier or a parameter count: which component carries the floor — the model, the `--oss` control
  path, the reasoning mode or the fixtures — is not established by EXP-07, and EXP-31
  substitutes `gemma4:31b` into the identical composition to decide it. The admission reading
  in the 20 August update does not depend on that answer.
- `[measured]` Claude Code 2.1.235, Codex 0.148.0 and Cursor CLI 2026.08.11 were inspected
  locally. Codex's authenticated app-server returned structured rate-limit windows; Cursor
  exposed no individual-usage field in its installed command surface.
- `[cited]` Anthropic's status-line documentation defines structured five-hour and
  seven-day subscription utilisation and reset fields, including their absent-before-first-
  response limitation.
- `[cited]` OpenAI's Codex app-server protocol documents
  `account/rateLimits/read`.
- `[cited]` Cursor's CLI reference defines `status` as authentication status, while its
  individual pricing documentation directs usage management to the account surface.
- `[cited]` Antigravity's status-line schema exposes plan tier and quota/reset fields;
  its plan documentation gives Pro and Ultra five-hour baseline refreshes and other plans
  weekly baseline limits, while the CLI credit-fallback setting defaults false.
- `[measured]` Antigravity 1.1.15 listed eleven Gemini model choices through the saved
  keyring identity, but a structured print probe selected the requested model and then
  failed before inference with zero tokens and `invalid location: ""`.
- `[cited]` OpenRouter's credits and management-key documentation exposes provider-side
  limits and reset periods.
- `[cited]` Khan (2026), *Token Budgets: An Empirical Catalog of 63 LLM-Agent
  Budget-Overrun Incidents*, arXiv:2606.04056, records 63 confirmed production incidents
  and supports hard, scoped enforcement over warnings.
- `[cited]` `llmfit` is MIT-licensed and supplies pre-download hardware-fit JSON;
  LM Studio supplies post-download, pre-load resource estimates.
- `[simulated]` ADR-0003's sensitivity table gives routing headroom of +0.123 at a 5×
  wasted-work multiplier, the largest value in that table.
- `[asserted]` Conservative admission is preferable to discovering exhausted allowance,
  overspend or local OOM after dispatch.

## Evidence against

- `[cited]` Claude's rate-limit fields refresh with session responses rather than through
  a documented standalone poll, so a cached reading can be stale.
- `[measured]` Cursor supplied no machine-readable individual headroom in the surfaces
  inspected. A local ledger cannot observe usage from Cursor's desktop app or other
  machines.
- `[measured]` Antigravity model discovery did not establish plan-backed execution
  readiness on the measured Google business/GCP identity.
- `[cited]` Provider-side caps are stronger than client estimates where available, which
  means the harness remains dependent on provider semantics and availability.
- `[cited]` Khan's 63 incidents are a convenience, failure-confirming sample. They show
  recurring mechanisms, not an incidence rate or expected loss.
- `[cited]` Hardware estimators are predictions. CPU offload can make a model technically
  runnable when a GPU-resident policy rejects it, and new architectures can invalidate
  catalogue assumptions.
- `[measured]` The n=1 caution recorded here — one trivial ticket, no general 5× multiplier —
  was vindicated. EXP-07 replicated at n=30 on 20 August and the pilot's headline figure did
  not reproduce: the single-attempt median is 1.69×, with three of five fixtures between 1.20×
  and 1.69×, and the pre-registered verdict is `insufficient_evidence`. The trigger crosses only
  with the serial best-of-five retry layer, so the wasted work is created by the scaffolding
  rather than by the raw local attempt being slow.
- `[asserted]` Failing closed can strand paid subscription capacity and reject a local
  model that would have run.

## Consequences

**Positive** — routing cannot select a backend that the admission boundary knows is
exhausted, over budget or unable to run the selected local model. [asserted] Budget and
hardware failures become explicit admission outcomes in the trajectory rather than
surprises after work begins. [asserted]

**Negative** — three provider-specific headroom readers, a budget ledger and a hardware-fit
adapter become v0 maintenance surfaces. [asserted] Cursor remains conservative until it
exposes an individual quota API or EXP-21 validates the fallback. [asserted] Fail-closed
behaviour can leave useful capacity idle. [asserted]

**Neutral but load-bearing** — ADR-0002 still decides which feasible backend is safe;
ADR-0026 decides which backends are feasible. [asserted] ADR-0003 was **not** reopened by
EXP-07: the pre-registered rule was applied at n=30 and the single-attempt multiplier did not
cross its trigger, so ADR-0003 stands unchanged. [measured] Neither outcome would have moved
this ADR, which removes actions before ADR-0002's safety surface is evaluated at all.
[asserted]

## Enforcement

This ADR declares one routing-admission chokepoint but does not implement it during the
pre-spec phase. [measured] The implementation commit must include all of these checks:

- Check: a boundary test rejects dispatch when authoritative subscription headroom is below
  the task reservation, including concurrent reservations and reset transitions.
- Check: metered-provider tests prove task-key allocation and disablement, and that
  per-task and per-period caps hard-stop retries and concurrent work without overshoot.
- Check: download and local-execution tests reject infeasible and unknown fit results before
  transferring model bytes or starting an engine.
- Check: a lint rule bans direct provider dispatch and model-download calls outside the
  routing-admission module.
- Fails CI: yes, once implementation exists.
- Added in the same commit as the implementation: **required; not yet applicable because
  this commit contains only the ADR, evidence and pre-registered experiment.**

## What would overturn this

EXP-21 decides the provisional claims. [asserted]

- Any provider-reported spend above a configured hard cap removes that metered provider
  from unattended routing until a provider-enforced boundary exists. [asserted]
- Any dispatch to a subscription that an authoritative snapshot already marked exhausted
  makes that adapter manual-only until corrected and remeasured. [asserted]
- Any local model admitted and then unable to load at the configured context, or any model
  bytes transferred after an infeasible/unknown verdict, disables automatic local
  downloads until the fit provider or boundary is superseded. [asserted]
- A false-refusal rate above 20% over at least 30 authoritative feasible cases per
  constraint class overturns fail-closed autonomous routing for that class; it becomes an
  explicit user decision while a better signal is sought. [asserted]
- If a provider exposes a fresh, authoritative headroom endpoint or a download tool ships a
  reliable pre-download hardware gate, replace the corresponding local estimate/wrapper
  rather than preserve our adapter for its own sake. [asserted]

## Publication candidate?

**No.** This is necessary operational engineering. A measured multi-machine
predicted-versus-actual fit dataset from EXP-21 could become a separate publication
candidate. [asserted]

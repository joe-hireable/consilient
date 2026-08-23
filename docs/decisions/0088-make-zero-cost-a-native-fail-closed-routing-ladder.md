# 0088. Make zero-cost a native, fail-closed routing ladder

- **Status:** PROVISIONAL — EXP-132 can confirm, narrow or remove each zero-cost claim. [asserted]
- **Date:** 2026-08-23. [measured]
- **Deciders:** Codex dispatch `20260823T094246-92012d7dd9` owns this provisional mechanism; the
  principal has not reviewed it and retains exclusive authority over spend, gates, approval and
  publication. [measured] [asserted]
- **Inquiry tier reached:** T1 ground — current repository paths and first-party provider/runtime
  documentation were inspected; no inference, authenticated provider or metered call was made.
  EXP-132 is the prospective T3 test. [measured]
- **Executable model:** none — the decision is a fail-closed state machine; utility and safety are
  measured prospectively by EXP-132 rather than inferred from a fitted model. [asserted]

## Context

ADR-0048 requires a fully local path for someone who pays nothing and contacts no Consilient-operated
server. ADR-0044, as amended by ADR-0064, puts subscriptions before bounded metered use and gives no
agent spend authority. ADR-0027 preserves domain, harness, provider and model as separate identities;
ADR-0077 makes automatic candidate exposure conditional on a robust upper bound. Those decisions do
not currently compose into an executable zero-cost route. [measured]

**Correction:** zero configuration does not produce model work today. `hardware_probe.py` reports CPU
memory topology as unknown, `local_fit.fit()` refuses it, no product caller invokes local acquisition,
and dispatch imports none of local fit, routing or budget. Dispatch also cannot prove its current CLI
outcomes used subscriptions: it records no authentication/account/plan binding, passes the non-Git
ambient environment and refuses common metered keys only for Grok. Existing local/OpenRouter adapters
are research artefacts; the measured Ollama composition in `backends.md` produced no artefact.
[measured: `scripts/hardware_probe.py`, `src/consilient/local_fit.py`, `scripts/dispatch.py`,
`docs/00-context/subscription-reach-2026-08-22.md`, `docs/20-design/backends.md`, inspected 2026-08-23]

Local inference and free hosted inference are occupied territory. Ollama and `llama.cpp` already cover
local model download/execution; OpenRouter, Google Gemini, GroqCloud and Cloudflare Workers AI document
free hosted allowances. The missing product capability is not another inference engine: it is an
honest, provenance-preserving admission ladder that cannot turn exhausted free capacity into a charge.
[cited: `../10-research/bibliography.md` §18, all [FULL], read 2026-08-23] [asserted]

## Decision

Implement one native routing ladder behind the existing dispatch boundary:
`Z0_LOCAL` (Consilient install only), then `Z1_FREE_KEY` (one supported key whose authenticated API
proves an unbillable account/request), then `S_SUBSCRIPTION` only with authenticated account/plan/
headroom proof, a provider-side hard zero-marginal-charge boundary and outer credential isolation, and
only then `M_METERED` under separately recorded, current, bounded principal-authored spend authority.
Select the first route that passes task capability,
data, licence, hardware, price and quota admission; gate automatic verifier-accepted/shippable exposure
separately on exact-composition safety. Display and record the rung and every earlier refusal. [asserted]

A zero-cash request cannot enter the metered rung. Free-tier exhaustion, ambiguous price/plan, stale
allowance, unknown upstream endpoint/model identity and partial output refuse or quarantine; none sheds
to paid work. A subscription route is ineligible unless overage and automatic top-up are disabled, or
the provider otherwise guarantees that concurrent exhaustion cannot debit extra usage; local headroom
alone is not a spend boundary. A fixed OpenRouter model also freezes its upstream endpoint, data policy
and fallbacks, or each returned endpoint/fingerprint remains a separate supervised composition. Every
credential-bearing route, including subscription CLIs, refuses until ADR-0084's outer process/security
namespace lets the authenticated harness operate while defeating hostile same-user credential-file/
process/network/IPC access; a gitignored broker and canary-only sink test are insufficient. Reuse `dispatch`, `coordination`,
`work_items`, `recall`, `routing`, `usage`, `budget`, `instructions` and the single `events` writer.
The complete contract is
[`2026-08-23-zero-cost-path.md`](../superpowers/specs/2026-08-23-zero-cost-path.md). [asserted]

Zero configuration targets a 16 GB, CPU-only Windows laptop running one small quantised local text
model for bounded, task-verifiable work. That target remains `experimental, supervised-only` until
EXP-132 runs. A clean Consilient install must also supply a pinned, verified inference runtime without a
separate Ollama/`llama.cpp` installation; the current downloader does not do that, and the dependency/
packaging choice remains a blocker. Below the resource floor, the product names the requirement and
climbs only through eligible rungs. This machine-specific refusal never waives ADR-0048: every shipped
capability still needs a fully usable local path on an admitted hardware profile, so a hosted-only
feature remains unshippable. [measured] [asserted]

Do not assign an assumed higher beta merely because a free model is weaker. Conditional
`beta = P(verifier accepts | human rejects)` need not rise with bad-output prevalence. Instead, isolate
`q`/beta by front-door provider, upstream endpoint, model revision/fingerprint, verifier contract and
task stratum. Apply ADR-0077's distribution-free
`n_max = floor(epsilon / q_upper)`, conservatively substituting `beta_upper` when `q` is unavailable;
unmeasured human safety gives zero automatic verifier-accepted/shippable exposure while still allowing
explicitly supervised generation. The logarithmic i.i.d. formula is diagnostic only, and EXP-132's
constructed bank cannot activate future-task routing even if its frozen-panel bound passes. [algebra]
[measured] [asserted]

## Evidence

- `[measured]` `local_fit.py` already owns conservative fit/acquisition types and refuses unknown
  topology; `budget.py` already owns refuse-only cash reservations; `usage.py` already distinguishes
  provider-native quota from money; `routing.py` already refuses an unmeasured beta ceiling. Extending
  these boundaries is smaller than creating parallel ones.
- `[measured]` The current CPU probe/fit pair refuses, free-provider quota vectors and resumable task
  checkpoints do not exist, beta scope omits provider/model/rung, and `dispatch.py` wires none of the
  local/free/budget/routing paths. No product path supplies a local runtime, and current CLI outcomes
  are not bound to subscription authentication. The ADR records a specification, not shipped capability.
- `[measured]` EXP-132 is present in the experiment register as `BLOCKED`, with zero-spend kill rules,
  one cold-install smoke, fixed warm utility/safety panels and stop, adverse rate/catalogue outcomes,
  supervised-utility thresholds, attainable 30-rejection cells and an explicit prohibition on
  future-task routing claims.
- `[cited]` Ollama documents no authentication for its local API plus model pull/list operations;
  `llama.cpp` documents CPU and quantised GGUF inference. Bibliography §18 [FULL].
- `[cited]` OpenRouter documents zero-priced free routing plus changing availability and strict free
  limits; it also documents default upstream load-balancing/fallbacks and per-request data-collection/
  ZDR controls. Google documents selected Gemini free pricing, per-project dynamic limits and free-tier
  data use; Groq documents a Free plan with organisation-wide rate limits; Cloudflare documents a free
  daily allowance that fails on exhaustion. Bibliography §18 [FULL].
- `[cited]` Cloudflare moved three free models to paid-only on 28 July 2026 and GitHub Models retired
  on 30 July 2026. These first-party records establish catalogue churn, not merely a hypothetical risk.
- `[algebra]` With only an upper bound on per-attempt bad-and-accepted risk, the union bound gives
  `P(any bad acceptance) <= n × q_upper`; hence `n <= floor(epsilon / q_upper)` without independence.
- `[asserted]` Exact price/account/endpoint receipts, a local quota lease or bounded unbillable
  one-request bootstrap, and an immutable zero cash ceiling are the minimum proof needed to call a
  hosted attempt zero cost.

## Evidence against

- `[measured]` **The local route's only recorded backend attempt failed:** the Ollama/Qwen composition
  in `docs/20-design/backends.md` ran for 114.2 seconds and produced no artefact. No current result says
  a 16 GB CPU-only laptop can complete useful Consilient work. “Zero configuration” may therefore be
  a promise whose reference implementation is too weak to matter.
- `[cited]` **Free catalogues disappear.** Cloudflare moved three models to paid-only in July 2026;
  GitHub Models retired days later. A provider matrix creates permanent maintenance work around
  benefits the provider can withdraw without notice.
- `[cited]` Free tiers are deliberately constrained: OpenRouter documents low zero-purchase request
  limits and volatile availability; Google says active limits are account-specific/not guaranteed and
  free-tier content may improve its products; Groq limits are organisation-wide. Mid-task exhaustion
  and privacy refusal may make the route less useful than its “free” label suggests.
- `[cited]` A normal Gemini/Groq key does not expose the complete account plan/remaining quota needed
  by this fail-closed admission contract, while OpenRouter successful responses omit remaining rate
  headers. “One key” is therefore supported only where an authenticated endpoint proves the request is
  unbillable; some cited free offerings may remain permanently undispatchable without a stronger
  read-only account surface. Bibliography §18 [FULL].
- `[measured]` Today's same-user permission-bypass launch has no outer credential-broker isolation,
  and current Claude/Codex dispatch can inherit ambient metered keys. Both keyed and purported
  subscription rungs are blocked until their hostile-boundary/authentication checks exist.
- `[asserted]` Small local/free models may create more bad artefacts and human review than a strong
  subscription saves. Even if their conditional beta is low because tests catch their mistakes, low
  joint success makes them a queueing and attention cost rather than a product benefit.
- `[asserted]` Dynamic catalogue, quota and price proof across providers is security- and money-critical
  integration work. An honest subscription may be simpler, more stable and cheaper once engineering,
  electricity and reviewer time are included; EXP-132 measures cash and outcomes, not total economic
  cost.

The strongest case is therefore that “free” is a trap: it is weak enough to fail, constrained enough
to stop mid-task, volatile enough to rot and expensive enough in review/maintenance that a subscription
is the honest answer. This decision concedes that case. No free route is described as useful until its
exact arm passes EXP-132; the interface says `subscription_required` when it loses, and unmeasured
automatic acceptance remains off. [asserted]

## Consequences

**Positive** — a new user has a concrete no-account target; one key can add capacity where that
provider's authenticated API proves an unbillable path; upstream route, local quota lease, price and
safety evidence stay visible; free failure cannot become a bill. [asserted]

**Negative** — the product must maintain provider-specific entitlement/quota adapters and a local
runtime/model supply chain; local downloads consume disk/bandwidth; dependency approval and hostile-
child isolation block first use; strict freshness/lease checks refuse some apparently free capacity;
supervised-only output shifts work to the human. [asserted]

**Neutral but load-bearing** — `events.py` stays the sole writer, `dispatch.py` stays the sole runner,
quota stays separate from money, model family is provenance rather than an evidence class, one Owner
remains baseline, and principal authority is not delegable. No gate or CLI surface changes. [asserted]

## Enforcement

This documentation commit implements no route. Every prospective invariant ships with its smallest
test in the same implementation commit. [measured] [asserted]

- Check: zero-cash plus free-provider 429/catalogue/paid-fallback and ambient Claude/Codex/Grok
  metered-key mutations cannot reach a metered adapter; ambiguous price/account/plan refuses, with only
  the proved-unbillable one-request quota bootstrap. Fails CI: yes, once implemented. Added in the same
  commit as implementation: required. [asserted]
- Check: while the authenticated adapter or subscription harness still operates, a hostile same-user
  child cannot inspect broker/subscription auth files or processes, connect to IPC without a run-scoped
  grant or retrieve a raw credential; canaries are also absent from child/durable sinks.
  Fails CI: yes, once implemented. Added in the same commit: required. [asserted]
- Check: subscription admission proves overage/automatic top-up disabled or an equivalent provider-side
  hard zero-marginal-charge boundary; concurrent-headroom and exhaustion fixtures refuse without
  debiting extra usage. Fails CI: yes, once implemented. Added in the same commit: required. [asserted]
- Check: a clean reference machine without an inference runtime acquires a pinned verified runtime and
  model and completes the local smoke task; refusal is a failure. Fails CI: yes, once implemented.
  Added in the same commit: required. [asserted]
- Check: exact route/rung/upstream endpoint and scoped beta/q are recorded; missing human evidence gives
  zero automatic shippable exposure; a mid-stream 429 yields a quarantined adverse outcome, never `ok`.
  Fails CI: yes, once implemented. Added in the same commit: required. [asserted]
- Check: prompt bytes cannot leave until endpoint retention/training/region policy is compatible and
  escaping fallbacks are disabled; returned identity cannot repair a mismatch. Fails CI: yes, once
  implemented. Added in the same commit: required. [asserted]
- Check: the six-command CLI and doctor/gate outputs remain unchanged, and no second writer/executor is
  introduced. Fails CI: yes. Added in the same commit: required. [asserted]

## What would overturn this

EXP-132 is the killing experiment. A zero-cost arm loses if it fails its fixed useful-supervised
threshold, if rate/catalogue failure affects more than 4/40 assignments, if zero-price eligibility is
unprovable for more than 4/40 admissions, or if any immediate zero-spend/identity/secret/partial-output
kill fires. Remove or narrow the losing rung and say why. [asserted]

An arm passing useful supervised work does not authorise automatic acceptance. EXP-132 can call its
sealed-panel safety acceptable only when every exact composition/stratum cell has 30 authenticated
human rejections and one-sided 95% `q` and beta upper bounds at or below its fixed `epsilon = 0.40`;
even then, a separately preregistered coverage-valid future-task experiment is required before any
automatic routing scope exists. A later first-party provider/endpoint policy change immediately
removes eligibility and reopens the dated provider seed even if EXP-132 once passed. [asserted]

## Publication candidate?

**No.** This is an unimplemented ladder assembled from incumbent runtimes/provider APIs and existing
Consilient boundaries. Reconsider only after EXP-132 produces reproducible public-task outcomes,
complete adverse denominators and zero-spend receipts; a provider list is not a research contribution.
[asserted]

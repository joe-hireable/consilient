# 0028. Optimise expiring subscription capacity for verified value

- **Status:** PROVISIONAL
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Supersedes in part:** ADR-0026's treatment of subscription headroom as admission only
- **Inquiry tier reached:** T2 — provider documentation and local authentication surfaces
  inspected; allocation policy not yet run
- **Executable model:** EXP-23 fixes the value, utilisation and plan-advice stopping rules

## Context

The decider pays for high-capacity individual plans from Claude, Codex and Cursor. [asserted]
Included allowance expires at provider reset boundaries, whereas OpenRouter and API-key
fallbacks incur marginal metered spend. [cited] Treating both regimes as “minimise usage”
would leave paid capacity idle; treating a reset as a reason to consume tokens would reward
activity rather than useful work. [algebra]

ADR-0026 correctly removes an exhausted subscription from the feasible action set but does
not decide how to allocate remaining included capacity among useful tasks. [measured] The
missing objective is value created from already-paid capacity, not utilisation for its own
sake. [asserted]

The provider surfaces are not uniform. Claude exposes five-hour and weekly progress/reset
data and shares limits across Claude product surfaces. [cited] Codex exposes structured
rate-limit windows locally and now shares an agentic usage/credit pool with other eligible
OpenAI agentic products. [cited] Cursor documents included monthly agent usage and detailed
dashboard accounting, but its installed individual CLI exposes authentication rather than
remaining usage. [cited] No honest common “token remaining” unit exists across the three.
[measured]

Antigravity documents plan-tier and quota/reset fields in its status-line payload. [cited]
Google AI Pro and Ultra receive five-hour baseline refreshes until weekly limits, while
other tiers receive weekly baseline quota; AI Plus is a current plan but cannot purchase
AI-credit top-ups. [cited] The installed CLI has not yet produced a verified plan-tier
snapshot or successful inference trajectory, so Google capacity is not admitted to the
optimiser. [measured]

## Decision

### Two economic regimes

Subscription and metered capacity remain separate ledgers. [asserted]

- **Included subscription capacity:** marginal cash cost is zero only while an authoritative
  admission snapshot says included headroom remains and metered overage is disabled.
  [algebra]
- **Metered capacity:** every call retains ADR-0026's per-task and per-period hard monetary
  caps. [asserted]
- **Local capacity:** hardware admission and elapsed machine time remain explicit; “no API
  charge” is not recorded as “free”. [asserted]

The router may compare expected outcomes across those regimes, but it must not add their
native usage counters as though they were one quantity. [asserted]

### Allocate subscriptions by incremental verified value

Only tasks already present in a user-authorised backlog are candidates for autonomous
subscription use. [asserted] Research, coding, evaluation and audit work are all eligible
when each task names a useful artefact, an acceptance check, a time bound and the decision
or outcome it serves. [asserted]

For task `q`, admitted action `a` and time `t`, the allocation score is conceptually:

```text
score(q, a, t)
  = expected_verified_value(q, a)
  - expected_review_and_rework_cost(q, a)
  - marginal_cash_cost(a, t)
  - expected_displacement_cost(q, a, t)
```

`expected_verified_value` is user-supplied or learned from accepted trajectory outcomes;
model self-report is never an input. [asserted] `expected_displacement_cost` reserves
headroom for higher-priority work expected before reset. [asserted] A task with non-positive
score is not run merely because allowance will expire. [algebra]

Within the admitted positive-score set, approaching expiry increases the priority of tasks
whose best safe alternative would require metered spend, a weaker verifier-backed route or
delay past a useful deadline. [asserted] The priority increase never overrides the β safety
gate, an authority boundary, a task's wall-clock cap or a provider reservation. [asserted]

### Reset-window assistance

One to two hours before an observed weekly or billing reset, the harness may propose a
bounded queue of high-value tasks that fit the remaining time and conservative headroom.
[asserted] The proposal shows artefact, verifier, expected duration, selected composition,
headroom source and the task displaced if its estimate is wrong. [asserted]

Automatic execution is permitted only for task classes the user has authorised in advance;
otherwise the queue is one-action approval, not a background run. [asserted] Every run stops
at its task time limit or provider limit and returns unfinished work to the backlog with its
trajectory. [asserted] The harness never invents work to consume a quota. [asserted]

### Plan-rightsizing advice

The harness records plan price and period, authoritative or estimated utilisation, accepted
artefacts, human review time, capacity exhaustion, metered overflow and valuable tasks
deferred at reset. [asserted] It may recommend keeping, downgrading, cancelling or upgrading
a plan; it never changes a subscription itself. [asserted]

A lower plan is recommended only after three complete billing periods below 40%
authoritative utilisation where the accepted incremental value attributable to the plan is
also below the price difference to the lower plan. [asserted] An upgrade is recommended only
after three complete periods at or above 90% utilisation with either at least three
high-value authorised tasks deferred per period or verified metered overflow exceeding the
price difference. [asserted] All other cases recommend no plan change. [asserted] EXP-23 may
overturn these thresholds; they are decision thresholds, not empirical facts. [asserted]

### Relationship to routing and the OpenCode default

ADR-0026 still constructs the feasible set and ADR-0002 still applies the β-centred safety
decision. [asserted] This ADR ranks useful work and admitted compositions within that set.
[asserted] ADR-0027's OpenCode fallback applies when no vendor-native frontier harness is
authenticated; it does not turn OpenRouter metered usage into subscription usage.
[asserted]

## Evidence

- `[cited]` Anthropic documents fixed weekly reset times, five-hour and weekly usage views,
  shared Claude/Claude Code limits and plan tiers intended for different usage levels.
- `[cited]` OpenAI documents a shared agentic pool, included usage first, optional purchased
  credits afterwards, and usage inspection in Codex settings; its local app-server exposes
  rate-limit windows.
- `[cited]` Cursor documents monthly included usage by plan, model-dependent consumption and
  dashboard token/usage breakdowns.
- `[cited]` Antigravity documents machine-readable plan/quota/reset fields and an optional
  AI-credit fallback; Google documents AI Plus, Pro and Ultra as distinct subscriptions,
  with purchased AI credits limited to Pro and Ultra.
- `[measured]` Local authentication checks identify Claude Max and ChatGPT-backed Codex;
  Cursor's WSL CLI confirms login but not individual-plan headroom.
- `[measured]` EXP-05 produced incompatible native accounting fields, so cross-provider raw
  token totals are not a valid allocation currency.
- `[asserted]` The decider values useful work completed before capacity expires and wants
  advice on whether roughly £200/month plans earn their keep.

## Evidence against

- `[cited]` Provider allowances vary with model, context, tools, product surface and plan;
  plan terms and bonus capacity can change.
- `[measured]` Cursor has no machine-readable individual headroom in the inspected CLI, and
  usage outside Consilience can make every local ledger stale.
- `[asserted]` “Value” is partly preferential and cannot be inferred reliably from tokens,
  verifier pass rate or nominal API-equivalent cost alone.
- `[asserted]` Reset-aware prioritisation can pull low-urgency work forward and displace a
  more valuable task that arrives later.
- `[asserted]` Three billing periods delay plan advice, while shorter windows would be more
  vulnerable to one atypical project or holiday.

## Consequences

**Positive** — paid capacity can be directed towards useful, accepted artefacts before it
expires, while metered spend remains hard-capped. [asserted] Plan recommendations become
traceable to completed value and missed work rather than guilt about unused tokens.
[asserted]

**Negative** — task-value estimates, future-work reservations and provider-specific reset
readers add uncertainty and operator-facing explanation. [asserted] Useful automation is
limited where authoritative headroom is unavailable. [asserted]

**Neutral but load-bearing** — maximising subscription value does not mean maximising usage.
[algebra] The optimisation target is incremental verified value from authorised work.
[asserted]

## Enforcement

This ADR declares no product implementation during pre-spec work. [measured] Its
implementation commit must include:

- Check: subscription-included and metered ledgers are distinct; an overage or API-key
  fallback can never be labelled included capacity.
- Check: the reset-window scheduler rejects tasks without prior authorisation, a named
  artefact, verifier, positive score, reservation and wall-clock cap.
- Check: no self-reported confidence or raw utilisation percentage contributes to artefact
  acceptance.
- Check: β, authority, headroom, budget and hardware vetoes run before reset priority.
- Check: reset-boundary and concurrent-reservation fixtures prove no work starts against
  expired or double-reserved headroom.
- Check: plan changes are recommendations only and cite the periods and counterfactual
  costs used.
- Fails CI: yes, once implementation exists.
- Added in the same commit as implementation: **required**.

## What would overturn this

EXP-23 decides the provisional allocation and plan-advice claims. [asserted]

- Any autonomous task outside a pre-authorised backlog disables reset-window autonomy.
  [asserted]
- Any reset-prioritised task that bypasses a verifier, resource veto or authority boundary
  disables the optimiser until the enforcement boundary is fixed and re-run. [asserted]
- If reset-aware scheduling does not increase accepted incremental value per human review
  hour under EXP-23's fixed rule, keep headroom as admission data only and remove automatic
  prioritisation. [asserted]
- If authoritative provider counters and local estimates diverge beyond EXP-21's rules,
  that subscription remains advisory rather than autonomous. [asserted]

## Publication candidate?

**No.** [asserted] This is product economics and operator assistance unless EXP-23 exposes
a reproducible allocation result across users and plan structures. [asserted]

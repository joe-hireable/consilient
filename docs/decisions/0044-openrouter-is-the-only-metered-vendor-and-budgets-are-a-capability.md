# 0044. OpenRouter is the only metered vendor, subscriptions cover everything else, and budgeting is a required capability

- **Status:** **ACCEPTED 20 August 2026.** Decided by Joe Brown in the orchestration chat and
  recorded in the trajectory as `decision.spend_policy` authored by the principal.
- **Date:** 2026-08-20
- **Deciders:** Joe Brown. The policy is his; the mechanism and the objections below are mine.
- **Supersedes in part:** [`0019`](0019-paid-capability-acquisition.md) — condition 3
  (per-transaction permission) and the prohibition on standing authorisation for a class of
  purchases. Conditions 1, 2 and 4 stand unchanged, as does everything ADR-0019 forbids about
  account creation, terms acceptance and credential storage.
- **Inquiry tier reached:** T0 assert for the policy, which is correctly the user's;
  T1 ground `[cited]` for the vendor capability, which has **not** been run here.
- **Executable model:** none. A preferential question with a bounded parameter.

## Context

Joe, 20 August 2026:

> *"Any metered call can go through OpenRouter. Otherwise converges any and all frontier
> subscriptions. Metered calls must be able to set weekly and monthly spend limits. For me it's
> already set to £100 month openrouter credits at openrouter account level so dont need to worry
> about setting budgets but must be a capability to budget metered use."*

## Decision

1. **Subscription-first.** Anything reachable through a flat-fee subscription the principal already
   holds is reached that way. Today: Claude, Codex, Cursor, and SuperGrok if he upgrades. Metered
   calls are the exception, not the default path.
2. **OpenRouter is the only permitted metered vendor.** One metered vendor is bounded; several are
   not. Any other paid API requires a new decision.
3. **Weekly and monthly spend limits are a required capability of the harness**, whether or not the
   principal chooses to set them. He has an account-level cap of £100/month configured outside this
   repository; that is *his* control, not the harness's, and does not discharge this requirement.
4. **The harness is not authorised to spend.** This ADR authorises a policy and a capability. It is
   not a transaction approval, and no credential has been supplied.

### What this changes about ADR-0019, said plainly

ADR-0019 condition 3 required **per-transaction permission** and its "What this explicitly forbids"
section named *"standing authorisation for a class of purchases"*. **This ADR replaces that with a
bounded standing authorisation for exactly one vendor.**

That is a real loosening and it should be read as one. The trade is per-call approval for an
enforced ceiling — which is the ordinary way spend is bounded, and it is the only way an autonomous
harness can make a metered call at all without a human present for each one. What it costs is the
per-transaction record ADR-0019 wanted. What it must therefore buy back is **attribution**: every
metered call must be traceable in the trajectory to the run that caused it, or the ceiling is the
only thing standing between the principal and an unexplained bill.

## Evidence

### The measured objection, which was real

`backends.md`, on the one metered composition attempted here: [measured]

> *"Failed before artefact production with no diff or usage telemetry; delayed cumulative billing
> prevents per-run attribution."*

That failure is a fact and is not withdrawn. What has changed is its **attribution**: it was read as
a property of the vendor, and it is better explained as a property of how the vendor was used.

### What OpenRouter documents `[cited]` — not `[measured]`, and the difference matters

Read from OpenRouter's own documentation on 20 August 2026. **None of it has been run here**, because
running it needs the principal's key.

| capability | field / endpoint | bears on |
|---|---|---|
| Per-key spend cap | `limit` on `POST /api/v1/keys` and `PATCH /api/v1/keys/{keyHash}` | the ceiling |
| Reset period | `limit_reset` | **the weekly/monthly requirement** |
| Remaining budget | `limit_remaining` on `GET /api/v1/key` | pre-flight refusal |
| Usage by period | `usage`, `usage_daily`, `usage_weekly`, `usage_monthly` | reconciliation |
| **Per-call cost** | a `usage` object **on every completion response**, carrying token counts and cost | **per-run attribution** |
| Exhaustion signal | HTTP **402** | fail-closed |

The last two are what answer the measured failure. A cost returned *on the response* is not delayed
cumulative billing; it is a per-run figure available at the moment the run ends, which is exactly
what was missing.

**One caveat, stated because it is load-bearing.** The documentation page for provisioning keys shows
only `"daily"` in its example of `limit_reset`; `weekly` and `monthly` appear in OpenRouter's own
help material but I did not see them demonstrated. **Joe's requirement is weekly and monthly.** If
only `daily` is supported vendor-side, the weekly and monthly ceilings must be enforced
harness-side, which is a weaker guarantee because it can be bypassed by anything not routed through
the boundary. That is a probe, not an argument — see Enforcement.

## Evidence against

- **The capability claim is `[cited]`, from documentation, by the party that wants it to be true.**
  Working principle 8 says run it. It has not been run, because doing so needs a credential, and no
  figure from this ADR may be quoted as measured until `EXP-51` reports.
- **A ceiling is not attribution.** If the per-response `usage` object is absent, malformed, or
  simply not read, the harness is back to exactly the 19 August failure with a cap bolted on. A cap
  tells you *how much* went; it never tells you *why*.
- **Harness-side limits are the weak half and this repository has measured why.** Working principle 3:
  a documented boundary that nothing enforces fragments — `jobboard-v2`'s `llm()` boundary became
  five access paths, and this project's own `append()` chokepoint was bypassed by 92 of 93 events
  **on the day it was written**. A budget check that anything can route around is decoration.
- **Single-vendor concentration is a real cost, not just a simplification.** Every metered call now
  depends on one company's availability, pricing and terms, and OpenRouter is itself a broker — so
  the model actually serving a request may change beneath a fixed model string. That is a
  reproducibility hazard for any measurement taken through it, which matters more here than in most
  projects.
- **£100/month is the principal's account-level cap, set outside this repository.** The harness
  cannot read it, cannot enforce it and must not assume it. Treating it as a safety net would be
  relying on a control this system has no visibility of.

## Consequences

**Positive.** A metered call becomes possible at all, which unblocks any capability behind a paid
API — and, if headless Grok proves to be metered-only, the SuperGrok question too. One vendor is a
small surface to probe, cap and reconcile.

**Negative.** Per-transaction approval is gone. If attribution is not built and verified, this ADR
has traded a real control for a documented one.

**Neutral but load-bearing.** A budget primitive is a *product* concern, not a research instrument.
It is the first piece of `src/consilient/` that exists to refuse an action rather than to observe
one.

## Enforcement

Every rule ships with its check (working principle 3). These ship with this decision:

- **Check:** a budget module that is **refuse-only** — it can return "not permitted" and has no code
  path that performs, authorises or initiates a network call. Shipped first, deliberately: the thing
  that says no exists before anything that can say yes.
- **Check:** weekly **and** monthly ceilings are both representable, and a request that would breach
  either is refused. A configuration that sets neither is itself refused — **fail-closed means no
  ceiling is not "unlimited", it is "no".**
- **Check:** an unreadable, stale or absent budget state refuses. Never "assume there is room".
- **Check:** no metered call may be attempted without an attribution record naming the run that
  caused it, so ADR-0019's per-transaction *record* survives even though its per-transaction
  *approval* does not.
- **Check:** a test asserting `src/consilient/` contains no outbound network capability, so this ADR
  cannot be read as authorising one.

## What would overturn this — EXP-51, registered here

**Probe OpenRouter's spend controls against a real key, before any spend is authorised.**
Pre-registered questions, fixed now:

1. Does `limit_reset` accept `weekly` and `monthly`, or only `daily`? If only daily, Joe's
   requirement cannot be met vendor-side and the weaker harness-side enforcement must be declared as
   such rather than presented as a cap.
2. Does every completion response carry a `usage` object with a cost, on every model, including
   streamed and errored requests? Per-run attribution rests entirely on this.
3. Does the account-level cap surface through `GET /api/v1/key`, or is it invisible to the API? If
   invisible, the harness cannot reason about the principal's £100 and must not pretend to.
4. What actually happens at exhaustion — a clean 402, or a partial charge?

**Stopping rule, fixed before the probe:** if (2) fails on any tested model, per-run attribution is
not available and this ADR should be reduced to *"metered calls are permitted only with a human
present for each one"* — that is, back to ADR-0019 condition 3, with the ceiling as an addition
rather than a replacement.

## Reversal

`git revert` this commit and reinstate ADR-0019's condition 3. Nothing has been spent, no credential
has been stored, and no network path exists, so the reversal costs nothing but the decision.

# Adding a fourth runtime — what it has to clear before an adapter is written

**Date:** 20 August 2026
**Status:** `[measured]` for the machine state and the prior adapter results; `[asserted]` for
the admission argument. **Nothing here purchases, subscribes to or authenticates anything.**

---

## The ask

Joe, 20 August 2026: *"Let's also prepare to add SuperGrok support and I plan to upgrade to heavy
so we have 4 subscriptions working together."*

He holds 20× Max/Ultra plans on Claude, Codex and Cursor. **The upgrade is his purchase and his
decision** — ADR-0033 §2 reserves money leaving an account to the principal, and no agent here
may buy, subscribe or authenticate on his behalf.

## What is already known, before any research

**Nothing on this machine can reach Grok.** No `grok`, `grok-cli` or `xai` executable exists in
the Windows PATH or inside WSL. [measured] So the question is genuinely open rather than a
matter of wiring something already present.

**Six adapters exist** (EXP-05), and `backends.md` records the two findings that decide this
case before any new evidence arrives:

> *"the adapter confirms the required login or credential; an installed executable is not
> enough."* [measured]

> The metered composition **failed**: *"Failed before artefact production with no diff or usage
> telemetry; delayed cumulative billing prevents per-run attribution."* [measured]

That second one is the trap. **If SuperGrok is reachable only through the metered xAI API rather
than through the subscription, it lands on the exact failure that killed the OpenRouter
composition** — and ADR-0019, which is *unresolved* and forbids standing spend authorisation,
blocks it independently.

## The three-way decision, and only one branch leads to an adapter

| branch | consequence |
|---|---|
| **Headless access included in the subscription** | Adapter #7 is worth writing, and it becomes the cleanest test of ADR-0001's stopping rule since EXP-05. |
| **Chat surface only** | Not orchestrable. No adapter. The finding is that a subscription is not a runtime. |
| **Metered API only** | Blocked by ADR-0019, and the OpenRouter precedent says per-run accounting fails anyway. Requires Joe to resolve ADR-0019 first, which is his and has been open since 19 August. |

A fourth branch exists and must be checked before the others matter: **whether automated use of a
consumer subscription breaches its terms.** If it does, that decides the case regardless of
technical feasibility, and a harness that checks it before its operator does is doing its job.

## Why a fourth family is worth wanting, stated fairly

A fourth model family is a fourth **evidence class**, which `CONSILIENCE.md` names as the scarce
resource — *"more agents are cheap; genuinely different classes of facts are not."* Today's most
valuable results all came from cross-family work:

- a private-corpus leak found by a search the orchestrator's own method could not have run;
- this project's founding claim about self-improving systems **refuted** by a survey a different
  family ran;
- an apparent β agreement between two families exposed as arithmetic cancellation.

## And the argument against, which is not weak

**Today also measured that cross-family agreement can be an artefact.** Two families reported β
within 0.0085 while differing on 16 of 75 underlying labels; the agreement was 14× narrower than
their inputs warranted. [measured] More families multiply that risk unless each one's
*independence* is checked rather than assumed.

There is also a cost the enthusiasm hides. Today ran roughly fifteen dispatches across three
runtimes and produced: two silent launch failures, a sandbox that broke on a narrowing flag, a
stale clone that would have reverted 5,838 lines, and six separate stale-base incidents.
**Orchestration overhead is superlinear in runtimes**, and the dispatch layer's twelve measured
requirements exist because of it. A fourth runtime is a fourth set of sandbox flags, workspace
semantics, output-buffering behaviours and path conventions.

**Three families are already enough to break an echo**, and nothing measured today suggests the
fourth adds a *class* rather than a *duplicate*. The honest test: does Grok fail differently from
Codex and Cursor on the same task, or merely differently from Claude?

## What an adapter would have to satisfy

Not new rules — the existing ones, applied:

1. **Auth confirmed, not assumed.** An installed executable is not enough (EXP-05).
2. **Per-run accounting observable**, or admission restricted to bounded supervised work.
   ADR-0026: unknown headroom disqualifies unbounded work.
3. **Zero-inference capability probe at dispatch**, extending `exp27/handshake.py`, which
   already covers the three installed harnesses and whose Cursor probe had to learn a WSL
   boundary crossing the hard way.
4. **No metered spend without a resolved ADR-0019** and a numeric hard cap authorised by Joe.
5. **The fourth-family claim measured, not asserted** — run it on a task where the existing three
   have known outcomes and see whether it diverges.

## Falsifier

If Grok's headless path exists and its adapter fits the common ticket/result interface without
forcing a redesign, that is the **seventh** consecutive adapter to do so, and ADR-0001's stopping
rule — *"the second one did not force a redesign"* — becomes so well supported that continuing to
test it is no longer informative. At that point the interface claim should be promoted and the
adapter count stopped being evidence for anything.

Conversely, if it *does* force a redesign, that is the most interesting adapter result since
EXP-05 began and the stopping rule fires in the direction nobody has seen.

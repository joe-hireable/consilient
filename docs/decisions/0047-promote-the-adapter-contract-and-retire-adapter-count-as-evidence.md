# 0047. Promote the adapter contract, retire adapter count as evidence, and start measuring what an adapter costs

- **Status:** **ACCEPTED 20 August 2026** — the stopping rule was pre-registered in
  `fourth-runtime-admission-2026-08-20.md` and fired on measurement, so this records an outcome
  rather than making a choice. **The third clause is new and is a judgement**; Joe may cut it.
- **Date:** 2026-08-20
- **Supersedes in part:** [`0001`](0001-build-a-meta-harness-not-a-harness.md) — its adapter-count
  evidence, not its decision.
- **Inquiry tier reached:** T1 ground, `[measured]` on both counts below.
- **Executable model:** none. A stopping rule that fired needs no model.

## Context — a pre-registered falsifier fired

`fourth-runtime-admission-2026-08-20.md`, written before Grok Build was installed:

> If Grok's headless path exists and its adapter fits the common ticket/result interface **without
> forcing a redesign**, that is the **seventh** consecutive adapter to do so, and ADR-0001's
> stopping rule — *"the second one did not force a redesign"* — becomes so well supported that
> continuing to test it is no longer informative. At that point the interface claim should be
> promoted and the adapter count stopped being evidence for anything.

Grok Build 1.0.5 was installed and adapted on 20 August. The result, from the agent that built it:

> *"The common ticket/result interface held completely unchanged. Neither `ticket` (`id`, `goal`,
> `repo_dir`, `timeout_s`) nor `outcome` (`ticket_id`, `agent`, `domain`, `harness`, `provider`,
> `model`, `ok`, `diff`, `tokens_in`, `tokens_out`, `cost_usd`, `duration_s`, `raw_tail`) required
> any redesign."* [measured]

Seven distinct backends across eight adapter modules — Claude Code, Codex, Cursor (two protocols),
Antigravity, OpenCode, a model-backed path, and now Grok Build. **None forced a change to the
boundary.**

## Decision

1. **Promote the contract claim.** The `ticket` / `outcome` boundary is stable across seven
   independently designed coding agents from five vendors. It is no longer provisional and no longer
   needs defending by example.
2. **Retire adapter count as evidence.** An eighth adapter fitting tells us nothing we do not
   already know. **Do not cite "N adapters fit" in support of the interface again**, and do not run
   an adapter to test the boundary. Adapters are now built because a runtime is wanted, not because
   the contract needs another datum.
3. **Start measuring what an adapter costs**, because that is the quantity still in question and
   nobody has been watching it.

## Why the third clause exists — the measurement that complicates the good news

The contract held. The honest question is *at whose expense*, and the agent's own report answers it
without quite saying so: three internal seams absorbed vendor differences — permission flags (A5),
working-directory flags (A6), and a platform namespace problem (A7) where the npm package installs a
**Windows** binary that fails inside WSL with `no platform binary installed for linux-x64`,
requiring a `cmd.exe` bridge inside the adapter.

Non-blank lines per adapter module, measured at this commit: [measured]

| adapter | lines |
|---|---:|
| `claude_code` | 78 |
| `codex` | 90 |
| `antigravity` | 107 |
| `opencode` | 124 |
| `cursor` | 130 |
| `model_backed` | 148 |
| `cursor_acp` | 233 |
| **`grok`** | **295** |

**The newest adapter is the largest — 3.8× the smallest and 2.3× the median.**

So the two claims must be separated, and conflating them would be the easy mistake here:

- *"The contract is stable"* — **supported**, seven times, and now promoted.
- *"Adapters are cheap"* — **not supported**, and the trend points the other way.

Some of Grok's size is not the contract's fault: the metered-API-key refusal is policy (ADR-0044)
and the Windows/WSL bridge is platform. But that is precisely the point. **A boundary that never
moves while the things behind it grow is not obviously in the right place** — it may be a boundary
that has stopped mediating and started merely surviving. Nothing here settles that, and nothing will
until the cost is tracked rather than noticed once.

## Evidence against

- **Seven backends is not seven independent designs.** They converge on a common shape because they
  all wrap a terminal-invoked coding agent that takes a prompt and edits files, and because several
  post-date and imitate one another. The contract may be stable because the *market* converged, not
  because the abstraction is good — and it would break on the first genuinely different execution
  model (a hosted agent, a streaming bidirectional session, an agent that negotiates scope).
  `cursor_acp` at 233 lines is the closest thing to that case already present.
- **Line count is a crude proxy for cost.** It counts the API-key guard, the platform bridge and the
  usage-field normalisation as though they were the same kind of complexity. A better measure would
  separate contract-driven complexity from vendor- and policy-driven complexity, and none exists.
- **One data point is not a trend.** Grok is the only adapter written after the others; a single
  large newcomer may be an artefact of writing it under two constraints the others never had.
  Calling it a trend on n=1 is exactly the overreach this repository has caught in itself twice
  today.
- **Retiring the count could hide a real regression.** If an adapter *does* one day force a
  redesign, this ADR has removed the habit of noticing. Mitigated by the check below, which is why
  the check is not optional.

## Consequences

**Positive.** A settled boundary that no longer has to be re-litigated per runtime, and a new
quantity under measurement that was previously invisible.

**Negative.** A promoted claim is harder to overturn than a provisional one, and this one rests on
seven instances of a converging market.

**Neutral but load-bearing.** ADR-0001's *decision* stands entirely. Only the evidence it cited is
retired.

## Enforcement

- **Check:** a test recording per-adapter non-blank line counts, failing if a **new** adapter
  exceeds the current maximum (295) — not to forbid it, but to force the excess to be argued in the
  commit rather than absorbed silently. This is the ratchet shape already used for `append()`
  bypass and the A3 refusal baseline.
- **Check:** the ticket/outcome field set is asserted in a test, so a redesign becomes a visible
  failing check rather than a quiet edit. **This is what replaces the retired evidence** — the
  boundary is guarded by an assertion instead of by counting instances.

## What would overturn this

An adapter that cannot be written against the current contract. That would be the most informative
adapter result since EXP-05 began, and this ADR should be superseded rather than patched.

Separately: if per-adapter cost keeps rising while the contract holds, the boundary is in the wrong
place and the right response is to move it, not to celebrate its stability. The check above is what
would surface that, and it will take several more adapters to say anything — which is fine, because
adapters will now be written for use rather than for evidence.

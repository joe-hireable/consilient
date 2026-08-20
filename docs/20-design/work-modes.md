# Work modes — and the arithmetic that governs them

Status: v1+ design documentation. **None of this is v0.** v0 is coding, instrumentation
only, gated by ADR-0015 Stage 2 (trajectory log, verdict prompt, β-meter — nothing else).
This file exists so the modes are designed against the ceiling that constrains them,
rather than shipped as a feature list and discovered to be a queue generator.

## The six modes

One harness, one loader, no per-domain variants (see `architecture-sketch.md`). A mode is
a *scheduling and attention pattern*, not a different architecture:

| Mode | Shape | Human attention |
|---|---|---|
| **Chat** | Interactive, synchronous, single thread | Continuous |
| **Project** | Long-lived context + goals spanning many sessions | Recurring |
| **Task** | Single ticket, bounded, delegated | At completion |
| **Scheduled** (cron / one-off) | Fires without the user present | Deferred |
| **Background** | Runs while the user does something else | Deferred |
| **Parallel background workflows** | N of the above at once | Deferred, batched |

## The arithmetic warning — read this before wanting the last four `[algebra]`

`findings.md` §5: sustainable throughput is capped by **human review, not agent
capacity** — `n_max = T_cycle / T_review` ≈ 3 agents at realistic numbers (25-min cycles,
8-min reviews). That result does not care *when* the agents run:

- A cron agent running overnight for 8 h produces ~19 reviewable diffs
  (8 × 60 / 25). A 2-hour morning review budget absorbs 15 (at 8 min each).
  **One overnight agent can outproduce the morning.** Five do so five times over.
- Total daily review capacity is fixed human-hours ÷ `T_review`. Unattended modes do not
  add review hours; they **time-shift when the debt arrives**. Steady state:
  production ≤ review capacity, or the queue diverges — same identity, same ceiling.
- So: **unattended work accumulates review debt rather than eliminating it.** "Run more
  agents in the background" is the feature that feels productive while making the ceiling
  worse. This sentence is the point of this document.

Two second-order effects make unattended accumulation *worse* than the identity alone
suggests, both `[asserted]` pending measurement:

- **Staleness compounding.** N queued diffs against the same repo are diffs against the
  same base. Reviewing and merging them serially invalidates later ones — rebases,
  conflicts, semantic drift — so effective review cost per queued diff *rises* with queue
  length. The identity above is therefore optimistic for parallel background work on one
  repo. (Parallel worktrees on genuinely independent work units avoid this; parallel
  workflows on one surface do not.)
- **Batching may cut the other way.** Reviewing 15 diffs in one sitting may lower
  per-diff overhead versus context-switching all day. Direction unknown; measurable from
  the trajectory log once it exists.

## The only lever is the critic tier — which is β again

`findings.md` §5: a critic that rejects bad diffs pre-review raises the ceiling
(recall 0.85 → ~5 agents), and **critic recall ≡ 1 − β**. So the viability of every
unattended mode is governed by the same measured quantity as routing safety. A repo with
unmeasured β should not run unattended fleets; a repo with high β *cannot* run them
without the queue filling with plausible-looking bad work — which is strictly worse than
a queue of honest failures, because it consumes review time at the same rate while
shipping defects at rate β.

Verifier-shopping caveat (`experiments/capability_context_beta_star.py`, Part C):
unattended retry loops that resample until checks pass expose the verifier n times —
P(bad ships) = 1 − (1−β)ⁿ, i.e. 41% at β = 0.10, n = 5. Background modes that "keep
trying overnight" are the highest-exposure pattern in the product. `[algebra]`

## Sequencing

Modes ship only after (in order): β measured on real repos (EXP-01); critic recall
measured (EXP-08); the ceiling arithmetic re-derived from *measured* `T_cycle`,
`T_review`, and recall rather than the placeholder numbers above; and Q24 (does β exist
outside coding?) answered for any non-coding mode. Until then, every mode in this file is
a queue with better marketing.

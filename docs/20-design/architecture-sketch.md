# Architecture sketch

**Status: provisional design position, reconciled through ADR-0028 but not approved for
implementation.** [asserted] This exists to be attacked in the brainstorm; the reviewable
implementation boundary is the explicitly unapproved `../40-spec/v0-draft.md`. [asserted]

---

## What v0 is, in one sentence

A β-meter with a cascade attached.

Not a router. Not an agent framework. An instrument that measures whether a repository's
automated checks can be trusted, and derives its own routing depth and parallelism ceiling
from that measurement.

## Domain posture (added 19 Aug 2026)

The harness is **domain-blind**. It records every routable action as the explicit
`(domain, execution harness, provider, model)` composition from ADR-0027. [asserted]
The domain supplies the task and verifier contract; an existing execution harness supplies
tools, permissions and artefact production; the provider supplies inference transport and
accounting; the model is the measured capability target. [asserted]

For coding, OpenCode is the fallback harness when no vendor-native frontier harness is
authenticated. [asserted] Claude Code, Codex and Cursor are eligible only after an
authentication check; Antigravity additionally requires a verified plan/quota snapshot
and successful structured execution probe. [asserted] OpenRouter is a provider beneath
OpenCode or another harness, and remains directly reusable for non-coding work; it is not
itself labelled a coding agent. [asserted] Antigravity with Google-plan capacity, direct
Gemini API access and OpenRouter-hosted Gemini remain separate compositions and ledgers.
[asserted]

**One orchestration core, task-appropriate context, domain-owned verifier contracts.**
[asserted] A mode is a scheduling pattern rather than an execution identity
(`work-modes.md`). [asserted] Coding is v0 because it supplies cheap automated oracles —
tests, typecheck and build — against which β can be measured. [asserted] Whether β survives
outside coding is **Q24**, and the architecture has no measured centre in oracle-free
domains until it is answered. [asserted]

## The five components, and nothing else

### 1. The β-meter
Instruments every run with `verifier_verdict` and `human_verdict`. β is the rate at which
those disagree in the *accept* direction — checks passed, human rejected the diff.

Gates everything downstream:
- refuse to cascade below a repo's measured β\* for the capability gap in play
  (`findings.md` §2)
- set parallelism at `T_cycle / T_eff_review` rather than letting the user pick a number

**Open:** how few samples give a usable estimate (Q2); whether β is one number or a vector
per check class (Q10); whether cheap proxy labels (reverted commits, follow-up fixes,
escaped bugs) can substitute for human verdicts.

### 2. The cascade
Admit feasible resources → cheap → verify → mid → verify → frontier. Three capability
tiers remain the starting hypothesis (`findings.md` §3). [asserted]
Escalation on verifier failure, never on self-reported confidence (D12).
No learned prior in v0 (D6) — revisit only if escalation wall-clock cost proves ≥2× (§4a).
Included subscriptions and metered providers use separate ledgers: reset-aware allocation
maximises incremental verified value, while metered calls retain hard monetary caps
(ADR-0026, ADR-0028). [asserted]

### 3. The ticket store
Native, agent-first, local-first. SQLite WAL holds mutable coordination state and is a
rebuildable projection of the versioned append-only JSONL trajectory committed to git
(ADR-0006). [asserted]
Optional one-way sync adapters out to Linear / ClickUp for humans who want to watch.
[asserted] Build the state machine, not a Trello competitor. [asserted]

### 4. Parallel orchestration
Across git worktrees on **independent work units**. This is the regime where the
multi-agent literature says parallelism actually helps — genuinely independent contexts,
no shared state to lose. Hard budget caps per session (63 documented production
budget-overrun incidents; see `literature-review.md` §7).

Bounded meetings only, never open-ended chat (D9). Each meeting must name its exogenous
signal (D10) or it doesn't ship.

### 5. The critic tier
Rejects bad diffs before the human sees them. The only lever that raises the parallelism
ceiling (`findings.md` §5). Critic recall ≡ 1 − β, which is why the same instrument
measures both.

---

## What is deliberately absent from v0

Learned router · trajectory corpus as an asset · debate / model battling · RL ·
multi-channel access · voice · a home-grown model engine or catalogue · autonomous
unbounded spending · CASB / ToS scanning / compliance trails · the Inquiry tier (Q14).
[asserted]

Stable logical identity, performance personas and same-turn typed control remain behind
EXP-24–26. [asserted] Runtime identity, principal, task role, evidence class, artefact,
verifier and authority are required provenance fields from the first implementation
because they describe what happened rather than claiming a persona effect. [asserted]

Each of these was argued through and cut or deferred. See `decisions-so-far.md`.

---

## The shape of the claim

```
       one measured quantity  β
              │
      ┌───────┼───────┐
      ▼       ▼       ▼
   routing  parallelism  human
   safety    ceiling     review load
```

Everything else in the design is downstream of that identity. If β is not measurable
(Q2) or the identity does not hold in practice, this architecture has no centre and
should be replaced rather than patched.

---

## Adopt, don't invent

From `literature-review.md`, these are solved elsewhere and should be taken wholesale:

- **Cascade mechanics** — FrugalGPT, Hybrid LLM, Dekoninck et al.'s routing/cascading
  continuum.
- **Context/skill evolution** — ACE's Generator / Reflector / Curator loop (ICLR 2026).
  This is what `/learn` should be.
- **Trajectory log invariant** — DeepSeek Harness's rule that everything reaching a model
  request must be rebuildable from an append-only log.
- **The verification pipeline shape** — Joe's own `CODEBASE_ASSESSMENT.md` method:
  independent discovery → independent verification of every lead → fabrication audit.
  Measured ~0.5% fabrication rate, caught. See `30-source-material/prior-repo-assets.md`.

## Do not compete with

**Meta-Harness** (Stanford/MIT, COLM 2026) already automates harness search end-to-end.
Any framing of this project as "the harness optimises itself" is walking into a
well-funded, well-cited incumbent. The differentiation, if it exists, is measuring the
*trustworthiness of the repo's own verification layer* — which is a different object from
optimising a harness against a benchmark. **Establish that honestly in Q1 before building.**

# What to port from Joe's existing repos

Read 19 Aug 2026 via filesystem access: `jobboard-v2` (jobs.co.uk / A.R.I.) and `hermes`.

`hermes` is an empty `create-next-app` scaffold. Nothing to take.

Everything below is from `jobboard-v2`. **Most of v0 already exists there**, scattered
across a recruitment product.

---

## 1. The single most valuable asset: the assessment methodology

`CODEBASE_ASSESSMENT.md` documents its own method:

> 12 read-only discovery agents → 197 leads → independent verification of every lead
> (185 CONFIRMED / 11 NUANCED / **1 FABRICATED, excluded**) → 10 grouped scoring agents over
> 19 rubric dimensions → **5-citation fabrication audit per scorer (0 failures in 50
> sampled)** → orchestrator synthesis.

This is a working multi-agent system with an adversarial verification tier and a **measured
hallucination rate of ~0.5%, caught**, validated on a real 3,900-file codebase.

It is also the bounded-meeting primitive, already built. And it respects the multi-agent
theorem: discovery agents work independent sources (exogenous signal); verification agents
re-derive from primary evidence (exogenous signal). Neither is debate.

**Port this first.** It becomes the critic tier.

## 2. The ratchets — this is the β instrumentation, already written

From `AGENTS.md` / `CLAUDE.md`, all CI-blocking:

| Ratchet | What it enforces |
|---|---|
| R1 `docs:check-counts` | Headline counts vs codebase, 5% tolerance |
| R4 `check:coverage-ratchet` | Coverage cannot drop |
| R5 `check:test-deletion` | Tests cannot be deleted to move the bar |
| R6 `check:skipped-probes` | Skipped probes cannot increase |
| — `check:rls-coverage` / `-substrate` | Every table read under RLS has a policy |
| — `check:constitution-hash` | Governing doc drift requires an ADR in the same PR |
| — `check:action-pins` | SHA-pinned GitHub Actions, self-checking |
| — `invariants:check` + `audit:invariant-probes` | 44 invariant probes stay covered |
| — `check:openapi-fresh`, `check:no-raw-fetch-redux`, `check:substrate-liveness` | assorted |

~20 check scripts, most traceable to a specific documented incident (journal drift →
`check-drizzle-journal`; a `drizzle-kit push` index loss → restore migration + guard; prod
schema drift → daily audit workflow). **This is the Engineering Ratchet, implemented and
proven to fire.** It is also exactly the verifier suite whose β you would measure.

## 3. The cascade skeleton

- `src/lib/ai/llm.ts` — provider routing by model-id prefix, circuit breaker, kill switch
- `src/lib/ai/model-resolver.ts` — model choice by task class (ADR-0019)
- Decode-time schema enforcement via `messages.parse` + `zodOutputFormat`, with two
  documented production incidents driving the hardening

## 4. The permission model

`src/lib/agent/tools/` — ~72–82 tools registered at module load; at turn time
`catalogueFor(ctx)` filters the registry by channel, sender kind, relationship state and
**role, fail-closed**, before the model sees them. Tool errors return a structured
`ToolResult` that **loops back to the model** rather than aborting the run.

## 5. The guard layer

`.claude/hooks/` — `block-secret-files.mjs` (PreToolUse on Edit|Write),
`auto-format.mjs`, `nudge-wiki-ingest.mjs`. Plus a hermetic test setup that neutralises
leaked env and dead-ends `DATABASE_URL` so tests can never write to staging.

## 6. Other patterns worth stealing

- **Closed error contract**: RFC7807-lite `problem()` + a registry, with a test that walks
  every call site and fails on unregistered codes. Zero ad-hoc error JSON across 206 routes.
- **Async-by-default LLM work**: no model call in any user-facing request path; cron
  drainers with `FOR UPDATE SKIP LOCKED` claims.
- **`claimRows`** — transactional work claiming, directly reusable for ticket claiming by
  parallel agents.

---

## The lesson that must not be repeated

`CODEBASE_ASSESSMENT.md` D1 found that the documented "unified `llm()` boundary" is in
practice **five access paths**, with the circuit breaker and kill switch covering ~12 call
sites while the **highest-cost paths — the agent turn loop and the Opus judge — bypass them
entirely**. Seven modules construct their own SDK clients. Two different Google SDKs.

The idea was right. The enforcement was never written — despite the same repo containing
the exact pattern that would have fixed it (a custom eslint rule banning raw fetch in the
agent layer).

> **A chokepoint without a lint rule banning bypass is not a chokepoint.**

Under agentic development this drift happens faster. It is invariant **I1** in
`decisions-so-far.md`, and it is the reason this project must never ship a declared
boundary without its enforcement in the same commit.

Second lesson, same document: the flagship matching pipeline had **no producer** — pg_cron
drained a queue nothing ever filled, undetected because an empty queue is indistinguishable
from a healthy one. Hence invariant **I2**: documented behaviour ships with the test that
proves it.

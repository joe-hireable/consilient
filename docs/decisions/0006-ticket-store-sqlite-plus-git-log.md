# 0006. Ticket store: SQLite for coordination, append-only JSONL in git for the record

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Claude, at Joe's request ("you decide, argue for it")
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — the decision turns on a concurrency primitive that either
  exists or does not. Gate G4 (formalizability) is not satisfied; there is no free parameter.

## Update: 2026-08-20 — EXP-16 measured the external-tool grounds; the decision is unchanged

**The decision below stands exactly as written.** EXP-16 stopping rule 4 fired *with a
correction*, and the correction is to the grounds, not the conclusion. The rule that could
have overturned this ADR — external tools handle the state machine and concurrency without
material friction, therefore supersede — did **not** fire. Source:
`../10-research/exp16-results.md`, both the ClickUp arm and the Linear leg.

**The falsified ground was never in this file.** EXP-16's register entry attributes to
ADR-0006 the claim that external PM tools "impose human-shaped state machines, human-shaped
rate limits, and a webhook round-trip on every state change". The rate-limit and round-trip
half of that is now measured and did not bite: ~470 API calls, 24 concurrent comment writers
on ClickUp and 4 on Linear, **zero rate-limit responses and zero write conflicts**, with
bracketed latency of 8.8–24 s that is dominated by agent-turn overhead and was an annoyance
rather than a blocker. [measured] That half is not available as a ground for anything here.
It costs this ADR nothing, because the sentence originates in
`../30-source-material/gemini-session-critique.md` and never appeared in *Evidence* below —
which rests on git's missing atomic claim primitive, not on any external tool's behaviour.
The register's misattribution is not this file's to correct; what this update settles is that
**ADR-0006 may not be cited for a rate-limit or webhook argument.**

**What was measured, and what now carries the external-tool case: schema rigidity and
identity — on both tools, which is what makes them tool-independent rather than a complaint
about one vendor.**

- **Schema rigidity, loud (ClickUp).** 6 of 6 Owners hit `Status does not exist` setting
  `decided`; there was no way to discover the permitted statuses except by failing, and all
  six fell back to `complete`. Custom-field *creation* is not exposed over MCP, so the
  ADR-0020 authority matrix degraded to markdown in a description. [measured]
- **Schema rigidity, silent (Linear) — the sharpest single argument for a native store.**
  Requesting the nonexistent state `decided` produced **no error, and the issue stayed
  `Done`**. [measured] The write returned success; the record did not change. ClickUp rejects
  loudly, so an agent learns it failed; Linear's MCP layer coerces silently, so an agent
  believes it set a state the record does not hold. For a trajectory record whose whole value
  is that it says what happened, a silent divergence between the write and the stored state is
  strictly worse than a loud failure, because nothing downstream can detect it. [asserted] The
  workaround demonstrated — carrying the missing semantics in a label (`parked-awaiting-user`)
  — is structure theatre of the same kind as the matrix in markdown. [measured]
- **Identity.** Every issue and comment in both tools was created under a single OAuth
  identity (`createdBy: Joe Brown`). [measured] On ClickUp this laundered a fabricated
  human-participation claim into a meeting record no human joined: a relayed proposal was
  misattributed to Joe, and the scribe then recorded that Joe had contributed directly.
  [measured] That is Whewell clause 1 failing — a conclusion whose provenance has been
  discarded cannot participate in a consilience test at all — and it cannot be fixed from
  outside the tool.

**Checks, named rather than implied.** The identity ground has one and it has shipped:
`actor` is required on every event and V0-18 refuses a `human_decision` authored by anyone
but its named principal, in `src/consilience/events.py`, with tests. [measured] The
schema-rigidity ground has **no check** — a harness-owned status vocabulary is named as a
native-design inheritance in `exp16-results.md` and does not exist in the observe-only
increment. Until it ships, "the harness owns the status vocabulary" is `[asserted]` and owed.

**What this update does not touch.** EXP-16 measured concurrency against hosted HTTP APIs,
not against git. The strongest argument in *Evidence against* below — that at a realistic
ceiling of 2–3 parallel agents, git lock contention may never bite — is untouched by these
numbers and remains unresolved. [asserted]

## Context

`0001` makes the ticket store the interface between the meta-harness and the agents it
orchestrates. Q6 posed it as a binary: git-backed files (diffable, reviewable, free
trajectory record) or SQLite (query performance, transactional integrity under parallel
writes).

The binary is false, and seeing why decides the question.

## Decision

Use **both, for different objects**:

| Object | Substrate | In git? |
|---|---|---|
| Mutable coordination state — who holds which ticket, right now | SQLite (WAL) at `.harness/state.db` | No, gitignored |
| Immutable trajectory record — what happened; the substrate β is computed from | Append-only JSONL at `.harness/log/YYYY-MM-DD.jsonl` | Yes, committed |

**The database is a projection of the log.** State is rebuildable by replay. That is the
invariant, and it is directly testable.

## Evidence

- `[cited]` Git has no atomic claim primitive. `index.lock` is a repository-global mutex;
  parallel agents in worktrees share one `.git` directory, so N agents committing state
  transitions contend on the hot path and generate merge conflicts on the coordination
  object itself.
- `[cited]` There is no git analogue of `SELECT … FOR UPDATE SKIP LOCKED`. SQLite under WAL
  gives an atomic claim in a single `UPDATE … RETURNING`.
- `[measured]` The claim pattern already exists and is proven in `jobboard-v2`, as
  transactional row claiming in its queue drainers — see
  `../30-source-material/prior-repo-assets.md`. Porting a known-good primitive beats
  inventing one. (The file path and identifier that were here are private-corpus content and
  were removed on 20 August 2026 by a pre-publication leak audit.)
- `[cited]` DeepSeek Harness's runtime invariant — everything reaching a model request must
  be rebuildable from an append-only log — is the pattern `../20-design/architecture-sketch.md`
  already commits to adopting. This ADR is that adoption, with a queryable index on top.
- `[algebra]` β is a proportion over accepted diffs (`0002`). Computing it from a
  commit-walk is O(history); from an indexed table it is a single query. The β-meter is
  invoked on every routing decision.

## Evidence against

- Two substrates is more machinery than one, and machinery is what a solo maintainer cannot
  afford. The counter-argument is that they are genuinely different objects with different
  access patterns, and collapsing them means one of the two is served badly.
- A pure-git design would be more legible to contributors and would need no rebuild logic.
  If parallelism in v0 turns out to be 2–3 agents (which `../10-research/findings.md` §5
  suggests is the ceiling anyway), git lock contention may never bite in practice.
  **This is the strongest argument against and it is not resolved.**
- JSONL committed to git will grow. Log volume needs measuring before this is settled;
  a daily-file layout is a guess at the right granularity.

## Consequences

**Positive.** Atomic ticket claiming without inventing a primitive. β becomes a query.
The trajectory record is diffable, reviewable and survives a corrupted database. Rebuild
gives a free integrity test.

**Negative.** Two things to keep consistent. A replay path that must be maintained even
though it is rarely exercised. Repository growth.

**Neutral but load-bearing.** Fixes the JSONL event schema as a public interface — changing
it later breaks replay of historical logs, so schema versioning is required from the first
commit.

## Enforcement

- Check: `.harness/state.db` is gitignored, asserted by a test.
- Check: **delete the database, replay the log, assert byte-identical state.** Runs in CI on
  a fixture log. This is the invariant that makes "the database is a projection" true rather
  than aspirational, and it satisfies I2.
- Check: every JSONL event carries a schema version; a test asserts no unversioned events.
- Check: no code path writes coordination state to git, and none writes trajectory events
  only to SQLite. Enforced by module boundary lint, same commit (I1).

## What would overturn this

- Measured parallelism stays at 2–3 agents and git lock contention never materialises →
  drop SQLite, keep git only, and the design gets simpler.
- Log volume proves unmanageable in a repository → move the log out of git and lose the
  reviewability argument, at which point reconsider the whole split.

## Publication candidate?

No.

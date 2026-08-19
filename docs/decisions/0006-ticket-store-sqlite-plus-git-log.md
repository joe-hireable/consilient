# 0006. Ticket store: SQLite for coordination, append-only JSONL in git for the record

- **Status:** ACCEPTED
- **Date:** 2026-08-19
- **Deciders:** Claude, at Joe's request ("you decide, argue for it")
- **Inquiry tier reached:** T1 ground
- **Executable model:** none — the decision turns on a concurrency primitive that either
  exists or does not. Gate G4 (formalizability) is not satisfied; there is no free parameter.

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
- `[measured]` The claim pattern already exists and is proven in `jobboard-v2`
  (`src/lib/db/claim-rows.ts`, `FOR UPDATE SKIP LOCKED` in the cron drainers) — see
  `../30-source-material/prior-repo-assets.md`. Porting a known-good primitive beats
  inventing one.
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

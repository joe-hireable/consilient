# Friction log

**Every manual step in the bootstrap harness that Consilience should automate.**
This is the v0 backlog, derived from use rather than imagination. See ADR-0017.

## How to keep it

One line per friction, dated, written **the moment it bites** — not reconstructed later,
because reconstruction remembers the dramatic frictions and forgets the frequent ones, and
the frequent ones are what matter.

```
| date | what I had to do by hand | how often | what would automate it |
```

**Never delete a line.** When Consilience automates something, add the commit reference in
the last column. The log is a record of what the tool is *for*; deleting satisfied entries
erases the justification for features that exist.

**Be honest about the ones that never recur.** A friction logged once and never repeated is
evidence *against* building for it. Mark those `one-off` rather than quietly leaving them
to inflate the backlog.

## The test this log exists to run

ADR-0017 states it plainly: if this log stays short for a month, one of two things is true.

1. **Claude Code is already sufficient**, and Consilience solves a problem Joe does not
   personally have. That is a serious finding for ADR-0004's premise that "the smallest
   thing worth a stranger's install and the smallest thing that improves my week are the
   same artefact" — and it should be reported, not buried.
2. **The log is not being kept honestly**, which is the more likely explanation and worth
   naming in advance.

Either way, a short log is information. Do not pad it.

## Log

| date | manual step | frequency | would be automated by |
|---|---|---|---|
| 2026-08-19 | Chose which model to use for a task by feel, with no measurement of whether the cheap one would have sufficed | every task | the cascade + β-meter (ADR-0002) |
| 2026-08-19 | Re-explained project context at session start despite `CLAUDE.md` | every session | memory layer wake-up (ADR-0017) |
| 2026-08-19 | Manually decided whether a design question warranted research vs answering from priors | several times per session | the Inquiry tier trigger (`docs/20-design/inquiry-tier.md`) |
| 2026-08-19 | Checked prior art by hand and found three times that a feature already existed | per feature idea | `checking-prior-art` skill; possibly a standing pre-design check |

*(Seed entries from the session that produced this repository. Add as you go.)*

**EXP-16 entries (19 Aug 2026) — frictions hit while prototyping the meeting layer on
rented PM tools:**

| date | manual step | frequency | would be automated by |
|---|---|---|---|
| 2026-08-19 | Linear MCP requires interactive browser OAuth; an agent cannot connect a PM tool alone — one experiment arm blocked on a human | once per tool | native store needing no third-party auth; or a credential broker (ADR-0019 territory) |
| 2026-08-19 | ClickUp MCP reads custom fields but cannot create field definitions — the RACI matrix degraded to markdown-in-description on day one | per workspace | native ticket store with typed role fields (ADR-0006 schema change from ADR-0020) |
| 2026-08-19 | Every agent write lands under one OAuth identity ("Joe") — per-agent attribution impossible in ClickUp and Slack, making ADR-0020's "outcome writes attributed to the Owner only" check unenforceable | every write | native store with a first-class `actor` field per event |
| 2026-08-19 | Six of six meeting Owners hit `Status does not exist` setting a `decided` status; no way to discover a list's valid statuses except a failed write or an extra call | every decision close | harness-owned decision state machine |
| 2026-08-19 | Latency instrumentation had to bracket MCP calls with separate Bash timestamp calls — measurements contaminated by agent-turn overhead | every measurement | harness-level tool-call telemetry in the trajectory log |
| 2026-08-19 | Parallel agents cannot safely append to one JSONL trajectory file; the orchestrator became the single writer by hand | every multi-agent run | exactly ADR-0006's split: SQLite for concurrent state, single-writer append-only log |
| 2026-08-19 | Verified licences of 20+ candidate tools by hand (GitHub API + raw LICENSE files) because directory listings and blog posts misstate them — found one proprietary landmine (anthropics/skills doc skills) in an "open" repo | per curation pass | licence audit in the capability loader; blocks bundling non-OSS |
| 2026-08-19 | Hand-checked four vendor blog figures at origin: three were single illustrative examples presented as results, one had an undefined metric | per cited number | the existing [FULL]-before-cite rule, enforced by the citing-sources skill |
| 2026-08-19 | Assembled a model's reasoning-capability tri-state by hand from three registries with three different flag semantics | per model considered | registry adapter with normalised tri-state (ADR-0025 territory) |
| 2026-08-19 | Nearly installed `cursor-agent` from npm — it is an unrelated individual's package, not Anysphere's CLI. Caught only by checking maintainer/repo before installing | per new tool adopted | the ADR-0016 supply-chain check, automated: verify publisher identity against the vendor's own documented install route before any install |
| 2026-08-19 | Installed Cursor's CLI into WSL because it ships linux/darwin only, then hand-wrote a path-translation seam (`C:\…` ↔ `/mnt/c/…`) so the orchestrator and agent could name the same directory | per cross-namespace agent | namespace-aware paths in the ticket schema (the interface change adapter #3 forced) |
| 2026-08-19 | Reconciled three mutually incompatible token/cost accountings by hand (Claude: last-call tokens + cost; Codex: cumulative session tokens, no cost; Cursor: neither) | per backend comparison | per-adapter accounting normalisation, or an explicit "not comparable" contract in the outcome schema |
| 2026-08-19 | Inspected a saved scratch repository by hand after a backend process exited successfully with no final message and no file change; the runner's `ok` signal contradicted the verifier | per ambiguous backend completion | record runner completion and verifier acceptance as separate fields, with only the verifier allowed to accept the artifact |

## What does not belong here

- Bugs in Claude Code. Those go upstream.
- Things that are annoying but that Consilience should not do. Scope creep enters through
  this file more easily than anywhere else, because every friction feels like a feature
  request.
- Frictions with no plausible automation. Log them if you like, but mark them
  `not-automatable` so they do not silently become requirements.

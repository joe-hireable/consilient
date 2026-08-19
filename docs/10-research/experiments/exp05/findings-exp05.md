# EXP-05 findings — the adapter surface, measured

Run 19 Aug 2026. Adapter #1 (Claude Code 2.1.235) written first with its assumptions
recorded; adapter #2 (codex-cli 0.148.0) written **without modifying adapter #1**; every
divergence recorded here. Total build+run time: well inside the one-day budget (~40 min).

## Headline: the stopping rule does NOT fire — with stated limits

ADR-0001's stopping rule: *"if adapter #2 forces a redesign of the interface and #3
forces another, the surface is not stable enough for one maintainer."* **Adapter #2 did
not force an interface redesign.** The `run(ticket) → outcome` contract (spawn, feed a
ticket, collect a diff + verdict) absorbed every difference inside ~80 adapter lines.
But 4 of the 6 assumptions baked into adapter #1 broke *within* it:

| Assumption (from adapter #1) | Codex reality | Verdict |
|---|---|---|
| A1 one-shot non-interactive invocation | `codex exec` is exactly that | **held** |
| A2 single JSON result object on stdout | JSONL *event stream* (`--json`); final message goes to a **file** (`--output-last-message`) | **broke** |
| A3 token/cost accounting in the result | No `cost_usd` anywhere; usage via stream events with different field names. And A3 was already misleading in adapter #1: Claude's `usage.input_tokens` is the *last call*, not the session (measured: 6 tokens in for a 19.6 s run costing $1.02) | **broke, both ways** |
| A4 artifact = `git diff` afterwards | identical | **held** |
| A5 permissions pre-granted via one flag | Two-axis model: sandbox (`read-only`/`workspace-write`/`danger-full-access`) × approval policy — mapped approximately, not equivalently | **broke** |
| A6 process cwd scopes the agent | Explicit `-C` flag; non-git dirs also need `--skip-git-repo-check` | **broke** |

**Consequences for the real interface** (design input, not yet an ADR change):
- `cost_usd` and token fields must be *optional and per-adapter-approximate* — no common
  accounting contract exists across the two vendors measured, or even reliably within
  one.
- The result channel must be adapter-owned (stdout-JSON vs stream+file); only the
  *outcome schema* is common.
- Permission mapping is per-adapter policy, not a shared flag — and it is safety-relevant
  (the closest Codex equivalent to Claude's skip flag disables sandboxing entirely).

## Smoke results `[measured]`

| | Claude Code | Codex |
|---|---|---|
| ok | true | false — **401 Unauthorized** (not logged in; interactive `codex login` required) |
| diff correct / tests pass | yes / yes (2 passed) | no run — auth-blocked |
| duration | 19.6 s | 17.9 s to 5× websocket retry exhaustion |
| cost | $1.02 (reported) | not reported (by design) |

The auth block is the third instance of the EXP-16 finding: **interactive human-at-a-
browser auth is a standing friction class across the delegated-agent ecosystem** (Linear
OAuth, ClickUp identity, now Codex login). The native store/adapters must treat
"credentialed but headless" as the design case, not the exception.

## Bonus finding — Codex as a local-tier runner

`codex exec --oss --local-provider {lmstudio,ollama}` runs the same harness against
local open models. That is a potential **cheap-tier execution path the cascade gets for
free** — one adapter, two tiers — and it interacts with ADR-0025's probe (the paired
probe could run both tiers through the *same* adapter, holding harness effects
constant). `[cited from --help; unmeasured]`

## Honest limits

- Smoke-scale: one trivial ticket. Interface stress (long runs, mid-run failures,
  streaming progress, budget caps) untested.
- The live Codex leg is pending `codex login` — parked, not skipped.
- Adapter #3 (opencode or Antigravity CLI) unwritten; the stopping rule's second clause
  is still open. opencode's registry (models.dev) suggests its surface is closest to
  Codex's; Antigravity is the wildcard.

## Register status

EXP-05: partially DONE — adapters #1+#2 written, breakage recorded, stopping rule not
fired on this evidence. Remaining: live Codex run (auth), adapter #3.

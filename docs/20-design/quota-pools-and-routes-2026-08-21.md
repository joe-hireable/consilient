# Quota pools and the routes that reach them — 21 August 2026

- **Artefact class:** the *schema* and the *rules* below are **PRODUCT** — they ship open source
  and apply to anyone holding more than one flat-fee subscription. Every **number, model id,
  file path and account observation is INSTANCE** — Joe Brown's Cursor Ultra seat and this
  Windows 11 machine — and is fenced in the sections marked INSTANCE. No credential appears
  here and none was read.
- **Companion to** [`../decisions/0056-schedule-work-across-prepaid-quota-pools-and-never-shed-to-spend.md`](../decisions/0056-schedule-work-across-prepaid-quota-pools-and-never-shed-to-spend.md).
- **Boundary with [`ADR-0054`](../decisions/0054-route-by-measured-capability-against-a-verifier-contract-never-by-a-harness-label.md):**
  0054 decides *which composition is able to do the work*. This table decides *which already-paid
  allowance pays for it*. Capability filters; quota schedules. Where they disagree, capability
  wins — an idle pool is never a reason to route work to a composition that cannot do it.

---

## The table is three joins, and only one of them is measured

A "task class → route → pool" table looks like one mapping. It is three, and they have
different evidence:

| Join | Owner | Status today |
|---|---|---|
| task family → admissible composition | ADR-0054's capability rows | **not measured.** 0054 is PROVISIONAL and its rows do not exist yet. Not duplicated here. |
| route → served model | this document | **`[measured]`** for five of seven routes, server-attested. |
| served model → quota pool | this document | **not measured for any Cursor route.** This is the gap. |

"Task class" is the brief's term; the project's term is **task family**, defined in `v0-draft.md` §5
and already a field in `src/consilient/beta.py` and an index column in
`src/consilient/projection.py`. [measured] ADR-0054 §2 makes the same correction. The
task-family column is deliberately absent below rather than filled with nulls.

---

## Model resolution — what the third column means

| Value | What was observed |
|---|---|
| **server-attested** | The CLI's own session store records `"providerOptions":{"cursor":{"modelName":"…"}}` on the assistant turn, in the same record as the probe's unique token. The server names the model it served; the client does not echo the flag. |
| **validated** | The requested id was accepted, and a deliberately bogus id was refused (`Cannot use this model`, exit 1, 3 s, no session directory, zero tokens), so there is no silent fallback to the account default. Weaker than attestation: nothing names the served model. |
| **drifts** | No stable model. The same command resolves differently minute to minute. |

---

## Routing table — INSTANCE (Joe's Cursor Ultra seat, 21 August 2026, 01:57–03:05Z)

All Cursor rows share the prefix
`wsl.exe -d Ubuntu -- /home/jpbpr/.local/bin/cursor-agent --print --output-format text --mode ask --trust --workspace <scratchpad>`.

| # | Route | Model flag | Runs? | Model resolution | Served model | Pool | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | `cursor-agent-composer` | `--model composer-2.5` | yes `[measured]` | server-attested `[measured]` | `composer-2.5` | **unknown** `[asserted]` — consistent with Cursor Models, never counted | usable, pool unattributed |
| 2 | `cursor-agent-cursor-grok-46` | `--model cursor-grok-4.6-medium` | yes `[measured]` | server-attested `[measured]` | `cursor-grok-4.6-medium` | **unknown** `[asserted]` | usable, pool unattributed |
| 3 | `cursor-agent-cursor-grok-45` | `--model cursor-grok-4.5-medium` | yes `[measured]` | validated `[measured]` | not attested | **unknown** `[asserted]` | usable, pool unattributed |
| 4 | `cursor-agent-parameterized-base-id` | `--model "grok-4.6[effort=medium,fast=true]"` | yes `[measured]` | server-attested `[measured]` | `cursor-grok-4.6-medium-fast` | **unknown** `[asserted]` | usable, but **prefer the canonical id** — caveat 3 |
| 5 | `cursor-agent-auto` | `--model auto` | yes `[measured]` | server-attested, 8/8 runs `[measured]` | `cursor-grok-4.5-high-fast` | **unknown** `[asserted]` | usable; resolution is server-side and is not a contract |
| 6 | `cursor-agent-default` | *(none)* | yes `[measured]` | **drifts** `[measured]` | `grok-4.6` → `composer-2.5` → `default` in 3 min 30 s | **undefinable** | **BANNED.** Caveat 1 |
| 7 | `cursor-agent-thirdparty` | `--model gpt-5-mini` | yes `[measured]` | server-attested `[measured]` | OpenAI-family (`fc_`/`rs_` server-minted id shapes; system prompt "powered by GPT-5 Mini") | **Other Models** `[asserted]` — the pool at 58% | negative control; ran as designed |
| 8 | `grok-bot` | — | **no route** | — | — | Grok Bot weekly, 0% | **UNREACHABLE.** No CLI, API, webhook or headless invocation is documented `[cited]`; no `bot` subcommand in `cursor-agent --help` and the desktop app is not installed `[measured]` |
| 9 | `cloud-agents-api` | `POST https://api.cursor.com/v1/agents` | **untested** | — | — | unknown | **UNAVAILABLE.** `CURSOR_API_KEY` unset in both Windows and WSL `[measured]`; never exercised end to end |
| 10 | `openrouter` | — | n/a | n/a | n/a | **money, not quota** | The only permitted metered vendor (ADR-0044). Ceilings enforced by `src/consilient/budget.py`. **Never a shed target** — ADR-0056 D3 |

**Read the pool column honestly.** Not one Cursor row says `cursor-models`. Every Cursor
invocation measured tonight produced a real billable request with a `request_id` and token
counts, and **no artefact anywhere named a pool**. Rows 1–5 are `unknown`, not `cursor-models`,
because that upgrade would repeat the 19 August SuperGrok/Grok Build CLI error exactly: the brand
matched, the model name matched, and the pool did not.

### What corroborates the 58% / 1% split without measuring a pool

`~/.cursor/ai-tracking/ai-code-tracking.db` (WSL, 17 MB) is a per-request local ledger:
45,056 rows, 448 distinct `requestId`s, all `source='cli'`, 19–21 Aug — `gemini-3.7-flash` 224,
`claude-opus-5` 135, `gpt-5.6-sol` 86, `kimi-k3` 2, `default` 1. **Zero grok rows and zero
composer rows.** [measured] Independently, across 78 `.harness/log/*.jsonl` files in the
consilience family, `gemini-3.7-flash-high` accounts for 76 of 76 Cursor model attributions —
100%, with zero `cursor-grok-*` and zero `composer-*`. [measured]

That is a different class of fact from the dashboard screenshot and it agrees with it. It still
does not attribute a pool: the ledger logs only requests that *wrote code* (a `--mode ask` probe
leaves no row, so it is a lower bound) and it has no pool or cost concept. [measured]

---

## Caveats that change what a harness may do — INSTANCE

1. **Never dispatch without `--model`.** Route 6's model was observed at four instants from one
   machine: `grok-4.6` (01:57Z), `grok-4.6` (01:59:09Z), `composer-2.5` (01:59:53Z), `default`
   (02:00:30Z) — three distinct values in 3 min 30 s, none set by the observing agent, because
   the CLI rewrites `~/.cursor/cli-config.json` on every invocation and concurrent agents share
   it. [measured] A route whose pool is decided by shared mutable state has no pool to attribute.

2. **The account default already moved during the audit.** It read *Gemini 3.7 Flash High* on
   20 August and *Cursor Grok 4.6 Medium Fast* at 02:45 on 21 August. [measured] The same
   unchanged dispatch code consumed a different pool before and after. Under ADR-0027 that is a
   **different composition**, not a cheaper route to the same one, and Cursor results recorded
   under Gemini may not be pooled with results recorded under Grok.

3. **`grok-4.6` is an undocumented alias.** It is accepted and resolves to
   `cursor-grok-4.6-medium-fast`, but it does not appear in `cursor-agent --list-models`.
   [measured] Pin the canonical id in a harness.

4. **`--output-format text` destroys the evidence.** The production shell route on this machine
   used `--output-format text`, which discards the JSON envelope carrying `session_id`,
   `request_id` and token counts. [measured] `dispatch.py:1467` then hardcodes
   `model="unknown:not-reported-by-runtime"` into every `Outcome`, for every runtime — while
   `adapter_cursor.py:95-108` already has a `model_fields()` that separates *requested* from
   *selected*. [measured] That pair is why a 58%/1% split ran for a month unnoticed.

5. **`--mode ask` is not a sandbox.** `--help` calls it read-only, and it is read-only with
   respect to the user's files by intent — but a measured `--mode ask --trust` run wrote
   `meta.json` and a 106 KB `store.db` and executed a `Read` tool call on a path **outside** the
   declared `--workspace`. `--help` says of `-p/--print`: *"Has access to all tools, including
   write and shell."* [measured] No repository was touched tonight, but the safety argument for
   these probes is `[asserted]`, not established. Confine probes by workspace *and* by what the
   filesystem permits.

6. **On Windows, `wsl.exe` argument handling has two live traps.** Git Bash MSYS path conversion
   rewrites a leading `/home/...` argument to `C:/Program Files/Git/home/...`; and an inline
   variable was flattened by the `wsl.exe` argv round-trip so a redirect failed with *Permission
   denied* **while the exit code still read 0**. [measured] Pass WSL commands as script files
   under `/mnt/c/...`, set `MSYS_NO_PATHCONV=1`, and verify by artefact size, never by exit code.

7. **`/usr/bin/python3` inside WSL, explicitly.** Bare `python3` in WSL resolves to
   `/home/jpbpr/.local/bin/python3`, a Windows PE executable leaking through PATH interop that
   mangles Linux paths into `C:\tmp\...`. `sqlite3` is not installed in WSL. [measured]

---

## Which pools can be reached from a command line

| Pool | Reachable headlessly? | Evidence |
|---|---|---|
| **Cursor Models** (Cursor Grok, Composer) | **Yes, a route exists** — rows 1–5 run and resolve to first-party models. **That the route debits this pool is unproven.** | route `[measured]`, pool `[asserted]` |
| **Other Models** (third-party) | **Yes** — row 7, and it is what the harness has been consuming all along | route `[measured]`, pool `[asserted]` from vendor docs plus the local ledger's 448 third-party rows |
| **Grok Bot** (weekly) | **No.** Human-facing desktop/iOS product; sign-in is the Cursor account; no documented CLI, API, webhook or headless entry point | `[cited]` docs.x.ai and cursor.com/help; `[measured]` absent from `cursor-agent --help` and not installed |

**The Grok Bot trap, recorded so nobody re-treads it.** Searching "Grok Bot headless" returns
`docs.x.ai/build/cli/headless-scripting`. That page belongs to **Grok Build**, xAI's coding-agent
CLI — the `grok` binary already on this machine's PATH at `C:/nvm4w/nodejs/grok` with live state
in `C:/Users/jpbpr/.grok/`. Same vendor, adjacent name, **different product and different
quota**. [cited + measured] This is the identical mistake made on 19 August. Any agent handed
"make Grok Bot work headlessly" will land there within two minutes.

**Grok Bot is not automatable and the recommendation is to stop.** The only conceivable path is
GUI-automating the Electron client, which needs an install and a signed-in GUI session, breaks on
every app update, and would put a Bot with a browser and terminal on a cloud VM acting under
Joe's identity. The strongest objection: 0% of a weekly pool for four weeks is real paid capacity
being written off, and Joe could use it manually for research and ops he currently does by hand.
That is worth telling him; it is not something Consilient can dispatch to.

---

## The counter that does exist, and was wrongly reported absent — INSTANCE

Five of six probe reports state that no programmatic quota counter exists on this machine. **That
is false, and the correction is the single most useful finding of the audit.** [measured]

The installed CLI bundle (`/home/jpbpr/.local/share/cursor-agent/versions/2026.08.11-e8db854/`)
carries a full quota client: `src/usage/usage-command.ts`, `src/usage/usage-data.ts`, and a
registered command `{id:"usage", title:"Usage", description:"Show plan and on-demand usage"}`.
`aiserver.v1.DashboardService` (Connect-RPC, default host `https://api2.cursor.sh`) exposes
`GetCurrentPeriodUsage`, `GetFilteredUsageEvents`, `GetAggregatedUsageEvents`,
`GetDailySpendByCategory`, `GetPlanInfo`. `UsageEventDetails` carries field 17 `routed_model` and
field 18 `requested_model_selection`; `ModelUsageAggregation` carries
`{model_intent, input_tokens, output_tokens, cache_write_tokens, cache_read_tokens, total_cents}`;
`UsageEventKind` distinguishes `INCLUDED_IN_ULTRA` from `USAGE_BASED` from
`ABORTED_NOT_CHARGED`. The command is hidden by a **client-side capability literal** —
`enableUsageCommand:true` for kind `remote`, explicitly overridden to `false` for
`local-authenticated`. Grepping `--help` (where a slash command never appears) and concluding
"none is readable" is how five reports reached the wrong conclusion.

Two honest limits on that finding. **Nobody has called it** — every claim above is read off the
JS bundle's literal protobuf descriptors, not off a live response; the bearer scope may be
`AiService`-only and a CLI-originated request may produce no usage event at all. And the three
dashboard pools **do not exist as counters anywhere**: grepping all 75 bundle files for the pool
labels returns only `e[e.GROK_BOT=33]` and `BACKGROUND_COMPOSER_SOURCE_GROK_BOT`, a
background-composer *source* enum, not a usage bucket; "Cursor Models" and "Other Models" appear
nowhere. [measured] The pools are a **presentation-layer grouping the dashboard computes over
per-model usage events**. So the reachable oracle is *per-request, per-model, with a billing
kind* — materially stronger than an invocation's self-report — and the last step from models to
pool percentages is a grouping rule we would be inferring. One human dashboard read binds it,
once.

That is what **EXP-94** would run. It needs Joe's authorisation because it handles a live bearer
token, and it must never touch `SetHardLimit` or `SetUsageBasedPremiumRequests`, which sit on the
same service — which is why the ADR-0056 lint check ships before the experiment, not after it.

---

## Why tonight's measurements cannot be repaired by re-reading the dashboard

Two independent reasons, either sufficient. **Resolution:** the dashboard reports integer percent
over a 30-day window and reads 1% for Cursor Models; a probe consuming ~21k input tokens cannot
move it by a resolvable amount. [measured] **Contamination:** between 02:58 and 03:05 local,
12–20 sibling `cursor-agent` sessions were written under the *same* workspace-hash directory
`264012d2faa6aa11e9c5f9540e6f0e22` — the chat store is keyed by workspace path, and every
concurrent agent used the same scratchpad. At least three different models carried the same
`CURSOR_POOL_PROBE` marker within a 44-second window. [measured]

**Therefore: any pool attribution derived from a dashboard delta taken tonight is contaminated and
must be rejected, including one reported as "confirmed".** The `--workspace`-keyed chat store also
means session-count baselines taken at depth 1 (`ls ~/.cursor/chats | wc -l`) were structurally
incapable of moving for a depth-2 write — a check that could not fail, the same failure class as
the 20 August repair to the CI replay step.

---

## Interface a pool-aware scheduler needs — PRODUCT

Recorded, **not built** — ADR-0056 is PROVISIONAL and clause D4 makes the scheduler inert until
EXP-94 lands. This is the shape to build against, and the shape *not* to reach for:

```
Allowance(pool: str, period: "weekly" | "monthly",
          consumed: Decimal, ceiling: Decimal, unit: str,
          observed_at: datetime, attribution: "measured" | "asserted")
```

- **Same fail-closed discipline as `src/consilient/budget.py`:** absent state refuses, stale state
  refuses, a period boundary crossed since `observed_at` refuses. `budget.py` uses a 15-minute
  `_STATE_MAX_AGE`; a pool ledger should reuse that number until a reconciliation latency is
  measured.
- **Do not extend `check_budget` to carry it.** `budget.py` is money-denominated by construction
  (`METERED_PROVIDER = "openrouter"`, `METERED_CURRENCY = "USD"`) and refuses any request whose
  currency differs. That currency-typed refusal is load-bearing in a module whose entire job is
  refusing to spend money. Widening it to a generic counter is how a money guard stops being one.
  A pool ledger is a **sibling**, not a generalisation.
- **`attribution` is a field, not a comment.** Clause D4: a pool may only be a *shed target* when
  its attribution is `measured`. Every Cursor pool is `asserted` today.

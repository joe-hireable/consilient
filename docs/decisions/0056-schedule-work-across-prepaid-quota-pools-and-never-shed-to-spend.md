# 0056. Treat prepaid quota pools as a first-class scheduling constraint, shed a near-exhausted pool onto an idle one, and never shed onto spend

- **Status:** **PROVISIONAL 21 August 2026.** The three clauses that cost nothing to be wrong
  about (D1, D2, D5) ship with this ADR and one of them ships with its check. The two that
  allocate work across pools (D3, D4) are **inert by construction** until **EXP-94** attributes
  at least one pool by measurement. No pool attribution in this repository is `[measured]`.
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (the instruction: *"we are not effectively utilising grok bot and cursor
  models such as cursor grok and composer usage limits via the cursor ultra subscription"*). The
  clause structure, the refusal to upgrade any pool tag, the inertness of D3/D4, the boundary
  with ADR-0054 and every objection in *Evidence against* are mine. Three of them contradict the
  brief that produced this ADR.
- **Inquiry tier reached:** **T3 measure, and the measurement came back negative.** Seven routes
  were probed on a live account; five resolved a model with server attestation; **zero attributed
  a pool.** That is a result, not a gap in effort, and it is why the ADR is PROVISIONAL rather
  than ACCEPTED.
- **Executable model:** none. `../20-design/inquiry-tier.md` gates a model on a formalizable
  *unknown parameter*. The decision variable (which pool pays) and the objective (accepted
  artefacts per unit of prepaid allowance before reset) are already carried by ADR-0002's closed
  form and ADR-0028's expiring-capacity argument. The one unknown here — *which pool a given
  model debits* — is a **lookup, not a parameter**: it has a discrete true value that one RPC
  call would read. A model would be a way of not making that call.
- **Artefact class:** **PRODUCT.** The scheduling rule ships open source and applies to anyone
  holding more than one flat-fee subscription. Every account figure, model id and file path is
  **INSTANCE** and lives in
  [`../20-design/quota-pools-and-routes-2026-08-21.md`](../20-design/quota-pools-and-routes-2026-08-21.md),
  labelled there. No credential appears in either document and none was read.

---

## Correcting the brief that produced this ADR

Four corrections. The third changes what gets built; the fourth changes where.

**1. "We are using exactly one pool" is true of the past and false as a stable property.** The
local per-request ledger corroborates the dashboard independently: 448 distinct `requestId`s,
all `source='cli'`, split `gemini-3.7-flash` 224 / `claude-opus-5` 135 / `gpt-5.6-sol` 86 /
`kimi-k3` 2, with **zero grok and zero composer rows**; and 76 of 76 Cursor model attributions
across 78 trajectory logs are `gemini-3.7-flash-high`. [measured] But the account default flipped
from *Gemini 3.7 Flash High* (20 Aug) to *Cursor Grok 4.6 Medium Fast* (02:45, 21 Aug) with no
code change. [measured] **The pool was never a property of the dispatch code; it was Cursor UI
state.** Anyone re-running this audit tomorrow gets a different answer from an unchanged
repository. That is the finding, and it is worse than the one the brief describes.

**2. "Route" is not the unit that determines the pool; the *served model* is.** Two of the seven
routes do not pin a model at all — `--model auto` resolves server-side, and the no-flag default
resolved to three different models in 3 min 30 s. A route → pool table is only well-formed for
routes that pin the model, which is why D2 exists as a separate clause.

**3. "Wire pool-aware selection in if a route was genuinely confirmed" conflates two
confirmations, and only one of them happened.** *This route runs and resolves model X* is
confirmed for five routes, server-attested inside the CLI's own session store. *This route debits
pool P* is confirmed for none. The brief's implementation clause is keyed to the second. Building
a pool-aware scheduler on the first would encode `[cited]` vendor grouping as if it were
measurement — the precise error made about SuperGrok Heavy versus Grok Build CLI on 19 August,
where the brand matched, the model name matched, and the pool did not. **So D3 and D4 ship as
policy and are inert until EXP-94.** Under ADR-0049 experiments inform rather than gate and under
ADR-0050 only an experiment whose largest possible effect changes *what* gets built may block it;
neither is violated, because what is withheld is not the build but the *activation* of a rule
whose input does not exist yet.

**4. "Wire it into the dispatch path" is not executable in the worktree I was told to work in,
and doing it would break a shipped invariant.** `src/consilient/` here is `beta`, `budget`, `cli`,
`events`, `projection` — there is no dispatch path. [measured] `dispatch.py` lives in
`consilient-clone-checks`. More than that: `tests/test_v0_invariants.py::test_the_cli_exposes_no_routing_or_blocking_surface`
asserts the command set is exactly `{record, replay, beta, doctor}` and that no argument
destination anywhere contains `route`, `dispatch`, `admit`, `invoke` or `gate`. [measured] This
increment is observe-only by invariant. Adding a router here would turn a passing test red and
would be the right test to keep. ADR-0054 reached the same boundary and said so: *"This ADR
describes the interface only."*

Everything else in the brief holds, and its central instinct — that an untouched paid pool beside
a 58%-consumed one is a scheduling failure — is correct and is already this project's recorded
position under ADR-0028.

---

## Context

At 02:17 on 21 August 2026 the Cursor Ultra dashboard showed three allowances on one flat-fee
subscription: **Cursor Models 1%**, **Other Models 58%**, **Grok Bot 0% (weekly)**, with
**On-Demand Spending Disabled**. [cited — the principal's own screenshot] Two of the three are
essentially untouched with thirty days to reset, and unused allowance does not roll over. [cited]

ADR-0044 already settles the direction: *subscription-first — anything reachable through a
flat-fee subscription the principal already holds is reached that way; metered calls are the
exception.* ADR-0028 already settles the urgency: included capacity expires at reset boundaries,
so idling it is a loss. **Nothing in this repository restricts routing to a particular vendor's
models.** So consuming Cursor Models is not a deviation from policy; it is the policy, unexecuted.

Two things stop it being a small fix.

**The first is that nobody has ever recorded which pool a run consumed.** `dispatch.py:1467`
hardcodes `model="unknown:not-reported-by-runtime"` into every `Outcome`, for every runtime, while
`adapter_cursor.py:95-108` already carries a `model_fields()` that separates *requested* from
*selected*; and the production shell route used `--output-format text`, which discards the JSON
envelope containing `request_id` and token counts before anything could read it. [measured] A
58%/1% split therefore ran for a month and became visible on a dashboard rather than in a
trajectory.

**The second is that quota is not budget, and this repository already has a budget layer that
must not be widened to pretend otherwise.** `src/consilient/budget.py` enforces weekly and monthly
ceilings, fails closed on absent, stale or malformed state, and refuses any request whose currency
is not `METERED_CURRENCY` against `METERED_PROVIDER = "openrouter"`. [measured] It is a
money-refusal module. A quota pool is not money — it is a percentage of an allowance already
paid for, where consuming it is free at the margin and *not* consuming it is the loss. Generalising
`check_budget` to carry both is how a money guard stops being one.

And underneath both: **On-Demand Spending is the single path by which this system could spend
Joe's money.** It is currently Disabled. Every other failure mode in this ADR costs an idle pool.
That one costs cash.

---

## Decision

**D1 — A quota pool is a first-class scheduling constraint, not an afterthought.** Every dispatch
names a triple — `(runtime, model_id, pool)` — and records all three in the trajectory alongside
the runtime's own reported model. `model="unknown:not-reported-by-runtime"` is a defect to be
fixed, never a default to be accepted, and a route emitting an output format that destroys the
served-model identity is misconfigured.

**D2 — No dispatch may omit an explicit model id.** The account default is shared mutable state
that concurrent agents rewrite on every invocation, and it was observed taking three distinct
values in 3 min 30 s. [measured] A route that inherits it has no pool to attribute and no
composition to compare under ADR-0027. `--model auto` is permitted but is not a pin: its
resolution is a server-side decision and may not be recorded as a requested model.

**D3 — A pool near exhaustion sheds work to an idle pool, and never to spend.** The order is:
(a) filter to compositions ADR-0054 admits as capable for the task family; (b) among those,
prefer the pool with the most headroom relative to time remaining before its reset; (c) if every
admissible prepaid pool is exhausted, **stop and ask the principal.** There is no fallback to a
metered vendor and no fallback to on-demand. Capability filters first; quota only ever breaks
ties among compositions already admitted, because an idle pool is not a reason to send work to a
composition that cannot do it.

**D4 — A pool whose attribution is not `[measured]` may not be a shed *target*.** Work may still
be routed to such a pool by ordinary capability routing; it simply may not be *chosen because of*
its headroom. Attribution is a field on the allowance record, not a comment. **Today this makes
D3 inert for every Cursor pool,** and that is the intended, honest behaviour of a rule whose
input has not been measured.

**D5 — On-Demand Spending stays Disabled, and only the principal may change that.** No code path,
script, agent instruction or configuration file in this repository may enable on-demand spending,
raise a spend cap, or call a spend-escalation endpoint. This is enforced by lint, not by
convention — see *Enforcement*.

**What ships now:** D1, D2 and D5, with D5's check in this commit. **What is withheld:** the
scheduler D3 describes, because D4 refuses to let it act on `[asserted]` attribution.

---

## Evidence

- `[measured]` **Five routes run and resolve a model with server-side attestation.** The CLI's own
  session store binds `"providerOptions":{"cursor":{"modelName":"…"}}` to the probe's unique token
  inside one record, for `composer-2.5`, `cursor-grok-4.6-medium`, `cursor-grok-4.6-medium-fast`
  (via the `grok-4.6[effort=medium,fast=true]` alias) and `cursor-grok-4.5-high-fast` (via
  `--model auto`, 8/8 runs). Artefacts are files with content, not exit codes: a 21-byte
  `stdout.txt` containing exactly `CURSOR_POOL_PROBE_OK`, 0-byte stderr, and a JSON envelope
  carrying `request_id` and token counts. Full table in
  [`../20-design/quota-pools-and-routes-2026-08-21.md`](../20-design/quota-pools-and-routes-2026-08-21.md).
- `[measured]` **`--model` is validated server-side, so there is no silent fallback.** A
  deliberately bogus id returns `Cannot use this model`, exit 1 in 3 s, with no session directory
  created and zero tokens consumed. This is the check that turns "I passed a flag" into "the flag
  was honoured", and it cost no quota.
- `[measured]` **The no-flag default drifts.** `selectedModel.modelId` read four times from one
  machine inside 3 min 30 s: `grok-4.6` → `grok-4.6` → `composer-2.5` → `default`, none set by
  the observing agent, because `~/.cursor/cli-config.json` is rewritten on every invocation and
  is shared. This is the whole of D2.
- `[measured]` **A per-request, per-model, per-cost oracle exists and was wrongly reported
  absent.** `aiserver.v1.DashboardService` at `https://api2.cursor.sh` exposes
  `GetFilteredUsageEvents` / `GetAggregatedUsageEvents`; `UsageEventDetails` carries field 17
  `routed_model` and field 18 `requested_model_selection`; `UsageEventKind` distinguishes
  `INCLUDED_IN_ULTRA` from `USAGE_BASED` from `ABORTED_NOT_CHARGED`. The `usage` command is
  registered in the bundle and hidden by a client-side literal (`enableUsageCommand` true for
  `remote`, false for `local-authenticated`). Five of six probe reports concluded no counter
  existed because they grepped `--help`, where a slash command never appears. **This is what makes
  EXP-94 a one-hour experiment rather than a standing unknown.**
- `[measured]` **The 58%/1% split is corroborated by a different class of fact than the
  dashboard.** 448 distinct CLI `requestId`s in the local tracking DB, none grok, none composer;
  76 of 76 Cursor model attributions across 78 trajectory logs are `gemini-3.7-flash-high`.
- `[cited]` **The three pools are genuinely distinct buckets.** Cursor Models and Other Models
  reset monthly with the billing cycle and do not roll over; Grok Bot access *"includes usage that
  resets weekly"* and is billed per-product. (cursor.com/help/models-and-usage/usage-limits;
  cursor.com/help/grok-bot/plans)
- `[cited]` **Grok Bot has no headless entry point.** Neither cursor.com/help/grok-bot/* nor
  docs.x.ai/grok-bot/* documents a CLI, API endpoint, webhook or headless invocation; it is a
  desktop/iOS application signed in with the Cursor account. Corroborated `[measured]` by the
  absence of any `bot` subcommand in `cursor-agent --help` and by the app not being installed.
- `[cited]` **Cursor's own docs classify pools by model, not by surface.** cursor.com/docs/models
  places Cursor Grok 4.6, Grok 4.5 and Composer 2.5 in Cursor Models and third-party models in
  Other Models, and nothing in the CLI, pricing or models documentation says the CLI, IDE and
  cloud surfaces differ. **This is the hypothesis EXP-94 tests. It is not a result, and this ADR
  does not treat it as one.**
- `[asserted]` Every pool cell for every Cursor route is `unknown`. Naming evidence — model id,
  server-injected system prompt identity, `api2.cursor.sh` endpoint — is *consistent with* Cursor
  Models and excludes nothing.

---

## Evidence against

**The strongest objection is to D4, and it is Joe's own instruction.** D4 makes the scheduler
inert on the only machine that motivated it. Joe asked tonight for better utilisation of pools
that are sitting at 1% and 0%; D4 delivers **zero utilisation change** until an experiment runs
that needs his authorisation. A weaker rule — shed on `[cited]` vendor grouping, since
cursor.com/docs/models states plainly which models sit in which pool — would deliver value
immediately and is *probably right*. I decided against it because the cost of being wrong is
asymmetric: a wrong shed sends work **into** the pool we believed was idle, and if the belief is
inverted it drains the pool we were protecting, invisibly, with no counter to catch it. That is
the 19 August failure re-run at larger scale. **If Joe overrides this, the honest override is to
set D4 aside explicitly and record the routing as running on `[cited]` attribution — not to
upgrade a tag.**

**My own evidence is contaminated, and I cannot fix it after the fact.** Between 02:58 and 03:05
local, 12–20 sibling `cursor-agent` sessions were written under the *same* workspace-hash
directory, because the chat store is keyed by workspace path and every concurrent agent used the
same scratchpad. At least three different models carried the same `CURSOR_POOL_PROBE` marker
inside a 44-second window, and one sibling session landed 5 s after a probe exited and could not
be attributed even by its own author. [measured] The brief instructed *"quiesce all other
cursor-agent activity first"*; that was not achievable, and the dashboard-delta method was
unavailable by construction for this entire batch. **Any pool attribution any sibling agent
reports as confirmed from a dashboard delta tonight should be rejected on these grounds.**

**The proposed instrument could not have worked even uncontaminated.** The dashboard reports
integer percent over a 30-day window and reads 1% for Cursor Models; a probe consuming ~21k input
tokens cannot move it by a resolvable amount. [measured] So a negative dashboard delta would have
been uninformative and a positive one would have been someone else's traffic.

**One baseline in the batch was a check that could not fail.** `ls -1 ~/.cursor/chats | wc -l`
counts workspace-hash directories at depth 1, while probe sessions are created at depth 2 under
an already-existing hash — so `458 → 458` was structurally incapable of moving. [measured] Same
failure class as the CI replay step repaired on 20 August, which had been comparing two rebuilds
from the same log and recorded as satisfying Gate A on a check that could not fail. It is the
project's characteristic error and it recurred tonight.

**Correlated reviewer error is not excluded.** Six agents refused to upgrade `unknown` to
`cursor-models`, which reads as strong independent agreement. It is weaker than it looks: they
share a brief, a machine, a prompt template and one salient cautionary tale (SuperGrok, 19 Aug).
A shared prior that produces six identical refusals is one observation, not six.

**The RPC oracle has never been called.** Every `DashboardService` claim above is read off literal
protobuf descriptors in the installed JS bundle, not off a live response. The bearer scope may be
`AiService`-only; a CLI-originated request may produce no usage event at all; and the three
dashboard pools **do not exist as counters anywhere in the bundle** — they are a
presentation-layer grouping the web dashboard computes over per-model events. So even a successful
EXP-94 delivers *per-request model and billing kind*, and the last hop from models to pool
percentages remains a grouping rule **we** infer. **One human dashboard read is still required to
bind it, once.** Anyone reading D3 as fully automatable is reading it too generously.

**Two claims about Grok Bot rest on documentation nobody tested.** Nobody installed the app,
signed in, or watched the weekly number move; the docs nowhere state the *size* of the Ultra
weekly allowance, so "0% of an unknown quantity" is the whole of what can be said; and
`docs.x.ai/llms.txt` returns 404, so the doc tree could not be enumerated and a page describing a
headless route may exist unseen. "Unreachable" is `[cited]`, not `[measured]`.

**Refusing to widen `budget.py` is a judgement, and the opposite case is real.** A reviewer could
reasonably say `Ceiling(period, amount, currency)` generalises to `Ceiling(period, amount, unit)`
in about four lines, and that two near-identical ledgers is the duplication this project usually
refuses. I decided the other way because the currency-typed refusal is the load-bearing part of a
module whose entire purpose is refusing to spend money, and because the two have opposite
objectives: budget minimises consumption, quota maximises it before reset. If the sibling ledger
lands and looks like a copy of `budget.py` with one field renamed, this paragraph is the record
that the objection was seen and overruled, and the merge is then the cheaper answer.

**And the plain possibility that the `[cited]` mapping is simply correct.** If Cursor bills by
model regardless of surface — which is what its documentation says and what nothing contradicts —
then D4 costs a month of an idle pool to avoid an error that was never going to happen. EXP-94
exists to close that in an hour rather than to keep the question open.

---

## Consequences

**Positive.** The pool a run consumed becomes a recorded fact rather than a dashboard
observation, which is the whole reason a 58%/1% split survived a month. D2 also repairs an
ADR-0027 comparability defect that has nothing to do with quota: every Cursor result recorded so
far was produced under Gemini, results from tonight onward are produced under Cursor Grok, and
nothing in the harness distinguishes them. D5 puts a lint rule between an autonomous system and
the one control that spends real money — before the experiment that requires touching the service
those controls live on, not after it.

**Negative.** No utilisation improves tonight. The 1% and 0% pools stay at 1% and 0% until EXP-94
runs, and EXP-94 needs Joe's authorisation because it handles a live bearer token. D2 makes every
Cursor dispatch site carry a model id, which means the model becomes a composition axis that must
be chosen, recorded and defended per ADR-0027 — real work at every call site, and previously
recorded Cursor results may not be pooled across the default's flip. D5's lint carries a
maintenance cost and a real false-positive risk: a future agent legitimately writing a *read-only*
usage query against `DashboardService` will trip it if it names a neighbouring method, and will
have to add an allowlist entry under review. That friction is the point.

**Neutral but load-bearing.** Grok Bot is now a recorded dead end rather than an open task, with
the Grok Build CLI confusion documented beside it — the pool is 0% and will stay 0%, and that is
the answer, not a backlog item. The pool ledger is committed to being a *sibling* of `budget.py`,
not an extension of it, which constrains the concurrent agent's data layer. And ADR-0054 now owns
capability admission while this ADR owns pool selection, in that order; a future ADR wanting
quota to override capability must supersede this one rather than amend it.

---

## Enforcement

Invariant **V0-39** — *No code path in this repository may escalate spend.*

Numbered from the free block ADR-0054 declared (`V0-30 … V0-39`), taking the **top** of the range
rather than the bottom, because ten concurrent worktrees sitting on the same maximum will all
reach for the lowest free number at once — the collision recorded in R15, where five agents
registered the same experiment number.

- **Check:** `.github/scripts/check_no_spend_escalation.py --check` — scans every tracked file for
  spend-escalation identifiers (`SetHardLimit`, `SetUsageBasedPremiumRequests`, their snake_case
  forms, and on-demand-spending enablers) and fails on any occurrence outside a short, explicit
  allowlist of documentation paths declared inside the script. The two RPC method names are not
  guesses: they were `[measured]` in the installed CLI bundle, on the *same* `DashboardService`
  that EXP-94 must call read-only.
- **The bypass ban is the allowlist itself.** A banned identifier is only permitted where the
  script says so by path, so introducing a new occurrence requires editing the allowlist in the
  same diff — which is the reviewable event. Without that, this ADR and its companion design note
  could not name the methods at all, and a check that cannot describe what it bans decays into
  one nobody can audit.
- **Fails CI:** yes. Wired as a step in `.github/workflows/invariants.yml`, alongside the existing
  rename-safety check.
- **Added in the same commit as the implementation:** yes (I1). Tests in
  `tests/test_v0_invariants.py` under the `V0-39` heading: a clean tree passes; a planted
  escalation call in a non-allowlisted file fails and names the file; an allowlisted documentation
  path passes; and a meta-test asserts the workflow actually runs the check, so the invariant
  cannot be silently unwired from CI.

**What is deliberately *not* enforced yet.** D3 and D4 declare a boundary that has no code behind
it, and a lint rule guarding a router that does not exist would be a check that cannot fail —
this project's characteristic error, committed twice already (the CI replay step, and one of
tonight's own baselines). **D3/D4's check ships in the same commit as the scheduler**, not before
it, and takes the form ADR-0054's Check 2 already specifies: the single recorded route decision
gains a `pool` field, and replay asserts that every route decision citing a pool as its *reason*
resolves to an allowance record whose `attribution` is `measured`.

---

## What would overturn this

**EXP-94 — which pool does a `cursor-agent` invocation actually debit?**

| | |
|---|---|
| **Design** | Serialise: no other `cursor-agent` activity on the account for the window — the condition that was impossible tonight and is the experiment's main scheduling cost. One probe per model family, each carrying a unique token, each capturing its own `request_id` from `--output-format json`. Then read `GetFilteredUsageEvents` from `aiserver.v1.DashboardService` and match on `request_id`, reading `routed_model` and `UsageEventKind`. **One row, one route, no contamination** — a per-request lookup rather than a difference of three aggregate percentages. |
| **Authorisation** | Required from Joe. It reads a live bearer token (`/home/jpbpr/.config/cursor/auth.json`, mode 600, not read, never to be echoed or written to an artefact). Read-only, no metered vendor, consumes no quota beyond the probes themselves. **It must not call `SetHardLimit` or `SetUsageBasedPremiumRequests`, which sit on the same service** — V0-39 exists to make that a build failure rather than a promise. |
| **Stopping rule** | n=1 per family. The observable is a returned row naming the model; a lookup has no sampling error. |
| **What it kills** | If the ledger returns rows for CLI-originated requests, every model appearing in one upgrades from `[asserted]` to `[measured]` and **D3/D4 become live**. If `DashboardService` refuses the CLI's bearer scope, the automated route is dead and the fallback is one serialised probe plus a single human dashboard read — roughly two minutes of Joe's attention. If CLI requests produce no usage event at all, the pools are unattributable from this machine and D4 makes the scheduler permanently inert for Cursor, which would itself be a publishable finding about subscription meta-harnessing. |
| **Blocks?** | **No.** Per ADR-0049 and ADR-0050: its largest possible effect is to *activate* a rule already written, or to prove the input unobtainable. It cannot show that pools should not be a scheduling constraint. D1, D2 and D5 ship regardless, and D5's check ships tonight. |

**Two things would overturn this without any experiment.** If Cursor exposes a supported
per-pool usage endpoint, D4's attribution field becomes trivially satisfiable and the interesting
part of this ADR evaporates. And if the principal enables On-Demand Spending — which is his to
enable and nobody else's — D3's terminal clause changes from *stop and ask* to a question about
spend policy, and this ADR must be superseded rather than amended, because D5 is the sentence in
it doing the most work.

---

## Publication candidate?

**Not as a paper.** Quota-aware scheduling across prepaid pools is operations, and the mechanism
is one vendor's dashboard grouping.

**Lane A research note, conditional on EXP-94 running, and the interesting result is the negative
one.** The reportable finding is not "Cursor bills by model" — the vendor's documentation says so.
It is the **measurement gap**: a paid subscription exposes three allowance pools to a human eye
and *zero* of them to a program, the CLI ships a working quota client and disables it with a
client-side literal for exactly the locally-authenticated case a meta-harness runs in, and six
independent agents probing a live account produced server-attested model identity and no pool
attribution whatsoever. **A meta-harness that cannot read its own remaining allowance cannot
schedule against it** — which is the same wall ADR-0026 hit on 20 August and idled a paid
subscription overnight for. That is a general obstacle to subscription-first orchestration, it is
measurable, and nobody reports it.

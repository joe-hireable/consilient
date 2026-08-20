# PM-tool purpose assignment — EXP-16

Written **before** running the arms, as EXP-16 requires. Each tool gets a hypothesis about
what it is best at, grounded in its actual affordances, and each hypothesis is falsifiable
by what the experiment measures. Deviations get recorded in **Surprises**, filled in after.

Status of all hypotheses: `[asserted]` until EXP-16 reports.

---

## Linear — hypothesis: best home for the decision/ticket state machine

Opinionated, fast, minimal state machine (Backlog → Todo → In Progress → Done, light
customisation), first-class API and webhooks, low ceremony per state transition.

**Hypothesis.** The decision lifecycle from ADR-0020 (`called → evidence gathered →
decided`) maps onto Linear's workflow states with the least distortion, and its transition
latency is the lowest of the three.

**Falsified if:** the state model cannot represent "parked awaiting user evidence" without
abusing a status; or transition latency/rate limits are materially worse than ClickUp's.

**Blocker recorded at setup (2026-08-19):** the Linear MCP connector requires an
interactive OAuth flow the agent cannot complete alone (`/mcp` → authenticate in browser).
Until the user authorises, the state-machine leg runs in ClickUp and the Linear comparison
is deferred. This is itself an EXP-16 finding: *an integration whose auth model assumes a
human at a browser is a friction class the native design must not inherit.* `[measured]`

**Run later the same day, after Joe authorised:** hypothesis **falsified in the same
direction as ClickUp's, with an aggravating twist** — no `decided` state, no
"parked" state, no status creation over MCP, and an invalid state request is **silently
coerced rather than rejected** (ClickUp at least errors loudly). Latency marginally
better than ClickUp (9.1–11.2 s vs 14.3–18.1 s bracketed); concurrency clean on both.
Full detail: `../10-research/exp16-results.md` § "The Linear leg". `[measured]`

## ClickUp — hypothesis: best home for the authority matrix as structured data

Rich custom fields, deep hierarchy (Space → Folder → List → Task → Subtask), native docs,
comments with threading, many views.

**Hypothesis.** The Owner/Contributor/Evidence/Informed/Escalation matrix (ADR-0020) fits
ClickUp's structured-data affordances better than Linear's minimalism or Slack's stream —
one task per decision, roles as fields, matrix queryable.

**Falsified if:** the matrix ends up living in free-text markdown anyway (structure
theatre), or hierarchy/custom-field overhead costs more than it organises.

**Workaround recorded at setup (2026-08-19):** the MCP surface exposes *reading* custom
fields but not *creating* custom field definitions. Roles therefore live as structured
markdown in task descriptions — the "rich custom fields" affordance is partially
inaccessible to an agent, which already dents the hypothesis. `[measured]`

## Slack — hypothesis: best for meetings and user participation, and most likely to echo

Real-time, threaded, conversational, the one surface where the user is reliably present.

**Hypothesis (double-edged, deliberately).** (a) For meetings that need the *user* as an
evidence class (preferential questions, ADR-0018 case 1/3), Slack minimises the user's
cost of participation — better than any ticket tool. (b) For agent↔agent exchange, a
free-form channel is exactly the relay structure arXiv:2603.26993 punishes: prose relay
lost ~8.5 pts/stage vs ~2.8 structured in the paper's (separate) comparison. Arm C exists
to measure (b) directly: expect echo — restatement of shared context rather than
introduction of new evidence.

**Falsified if:** (a) the user finds ticket-comment participation no more costly than
Slack; or (b) Arm C's free-form discussion matches Arm B's decision quality at matched
budget — which would be evidence *against* ADR-0020's structural claims, and must be
reported as such.

---

## Isolation (created 2026-08-19)

| Tool | Space | ID / URL |
|---|---|---|
| Slack | `#consilience-exp16` (public channel) | `C0BRCQY2MED` |
| ClickUp | Folder `consilience-exp16` in the Innovation space | folder `901213139850`; lists: Decisions `901220499980`, Authority Matrix `901220499983` |
| Linear | *pending user OAuth* | — |

Nothing outside these spaces is touched.

## Surprises

*To be filled during/after the arms. A hypothesis that survives unmodified is also worth
recording — that is a calibration datum, not a null.*

- (setup) ClickUp custom-field creation not exposed over MCP → matrix-as-fields degraded
  to matrix-as-markdown on day one. `[measured]`
- (setup) Linear auth model blocks headless setup entirely. `[measured]`
- (setup) Parallel agents cannot safely append to one JSONL trajectory file; events are
  returned to a single writer and serialised — ADR-0006's "SQLite for concurrent
  coordination, single-writer log for the record" reproduced itself in miniature before
  the experiment even ran. `[measured]`
- (run) The rate-limit half of the external-tool case **did not materialise** — note that this
  half was never ADR-0006's, the attribution having been corrected on 20 August 2026 to
  `../30-source-material/gemini-session-critique.md`: 24 concurrent
  ClickUp writers, ~470 API calls across the run, zero rate-limit responses, zero write
  conflicts. The state-machine half over-delivered: 6/6 Owners hit `Status does not
  exist`. `[measured]`
- (run) The biggest surprise was not on the hypothesis list at all: **single-identity
  attribution corrupted provenance**. With every write posting as "Joe", an agent
  misattributed another agent's proposal to the human, and the scribe recorded human
  participation in a thread no human joined. The failure class rented tools cannot fix:
  who-said-what. `[measured]`
- (run) Slack's echo risk manifested as *dissent-smoothing*, not restatement: all six
  free-form threads closed in reported unanimity while all six structured meetings
  preserved explicit dissent. `[measured]`

Full numbers and stopping-rule verdicts: `../10-research/exp16-results.md`.

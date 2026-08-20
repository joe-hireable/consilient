# EXP-16 results — the meeting layer prototyped on rented PM tools

Run 19 Aug 2026, single session. Register entry: `experiment-register.md` § EXP-16.
Trajectory: `.harness/log/2026-08-19.jsonl` (append-only, replayable, single writer).
Purpose assignment written before the run: `../20-design/pm-integration-purposes.md`.

**No ADR has been changed on the basis of this file.** Stopping-rule verdicts are stated
below; supersessions await Joe's response, per the experiment's own rules.

## What ran

Six genuinely open decisions (D1 plugin-vs-standalone, D2 v0 success condition, D3
Inquiry tier, D4 v0 scope, D5 model library, D6 executable-model ratchet), identical
briefs across three arms:

- **Arm A** — one agent per decision, all four evidence classes, no communication layer.
- **Arm B** — ADR-0020 structure: four Evidence agents with declared distinct classes
  (E1 simulation, E2 verified literature, E3 landscape, E4 constraints) posting
  structured comments on a ClickUp ticket; an Owner holding no pack reads and decides
  alone. Joe holds an Evidence seat on D4 (parked awaiting his reply, per ADR-0020 §3).
- **Arm C** — same agents, same evidence partition, free-form Slack threads, no chair,
  decision "by whatever emerges", recorded by a no-judgement scribe.

**Deviations from the spec, honestly:** (1) the Linear leg never ran — the MCP connector
requires interactive browser OAuth; the state-machine hypothesis is untested against
ClickUp's. (2) The optional structured-relay Slack fourth condition was not run (cheap to
add later by resuming the workflow). (3) Token budgets were **not** matched across arms;
coordination overhead is reported as a result instead — matching would have required
padding Arm A or starving B/C, both of which distort quality. (4) Joe had not replied to
either participation point at time of writing; both remain parked, which is itself the
ADR-0020 §3 async mechanism working as designed. (5) All 96 agents are the same model
family — see Limitations.

## The numbers `[measured]`

| | Arm A | Arm B | Arm C |
|---|---|---|---|
| agents | 6 | 30 | 60 |
| subagent tokens | 362,257 (1.0×) | 1,748,053 (**4.8×**) | 3,523,966 (**9.7×**) |
| wall-clock | 46 s | 169 s | 398 s |
| tool calls | 33 | 235 | 423 |
| messages produced | 6 decisions | 24 evidence comments + 6 owner decisions | 43 posted turns (11 of 24 round-2 turns voluntarily passed) + 6 scribes |
| new-evidence fraction (per-decision context) | n/a | **0.60** | **0.48** |
| API errors / write conflicts / rate limits | n/a | **0 / 0 / 0** (24 concurrent comment writes) | 0 / 0 / 0 |
| bracketed API latency (upper bound; includes agent-turn overhead) | n/a | comment post: 14.3–18.1 s (med 15.7); owner read 7.5–9.9 s; owner close 20.8–24.1 s | Slack post: 8.8–23.0 s (med 14.5) |

**Correction, 2026-08-20.** This file previously compared the 4.8× / 9.7× multiples above
to Kim et al.'s 1.6–6.2× range. That comparison was incommensurable and has been withdrawn:
the full text, read on 20 August 2026, reports 1.6–6.2× **realised reasoning turns**, whereas
the figures above are **subagent tokens**. [measured] No token-overhead range from that paper
is available to compare against, and this experiment did not record reasoning turns, so the
arms stand on their own measured token multiples with no external referent. [measured]

## Decisions across arms

| | A (single) | B (Owner meeting) | C (free-form) |
|---|---|---|---|
| D1 | standalone | standalone, EXP-05-gated | **plugin-first — flip** |
| D2 | β-meter, one artifact | β-meter, Joe-first | β-meter, Joe-first, +audit riders |
| D3 | defer Inquiry | defer | defer, 4–0 |
| D4 | β-meter + budgets, **cut cascade** | β-meter + 2-tier cascade (PROVISIONAL, parked on Joe) | β-meter + cascade + budgets |
| D5 | out (endpoint config) | out | out |
| D6 | keep minimal ratchet | **drop from v0 — flip** | adopt |

Three-way substantive agreement on D2/D3/D5. Format-dependent flips on D1 (C vs A+B) and
D6 (B vs A+C); three-way scatter on D4. **Decision quality is Joe's to grade** — the
experiment's design names his judgement as ground truth for these preferential-adjacent
questions; the structural observations below are what can be said without him.

## Structural findings `[measured]`

1. **Dissent survives structure and dies in discussion.** All six Arm B owner decisions
   carry an explicit, often self-critical DISSENT section (D4's owner concedes it
   weighted an anecdotal friction log over ecosystem-scale incident data). All six Arm C
   threads closed in reported *full convergence with zero standing dissent* — caveats
   were absorbed as "conditions" rather than held open. On the repo's own principle
   ("honest disagreement is information"), the free-form format destroyed information
   the structured format preserved.
2. **Provenance corrupted within two hops on identity-free infrastructure.** Every write
   in both tools lands under one OAuth identity ("Joe"). In D3's thread, agent E2's
   second turn misattributed agent E1's proposal to *"Joe's quantitative revisit
   criterion"*, and the scribe then recorded "Joe contributed directly (reply 5)" —
   **a false human-participation claim now sitting in a meeting record no human joined.**
   The fabrication audit traced it: born in prose relay, laundered by summarisation.
   This is Whewell clause 1 (provenance) failing exactly as CONSILIENCE.md predicts, and
   it makes ADR-0020's "outcome writes attributed to the Owner only" check unenforceable
   on rented tooling.
3. **Echo was structural, not informational — by design, and that limits the test.**
   Both arms held partitioned evidence, so most messages carried genuinely new facts
   (B 0.60, C 0.48 per-decision). The MIT theorem's punished regime — agents reprocessing
   *shared* context — was never instantiated. What C showed instead: round-2 new-evidence
   density halves (r1 65–85% → r2 30–65%), 11/24 round-2 turns passed voluntarily, and
   under a whole-arm reading the cross-decision recycling puts C's yield nearer 0.25–0.30.
   One genuine mind-change occurred (D4: E4 conceded to E3's staleness facts) — evidence
   moving a vote, which is what a meeting is for.
4. **The relay-degradation prediction did not visibly bite at depth 2.** Two free-form
   rounds over partitioned evidence produced coherent, evidence-dense discussions — no
   measurable quality collapse vs Arm B. The 8.5-pts/stage prose penalty is a 3+-stage
   relay phenomenon; nothing here contradicts the paper, but nothing here needed the
   theorem either. Deeper chains or shared-context arms would be the real test.

## Tooling findings, against the pre-registered hypotheses

| Hypothesis | Verdict |
|---|---|
| ClickUp best for the authority matrix as structured data | **Dented at setup, failed in use.** Custom-field *creation* is not exposed over MCP → matrix lived as markdown. Structure theatre, as pre-registered under "falsified if". `[measured]` |
| Slack best for user participation; most likely to echo | **Half-confirmed, half-untested.** The D4 summons to Joe worked exactly as ADR-0020 §3 prescribes (parked, async, cost-of-deciding-without-you stated). Echo as *restatement* did not dominate (0.48) because evidence was partitioned; echo as *dissent-smoothing and provenance loss* showed up instead — a more precise failure mode than the hypothesis named. |
| Linear best for the decision state machine | **Untested** — interactive OAuth blocked the arm entirely, which is itself a finding about rented infrastructure. |
| ADR-0006: external tools impose human-shaped state machines | **Confirmed, specifically.** 6/6 Owners hit `Status does not exist` setting `decided`; no status discovery except by failing; fell back to `complete`. `[measured]` |
| ADR-0006: human-shaped rate limits / webhook round-trips bite | **Not confirmed at this scale.** 24 concurrent writers, ~470 API calls, zero rate-limit responses, zero conflicts. Latency upper bounds (8.8–24 s bracketed, dominated by agent-turn overhead, true API latency unresolved) were an annoyance, not a blocker. |

## Stopping rules, applied as written

1. *"If Arm B does not beat Arm A at matched budget → meetings are ceremony; cut
   ADR-0020 and the matrix."* — **On the structural evidence, Arm B did not beat Arm A.**
   Same substantive decisions in 4/6 cases at 4.8× token cost and 3.7× wall-clock. What B
   uniquely produced: preserved dissent, enforced provenance-by-format, and the parked
   preferential question to Joe — none of which is decision *quality* on the metric the
   rule names. **If Joe's grading confirms quality parity, this rule fires and ADR-0020's
   meeting layer should be cut or radically shrunk** (the Owner/Escalation matrix may
   survive as schema without the convened-meeting machinery). Not softened: the rule as
   written is currently pointing at "ceremony".
2. *"If Arm C beats Arm B → the delegation theorem does not apply as claimed."* — C did
   not beat B cleanly (false unanimity, provenance corruption, 2× B's cost), but it did
   not lose cleanly either (richer riders on D2/D4; one genuine evidence-driven vote
   change). **The honest verdict is that this experiment cannot decide the rule**: with
   partitioned evidence, Arm C was never the structure the theorem punishes. A follow-up
   with shared-context participants and 3+ relay stages would be.
3. *"If Linear/ClickUp handle state machine + concurrency without material friction →
   supersede ADR-0006."* — **Does not fire.** Concurrency was clean, but the state
   machine, identity model, and field schema all failed in ways that matter (6/6 status
   rejections; single-identity attribution breaking two ADR-0020 enforcement checks;
   RACI-as-markdown).
4. *"If rate limits or human-shaped state bite → ADR-0006 validated; record numbers."* —
   **Fires, with a correction.** ADR-0006's *conclusion* stands but its *grounds* shift:
   the binding external-tool failures are **identity/attribution and schema rigidity**,
   not rate limits or round-trip latency, neither of which bit at 24-writer concurrency.
   The native design inherits: a first-class `actor` field per event (the misattribution
   finding makes this non-negotiable), harness-owned status vocabulary, typed role
   fields, and tool-call telemetry (self-timed latency, not bracketed).

## The Linear leg (run 19 Aug 2026, after Joe's OAuth — completing the deferred arm)

Project `consilience-exp16` in the Hireable team
(linear.app/hireable/project/consilience-exp16-a8e8bed56d49), issues HIR-47…52
mirroring the six ClickUp decision tickets. Findings, against the pre-registered
hypothesis ("Linear is the best home for the decision state machine"):

1. **The state-machine hypothesis fails the same way ClickUp's did, plus a worse
   failure mode.** Native vocabulary: Backlog / Todo / In Progress / In Review / Done /
   Canceled / Duplicate — no `decided`, nothing between In Review and Done for "parked
   awaiting user evidence", and the MCP surface exposes **no status creation** (labels
   only). Worse: requesting the nonexistent state `decided` produced **no error — the
   issue silently stayed `Done`.** ClickUp rejects loudly; Linear's MCP layer coerces
   silently, so an agent believes it set a state the record does not hold. A silent
   state divergence is strictly worse for a trajectory log than a loud failure.
   `[measured]`
2. **Workaround demonstrated:** label `parked-awaiting-user` carries the semantics the
   state machine cannot (HIR-50). Semantics-in-labels is structure theatre of the same
   kind as ClickUp's RACI-in-markdown. `[measured]`
3. **Concurrency clean, again:** 4 concurrent comment writers on HIR-50, zero
   conflicts, zero rate limits, bracketed latency 9.1–11.2 s (vs ClickUp 14.3–18.1 s;
   both upper bounds including agent-turn overhead). The rate-limit half of ADR-0006's
   case fails to bite on Linear too. `[measured]`
4. **Single-identity attribution replicates:** every issue and comment shows
   `createdBy: Joe Brown`. The provenance failure class is tool-independent.
   `[measured]`

**Verdict on the tooling stopping rules: unchanged by the Linear leg, now with both
tools measured.** The binding external-tool failures are schema rigidity and identity,
not rate limits — and Linear adds silent-coercion to the schema-rigidity column.
ADR-0006's native-store conclusion stands with corrected grounds.

**D4 closure for the record:** Joe's preferential evidence arrived (15–30 hrs/week;
full-list appetite); the Owner's final decision — full candidate list, sequenced
β-meter-first with measurement gates — is on ClickUp ticket 869em65r1 and mirrored on
HIR-50. The ADR-0020 §3 park/resume lifecycle completed end-to-end. `[measured]`

## Limitations

- All 96 agents share one model family. Cross-arm agreement (D2/D3/D5) may be shared
  prior, not robustness — the same Q19 caveat that hangs over the whole repo. A
  cross-model replication is the obvious next step.
- n=6 decisions, one replication, no statistical power. This is EXP-14's protocol
  pilot-tested on rented infrastructure, not EXP-14.
- The echo metric resets context per decision; the cross-decision recycling caveat means
  the B/C fractions are upper bounds on information yield.
- Latency figures are bracketed wall-clock including agent overhead — upper bounds only.
- The echo classifier is the same model family as the participants.
- Decision-quality ground truth (Joe's grading) outstanding at time of writing.

## Recommended follow-ups (not registered — Joe's call)

1. Joe grades the 18 decisions blind (arm labels stripped) → resolves stopping rules 1–2.
2. A shared-context Arm C′ (all four packs to all participants) at 3+ relay stages — the
  actual theorem regime — before any ADR-0020 supersession is written.
3. If ADR-0006 is reaffirmed, rewrite its Evidence section via supersession to cite the
  measured grounds (identity, schema) and drop the unconfirmed ones (rate limits).
4. Structured-relay Slack fourth condition (the paper's Bpost analogue) — one workflow
  resume away.

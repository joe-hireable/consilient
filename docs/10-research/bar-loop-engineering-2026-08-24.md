# Bar: `cobusgreyling/loop-engineering` as the orchestration-layer incumbent

**Frozen:** 2026-08-24. Re-check the GitHub API fields below before claiming this bar is
still current. An incumbent moves; a bar beaten in August and never re-measured is a bar
you have stopped clearing.

**Status of this artefact:** `[measured]` for GitHub/npm numbers fetched on this date;
`[cited]` for what was read in the published repository and docs; `[asserted]` for the
recommendation and the mapping judgements.

**Correction to the brief and to `.harness/plan-units.json`.** Unit AW is *not* a section
of `docs/10-research/literature-review.md`. That file does not mention this repository.
The unit lives in `.harness/plan-units.json` under `"AW"`. The plan pointer is wrong.
`docs/10-research/loop-engineering-and-agent-organisation-2026-08-23.md` is a different
subject — a 23 August literature sweep of organisational MAS and self-improvement papers —
and is not a prior reading of `cobusgreyling/loop-engineering`. Treat a name collision as
a collision, not as prior art.

**What this unit does not do.** No dependency is added. Their code is not vendored. Nothing
is opened upstream. `pyproject.toml` still declares `dependencies = []`.

---

## Re-checkable bar

Incumbent: [`cobusgreyling/loop-engineering`](https://github.com/cobusgreyling/loop-engineering),
default branch `main`.

| Field | Brief's 24 Aug snapshot | Re-measured 24 Aug 2026, 17:24 UTC | How to re-check |
|---|---|---|---|
| Stars | 10,633 | **10,635** (`stargazers_count` = 10635) | `GET https://api.github.com/repos/cobusgreyling/loop-engineering` → `stargazers_count` |
| Forks | 1,460 | **1,460** (`forks_count` = 1460) | same → `forks_count` |
| Open issues | 16 | **16** (`open_issues_count`) | GitHub counts **issues plus pull requests**. The sample page mixed PRs (#548, #543) with issues. Do not quote this as "16 issues" without subtracting PRs. |
| Licence | MIT | **MIT**, SPDX `MIT`, `LICENSE` read: *Copyright (c) 2026 Cobus Greyling and contributors* | `license.spdx_id`; raw `LICENSE` |
| Created | 2026-06-09 | **2026-06-09T06:28:20Z** | `created_at` |
| Pushed | 2026-08-24 | **2026-08-24T08:13:28Z** | `pushed_at` |
| Updated | — | **2026-08-24T16:55:10Z** | `updated_at` |
| Language | — | JavaScript | `language` |
| Homepage | — | https://cobusgreyling.github.io/loop-engineering/ | `homepage` |
| npm `loop-audit` | published | **`@cobusgreyling/loop-audit@1.7.0`**, MIT, Node `>=18` | `GET https://registry.npmjs.org/@cobusgreyling/loop-audit/latest` |

Companion repos named from their README, retrieved the same day, and **not** treated as
this bar's star count: `harness-foundry` (versioned stacks, sessions, traces);
`outerloop` (9 stars, pushed 2026-08-24T16:47:05Z — evidence → human verdict → ledger);
`goal-engineering`; `memory-engineering`; `fleet-engineering`. [measured]

**What the bar is.** Closest published product to what `.harness/build_driver.py` and
`scripts/dispatch.py` do: worktree isolation, maker/checker sub-agents, scheduled
automation, skills, MCP connectors, cost observability, and starters for Grok, Claude
Code, Codex and Opencode — the same harnesses Consilient dispatches to. [cited]
[measured: `docs/20-design/backends.md`]

**What beating it would mean.** Not a higher Loop Ready score. A measurement of the rate
at which a check accepts a bad artefact (β), used to bound routing depth and unattended
exposure, on a repository other than this one. Their score does not answer that question.
See below. [asserted]

---

## loop-audit scoring dimensions

Source: `tools/loop-audit/README.md` and `tools/loop-audit/src/auditor.ts` on `main`,
fetched 2026-08-24. Package on npm is v1.7.0; the README heading is "Signals Checked
(v1.7+)". [cited] [FULL]

`computeScore` starts at `SCORE_WEIGHTS.base = 7`, adds boolean weights, then
`Math.min(100, …)`. Levels: L1 at 38 if a state file exists; L2 at 58 if triage exists;
L3 at 78 if verifier + state + cost observability (`loop-budget.md` + `loop-run-log.md` +
LOOP.md budget hints) **and** `loopActivity.present`. [cited]

| Signal (code identifier) | Weight | What the auditor actually looks for |
|---|---|---|
| `base` | 7 | Always awarded |
| `stateFile` | 18 | Presence of `STATE.md` or a named `*-state.md` |
| `triage` | 14 | A listed triage skill name exists |
| `skillsTwoPlus` / `skillsOne` | 14 / 7 | Count of listed loop skill names |
| `verifier` | 14 | A skill or agent file whose name includes `verifier` / `loop-verifier` |
| `loopConfig` | 9 | `LOOP.md` exists |
| `agentsMd` | 9 | `AGENTS.md` or `CLAUDE.md` exists |
| `safetyLoopMd` / `safetyDoc` | 4 / 4 | LOOP.md mentions gate/denylist/auto-merge/safety; `safety.md` / `SECURITY.md` exists |
| `github` / `githubWorkflows` | 6 / 4 | `.github/` and `.github/workflows/` exist |
| `mcp` | 3 | `.mcp.json` (or cousins) **or** LOOP.md mentions MCP |
| `worktree` | 3 | The word "worktree" in a short list of markdown files |
| `registry` | 2 | `patterns/registry.yaml` exists |
| `budgetDoc` / `runLog` / `loopMdBudget` / `budgetSkill` | 3 / 3 / 2 / 2 | Files and keyword hints |
| `toolScope` / `stallDetection` / `escalation` / `gateYaml` | 3 each | `allowed-tools:` frontmatter or regex hints; circuit-breaker hints or a `*ledger*` file; escalation regex; `gate.yaml` exists |
| `constraintsFile` / `constraintsSkill` | 4 / 2 | `loop-constraints.md` / skill |
| `loopActivity` | 6 | "Last run" text, a run-log filename, a loop-ish workflow name, or a recent `git log` line matching loop/triage/audit |
| `harnessStack` / `lock` / `sessions` / `emit` / `host` | 4 / 1 / 2 / 1 / 1 | `.foundry/*` files (funnel into harness-foundry) |
| `memoryTiers` / `memoryBudget` | 4 / 2 | `memory-tiers.md` / `memory-budget.md` |
| `fleetRegistry` / `fleetInbox` | 4 / 2 | `fleet-registry.md` / `fleet-inbox.md` |

The weights sum to more than 100; the cap is the point. Almost every signal is
**file-or-string presence**. `loopActivity` is the one "dynamic" signal, and it is still
presence of timestamps, filenames, workflow names or a matching git subject — not an
outcome, and not a false-accept rate. [cited]

Verifier detection, quoted from the source we fetched: a Claude/Codex agent file whose
basename includes `verifier`, or an Opencode agent name that includes `verifier`, or the
skill name `loop-verifier`. That is a checkbox. [cited]

---

## Failure catalogue

Source: `docs/failure-modes.md` ("Failure Mode Catalog"), fetched 2026-08-24. Ten modes.
Severity S1 annoying / S2 harmful / S3 critical. [cited] [FULL]

| Mode | Severity | Symptom | Stated mitigations |
|---|---|---|---|
| Infinite Fix Loop | S2 | Same PR/CI fixed 5+ times, never converges | Hard attempt cap (e.g. 3) then escalate; separate verifier model; quarantine flakes; record attempt count in state |
| State Rot | S1→S2 | STATE.md cites merged PRs, closed tickets, stale branches | Prune every run; `Last run` + validate IDs; one state file per pattern |
| Verifier Theater | S2 | Verifier "approves" but CI/review finds bugs | Verifier must run test/lint and report output; reject-default instructions; stronger model on verifier |
| Notification Fatigue | S1→S2 | Pings every few minutes; team mutes the bot | Notify only when a human decision is required; digest mode; tighten "High Priority" |
| Token Burn | S1 | Bill spikes on empty/noisy triage | Cheap triage first; delete the scheduler when idle; daily token budget |
| Over-Reach (Wrong Scope) | S2→S3 | Unrelated refactors; denylist paths touched | Path denylist; smallest diff + verifier checks touched files; triage is signal only |
| Comprehension Debt Spiral | S2 | Velocity up, no one can explain the diffs | Human review for non-trivial PRs; weekly digest; cap auto-merge |
| Cognitive Surrender | S2 | "The loop handles it" | Explicit human gates; success = time saved *with* quality held |
| Parallel Collision | S2 | Two sub-agents edit the same files | `isolation: worktree`; lock or queue in state |
| Escalation Failure | S2 | Loop retries; human never notified | Connector ping; waiting-on-human section; alert if parked >24h |

Anti-patterns (`docs/anti-patterns.md`) are the design-time twins: same agent implements
and verifies; no attempt cap; vague triage; L3 before L1; shared state without schema;
write-everything MCP; no kill switch; fixing flakes with code; auto-merge without
allowlist; no run log. [cited]

They have shipped code behind several of those mitigations: `loop-worktree` (one worktree
per attempt, path locks, orphan GC); `loop-context` (deterministic circuit breaker on
iteration count, repeated error, no-progress, token budget — exit 2 to escalate);
`loop-gate` (path denylist / auto-merge allowlist from `gate.yaml`). [cited]

---

## Does it measure false acceptance?

**No.** Confirmed from the auditor source and the failure catalogue, 24 August 2026.
[cited]

loop-audit scores whether a verifier *exists* (`verifier.present`, weight 14) and whether
docs mention tests/gates. It does not run a verifier against a labelled bad artefact. It
does not record accept/reject against ground truth. It does not emit a false-accept rate,
precision, β, or critic recall. The L3 rule is "verifier file + state file + budget files
+ activity hints", not "verifier error rate below a ceiling". [cited]

"Verifier Theater" is named as a failure mode and mitigated by "run the tests" and
"default REJECT". That is operational advice. It is not a measurement of how often the
advice fails. A project can score 82+, sit at L3, and still accept bad work every time the
named verifier is wrong. Their own catalogue predicts that case. [cited] [asserted]

The companion `outerloop` (README fetched 2026-08-24) is closer in vocabulary: evidence
package → **human** verdict with mandatory rationale → ledger → answerability. That is
provenance of a human ship/block decision, not a measured rate at which an automated
check accepts a bad artefact. Its `audit` command "scores governance health". Nine stars;
not this bar. [cited] [measured]

This is the same gap already recorded for Ruflo (`docs/10-research/ruflo-assessment-2026-08-20.md`):
quality gates that grade setups 1–100, and nothing that states how often a gate passes
something bad. [cited] loop-engineering is the closer *orchestration* incumbent; Ruflo
remains the closer *meta-harness popularity* incumbent. Neither measures β. Ratchet
(arXiv:2605.22148v3) still does. [cited]

The preliminary read in the brief is therefore **confirmed**, not refuted.

---

## Primitive map

Their five primitives + memory (`docs/primitives.md`, fetched 2026-08-24) versus this
repository. Both directions. [cited] [asserted for the mapping]

| Their primitive | Closest thing here | Who is ahead, on what evidence |
|---|---|---|
| Automations / scheduling | `scripts/run_loop.py`, `.harness/build_driver.py`, GitHub Actions | They ship pattern kits (daily triage, CI sweeper, PR babysitter) with cadence and token-cost tables. We have a driver and a refuse-exhausted dispatcher. They are ahead on *packaged* loops. We are ahead on *pool/quota refusal* (`scripts/dispatch.py`, ADR-0056). [cited] [measured] |
| Worktrees | `.harness/unit-worktrees/`, dispatch `--cwd` | They ship `loop-worktree`: one tree per attempt, manifest, orphan GC, **path locks with deadlock detection**. We isolate units in worktrees and still spent 24 August on stale bases, double-builds and silent retries. They are ahead on the mechanical convention. [cited] [asserted] |
| Skills | `.agents/skills/`, `.claude/skills/` | Same shape. Ours are pinned to CONSILIENCE.md and carry evidence tags. Theirs are operational (triage, minimal-fix, verifier). Different job. |
| Plugins & connectors (MCP) | `consilient_connectors` (email/SMS/computer-use), instance Playwright; product package is refuse-only | They treat MCP as a first-class loop primitive. We deliberately keep product `src/consilient/` AST-locked (no network, no subprocess). Different floor. [measured: `pyproject.toml`; `tests/test_tier1_imports.py`] |
| Sub-agents (maker/checker) | `scripts/dispatch.py` + cross-family review in `build_driver.py` | Same idea. Unit AV's note (24 Aug) records that the driver writes `<uid>-verify.out` and **never reads it**. They at least document reject-default and a separate verifier role. We have the better *theory* (different class of facts; Ao et al. arXiv:2603.26993) and a broken *consumption* of the second class. [cited] [asserted] |
| Memory / STATE.md | JSONL trajectory (`events.py` single writer), `scripts/recall.py` (EXP-45) | We are ahead on append-only provenance and measured condensation loss. They are ahead on a human-readable loop spine (`STATE.md`, prune rules) that operators actually open. [measured: EXP-45] |
| Cost observability | `consil usage`, adapter usage blobs, `budget.py` | They require `loop-budget.md` + run log as an L3 gate. We refuse exhausted pools and unknown headroom (ADR-0026). Different, both real. |
| loop-context circuit breaker | dispatch leashes, turn caps, claim expiry | **They escalate (exit 2) on stagnation; we have killed runs silently with a turn cap.** That is the defect they already named (Infinite Fix Loop / Escalation Failure / Token Burn). [cited] [asserted] |
| Coordination state | `.harness/driver-state.json`, dispatch claims in the log | They warn against unstructured shared STATE.md. We store orchestration state in a JSON file the driver treats as authoritative. Claims in the log are the better substrate (`events.py`); the driver file is the weaker one. [asserted] |
| β / contract-beta / human-verdict | `consil beta`, ADR-0103, Gate A | **We have this; they do not.** It is the whole of what is left. |

**What they do better, stated without comfort:**

1. Attempt caps that escalate instead of looping or dying quietly.
2. One worktree per *attempt*, with sweep and path locks, not one worktree per unit left stale.
3. A published failure catalogue that already names our 24 August defects (stale state,
   parallel collision, infinite retry, verifier theater, token burn, escalation failure).
4. A single front door (`npx @cobusgreyling/loop init|doctor|status|audit|cost`) that an
   operator can type. Our operator surface is correct (`consil` observe, `dispatch.py`
   orchestrate) and still harder to land on.
5. Dogfooding: they run `validate-patterns` + `audit` on their own repo.

**What we do better, stated without inflation:**

1. An append-only trajectory with a single writer and reconstructable projections.
2. Evidence tags and a bibliography with verification flags — they have stories; we have
   `[measured]` / `[cited]` / `[asserted]`.
3. The exogenous-signal rule and a theorem bound on echo (CONSILIENCE.md; arXiv:2603.26993).
4. β as a first-class quantity, even while Gate A is shut and human-beta is unestimated.
5. Stdlib-only product code with an AST lock. That is a constraint, not a feature, and it
   is load-bearing.

---

## Recommendation

**Keep building this repository. Do not adopt `@cobusgreyling/loop` as a dependency. Do
not vendor their tree. Steal the mechanisms, in our stack, that already solve defects we
measured on 24 August: attempt-cap-then-escalate, path locks, one-worktree-per-attempt
with GC, a circuit breaker that fails *open to a human* rather than silent death, and
atomic/durable orchestration state in the log rather than a JSON file.** [asserted]

Do not open an upstream PR from this unit. If the principal later wants to contribute,
the honest gift is not another starter: it is a scoring dimension that a checkbox
verifier cannot satisfy — a labelled false-accept rate. That would be ADR-0036 applied
in the useful direction.

**Strongest objection (ADR-0036).** The decision is upstream-first: building what already
exists under MIT is permitted only after the existing thing has been tried and found
wanting on a stated dimension. This repository is MIT; theirs is MIT; the maintainer is
active (pushed today; 48-hour review aim on the README). They already ship worktree
locks, a circuit breaker, and a failure catalogue that names our day's defects. "Keep
building" can be the expensive rationalisation this project has already paid for — a
quota-pool rediscovery, a Ruflo teardown commissioned after the adoption note existed.
The objection is that inspiration-without-adoption is how we spend another day
re-implementing `loop-context --check`.

Why the recommendation still stands: **the products are not the same, and adopting theirs
would launder the wrong score as the right one.** Their floor is "is a loop designed".
Ours is "how often does the test accept a bad artefact, and may we depend on that".
Importing an npm CLI into a stdlib-only Python package is an ask-first dependency
(`AGENTS.md`) and would put Node on the product path. Importing their readiness rubric
into `consil doctor` would make Gate A/B report file presence. We have already watched a
hand-maintained copy of doctor drift. A Loop Ready 82 that does not measure β is
verifier theater with a badge.

That is brick versus wet sand, not npm versus Python. The floor is the measurement.
Above the floor, their CLIs and our scripts are interchangeable *as loop machinery*;
below it, adopting them is a retreat.

---

## What is left

After this bar, the novelty claim for the *orchestration layer as a bag of primitives*
is gone. Worktrees, maker/checker, skills, MCP, budgets, scheduled loops: shipped, MIT,
starred, same harnesses. [cited]

What remains, and it is narrower than the README once claimed:

1. **Measure the verifier, not its filename.** β / contract-beta per repository, with a
   denominator, used as a gate rather than a blog number. Ruflo does not. loop-audit does
   not. Ratchet does, in its setting. [cited]
2. **Consume the second class of facts.** A cross-family review whose file is never read
   is echo that spent money. That is our defect, not theirs. [asserted]
3. **Dependence, not scaffolding.** Gate B is whether this harness is trustworthy on
   another repository. Their L3 is "unattended-capable with human gates" scored from
   files. Different question. [measured: `consil doctor` remains the authority; this
   document does not report a gate pass]
4. **Provenance that a third party can replay.** JSONL + single writer versus STATE.md +
   a ledger. We should not lose that while stealing their attempt-cap.

If a later reading finds that `outerloop` or harness-foundry *does* measure false
acceptance, that finding outranks this recommendation and this file should be amended
with the date and the identifier. This pass fetched their READMEs and did not read their
full trees. [asserted]

---

## Better-than-best protocol (threshold met)

A later design decision (adopt vs build) turns on this answer; the repository had no
verified reading of this incumbent; being wrong here is how a false superlative ships
again.

1. **Bar.** `cobusgreyling/loop-engineering` (retrieved 2026-08-24, GitHub API + raw
   docs + `auditor.ts` + npm 1.7.0). Near miss: Ruflo (larger, already assessed, not the
   same harness-loop shape). Near miss: the 23 August "loop engineering" literature sweep
   (same words, different object).
2. **Stress.** The axiom is "presence of loop machinery ⇒ readiness". Exhibited in
   `SCORE_WEIGHTS` and in L3 requiring files + activity hints. The bottleneck is
   epistemic: a test of existence cannot be a test of truth (Whewell's third clause).
3. **Import.** Medical diagnostics: sensitivity/specificity of a screening test, not
   "does the clinic own a sphygmomanometer". Transfers because both are tests with error
   rates.
4. **Synthesis.** Keep the product; copy the mechanical mitigations; refuse the score as
   a gate input. Killing check: if `loop-audit` on this repo, or a future `consil`
   command, is allowed to move a gate, this recommendation is dead.
5. **Validation.** Re-fetch the API row on review-by **2026-09-24**. If stars, licence or
   `auditor.ts` weights change, update the table before citing. Predicted failure of
   *this* document: treating "keep building" as permission to re-implement `loop-worktree`
   poorly. Mitigation: any new isolation/lock/circuit-breaker work names their CLI as the
   incumbent in the same commit.

**Plain answer, and the delta.** The plain answer is "they are the closest thing; they
score files; keep building; don't add npm". The protocol added the exact weights, the
ten-mode catalogue, the Ruflo/Ratchet placement, the ADR-0036 objection stated as the
strongest case against ourselves, and a dated re-check table. If those are unused, the
plain answer was enough.

---

## Search log

Searched 24 August 2026, this worktree and the public web:

| Query / path | Result | What it changed |
|---|---|---|
| `docs/**` for `loop-engineering`, `cobusgreyling`, `loop-audit`, `Loop Readiness` | No hit on the GitHub product. Hit on `docs/10-research/loop-engineering-and-agent-organisation-2026-08-23.md` (academic sweep) and `docs/10-research/sweeps/loop-engineering-sweep-2026-08-23.json` | Prevented treating the 23 Aug note as this bar |
| `docs/10-research/literature-review.md` | No AW unit; no mention of this repo | Corrected the plan pointer |
| `docs/10-research/findings.md`, experiment register | No loop-engineering product measurement | Nothing to reuse |
| `docs/20-design/ruflo-adoption-and-upstream-plan-2026-08-20.md`, `docs/10-research/ruflo-assessment-2026-08-20.md` | Same β question already asked of a larger incumbent | Reused; did not commission a second teardown-shaped document |
| `docs/20-design/backends.md` | Same four harnesses they start | Confirmed the "same harnesses" claim |
| `docs/decisions/0036-…` | Upstream-first | Bound the recommendation's objection |
| `docs/40-spec/v0-draft.md` | Observe-only product; orchestration gated; six commands | This unit stays a document; it does not exceed v0 |
| `docs/00-context/orchestration-failure-modes-2026-08-23.md` | Stale cache / stale-base conflict | Named as our side of Parallel Collision / State Rot |
| `.harness/plan-units.json` `"AW"` | The real unit text | Followed this, not literature-review.md |
| GitHub API + raw README, `auditor.ts`, `failure-modes.md`, `anti-patterns.md`, `primitives.md`, `LICENSE`, loop-audit/loop-worktree/loop-context READMEs | Primary evidence | All `[cited]` numbers and lists above |
| npm registry `@cobusgreyling/loop-audit` | 1.7.0 published | Confirmed the brief's "CLI is npm-published" |
| `cobusgreyling/outerloop` README + API | Human verdict ledger; 9 stars; no β | Closed the "maybe the companion measures it" hole at README depth |
| GitHits `search` on the repo | `AUTH_REQUIRED` | Degraded to GitHub raw + API. Not a snippet-only source. |

Review-by: **2026-09-24**, or immediately after `auditor.ts` `SCORE_WEIGHTS` or the
licence changes.

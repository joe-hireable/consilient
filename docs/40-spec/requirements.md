# Requirements — audit-extracted, attribution not attested

> **Provenance warning, 21 August 2026. Read this before citing anything below.**
>
> These requirements were extracted by an automated audit of the principal's messages.
> **At least one quote was fabricated.** Shown R11 — *"Do not let any arm run unbounded.
> Hard turn and token caps."* — he stated plainly that those are not his words. Its
> attribution is withdrawn below, and two further quotes could not be located in his
> transcripts at all.
>
> **The remaining quotes have NOT been independently re-verified.** Two mechanical
> attempts failed: the transcripts interleave his typed messages with tool results,
> injected file contents and assistant replies, so a naive search matches this document
> quoting itself. The first attempt reported 33 of 36 verified and was wrong. Treat every
> quote here as **audit-extracted, not attested**.
>
> **An obligation can be right while its attribution is wrong.** Where that holds the
> requirement is kept on engineering merit and says so — but it carries no claim on the
> principal's authority. Invariant V0-18 means only he can supply that, and a requirement
> he did not write must never be quoted back to him as though he had.

**Generated** from a 72-hour audit of his messages, 18–21 August 2026, assessed against the
code as built. Regenerate with `python scripts/build_requirements.py`; verify with
`--check`. **Do not hand-edit.**

**36 requirements. 0 met · 26 partial · 2 substrate only · 8 absent.** [measured]

**Status meanings.** *Met* — implemented and enforced by a test that can fail. *Partial* —
some of it works. *Substrate only* — the machinery exists but nothing uses it, which is the
most misleading state because a code inventory reads as progress while a user gets nothing.
*Absent* — no implementation.

## Blocking requirements

These unblock other work, so they come first. **19 of 36.**

| id | area | requirement | status | effort |
|---|---|---|---|---|
| **R14** | mcp | One dynamic context loader selects tools/MCPs/skills/plugins/connections per task; no domain-ke | ABSENT | large |
| **R28** | gates | Local-model selection is gated at download time against auto-detected hardware so the harness c | ABSENT | medium |
| **R30** | gates | Reversible decisions are taken autonomously by the agent, with the reversal path recorded; defe | ABSENT | medium |
| **R19** | privacy | Consent for product-improvement feedback and for training use are separately obtained and visib | SUBSTRATE ONLY | large |
| **R08** | skills | .agents/skills is the single source of truth and .claude/skills mirrors it, with a CI check tha | PARTIAL | small |
| **R11** | budget | Every dispatched run carries an enforced turn cap and token cap; unbounded runs are prohibited. | PARTIAL | medium |
| **R07** | orchestration | Any multi-agent structure must declare the distinct evidence class it contributes; structures t | PARTIAL | medium |
| **R13** | tools | The capability/tool layer is curated from existing licensed open-source components, with a docu | PARTIAL | small |
| **R15** | routing | Two execution paths must both exist: delegation to the user's chosen agent under their own cred | PARTIAL | large |
| **R12** | other | The harness and its documentation must cover chats, projects, tasks, scheduled (cron and one-of | PARTIAL | large |
| **R10** | orchestration | All agent interaction is written to the append-only replayable trajectory log; unlogged work is | PARTIAL | medium |
| **R24** | privacy | Model discovery and capability probing run locally on demand with no default telemetry and no p | PARTIAL | large |
| **R27** | budget | Routing decisions account for remaining subscription usage limits and for user-specified spend  | PARTIAL | medium |
| **R34** | coding | QA and QA automation is a first-class harness capability with its own R&D pipeline: synthetic d | PARTIAL | large |
| **R26** | routing | All five backends (Claude, Codex, Cursor Max plans; Ollama local; OpenRouter) are wired in as u | PARTIAL | medium |
| **R29** | gates | The harness escalates to the human only for irreversible, genuinely preferential, or destructiv | PARTIAL | medium |
| **R32** | orchestration | Orchestrator agents detect stalled workers and recover them without human intervention; stall d | PARTIAL | large |
| **R33** | budget | All three subscription providers are kept concurrently utilised near their included capacity, w | PARTIAL | large |
| **R36** | other | Adopt the best existing open-source component and contribute fixes upstream; building custom re | PARTIAL | medium |


## Budget

### R11 — PARTIAL

> [ATTRIBUTION WITHDRAWN] Do not let any arm run unbounded. Hard turn and token caps.

**Obligation.** Every dispatched run carries an enforced turn cap and token cap; unbounded runs are prohibited.

**blocks other work** · effort: medium

**Gap.** Neither cap Joe named exists. (1) Turn cap: build_command (scripts/dispatch.py:443-543) passes no turn limit to claude, grok, codex or cursor-composer, so an arm may take unlimited turns inside its 600s window; the existing optional_flags(help_text(...)) probe already used at :471, :482 and :496 is the mechanism a cap would ride on, and nothing uses it for this. (2) Token cap: no token counter and no token ceiling exists at all — dispatch does not even request structured output from claude or codex (only cursor-composer gets --output-format, and it is `text`, :512-513), so no token figure is available to cap against. (3) Defaults are unbounded where machinery does exist: loop.max_ticks defau

**Evidence.** [measured] ENFORCED: an unconditional wall-clock deadline on every dispatched arm — scripts/dispatch.py:92 (DEFAULT_TIMEOUT_S=600), :1276 (--timeout), plumbed to the single-run path :1371 and the fan-out path :1394, killed by tree at :361-368 (process.wait -> kill_process_tree). Test that can fail:

### R27 — PARTIAL

> We also need the consilience meta harness to route intelligently based on usage limits for frontier subscriptions or specified budgets within OpenRouter etc.

**Obligation.** Routing decisions account for remaining subscription usage limits and for user-specified spend budgets on metered providers.

**blocks other work** · **he asked more than once** · effort: medium

**Gap.** Three things are missing. (1) No routing decision anywhere consults an OpenRouter spend budget: there is no metered route in the registry, and `check_budget` never reaches the selector — the requirement's second clause ("or specified budgets within OpenRouter") has no implementation, only a loop-stop. (2) The subscription headroom the router acts on is never checked for freshness: a snapshot from any date routes silently, and on a fresh checkout it is the hard-coded 21 August figures, so `select()` will keep declaring claude-weekly exhausted and cursor-models 1% used indefinitely. Routing on an unbounded-age number is the same failure class `budget.py` already refuses with `_STATE_MAX_AGE`.

**Evidence.** SUBSCRIPTION HALF — WIRED AND ENFORCED [measured]. `src/consilient/harness.py:439` `select()` and `:238` `select_model()` rank candidates by remaining pool headroom, hard-refuse exhausted pools (`_is_exhausted`, `:373`, threshold `EXHAUSTED_USED_PERCENT = 90.0` at `:25`) and refuse unknown headroom

### R33 — PARTIAL

> Make sure we are continuously fully utilising intelligence across codex, claude code and cursor models and maximally utilising the $200 max plans across the 3 providers without being wasteful, overengineering  etc

**Obligation.** All three subscription providers are kept concurrently utilised near their included capacity, without waste or over-engineering; idle paid capacity is a defect.

**blocks other work** · **he asked more than once** · effort: large

**Gap.** Four things are missing, in dependency order. (a) A producer for headroom: nothing writes `.harness/usage/*.json`, so `usage.py`'s collectors have no input and `.harness/headroom.json` is a hand-typed operator observation with no expiry. Needs a probe (exp07/headroom.py already works for Codex) plus a claude status-line and cursor capture, and a freshness gate on `PoolState.observed_at` mirroring budget.py's `_STATE_MAX_AGE` so a stale snapshot refuses instead of being trusted forever. (b) A join between usage.py collectors and harness.pools_from_mapping — today they are two unconnected representations of the same fact, which is why `codex-weekly.used_percent` is still None and Codex is auto

**Evidence.** WORKS [measured]. Headroom-aware selection is wired into the live run path and demonstrably changes which provider runs: src/consilient/harness.py:118-157 (DEFAULT_POOLS, five pools over four providers), harness.py:373 `_blocked` (real gate: exhausted or >=90% used refuses), harness.py:441 `select`


## Coding

### R34 — PARTIAL

> how we can facilitate automated codebase QA and automation via the harness.  Including synthetic data generation, synthetic users, sandboxes, whatever else. […] the QA and QA automation stuff really needs a dedicated and extensive R&D pipeline including experimentation and simulations etc.

**Obligation.** QA and QA automation is a first-class harness capability with its own R&D pipeline: synthetic data generation, synthetic users, sandboxes, experiments and simulations.

**blocks other work** · **he asked more than once** · effort: large

**Gap.** Three of the five named components have no implementation. (1) Synthetic users: ADR-0055 specifies the run-spec object and the finding object in prose only; no dataclass, no runner, no findings store, and no code path enforcing clause 3 (an unmeasured verifier's pass may not accept) — the guard every future verifier is supposed to inherit. (2) Sandboxes: none exist; dispatch defaults to bypassing the child harness's sandbox (harness.py:39,42), so a driven QA run today would execute unconfined. (3) First-class harness capability: QA has no surface — no `consil` subcommand, no module in src/consilient/, and dispatch drives no QA run; every instrument is an out-of-tree experiment script invoked

**Evidence.** BUILT+USED: docs/10-research/experiments/exp47/run_exp47.py:1-507 ran a 1,931-mutant census producing beta=0.3132 [0.2926,0.3346] (results-exp47.json, register line 1464 `DONE`); tests/test_exp47.py:19-60 asserts Wilson boundaries, diff extraction and equivalence classification against fixed values


## Design

### R20 — ABSENT

> Feedback prompts must be skippable with no consequence and no re-ask.

**Obligation.** Any feedback prompt can be skipped with no functional consequence and is not re-asked.

effort: medium

**Gap.** Everything the obligation covers is missing, and so is the thing it constrains. Needed, in order: (1) a task-close feedback surface at all — three questions rendered from a pre-committed goal record, which itself does not exist (`work_item.opened` carries only a 500-char claim string, `coordination.py:258`); (2) an explicit skip path whose functional consequence is nil — nothing gated, no capability withheld, per ADR-0024's forbidden list; (3) a durable per-task asked/declined record in the append-only log so a skip is never re-asked for that task — no such event kind exists (`work_items.KINDS` is opened/comment/completed only). Because there is no prompt, the "no re-ask" guard has nothing t

**Evidence.** [measured] The obligation lives only in prose. `docs/20-design/feedback-signals.md:57` ("Asked, at task close only ... skippable with no consequence and no re-ask") and `:121-122` (friction budget) are its only statements, and line 3 of that same file marks the whole document "Status: **v1+ design d

### R22 — PARTIAL

> Do not build response-level rating at all. A response is an intermediate artifact; rating it measures whether it read well in the moment.

**Obligation.** No response-level rating surface may be built; the unit of feedback is the task, measured by goal achievement, cost, durability and turns.

effort: small

**Gap.** Missing: a regression guard. Compliance today rests entirely on nobody having written the code - there is no check that fails if a response-rating field, prompt or widget is added tomorrow, and v0-draft.md:422 already asserts such a check exists when it does not. Needed: one invariant test that (i) greps the source tree and the rendered dashboard for approval-signal fields/strings (thumbs, satisfaction, rating, helpful, star, 1-5 scale) and fails on any hit, and (ii) asserts events.validate() rejects an event carrying an approval-style field, so the prohibition lives in the schema rather than in prose. Also missing, but staged not skipped: the positive clause - goal recorded at dispatch, tur

**Evidence.** PROHIBITION HOLDS IN FACT [measured]. Repo-wide searches found no response-level rating surface: (1) `grep -rniE "rating|thumbs|upvote|downvote|response[-_ ]?level" src packages tests scripts` -> only substring false positives ("orchestrating", "operating system", "generating"); (2) `grep -rniE "\br

### R23 — PARTIAL

> Document that these are recorded SEPARATELY and never collapsed into a single score unless the user has explicitly set the trade-off.

**Obligation.** Efficiency and goal-achievement are stored as separate signals; any composite score requires an explicit user-set weighting.

effort: small

**Gap.** Two things are missing. (1) STORAGE: goal-achievement is not recorded anywhere — no task-close question surface, no durability check, no column in projection.py's SCHEMA, no event kind in events.py. So "stored as separate signals" is vacuously true rather than satisfied: only the cost side exists (duration_s on dispatch.outcome; provider quota rows in the `usage` table), and there is nothing to keep separate from it. (2) ENFORCEMENT: no test can fail if someone adds a default composite score tomorrow. Nothing in tests/ references docs/20-design/feedback-signals.md, and the repo has doc-invariant tests elsewhere (tests/test_v0_invariants.py:1174-1229 pins doc content for other rules), so the

**Evidence.** [measured] DOCUMENTED: docs/20-design/feedback-signals.md:107-116 — section "Efficiency and achievement are recorded separately — permanently": "Achievement (asked + durability) and cost (derived) are **separate records**. No default composite score exists anywhere in the product." / "Any composite

### R31 — PARTIAL

> human users can correct, jump in at any point, have maximum visibility or none at all or a mix depending on how they feel.

**Obligation.** A visibility/intervention dial exists letting the human interrupt or correct at any point and choose full, zero, or partial visibility.

**he asked more than once** · effort: large

**Gap.** The dial does not exist in any form: no levels, no floor set, no per-kind `--see` overrides, no configuration-load floor validation, no `visibility_change` event, no effective level on `verdict`/`approval` events, and no streaming surface to render at a level (dispatch writes to files, the dashboard is a one-shot static HTML render with no refresh). "Zero visibility" and "full visibility" are not selectable states — the only variation is `--json` versus text formatting. On the intervention side: the human can HALT the always-on loop mid-tick and can OVERTURN a verdict after the fact, but cannot jump into or correct a dispatched agent run at any point — no stop file honoured by dispatch, no s

**Evidence.** VISIBILITY HALF — ABSENT. `grep -rn "visibility" --include=*.py .` (excluding .venv/ and build/) returns exactly ONE hit repo-wide: tests/test_v0_invariants.py:1988, and that is a JSON string inside a recorded trajectory fixture, not code. `grep -rnE '"--see"|"--level"|"--quiet"|"--silent"|"--fireho


## Documentation

### R03 — PARTIAL

> Supersede ADRs, never silently edit them. The trail of reversals is the point.

**Obligation.** ADR changes must be recorded as supersessions with the prior text intact; silent in-place edits are prohibited. Testable from git history over docs/decisions/.

**he asked more than once** · effort: small

**Gap.** No check tests the obligation from git history, which is exactly where the brief says it is testable. Three specific things are missing: (1) a checker that, for each commit touching docs/decisions/NNNN-*.md, reads the parent blob's Status and fails when it was ACCEPTED/SUPERSEDED and the whitespace-insensitive diff deletes or modifies body lines without adding a supersession pointer or a dated correction block quoting the prior text — my ad-hoc version of this took ~30 lines and surfaced 9 candidate commits in one run; (2) a trail-integrity check: every "SUPERSEDED by NNNN" resolves to an existing file, the superseded ADR carries the back-reference, and every ADR has a row in index.md — this

**Evidence.** DOCUMENTED TWICE, ENFORCED BY NO HISTORY CHECK. Rule: docs/decisions/README.md:70-74 and .agents/skills/writing-adrs/SKILL.md:74-79 ("Never rewrite an ACCEPTED ADR to reflect a changed mind... the trail of reversals is the most valuable thing in the directory"). [measured]

THE ONE MECHANICAL PART T

### R05 — SUBSTRATE ONLY

> Never cite a [SNIP] or [2ND] source publicly.

**Obligation.** Publication-facing documents may cite only [FULL]/[ABS]-verified sources; a [SNIP] or [2ND] flagged source appearing in a public artefact is a violation.

**he asked more than once** · effort: small

**Gap.** There is no executable checker for citation depth — no `.github/scripts/check_source_depth.py` or equivalent, no release_check.py gate, no pre-push step, no CI step, no test. Enforcement is entirely a prose instruction that a human or a dispatched agent must remember, in four separate documents, and the pre-publication-gate skill openly records the enforcement mechanism as "you". The single concrete check that was written (RELEASE-PLAN.md:319-322) is PowerShell-only, depends on `rg` being installed, and points at a `$release_root` placeholder path that does not exist — the exact defect release_check.py's own docstring says it was built to fix, for every other item on that checklist but this

**Evidence.** [measured] Substrate exists and is populated: `.agents/skills/citing-sources/SKILL.md:14-19` defines [FULL]/[ABS]/[SNIP]/[2ND]; the three publication drafts apply per-citation depth markers — `docs/50-publications/P1-proxy.md` 38, `P2-guards.md` 26, `P3-echo.md` 21 (85 total, counted via `grep -oE '

### R06 — PARTIAL

> Keep docs/00-context/friction-log.md updated as you go — every manual step you have to do that Consilience should automate. That log is the v0 backlog.

**Obligation.** Every manual step an agent performs that the harness should automate is appended to friction-log.md, and that log is treated as the v0 backlog.

**he asked more than once** · effort: small

**Gap.** Two things are missing. (1) Enforcement: nothing appends to the log, nothing prompts an agent to, and nothing fails when it goes stale — so it degraded to a two-day artefact the moment attention moved elsewhere. This is the project's own catalogued failure shape: a documented rule with no check behind it. The cheapest honest fix is a staleness check in tests/test_v0_invariants.py or .githooks/pre-commit comparing the newest `| YYYY-MM-DD` row against the newest commit date and failing when the lag exceeds a threshold, plus a standing line injected by scripts/dispatch.py into every worker prompt. The check must fail on the current tree (it would: newest row 2026-08-20, newest commit 2026-08-2

**Evidence.** [measured] ATTRIBUTION VERIFIED: .harness/dispatch/joe-messages.txt line 19 contains Joe's verbatim words ("Keep docs/00-context/friction-log.md updated as you go — every manual step you have to do that Consilience should automate. That log is the v0 backlog."). ARTEFACT EXISTS: docs/00-context/fric


## Gates

### R01 — PARTIAL

> Evidence tags on every claim: [measured] / [simulated] / [cited] / [algebra] / [asserted]. [asserted] is honest. Mislabelling is not. Never report a simulated figure as a fact about the world.

**Obligation.** Every claim in the repo carries one of the five evidence tags; a simulated figure may never be presented as a fact about the world. Testable by a lint/verify pass over docs for untagged or mis-tagged claims.

**he asked more than once** · effort: medium

**Gap.** Three distinct gaps. (1) NO DOCS LINT. I3 ("no claim in docs/ without an evidence tag") is a documented rule with zero enforcement — no script, no CI step, no git hook, no test reads a markdown file. This is the repo's catalogued failure pattern, in its own first rule. (2) THE ENFORCED TAG SET IS INCOMPLETE: PROVENANCE (events.py:51) holds only {measured, cited, asserted}. `simulated` and `algebra` are rejected values, so the exact harm Joe named — "never report a simulated figure as a fact about the world" — cannot even be expressed in the one place tags are machine-checked; a simulated figure must currently be mislabelled as one of the other three to pass validation. (3) MIS-TAGGING IS UNC

**Evidence.** ENFORCED SLICE [measured]: src/consilient/events.py:376-382 `_check_provenance` raises EventError unless a value is in PROVENANCE; called at events.py:345 (quota) and :359 (spend). Tag set at events.py:51 is frozenset({"measured","cited","asserted"}). Real failing-capable test at tests/test_v0_invar

### R02 — PARTIAL

> Any invariant ships with the check that enforces it, in the same commit (I1). A chokepoint without a lint rule banning bypass is not a chokepoint.

**Obligation.** No invariant may be documented without its enforcing check landing in the same commit. Testable: for each stated invariant there is a corresponding executable check.

**he asked more than once** · effort: medium

**Gap.** Nothing executable verifies the invariant-to-check pairing. There is no artefact that (1) enumerates declared invariants (the 26 V0-NN rows in docs/40-spec/v0-draft.md §11, the 35 V0 ids across docs/, and the 64 ADR "## Enforcement" sections) and asserts each names an executable check that exists and is reachable from CI, and (2) fails a commit that adds an invariant declaration without adding its check. The "same commit" half is enforced only by an unchecked PR-template box (.github/PULL_REQUEST_TEMPLATE.md:57), which is self-attestation, not a check. Concretely uncovered today: 20 of 35 declared V0 ids are named nowhere in executable code; ADR-0064's vendor allowlist and joint ceiling and

**Evidence.** WORKS [measured]: .github/workflows/invariants.yml runs mypy --strict, ruff, 199 pytest invariant tests, check_rename_safety.py --check (:32), check_no_spend_escalation.py --check (:37), check_foreign_identifiers.py --self-test (:47), and a replay drift control (:50-89) whose two assertions can both

### R04 — PARTIAL

> Apply stopping rules honestly, including when they kill a decision I like.

**Obligation.** Every experiment fixes its stopping rule before the run and the recorded outcome must follow it even when it kills a favoured decision.

**he asked more than once** · effort: medium

**Gap.** Three distinct holes. (1) Nothing verifies a stopping rule was fixed BEFORE the run — 75 of 76 register entries have no commit pin and the only control is an unenforced PR-template checkbox, so a rule written after seeing the result is indistinguishable in the record from one written before it. (2) Nothing verifies a stopping rule exists — 3 of 76 entries have none, including EXP-04 which is marked DONE, contradicting the register's own header rule at line 8-9. (3) Only EXP-01's fired rule is connected to any decision: cli.py's REQUIREMENTS table (lines 99-107) hard-codes seven gate conditions and the "fired" check appears in the A1 branch alone, so EXP-16 rule 2, EXP-47 rule 1 and EXP-56 ru

**Evidence.** ENFORCED: src/consilient/cli.py:283-301 fails Gate A1 when EXP-01's register entry contains "stopping rule FIRED", overriding an otherwise-passing beta interval; non-vacuous test at tests/test_v0_invariants.py:2517-2531 (fixture supplies beta 0.3132 [0.2800,0.3464], half-width 0.0332, which would PA

### R18 — PARTIAL

> [ATTRIBUTION WITHDRAWN] NEVER a training target: "was this helpful?" style approval signals.

**Obligation.** Stated-approval signals are prohibited as a training or optimisation target anywhere in the system.

effort: small

**Gap.** The prohibition is enforced only incidentally and only on one channel. (1) V0-21's declared check does not exist: no test anywhere refuses a satisfaction, thumbs-up or confidence field as a routing or acceptance input — the accept/reject enum test at tests/test_v0_invariants.py:731 was written for V0-18 authorship and blocks a graded rating only as a side effect of the enum. This is a documented-rule-with-nothing-enforcing-it of exactly the catalogued kind. (2) events.validate() has no data-field allowlist, so an approval field can be appended to the authoritative log today; nothing would refuse it and nothing would notice a later consumer reading it. (3) The training-target half has zero en

**Evidence.** DOCUMENTED, THREE PLACES [measured]: docs/40-spec/v0-draft.md:422 (V0-21: "no self-report, human or model, is an acceptance or routing input"); docs/40-spec/v0-draft.md:233-238 ("the same rule applies to user satisfaction, a thumbs-up, or an answer to 'did that help?'"); docs/20-design/feedback-sign

### R28 — ABSENT

> for local models it must be smart about not overloading the user's hardware. This should be gated at download as discussed based on the hardware the user has detected.

**Obligation.** Local-model selection is gated at download time against auto-detected hardware so the harness cannot overload the user's machine.

**blocks other work** · **he asked more than once** · effort: medium

**Gap.** Everything. Missing: (1) hardware autodetection — GPU/VRAM, system RAM, free disk, backend (CUDA/ROCm/Metal/CPU), unified-vs-discrete — nothing in src/ or scripts/ reads machine spec; (2) a fit decision per docs/10-research/local-model-fit-arithmetic.md (W + KV + G + F <= 0.9 * VRAM_total), whether built or wrapped via the llmfit candidate ADR-0026 defers to a separate dependency-approval decision; (3) any model-download or local-execution path at all, so there is no byte-transfer boundary at which to refuse — ADR-0005 §Enforcement requires the refusal be at the engine boundary, "a UI-only gate is not a gate"; (4) fail-closed on *unknown* as well as infeasible, which docs/40-spec/v0-draft.md

**Evidence.** [measured] Attribution confirmed: .harness/dispatch/joe-messages.txt:73 carries the quote verbatim. No implementation: `grep -rn "nvidia-smi" src/ scripts/ tests/ packages/` exits 1 (no matches); `grep -rni "vram|hardware|gguf|ollama" src/ scripts/ tests/ packages/` yields one hit only, src/consilie

### R29 — PARTIAL

> The user must be free to only make the irreversable calls that really have no clear answer. Or potentially destructive actions like making a payment, handling a sensitive credential, etc.

**Obligation.** The harness escalates to the human only for irreversible, genuinely preferential, or destructive actions (payment, credentials); everything else it decides itself.

**blocks other work** · **he asked more than once** · effort: medium

**Gap.** Four distinct gaps. (1) NO ESCALATION PRIMITIVE EXISTS. The harness cannot ask, so "escalates only for X" holds vacuously rather than by design. ADR-0033's own Enforcement section (docs/decisions/0033-decide-by-default-ask-only-where-the-user-is-the-only-valid-decider.md:283-287) lists four checks; only the first (an unknown decision class is rejected — events.py HUMAN_ONLY) exists. Bullet 2 "an autonomous decision event without a `reversal` field fails schema validation" is unimplemented: events.REQUIRED at events.py:36 is ("v","ts","event","actor","data") and `reversal` appears nowhere in src/ — its only occurrences are inside historical fixture strings at tests/test_v0_invariants.py:1985

**Evidence.** [measured] HALF THAT WORKS — "everything else it decides itself": src/consilient/harness.py:39 DEFAULT_PERMISSION_MODE="bypass"; BYPASS_FLAGS harness.py:40-45; permission_flags harness.py:313-319; load_permission_mode harness.py:322-337; scripts/dispatch.py:459-460 injects "Do not wait for confirmat

### R30 — ABSENT

> Users can easily reverse reversible decisions. So these should be made autonomously.

**Obligation.** Reversible decisions are taken autonomously by the agent, with the reversal path recorded; deferring a reversible decision to the human is a defect.

**blocks other work** · **he asked more than once** · effort: medium

**Gap.** Everything except the prose. Three things are missing and each is load-bearing. (1) There is no autonomous-decision event kind — src/consilient/events.py declares six kinds and none of them represents "the harness decided X", so there is no record for a reversal path to live on. (2) There is consequently no required `reversal` field and no schema test rejecting a decision that lacks one (V0-22); the sole decision-shaped event, `spend.reserved`, is actively pinned by tests/test_budget.py:229-236 to a five-key dict that excludes it, so the current test suite would reject the fix. (3) There is no ask surface at all, so the second half of the obligation — "deferring a reversible decision to the

**Evidence.** [measured] `grep -rn "reversal" src packages scripts` returns 0 matches; the word occurs in no shipped code. [measured] `grep -rn "V0-22\|V0-23\|V0-24" src tests packages scripts` returns 0 matches — these are the three spec invariants that encode R30 (docs/40-spec/v0-draft.md:425 V0-24, and the V0-


## Gtm

### R21 — ABSENT

> ADR-0024 forbids withholding capability as reward, so recognition must be social, never functional — no perks, no unlocked features, no tiering.

**Obligation.** Contributor recognition is social only (release notes, contributors file); no perks, unlocked features or tiering may be granted as reward.

effort: small

**Gap.** Both limbs missing. Positive limb: no CONTRIBUTORS file, no opt-in naming mechanism, no release-notes or project-stats crediting path — so there is no social recognition to be "social only". Negative limb: no test or build check would catch a perk, tier or unlocked feature if one were introduced; the prohibition lives only in two prose paragraphs, the exact pattern release_check.py:17-19 catalogues as thirteen guards that could not fail. Also unbuilt upstream: the feedback/outcome-reporting contributor class itself (zero "feedback" hits in src), which is what feedback-signals.md says the credit is for.

**Evidence.** [measured] Rule stated in prose only: docs/00-context/ways-to-contribute.md:56-58 and docs/20-design/feedback-signals.md:150-153. Nothing implements it. `find . -iname "*contributor*"` over the whole tree returns nothing — no CONTRIBUTORS file exists. `grep -rni "feedback" src tests scripts --includ


## Mcp

### R14 — ABSENT

> Tools, MCPs, skills, plugins and connections are loaded DYNAMICALLY for the task, not statically by domain. Therefore there is no "code mode" and no "document mode". One loader, task-appropriate context.

**Obligation.** One dynamic context loader selects tools/MCPs/skills/plugins/connections per task; no domain-keyed modes exist in the architecture.

**blocks other work** · effort: large

**Gap.** Everything on the positive half. There is no loader object, no per-task capability selection record, and no injection of a selected tool/MCP/skill/plugin/connection set into any child invocation — build_command (scripts/dispatch.py:443) passes none and would need a per-vendor injection leg for each of claude/grok/codex/cursor, whose flags already diverge there. No fail-closed validator gates what a task may load (exp27's validate_capability_record covers CLI flags, not capabilities, and is unwired). The negative half ("no domain-keyed modes") is currently true only by absence: nothing keys behaviour on domain, but no test would fail if a code-mode/document-mode branch were added to scripts/d

**Evidence.** [measured] No implementation in the run path. scripts/dispatch.py:443-544 build_command() is the sole child-invocation site; for all four harnesses it emits argv = binary + permission/model flags + "Read the file <brief> and do exactly that task" — zero tool/MCP/skill/plugin/connection selection; ch


## Memory

### R09 — PARTIAL

> Set up the bootstrap harness per ADR-0017: Graphify + MemPalace, git-hook updates not agent-hook updates

**Obligation.** Memory bootstrap uses Graphify plus MemPalace, refreshed by git hooks rather than agent hooks. Testable: hook installed in .git/hooks, no agent-hook refresh path.

effort: medium

**Gap.** Three things missing. (1) `.githooks/post-commit` does not exist — the working hook body sits orphaned in `.git/hooks/post-commit`, which `core.hooksPath=.githooks` makes unreachable, so no graph refresh has run since the redirect; move the file and add it to the `install_hooks.py:19` existence check. (2) No test asserts `.githooks/post-commit` exists or invokes graphify, so the regression is invisible; `tests/test_hooks.py` must gain an assertion that fails when the hook is absent. (3) MemPalace is absent from the bootstrap entirely — no repo config, no git-hook refresh, no consumer; the store predates the instruction by two days and nothing writes to it. Also missing is ADR-0017's own stal

**Evidence.** [measured] The git-hook refresh is written but DEAD. `C:/Users/jpbpr/Repositories/consilience/.git/hooks/post-commit:1-4` contains exactly the ADR-0017 hook ("git-hook updates, not agent-hook updates — per Phase 2 spec"; runs `graphify.watch._rebuild_code`). But `core.hooksPath=.githooks` is set in


## Orchestration

### R07 — PARTIAL

> Any multi-agent structure must name the different class of facts it introduces (ADR-0010), or it does not ship.

**Obligation.** Any multi-agent structure must declare the distinct evidence class it contributes; structures that cannot name one are blocked from shipping. Testable as an admission check on agent/meeting definitions.

**blocks other work** · effort: medium

**Gap.** The declaration is opt-in, so the "or it does not ship" half of the rule does not exist. Three things are missing. (1) No admission check that a multi-agent structure carries `contributors` at all: `events.py:398` returns early when the field is absent, so any structure can escape V0-26 by staying silent — proven by validate() accepting a three-agent `fleet.dispatched` with no contributors and a `dispatch.fanout` naming `grok` twice. Fix: name the multi-agent event kinds (`dispatch.fanout`, `fleet.*`, any future merge kind) and require a `contributors` list of length ≥ 2 on them, converting the opt-in invariant into a closed one. (2) No configuration-load check on agent role definitions, whi

**Evidence.** IMPLEMENTED: `src/consilient/events.py:385-427` `_check_evidence_class` (V0-26) refuses a multi-contributor event whose contributors carry duplicate, missing, empty or case/whitespace-variant `evidence_class`; called from `validate()` at `events.py:175`. Non-vacuous tests at `tests/test_v0_invariant

### R10 — PARTIAL

> Log everything in the append-only trajectory format from ADR-0006 so the whole thing is replayable. A meeting absent from the log does not count.

**Obligation.** All agent interaction is written to the append-only replayable trajectory log; unlogged work is treated as not having happened.

**blocks other work** · effort: medium

**Gap.** The format, the single writer, and replay are done to a high standard. What is missing is *completeness* — the half of R10 that says unlogged work does not count. Concretely: (1) no start-of-run event in committed code, so a dispatch killed between launch and return leaves no trace — measured twice in today's log; (2) no check anywhere reconciles `.harness/dispatch/` run directories against run_ids in the trajectory, so the 18-of-36 gap is invisible to every command the repo ships (`doctor`, `replay`, `dashboard`); (3) `coordination.py`, which contains the pre-run claim event, is untracked and unexercised on the real record; (4) the bypass ratchet — the only check enforcing "append() is the

**Evidence.** BRIEF CORRECTION FIRST: the verbatim sentence quoted as Joe's words traces in this repository only to `docs/10-research/experiment-register.md:404-405`, inside the EXP-16 *protocol* ("Every event logged to the append-only trajectory JSONL (ADR-0006 format); a meeting absent from the log does not cou

### R32 — PARTIAL

> Orchestrators/manager agents/leadership agents shod be able to catch and fix stalled agents etc. We waited ages on that

**Obligation.** Orchestrator agents detect stalled workers and recover them without human intervention; stall detection is a harness capability, not a manual check.

**blocks other work** · effort: large

**Gap.** Nothing detects a stalled dispatched worker and nothing recovers one. The three clauses of the obligation fail separately: (a) DETECT — dispatch.py has only an end-to-end 600s deadline, no mid-run progress sampling; the artefact-progress detector that exists (loop.status) is never applied to a worker because dispatch.py does not import it, so a stalled agent stays stalled for the full timeout, which is exactly the wait Joe complained about; (b) RECOVER — no requeue, restart, re-dispatch, stall event, diagnostic capture or escalation exists anywhere; ADR-0034 §3 (record stall + capture diagnostics + escalate + do not terminate), §5 (lease + fencing epoch before reassignment) and §6 (observabl

**Evidence.** EXISTS [measured]: (1) src/consilient/loop.py:253-349 `status()` resolves liveness from artefact progress (transcript bytes since the tick's intent record), never a PID; enforced by tests/test_v0_invariants.py:3493-3541, which can fail (writes bytes, asserts the flip, plus an AST scan forbidding pro


## Other

### R12 — PARTIAL

> Consilience is not coding-specific. It orchestrates any agentic work: chats, projects, tasks, scheduled agents (cron and one-off), background agents, and parallel background workflows.

**Obligation.** The harness and its documentation must cover chats, projects, tasks, scheduled (cron and one-off) agents, background agents and parallel background workflows — not coding alone. Coding is v0 only because it has a cheap oracle.

**blocks other work** · effort: large

**Gap.** Three of the six modes have no implementation and one has no enforcement. (1) Chat: no session continuity — dispatch builds a fresh one-shot `-p` invocation per run, so a multi-turn interactive mode needs a per-harness resume/session mechanism (each vendor CLI differs) plus a session id on the trajectory record. (2) Project: no durable cross-session context object; recall.py's trajectory pack is the only thing spanning sessions, and it is not keyed to anything. (3) Scheduled: ADR-0051's own schedule invariants are unimplemented — no schedule registry, no mandatory `expires_at`, no per-schedule budget principal wired into budget.py's ceilings, no disarm-and-escalate-once on exhaustion. A cron

**Evidence.** DOCS HALF — MET. docs/20-design/work-modes.md:13-20 tables all six modes (Chat, Project, Task, Scheduled cron/one-off, Background, Parallel background workflows) with the review-ceiling arithmetic; README.md:23-26 ("work in general — chats, projects, tasks, scheduled and background runs, parallel wo

### R36 — PARTIAL

> if we use mempalace or something or mem0 or graphify or a combination we should PR upstream rather than custom engineering everything unless.validated by experimentation and research etc.

**Obligation.** Adopt the best existing open-source component and contribute fixes upstream; building custom requires experimental/research justification recorded first.

**blocks other work** · **he asked more than once** · effort: medium

**Gap.** Three distinct gaps, in ascending cost.

(1) ADR-0065's two owed checks, both explicitly named at :134-136. (a) The tier-1 third-party import ban -- the AST machinery ALREADY EXISTS at tests/test_v0_invariants.py:3944-3964 (20 lines), but it is scoped to the whole package rather than the tier-1 module list (beta, events, projection, recall, budget, work_items, coordination, routing). It must be SPLIT, not extended: tier 1 keeps the hard ban, tier 2 modules must become permitted to import an adopted library, otherwise the enforced position is "adopt nothing", which is the opposite of what Joe asked for. Today no tier-2 module can legally take a dependency. (b) No check records an adopted depe

**Evidence.** DOCTRINE (real, and one half genuinely practised): docs/decisions/0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md is ACCEPTED 21 Aug 2026 and states the adopt-vs-build test ("a component whose error rate must be measured is native... one whose errors are self-evident may be adopted"


## Privacy

### R19 — SUBSTRATE ONLY

> Feedback for PRODUCT IMPROVEMENT and feedback for TRAINING are different purposes and must not be bundled — that bundling is the specific manoeuvre §3 forbids.

**Obligation.** Consent for product-improvement feedback and for training use are separately obtained and visibly separate in the UI, with per-use re-consent where there is commercial gain.

**blocks other work** · effort: large

**Gap.** All three limbs of the obligation are missing; only the negative prohibition is enforced, and only on an event no user can produce.

1. **Separately obtained** — absent. There is no training-consent path to separate *from*: `CONSENT_PURPOSES` holds one value, and `commercial-training` is refused outright. Nor is there a product-improvement consent *flow* — only a schema check on an event a human would have to hand-write into the JSONL. Neither purpose can be granted through any product surface, so nothing is "obtained" at all.
2. **Visibly separate in the UI** — absent. No consent UI of any kind: no CLI subcommand (surface pinned at `tests/test_v0_invariants.py:1011`), nothing in `dashboard.

**Evidence.** [measured] The only implementation is schema validation on a hand-written event. `src/consilient/events.py:77-80` defines `CONSENT_GRANTED`/`CONSENT_WITHDRAWN`/`CONSENT_KINDS` and pins `CONSENT_PURPOSES = frozenset({"improve-consilient"})`. `_check_consent_contract` (`events.py:486-513`) refuses any

### R24 — PARTIAL

> [ATTRIBUTION WITHDRAWN] ADR-0024 requires no telemetry by default, so a central "model registry" that phones home is out. Design it local-first.

**Obligation.** Model discovery and capability probing run locally on demand with no default telemetry and no phone-home registry.

**blocks other work** · effort: large

**Gap.** Two of the three clauses fail.

1. "Model discovery … runs locally on demand" — there is no discovery call at all. `harness.py:177-201` is a hand-transcribed snapshot of one `cursor-agent --list-models` run; it goes stale silently and nothing detects that. Needed: a local on-demand enumeration (the same `_run_probe` subprocess pattern already in dispatch.py) replacing or refreshing the literal, plus a test that fails when the registry and the machine disagree.

2. "capability probing" — ADR-0025's Δ̂/φ̂ paired probe exists only as a seeded Monte Carlo simulation in the research tree, imported by nothing. Nothing in the run path estimates a candidate model's capability gap, so ADR-0054's `str

**Evidence.** PRIVACY CLAUSE MET AND ENFORCED. [measured] `tests/test_budget.py:807` `test_product_tree_has_no_outbound_or_credential_capability` AST-walks every `src/consilient/**/*.py` against `FORBIDDEN_IMPORT_ROOTS` (test_budget.py:20-38: `http`, `httpx`, `requests`, `socket`, `urllib`, `urllib3`, `openrouter

### R25 — PARTIAL

> these two aforementioned local repos can be used as inspiration but are STRICTLY PRIVATE and must not be published as part of this repo

**Obligation.** Nothing from ../hireable-3.0 or ../jobboard-v2 may appear in the public repository, and this must be encoded as a persistent memory and rule, not just observed.

effort: small

**Gap.** Two gaps, both in enforcement rather than in fact. (1) CONTENT-EXCERPT CLASS IS UNGUARDED. Both gates match only file PATHS and 40-hex SHAs; neither ever reads a corpus file's contents — check_private_corpus.py:138-156 builds needles purely from corpus_paths(). The script's own docstring lines 11-13 records that "a verbatim quotation from a private assessment document" was part of the original initial-commit leak, found by a paid cross-family audit rather than by any gate. So the exact class that has already leaked here has a documented rule and no check — the thirteen-catalogued-cases pattern, one sub-class deep. My scan above shows the tree is clean today, so this is an undetected-regressi

**Evidence.** ENFORCED [measured]: .github/scripts/check_private_corpus.py ran clean — EXIT=0, "checking against 2854 distinctive paths from 2 corpora". Soundness repair is genuine: GIT_ENV scrub at line 92; ls_files() lines 95-131 raises BindingError unless `git rev-parse --show-toplevel` resolves to the same di


## Routing

### R15 — PARTIAL

> The harness delegates to whatever agent the user favours — Claude Code with their own Anthropic credentials, Codex, Antigravity, or any other — OR executes natively against open models via OpenRouter or locally.

**Obligation.** Two execution paths must both exist: delegation to the user's chosen agent under their own credentials, and native execution against open models via OpenRouter or locally.

**blocks other work** · effort: large

**Gap.** The entire native execution path is missing. Concretely, none of the following exists anywhere in src/ or scripts/: (1) an HTTP transport to https://openrouter.ai/api/v1/chat/completions or to a local endpoint (Ollama at localhost:11434, llama.cpp, vLLM); (2) an OpenRouter provider adapter or a local provider adapter, plus the model catalogue read that would let one be selected; (3) credential acquisition and injection for OPENROUTER_API_KEY -- the friction log (docs/00-context/friction-log.md:114) already calls for a broker holding it, and today src/ may not even read os.environ (FORBIDDEN_CALLS at tests/test_budget.py:39-49 blocks os.getenv/os.environ.get); (4) a native agent loop -- tool-

**Evidence.** PATH A (delegation) MET: src/consilient/harness.py:103-113 registers claude/cursor-composer/grok/codex; scripts/dispatch.py:443-541 builds real argv per harness (claude -p, codex exec -C, grok -p --cwd, cursor-agent -p --model); dispatch.py:328-372 executes it. Own-credential delegation is ENFORCED,

### R17 — ABSENT

> A model registry needs a reasoning-capability field, and the harness must never double-apply.

**Obligation.** The model registry carries a reasoning-capability field and the harness is prohibited from applying scaffolding to a model that already reasons natively.

effort: medium

**Gap.** Both halves are missing. (1) `ModelOption` needs a reasoning-capability field, and it must be a tri-state plus unknown — `reasoning-layer.md:23-35` records that `supports_reasoning` booleans from models.dev/LiteLLM mean "accepts reasoning", not "reasoning-trained", and only OpenRouter's `mandatory` flag or models.dev's `reasoning_options` recover native/hybrid/absent. (2) A hard problem the design doc does not anticipate: the 22 registered ids are Cursor-namespaced (`composer-2.5`, `cursor-grok-4.6-xhigh`, `kimi-k3-max`, `glm-5.2-high`) and will not key into models.dev or LiteLLM without a mapping; several already encode effort in the id suffix (xhigh/high/medium/low) with nothing reading it

**Evidence.** [measured] The registry exists but carries no reasoning field. `src/consilient/harness.py:156-163` — `@dataclass(frozen=True) class ModelOption` has exactly four fields: `id`, `harness_id`, `family`, `pool`. All 22 entries of `MODELS` (`src/consilient/harness.py:181-203`) are four-positional-argumen

### R26 — PARTIAL

> I now have £200 max plans on Claude, Codex and Cursor. As well as local free via Ollama, and models from OpenRouter. I want to plug these in now, so I can continue developing the harness itself with them. It should transfer seamlessly. Set it up.

**Obligation.** All five backends (Claude, Codex, Cursor Max plans; Ollama local; OpenRouter) are wired in as usable execution targets, and work transfers between them without rework.

**blocks other work** · effort: medium

**Gap.** Two of the five named backends are not execution targets. (1) Ollama has zero presence in src/, scripts/ or tests/ — it cannot be selected, probed, or dispatched; the proven invocation (`codex exec --oss --local-provider ollama -m <model>`) exists only in an experiment adapter driven by a hardcoded synthetic ticket. (2) OpenRouter is a budget-refusal object and a spend reader, never a run target; scripts/dispatch.py has no branch that can invoke it. Closing it needs more than two build_command branches: PoolState (harness.py:65) models only known-percent / unknown headroom, and select_model refuses unknown headroom, so a local £0 backend needs a third "unmetered, no quota" pool state rather

**Evidence.** [measured] Wired: src/consilient/harness.py:103 HARNESSES registers claude, cursor-composer, grok, codex; scripts/dispatch.py:443 build_command has branches for exactly those four and returns "no invocation for harness {id}" at :543 otherwise; probe_all at :272 probes the same four. Real outcomes in


## Skills

### R08 — PARTIAL

> Mirror .agents/skills/ → .claude/skills/ (symlink if Windows developer mode is on, otherwise copy + a CI drift check)

**Obligation.** .agents/skills is the single source of truth and .claude/skills mirrors it, with a CI check that fails on drift.

**blocks other work** · effort: small

**Gap.** Three distinct gaps. (1) The mirror does not exist right now: .claude/skills is a plain 17-byte file in HEAD, on main, and on disk, so it resolves to nothing and Claude Code loads no project skill — the requirement's whole operational point fails, and the repo's own docs still describe the pre-c725874 state. (2) The "otherwise copy" half of the instruction was never built: there is no copy path, no bootstrap/repair script, and no content-equality drift check — skills-mirror.yml only compares the symlink target string, so a byte-identical copy (the sanctioned Windows fallback) would be rejected by CI rather than validated. Closing (1) by restoring the symlink leaves every non-developer-mode W

**Evidence.** SOURCE OF TRUTH EXISTS [measured]: .agents/skills/ holds 8 skills + README.md (find .agents/skills -maxdepth 2). CI CHECK EXISTS AND CAN FAIL [measured]: .github/workflows/skills-mirror.yml:23-28 asserts `test -L .claude/skills`, `test -f .claude/skills/README.md`, `readlink` == ../.agents/skills, a


## Tools

### R13 — PARTIAL

> Before designing anything, search properly and report what exists. "Someone already built this, MIT-licensed" has been the right answer four times on this project (model library, harness, harness optimisation, skill distribution). Assume it is five.

**Obligation.** The capability/tool layer is curated from existing licensed open-source components, with a documented prior-art search and licence per component, before anything is built.

**blocks other work** · **he asked more than once** · effort: small

**Gap.** The search-and-licence record exists as prose; nothing makes it binding, and no curated component is actually supplied.

Missing, precisely:
1. A machine-readable component record. `capability-layer.md:37-45` is a markdown table only — no field a test can read. Needs name, source URL, SPDX licence, verification date per component, covering non-Python components (MCP servers, shelled-out binaries), which the two existing stdlib tests cannot see at all.
2. The check ADR-0065:135-136 owes itself: an entry with a missing licence, or one on a denylist (BUSL, SSPL, AGPL, proprietary/source-available), fails CI. Also owed is the sibling tier-1 third-party-import ban at :131-134, likewise "Not yet w

**Evidence.** DOCUMENTATION HALF — MET, and unusually well. [measured] `docs/20-design/capability-layer.md:37-45` is a per-component supply table with a dated licence column ("Licence (verified 19 Aug 2026)"): Playwright MCP Apache-2.0 (:39), MCP reference servers `src/fetch`/`src/filesystem`/`src/git`, Brave/Exa

### R16 — ABSENT

> The harness should supply a reasoning layer natively WHEN THE MODEL LACKS ONE — so that capability is a property of the harness, not of the model.

**Obligation.** Reasoning scaffolding is supplied by the harness to models lacking native reasoning, so capability is a harness property. Same principle already stated for tools, skills and MCPs.

**he asked more than once** · effort: large

**Gap.** Everything except the design write-up and the β* algebra. Specifically missing, in dependency order:

(a) A reasoning-capability tri-state on the model registry. `ModelOption` (`src/consilient/harness.py:165-171`) needs a fourth-plus field distinguishing native-and-mandatory / hybrid-toggleable / absent. The design says adopt, don't build (`reasoning-layer.md:26-32`): models.dev is MIT and redistributable; nothing ingests it today. Note the semantics trap the design already names — `supports_reasoning` means "accepts reasoning params", not "reasoning-trained"; only `reasoning_options`/`mandatory` recovers the tri-state.

(b) The double-application refusal (design condition I1). Nothing anywh

**Evidence.** BRIEF CORRECTION FIRST: the brief's example is half-stale. `scripts/dispatch.py:73` imports `from consilient.recall import pack as pack_recall` and `scripts/dispatch.py:414` calls it inside `write_brief`, whose docstring records the change ("Until 21 August 2026 this function wrote the task alone").

### R35 — ABSENT

> I also want the harness to handle error tracking and self correction natively. We can use Sentry plugin optionally including locally here because it's already connected but we need a native version or an adopted open source version for error tracking.

**Obligation.** Error tracking and self-correction are native harness capabilities backed by an adopted open-source implementation; Sentry is an optional plugin, never the dependency.

effort: medium

**Gap.** Everything is missing: (a) no adopted open-source collector wired in — no dependency, no config, no emit path; (b) no optional Sentry plugin surface, so "Sentry optional, never the dependency" is untestable because neither side exists; (c) no error record store with a stable error identity; (d) no ratchet link — no field recording the enforcement that now prevents an error or an explicit `no_check_yet`; (e) no CI check failing on recurrence of an error marked prevented, which ADR-0036 line 163 names as the one native piece; (f) no self-correction path at all — `scripts/dispatch.py:1058-1059` deliberately refuses retry ("a silent or failed run is NOT retried on another pool"), and `docs/20-de

**Evidence.** [measured] `grep -rniI "sentry\|glitchtip\|opentelemetry\|sentry_sdk" src scripts tests .githooks .github packages pyproject.toml` → one hit, `.github/scripts/check_foreign_identifiers.py:97`, a SHA allowlist entry for a cited GitHub URL, not an integration. `grep -rniI "no_check_yet\|prevented_by\|

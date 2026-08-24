# Codebase audit — 24 August 2026

Eleven parallel audit areas, 109 findings, 72 distinct after de-duplication, each put through an
independent refutation pass. 96 agents.

**The headline number: guard survival for `src/consilient` is 45.5%.** 87 of 191 guard functions
can have every `raise` deleted with the whole 1,327-test suite in exactly the state of its own
unmutated control. 175 of 619 refusal statements go unnoticed, across 17 of the 19 modules that
contain refusals. Wilson 95% CI [0.386, 0.526].

**And the gate built to measure that has never run.** It is the only step in `invariants.yml`
without `if: ${{ !cancelled() }}`, so it has not executed in CI since it landed.

**The suite went red at midnight with no code change.** Eleven tests wrote a log named by today's
date and read one named by the literal `2026-08-23`; the two agreed until they did not. Repaired
the same day by reading the directory rather than computing a date, which is also immune to a run
that straddles midnight.

`mypy --strict src/consilient` is green across 27 files. `ruff check .` — the command CI runs — is
red on a pristine `git archive HEAD` export with 18 errors, five inside the capability-locked core.

Thirteen units, A through M, no two claiming the same file. A runs first and alone.

---

# Audit report — consilience, 24 August 2026

**Scope:** eleven parallel audit areas against HEAD `37f1791`. 109 findings raised, 72 distinct after de-duplication, each put through an independent refutation pass. British English throughout; every claim tagged `[measured]`, `[cited]` or `[asserted]`.

---

## The headline

Guard survival for `src/consilient` is **45.5%** — 87 of 191 guard functions can have every `raise` deleted with the whole 1,327-test suite in exactly the state of its own unmutated control; 175 of 619 refusal statements (28.3%) go unnoticed, across 17 of the 19 modules that contain refusals (Wilson 95% CI [0.386, 0.526]) `[measured]`. Repairing one date-locked test file recovers four of those survivors, giving a corrected floor of **43.5%** `[measured]`; the true figure is at or above that, because deletion is the crudest defect a guard can suffer and flaky failures under parallel load were scored as kills. The suite that gates all of this is red today for a reason unrelated to any code change — eleven tests write a log named by today's date and read one named by the literal `2026-08-23` `[measured]` — and because the guard-mutation step is the only step in `invariants.yml` without `if: ${{ !cancelled() }}`, the one gate built to measure the first sentence **has never executed in CI since it landed** `[measured]`.

`mypy --strict src/consilient` is green, 27 files `[measured]`. `ruff check .` — the same command CI runs — is red on a pristine `git archive HEAD` export with 18 errors, five of them inside the capability-locked core `[measured]`.

---

## What we are doing about it

Thirty-four issues, thirteen units. No two units claim the same file. **A runs first and alone**; the rest are parallel.

| # | Unit | Deliverable | Done when | Files | Deps |
|---|---|---|---|---|---|
| **A** | CI honesty | `if: !cancelled()` on the guard step; a test asserting *every* named step carries it; date-derived log paths in `test_organisation_plan.py` (lines 151, 162, 397, 405 — four sites, not one) plus a scan banning date-literal log paths; 18 ruff errors cleared; `.harness` excluded; `RUF100` on; `strict = True` in `mypy.ini` | `ruff check .` exits 0 on a clean export; `pytest tests -q` exits 0; the step-condition test fails when the `if:` is removed | `invariants.yml`, `test_guard_mutation.py`, `test_organisation_plan.py`, `pyproject.toml`, `mypy.ini`, 3 F401 test files; delete untracked `src/mine.py`,`src/x.py` | — |
| **B** | Log durability | Refuse an append when the file does not end in `\n`, naming the torn offset (fail closed); `read_all` skips non-files; PermissionError text states what was observed, not an unverified cause; `killed` added to `Status`/`parse_status`/`classify_gap` **and** an append-time vocabulary check | A torn tail is refused, not silently glued; the four historical `killed` events still replay | `events.py`, `harness.py` | A |
| **C** | Projection & readouts | `.stale-*` copy only on genuine digest disagreement; build into a sibling temp file + `os.replace` (reuse `records._install_object`); duplicate `record_id` → `_quarantine_relational`, not `IntegrityError`; version key in `projection_meta` with a third replay state; test asserting every `*_KIND` ∈ handlers ∪ `NOT_PROJECTED`; rejection **reasons** surfaced in `cmd_beta` and the dashboard; delete `relational_quarantine_count`; `try/finally` on `cmd_beta`'s connection | Appending any declared kind twice leaves `build` succeeding with the quarantine count up; a one-event lag produces zero `.stale-*` files | `projection.py`, `cli.py`, `dashboard.py` + tests | A |
| **D** | Work items | Recompute `source_turn_digest` in `validate_transition` (**not** `_check_commitment_contract` — that function never receives the turn texts); replace the `"sha256" in text and redactions` guard with `DIGEST_RE` and drop the conjunction; rename or repair the tautological redaction test; validate `retrieval_date` and constrain `evidence_tag` in `_check_incumbent` | Reordered ids, a forged digest, and a digest over invented text are each refused on the `principal_required` path; `{name:"x", … evidence_tag:"vibes"}` is refused | `work_items.py`, `test_conversation.py`, `test_work_items.py` | A |
| **E** | Effects | `_intent` calls `_observation_predicate`; delete the three unreachable `_disposition_for` arms; delete `PLANNING_OPERATIONS`; remove `data.read`/`network.call` from `MUTATION_EFFECTS` with a disjointness test; make the ADR-0078 comment state the truth and pin `derive_admission` as unwired | An observation intent with a mutating operation is refused; `MUTATION_EFFECTS & READ_ONLY_EFFECTS == frozenset()` | `effects.py`, `test_effect_contract.py`, `test_effect_admission.py` | A |
| **F** | Capabilities | `select_capabilities` refuses an entry whose gate state is not `admitted` and whose `expires_at` has passed; thread the per-row `label` into `parse_inventory_entry` | A gated inventory entry is refused; a malformed row names its index | `capabilities.py`, `test_capabilities.py` | A |
| **G** | Verification | Delete the two literal redefinitions shadowing the imports from `events` | `ruff check src/consilient/verification.py` reports zero F811 | `verification.py` | A |
| **H** | Promote & sandbox | Lift `capability_violations` out of `test_budget.py` into `src/consilient/`; a fixed containment probe run through the same `execute` callable before scoring, returning `candidate_unexecutable` on socket or out-of-scratch write; flip `no_conflicting_candidate` to `False`; parametrised refusal table for `_check_promote_contract`, registered | The measured escape (socket bound, file written outside scratch) returns `candidate_unexecutable`; the ten `_check_promote_contract` raises die under mutation | `promote.py`, new `_scan.py`, `test_budget.py`, `test_promote_*.py`, `check_guard_mutation.py` | A |
| **I** | Orchestrator | Track `build_driver.py`/`plan-units.json`, ignore `driver-state.json`; per-attempt artefact paths, handles closed; parse the SOUND/DEFECTIVE verdict into `verified`; atomic state write + `load()` distinguishing absent from corrupt; timeout on `suite_green`; compute `green` before the merge loop; baseline interpolated from the last green summary; `--require-corpora`; release claims on the silence path; delete `ORDER`, `last_published_count`, `skipped` | A DEFECTIVE verdict keeps its unit out of `verified`; a truncated state file halts rather than restarts; no cherry-pick lands on a red tree | `.harness/build_driver.py`, `.gitignore` | A |
| **J** | Dispatch scripts | `try/finally` from `open_claim` to `close_claim` in both `dispatch_one` and `dispatch_fanout` (the fanout parent is worse: children release under different run ids); stop after N consecutive empty ticks | An exception in `run_harness` leaves no live claim | `scripts/dispatch.py`, `scripts/run_loop.py` | A |
| **K** | Gate scripts | `mypy --strict .github/scripts` clean and wired as a CI step; correct the `attr-defined`/`union-attr` mis-code in `check_component_licences.py`; delete the shadowed `GIT_ENV`; new `check_private_repo_names.py` with a three-entry allowlist and a shrink-only pin list; correct `check_private_corpus.py`'s superseded docstring | `check_private_repo_names.py --self-test` passes and the pin list only shrinks | `.github/scripts/*`, `.githooks/pre-push` | A (step added to A's file after K is green) |
| **L** | Doc truth | Correct R05 in `requirements-source.json` and regenerate; generate ADR/experiment/step counts into README and CLAUDE.md via the manifest; restate the superlative check honestly in AGENTS.md | `check_generated_documents.py --check` covers the counts; CLAUDE.md's "45 ADRs" is gone | `requirements-source.json`, `README.md`, `CLAUDE.md`, `AGENTS.md`, new `scripts/build_counts.py` | A |
| **M** | β seam | One test enumerating every `via` the writer accepts, driven through `append` → `build` → `beta`, asserting at least one row is admitted | Lands **red** — it is the record of the defect | new `tests/test_beta_seam.py` | A |

---

## What we are deferring, and what unblocks it

Twenty-one genuine findings, each with the specific release condition.

**Joe's approval** (`docs/10-research/` is "Ask first"): the five-way EXP-58 heading collision `[measured]`; the duplicated `test_exp43.py` block whose surviving copy references an undefined `LOCK` `[measured]`; wiring the 23 experiment suites into CI; wiring `check_record_numbers.py`, which follows the EXP-58 repair or it lands red in both modes `[measured]`. P1-proxy's per-repo metrics need re-anchoring on the `itsdangerous` corpus before that paper ships.

**Unit A**: growing the guard registry beyond three entries, the survival ratchet, `validate_transition`'s entry, and a second operator for the 13 return-shaped refusals that the deletion operator structurally cannot reach — including all of `budget.py`, the module that governs spend `[measured]`. All worthless while the step is skipped.

**A quiet window on `events.py`** (442 unordered unit pairs claim it `[measured]`): the day-seam consistency boundary — validators see one daily file while `read_all` spans the directory, measured live as a revision-uniqueness fence evaporating at midnight and one production completion already crossing it `[measured]`; the shape-validator registry; sharing `STREAM_CAP`/`SELECTOR` between producer and validator; the remaining seven duplicated kind strings.

**The day-seam fix**: moving claim-overlap detection inside the F02 transaction — its prefix is one day, so it would be wrong today.

**An ADR**: bounding the duplicate-id check to make the reader's fixed 2.52 s budget survive a growing lock hold (measured headroom 3.4×, halved by a wasted final sleep `[measured]`).

**One decision each**: does the budget ceiling bind? (kernel-backed lock, reservation expiry, wiring into dispatch); is `seal_turn` meant to scrub?; what is `state_digest` for? (splitting object integrity out of V0-02). **U3's signature verifier** unblocks β's `via` vocabulary. **Reading the S02 spec** decides whether `NO_FRESH_INSTRUMENT`/`HIDDEN_FIELD_ACCESS` are dead constants or missing checks.

---

## What we are rejecting, and why

Seventeen. **Module splits** (`events.py` 3,391 lines, `harness.py` 1,779), `record_temporal_views`, `cli.render`, `_text` triplication, the activation dataclass, `dispatch.py`'s union returns, widening mypy to `scripts/` — refactors whose only named cost is complexity, in files fifteen agents are editing; the reviewer's own note that "nothing behaves incorrectly, no test fails" is decisive. **Promoting `qa_battery.py`/`release_check.py`** — testing instruments nothing runs. **A pre-commit ruff hook** — refuses commits mid-task, and `core.hooksPath` is opt-in, so it is a no-op for an unmeasured share of the fleet. **Entropy secret detection** — false positives across a log full of digests, on a single-user machine that already blocks `.env`. **MAX_PATH relocation** and the directory-fsync `ctypes` call — hazards with no current consumer. **Claim fencing tokens** — `[cited]`, and N03 is in flight. **Branch-hit metrics** and two display-only surfacings (`skills_omitted`, memory views) — numbers nobody has to answer for. **Ruff `S`/`TID` families** — not onto a red tree.

---

## Findings that were killed

Eleven of 72 did not survive refutation `[measured]`. The pattern in the misses is instructive.

Three auditors reported the S02 sandbox escape as live. It was repaired the same night at the layer the original review prescribed — commit `ae74e59` runs the candidate in its own process, and the frame-walking payload now scores 0.0 with a negative control at `test_promote_instrument.py:146`. Two of the three had read the 23 August brief and assumed it still described the code; one was working from a stale `.harness` copy. The residual — the isolated child can still write outside the scratch directory — is real, and is why unit H ships a probe rather than another scanner.

`live_dispatchers()` returning 0 was reported as fail-open; enumerating all 29 live `python.exe` showed none was a dispatcher, so 0 was correct. The 263 dispatch outcomes "reported by no surface" are surfaced — via `capability.gap`, on the line immediately after the range the auditor cited as proof of absence. The 81.6% ADR enforcement rate scores nine ADRs as defective which each state, in bold, that their check does not exist yet; `_template.md` has a field for exactly that disclosure. `check_record_numbers.py` is invoked by five agent-facing surfaces the four-directory census did not scan. The cross-file duplicate `event_id` needs a caller that both reuses a mutated dict and recomputes the path from a second clock reading; every caller is one shape or the other.

Two findings survived on symptom and were refuted on diagnosis — the date-locked suite is a four-line typo, not a missing `log_path()` helper plus clock injection (which would require weakening `_check_clock`, a guard added four days ago after a measured integrity failure). Both corrections are carried into unit A.

---

## The pattern

Machinery wired to nothing is not an occasional slip. Measured across the tree: 51 top-level names in `src/consilient` with zero references outside their defining file, 27 in `scripts/`, 48 in `.github/scripts` `[measured]`; 33 public definitions with no production caller `[measured]`; 11 of 1,079 test functions with no assertion at all `[measured]`; three of 193 guard functions registered for mutation `[measured]`. The full admission subsystem in `effects.py` executes only from its own test file — verified at zero coverage with that file ignored `[measured]`. `verification.py`'s queue vocabulary was dead in the commit that created it `[measured]`.

The single mechanism that closes the class is a **caller census as a CI test**: every public definition in `src/consilient` must have a non-test caller, and every `.github/scripts/check_*.py` must be named by a workflow, a hook, a test or `release_check.py`, with a dated shrink-only pin list for today's exceptions. The project's own plan already carries the second half as an open item `[cited]`. It is roughly thirty lines of stdlib `ast`, it is cheap because the capability lock forbids `getattr` in the product core so a grep miss is close to a proof, and it converts "someone will notice" into a build failure at the moment the orphan is written. That is the working principle the repository states and, in four separate places, does not enforce on itself.

---

## What could not be audited

Two of eleven areas did not run `pytest tests` at all — fifteen agents were live and a second full run would have contended for `.harness/state.db`. **No auditor observed a GitHub Actions run**; every CI claim is a reading of `invariants.yml` plus local execution of the same command, and it remains possible these gates have simply not fired, since all four workflows trigger only on `pull_request` and `push: main` while the branch is `worktree-consilience-cto`. Branch protection is a repository setting no file reveals.

Everything was measured on Windows; CI is `ubuntu-latest`, and one cross-platform assertion (`test_dispatch.py:626`) evaluates False under Linux path separators `[measured]`. `check_private_corpus.py --history` and `check_secrets.py --history` were deliberately not run by most auditors — they read two private commercial repositories. Roughly 7,700 lines — 43% of the product core: `dashboard.py`, `harness.py`, `recall.py`, `instructions.py`, `promote.py`, `usage.py` — had no line-by-line reading, and `src/consilient_connectors/` was not opened. The 1,506 `mypy --strict` errors in `tests/` are counted, not triaged. `docs/20-design/`, the 116 experiment-register entries and the `.agents/` skill definitions are essentially unaudited; the ADR corpus was checked for artefact existence, never for whether a named test asserts what its ADR claims.

One methodological near-miss, recorded because it is the same failure the project studies: an auditor ran forty minutes of mutation census producing entirely plausible numbers before noticing the worker trees belonged to a concurrent agent — the shared scratchpad is not session-isolated. Sixteen further runs exited `3221225794` having never started pytest, and the first aggregation counted every one as a kill. Both would have been invisible in the summary statistic.

*≈2,650 words.*

---

## Triage

## First, if only one

**Add `if: ${{ !cancelled() }}` to `.github/workflows/invariants.yml:49`.** One line. The guard-mutation gate — the only check built to answer the systemic finding — is skipped on exactly the pushes where something is already broken, and something is broken now. Every other repair is invisible while the gate that would notice it cannot run. The date fix and the ruff clear are its neighbours in the same commit, but the `if:` is the one that removes a *class* (a masked gate, forever) rather than today's instance.

## Triage

109 findings collapse to **72 distinct issues**: **34 TAKE / 21 DEFER / 17 REJECT**. Duplicate count in brackets.

### TAKE (34)

| # | Issue | Reason |
|---|---|---|
| T1 | `!cancelled()` on guard step + assert every step carries it [×5] | One line restores the highest-leverage gate permanently. |
| T2 | Date-locked `test_organisation_plan.py` + no-date-literal check [×7] | Suite red for fifteen agents; the check stops the next one. |
| T3 | Clear 18 ruff errors, `.harness` exclude, `RUF100`, `mypy.ini strict=True`, delete `src/mine.py`/`x.py` [×6] | A gate that cannot pass is a gate nobody reads. |
| T4 | Torn-tail append refusal | Acknowledged-but-absent events; the one thing F01 exists to prevent. |
| T5 | `read_all` skips non-files; honest PermissionError text | Two lines; stops a confident wrong diagnosis. |
| T6 | `killed` in the status vocabulary + append-time check | Live log holds a value the type says is impossible. |
| T7 | Stop `.stale-*` copies on lag | 11 MB/hour unattended, accelerating. |
| T8 | `projection.build` → temp + `os.replace` | Reuses `records._install_object`; kills a false DIVERGED and a false unhealthy. |
| T9 | Duplicate `record_id` → quarantine, plus double-append property test | One accepted append permanently kills replay. |
| T10 | Projection version stamp in `projection_meta` | Stops a legitimate change reading as corruption at Gate A2. |
| T11 | Assert every `*_KIND` is in handlers ∪ `NOT_PROJECTED` | Test only, no restructure; makes "forgotten" fail loudly. |
| T12 | Surface rejection reasons; delete `relational_quarantine_count` | Three forged principal approvals pooled into a bare integer. |
| T13 | `try/finally` on `cmd_beta`'s connection | Two lines, matches `cmd_replay`. |
| T14 | Recompute `source_turn_digest` [×4] | Correct pattern is six lines below; clears the F841 in the same edit. |
| T15 | Match `DIGEST_RE`, drop the `and redactions` conjunction | Guard is neither necessary nor sufficient and disables by omission. |
| T16 | Make the redaction test honest (rename + refusal table) | Test named for a guarantee the code does not make. |
| T17 | Validate `retrieval_date`, `evidence_tag` in `_check_incumbent` | Principle 9 currently enforces spelling. |
| T18 | `_intent` calls `_observation_predicate` | Route to a decision-free record of a mutating operation. |
| T19 | Delete the three unreachable `_disposition_for` arms | Coverage proves they never run; they read as guards. |
| T20 | Delete `PLANNING_OPERATIONS`, fix `MUTATION_EFFECTS` overlap, add set-disjoint test [×3] | Named twice already and still there. |
| T21 | Make the ADR-0078 comment honest + pin `derive_admission` unwired | The comment asserts wiring that does not exist. |
| T22 | Delete `verification.py:34-35` [×3] | Second source of truth for the event vocabulary. |
| T23 | Thread the inventory label | Uses the dead variable the code was reaching for. |
| T24 | `select_capabilities` refuses non-`admitted` gates | Gate parsed in full, decision made on `available` alone. |
| T25 | Real scanner + containment probe for the sealed instrument | Measured escape: socket, out-of-scratch write, `_getframe`. |
| T26 | Six evasion probes as negative controls in `test_budget.py` | The lock is defeated by an assignment; controls make that falsifiable. |
| T27 | Flip `no_conflicting_candidate` default to `False` | One word, fail-closed, tests-only callers. |
| T28 | Refusal table for `_check_promote_contract` + registry entry | Largest survivor: n≥30 floor and un-weakenable clause both deletable. |
| T29 | build_driver: per-attempt artefacts, verdict parsing, tracked file, atomic state, `suite_green` timeout, green-before-merge, computed baseline, `--require-corpora`, release on silence, delete `ORDER` [×9] | The scheduler's judgements are all downstream of one reused file. |
| T30 | `try/finally` round the claim; stop after N empty ticks | Three lines against a one-hour orphan. |
| T31 | `mypy --strict .github/scripts`; fix the mis-coded ignore; delete the shadowing `GIT_ENV` | Suppression asserting an audit that never happened, in the licence gate. |
| T32 | `check_private_repo_names.py` + allowlist + shrink-only pin list | Boundary settled in prose, unenforced in code, 66 files breaching. |
| T33 | Correct R05; generate the ADR/experiment counts; correct AGENTS.md's superlative claim [×3] | A generated, CI-checked doc states as measured that a shipped gate does not exist. |
| T34 | Cross-seam test: every accepted `via` → append → build → beta | Lands red; it is the record of the β defect. |

### DEFER (21)

All `docs/10-research/` work — exp43 duplicates, EXP-58, wiring the 23 experiment suites, RUF100 there — **unblocked by Joe's approval** (AGENTS.md "Ask first"); `check_record_numbers` wiring follows EXP-58. Registry growth, the census ratchet, `validate_transition`'s entry and the return-shaped operator: **unblocked by T1** — worthless while the step is skipped. Day-seam consistency boundary, the shape-validator registry, the `events`↔`verification` constant sharing and the remaining duplicate kind constants: **unblocked by a quiet window on `events.py`** (442 unordered pairs claim it). Claim-overlap validation inside the transaction: **unblocked by the day-seam fix** — its prefix is one day. Reader-retry deadline: **needs an ADR** on bounding the duplicate check. All budget work — kernel lock, reservation expiry, wiring into dispatch: **one decision, does the ceiling bind?** β's vocabulary repair: **needs the signature-verification call (U3)**. V0-02 digest split and `seal_turn` scrubbing: **need a decision on what each is for**. `promote.py`'s two dead refusal reasons: **read the S02 spec first** — this may be a missing check. Clean-install CI job, `worktree-*` trigger, widening `PUBLIC_PROSE`, P1-proxy's metrics re-anchoring, the shared `_gate.run` helper: all genuine, all collide or wait on a call.

### REJECT (17)

Module splits (`events.py`, `harness.py`), `record_temporal_views`, `cli.render`, `_text` triplication, the activation dataclass, `dispatch.py`'s union returns and widening mypy to `scripts/` — refactors with complexity as their only named cost, in files fifteen agents are editing. QA-battery and `release_check` promotion — testing instruments nothing runs. Pre-commit ruff hook — refuses commits mid-task and the hook is opt-in, so it is a no-op for an unknown share of the fleet. Entropy secret detection — false positives on a log full of digests, on a single-user machine that already blocks `.env`. MAX_PATH relocation and the directory-fsync `ctypes` — hazards with no current consumer. Claim fencing tokens — [cited], and N03 is in flight. Branch-hit metric and the two display-only surfacings (`skills_omitted`, memory views) — numbers nobody has to answer for. Ruff `S`/`TID` families — not onto a red tree.

## Build units (disjoint file sets)

| Unit | Files | Carries |
|---|---|---|
| **A. CI honesty** | `invariants.yml`, `tests/test_guard_mutation.py`, `tests/test_organisation_plan.py`, `pyproject.toml`, `mypy.ini`, 3 F401 test files, delete `src/mine.py`,`src/x.py` | T1 T2 T3 |
| **B. Log durability** | `events.py`, `harness.py` | T4 T5 T6 |
| **C. Projection & readouts** | `projection.py`, `cli.py`, their tests | T7–T13 |
| **D. Work items** | `work_items.py`, `test_conversation.py`, `test_work_items.py` | T14–T17 |
| **E. Effects** | `effects.py`, `test_effect_contract.py`, `test_effect_admission.py` | T18–T21 |
| **F. Capabilities** | `capabilities.py`, `test_capabilities.py` | T23 T24 |
| **G. Verification** | `verification.py` | T22 |
| **H. Promote & sandbox** | `promote.py`, new `_scan.py`, `test_budget.py`, `test_promote_*.py`, `check_guard_mutation.py` | T25–T28 |
| **I. Orchestrator** | `.harness/build_driver.py`, `.gitignore` | T29 |
| **J. Dispatch scripts** | `scripts/dispatch.py`, `scripts/run_loop.py` | T30 |
| **K. Gate scripts** | `.github/scripts/*` (not check_guard_mutation), `.githooks/pre-push` | T31 T32 |
| **L. Doc truth** | `requirements-source.json`, `README.md`, `CLAUDE.md`, `AGENTS.md`, new `scripts/build_counts.py` | T33 |
| **M. β seam** | new `tests/test_beta_seam.py` | T34 |

Sequencing: **A first and alone** — everything else is unmeasurable until the suite and the gate are honest. K's new mypy step lands in A's file *after* K is green; H's registry entries land after A. B, C, D, E, F, G, H, I, J, L, M then run in parallel; none shares a file.

Two things I am not doing that the findings ask for, deliberately: I am not growing the guard registry now (worthless behind a skipped step), and I am not splitting `events.py` (a diff that conflicts with everything, to fix a cost nobody has paid yet).

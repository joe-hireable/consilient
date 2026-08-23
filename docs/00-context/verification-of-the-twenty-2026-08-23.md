# Cross-family verification of the first twenty units, 23 August 2026

The first adversarial review this project has ever completed. Twenty units had reached `done`
with `verified: 0` -- every review had been dispatched and every one had crashed, leaving no gap
anyone could see. 106 agents: one verifier per unit, then a refuter per finding whose job was to
kill it.

**0 of 19 units sound. 5 blocking defects. 85 findings raised, 68 survived refutation, 17 killed.**
A 20% kill rate is the evidence the refutation stage did real work rather than rubber-stamping.
(A01's verifier was blocked by a safety classifier and did not report.)

**The systemic finding, and the one that matters most: 14 of 19 units have at least one guard that
can be deleted with the unit's own suite still green.** A test that cannot fail is worse than no
test, because it is counted as evidence.

This is also the closest thing to a direct measurement of beta the project has: the automated
checks accepted all nineteen, and independent cross-family review found defects in all nineteen.

---

# Verification report — 19 units, cross-family review

## The headline

**0 of 19 units are sound. 19 carry confirmed defects. 5 carry blocking ones.** [measured]

85 findings were raised; 68 survived a genuine refutation attempt, 17 were killed. Breakdown of survivors: **5 blocking, 31 serious, 32 minor** [measured]. Every unit that reached "done" carries at least one surviving finding — including F05, which the reviewer graded `sound` on its narrow criterion while a surviving minor finding shows its acceptance test skips silently off the principal's machine [measured].

No unit was verified end-to-end. Every reviewer declined to run the full suite (concurrent agents in a shared tree) or could not (`tests/test_task_projection.py` never existed) [measured].

## Confirmed defects

Ranked by severity, then by downstream dependents.

**1. A02 — two caller-supplied booleans disable every admission protection** [measured, blocking]
`AdmissionFacts(is_material_choice=True)` or `is_proof_operation=True` short-circuits protected-class escalation, containment and recovery-proof in `derive_admission` (`src/consilient/effects.py:406-410`; `_disposition_for` at 429-441 has no arm for either class, so both fall to `return "execute"`). Measured: `money.commit` with `authority_standing=False` returns `material_choice/execute/exact_grant` instead of `protected_uncovered/escalate`; uncontained `process.run` executes. No production caller yet — latent, not live. Fix: conjoin each flag with a manifest predicate (`PLANNING_OPERATIONS` at effects.py:64 is already declared and wired to nothing). A03/A04/P01 build on this.

**2. S02 — a candidate reads the entire sealed hidden instrument, in-process** [measured, blocking]
`find_forbidden_imports` is an AST scan for `Import`/`ImportFrom` only; `__import__("sys")._getframe()` passes it, and `promote_loop.py` `exec()`s the candidate in the same interpreter as `evaluate_sealed`. Reproduced end-to-end through the shipped CLI: the candidate exfiltrated all three held-out items, wrote a file outside `--scratch-dir`, and the run reported `qualification_accept: true`, exit 0 [measured]. `CandidateInstrumentView`'s guard is never on the execution path. This defeats the Goodhart check, not just confidentiality. Fix requires real process isolation, not another guard.

**3. S02 — mypy `--strict` is red at the commit; CI's first step fails** [measured, blocking]
Clean at parent, 6 errors at S02's commit, all `git blame`d to it (`promote.py:219,223,234`). `.github/workflows/invariants.yml:25` runs it before tests. Now 12 at HEAD — projection.py carries 6 of the same shape from other units [measured]. Fix: delete three unused `type: ignore`s; the pattern needs a gate, since three units repeated it.

**4. V01 — beta reports 0 human rejections over a log containing 35** [measured, blocking]
`_verdict_auth_status` admits only `via == "phone_webauthn"`, which `events._check_human_authority` refuses at append time (V0-28). So every real verdict is `declared_principal` and is dropped by `admits_human_beta_row` — and is *not* quarantined, so no count, locator or caveat appears in either output mode. The exclusion is specified; hiding it is not. Fix is one count and one rendered line. Note the pre-V01 behaviour was worse (β = 1.000 by construction); do not revert.

**5. L01 — generated ADR index fails its own `--check` on any clean checkout** [measured, blocking]
`build_decision_index.py:116` digests working-tree bytes under `.gitattributes * text=auto eol=lf`, so 31 CRLF files are baked into the committed header. A `git archive` of HEAD fails `--check` (rc 1) and the CI gate reports `adverse=2`, while the live worktree passes. `docs/40-spec/requirements.md` fails identically — the root cause is the shared `source_digest` helper, not one producer.

**Serious, worth naming (31 survived; the load-bearing ones):**
- **C01** — `source_turn_digest` is never recomputed on any path; a commitment can cite turns that never happened, or reorder them, and be accepted [measured]. The "no secret hash" guard is a substring search for the literal word `sha256`, admitting real digests and refusing innocent text [measured].
- **D01** — a `delivery.estimate` revision zero can carry any window, `sample_size` and `evidence_class`; only `analogue_ids` is compared against the honest derivation. A 2-second window labelled `[measured]` from a claimed 999 samples is accepted, sealed and projected [measured]. Separately, the claim-ordering gate keys on an optional `delivery_id` that `coordination.open_claim()` never sets, so it has zero live subjects [measured].
- **M02** — the entire relation-defect detection path can be deleted with 9/9 tests green, and the test named for that behaviour repairs the relation and asserts the defect is *absent* [measured]. `work_item`/`capability_contract` columns are structurally unfillable (M01's field set forbids them) and two asserts enshrine the NULLs [measured].
- **S02** — one-use seal does not exist at the entrypoint: three identical CLI runs all evaluated; the `reserve_qualification_batch` result is a dead store and the registry is process-local [measured]. Containment defaults to `contained=True` for a boundary ADR-0076 records as absent [measured].
- **F02** — the mutual-exclusion test for the unit's headline property cannot fail when the lock is deleted (`ctx.Event()` set before spawn children exist); a barrier probe shows 19/25 double admissions under the mutant [measured].
- **F01** — the Windows lock is mandatory: an ordinary concurrent writer makes `events.read()` fail closed after ~2.5s of backoff; reproduced with a plain writer, 2 hard failures in 5s at 2000 events [measured]. This matches the six dead dispatches recorded in the tree.

## Findings that were killed

17 of 85 (20%) were refuted [measured]. The refutation stage did real work.

Representative kills, with what the reviewer had misread:
- **L03** (serious): the marker-conditional pin was claimed to *launder* settled-ADR edits. Running it with shipped constants shows the opposite — pre-L03 code excused markers forever; L03 narrowed it to a closed historical window. The reviewer measured pins they had constructed themselves [measured].
- **V01** (blocking + serious): "10 tests still red" — the tree is green at HEAD (1218 passed); and the `n_rejected == 0` assertions the reviewer called a bug are the deliverable, because the fixtures use `via="cli"` [measured].
- **F04** (serious): "missing commit means the gap is silent" — `committed()` fails *closed* and the gap was recorded verbatim in `driver-state.json` [cited].
- **F03**, **F01**, **S01**, **S02**, **A02**, **O01**, **R01**: misread scope, redundant-but-harmless constants, equivalent mutants, and one case where the reviewer's own probe rebuilt the payload rather than retrying it.

## Tests that cannot fail

This is the largest single category, and it is systemic. **14 of 19 units have at least one guard that can be deleted with the unit's own suite green** [measured].

| Unit | What survives deletion |
|---|---|
| C01 | whole secret/redaction guard (24 pass); the assertion is a tautology |
| D01 | 18 non-degenerate rules, incl. "reforecast must widen" and the whole chain-integrity layer |
| E01 | status vocabulary — add `"rejected"` or drop `"not_run"`, all 1207 tests pass |
| F02 | the per-log lock in `_transaction` |
| F04 | every source citation in the pool registry |
| L02 | 7 of 14 checker guards, incl. four named by the plan |
| L03 | ordinal counter; the marker-pin conditional |
| M01 | atomic object install; digest format guard; canonical-metadata guard |
| M02 | all relation-defect branches; `state_digest`; `memory_record_rows` |
| O01 | six validations the Deliverable names, incl. estimate inputs and ownership |
| S01 | `contract_digest` (hash a constant); the whole 74-line `events.py` validator; the n≥30 floor |
| S02 | `frozen=True` on both result types; lineage anchors |
| V01 | quarantine path/line/digest fields (full suite green) |
| A02 | two guards survive all 50 tests (available=False, already-admitted widening) |

**S01 and M02 are the worst:** their headline properties ("accepts only an exact immutable contract", "malformed relation targets are visible defects") are each unprotected by a single assertion [measured].

## Claims that were exceeded

**No commit exceeded its plan-declared claims.** Every one of the 19 commits touched exactly the files its plan's "Claim exactly" block names [measured]. That check is clean.

Two adjacent problems:
- **`.harness/plan-units.json` is a sliding 10-bullet window over the plan, ignoring unit boundaries.** 46 of 78 units have exactly 10 claims; 16 match `flat[i:i+10]` at a fixed offset; entries contain literal duplicates [measured]. This *over*-declares (R01, E01, V01, L01, L03, S01, D01, F04) and, at L05, *under*-declares four real paths that appear in no unit's list at all. It reaches workers: it is spliced into each dispatch brief under "Claim exactly these and nothing else", handing builders a ~5× scope grant, and into the reviewer brief as the out-of-scope oracle [measured].
- **F04 has no commit of its own.** Its implementation is inside `1ee4a4e` (a rescue commit) and its test inside `ad5e034` (an omnibus). The declared subject exists in no ref [measured]. F01 also landed E01's `verification.outcome` validator a day early, inside its own claimed file, before E01's F03 dependency existed [measured].

## What could not be checked

- **The full suite, by anyone.** All 19 reviewers declined it or ran subsets; concurrent agents made attribution impossible [cited].
- **Two units' Done commands are unrunnable**: D01 and M02 name `tests/test_task_projection.py`, which has never existed in any ref [measured]. F01's and L02's Done commands were red *at their own commits* [measured].
- **POSIX behaviour of everything.** All measurement is Windows 11 / CPython 3.13. F01's directory-fsync path can only fire on POSIX and was simulated, not exercised [cited].
- **Real durability.** No test anywhere shows an acknowledged event surviving power loss; only that `fsync` is called [cited].
- **Governance preconditions.** A02 and O01 both shipped against ADR amendments still marked "principal acceptance required", with no acceptance record in the tree — findings rest on absence of a record, not proof of refusal [cited].
- **Two vendor facts:** F04's Cursor pool citation has no saved snapshot; F05's arm rides one machine's SuperGrok subscription [cited].
- **One scratchpad collision.** O01's reviewer had another agent overwrite their mutation script mid-run, briefly producing two false survivors [measured]. Assume other reviewers hit this and did not notice.

## What this says about the gate

Nineteen units cleared their Done commands and a green suite. **19/19 carry a surviving defect; 5/19 carry a blocking one.**

Treating "reached done" as an accept and "surviving blocking finding" as bad work:

- **β̂ (any defect) = 1.00, Wilson 95% [0.83, 1.00]** [measured]
- **β̂ (blocking) = 0.26, Wilson 95% [0.12, 0.49]** [measured]

What the suite catches: happy paths, and behaviours a unit's own author thought to break. What it does not catch: **mutation survival** (14/19 units have deletable guards), **type errors** (mypy is a separate step no test runs, red in 3 units), **cross-file state** (CRLF, working-tree vs blob), **anything outside the unit's own test file** (F04's regression, E01's containing file, V01's 10-test window), and **unrunnable acceptance commands**, which return exit 4 and are read as "not a failure".

The single highest-leverage change is not more review. It is making the gate include what the reviews used: **one mutation run per unit against its own suite**, plus `mypy --strict` and a clean-checkout `--check` in the same gate as pytest. Every blocking finding above would have been caught by one of those three.

Weaknesses of this estimate, stated plainly [asserted]: n = 19; one reviewer family, sharing a base model with each other and correlated in what they think to probe; the builders were a different family, which is the only thing keeping this from being self-assessment; and the 20% kill rate says the reviewers over-claim roughly one finding in five, so β̂ (any defect) = 1.00 is an upper reading of a real number that is high but not exactly 1.

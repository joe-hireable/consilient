# EXP-49 findings — the instruments that measure β are twice as weakly guarded as the code they measure

**Date:** 20 August 2026
**Status:** `[measured]` for every count, rate and interval below; `[algebra]` for the equivalence
sensitivity analysis; `[asserted]` for the interpretation and for the harness defect's fix.
**Verdict under the pre-registered stopping rules: `insufficient_evidence`.** The census did not
complete, twice, for a reason that is a defect in the harness rather than a property of the data.
That verdict is reported as the instrument computed it and is not talked around.
**Engine:** `mutmut` 3.7.0 + `libcst` 1.9.0, 24 workers, 60 s per-mutant timeout.
**Pre-registered at** `7b6ada0`, before any mutant was generated.

---

## 1. The question

EXP-47 measured the **product** code at composite raw β = 0.3345 [0.3138, 0.3559]. Every β, α and
interval this project has published, however, was produced by a different body of code: the
research runners under `docs/10-research/experiments/`. Nobody had asked what *their* β is.

The question is not academic. If the code that produces a measurement is less well guarded than
the code being measured, the error bars on every published figure are wrong in an unknown
direction, and the project's central claim — that verification quality is measurable and
load-bearing — applies first to itself.

## 2. Headline `[measured]`

Across the five targets that completed (run 1, 5,430 first-order mutants, 23 min wall clock):

| body of code | mutants | survived | raw β | 95% Wilson |
|---|---:|---:|---:|---|
| **research instruments** (EXP-49) | 5,430 | 3,706 | **0.6825** | **[0.6700, 0.6948]** |
| product `src/consilient/` (EXP-47) | 1,931 | 646 | 0.3345 | [0.3138, 0.3559] |

**The instruments are roughly twice as permissive as the code they are used to study**, and the
intervals do not come close to overlapping.

Per instrument:

| target | mutants | survived | raw β | 95% Wilson |
|---|---:|---:|---:|---|
| `exp31` (GPU / served-model runner) | 1,068 | 981 | **0.9185** | [0.9006, 0.9335] |
| `exp27_collector` (trajectory collector) | 490 | 391 | 0.7980 | [0.7602, 0.8311] |
| `exp43` (retro-verifier) | 1,073 | 796 | 0.7418 | [0.7148, 0.7671] |
| `exp07` (headroom / attempt runner) | 1,322 | 774 | 0.5855 | [0.5587, 0.6117] |
| `exp45` (condensation retention) | 1,477 | 764 | 0.5173 | [0.4918, 0.5427] |
| `exp27_handshake` | **0 of 965 completed** | — | — | — |

## 3. The sharp finding: fifteen functions where nothing is killed at all

`[measured]` **1,773 of the 5,430 mutants — 32.7% — lie inside functions in which not a single
mutation is caught by any check.** Fifteen of the sixty functions tracked have `killed == 0`.
The eleven largest:

| function | mutants, all surviving |
|---|---:|
| `exp43/run_commit_test` | 295 |
| `exp31/main` | 260 |
| `exp31/summarise` | 224 |
| `exp07/run_attempt` | 215 |
| `exp27_collector/collect` | 208 |
| `exp31/run_attempt` | 202 |
| `exp45/main` | 132 |
| `exp31/feasibility_probe` | 76 |
| `exp43/ensure_scratch_clone` | 54 |
| `exp31/served_identity` | 37 |
| `exp31/gpu_free_mib` | 35 |

Read the names. `run_commit_test` is the retro-verifier's oracle — the function that decides
whether a historical commit passes its own tests, and therefore the function that produced
EXP-43's β. `summarise` computes the numbers EXP-31 reports. `run_attempt` executes the attempt
whose outcome becomes a data point. `collect` writes the trajectory.

**These are not helpers. They are the measurement apparatus, and β = 1.0 across all of them.** Any
single-token change to the code that decides what a result *is* passes every check this repository
runs.

This is `P2-guards.md`'s thesis in its strongest available form. P2 catalogued individual checks
that could not fail. Here an entire evidence-producing layer has no automated verification at all,
and it was invisible because the layer's own tests are what the census mutates *against* — the
tests exist, they pass, and they exercise almost none of the code that matters.

### Critical paths, which are worse than the average

The pre-registration named four categories to report separately, on the grounds that a defect in
them corrupts results silently rather than loudly:

| path | mutants | survived | raw β | 95% Wilson |
|---|---:|---:|---:|---|
| `results_write` — writing the output file | 258 | 206 | **0.7984** | [0.7453, 0.8429] |
| `timeout` — deadline and process-tree kill | 267 | 207 | **0.7753** | [0.7215, 0.8212] |
| `run_id` — run identity in the record | 97 | 54 | 0.5567 | [0.4576, 0.6515] |
| `lock` — mutual exclusion between runs | 271 | 138 | 0.5092 | [0.4500, 0.5682] |

`timeout` at 0.7753 is the one to take seriously. This machine has already measured subprocess
overruns of 10–269 seconds past their deadline because descendant processes held pipes open. Four
in five mutations of the code meant to prevent that survive every check.

## 4. Equivalence is not corrected, so β here is an upper bound `[algebra]`

EXP-47 audited its survivors and found 60 of 646 (9.29%) semantically equivalent. **EXP-49
classified none**: all 3,706 survivors are recorded `unclassifiable / semantic_equivalence_not_proven`,
which is the conservative treatment the pre-registration fixed. The 0.6825 above is therefore an
**upper bound**, not a corrected estimate, and the instrument correctly refused to compare it with
EXP-47's corrected 0.3132.

The comparison survives anyway, and this is worth stating precisely because it is the reason the
headline is safe:

> For EXP-49's corrected β to fall as low as the **top** of EXP-47's corrected interval (0.3346),
> **2,498 of its 3,315 survivors — 75.4% — would have to be equivalent mutants.**
> EXP-47 measured 9.29%.

An equivalence rate eight times higher in the research code than in the product code, in the same
language with the same operator set, is not a live possibility. The two-fold gap is robust to any
plausible correction.

*(Both figures in that sentence are computed over run 1's five completed targets; the arithmetic is
`(3315 − e)/(4940 − e) = 0.3346`.)*

## 5. The census never completed, and why `[measured]`

Two runs, two different stopping points, both `insufficient_evidence`:

| run | targets completed | mutants | stopped by |
|---|---|---:|---|
| 1 | 5 of 6 | 5,430 | killed externally during `exp27_handshake` (96/965 done) |
| 2 | 2 of 6 | 2,390 | `input manifest changed; stopping with insufficient evidence` |

Run 2's abort is a **harness defect, not a data property.** `input_manifest()` hashes every file
found by `rglob("*")` under the five watched experiment directories, excluding only `__pycache__`
and `.pyc`. Any transient file appearing there during execution — a lock, a scratch output, a
temporary artefact written by an instrument's own test suite — changes the manifest and aborts the
census.

It is a **race**, not a deterministic condition: run 1 passed the same checkpoint that stopped run
2, and re-hashing every pinned path afterwards shows **no file differing from the pinned manifest**.
The offending file appeared and was removed inside the window.

The guard's intent is *"the inputs did not change under me"*. Its implementation is *"the set of
files under these directories is identical"*, which is a stronger and wrong condition when one of
the mutated instruments creates files under its own directory. **Proposed repair, not yet applied:**
compare hashes for the pinned path set only, treat newly appeared paths as a reported warning rather
than an abort, and keep aborting on any modification to a pinned path. Applying it changes
`harness_sha256` and therefore needs recording as an amendment to the pre-registration rather than a
silent patch, which is why it has not been done here.

`exp27_handshake` is a separate and legitimate cost: its verifier performs live zero-inference CLI
capability probes, so its 965 mutants each pay a real subprocess round trip. It makes no model calls
and spends nothing, but it is roughly an order of magnitude slower per mutant than the rest.

## 6. Determinism, which is the one thing that did go right `[measured]`

Twenty-four concurrent workers, instruments that spawn subprocesses, take locks and probe hardware.
None of that is obviously reproducible, and a mutation outcome that varies between runs is not a
measurement.

```
$ python docs/10-research/experiments/exp49/compare_runs.py
run 1: 5430 mutants   run 2: 2390   overlap: 2390
outcome disagreements across the overlap: 0
```

**Zero disagreements across every mutant both runs reached.** Per-target survivor counts are
identical to the unit: `exp07` 774/1322 and `exp31` 981/1068 in both. Whatever else is wrong with
this census, its results are reproducible, and the control script is committed so that claim can be
re-checked rather than believed.

## 7. What this does not decide

- **It does not correct any published figure.** A weakly guarded instrument is not a wrong one. β =
  1.0 on `run_commit_test` says a defect there would go undetected; it does not say a defect is
  present. Nothing here shows any published number to be false.
- **It inherits EXP-47's competence-difficulty gap.** First-order syntactic mutants are not the
  faults humans and agents actually emit. Whether that makes 0.6825 optimistic or pessimistic is
  exactly what **EXP-50** is pre-registered to measure.
- **`exp27_handshake` is unmeasured**, and it is the instrument that probes what the other runtimes
  can do — plausibly the most consequential of the six.
- **The three remaining research instruments were never in scope**, and the sixteen not selected as
  targets are unmeasured.

## 8. The one action this justifies, and the one it does not

**Justified:** the four critical paths — `results_write`, `timeout`, `run_id`, `lock` — get tests
before any further instrument is written, starting with `timeout`, where the failure mode has
already been observed on this machine rather than merely imagined.

**Not justified:** rewriting the instruments. Their β is high because they were written to answer a
question once, under time pressure, and were then relied on repeatedly — which is an ordinary and
mostly correct trade. The finding is not that they are bad code. It is that **the project measured
its product and never once measured its own instruments**, and the number was twice as bad in the
place nobody looked.

## Reversal and falsifier

**Reversal:** `git revert` this commit; the instrument, both result sets and this document
disappear, and the research runners return to being unmeasured.

**Falsifier:** an equivalence audit that classifies 75% or more of EXP-49's survivors as semantically
equivalent would collapse the two-fold gap and refute the headline. That audit has not been run and
is the single cheapest way to overturn this document. A smaller falsifier: if the fifteen zero-kill
functions turn out to be dominated by unreachable defensive branches, the "no automated
verification" reading is too strong and should be narrowed to the reachable subset.

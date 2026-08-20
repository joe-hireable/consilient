# Codex numeric-provenance audit — 20 August 2026

**Auditor:** Codex (`gpt-5.6`), read-only, over a snapshot of `docs/` staged outside the
repository. **382 quantitative claim bundles reviewed; 336 adjudicated — 184 reproduce, 13 do
not, 139 untraceable; 46 could not be dynamically checked.** All 39 decision records examined.
[measured]

**Complete: all 33 findings.** Six of them (20–25) were initially lost to an output cap I set on the terminal, and were recovered by resuming the session. That is recorded because a report silently missing a fifth of its findings would look complete.

**Preserved here because it existed only in a session temp directory.** The audit could not write
its own report: I launched it with a sandbox flag that forbade file writes, so it delivered the
report as terminal output and nothing else. That is the second time in one night that a
substantial result survived only in `%LOCALAPPDATA%/Temp` — see
`../10-research/experiments/exp16/transcripts/README.md`. [measured]

**Two limitations the auditor declared, unprompted, and which should be read first:**

1. **Python execution was blocked**, including by absolute path. It states plainly: *"I therefore
   cannot honestly claim the requested Python recomputation; I independently recomputed the raw
   JSON using Node instead."* The recomputation is real, and it is not the one that was asked for.
2. **The `docs/` tree was verified unchanged**: a SHA-256 manifest before and after is identical
   at `183acf23a308331bb042051f6b2be3dc05211d5cbf385d9bd0bda3c6147444cd`.

**What has already been acted on, and how it was checked.** Findings 3, 27, 28 and 30 have been
addressed in commits `272648d`, `4a92453` and earlier. Finding 3 — ADR-0002's zero false-safe
rate — was verified **three ways** before anything was changed: the auditor's arithmetic, an
independent exact-binomial computation, and running the ADR's own named script unchanged. Finding
30 (EXP-36 assigned twice) had already been found and fixed hours earlier from the register side;
the auditor was reading a pre-fix snapshot, and independently reached the same conclusion.

**The remaining findings below are NOT yet verified.** They are an auditor's report, not this
project's evidence. Each needs the same treatment before it is acted on or quoted — and at least
one already known to be partly wrong is noted inline where it appears. Treat every number in this
file as `[asserted]` until checked.

---

## Finding 1 — EXP-01 has three incompatible sample denominators

**Where:** `docs/10-research/experiments/exp01/findings-exp01.md:3-7,22-30`; `docs/10-research/experiment-register.md:25-35`

**Number as quoted:** A 32-agent audit, with one agent per sampled label.

**What the artefact says:** The findings describe 15 bad-pair labels plus 5 clean labels per repository across two repositories. The register separately specifies a 30-PR manual sample. No raw sample manifest resolves the discrepancy.

**Arithmetic:**  
`(15 + 5) × 2 repositories = 40 sampled labels`, not 32. The three recorded denominators are therefore 32, 40, and 30.

**Severity:** Material. It makes the EXP-01 audit denominator indeterminate and weakens every measured β estimate derived from that audit.

## Finding 2 — The specification’s n=1 EXP-07 status is contradicted by the completed n=30 experiment

**Where:** `docs/40-spec/v0-draft.md:53-56,319-327`; `docs/10-research/experiments/exp07/results-exp07.json:75-1008`; `docs/decisions/0003-no-learned-routing-policy-in-v0.md:75-95`

**Number as quoted:** EXP-07 has reopened ADR-0003, but `n=1` has not overturned it.

**What the artefact says:** EXP-07 contains 30 completed attempts: 5 frontier and 25 local. The raw single-attempt median is 1.693×, below the 2× trigger. Only best-of-five crosses it, so ADR-0003 is explicitly not reopened. The specification’s later section records this correctly.

**Arithmetic:**  
`5 frontier + 25 local = 30`, not 1.

Single-attempt ratios:

- `74.815 / 44.190 = 1.6930`
- `509.257 / 40.755 = 12.4956`
- `78.368 / 63.166 = 1.2407`
- `290.483 / 39.688 = 7.3192`
- `97.658 / 81.152 = 1.2034`

Their median is `1.6930`, below `2×`.

**Severity:** Material staleness. It changes the stated non-goal and research posture, although the actual ADR-0003 decision remains unchanged.

## Finding 3 — ADR-0002’s “zero” false-safe rate is mathematically false

**Where:** `docs/decisions/0002-organise-around-beta-verifier-false-accept-rate.md:49-56`; `docs/10-research/experiments/q3_bimodal_and_q2_sample_complexity.py:61-66,88-105`

**Number as quoted:** “The false-safe rate is 0 at every sample size tested.”

**What the artefact says:** The current producer uses the exact threshold  
`β* = 0.97 × exp(−8 × 0.27) = 0.1118653674` and declares safe when the Wilson upper bound is below it.

At `n=50`, `k≤1` is declared safe. At `n=100`, `k≤5` is declared safe.

**Arithmetic:** At true `β=0.15`:

`P(X≤1; n=50) = 0.85^50 + 50 × 0.15 × 0.85^49 = 0.00290545`

At `n=100`:

`P(X≤5; n=100, p=0.15) = 0.00155265`

Neither is zero. Across 8,000 simulation draws, the expected false-safe counts are approximately:

- `8,000 × 0.00290545 = 23.24`
- `8,000 × 0.00155265 = 12.42`

The probability of observing zero at `n=50` is approximately:

`(1 − 0.00290545)^8000 ≈ 8 × 10^-11`

**Severity:** Material safety overstatement. The conservative decision rule survives, but its claimed error behaviour does not.

## Finding 4 — ADR-0002’s 84% power result uses a rounded threshold rather than the current formula

**Where:** `docs/decisions/0002-organise-around-beta-verifier-false-accept-rate.md:53-56`; `docs/10-research/experiments/q3_bimodal_and_q2_sample_complexity.py:88-103`

**Number as quoted:** At true `β=0.08`, even `n=800` reaches only 84% safe-declaration power against `β*=0.111`.

**What the artefact says:** The current executable uses the exact threshold `0.1118653674`. At `n=800`, the Wilson upper bound for `k=72` is `0.1118401`, so `k=72` is also accepted.

**Arithmetic:**

Using the exact threshold:

`P(X≤72; n=800, p=0.08) = 0.8652789 → 87%`

Using the displayed rounded threshold `0.111`, `k=72` is excluded:

`P(X≤71; n=800, p=0.08) = 0.8361288 → 84%`

**Severity:** Material near a discrete decision boundary. The headline and current executable do not reproduce each other because premature rounding changes the accepted count.

## Finding 5 — The retained β*=0.432 value does not reproduce from the superseding closed form

**Where:** `docs/decisions/0002-organise-around-beta-verifier-false-accept-rate.md:27-33,155-160`; `docs/10-research/findings.md:41-51`

**Number as quoted:** At capability gap `0.10`, `β*=0.432`.

**What the artefact says:** The same ADR’s superseding exact formula gives `0.4358`, rounded to `0.436`.

**Arithmetic:**

`β* = 0.97 × exp(−8 × 0.10)`  
`= 0.97 × exp(−0.8)`  
`= 0.435849 → 0.436`

This is not `0.432`.

**Severity:** Cosmetic because the old table is explicitly superseded, but it remains a non-reproducing number in the decision record.

## Finding 6 — ADR-0011 turns 21 subprojects into 21 orchestration frameworks

**Where:** `docs/decisions/0011-evidence-merge-not-meeting.md:55-56`; `docs/10-research/bibliography.md:138`

**Number as quoted:** 63 production incidents across 21 orchestration frameworks.

**What the artefact says:** The full-read bibliography records 63 incidents across 21 subprojects and 18 ecosystems. It also warns that this is a convenience, failure-confirming sample.

**Arithmetic:** The incident count `63` reproduces. The unit attached to `21` does not:

- Quoted: `21 frameworks`
- Source: `21 subprojects`
- Separate source denominator: `18 ecosystems`

**Severity:** Moderate. The hard-budget decision survives, but the breadth of evidence is overstated and the denominator is corrupted.

## Finding 7 — ADR-0017 repeats a Graphiti-versus-mem0 comparison the bibliography retracts

**Where:** `docs/decisions/0017-bootstrap-harness.md:65-73`; `docs/10-research/bibliography.md:132`; `docs/decisions/0025-model-discovery-and-capability-probing.md:132-141`

**Number as quoted:** Graphiti scores 63.8% versus mem0’s 49% on the temporal subset of LongMemEval.

**What the artefact says:** The full bibliography says this is a mashup:

- 63.8% is Zep’s overall result from its vendor paper.
- 49% is mem0’s overall result from an unrelated third party.
- No temporal-subset head-to-head comparison exists.

The repository’s corrected vendor temporal figures are `54.1%/62.4%` versus full-context `36.5%/45.1%`, not Graphiti versus mem0.

**Arithmetic:** Although `63.8 − 49.0 = 14.8 percentage points`, subtracting unrelated overall results does not produce a valid comparative estimand.

**Severity:** Material citation error in the evidence against the selected bootstrap stack.

## Finding 8 — ADR-0019 repeats the wrong “21 frameworks” denominator

**Where:** `docs/decisions/0019-paid-capability-acquisition.md:45-48`; `docs/10-research/bibliography.md:138`

**Number as quoted:** 63 confirmed incidents across 21 orchestration frameworks.

**What the artefact says:** The cited full-read source is recorded as 63 incidents across 21 subprojects and 18 ecosystems.

**Arithmetic:**

- `63` incidents: reproduced.
- `21` frameworks: not reproduced.
- Correct units: `21 subprojects`, spanning `18 ecosystems`.

**Severity:** Moderate. This is a second downstream laundering instance of the same corrupted denominator.

## Finding 9 — ADR-0031’s claim that all three neighbouring harnesses are Node CLIs is superseded by local inspection

**Where:** `docs/decisions/0031-implement-v0-in-python-with-a-stdlib-only-core.md:57-60`; `docs/decisions/0032-single-language-python-for-the-orchestrator.md:43-58`

**Number as quoted:** All three neighbouring harnesses are Node CLIs.

**What the artefact says:** ADR-0032 explicitly records that this ecosystem-adjacency premise is factually false after inspecting the installed distributions. The local measurements themselves lack retained raw output, but the fixed corpus unambiguously supersedes the earlier `3/3` claim.

**Arithmetic:** A universal claim of `3/3` fails if any one of the three is not a Node CLI. The later ADR records at least one counterexample, so the reproduced count is fewer than three.

**Severity:** Material stale premise, although ADR-0032 supplies independent replacement grounds for the Python decision.

## Finding 10 — ADR-0032 rounds 52.2/2.2 to 23× rather than 24×

**Where:** `docs/decisions/0032-single-language-python-for-the-orchestrator.md:94-100`

**Number as quoted:** Python at 52.2% versus TypeScript at 2.2% is a 23× gap.

**What the artefact says:** The quoted endpoints are sufficient to recompute the multiplier.

**Arithmetic:**

`52.2 / 2.2 = 23.7272727`

That is `23.7×`, or `24×` to two significant figures, not `23×`.

**Severity:** Cosmetic arithmetic error. The broader warning that language benchmarks disagree remains intact.

## Finding 11 — ADR-0033’s approximately 69%→28% result conflicts with the later full-read bibliography entry

**Where:** `docs/decisions/0033-decide-by-default-ask-only-where-the-user-is-the-only-valid-decider.md:74-77`; `docs/10-research/bibliography.md:293,341`

**Number as quoted:** A salient error display reduced over-reliance from approximately 69% to approximately 28%.

**What the artefact says:** Bibliography line 293 supports `~69%→~28%`. A second `[FULL]` entry for the same paper at line 341 says the salient condition’s average over-reliance was `0%`. TASK.md prohibits external verification, so this snapshot cannot resolve which arm or estimand is intended.

**Arithmetic:**

Quoted reduction:

`69 − 28 = 41 percentage points`  
`41 / 69 = 59.4% relative reduction`

Later bibliography account:

`69 − 0 = 69 percentage points`  
`69 / 69 = 100% relative reduction`

These cannot be the same endpoint.

**Severity:** Material internal citation conflict because the number supports the human-gate design.

## Finding 12 — ADR-0035’s decision-shaping 69%→28% figure conflicts with the later full-read entry

**Where:** `docs/decisions/0035-user-controlled-visibility.md:21-25`; `docs/10-research/bibliography.md:293,341`

**Number as quoted:** The “only manipulation known” to work reduced over-reliance from approximately 69% to approximately 28%.

**What the artefact says:** One full-read bibliography entry supports approximately 28%; the later duplicate says average over-reliance was 0%. The ADR says this single finding decides the shape of the interface.

**Arithmetic:**

`69% → 28%` is a `41 percentage-point` reduction.

`69% → 0%` is a `69 percentage-point` reduction.

The endpoint differs by `28 percentage points`.

**Severity:** Material. The cited intervention is load-bearing, and the repository has not reconciled its own two full-read summaries.

## Finding 13 — ADR-0035 repeats the same unresolved Vasconcelos endpoint in its evidence section

**Where:** `docs/decisions/0035-user-controlled-visibility.md:102-105`; `docs/10-research/bibliography.md:293,341`

**Number as quoted:** Salient display produces approximately `69%→28%`, while written explanations produce approximately `68%→66%`.

**What the artefact says:** The written-explanation figures agree with bibliography line 293, but the salient-display endpoint again conflicts with line 341’s `0%`.

**Arithmetic:**

Salient result as quoted:

`69 − 28 = 41 percentage points`

Later full-read result:

`69 − 0 = 69 percentage points`

Difference between the two reported effects:

`69 − 41 = 28 percentage points`

**Severity:** Material repeated laundering. This is a separate downstream claim bundle because the inconsistent number is asserted again as evidence.

## Finding 14 — Untraceable rank 1: EXP-01’s measured β estimates have no retained raw labels

**Where:** `docs/10-research/experiments/exp01/findings-exp01.md:3-7,9-33`

**Number as quoted:** Raw β estimates of `128/202 = 0.63` and `18/42 = 0.43`; corrected estimates of approximately `0.12` and `0.14`; jobboard interval approximately `[0.02,0.42]`.

**What the artefact says:** Per-PR records are gitignored and absent. There is no results JSON, redacted sample manifest, or retained label table. Only aggregate prose operands remain.

**Arithmetic:** The prose arithmetic reproduces:

- `128/202 = 0.633663 → 0.63`
- `18/42 = 0.428571 → 0.43`
- `(128/15 + 74/5) / 202 = 0.115512 → 0.12`
- `(18/15 + 24/5) / 42 = 0.142857 → 0.14`
- Propagated jobboard bounds: `[0.020789,0.417707] → [0.02,0.42]`

This verifies only the summary’s arithmetic, not its inputs.

**Severity:** Highest. β is the project’s organising measurement, and this snapshot cannot independently audit its first real-repository estimate.

## Finding 15 — Untraceable rank 2: the +0.123 learned-routing trigger has no results artefact or current producer path

**Where:** `docs/10-research/findings.md:78-91`; `docs/decisions/0003-no-learned-routing-policy-in-v0.md:23-30`; `docs/10-research/experiments/simulations.py:75-94,126-161`

**Number as quoted:** Wasted-work headroom is `+0.002` at `1×`, `+0.024` at `2×`, and `+0.123` at `5×`.

**What the artefact says:** No results JSON or stdout capture exists. More seriously, although `episode` accepts a `waste` parameter, the evaluation path never passes it, and the main block does not run a wasted-work sweep.

**Arithmetic:** The raw per-class utilities and costs needed to compute the three headroom values are absent. The only derivable comparison is that the quoted `5×` condition exceeds the ADR’s `2×` reopening threshold; the `+0.123` value itself cannot be reconstructed.

**Severity:** Material. The value is the largest sensitivity result and is used as a learned-routing reopening trigger.

## Finding 16 — Untraceable rank 3: the specification’s four tests plus four defects have no audit artefact

**Where:** `docs/40-spec/v0-draft.md:89-97`; `docs/10-research/experiments/exp07/findings-exp07.md:1-106`; `docs/10-research/experiments/exp07/results-exp07.json:1-1078`

**Number as quoted:** The author’s four instrument tests passed, then an independent `claude-opus-5` audit found four further defects.

**What the artefact says:** Neither count occurs in the EXP-07 findings or raw JSON. The register records an invalidated run and repairs but does not retain a four-test execution or a four-defect audit report.

**Arithmetic:** The prose implies `4 + 4 = 8` relevant observations, but zero of the eight is represented as a row or identifiable defect record in the fixed artefacts.

**Severity:** Material. This is the specification’s principal example of an independent “different class of facts”.

## Finding 17 — Untraceable rank 4: ADR-0032’s accepted T3 language decision lacks raw local measurements

**Where:** `docs/decisions/0032-single-language-python-for-the-orchestrator.md:43-76,108-110`

**Number as quoted:** Measurements include 7,236 bytes; 50.6 MB versus 98 KB; eight binaries/330 MB; 0.775 seconds; 655 KB; 88 versus approximately 1,000 lines; 43.3/49.2 MB; 27 tests; 700+/487; approximately 100,000 operations/second; and several start-up/checker timings.

**What the artefact says:** Exact-value searches find these figures only in ADR-0032. No command transcript, machine/environment record, raw output, or result file is retained.

**Arithmetic:** Some derived arithmetic is internally sound—for example:

`1,000,000 / 10.3 seconds = 97,087 operations/second`

But the `10.3 seconds` operand itself is not preserved outside the ADR.

**Severity:** Material. The ADR explicitly presents the evidence as measured T3 support for an accepted implementation-language decision.

## Finding 18 — Untraceable rank 5: private-history baselines underpin several accepted gates without a redacted aggregate artefact

**Where:** `docs/decisions/0010-name-the-different-class-of-facts.md:75-77`; `docs/decisions/0013-evaluate-on-repo-history-not-benchmarks.md:29-31,41-44`; `docs/decisions/0015-dogfooding-gate.md:59-62`; `docs/decisions/0023-pr-review-gates.md:107-122`; `docs/decisions/0036-upstream-first-adopt-contribute-never-silently-fork.md:109-124`

**Number as quoted:** 12 agents, 197 leads, one fabrication caught, 0/50 citation failures, 991 commits in 36 days, approximately 20 CI ratchets, 44 probes, five Major findings in 12 days, 1,693/1,350-file PRs, and 110 call sites.

**What the artefact says:** The original private repositories and prior codebase assessment are absent by policy. The snapshot contains prose summaries but no publishable aggregate manifest with corpus range, definitions, commands, and outputs.

**Arithmetic:** The surviving prose permits only superficial calculations:

- `1/197 = 0.005076 → 0.51%`
- `0/50 = 0%` observed failures, without an uncertainty calculation
- `991/36 = 27.53` commits/day

None validates the underlying event counts.

**Severity:** Material. These baselines support Gate A, the “different class” rule, enforcement ratchets, and review policy.

## Finding 19 — Untraceable rank 6: ADR-0034’s stall-detector numbers have neither sources nor event records

**Where:** `docs/decisions/0034-detect-stalls-by-artefact-progress-and-default-to-diagnosis.md:15-24,31-48,59-60,76-85,100-108,131-134`; `docs/decisions/0036-upstream-first-adopt-contribute-never-silently-fork.md:109-113`

**Number as quoted:** Three failures including a 30-minute/exit-0 case; approximately 180 seconds; 2–3× work; one-hour/30-minute and 120-second timeouts; a 32,768 process limit; 3/7 human catches; and a 2/9 bas

## Finding 20 — Untraceable rank 7: ADR-0005’s 5–30× offload cliff and catalogue figures have no source

**Where:** `docs/decisions/0005-local-model-library-with-hardware-gating.md:18-34,87-92,112-114`; `docs/10-research/bibliography.md:153-155`; `docs/10-research/local-model-fit-arithmetic.md:262-287,371-383`

**Number as quoted:** Approximately 1.7k stars, 200+ models, a 165-entry/four-component catalogue, and 5–30× CPU-offload slowdown.

**What the artefact says:** None of those figures has a named producing source in the fixed corpus. Later local metadata also requires KV-geometry wording: qwen3:8b uses 144 KiB per context token while gemma4:31b uses 80 KiB because of sliding-window attention.

**Arithmetic:** Despite being smaller:

`144 KiB/token > 80 KiB/token`

The ratio is:

`144 / 80 = 1.8×`

Thus size alone is not a sufficient KV predictor.

**Severity:** Material. The unsupported 5–30× range turns hardware feasibility into a binary policy, while the stale size rule can reject or admit the wrong model.

## Finding 21 — Untraceable rank 8: ADR-0025’s probe intervals and correlation corrections have no stored result

**Where:** `docs/decisions/0025-model-discovery-and-capability-probing.md:57-77,105-111,143-146`; `docs/10-research/experiments/probe_delta_ci.py`

**Number as quoted:** At `n=20/100/200`, β* bands `[0.064,0.310]`, `[0.064,0.193]`, and `[0.077,0.164]`; correlation changes `0.112→0.028`; `SE(φ)≈0.07–0.10`; naive `Δ̂=0.34` versus true `0.27`; approximately 5,000 trajectories.

**What the artefact says:** A named generator exists, but no results JSON or retained run output exists. The approximately 5,000 result is also wrongly attributed to registered EXP-03, which is a different, unrun experiment.

**Arithmetic:** The quoted correlation change is a factor of:

`0.112 / 0.028 = 4`

But the simulated samples producing the endpoints and interval bands are absent, so the figures cannot be independently regenerated in this run.

**Severity:** Material. These figures define the probe’s sample size and reopening conditions.

## Finding 22 — Untraceable rank 9: ADR-0026’s provider-admission measurements are prose-only

**Where:** `docs/decisions/0026-admit-only-budget-and-hardware-feasible-backends.md:53-54,182-197`

**Number as quoted:** Three approximately £200/month subscriptions, one exhausted; locally inspected tool versions; eleven Antigravity model choices; zero reported tokens.

**What the artefact says:** The fixed raw comparison has no Antigravity row, provider-headroom capture, or installed-version record. The values occur only in prose and bibliography descriptions.

**Arithmetic:** The asserted subscription outlay is approximately:

`3 × £200 = £600/month`

But neither the three-account inventory nor the exhaustion event is captured in an artefact.

**Severity:** Material to admission and budget feasibility, although it does not affect EXP-05’s raw coding-path arithmetic.

## Finding 23 — Untraceable rank 10: EXP-05’s Antigravity/OpenCode readiness counts are absent from its JSON

**Where:** `docs/10-research/experiments/exp05/findings-exp05.md:70-80,139-157`; `docs/10-research/experiments/exp05/backend-comparison.json`

**Number as quoted:** Antigravity CLI 1.1.15 returned eleven models and zero tokens; OpenCode was version 1.18.18; four strengthened path tests passed.

**What the artefact says:** `backend-comparison.json` contains seven coding-path rows but no Antigravity result, tool-version field, or four-test execution record. OpenCode’s tokens and cost are retained, but its version is not.

**Arithmetic:** The JSON supports seven rows and six distinct compositions. It provides no denominator from which eleven discovered models or four executed tests can be counted.

**Severity:** Moderate. The missing Antigravity evidence affects backend admission; the version gap is principally reproducibility metadata.

## Finding 24 — Untraceable rank 11: per-check β is asserted near zero or one without a dataset

**Where:** `docs/decisions/0012-composite-beta-with-per-check-diagnostics.md:11-14`

**Number as quoted:** Type-checker β is near zero for type errors and near `1.0` for logic errors.

**What the artefact says:** No per-check labelled dataset, accepted-bad denominator, or result artefact exists. EXP-03, which would measure dependence and per-check behaviour, remains unrun.

**Arithmetic:** “Near zero” and “near 1.0” provide neither counts nor operational bounds, so no proportion or interval can be recomputed.

**Severity:** Material as motivation for per-check diagnostics, though the decision to route only on the directly measured composite remains sound.

## Finding 25 — Untraceable rank 12: EXP-27’s 1.3-second headline has no timing field

**Where:** `docs/10-research/experiments/exp27/findings-exp27.md:7-10`; `docs/10-research/experiments/exp27/results-source-probe.json:1-54`

**Number as quoted:** All six endpoints returned HTTP 200 in 1.3 seconds.

**What the artefact says:** The JSON contains exactly six source rows and every status is 200. It contains `observed_at`, content type, and sample bytes, but no elapsed, duration, start, or end field.

**Arithmetic:**

- Row count: `6`
- Status-200 count: `6`
- Elapsed time: impossible to compute from the retained fields

**Severity:** Modest. Reachability reproduces; the performance headline does not have provenance.
8,348
## Finding 26 — Monte Carlo outputs are mistagged as algebra

**Where:** `docs/decisions/0002-organise-around-beta-verifier-false-accept-rate.md:13-14,31-37,49-56`; `docs/10-research/experiments/q3_bimodal_and_q2_sample_complexity.py:38-53,69-105`

**Number as quoted:** Empirical β* comparisons, movement ≤0.003, 18.8–63.5% escalation, and simulated declaration frequencies appear under `[algebra]`.

**What the artefact says:** The closed form and Wilson formula are algebra. The empirical comparisons, escalation range, and declaration frequencies are generated with random samples and are `[simulated]`.

**Arithmetic:** Exact formula evaluation can reproduce selected endpoints, but not convert Monte Carlo draws into algebra. For example, `0.97 exp(−8×0.27)=0.111865` is algebra; an empirical estimate near `0.112` is simulated.

**Severity:** Direct evidence-tag violation. It matters most where a random frequency is described as a guaranteed safety property.

## Finding 27 — External literature is promoted from cited to measured

**Where:** `docs/decisions/0010-name-the-different-class-of-facts.md:9-17`; `docs/decisions/0032-single-language-python-for-the-orchestrator.md:79-100`; `docs/decisions/0002-organise-around-beta-verifier-false-accept-rate.md:91-94`; `docs/10-research/bibliography.md:39,191`

**Number as quoted:** Kim et al.’s 94% of 16 configurations and up-to-80.8% gain; published SWE-PolyBench/Multi-SWE-bench/SWE-bench/ProMax figures; Claude Code v2.1.7 tool-search availability.

**What the artefact says:** These are external full/snippet/changelog sources. No local results artefact contains them. Reading a paper in full improves citation quality; it does not turn its results into a local measurement.

**Arithmetic:** The Kim values agree with the bibliography. The defect is the `[measured]` tag, not transcription.

**Severity:** Direct evidence-label violation, material where external benchmarks support the accepted language decision.

## Finding 28 — Cited works do not support several causal or operational inferences

**Where:** `docs/decisions/0003-no-learned-routing-policy-in-v0.md:31-33`; `docs/decisions/0020-meetings-and-authority-matrix.md:31-46,128-129`; `docs/decisions/0033-decide-by-default-ask-only-where-the-user-is-the-only-valid-decider.md:42-45,78-80,130-140`; `docs/decisions/0035-user-controlled-visibility.md:126`; `docs/10-research/bibliography.md:37,87,322`

**Number as quoted:** `b=−0.69` is treated as earned trust reducing scrutiny; sub-second approval is called unambiguous complacency.

**What the artefact says:** The `b=−0.69` source is a cross-sectional self-report association, not longitudinal earned trust, objective scrutiny, or artefact quality. No source validates a sub-second code-review threshold. Separately, Dekoninck’s “continuum” is an interpretation rather than its literal result, and Ao proves only that same-information delegation cannot outperform a centralised decision-maker—it does not forbid consultation.

**Arithmetic:** The coefficient is transcribed, but causal direction cannot be derived from a cross-sectional coefficient. The `<1 second` rule has no observed positive/negative counts from which sensitivity or specificity could be calculated.

**Severity:** Material for human-gate and visibility predictions; modest for the routing/governance wording.

## Finding 29 — Load-bearing decisions rely on abstract-only or second-hand sources

**Where:** `docs/decisions/0001-build-a-meta-harness-not-a-harness.md:48-52,75-80`; `docs/decisions/0016-skill-distribution-mcp-plugins.md:18-24,79-81`; `docs/decisions/0018-self-modification-gated-by-measured-verifier.md:16-20`; `docs/40-spec/v0-draft.md:420-423`; `docs/decisions/0035-user-controlled-visibility.md:17,107-120`; `docs/10-research/bibliography.md:58,107-108,167,300-306,347,350,352`

**Number as quoted:** A 6× harness gap; approximately 351,000 skills; DGM `20→50`; SICA `17→53`; `+55.8%` on a toy task versus `−19%` on real issues; and human-factors support for the visibility mechanism.

**What the artefact says:**

- The 6× number is Meta-Harness’s opening citation, not its own result.
- Approximately 351,000 is `[2ND]` and explicitly unverified.
- DGM and SICA are `[ABS]`.
- The `−19%` source is `[FULL]`, but `+55.8%` is `[ABS]` and lacks n/interval details.
- Parasuraman, Warm, and Endsley are `[ABS]`, with no software/LLM setting or effect sizes.

**Arithmetic:** No arithmetic error is established; the problem is evidential weight unsupported by reading depth.

**Severity:** Material for the release gate and visibility rationale; moderate elsewhere.

## Finding 30 — EXP-36 is assigned to two incompatible experiments

**Where:** `docs/decisions/0035-user-controlled-visibility.md:5,114-116,161-178`; `docs/10-research/experiment-register.md:942-949`; `docs/decisions/0016-skill-distribution-mcp-plugins.md:55-59`

**Number as quoted:** EXP-36 is presented as the pre-registered visibility-dial experiment.

**What the artefact says:** The experiment register assigns EXP-36 to the Ponytail behavioural-plugin experiment, and ADR-0016 uses that registered meaning.

**Arithmetic:** One identifier is assigned to two distinct protocols: `1 ID : 2 experiments`.

**Severity:** Material. The visibility experiment is not registered under a unique identifier and cannot honestly be described as pre-registered.

## Finding 31 — ADR-0002 still orders a completed test and says β has never been measured

**Where:** `docs/decisions/0002-organise-around-beta-verifier-false-accept-rate.md:6-7,35-45,168-182,211-216`; `docs/10-research/experiment-register.md:17-35,55-61`; `docs/10-research/experiments/exp01/findings-exp01.md:1-9,31-40`

**Number as quoted:** T3 has not been reached, β has never been measured, and test 3 should run first because bimodality may turn thresholds into cliffs.

**What the artefact says:** EXP-01 is a real but audit-limited proxy measurement. EXP-04 is DONE, and ADR-0002’s own update closes Q3 as distribution-free under its stated model. The residual risk is non-logistic competence, not bimodality. The same stale section calls Affordance Agent Harness unread although the bibliography records it `[ABS]` and checked/cleared.

**Arithmetic:** Not applicable; this is experiment-state and supersession drift.

**Severity:** Material research-priority staleness. PROVISIONAL status remains defensible, but its stated reason and next test do not.

## Finding 32 — Architecture numbers reproduce but omit required evidence tags

**Where:** `docs/20-design/architecture-sketch.md:56-60,72-79,131-134`

**Number as quoted:** `≥2×`, 63 incidents, and a measured approximately 0.5% fabrication rate.

**What the artefact says:** The `≥2×` trigger traces to the simulated wasted-work rule; 63 traces to the full Khan bibliography entry; the private summary reports one fabrication among 197 leads. None carries a literal bracketed evidence tag in the architecture document.

**Arithmetic:**

`1/197 = 0.005076 = 0.5076% → approximately 0.5%`

**Severity:** Evidence-tag rule violation. The arithmetic is sound; the missing tag on the routing trigger is the most consequential.

## Finding 33 — EXP-31 is an incomplete 25/50-run artefact

**Where:** `docs/10-research/experiments/exp31/results-exp31.json:2,38-772`; `docs/10-research/experiment-register.md:978-1025`; `docs/40-spec/v0-draft.md:325-327`

**Number as quoted:** The registered procedure is `5 fixtures × 2 models × 5 attempts = 50 attempts`.

**What the artefact says:** The JSON sets `complete:false` and contains 25 runs:

- qwen3:8b: `0/15` passed, comprising 10 rejected and 5 timed out.
- gemma4:31b: `10/10` passed, but only on the first two fixtures.

Neither model has completed all five fixtures.

**Arithmetic:**

`15 + 10 = 25`

`25 / 50 = 50%` of the registered run.

The partial rates `0/15` and `10/10` are not comparable five-fixture estimands.

**Severity:** No final EXP-31 conclusion is supportable. The specification honestly says it is running; the register heading still says READY.

## Checked and correct

### EXP-05 raw comparison

`docs/10-research/experiments/exp05/backend-comparison.json` contains seven rows representing six coding compositions. All recorded process/verifier, duration, token/cache, and cost fields reproduce the paired findings.

The principal latency ratios reproduce:

- Ollama/Codex: `114.2 / 20.4 = 5.5980 → 5.6×`
- Ollama/Claude: `114.2 / 25.6 = 4.4609 → 4.5×`
- Ollama/Cursor: `114.2 / 47.0 = 2.4298 → 2.4×`

Other raw rows also match:

- Claude: 25.6 seconds, 8 input tokens, `$0.53987225`
- Codex: 20.4 seconds, 87,356 tokens
- Ollama: 114.2 seconds, 559,095 tokens
- Cursor: 47.0 seconds, 74,781 input and 92,160 cached tokens
- Codex/OpenRouter: 100.9 seconds, verifier failure, immediate counter zero and delayed cumulative `$0.045138255`
- OpenCode: 24.1 seconds, 40,918 input and 40,138 cache-read tokens, `$0.0170272`, functional tests passing but scope failing
- Cursor ACP: 29.7 seconds and verifier pass

### EXP-07 raw runs

Independently ignoring the stored summary, the 30 run rows give:

- Frontier: `5/5` passed
- Local: `0/25` passed
- Outcomes: 5 passed, 19 rejected, 6 agent timeouts
- Every local `changed_files` list is empty

Frontier durations:

`[44.190, 40.755, 63.166, 39.688, 81.152]`

- Median: `44.190`
- Range: `39.688–81.152`

The 25 local durations give:

- Median: `97.658`
- Range: `44.436–509.257`

First-attempt ratios:

- `74.815 / 44.190 = 1.6930`
- `509.257 / 40.755 = 12.4956`
- `78.368 / 63.166 = 1.2407`
- `290.483 / 39.688 = 7.3192`
- `97.658 / 81.152 = 1.2034`

Median: `1.6930 → 1.69`

Five-attempt sums divided by frontier duration:

`[17.9534, 25.6971, 5.3586, 24.4077, 8.3418]`

Median: `17.9534 → 17.95`

Replacing every censored duration with its 240-second timeout gives:

`[16.7503, 18.5850, 5.3586, 22.5923, 8.2213]`

Median: `16.7503 → 16.75`

Timeout overruns also reproduce after rounding:

`[9.781, 20.597, 21.565, 50.483, 53.166, 269.257]`

The raw file is 36,957 bytes with SHA-256:

`77ad41759a0913cb483d68797e2edd62d7b7eaa117f35d09c3e4ee5082fa37d7`

Both match the findings.

### EXP-27 raw probe

The raw JSON has six rows and all six statuses are 200. The recorded content types also reproduce. Only the 1.3-second duration is absent.

### EXP-01 prose arithmetic

Although the raw evidence is absent, the arithmetic from the published operands reproduces:

- `98/300 = 32.67% → 33%`
- `128/202 = 0.6337 → 0.63`
- `18/42 = 0.4286 → 0.43`
- Wilson `1/15 = [0.0119,0.2982] → [0.01,0.30]`
- Wilson `1/5 = [0.0362,0.6245] → [0.04,0.62]`
- Corrected jobboard: `(128/15 + 74/5)/202 = 0.1155 → 0.12`
- Propagated jobboard interval: `[0.0208,0.4177] → [0.02,0.42]`
- Corrected hireable: `(18/15 + 24/5)/42 = 0.142857 → 0.14`

These calculations do not cure the absent labels or contradictory sample count.

### Global review-ceiling algebra

The human-review figures reproduce:

- `25/8 = 3.125 → 3.1 agents`
- `60/8 = 7.5 diffs/hour`

With `p_good=0.55`, review time 8 minutes, and  
`T_effective = 8 × [0.55 + 0.45(1−R)]`, the critic rows reproduce:

| Critic recall | Max agents | Good merges/hour |
|---:|---:|---:|
| 0.00 | 3.125 → 3.1 | 4.125 → 4.1 |
| 0.50 | 4.032 → 4.0 | 5.323 → 5.3 |
| 0.85 | 5.061 → 5.1 | 6.680 → 6.7 |
| 0.95 | 5.459 → 5.5 | 7.205 → 7.2 |

### ADR-0002 deterministic calculations

The following reproduce:

- `0.97 exp(−8×0.27) = 0.111865 → 0.1118`
- Gap 0.42: `0.033693 → 0.0337`
- Gap 0.10: `0.435849 → 0.4358`
- Wilson `k=2,n=50`: `[0.011039,0.134603]`
- Wilson `k=5,n=100`: `[0.021543,0.111752]`
- Wilson `k=10,n=200`: `[0.027382,0.089579]`
- At true `β=0.04,n=200`: safe-declaration probability `0.968788 → 97%`
- Structural-zero change: `0.111865→0.058582`, quoted `0.112→0.059`
- Majority-of-five midpoint slope multiplier: `1.875`
- Five-try verifier shopping: `1−0.9^5 = 0.40951 → 0.41`

The exceptions are Findings 3–5.

### Other traced decision figures

The following reproduce against raw artefacts or the repository’s full-read bibliography:

- ADR-0003’s completed EXP-07 update
- ADR-0007’s review-capacity algebra
- ADR-0010’s Kim and relay-degradation figures
- ADR-0027’s EXP-05 composition claims
- ADR-0029’s six source probes
- Architecture’s `1/197≈0.5%` arithmetic
- The bibliography’s 63-incident count, provided its correct units—21 subprojects and 18 ecosystems—are retained

### Decision-file coverage

All 39 files were read in full.

Files with no additional numeric adverse finding were:

- `0004-licence-mit-dco-and-the-cla-question.md`
- `0006-ticket-store-sqlite-plus-git-log.md`
- `0007-cli-only-no-review-surface.md`
- `0009-route-per-task-not-per-step.md`
- `0021-pushback-protocol.md`
- `0022-safety-floor-and-moderation.md`
- `0024-commercialisation-and-telemetry.md`
- `0027-compose-domain-harness-provider-and-model.md`
- `0030-size-orchestration-by-usable-context-and-measured-outcomes.md`
- `README.md`—its numeric row is explicitly an example
- `_template.md`

All remaining decision files contributed a finding, an untraceable claim, or a declared could-not-check item above. The directory count itself reproduces: 36 numbered ADRs plus three supporting markdown files equals 39.

## Could not check

- **Python execution was impossible.** Both `python --version` and the absolute pyenv-win Python 3.13.11 executable were rejected before process creation with `CreateProcess ... rejected: blocked by policy`. Spawning the same executable from the persistent Node runtime returned `EPERM`. No Python/Jupyter tool was available, and no local Pyodide module existed. Raw JSON calculations above were therefore independently recomputed in Node, never from stored summary fields, but were not performed with Python.

- **Forty-five stochastic bundles in `docs/10-research/findings.md` could not be dynamically rerun.** Their scripts retain no raw output, and Python launch was blocked. Their downstream ADR quotations are counted untraceable under TASK.md’s strict rule.

- **EXP-07’s “15 tests pass” statement could not be dynamically rerun.** Exactly 15 test definitions are present statically, but static counting is not a test execution.

- **EXP-01 raw labels are unavailable by design.** Its data directory is gitignored/private. Only aggregates remain, so neither the sample contradiction nor the measured β inputs can be independently resolved.

- **Private-repository claims cannot be checked.** Project rules prohibit publishing those sources, and the snapshot contains no redacted aggregate manifest. The audit reports the gap without seeking private code.

- **EXP-31 is incomplete.** Its 25 partial rows were recomputed, but no registered final headline can be checked.

- **Live registry, star, provider-headroom, and local-command measurements lack dated response captures.** Re-probing would not reproduce the historical 19–20 August snapshots even if network access were available.

- **Legal claims in ADR-0004 lack named internal sources.** The ADR correctly demands solicitor review; this audit cannot assess them internally.

- **External papers were not independently verified.** Per TASK.md, bibliography honesty was checked only against the repository’s own `[FULL]`, `[ABS]`, `[SNIP]`, and `[2ND]` records.

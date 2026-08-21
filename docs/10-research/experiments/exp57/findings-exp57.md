# EXP-57 findings — the marginal value of context

**Date:** 20 August 2026
**Status:** `[measured]` for every rate, interval, token count and disagreement figure below;
`[asserted]` for the stopping-rule verdicts, the criticisms of the pre-registration, and the
design implications.
**Instrument:** `run_exp57.py` · **Results:** `results-exp57.json`,
`results-exp57-rerun-control.json` · **Raw call log:** `checkpoint-exp57*.jsonl` ·
**Determinism control:** `compare_runs.py` · **Paired tests:** `test_exp57.py` (28 passing).
**Pre-registration:** `docs/10-research/experiment-register.md` → EXP-57, unaltered.

---

## Executive summary

640 model calls — 512 in the census, 128 in the determinism control — over 128 items drawn
from EXP-47's committed mutant corpus, one model, four arms differing only in how much context
the model saw.

**Between the smallest and the largest arm, the input token count rises 45× and nothing else
moves.** Every one of the eighteen pairwise difference intervals spans zero. The four arms
disagree with each other on 2–9 items out of 128, symmetrically, and no McNemar test comes
close to significance.

**The pre-registered verdict is the fourth stopping rule: insufficient power.** It is quoted in
full in §5, and the honest reading of it is in §6 — this run did not fail to find a difference
because the instrument was weak. It found that on this task the model errs 2.3%–4.7% of the
time *with the diff alone*, and no amount of extra context moved that number by more than the
experiment's own noise.

**The load-bearing number is not in the pre-registration.** The determinism control re-ran 128
of the calls and **4 verdicts flipped — 96.88% agreement, a 3.1% irreproducibility rate.** The
largest gap between any two arms is 1 item in 64 (1.6 percentage points). **The run-to-run
noise floor is larger than every between-arm difference measured.** Any narration of a trend
across these arms would be narrating resampling noise.

---

## 1. What was run

| | |
|---|---|
| Corpus | `exp47/results-exp47.json`, `weakest_guards` — EXP-47's non-equivalent surviving true defects |
| Equivalent mutants excluded | **60**, by EXP-47 itself; re-derived at load time (`verify_corpus_excludes_equivalents`) |
| Non-equivalent survivors available | 586 |
| Uniquely locatable in the pinned tree | **520** (66 dropped: multi-line, 120-char-truncated, or not uniquely addressable) |
| Items drawn | **128** — 64 defect, 64 fix, disjoint mutants, `random.Random(57).sample` over a sorted pool |
| Source revision | `d579bee` — the commit EXP-47's corpus was generated from |
| Model | `claude-sonnet-5` via `claude -p`, flat-fee, no metered vendor |
| Calls | 512 census + 128 control = **640**, 0 failed, 0 unadjudicated |
| Total input tokens | **8,407,929** to Sonnet, plus **2,964,703** to an auxiliary model (§4) |
| Total call time | 2,249.8 s census + 515.9 s control |

### The item construction, and why it is symmetric

The corpus gives, for each surviving mutant, a pristine line and a mutated line. Each item is a
one-line unified diff (3 lines of context) in one of two directions:

| class | before | after | correct verdict |
|---|---|---|---|
| **defect** (n=64) | pristine file | mutated file | REJECT |
| **fix** (n=64) | mutated file | pristine file | ACCEPT |

Ground truth is mechanical: EXP-47 established these mutants are non-equivalent, so the change
is behaviourally real in both directions; the pristine line is the repository's own reviewed
code. A good item and a bad item are therefore *the same two lines* with the arrow reversed —
the surface form is matched, and no cue distinguishes the classes. β is the false-accept rate on
defect items; α is the false-reject rate on fix items. No mutant is used in both directions, so
the two classes are independent samples rather than 64 correlated pairs.

**One thing this construction had to get right and nearly did not.** Whatever extra context an
arm supplies is rendered in the **after** state of the change. Rendering the pristine tree would
have made every defect item's new line the only line in the prompt that contradicts the rest of
the codebase — a free tell, available only to the two arms that see the tree, that would have
manufactured exactly the result the experiment is looking for. `test_exp57.py` asserts this
against `build_prompt` itself; the first version of that test rebuilt the rendering inline and
passed while the code shipped the pristine tree, which is the defect class `P2-guards.md`
catalogues.

### The padding — what it tests and what it does not

`padded` = `full` plus a fixed 56,642-byte body of **irrelevant-but-plausible** material: four
Python standard-library modules (`textwrap.py`, `shlex.py`, `csv.py`, `colorsys.py`,
sha256 `17ce5853…`, CPython 3.13.11), taken in a fixed order until they exceeded the byte size
of the source tree. Identical for every item.

- **It tests** whether *plausible but wrong* code degrades the answer. That is the realistic
  failure of a retrieval system: it does not return lorem ipsum, it returns real code from the
  wrong place.
- **It does not test** whether volume alone distracts — that is irrelevant-**and-obvious**
  padding (lorem ipsum), and it is a different experiment with a different mechanism.
- **It also does not test** the nastier case: near-miss context, code from the *same* project
  but the wrong module, which shares vocabulary with the diff. Third experiment.

---

## 2. β and α per arm `[measured]`

Wilson 95% intervals, n = 64 per class per arm, 0 unparsable replies in 640 calls.

| arm | β (accepted a defect) | α (rejected a fix) | error rate (128) | accept rate |
|---|---|---|---|---|
| **minimal** | **0.0469** [0.0161, 0.1290] — 3/64 | 0.0313 [0.0086, 0.1070] — 2/64 | 0.0391 [0.0168, 0.0882] | 0.508 |
| **relevant** | **0.0469** [0.0161, 0.1290] — 3/64 | 0.0469 [0.0161, 0.1290] — 3/64 | 0.0469 [0.0217, 0.0985] | 0.500 |
| **full** | **0.0313** [0.0086, 0.1070] — 2/64 | 0.0469 [0.0161, 0.1290] — 3/64 | 0.0391 [0.0168, 0.0882] | 0.492 |
| **padded** | **0.0313** [0.0086, 0.1070] — 2/64 | 0.0156 [0.0028, 0.0833] — 1/64 | 0.0234 [0.0080, 0.0666] | 0.508 |

Accept rates sit within 0.008 of 0.5 in every arm: no arm collapsed into always-accepting or
always-rejecting, which is the degenerate failure that would have made β and α uninterpretable.

**The 19 errors across 512 calls fall on 10 distinct items.** 118 of the 128 items are answered
correctly in all four arms. Everything this experiment could possibly measure lives in those 10
items — and 4 verdicts are not reproducible (§3). One item (mutant 1552) is wrong in three of
the four arms; the rest are wrong in one or two.

### Input tokens per arm `[measured]`

| arm | input tokens / call | vs minimal | s / call | total input tokens |
|---|---|---|---|---|
| minimal | **921** (851–1,017) | 1.0× | 3.79 | 117,833 |
| relevant | **1,601** (885–4,762) | 1.74× | 4.02 | 204,962 |
| full | **21,479** (21,409–21,579) | 23.3× | 4.56 | 2,749,319 |
| padded | **41,686** (41,616–41,786) | **45.3×** | 5.21 | 5,335,815 |

Latency is almost flat — 3.8 s to 5.2 s across a 45× context range. **Context volume is a
token-cost variable on this task, not a latency variable, and on the evidence of §2 not an
accuracy variable either.**

---

## 3. The determinism control — the finding that governs all the others `[measured]`

Thirty-two items (a stride across the sorted item list, so 16 defect and 16 fix) were re-run in
all four arms: 128 calls, same prompts, same invocation.

```
run 1: 512 calls   run 2: 128   overlap: 128
verdict disagreements across the overlap: 4
agreement: 0.9688
  minimal: 2/32 disagree
  padded: 1/32 disagree
  relevant: 1/32 disagree
```

`compare_runs.py` exits 1 on any disagreement, so this cannot be piped past.

**3.1% of verdicts are not reproducible.** Three of the four flips are on `fix` items; item
`fix:1043` flipped in two different arms, so it is a genuinely borderline change rather than a
random-seed artefact.

The largest β gap between any two arms is **1 item in 64 = 1.6 percentage points**. The noise
floor is **twice that**. Re-running the whole census would be expected to move each arm's error
count by ±2 items — more than the entire spread between the arms. This is the answer to "is the
difference real": *the experiment cannot distinguish the arms from re-running one arm twice.*

---

## 4. Two measurement facts the pre-registration did not anticipate `[measured]`

**(a) The default CLI invocation carries 75,285 input tokens before the prompt begins.** A bare
`claude -p "reply with the single word: ok"` on this machine spent 75,285 tokens (one
measurement, 20 Aug 2026) on tool
schemas, `CLAUDE.md`, skills, plugins and MCP server definitions. That is 82× the entire
`minimal` arm prompt and would have swamped the variable under test. Every call in this
experiment therefore ran with `--tools "" --safe-mode --strict-mcp-config
--no-session-persistence` and an explicit `--system-prompt`, from a scratch directory outside
the repository. Fixed overhead measured after stripping: **~600 tokens**. (This is the same
class of observation as EXP-57's own motivation — Grok's 33,344 tokens to answer "ok" — and it
is worse here by a factor of two.)

**(b) The CLI silently bills a second model on the same prompt.** `modelUsage` shows
`claude-haiku-4-5` consuming input tokens alongside Sonnet: **0 per call on `minimal` and
`relevant`, 2,465 on `full`, 20,697 on `padded`** — 2,964,703 tokens over the census, 35% on top
of the arm's own figure. It contributes nothing to the answer. Counting only the answering
model, `padded` costs 45.3× `minimal`; counting what is actually billed, **67.7×**. A
pre-registration that says "record input tokens per call" is under-specified for a harness that
runs more than one model per call.

**(c) 125 of the first 512 calls returned a verdict and no usage block at all.** Under sustained
concurrency (6 workers) the CLI began returning results with `usage` absent — clustered in the
last 30% of the run, alongside one hard rate-limit error, and ~3× slower than the healthy calls (12.3 s against 4.3 s).
Recorded as zeros, they would have reported the `padded` arm at 6,893 tokens per call instead of
41,686 — a sixfold understatement of the experiment's headline cost. The instrument now records
`usage_reported` per call and `--retry` re-runs anything that failed, went unadjudicated, or
reported no usage; concurrency was cut to 3 and all 125 were re-run. **This is a verify-by-
artefact catch: every one of those calls exited fine and returned the right kind of answer.**

---

## 5. Which stopping rule fired

Quoted from `docs/10-research/experiment-register.md` → EXP-57, unaltered:

> - If **all four arms overlap** $\implies$ **insufficient power**; report the intervals and do
>   not narrate a trend across overlapping bars. `[asserted]`

**This rule fired.** All six pairwise β difference intervals span zero, as do all six on α and
all six on the error rate. All eighteen are tabulated in §5.2; §5.3 is the sharper read of the
same data.

The rule on padding also resolved, in the negative:

> - If **padded is worse than full** $\implies$ irrelevant context actively degrades the answer.
>   That is context poisoning with an interval on it, and it makes retrieval quality a
>   correctness concern rather than a cost one. `[asserted]`

**Did not fire.** `padded` has the *lowest* error rate of the four arms (0.0234 vs `full`'s
0.0391), the difference interval is [−0.0330, +0.0671], and the two arms disagree on 2 of 128
items. **No measured context poisoning at 41,686 tokens of plausible irrelevant code**, on this
task, at this n. That is a negative result on a real hypothesis, not an absence of evidence, and
it should be read with §6's ceiling firmly attached.

The other two rules did not fire and could not, because the first branch of the pre-registered
order is unconditional once all intervals overlap:

> - If **minimal ≈ full** $\implies$ context volume is cost without benefit on this task […]
> - If **full materially beats minimal** $\implies$ **the premise is wrong**: send everything,
>   and build nothing. This outcome contradicts what Joe asked for and must be reported as
>   loudly as the other. `[asserted]`

**Reporting the adverse rule as loudly as required: it did not fire, and it did not come close.**
`full`'s β is 0.0313 against `minimal`'s 0.0469 — the sign favours more context, by one item in
64, on an interval of [−0.0661, +0.1008] that is six times wider than the gap. There is no
evidence here for "send everything and build nothing". There is also no evidence *against* it
beyond a 10-percentage-point resolution. The stopping rule's own test for the adverse outcome
was implemented and is exercised by `test_exp57.py`, so this is a branch that could have fired
and did not, rather than a branch that was never wired up.

### 5.2 Pairwise differences — the pre-registered intervals

Newcombe hybrid-score 95% intervals on the difference of two proportions.

| pair | Δβ | interval | Δ error rate | interval |
|---|---|---|---|---|
| minimal − relevant | +0.0000 | [−0.0877, +0.0877] | −0.0078 | [−0.0640, +0.0474] |
| minimal − full | +0.0156 | [−0.0661, +0.1008] | +0.0000 | [−0.0539, +0.0539] |
| minimal − padded | +0.0156 | [−0.0661, +0.1008] | +0.0156 | [−0.0330, +0.0671] |
| relevant − full | +0.0156 | [−0.0661, +0.1008] | +0.0078 | [−0.0474, +0.0640] |
| relevant − padded | +0.0156 | [−0.0661, +0.1008] | +0.0234 | [−0.0266, +0.0773] |
| full − padded | +0.0000 | [−0.0790, +0.0790] | +0.0156 | [−0.0330, +0.0671] |

α, same method: minimal−relevant −0.0156 [−0.1008, +0.0661]; minimal−full −0.0156 [−0.1008,
+0.0661]; minimal−padded +0.0156 [−0.0558, +0.0924]; relevant−full +0.0000 [−0.0877, +0.0877];
relevant−padded +0.0312 [−0.0431, +0.1144]; full−padded +0.0312 [−0.0431, +0.1144].

**Eighteen intervals, eighteen spanning zero.**

### 5.3 Item-level agreement — the sharper read `[measured]`

Every arm answers the *same* 128 items, so the arms are **paired** and the Newcombe interval
above — which assumes two independent samples — is conservative. Equal error rates could still
hide two arms disagreeing on half the corpus and cancelling out. They do not:

| pair | verdicts that differ | wrong in A only | wrong in B only | exact McNemar p |
|---|---|---|---|---|
| minimal vs relevant | 3 / 128 | 1 | 2 | 1.000 |
| **minimal vs full** | **8 / 128** | **4** | **4** | **1.000** |
| minimal vs padded | 6 / 128 | 4 | 2 | 0.688 |
| relevant vs full | 9 / 128 | 5 | 4 | 1.000 |
| relevant vs padded | 9 / 128 | 6 | 3 | 0.508 |
| full vs padded | 2 / 128 | 2 | 0 | 0.500 |

The decisive comparison, minimal vs full, is **perfectly symmetric**: 8 items where the two arms
give different verdicts, 4 where minimal is the one that is wrong and 4 where full is. Adding
21,479 tokens of source tree changes the answer on 6% of items and improves it on none of them
net. At 8 discordant pairs the exact test cannot resolve anything finer than about a 3:1 split,
which is itself a statement about the design (§6).

---

## 6. What is wrong with the pre-registration `[asserted]`

The brief asked for this and the design was not altered to accommodate any of it. Every item
below was settled in code, with its reasoning, before the first model call.

**(a) It fixes no sample size, and it offers "insufficient power" as a verdict.** EXP-52's
registration ends with *"If fewer than 60 adjudicable items complete in any arm, the verdict is
insufficient evidence"*; EXP-57 has no equivalent. An experiment that can declare its own null
by being small is not pre-registered against that null. Fixed here as `N_DEFECT = N_FIX = 64`
before the run. **Falsifier:** if a re-run at n=64 produced non-overlapping intervals, the
choice was adequate and this criticism is wrong.

**(b) "materially beats" and "≈" are undefined.** Both decide stopping rules. Operationalised in
`decide()` before the run: two arms *differ* when the Newcombe 95% interval on the difference
excludes zero; one *materially beats* the other when it differs **and** the point difference is
at least 0.10. **Reversal:** change `MATERIAL_DELTA` and re-run `run_exp57.py` — the analysis
re-derives from the checkpoint without new calls.

**(c) It has no floor-effect guard, and the floor is what it hit.** The model errs on 2.3%–4.7%
of items *with the diff alone*. There is almost nothing for extra context to fix. A
registration for a difference experiment should fix the band of baseline error rates in which
the comparison is informative, and require a pilot to check the minimal arm is not already
saturated. To resolve the observed 1.6-point β gap at 80% power would need roughly **2,400
items per class per arm** — 4,800 calls and ~200M input tokens in the padded arm alone. **This design cannot ever
resolve a difference of the size it produced**, and that is a property of the design, not of the
run.

**(d) "the interval on each pairwise difference" does not say paired or unpaired.** All four
arms answer the same items. The pre-registered unpaired interval is reported in §5.2 as
specified; the paired discordance analysis in §5.3 is supplementary and is the stronger
evidence.

**(e) The `relevant` arm is half-degenerate on this corpus, and the two choices interact.** For
**65 of 128 items (51%) no test in the suite names the changed code**, so the arm shows the
model "No test in the suite names the changed code" and is otherwise identical to `minimal`.
This is not a defect in the arm — it is the corpus telling the truth. The corpus is made of
mutants that *survived pytest*, and code with no test naming it is exactly where such mutants
live. But the registration chose a pytest-survivor corpus and an arm defined as "the tests that
cover it" without noticing that the first choice guts the second. `relevant` should be read as a
treatment diluted by half. **Not changed:** widening the match to file-level tests would have
put tests that demonstrably do *not* cover the line into the arm, which is padding wearing a
relevance label.

**(f) "input tokens per call" is under-specified for this harness** — see §4(b). Recorded
separately as `auxiliary_model_input_tokens` rather than folded in, so the pre-registered figure
stays the pre-registered figure.

**(g) β here is not the project's β, and the register does not say so.** The project's β is the
rate at which *automated checks* accept a bad artefact. This measures a *model reviewer's*
false-accept rate. A model reviewer is a check, so the extension is legitimate, but the two
numbers are not comparable and must not be quoted against each other. EXP-47's composite
$\hat\beta = 0.3132$ and this run's $\hat\beta = 0.0313$ are different quantities measured on
the same artefacts.

---

## 7. What this decides, and what it does not

**Decides, on this task:** context volume is a cost variable. Going from a one-line diff to the
whole source tree multiplies input tokens by 23×, and by 45× with irrelevant material on top,
while moving β and α by less than the experiment's own reproducibility noise. If the effect of
just-in-time context engineering on *accuracy* is what would justify building it, this run
supplies no such justification; if the effect on *cost* is enough, a 45× token ratio at flat
accuracy is a large lever. `[measured]` for the rates and tokens, `[asserted]` for the reading.

**Does not decide:**

- **Whether the effect holds for tasks whose difficulty scales with context** — the register's
  own caveat, and it is the honest reason this is a first step. A one-line diff is answerable
  from a one-line diff. The interesting cases are the ones where the answer depends on a caller
  three modules away, and this corpus contains none of them by construction.
- **Anything at a resolution finer than about 9 percentage points of β** (§6c).
- **Anything about other models.** One model, by design — the variable under test was context,
  not model — and therefore one model's answer.
- **Anything about near-miss padding** (§1) or about volume-only padding.
- **Whether the 3.1% irreproducibility is a property of the model or of the harness.** The
  control varies both together. Separating them needs a fixed-seed or temperature-zero path,
  which `claude -p` does not expose.

---

## 8. Reproducing

```
cd C:/Users/jpbpr/Repositories/consilient-clone-checks
python -m pytest docs/10-research/experiments/exp57/test_exp57.py -q     # 28 passed
python docs/10-research/experiments/exp57/run_exp57.py                   # census, resumable
python docs/10-research/experiments/exp57/run_exp57.py --retry           # re-run unmeasured calls
python docs/10-research/experiments/exp57/run_exp57.py --control         # determinism control
python docs/10-research/experiments/exp57/compare_runs.py                # exits 1 on disagreement
```

Re-running `run_exp57.py` with a complete checkpoint makes no calls and re-derives the analysis
in under a second, so the statistics can be revised without re-spending the census.

**Prove the checks can fail.** Five defects were injected into `run_exp57.py` in a throwaway
copy — a `parse_verdict` that scores ambiguous replies, a disabled corpus-arithmetic guard, a
`MATERIAL_DELTA` of 99, a `full` arm rendering the pristine tree, and a `build_pool` that skips
its uniqueness check. **All five were killed by `test_exp57.py`.** Two of them survived the
first version of the suite; both are named in §1 and §6.

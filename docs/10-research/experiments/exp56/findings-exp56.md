# EXP-56 findings — stopped before scoring because the registered corpus is not committed

**Date:** 20 August 2026
**Status:** `[measured]` for the corpus and Cursor preflight, `[algebra]` for the interval and
stopping-rule checks, and `[asserted]` for the interpretation and repair.
**Verdict:** **stopped before scored calls.** `[measured]` No registered stopping rule was
evaluable. `[algebra]`
**Model calls:** **1 unscored Cursor identity probe; 0 scored calls.** No metered provider was
used. `[measured]`

This experiment could only have decided accept/reject performance on small mutated Python source
regions with covering tests. It could not have decided anything about long-horizon planning,
open-ended design or multi-file refactoring. [asserted]

## Headline result

The prerequisite in the brief — sample survivors and killed mutants from EXP-47's committed
corpus — cannot be executed from the committed result. `results-exp47.json` contains aggregate
counts and 586 item-level non-equivalent survivors, but contains **zero item-level killed rows,
zero item-level equivalent rows and no source snapshot identity**. [measured]

| EXP-47 class | aggregate count | item rows committed |
|---|---:|---:|
| killed by the composite verifier | 1,285 | **0** |
| survived, semantically equivalent | 60 | **0** |
| survived, non-equivalent | 586 | **586** |
| **total** | **1,931** | **586** |

The killed count is `1,931 - 646 = 1,285`; the 646 composite survivors divide into 60 equivalent
and 586 non-equivalent survivors. [algebra] The result-writing path emits only the final
`weakest_guards` list, which is the 586 non-equivalent survivors; the other item identities and
their full mutated source were discarded. [measured]

EXP-47 also omitted the source commit and source/test hashes. Selecting any historical snapshot
now and rerunning the discarded outcomes would therefore be a post hoc amendment not named by
EXP-47 or EXP-56. [asserted]

The option not taken was to use the 586 survivors alone. That would violate the required
survivor/killed mixture and change the estimand from the registered mutation corpus to known blind
spots in the existing verifier. [asserted] The other option not taken was to infer killed IDs as
the complement of survivor IDs: the exact 60 equivalent IDs are also absent, so that complement
cannot implement the mandatory exclusion. [measured]

The executable gate is in `run_exp56.py`; the primary and independent control results are
byte-identical with SHA-256
`1fa8e8b28513ee3fb2700c3a062b99a5c87aa51f2223f67002774cf8a9265ae5`. [measured]

## Requested statistics

No per-model β, α, Wilson interval, agreement matrix, variance or hindsight-optimal ceiling exists,
because no scored model saw an item. [measured] Reporting values by requested model string would
therefore be fabrication, not an estimate. [asserted]

No stopping rule from the register fired. In particular, neither of the registered ceiling rules,
the β-span rule nor the refusal rule can be evaluated with zero scored calls. [algebra] The stop
comes from the dispatch brief's prior instruction to stop rather than silently change a design
after discovering a problem with it. [asserted]

`unidentified_served_model_calls = 1`. Before scoring, one flat-fee Cursor call tested the identity
surface with requested ID `gemini-3.7-flash-low`; the stream init event reported the display name
`Gemini 3.7 Flash Low`, and the response was `identity-probe-ok`. [measured] The runtime did not
report served-weight identity, so the call is recorded as `unknown:not-reported-by-runtime` and is
excluded from comparison as the brief requires. [measured] The exact prompt, request/session IDs,
usage and exclusion are preserved in `identity-probe-exp56.json`. [measured]

## Cursor preflight

Cursor CLI `2026.08.11-e8db854` listed 204 entries, of which one was `auto`; the live surface has
203 explicit request IDs, not 204 explicit models. [measured] The following 16 request IDs were
fixed and verified from that live list before any scored call: [measured]

| vendor family | verified request IDs |
|---|---|
| Anthropic | `claude-sonnet-5-low`; `claude-opus-5-thinking-high`; `claude-fable-5-thinking-max`; `claude-opus-4-8-medium` |
| OpenAI | `gpt-5.6-sol-none`; `gpt-5.6-terra-medium`; `gpt-5.6-luna-high`; `gpt-5.4-mini-xhigh` |
| Google | `gemini-3.7-flash-low`; `gemini-3.6-flash-high`; `gemini-3.1-pro` |
| xAI | `cursor-grok-4.6-low`; `cursor-grok-4.5-high` |
| Moonshot | `kimi-k3-max`; `kimi-k2.7-code` |
| Zhipu | `glm-5.2-high` |

These are request IDs and model-list display labels, not evidence of distinct served weights.
[measured] Cursor's text list cannot answer whether two IDs share weights, and the registered
requirement to establish same served weights is not operationalised by the stated command.
[asserted]

## Problems in the pre-registration

1. **The corpus prerequisite is false.** The committed EXP-47 result is not an item-level corpus
   from which the specified strata can be sampled. [measured]
2. **The precision calculation uses the wrong denominator.** β has 60 mutated trials and α has 60
   control trials, not 120 trials each. At β = 0.30, 18/60 has Wilson 95% interval
   `[0.1990, 0.4251]`, half-width 0.1131; 36/120 has `[0.2253, 0.3872]`, half-width 0.0809.
   [algebra] The registered claim of approximately ±0.09 therefore overstates precision for each
   error rate. [asserted]
3. **The common item matrix is unstated.** Pairwise agreement and a per-item hindsight ceiling are
   defined only when every model sees the same 120 items. [algebra]
4. **Two stopping rules can contradict.** Models can have a β span below 10 percentage points while
   making errors on different items, so the hindsight-optimal ceiling can still beat every single
   model. Equal marginal error rates do not imply equal error sets. [algebra] The rule declaring
   routing moot “regardless of the ceiling” is therefore not entailed by its premise. [asserted]
5. **“Best single model” is undefined.** The registration defines β and α separately but does not
   define the scalar quality measure used to select one best model or compare it with the ceiling.
   [measured]
6. **Missing outcomes are under-specified.** More than 20% refusals makes a model unusable, but the
   registration does not say how fewer refusals affect denominators, pairwise agreement or the
   ceiling. [measured]
7. **The named seam does not exist yet.** EXP-56 says it reuses EXP-08's critic seam while EXP-08 is
   registered as blocked on the critic tier. [measured]
8. **The served-weights falsifier is ill-posed.** The list counts effort parameterisations as model
   IDs while asking whether two names resolve to the same weights. Effort variants can share base
   weights by construction, and Cursor exposes request IDs/display labels rather than weight
   identity. [asserted]
9. **The interval comparison is not a paired selection-aware test.** The ceiling and every model
   use the same items, while “best” is selected from the same 16-model sample. Overlap between
   separate Wilson intervals is not an interval for the paired ceiling-minus-selected-best
   difference, and overlapping marginal 95% intervals do not entail no improvement. [algebra]
10. **The mutant estimand is under-specified.** A survivor/killed stratified sample estimates the
    chosen sample mixture unless its allocation matches the 586:1,285 non-equivalent corpus ratio
    or the analysis reweights strata. [algebra] Weighted stratified inference would not use the
    registered unweighted Wilson calculation. [asserted]

## Repair, reversal and falsifier

**Repair:** amend and re-register EXP-56 before any scored calls. First rerun EXP-47 against an explicitly
pinned source/test tree and persist one row for every mutation, including its outcome,
equivalence classification, mutated source region, mapped covering-test text and input hashes.
Persist a reproducible mutation receipt and add a verifier tying every row to that pinned tree.
Then freeze the shared 120-item manifest, exact prompt, response parser, refusal denominators,
target population, stratum allocation/weights, interval method, scalar ceiling metric and paired,
selection-aware comparison method. [asserted]

**Reversal:** after this result is committed, run
`git revert (git log --format=%H --grep='Stop EXP-56 before scored calls on corpus provenance' -1)`
from PowerShell. [asserted]

**Falsifier:** a pre-scoring committed artefact containing all 1,931 EXP-47 item rows, the exact
60 equivalent identities, all killed outcomes, a verifiable source/test snapshot and a reproducible
mutation receipt accepted by an independent verifier would falsify the corpus stop. [asserted] It
would not repair the other preregistration defects; those still need an amendment before scoring.
[asserted]

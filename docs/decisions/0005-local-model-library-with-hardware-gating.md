# 0005. Ship a local model library with hardware-gated downloads

- **Status:** SUPERSEDED IN PART — see "Update: wrap, don't build"
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Inquiry tier reached:** T1 ground
- **Executable model:** none yet — but see "Enforcement": the feasibility predictor itself
  must be validated empirically before shipping, which makes this a T3 candidate.

## Update: wrap, don't build (Q20 answered, 2026-08-19)

`[cited]` The build-vs-wrap question was researched and the answer is wrap.

- **LM Studio already ships this exact UX** — a model browser filtered to compatible GGUF,
  with per-model status (fully supports / partially supports / likely won't support). It
  shows incompatible models with a label rather than hiding them: the reveal-toggle in the
  inverse default.
- **LLM Checker** (open source, ~1.7k stars) — CLI, hardware-calibrated memory estimation,
  200+ models, scoring across quality / speed / fit / context, Ollama integration.
- **Ollama does not have it.** An unmerged proposal (issue #14771, Mar 2026) adds
  `ollama fit` with a 165-entry catalogue and 4-component scoring.
- A browser-based checker (llmconfigurator.com) also exists.

**Revised decision: do not build a model library.** Wrap LM Studio or LLM Checker for the
fitting question and spend the effort on Q22 — *should* you route here, given the
repository's measured β — which is the part nobody has.

### Banding simplification

`[cited]` Partial fit with CPU offload runs **5–30× slower**; the guidance is uniform that
this is a cliff, not a gradient. So the Comfortable / Tight boundary is simply **"fully
GPU-resident at the harness's default context"**, not an invented tokens-per-second floor.
That removes the need to pick a throughput threshold, which was the weakest part of the
original proposal.

### What survives

The requirement as Joe stated it — autodetect, default to feasible-only, reveal on request,
block download and local execution of infeasible models while keeping them usable via remote
inference — all survives. It is now satisfied by wrapping rather than building, and the
enforcement rules below still apply to the harness's own execution path.

---

## Context

The cascade (`0002`) needs a cheap tier. The cheapest tier available to a developer is a
model running on their own machine, and it is free at the margin. But the practical barrier
to local inference is not capability — it is that getting a model running is fiddly, and the
most common failure is a user downloading 20 GB and discovering it will not fit, or that it
fits but produces four tokens a second.

Separately, one stated commercial direction is a simplified distribution that "inferences
open source models directly so developers avoid configuring their own credentials". This
ADR is the open-source half of that: the credential-free path is a model that runs locally.

## Decision

Ship a **model library** in the harness that:

1. **Autodetects machine specification** — GPU model and VRAM, system RAM, free disk,
   accelerator backend (CUDA / ROCm / Metal / CPU), and unified-vs-discrete memory.
2. **Shows only models the machine can reliably run, by default.** "Reliably" is defined
   operationally in the section below, not by a spec-sheet lookup.
3. **Lets users reveal the rest.** An explicit "show models this machine cannot run" toggle.
   Nothing is hidden permanently; the default is simply not a list of disappointments.
4. **Blocks download and local execution of revealed-but-infeasible models.** These remain
   selectable as *remote* inference targets (OpenRouter or equivalent) so the model is still
   usable, just not locally.
5. **Never redistributes weights.** The library resolves to upstream sources; the user
   accepts upstream licence terms directly with the upstream provider.

## "Reliably run" must be measured, not predicted

This is the load-bearing design point, and it follows the project's standing rule
(`AGENTS.md` §8): run it, don't reason about it.

A static prediction from specs is achievable but fragile. The first-order arithmetic is:

```
VRAM_required ≈ weights + KV_cache + activations + runtime_overhead

weights     ≈ params × bits/8 × (1 + quant_metadata_overhead)
KV_cache    ≈ 2 × layers × kv_heads × head_dim × bytes × context_length × batch
```

Every term has a trap. Grouped-query and latent attention change `kv_heads` by an order of
magnitude, so KV cache is frequently the binding constraint rather than weights — a 32B at
4-bit with a long context will OOM before a 14B at 8-bit does. MoE models size on *total*
params for memory but *active* params for throughput, so a 30B-A3B fits like a 30B and runs
like a 3B. The desktop compositor takes VRAM. Apple silicon has unified memory, so the whole
concept of "VRAM" differs. Engine choice (llama.cpp / vLLM / Ollama / MLX) changes all of it.

**Therefore: predict to shortlist, measure to confirm.** The predictor produces a candidate
set; a short on-device calibration run produces the verdict. Store the result. A machine is
characterised once, not on every launch.

Proposed feasibility bands, to be validated:

| Band | Meaning |
|---|---|
| **Comfortable** | Measured on this machine at ≥ X tok/s at the harness's default context, with headroom |
| **Tight** | Runs, but near the memory ceiling or below the usable throughput floor |
| **Predicted-only** | Arithmetic says yes; never measured here |
| **Infeasible** | Arithmetic says no, or a calibration run failed |

Default view shows Comfortable. Tight is shown with a warning. Predicted-only and
Infeasible are behind the reveal toggle.

## Evidence

- `[cited]` `docs/10-research/local-experimentation.md` — on a 32 GB card, a 30B-A3B-class
  MoE at 4-bit is comfortable, a 30B dense at 4-bit is tight, and long context is
  KV-bound rather than weight-bound. The bands above exist because these differ.
- `[algebra]` The KV-cache formula above; the dominance of KV over weights at long context.
- `[asserted]` The dominant failure mode for new local-inference users is a wasted large
  download. This is widely reported but has not been measured by us.

## Evidence against

- `[simulated]` **A local cheap tier is a wide capability gap, and wide gaps demand
  near-perfect verification.** `../10-research/findings.md` §2: at a 0.42 gap, β\* is 0.033
  — tests may miss at most ~3% of bugs before routing to local costs you quality. So for
  many users the honest answer will be *"you can run this model, and you should not route to
  it"*. The library must say that, which makes it less appealing than a plain download
  button and is the right thing to do.
- `[asserted]` Calibration runs cost the user time on first use. A 20 GB download followed by
  a benchmark is a slow first-run experience. Predicting well enough to skip calibration is
  tempting and probably wrong.
- `[asserted]` This is a substantial feature for a pre-v0 project with one maintainer. It may
  belong in v1. See Q23.

## Consequences

**Positive.** Removes the single largest friction in local inference. Gives the cascade a
free cheap tier. Directly serves the credential-free story. Produces per-machine performance
data that feeds routing decisions.

**Negative.** Cross-platform hardware detection is a permanent maintenance surface
(nvidia-smi, ROCm, Metal, driver versions, WSL). Model metadata goes stale as new
architectures land. Owning the download path means owning download failures.

**Neutral but load-bearing.** Once the harness knows machine capability *and* repo β, it can
answer "should I route locally?" rather than just "can I run this?". That composition is
more valuable than either half.

## Enforcement

- Check: the local execution path must refuse any model not marked Comfortable or Tight
  **for this machine**, enforced at the engine boundary, not in the UI. A UI-only gate is
  not a gate. Same commit as the feature (invariant I1).
- Check: weights are never served from project-controlled infrastructure. A test asserts
  every catalogue entry resolves to a third-party URL.
- Check: `safetensors` or equivalent only. No pickle-format weights, ever — they are
  arbitrary code execution. Hash verification on download, failing closed.
- Validation: the feasibility predictor's accuracy is itself a measurable quantity. Track
  predicted-vs-measured across machines; a predictor that is wrong more than N% of the time
  is a bug, and the threshold goes in this ADR once we have data.

## What would overturn this

- Ollama, LM Studio or an equivalent ships hardware-gated discovery good enough that
  wrapping it beats building it. **Check this before starting** — it is the likeliest
  outcome and the cheapest to discover.
- Calibration proves too slow or too unreliable to be a gate, forcing a pure-prediction
  design.
- Local models prove unroutable in practice because of the β\* constraint above, reducing
  the library to a nice-to-have rather than a cascade component.

## Open legal points

Flagged for the same review as `docs/legal/README.md`:

- **Gated and acceptance-required licences.** Several major open-weight families require
  accepting terms with the provider, and some Hugging Face repos are access-gated. The
  library must route the user to accept upstream, must not proxy or cache weights, and must
  not automate acceptance on the user's behalf.
- **Licence surfacing.** Each catalogue entry should display the model's licence and any
  use restrictions before download. Some open-weight licences carry acceptable-use terms
  that are not OSI-open.
- **Distribution status.** Confirm that pointing at third-party weights, without hosting or
  mirroring, does not make the project a distributor for the purposes of those licences or
  of the EU AI Act's GPAI provisions.

## Publication candidate?

**Possibly.** "Predicted vs measured local-inference feasibility across N consumer machines"
is a small, genuinely useful dataset that does not appear to exist publicly, and Hugging Face
is the natural venue for it (see `../publications/README.md`, which notes that a
well-carded dataset is often used more than the paper describing it). Only after we have
real data across more than one machine.

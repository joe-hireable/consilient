« CANDIDATE LOCAL MODELS FOR AGENTIC CODING — RTX 5090 32 GB, AUGUST 2026 »

Zero spend. Nothing downloaded. Nothing run on the GPU. All specifications below are public
registry and model-card metadata from ollama.com and huggingface.co, fetched 20 Aug 2026.
Every parameter count, context length, licence and size in the table is **[cited] and
vendor-sourced**. Nothing here is [measured] except the two rows marked INSTALLED, which carry
tonight's numbers.

---

## 0. The fit rule this table uses, and why it is tighter than the repo's

The only VRAM measurement that exists is gemma4:31b. `ollama list` reports it at **19 GB**
(decimal, = 18,120 MiB) and it was measured at **29,442 MiB in use, 3,180 MiB free**.

- Ratio = 29,442 / 18,120 = **1.63x**, not 1.5x.
- Budget = 32,607 MiB total − ~1,000 MiB for the display = ~31,600 MiB usable.
- Ceiling = 31,600 / 1.63 = **~19,400 MiB ≈ 20.3 GB on disk (decimal)**.

So the practical bands are:

| On-disk size | Verdict |
|---|---|
| ≤ 18 GB | fits with ~4 GB of headroom for KV |
| 19–20 GB | fits, as tight as gemma4:31b already is |
| ≥ 21 GB | does not fit fully; spills to system RAM |

**The load-bearing caveat:** that 29,442 MiB was almost certainly measured at Ollama's default
context, not at an agentic context. KV cache is additive and grows with the task. A model that
"fits" at 19 GB on disk may not fit while holding 64K tokens of repository context. Until KV is
measured at a realistic context, **treat the 19–20 GB band as unfit for agentic work and the
≤18 GB band as the real shortlist.** This is the single most consequential thing in this document
and it is not in the current fit table.

---

## 1. The table, ordered by plausibility for this card

`MoE` column is the flag the brief asked to be explicit about. `Fit` uses the bands above.

| # | Ollama id | HuggingFace id | Params (total / active) | Arch | MoE? | Native ctx | Quants on disk | Licence | Released | Fit | Note — why it is or is not a serious candidate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `muse-glimmer:30b` | `meta-models/Muse-Glimmer-30B` | 29.78B / 29.78B | dense, sliding-window + full attn, 52 layers, perception encoder | **No** | 128K | q4_K_M 18 GB · nvfp4 17 GB · q8_0 31 GB · bf16 57 GB | Apache-2.0 | 2026-08-09 | ✅ comfortable | **Top pick.** The only ≤18 GB model that is *architecturally the same shape* as the one thing measured to work here (dense ~30B). Meta built it explicitly for "always-on local agents… multi-step reasoning, reliable tool use, failure recovery". Apache-2.0, eleven days old. Against it: 128K context is the shortest of the serious candidates, and Meta's agentic claims are vendor benchmarks only. |
| 2 | `glm-4.7-flash` | `zai-org/GLM-4.7-Flash` | 31.2B / ~3B (A3B; 4 experts/token in config) | `Glm4MoeLiteForCausalLM` | **YES** | 198K | q4_K_M 19 GB · q8_0 32 GB · bf16 60 GB | MIT | 2026-01-19 | ⚠️ tight (19 GB) | The most *mature* MoE candidate — seven months in the wild, 1.5M pulls, so harness quirks are likely already shaken out. MIT is the cleanest licence in the table. Against it: seven months is old in this space, and 19 GB puts it in the same squeeze gemma4:31b is already in. |
| 3 | `north-mini-code-1.0` | `CohereLabs/North-Mini-Code-1.0` | 30B / 3B (128 experts, 8 active) | sparse MoE, 3:1 sliding:global attn, SwiGLU | **YES** | 488K | q4_K_M 19 GB · q8_0 32 GB · nvfp4 20 GB · bf16 61 GB | Apache-2.0 + Cohere AUP | 2026-06-05 | ⚠️ tight (19 GB) | The only candidate whose stated purpose is *exactly* the task: "Cohere's first model for developers… built for agentic software engineering". 488K context is the longest here and the 3:1 sliding:global ratio means most of it is cheap. Against it: an acceptable-use policy rides on top of Apache-2.0, and Cohere has no track record at this size. |
| 4 | `laguna-xs-2.1` | `poolside/Laguna-XS-2.1` | 33B / 3B (256 experts + 1 shared, 8 active) | MoE, 40 layers (10 global / 30 sliding-window attn) | **YES** | 262,144 | nvfp4 19 GB · q4_K_M 20 GB · q8_0 36 GB · mxfp8 39 GB · bf16 67 GB | OpenMDW-1.1 | 2026-06-20 | ⚠️ tight (19–20 GB) | Poolside built this for "agentic coding and long-horizon work **on a local machine**" — the most on-brief design intent of anything listed. Richest quantisation ladder, including a 19 GB NVFP4 that suits Blackwell. Against it: OpenMDW-1.1 is an unusual licence that needs reading before this ships in an open-source harness's default library, and 33B total is the largest thing that will fit at all. |
| 5 | `qwen3.8:27b` | `Qwen/Qwen3.8-27B` | 27.78B / 27.78B | dense, hybrid linear+full attn (3:1), 64 layers, MTP head | **No** | 262,144 | q4_K_M 18 GB · nvfp4 18 GB · q8_0 30 GB · mxfp8 32 GB · bf16 56 GB | Apache-2.0 | 2026-08-05 | ✅ comfortable | Newest Qwen at a size that fits; "substantial gains across coding… and long-horizon agentic tasks". Dense, so it is a like-for-like successor to the shape that worked. Against it: it carries a vision tower this workload does not need but must still hold in VRAM, and its KV cost is ~64 KB/token — the highest of the shortlist, ~3x Qwen3.6-35B-A3B (see §3). |
| 6 | `gemma4:26b` (`26b-a4b`) | `google/gemma-4-26B-A4B-it` | 25.2B / 3.8B (128 experts, 8 active, 30 layers) | MoE | **YES** | 256K | qat 16 GB · q4_K_M 18 GB · q8_0 28 GB · bf16 52 GB | Gemma Terms of Use *(not verified this session — [asserted])* | 2026-03-11 | ✅ comfortable (16 GB QAT) | **The cleanest experiment in the table, and not because it is the best model.** Same vendor, same tokeniser, same training recipe and same generation as the installed gemma4:31b — so a 26b-a4b vs 31b run isolates *MoE vs dense* with almost every other variable held. The 16 GB QAT build is the roomiest serious option. Against it: it is precisely *not* a different class of facts from gemma4:31b, and Google's licence is not OSI-open. |
| 7 | `qwen3-coder:30b` | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 30B / 3.3B | MoE | **YES** | 256K (→1M by extrapolation) | q4_K_M 19 GB | Apache-2.0 | ~mid-2025 *(Ollama: "11 months ago")* | ⚠️ tight (19 GB) | The incumbent. Whatever else is true, this is the model the outside world has actually been driving agent loops with for a year, so it is the honest baseline any new candidate must beat. Against it: it is a year old, non-thinking, and superseded within its own family twice. |
| 8 | `devstral-small-2:24b` | `mistralai/Devstral-Small-2-24B-Instruct-2512` | 24B / 24B | dense | **No** | 384K | 15 GB (default) | Apache-2.0 | 2025-11-28 | ✅ roomiest | **Fits with the largest KV budget of any serious candidate** — 15 GB leaves ~7 GB for context, which is the difference between "fits" and "fits while doing the job". Purpose-built: "excels at using tools to explore codebases, editing multiple files and power software engineering agents". Against it: nine months old, and its 65.8% SWE-Bench Verified figure is **[cited] and vendor-sourced** — the single-leaderboard warning applies in full. |
| 9 | `granite4.1:30b` | `ibm-granite/granite-4.1-30b` | 28.9B / 28.9B | dense decoder-only | **No** | **128K or 512K — vendor contradicts itself** | q4_K_M 17 GB · q8_0 ~31 GB | Apache-2.0 | 2026-04 | ✅ comfortable | Real tool-use and structured-JSON training, Apache-2.0, IBM's enterprise QA behind it, and 17 GB is a genuinely comfortable fit. Against it: nothing in its card claims *agentic coding* — it claims tool use and RAG, which is a weaker property. And its own vendor lists 128K on the family page and 512K on the model page; that must be resolved before it is trusted for repo-scale work. |
| 10 | `gemma4:31b` | `google/gemma-4-31B-it` | 30.7B / 30.7B, 60 layers, 1024 sliding window | dense | **No** | 256K | qat 19 GB · q4_K_M 20 GB · q8_0 34 GB · bf16 63 GB | Gemma Terms of Use *([asserted])* | 2026-03-11 | ⚠️ **INSTALLED, MEASURED** — 29,442 MiB in use, 3,180 MiB free | **The control, and the only thing on this list with evidence.** 4/4 on fixture 1 with a file edit every time [measured]. Keep it as the reference arm; do not re-litigate it. Against it: it is at the edge of the card *before* long context, and there is a `31b-coding-mtp-bf16` build that would presumably be better at this task but ships only at 64 GB — unusable here. |
| 11 | `qwen3.6:27b` | `Qwen/Qwen3.6-27B` | ~27B / dense | dense | **No** | 256K | q4_K_M 17 GB · nvfp4 19 GB · **`27b-coding-nvfp4` 20 GB** | Apache-2.0 | 2026-04-15 | ✅ comfortable (17 GB) | "Substantial upgrades in agentic coding… repository-level reasoning", and it ships an explicit **coding-tuned** tag, which few do. 17 GB is comfortable. Against it: superseded by qwen3.8 four months later, and the coding variant is only available at 20 GB NVFP4 / 31 GB MXFP8 — i.e. the good build does not comfortably fit. |
| 12 | `ornith:35b` | `ornith-ai/Ornith-1.0-35B` | 35B | not disclosed | unknown | 256K | 21 GB | MIT | 2026-06-21 | ❌ 21 GB, over | Conceptually the most interesting model in existence for *this repo*: it is trained by RL "to generate not only solution rollouts, but also **the scaffold that drives those rollouts**" — i.e. it is a learned meta-harness, which is Consilient's own thesis embodied as a model. It belongs in the literature review whether or not it is ever run. Against it as a *candidate*: 21 GB does not fit, and see #16 — the family is a Qwen derivative. |
| 13 | `qwen3.5:27b` | `Qwen/Qwen3.5-27B` | ~27B | hybrid dense/MoE ("Gated Delta Networks + sparse MoE") | mixed | 256K | 17 GB | Apache-2.0 *([asserted])* | ~2026-03 | ✅ comfortable | Fits, multimodal, 201 languages, two generations of Qwen fixes behind it. Against it: superseded twice in five months. Only worth a slot if a *stability-over-recency* arm is wanted. |
| 14 | `ornith-1.5:9b` | `ornith-ai/Ornith-1.5-9B` | 9B / dense | dense | **No** | 256K | 6.6 GB | MIT | 2026-08-18 | ✅ trivial | Critic-tier / dispersion-tier candidate, not a driver. Two days old. The right thing to point at the question "is the 8-9B failure a size wall or a harness bug?" — if a *2026-tuned* 9B also produces zero file edits, the harness is the suspect, not the size. |
| 15 | `lfm2.5:8b` | `LiquidAI/LFM2.5-8B-A1B` | 8B / **1B active** | hybrid LFM2, MoE | **YES** | 125K | 5.2 GB | LFM Open Licence *([asserted], unverified)* | 2026-05-28 | ✅ trivial | "Built for fast, reliable **tool calling** on consumer hardware" — the narrowest, most relevant claim of any small model here. 1B active means it is the cheapest thing on the list to run many samples from. Against it: 8B, and 8B is the class that has already failed once tonight. Licence needs reading before inclusion in a curated library. |
| 16 | `ornith-1.5:35b` | `ornith-ai/Ornith-1.5-35B-A3B` | 35.95B / ~3B | `Qwen3_5MoeForConditionalGeneration` | **YES** | 256K | 23 GB | MIT | 2026-08-18 | ❌ 23 GB, over | Fails twice. **(a)** 23 GB does not fit. **(b)** More importantly for this project: its architecture string is `Qwen3_5MoeForConditionalGeneration` and its parameter count is **35.95B — identical to Qwen/Qwen3.6-35B-A3B's 35.95B**. It is a Qwen fine-tune. Running it as a "second opinion" alongside a Qwen model is **echo, not consilience**. |
| 17 | `qwen3.6:35b` (`35b-a3b`) | `Qwen/Qwen3.6-35B-A3B` | 35.95B / ~3B (256 experts, 8 active, 40 layers) | MoE, 3:1 linear:full attn | **YES** | 262,144 | q4_K_M 24 GB · nvfp4 24 GB · **`35b-a3b-coding-nvfp4` 22 GB** · q8_0 39 GB | Apache-2.0 | 2026-04-15 | ❌ 22–24 GB, over | Painful near-miss. It has the best KV profile in the whole table (§3), an explicit coding-tuned build, and 256K context — and its smallest build is 22 GB, ~2 GB past the ceiling. Worth one experiment purely to find out how badly a 2 GB overspill degrades throughput, because if the answer is "barely", the ceiling moves and this becomes a top-3 candidate. |
| 18 | `nemotron-3.5-lightning:30b` | `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B` | 31.6B / ~3B (6 experts/token) | `NemotronHForCausalLM` (hybrid Mamba) | **YES** | **1M** | Ollama tag 25 GB · NVFP4 checkpoint on HF (size unverified) | OpenMDW-1.1 | 2026-08-01 | ❌ 25 GB as packaged | NVIDIA claims "4x higher throughput and 30% lower task completion time" for always-on agents, 1M context, on NVIDIA's own silicon. Everything about the pitch fits this box except the packaging: the Ollama build is 25 GB. `nvidia/…-30B-A3B-NVFP4` exists and would very plausibly fit — **this is the highest-value unresolved question in the table** and it costs one metadata lookup, not a download. |
| 19 | `nemotron3:33b` | — | 33B | multimodal (Nano Omni) | unknown | 128K | 28 GB | NVIDIA Open Model Agreement | ~2026-05 | ❌ 28 GB, over | Video/audio/text unification is irrelevant to a coding harness and costs VRAM this card does not have. |
| 20 | `qwen3-coder-next` | `Qwen/Qwen3-Coder-Next-80B-A3B` | 80B / 3B | hybrid attention + MoE | **YES** | 256K | q4_K_M 52 GB · q8_0 85 GB | Apache-2.0 *([asserted])* | ~2026-02 | ❌ RAM-offload only | Trained on 800K executable tasks with environment-interaction RL — the most agentically-trained model in the list by construction. 52 GB fits in 64 GB system RAM but not on the card. Legitimate as a **batch evaluation oracle**, never as an interactive tier. |
| 21 | `qwen3:8b` | `Qwen/Qwen3-8B` | 8.2B | dense | **No** | 40,960 | 5.2 GB | Apache-2.0 | 2025-04 | **INSTALLED — falsified** | 0/25, **no file edit in any attempt** [measured]. Keep installed as the negative control. But see §4: zero edits in 25/25 is a degenerate mode, and degenerate modes are usually harness bugs. |
| 22 | *DeepSeek — none* | `deepseek-ai/DeepSeek-V4-Flash` (284B-A13B), `deepseek-r1:32b` | — | — | — | — | — | — | — | ❌ | **DeepSeek has no serious candidate for this card.** Its current line is 284B-A13B and 671B (cloud / far out of range); the only in-range artefact is the Jan-2025 `deepseek-r1:32b` distill, which predates agentic tool-use tuning entirely. Report this as an absence, not an oversight. |
| 23 | *Phi — none* | `microsoft/phi-4` | 14B | dense | No | 16K | ~9 GB | MIT | 2024-12 | ❌ stale | **The Phi family has shipped nothing past phi4 (14B) and phi4-reasoning.** No 2026 release, no agentic variant, no tool-calling model above 3.8B. Fits easily; has nothing to offer. Include it in the library only as a documented dead end. |
| 24 | *Llama — none in range* | `meta-llama/Llama-4-Scout` (16x17b) | 109B total / 17B active | MoE | YES | 10M | ~60 GB+ | Llama licence | 2025-04 | ❌ over | Meta's answer at this size is **muse-glimmer** (#1), which is not called Llama. Llama-4 Scout is out of range on a 32 GB card. |
| 25 | `codestral:22b`, `mistral-small3.2:24b` | `mistralai/…` | 22–24B | dense | No | 128K | ~13–15 GB | Apache-2.0 / MNPL | 2024–2025 | ✅ fits, ❌ superseded | Both fit comfortably and both are strictly dominated by `devstral-small-2:24b` (#8), which is the same vendor, the same size class, newer, and actually trained for coding agents. |

**Already installed:** row 10 (`gemma4:31b`) and row 21 (`qwen3:8b`). Nothing else on this list is
on the machine and nothing was downloaded to produce it.

---

## 2. The MoE flag, summarised — because it is not the axis it looks like

Requested explicitly, so stated plainly.

**MoE at this size does not save VRAM.** Every expert must be resident. `gemma4:26b-a4b` (MoE,
3.8B active) is 18 GB on disk; `gemma4:31b` (dense, 30.7B active) is 20 GB. Two GB apart, ~8x
apart in active parameters. What MoE buys is *tokens per second and time-to-first-edit*, which on
an agent loop with dozens of turns is a real and possibly decisive advantage — but it is a
**throughput** advantage, and it must be measured as one.

This means the brief's framing — that dense-vs-MoE "is the single most important axis on this
hardware" — is right about *why it matters* (throughput) and would be wrong if read as *fit*. The
fit table row "30B-A3B-class MoE — Yes, comfortably" is comfortable only against a bigger dense
model, not against `gemma4:31b`. It should be corrected before it drives a decision.

MoE rows: 2, 3, 4, 6, 7, 15, 16, 17, 18, 20, (24).
Dense rows: 1, 5, 8, 9, 10, 11, 14, 23, 25.
Mixed/unclear: 12, 13, 19.

---

## 3. A second axis the brief did not name, which may matter more

For a 32 GB card doing *long-horizon* agentic coding, the KV cache — not the weights — is what
runs you out of memory, and KV cost is set by attention topology, not by MoE. From the configs:

| Model | Full-attention layers | KV bytes/token (bf16) | KV at 64K ctx |
|---|---|---|---|
| `Qwen3.6-35B-A3B` | 10 of 40 (3:1 linear:full), 2 kv heads, head_dim 256 | ~20 KB | ~1.3 GB |
| `Qwen3.8-27B` | 16 of 64 (3:1), 4 kv heads, head_dim 256 | ~64 KB | ~4.2 GB |

Same vendor, same generation, ~3.2x apart. `north-mini-code` (3:1 sliding:global),
`laguna-xs-2.1` (10 global of 40) and `muse-glimmer` (sliding-window) are all in the cheap camp.
This is [algebra] from published configs, not measured — but it says that if the shortlist is
picked purely on MoE-vs-dense, the wrong variable is being optimised. **The candidate that wins
is likely the one that is cheap in KV *and* sparse in compute, and only rows 3 and 4 are both.**

---

## 4. What cuts against this ranking — read this before acting on the table

Stated as prominently as the recommendations, per the brief.

1. **The only model measured to work here is dense, and the ranking's headline argument is that MoE is the interesting axis.** The single positive datapoint (gemma4:31b, 4/4, edits every time) is a *dense* 31B. Nothing measured supports MoE producing better file edits. The MoE case is entirely a throughput argument, and throughput has not been measured either.

2. **The 1.63x VRAM rule is one measurement, on one dense multimodal model, at one unknown context setting.** MoE routing buffers, hybrid-attention state (Mamba/linear-attention caches are constant-size, not growing) and vision towers all behave differently. Applying 1.63x to `laguna-xs-2.1` or `nemotron-3.5-lightning` is extrapolation dressed as arithmetic. The band boundaries in §0 could move by several GB in either direction.

3. **The qwen3:8b result probably does not mean what the ranking implicitly assumes.** Zero file edits in 25 of 25 attempts is not a capability curve — it is a switch that never closed. The most likely cause is a tool-call template mismatch in the `Codex --oss --local-provider ollama` path. Tonight's own 2.23%-vs-11.16% scaffold result is the precedent. Rows 14 and 15 exist partly to test this, and if a 2026-tuned 9B also produces zero edits, then **the harness is the finding and the model ranking is noise.**

4. **On-disk GB is not comparable across vendors.** `gemma4:31b`'s 19 GB includes a vision tower; `devstral-small-2`'s 15 GB includes one too; `granite4.1:30b`'s 17 GB does not; several entries bundle an MTP head. Ranking by disk size compares quantisation recipes as much as models.

5. **Vendor benchmark numbers are load-bearing in this table and should not be.** "65.8% SWE-Bench Verified" (Devstral), "4x throughput" (NVIDIA), "strongest model in the 30B class" (GLM), "state of the art on Terminal-Bench 2.1" (Ornith) are all [cited] **and vendor-sourced**. Given that a single scaffold change moved a score 5x tonight, and that two multilingual benchmarks inverted each other's rankings, none of these should move a decision more than one rank.

6. **Ordering rewards recency, which is a bet, not evidence.** Rows 1 and 5 are eleven and fifteen days old. Row 2 has seven months of community shakedown and 1.5M pulls. If the failure mode that matters is *harness incompatibility* rather than *capability*, the ranking is upside down and `glm-4.7-flash` should be first.

7. **Unverified or contradictory in this table:** Gemma 4 licence (assumed Gemma Terms, not read); LFM2.5 licence; Qwen3.5 licence; Qwen3-Coder release date; Granite 4.1 context (128K vs 512K, vendor self-contradiction); whether the `nvfp4` Ollama tags are CUDA or MLX-only — the latter changes the fit of five rows.

---

## 5. Recommended next actions — all zero-spend, none touching the GPU

1. **Resolve the NVFP4 question** (metadata only). If Ollama's `nvfp4` tags are Blackwell-native rather than MLX, rows 4, 17 and 18 all move up and the ceiling in §0 changes. This is the cheapest high-value lookup available.
2. **Check `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4` file sizes.** If it lands ≤18 GB, row 18 goes from "does not fit" to a top-3 candidate.
3. **Re-measure gemma4:31b VRAM at an explicit 64K context** before trusting any 19–20 GB row. Until then the shortlist is realistically rows 1, 5, 6, 8, 9 — the ≤18 GB band.
4. **Correct the fit table** in `docs/10-research/local-experimentation.md`: the "30B-A3B MoE — Yes, comfortably" row implies a memory saving that does not exist, and the "1.5x" heuristic should be 1.63x with the KV caveat attached.
5. **Do not test Ornith-1.5-35B alongside a Qwen model and call it a second opinion.** Same architecture, same 35.95B parameter count, same base. That is echo.

---

*Sources (public metadata only, no metered API called):*
[ollama.com/library/muse-glimmer](https://ollama.com/library/muse-glimmer) ·
[ollama.com/library/glm-4.7-flash](https://ollama.com/library/glm-4.7-flash) ·
[ollama.com/library/north-mini-code-1.0](https://ollama.com/library/north-mini-code-1.0) ·
[ollama.com/library/laguna-xs-2.1](https://ollama.com/library/laguna-xs-2.1) ·
[ollama.com/library/qwen3.8](https://ollama.com/library/qwen3.8) ·
[ollama.com/library/qwen3.6/tags](https://ollama.com/library/qwen3.6/tags) ·
[ollama.com/library/gemma4/tags](https://ollama.com/library/gemma4/tags) ·
[ollama.com/library/granite4.1:30b](https://ollama.com/library/granite4.1:30b) ·
[ollama.com/library/devstral-small-2](https://ollama.com/library/devstral-small-2) ·
[ollama.com/library/qwen3-coder](https://ollama.com/library/qwen3-coder) ·
[ollama.com/library/qwen3-coder-next](https://ollama.com/library/qwen3-coder-next) ·
[ollama.com/library/nemotron-3.5-lightning](https://ollama.com/library/nemotron-3.5-lightning) ·
[ollama.com/library/ornith-1.5](https://ollama.com/library/ornith-1.5) ·
[ollama.com/library/lfm2.5](https://ollama.com/library/lfm2.5) ·
[huggingface.co/Qwen/Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) ·
[huggingface.co/Qwen/Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) ·
[huggingface.co/meta-models/Muse-Glimmer-30B](https://huggingface.co/meta-models/Muse-Glimmer-30B) ·
[huggingface.co/ornith-ai/Ornith-1.5-35B-A3B](https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B) ·
[huggingface.co/zai-org/GLM-4.7-Flash](https://huggingface.co/zai-org/GLM-4.7-Flash) ·
[huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16) ·
[huggingface.co/CohereLabs/North-Mini-Code-1.0](https://huggingface.co/CohereLabs/North-Mini-Code-1.0) ·
[huggingface.co/poolside/Laguna-XS-2.1](https://huggingface.co/poolside/Laguna-XS-2.1) ·
[huggingface.co/ibm-granite/granite-4.1-30b](https://huggingface.co/ibm-granite/granite-4.1-30b) ·
[huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512](https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512) ·
[huggingface.co/LiquidAI/LFM2.5-8B-A1B](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B) ·
[huggingface.co/google/gemma-4-26B-A4B-it](https://huggingface.co/google/gemma-4-26B-A4B-it)

= VRAM required by a local model: the formula, sourced, with worked examples on a 32,607 MiB card

Evidence tags: [measured] = observed on this machine tonight; [cited] = read from a named
source (with file and line); [asserted] = my reasoning, unverified. Vendor benchmark numbers
appear nowhere in this document — nothing here depends on a leaderboard.

Constraints honoured: no model downloaded, no GPU work run, no metered API called. Everything
measured came from GGUF metadata on disk, Ollama's local HTTP API, and Ollama's own process
report — all CPU-only reads.

---

== 1. The headline

The naive rule ("weights file fits in VRAM") is wrong, but the correction is *not* a fixed
multiplier. `1.5x on-disk size` is a coincidence of the context Ollama happened to pick.

For gemma4:31b the same model on the same card is:

  ctx  4,096  -> ~1.3x on-disk
  ctx 32,768  -> ~1.55x on-disk   <- the number measured tonight
  ctx 262,144 -> ~2.4x on-disk    <- and it does not fit

The variable term is the KV cache, and it is linear in context. Any fit table with one row
per model is measuring the wrong object; the unit of fit is (model, context, KV precision).

---

== 2. The formula

    VRAM_total  =  W  +  KV(c, p)  +  G(b, c)  +  F

Every term below is in bytes.

--- Term W: weights ---

Exactly:

    W = SUM over tensors t of  ceil(n_t / blockSize(type_t)) * typeSize(type_t)

where n_t is the element count of tensor t. Block and type sizes [cited:
ollama/ollama `fs/ggml/ggml.go`, `TensorType.BlockSize()` L407 and `TensorType.TypeSize()` L442]:

  | type   | block | bytes/block | bits per weight |
  |--------|-------|-------------|-----------------|
  | F32    |   1   |      4      | 32              |
  | F16/BF16 | 1   |      2      | 16              |
  | Q8_0   |  32   |     34      | 8.5             |
  | Q6_K   | 256   |    210      | 6.5625          |
  | Q5_K   | 256   |    176      | 5.5             |
  | Q4_K   | 256   |    144      | 4.5             |
  | Q4_0   |  32   |     18      | 4.5             |
  | MXFP4  |  32   |     17      | 4.25            |
  | NVFP4  |  64   |     36      | 4.5             |

Approximately, when you only know parameter count P (i.e. before download — which is the
case ADR-0026 cares about):

    W ~= P * bpw_effective / 8

**bpw_effective is not the nominal bits of the quant name.** Measured on both local models
[measured]:

  gemma4:31b, "Q4_K_M":  18.490 GiB over 31.273 B params = **5.079 bpw**  (nominal 4.5)
  qwen3:8b,   "Q4_K_M":   4.861 GiB over  8.191 B params = **5.098 bpw**  (nominal 4.5)

The excess is structural, not noise: llama.cpp's K-quant mixes promote `attn_v` and
`ffn_down` to Q6_K, and every norm tensor stays F32. Use these multipliers instead of the
nominal bits [asserted, but anchored on two measured points]:

  | scheme      | planning bpw | note |
  |-------------|--------------|------|
  | Q4_K_M      | 5.0 – 5.1    | [measured] on two models tonight |
  | Q5_K_M      | 5.9 – 6.0    | [asserted] same mix logic, one step up |
  | Q6_K        | 6.6          | [cited] block definition, near-uniform in practice |
  | Q8_0        | 8.5          | [cited] block definition |
  | fp16/bf16   | 16.0         | exact |
  | MXFP4       | 4.25 for the tensors that carry it | [cited] ggml block def; in practice gpt-oss-style releases apply it to MoE expert weights only and keep attention/norms at bf16, so whole-model bpw lands nearer 4.6–5.0 [asserted, unverified this session] |
  | AWQ 4-bit   | ~4.15 – 4.25 | [asserted]: 4 bits/weight + one fp16 scale and one 4-bit zero per group of 128 = (128*4 + 16 + 4)/128 = 4.16 bpw. Packing/`g_idx` overhead pushes it up. I could not verify against the AWQ paper in this session (no search budget) — treat as arithmetic, not citation. |
  | GPTQ 4-bit g128 | ~4.16 – 4.3 | [asserted], same arithmetic; act-order variants store an extra index tensor. |

Note that AWQ/GPTQ are *not* directly comparable to GGUF K-quants at equal bpw: they keep
everything in one precision, whereas K-quants spend extra bits where the error matters. That
is a quality question, not a memory one, and it is out of my scope.

--- Term KV(c, p): the KV cache ---

Per layer, per token, the cache holds K and V for each KV head:

    KV(c, p) = p * SUM over layers l of  min(c, w_l) * (d_k,l + d_v,l) * h_kv,l * e

  c    = context length in tokens
  p    = parallel slots (num_parallel); Ollama v0.21.1 default is **1**
         [cited: `server/sched.go` L412 `numParallel := max(int(envconfig.NumParallel()), 1)`]
  w_l  = the layer's attention span: c for a global layer, (window * p + batch) for a
         sliding-window layer
  d_k,l, d_v,l = key/value head dimension for that layer (GGUF `attention.key_length` /
         `value_length`, and the `_swa` variants where present)
  h_kv,l = KV heads in that layer (GGUF `attention.head_count_kv`, which may be a per-layer
         array)
  e    = bytes per element: **f16 = 2, q8_0 = 1, q4_0 = 0.5**
         [cited: `fs/ggml/ggml.go` L959 `kvCacheBytesPerElement`]

Shape of the term [cited: `fs/ggml/ggml.go` L676-707, `GraphSize`]:
`kv[i] = context * (embeddingHeadsK + embeddingHeadsV) * headsKV_i * bytesPerElement`,
with a sliding-window override for architectures that declare one (L745-755).

Three traps in this term:

1. **It is allocated up front, for the whole context, at load time.** It does not grow with
   the conversation. This is llama.cpp/Ollama behaviour. vLLM's paged KV is a different
   regime entirely: it grabs `gpu_memory_utilization` (default 0.9) of the card regardless,
   then pages inside it — so a vLLM-based library entry needs a different fit rule
   [asserted, from the design of PagedAttention; not verified this session].
2. **Sliding-window attention breaks the linearity for most layers.** See the worked example.
3. **MLA (DeepSeek-style) breaks the formula outright** — it caches a compressed latent, not
   per-head K and V. Do not apply this formula to MLA architectures [asserted].

--- Term G(b, c): compute graph and activations ---

The transient buffers for one forward pass. Dominated by two things:

  * the output/logits path, ~ 4 * batch * (d_model + vocab) bytes
    [cited: `fs/ggml/ggml.go` L775-778, gemma family `fullOffload` estimate]
  * attention temporaries, which **scale with batch * context * heads when flash attention
    is off** and collapse to O(batch * heads * d_head) when it is on. This is why
    `OLLAMA_FLASH_ATTENTION` is a memory switch, not just a speed switch. Ollama's own
    static estimate for this term is visibly unusable at long context (the gemma expression
    `4*batch*(2 + context + context*heads + ...)` evaluates to terabytes at batch 512,
    ctx 32k) — which is itself evidence that this term is not predicted, it is allocated and
    then measured.

Vocabulary size matters here far more than people expect: gemma4 has a 262,144-token
vocabulary, so a single fp32 logits buffer at batch 512 is 512 * 262,144 * 4 = 537 MB.

--- Term F: framework and driver floor ---

CUDA context, cuBLAS/cuDNN workspaces, allocator fragmentation, and on Windows the WDDM
display allocation. Not modelled by Ollama at all: `OLLAMA_GPU_OVERHEAD` defaults to **0**
[cited: `envconfig/config.go` L303 `var GpuOverhead = Uint64("OLLAMA_GPU_OVERHEAD", 0)`].
Plan on 0.5–1.0 GiB on a Windows box with a display attached [asserted]; measured residual
tonight was larger, see §3.

--- What Ollama itself adds on top ---

These are policy, not physics, but they decide whether your model loads [all cited,
`server/sched.go` @ v0.21.1]:

  * automatic context ladder: train-context -> **32,768** -> **4,096**, then give up
    (`nextLowerAutoNumCtx`, L917-926)
  * a load is only accepted if predicted VRAM <= **80%** of available memory
    (`generationBatchFits`, L874)
  * batch surcharges: **+2 GiB** for batch >= 2048, **+768 MiB** for batch >= 1024
    (`generationBatchSurcharge`, L905-913)
  * extra headroom gates: predicted <= 60% of available at large batch, <= 75% at medium
    (L798-804, L886-895)

---

== 3. Worked example A — gemma4:31b on 32,607 MiB (31.84 GiB)

All architecture facts below were read out of the local GGUF header and Ollama's API
[measured] — not from vendor documentation, which I did not consult.

  block_count 60, d_model 5376, head_count 32, vocab 262,144, train ctx 262,144
  attention.sliding_window 1024
  attention.sliding_window_pattern = [T,T,T,T,T,F] repeated 10x   (60 entries)
  attention.head_count_kv         = [16,16,16,16,16,4] repeated 10x
  key_length 512 / value_length 512   (global layers)
  key_length_swa 256 / value_length_swa 256   (sliding layers)

Confirmed independently by tensor shapes: `blk.4.attn_k.weight [5376, 4096]` = 16 x 256
(sliding), `blk.5.attn_k.weight [5376, 2048]` = 4 x 512 (global).

So **50 of 60 layers only ever cache 1,024 tokens**, and just 10 layers pay for full context.
This is the single most important structural fact about the model's memory behaviour, and
nothing on the model card or in the file size tells you it.

--- W ---

  Sum over 1,189 tensors  = 18.490 GiB
  Blob on disk            = 19,868,969,920 B = 18.504 GiB
  Gap 0.014 GiB (0.08%)   = GGUF header + tokenizer arrays (262k tokens, 515k merges)

  Composition: Q4_K 13.272 GiB, Q6_K 4.096 GiB, F16 1.028 GiB, F32 0.093 GiB
  By part:     text blocks 16.296 GiB, vision tower + projector 1.117 GiB,
               embeddings/output/other 1.077 GiB

The formula reproduces the file to within 0.1%. That is the part of the prediction that is
solid.

--- KV, per token ---

  sliding layer: (256 + 256) * 16 * 2 B = 16,384 B/token, but capped at 1,024 + batch
  global layer:  (512 + 512) *  4 * 2 B =  8,192 B/token, uncapped

  Fixed sliding cost (50 layers x 1,536 tokens):  1.172 GiB
  Marginal cost of context: 10 * 8,192 = **80 KiB per token** at f16

--- Budget at the measured configuration (ctx 32,768, batch 512, f16 KV, p=1) ---

  weights                             18.49 GiB
  KV (1.172 fixed + 2.50 global)       3.67 GiB
  ------------------------------------------------
  subtotal predicted by formula       22.16 GiB
  `ollama ps` reports                 25.15 GiB (27 GB)  -> G = **2.98 GiB** residual
  `nvidia-smi` reports                28.75 GiB (29,442 MiB) -> a further **3.61 GiB**

**So the answer to "why did 19 GB on disk consume 29.4 GB?" is:**

  +0.0 GiB  the 19 GB figure is decimal; it is 18.5 GiB, so ~1.4 GiB of the apparent gap is
            unit confusion (GB vs GiB) before any physics happens
  +3.7 GiB  KV cache for the 32,768-token context Ollama chose
  +3.0 GiB  compute graph, logits buffer over a 262k vocabulary, vision-tower buffers
  +3.6 GiB  CUDA context, WDDM/display, fragmentation — **and anything else on the GPU**

That last line is the weak one and I flag it hard: `ollama ps` attributes 27 GB to the model,
`nvidia-smi` said 29,442 MiB were in use system-wide, and a concurrent experiment was running.
Attributing all 29.4 GB to gemma4:31b overstates it by ~3.6 GiB. The defensible statement is
**"Ollama allocated 25.15 GiB for a model whose weights are 18.49 GiB"** — a 1.36x multiple,
not 1.55x.

--- Context scaling: the answer to the 262,144 question ---

  | ctx     | KV f16   | KV q8_0 | weights+KV f16 | fits in 31.84 GiB with ~3 GiB graph? |
  |---------|----------|---------|----------------|--------------------------------------|
  |   4,096 |  1.48 GiB| 0.74 GiB|      19.97 GiB | yes, comfortably                     |
  |   8,192 |  1.80    | 0.90    |      20.29     | yes                                  |
  |  16,384 |  2.42    | 1.21    |      20.91     | yes                                  |
  |  32,768 |  3.67    | 1.84    |      22.16     | yes — **this is what loaded**        |
  |  65,536 |  6.17    | 3.09    |      24.66     | yes, tight                           |
  | 131,072 | 11.17    | 5.59    |      29.66     | no (graph pushes it over)            |
  | 262,144 | 21.17    |10.59    |      39.66     | **no, by ~8 GiB**                    |

Ceiling on this card at f16 KV, after weights, the fixed sliding cost, ~0.8 GiB driver floor
and a graph allowance:

  graph 1.0 GiB -> ~151,000 tokens
  graph 2.0 GiB -> ~138,000 tokens
  graph 3.0 GiB -> ~125,000 tokens   <- the graph residual actually measured

So: **advertised 262,144; achievable roughly 125,000 at f16, and what you actually get is
32,768** — because Ollama's ladder has no rung between 262,144 and 32,768. Switching the KV
cache to q8_0 buys back roughly a factor of two on the KV term and would put ~250k in reach
arithmetically, but there is still no ladder rung to select it and I have not measured the
quality cost of q8_0 KV.

The prediction that would have been made by the naive "use the max head dim and full context
for all 60 layers" reading of the metadata is 60 GiB at ctx 32,768 and 480 GiB at 262,144 —
off by 16x and 23x. **Anyone building a fit predictor who ignores sliding-window attention
will reject models that run fine.**

Related, and worth a defect report: Ollama v0.21.1's static estimator has no `gemma4` case
(`fs/ggml/ggml.go` L725 lists `"gemma", "gemma2", "gemma3", "gemma3n"`, and the sliding-window
correction at L745 is gated on `Architecture() == "gemma3"`). For this model its pre-load
estimate is therefore the ~60 GiB figure. The model loads anyway because the new engine
reports its real allocations back to the scheduler. **A hardware-fit recommender must compute
this itself and must not shell out to Ollama's static estimate.**

---

== 4. Worked example B — qwen3:8b, and a result that inverts the intuition

  36 layers, d_model 4096, head_count 32, head_count_kv 8, key/value_length 128,
  train ctx 40,960, no sliding window declared. [measured, local GGUF]

  W = 4.861 GiB (399 tensors; matches the 5.2 GB decimal figure)
  KV per token = 36 * (128+128) * 8 * 2 = **144 KiB/token** at f16

  | ctx    | KV f16  | weights + KV |
  |--------|---------|--------------|
  |  4,096 | 0.56 GiB|   5.42 GiB   |
  | 32,768 | 4.50    |   9.36       |
  | 40,960 | 5.62    |  10.49       |

**The 8B model costs 144 KiB per token of context; the 31B model costs 80 KiB.** The larger
model has the cheaper context. Parameter count tells you nothing about KV cost — only
(layers x KV heads x head dim x span) does. A model library ordered by parameter count will
mis-rank models for long-context work.

Two consequences for the workstream that owns the library:

  * qwen3:8b at full 40,960 context uses 10.5 GiB of 31.84 GiB. **Its 0/25 failure and its
    total absence of file edits are not a hardware-fit problem** and must not be recorded as
    one. That belongs to whoever owns capability, not to me.
  * both models fit simultaneously (10.5 + 25.2 = 35.7 GiB) — no, they do not. 35.7 > 31.84.
    Co-residency needs the context of at least one of them dropped. Worth stating explicitly
    because a harness that routes between a critic and a coder will want both loaded.

---

== 5. The rule to encode in the library

Before any download, from public metadata alone (config.json / GGUF header on the hub, both
readable without pulling weights):

    W    = P * bpw_planning / 8              bpw_planning from the table in §2, NOT the quant name
    KV   = p * SUM_l min(c, span_l) * (d_k + d_v) * h_kv,l * e
    G    = max(4 * batch * (d_model + vocab), attention temporaries)   ~ 1–3 GiB, allow 3
    F    = 0.8 GiB on a Windows box with a display

    fits  <=>  W + KV + G + F  <=  0.9 * VRAM_total     and report c, not just yes/no

And the column that actually matters to a user of the meta-harness is not "fits" but
**"largest context that fits, and the context the runner will actually give you"** — those
differ, here by a factor of four (125k achievable, 32,768 delivered).

---

== 6. What cannot be predicted without loading the model

Honest list. Everything here is a reason the formula gives a *lower bound plus an allowance*,
not a number.

1. **The compute-graph term G.** Ollama does not predict it either — the current engine
   allocates a worst-case graph at load and reports back what it took. It depends on batch
   size, whether flash attention is on, the backend build, kernel selection and the driver.
   Measured residual here: 2.98 GiB, which I can attribute by subtraction but not derive.
2. **The driver/allocator floor F.** CUDA context size varies with driver version and card;
   Windows WDDM adds display allocations that move when you plug in a monitor.
3. **Fragmentation.** Two loads of the same model in different orders can differ by hundreds
   of MB. This is why "fits with 400 MiB spare" is not a fit.
4. **Multimodal buffers.** gemma4 carries a 27-block vision tower. Image-token buffers depend
   on the *resolution of the images in the request*, which is unknowable at load time.
5. **Whether the runner will fully offload.** Partial offload changes the arithmetic
   completely — the estimator has entirely separate `partialOffload` expressions, and a model
   that "fits" at 59 of 60 layers performs like a different model.
6. **Architectures the estimator does not know.** Demonstrated above with gemma4 in v0.21.1.
   For a genuinely new architecture, the per-layer KV geometry may not be inferable from the
   standard GGUF keys at all.
7. **What else is on the GPU.** The largest single uncertainty in tonight's measurement.

---

== 7. What cuts against my own conclusion

Stated as prominently as the rest, per the brief.

* **The 29,442 MiB figure is not the model's footprint.** Ollama's own accounting says 27 GB.
  The 2.4 GB difference could be CUDA context, or it could be the concurrent experiment. I
  cannot separate them without a clean measurement, and I was told not to touch the GPU. If
  the residual is mostly other processes, my "F ~ 0.8 GiB" allowance is too generous and the
  real framework floor is smaller — which would make the formula *conservative*, i.e. it
  would reject models that fit.
* **"1.5x on-disk" is not a rule and I should not have been asked to defend it as one, but
  nor should I over-claim the alternative.** My replacement — "compute W exactly, add KV at
  your actual context, allow 3 GiB" — has exactly one measured calibration point for the
  3 GiB allowance. One point is not a calibration.
* **G is the term that decides marginal cases, and it is the term I cannot compute.** Every
  "fits / does not fit" verdict near the boundary in §3 is therefore soft. The 262,144 verdict
  is safe (it misses by 8 GiB); the 131,072 verdict is not (it misses by ~0.8 GiB, which is
  inside my uncertainty on G and F).
* **The sliding-window discovery is inferred from the GGUF metadata and tensor shapes, and
  from Ollama's gemma3 handling — not from vendor documentation for gemma4, which I did not
  read** (no search budget remained). The `sliding_window_pattern` array is unambiguous and
  the tensor shapes corroborate it, so I am confident in the geometry; I am less confident
  that the *runner* implements the window exactly as `window*p + batch`, which is where my
  1.172 GiB fixed sliding cost comes from. If the runner rounds the sliding cache up to a
  multiple of the batch or keeps a larger margin for context shift, that term grows.
* **The bpw table's AWQ/GPTQ/MXFP4 rows are arithmetic from format definitions, not citations.**
  Two of them (AWQ, GPTQ) I could not check against their papers in this session. If the
  library is going to recommend AWQ or GPTQ builds, someone should verify those two rows
  against a real safetensors index before anything downloads.
* **This whole analysis is llama.cpp/Ollama-shaped.** If the library ever recommends a vLLM
  or SGLang path — and `local-experimentation.md` §1 says it will, for the constrained-decoding
  work — the KV term is replaced by a pool-allocation model and the fit question changes from
  "does it fit" to "how many concurrent sequences fit". None of §3's numbers transfer.

---

== 8. Repo docs this contradicts

`docs/10-research/local-experimentation.md` §"What fits in 32 GB VRAM" is marked
"Rough, verify before relying on it". Verified, and it is wrong in one row and right in the
most important sentence:

* Row "30–32B dense, 4-bit (AWQ/GPTQ): ~20–22 GB weights" — measured 18.5 GiB for a 31.3B
  Q4_K_M. Close enough, but the row's "limited KV cache" understates it: at 32k context this
  model needs 25 GiB total, leaving ~6 GiB, and it cannot reach its advertised context at all.
* The sentence "Long-context work is KV-cache-bound, not weight-bound. A 32B at 4-bit with a
  large context will OOM before a 14B at 8-bit does" is **correct in direction and wrong in
  the specific case measured**: this 31B is *cheaper* per context token than an 8B, because of
  sliding-window attention. The claim should be restated as KV-geometry-bound, not size-bound.

I have not edited any file in `docs/10-research/` — that is on the "ask first" list in
AGENTS.md.

# Local experimentation rig

**Hardware:** RTX 5090 (32 GB VRAM), Ryzen 9 9950X3D, 64 GB system RAM.
Licences for anything needed are available on request.

**Standing instruction:** prefer local experimentation. If a question can be answered by
running something on this box, run it rather than reasoning about it. Local compute is free;
the only cost is wall-clock. This is the cheapest evidence in the project and it upgrades
claims from `[simulated]` to `[measured]`, which is the tag that matters.

---

## What this unblocks that an API cannot

### 1. CASD / constrained decoding — the missing experiment
Grammar-constrained decoding and jump-forward decoding both operate on **logits**. No
hosted API exposes them. The comparison that was never run — and which is the whole of
publication candidate C2 in `../publications/README.md` — requires exactly this hardware.

Stack: vLLM or SGLang locally, XGrammar / Outlines / llguidance for the constrained path,
SGLang's jump-forward as the baseline. **This is now the shortest route to a first
publication.**

### 2. Free trajectory volume for measuring β
`../decisions/0002-*` is PROVISIONAL because β has never been measured, and Q2 asks whether
it is measurable at solo-founder data volumes. A local cheap tier removes the token cost of
generating trajectories entirely. The remaining constraint is *human verdicts*, not model
calls — which sharpens Q2 rather than answering it, but it removes one of the two blockers.

### 3. Prior dispersion (Inquiry-tier gate G3) becomes free
G3 samples the same question from N models at temperature and measures semantic agreement.
Locally that is N forward passes and an embedding comparison — no marginal cost. Gate G3 was
the design's most expensive component; on this rig it is nearly free.

### 4. The critic tier does not need a frontier model
`../10-research/findings.md` §5: the critic's only job is rejecting bad diffs before a human
sees them. That is a classification task against test output, not open-ended reasoning.
Run it locally, measure its recall, and recall ≡ 1 − β.

---

## What fits in 32 GB VRAM

Rough, verify before relying on it:

| Class | Fits | Notes |
|---|---|---|
| 30–32B dense, 4-bit (AWQ/GPTQ) | Yes, tight | ~20–22 GB weights, limited KV cache |
| 30B-A3B-class MoE, 4-bit | **Yes, comfortably** | Only ~3B active — best throughput/capability ratio on this box |
| 14B, 8-bit | Yes, roomy | Good for the critic tier |
| 7–8B, fp16 | Yes | Fast dispersion sampling for G3 |
| 100B+ MoE, 4-bit with CPU offload | Technically, via 64 GB RAM | Very slow; fine for batch eval, not for an interactive tier |

Long-context work is KV-cache-bound, not weight-bound. A 32B at 4-bit with a large context
will OOM before a 14B at 8-bit does.

---

## Two warnings that change design conclusions

### A. A local cheap tier widens the capability gap — which tightens β\*

`findings.md` §2, and this is the uncomfortable one:

| capability gap | β\* (tests may miss at most) |
|---|---|
| 0.42 | 3.3% |
| 0.27 | 11.1% |
| 0.17 | 24.9% |

A local 30B against a frontier model is a **wide** gap. So routing to local-cheap demands
*near-perfect verification* — a repo with anything less than excellent tests is better off
not routing locally at all. This is not a reason to avoid local inference; it is the single
most important thing the β-meter would tell a user, and it is testable on this rig.

### B. GPU inference is not reproducible by default

Continuous batching, non-deterministic reductions and kernel selection mean two identical
prompts can give different outputs. The publication policy's truth gate requires
"reproducible from a seed".

For any run that will be cited: fixed seed, batch size 1, deterministic kernels where
available, pinned model revision (by hash, not tag), pinned inference-engine version, and
record all of it. Expect to re-run and confirm rather than assume. **Record the
non-determinism you cannot eliminate rather than pretending it is absent.**

---

## Consequence for ADR-0003 (no learned router)

`findings.md` §4a: a learned prior only earns its keep when a failed cheap attempt is
expensive — headroom +0.002 at a 1× wasted-work multiplier, +0.024 at 2×, +0.123 at 5×.

With an API cheap tier, a failed attempt costs tokens: roughly 1×.
**With a local cheap tier it costs wall-clock on a single GPU, which is a serialising
resource.** That plausibly pushes the multiplier past 2× and back into the regime where
learned routing pays.

This does not overturn ADR-0003, but it is exactly the condition that ADR names as the
trigger to reopen it. **Measure the multiplier on this rig before assuming either way.**

---

## Suggested first runs

In order, cheapest evidence first:

1. **Bimodal difficulty check (Q3).** Pure CPU, minutes. Re-run
   `experiments/simulations.py` with a bimodal `d`. Most likely way the thesis is wrong.
2. **Jump-forward vs constrained decoding (C2).** The publication.
3. **Wasted-work multiplier.** Time a local cheap attempt end-to-end, including verifier,
   against a frontier call. Feeds ADR-0003.
4. **Critic recall.** Run a local 14B as a diff critic over historical `jobboard-v2` PRs
   with known outcomes. Gives a first real number for 1 − β.
5. **G3 dispersion cost.** Measure latency and agreement spread for N ∈ {3,5,8} local models
   on real architecture questions.

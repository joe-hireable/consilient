# Two Ollama issue drafts — awaiting Joe, not sent

**Correction first.** I described these as "drafted, not sent" in three overnight messages. They
were not drafted. They existed only as a two-sentence description inside ADR-0036 § 5. They are
drafted now, and the discrepancy is recorded rather than quietly closed. [measured]

**Status: drafts. Nothing has been sent.** ADR-0036 § 3 requires an outbound contribution to meet
the same tier standard we ask of inbound work — a reproduction, the measurement behind every
number citing what measured it, what the change might break, and the honest limits of the
evidence. It also carries a restraint that matters more than the standard: **rigour is
proportional to blast radius in *their* project, and their `CONTRIBUTING.md` governs, not ours.**

**Two things to do before sending, neither of which I can do from here:**

1. **Read `ollama/ollama`'s `CONTRIBUTING.md` and issue templates**, and reshape both drafts to
   them. No web access in this session. If they want a template filled in, fill it in and cut
   whatever does not fit — turning up with another project's document format uninvited is being a
   nuisance, not setting an example.
2. **Re-verify the line numbers against current `main`.** They were read at v0.21.1. A defect
   report citing a moved line wastes a maintainer's time.

---

## Draft 1 — `fs/ggml` static memory estimate has no `gemma4` case, and the sliding-window correction is gated on `gemma3`

**Version:** v0.21.1

### What happens

`EstimateGPULayers` produces a pre-load VRAM estimate that is roughly **16× too high at ctx
32,768** and **23× too high at ctx 262,144** for `gemma4:31b`. [measured — computed from the
model's own GGUF metadata against the estimator's expression; both figures derived below]

### Why

Two places in `fs/ggml/ggml.go` (line numbers as at v0.21.1):

- **L725** enumerates the gemma family for the estimate as `"gemma", "gemma2", "gemma3",
  "gemma3n"`. `gemma4` is absent, so it falls through to the generic path.
- **L745–755** applies the sliding-window KV correction gated on `Architecture() == "gemma3"`,
  so `gemma4` does not receive it.

`gemma4:31b` declares sliding-window attention in its GGUF metadata:

```
attention.sliding_window          1024
attention.sliding_window_pattern  [T,T,T,T,T,F] × 10   (60 entries)
key_length_swa / value_length_swa 256 / 256            (sliding layers)
```

So 50 of its 60 layers cache a 1,024-token window at head dimension 256, and only 10 cache the
full context at the global head dimension. Without the correction the estimator prices **all 60
layers at the global head dimension across the full context**.

### The arithmetic

Naive reading of the metadata — full context, global head dimension, all 60 layers:

| context | naive estimate | corrected for sliding window |
|---|---|---|
| 32,768 | ~60 GiB | ~3.7 GiB |
| 262,144 | ~480 GiB | ~21 GiB |

The corrected column splits into a fixed sliding cost of **1.172 GiB** (50 layers × 1,536 tokens,
which is the 1,024 window plus batch) and a context-linear global term over the remaining 10
layers. [measured — recomputed from the GGUF metadata this session]

### Why it is not a crash

The model loads correctly. The new engine reports its real allocations back to the scheduler, so
the static estimate is not load-bearing for `gemma4` in practice. **The defect is in what consumes
the estimate**, not in the loader.

### Why report it anyway

Anything that reads the pre-load estimate to decide *whether a model will fit* — a hardware-fit
recommender, a scheduler placing models across cards, a UI warning a user off a download — will
reject a model that runs comfortably. In our case it would have rejected a 31B model that fits a
32 GB card with room to spare. [measured]

Generalising: **a fit predictor that ignores sliding-window attention will reject models that run
fine**, and this one silently does for every architecture not on the L725 list.

### Suggested fix

Add `gemma4` to L725, and widen the L745 gate from an exact `gemma3` match to any architecture
declaring `attention.sliding_window` — the metadata is already there to key on, which would make
the correction forward-compatible rather than needing an edit per release.

### Limits of this evidence

- One model on one card. No sweep across architectures. [measured]
- The estimator expression was evaluated by hand against the GGUF metadata, not by instrumenting
  a build. A maintainer running it directly may get a different figure and that would be the
  better number.
- I have not checked whether other sliding-window architectures beyond the gemma family are
  affected — the code shape suggests they would be, but I have not confirmed it. [asserted]

---

## Draft 2 — an oversized context is quietly reduced rather than refused

**Version:** v0.21.1

### What happens

`gemma4:31b` advertises a **262,144**-token context. On a 32 GB card the arithmetic supports
roughly **125,000** at f16 KV. What is actually served is **32,768**, with no error, no warning
and no log line saying a reduction occurred. [measured]

The immediate cause appears to be that the context ladder has no rung between 262,144 and 32,768,
so the request lands on the next one down. [asserted — inferred from the served value, not traced
through the selection code]

### Why it matters

A caller that asks for a long context and receives a short one without being told will produce
**silently truncated results**. That is worse than a refusal in a specific way: a refusal is
visible at setup and fixed once, whereas a silent reduction is discovered later, if at all, as
degraded output nobody can attribute.

This is the same failure shape as a database that accepts an out-of-range value by coercing it.
The write reports success and the record does not say what the caller asked for.

### What would fix it

Any one of these, in descending order of preference:

1. **Log the reduction** at load time — requested, granted, and why. One line, no behaviour change.
2. **Expose the granted context** in `/api/show` or the load response, so a caller can check.
3. **Refuse** when the granted context is below some fraction of the requested one, behind a flag.

Option 1 alone would have made this a non-issue for us and costs nothing.

### Limits of this evidence

- **I have not traced the selection code**, so "no rung between 262,144 and 32,768" is an
  inference from the served value. A maintainer will know immediately whether that is the
  mechanism, and it may be something else entirely. [asserted]
- One model, one card, one Ollama version.
- I have not checked whether a log line exists at a verbosity I was not running. **This should be
  checked before filing** — reporting a missing warning that exists at `OLLAMA_DEBUG=1` would be
  exactly the sloppiness ADR-0036 § 3 is meant to prevent.

---

## What these two are worth

Neither is dramatic. Draft 1 is a stale enumeration with a clean fix and a real downstream
consequence; draft 2 is a usability defect that costs one log line.

They are worth sending because ADR-0036 § 5 commits this project to offering findings back **in
their terms, whether or not it suits us** — and because both were produced as a by-product of
work we were doing anyway. The supply of these is not the constraint; the willingness to write
them up properly is.

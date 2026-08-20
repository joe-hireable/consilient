# EXP-31 findings — the capability floor is the model, not the tier

**Run `exp31-20260820T085909-21636`, 20 August 2026, 08:59–10:40.** Complete: **50 of 50
attempts**, `stop_reason: null`, 6,057 seconds against a 10,800-second cap. The first complete
execution of this experiment. [measured]

## Result

| | attempts | passes | **produced an edit** | censored | first-attempt passes |
|---|---|---|---|---|---|
| `qwen3:8b` | 25 | **0** | **0** | 2 | 0 |
| `gemma4:31b` | 25 | **21** | **22** | 3 | 5 |

**Registered verdicts, as the instrument computed them:**

- **`pass_rate: difference_claimed`** — `qwen 0/5 vs gemma 5/5` fixtures. [measured]
- **`latency: insufficient_evidence`** — median first-attempt ratio **1.05**, signs not
  consistent. There is no latency difference to speak of. [measured]

Per fixture, `gemma4:31b` passed **5 of 5 on every one of the five fixtures**. `qwen3:8b` passed
none of 25 attempts and **produced no file edit at all**.

## What this settles

EXP-07 found `qwen3:8b` produced no edit in 25 attempts and asked whether that was **the model or
the tier**. On a *different* fixture set, with a repaired instrument, the answer is unambiguous:
**the model.** A 31B model on the same rig, the same harness, the same 240-second timeout and the
same five fixtures produced 22 edits and 21 passes.

Pooled with EXP-07, `qwen3:8b` has now produced **zero file edits in 50 attempts across two
fixture sets** — 48 of them observed rather than censored. [measured]

**The latency verdict matters too, and it cuts against the earlier framing.** A median ratio of
1.05 means the two models take about the same time. The wasted-work story was never about the
cheap model being *slow*; it is about it producing *nothing*.

## The earlier "bimodal by fixture" reading was an instrument artefact, and this proves it

Before the timeout was repaired, `gemma4:31b` showed a clean partition: 5/5 passes on
`duration-parser` and `event-replay`, 5/5 **timeouts** on `windows-wsl-path` and
`wilson-verdict`. I called that bimodality and then corrected myself to say it was confounded.

**With a working process-tree kill, `gemma4:31b` passes 5/5 on all four of those fixtures.**
[measured] The partition was not a property of the model. It was the instrument losing control of
processes it believed it had killed, and recording the resulting chaos as a model failure.

**Censoring fell from roughly a third of attempts to 5 of 50** once the timeout could actually
stop a run. That single repair is the difference between an experiment that could not complete in
three hours and one that finished the full matrix in 101 minutes.

## Limits, unchanged from the registration

- **This is model substitution in a fixed composition, not a size effect.** The two models differ
  in family, training data, tokeniser, instruction tuning and quantisation. No same-family
  sibling pair is installed. Nothing here says "bigger is better".
- Reasoning modes are not matched; each model runs at its own Ollama default.
- **β is not measured here.** The fixture oracle's own false-accept rate is unknown, so a pass is
  a pass against *these* checks and no more.
- One `gemma4:31b` attempt shows `tests_pass_scope_fail` — tests green, scope violated. That is
  exactly the artefact class β exists to count, and it is one observation, not a rate.

## The stopping rule that could not fire, still

The registration obliges a stop on *"a write outside the temporary repository"*, and **the
instrument still cannot observe one**: the runner invokes Codex with the sandbox bypassed and the
scope gate inspects only the temporary repository. That defect was recorded before this run and
is unrepaired, so **this run's out-of-repository writes are unobserved rather than absent.**
[asserted] The other stopping rules — the attempt cap, the wall-clock cap, the OOM rule — all
held.

## Provenance

This is the third execution. The first two ran **concurrently by my own error**, interleaved into
one results file, and are void; both partial datasets are preserved outside the evidence base and
the incident is written up in `../../../00-context/exp31-interleaving-2026-08-20.md`. **They are
not pooled with this run**, because the instrument changed between them — pooling would be the
outcome-aware move this project has refused throughout.

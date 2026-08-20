# EXP-31 has been running twice, into one file, all night

**Found 20 August 2026, 06:20.** The run is compromised. Nothing about it should be believed
without reading this page first. [measured]

## How it surfaced

A routine progress check showed the run count going **backwards** — 28 runs at 05:00, 25 runs at
06:15. A count that decreases is not slow progress; it is a different file.

## What is actually happening

`results-exp31.json` records a `probe` block, written once when a run starts, containing the free
VRAM measured before any model was loaded. Reading that field out of every commit that touched the
file gives this:

| commit | runs | `free_mib_before` |
|---|---|---|
| `1c284bc` | 4 | **29126** |
| `fdd54f4` | 8 | 19126 |
| `d01d82a` | 13 | 19126 |
| `2120fa7` | 14 | 19126 |
| `41b2780` | 15 | **29126** |
| `dea3256` | 16 | 19126 |
| `ed1792d` | 22 | 19126 |
| working tree | 25 | **29126** |

The fingerprint **alternates**. This is not one runner that restarted. It is **two runners,
running concurrently since before 01:00, each holding its own list of results in memory and
rewriting the whole file on every checkpoint.** Whichever writes last wins, and the other's
progress vanishes until its next write puts it back. [measured]

The apparently healthy monotone growth from 4 to 28 was two saw-teeth interleaved.

## Why the file cannot simply be repaired

Each writer's file is internally consistent — a coherent sequence of cells with no duplicates.
The corruption is not *within* either file. It is that **the file on disk at any moment belongs
to one writer and silently discards the other's work**, and neither writer knows the other exists.

Both partial datasets are preserved, reconstructed from the richest surviving snapshot of each
fingerprint, in the session scratchpad as `writer-probe-19126.json` (22 runs) and
`writer-probe-29126.json` (25 runs), with `disagreements.json`. They are deliberately **not**
committed into `docs/10-research/`: that directory is gated on Joe by `AGENTS.md`, and an
automated attempt to write there was correctly blocked earlier the same night. Adding raw
experimental data to the evidence base is his call, not mine. [asserted]

## ⚠️ The trap this sets

Each runner will eventually reach 50 runs and write `complete: true`. **The result will be a file
that looks finished, clean and single-sourced, with no trace that a second run ever existed.** A
reader tomorrow would find a completed experiment and no reason to doubt it.

**A `complete: true` from this run must not be believed.** That is the single most important
sentence on this page. [asserted]

## What the accident measured, which is worth more than the run

The two writers independently executed the same 22 `(fixture, model, attempt)` cells. That is a
free replication the experiment never registered — and it is a measurement of the instrument's own
run-to-run variance, which nothing in this project had.

**5 of 22 cells disagree — 22.7%.** [measured]

| cell | writer A | writer B |
|---|---|---|
| `duration-parser` / `qwen3:8b` / 5 | agent_timeout | rejected |
| `event-replay` / `gemma4:31b` / 3 | **passed** | **agent_timeout** |
| `event-replay` / `qwen3:8b` / 1 | agent_timeout | rejected |
| `windows-wsl-path` / `qwen3:8b` / 1 | rejected | agent_timeout |
| `windows-wsl-path` / `qwen3:8b` / 2 | rejected | agent_timeout |

**Every single disagreement involves `agent_timeout`.** None is a pass/reject flip. [measured]

That is not random noise, and it lands exactly where the instrument was already known to be
weak. EXP-07 recorded that the agent timeout overruns by 10–269 s because
`subprocess.run(timeout=…)` kills the direct child while Codex descendants keep the pipes open,
and EXP-31 reuses that control path unchanged. The sweep's item P9 recorded the repair as owed
and unscheduled.

**The row that matters most is the second one.** `gemma4:31b` on `event-replay` attempt 3
**passed** in one execution and **timed out** in the other. The timeout is therefore not merely
censoring slow runs — it is censoring runs that would have succeeded, which biases the measured
pass rate **downward for the model under test**. EXP-31 exists to decide whether the capability
floor is `qwen3:8b` specifically or the tier; a mechanism that randomly converts `gemma4`'s
passes into timeouts attacks that comparison directly. [measured]

Two runners also contend for one GPU, so both ran slower than either would alone, which makes a
wall-clock-triggered timeout more likely in both. The contention and the disagreements are not
independent. [asserted]

## What has deliberately not been done

**`run_exp31.py` has not been modified, and neither runner has been killed.** [measured]

Repairing an instrument during its own run, after seeing what it produced, is the outcome-aware
tampering EXP-07 refused and EXP-31 refused again earlier the same night over its unobservable
stopping rule. The correct response to a compromised run is to record the compromise, not to
quietly improve the instrument until the numbers look better.

Killing a runner is also not obviously reversible: whichever survives writes a file that looks
clean, which is the trap above rather than an escape from it.

## The ratchet — the fix that belongs in code

This project's trajectory log is **append-only**, with a schema version and a digest over
committed positions, and there is a test that a committed position can never change. That
invariant exists because exactly this failure — two writers, last-write-wins, silent loss — is
what append-only prevents.

**The experiment runners do not follow their own project's invariant.** They hold results in
memory and rewrite a whole JSON file. [measured] Every experiment in this repository that writes
a `results-*.json` has the same shape and the same exposure.

The fix, owed before the next registration and not applied here:

1. Runners append one JSON line per completed cell, never rewriting.
2. Every line carries a **run id** generated at start, so two concurrent runs are separable after
   the fact instead of destroying each other.
3. A runner takes a lock, or detects an existing live run and refuses to start — the harness
   already has the concept in ADR-0011's write leases and does not apply it to its own experiments.
4. Analysis reads lines and groups by run id, so an interleaving is visible rather than invisible.

Point 3 alone would have prevented this. Points 1 and 2 would have made it harmless.

## What Joe has to decide

1. **Is EXP-31 re-run?** Recommendation: yes, once the runner is append-only and single-writer.
   Its question — model or tier — is unanswered, and the direction so far (`gemma4:31b` passing
   where `qwen3:8b` never edits a file) is suggestive but now rests on contaminated data.
2. **Do the two partial datasets enter the evidence base?** They are preserved outside it. The
   22.7% disagreement figure is genuinely useful and did not exist before; it is also an accident,
   from an unregistered comparison, under GPU contention.
3. **Does the append-only rule become an invariant for all experiment runners**, with a check, in
   the same commit? That is working principle 3 applied to the instruments rather than the product.

## What would overturn this reading

A single runner that legitimately re-probes VRAM mid-run and re-emits the probe block, which
would make the alternating fingerprint an artefact of my reading rather than evidence of two
processes. I do not find such a path: the probe is written once at start-up, and the 22
overlapping cells with 5 disagreements cannot be produced by one process executing each cell once.
[asserted]

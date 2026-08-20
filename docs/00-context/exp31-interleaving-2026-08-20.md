# EXP-31 has been running twice, into one file, all night

**Found 20 August 2026, 04:05.** The run is compromised. Nothing about it should be believed
without reading this page first. [measured]

## How it surfaced

A routine progress check showed the run count going **backwards** — 28 runs, then 25 about
seventy minutes later. A count that decreases is not slow progress; it is a different file.

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


---

## Update 04:41 — the run is degrading, and it cannot be stopped

**`gemma4:31b`'s timeout rate has risen from roughly 17% to 41%.** At the time this page was
written the model under test showed 10 passes against 2–3 timeouts; it now shows **10 passes
against 7 timeouts** in the richer of the two writers. [measured]

That is the predicted direction. Two runners contend for one GPU, both run slower than either
would alone, and a wall-clock timeout converts runs that would have passed into censored ones. The
contention is not merely contaminating the comparison — **it is worsening**, and it worsens
against the model whose capability the experiment exists to establish.

Both writers' states are preserved again at this point, so the degradation itself is recorded
rather than lost.

### The judgement, and why it could not be carried out

On the evidence above, **stopping both runners is the right call**: the run is already recorded as
compromised, further cells are produced under worsening contention, and each runner is heading for
a `complete: true` file that will look clean. Stopping is reversible — EXP-31 has to be re-run
regardless — so under ADR-0033 it is a decision the harness should take rather than park.

**It could not be executed.** The runners cannot be identified. On this machine
`Get-CimInstance` fails (the PowerShell host cannot read its own config file from OneDrive),
`wmic` is absent, and `psutil` is not installed, so no available tool returns a command line for a
process. `tasklist /v` returns twelve `python.exe` processes with no window titles and no
arguments — and **some of them are this session's own**: the heartbeat monitor, scratch analysis
scripts, and whatever else is running in adjacent sessions. [measured]

Killing on a guess risks taking down the monitor that is watching this very experiment, or another
session's work. **A blind kill is a worse action than an ongoing bad measurement**, so it was not
attempted.

### The finding this produces, which is worth more than the stop would have been

**Detection without identification is half a control.**

ADR-0034 decides that stalls are detected by artefact progress rather than by PID, and it is right
— PIDs recycle and a zombie can hold a pipe open. But the ADR stops at *detecting*. This incident
shows the other half: **a runner that can be detected and not identified cannot be acted upon.**
Tonight the harness could see the problem in perfect detail, could reason about it correctly, and
could do nothing at all.

The fix is the one already owed from § *The ratchet*, and this makes it stricter. A runner must
write a **lock file naming its own PID, its `run_id` and its start time**, and remove it on exit.
That single artefact would have delivered all three things this incident needed and lacked:

1. **Prevention** — the second runner would have found the lock and refused to start.
2. **Attribution** — the interleaving would have been obvious immediately, not inferred from an
   alternating VRAM probe.
3. **Action** — stopping it would have been one `kill` against a named PID, rather than a guess
   among twelve.

A lock file is perhaps ten lines. It is worth more than any of tonight's audits, because it is the
difference between knowing and being able to act.

**Recorded rather than done**, because the ten lines belong in `run_exp31.py`, and changing an
instrument during its own run is the tampering this project has now refused three times in one
night.


---

# Correction 05:05 — two of my claims on this page were wrong, and the instrument is better than I said

One of the two runners finished while I was writing the closing summary, and what it wrote
refutes two things asserted above. Both corrections are against me. [measured]

## Wrong claim 1: "each runner will write `complete: true` and look finished"

**It did not.** The runner carries a pre-registered `wall_clock_cap_s` of 10,800 seconds, hit it
at `elapsed_s: 10799.354`, and wrote:

```
"complete": false,
"stop_reason": "wall_clock_cap"
```

It stopped at **38 of 50 cells**, said so, and named why. It also emitted a `protocol` block
recording its fixtures, attempt budget and timeout, and a `summary` whose registered verdicts read
`insufficient_evidence` on both axes. [measured]

**That is an honest instrument behaving well**, and the "trap" I described — a file that would
shortly stop advertising its own problem — did not materialise for this writer. I predicted a
failure mode from the code shape without checking whether a cap existed. The interleaving defect
is real; this particular consequence I invented.

## Wrong claim 2: "`gemma4`'s timeout rate rose from ~17% to 41%, so contention is degrading the run"

**It is not degradation. It is fixture composition, and I misread a rising aggregate as a trend.**

| fixture | `qwen3:8b` | `gemma4:31b` |
|---|---|---|
| `duration-parser` | 3 rejected, 2 timeout | **5 passed** |
| `event-replay` | 3 rejected, 2 timeout | **5 passed** |
| `windows-wsl-path` | 4 rejected, 1 timeout | **5 timeout** |
| `wilson-verdict` | 2 rejected, 1 timeout | **5 timeout** |

`gemma4` is **5/5 or 0/5 on every fixture**. Not one mixed result. [measured] If GPU contention
were driving the timeouts they would scatter within fixtures; instead they partition perfectly by
fixture. The aggregate rate climbed because the run advanced into two fixtures where `gemma4`
times out deterministically — not because conditions worsened over time.

**This is the more interesting finding, and I nearly buried it under a contention story.**
`gemma4:31b` is bimodal by fixture: it either solves the task every single attempt, or exceeds the
240-second timeout every single attempt. That is a capability-or-latency boundary sitting inside
the fixture set, and it is exactly the kind of structure a median multiplier would hide.

## What stands

The interleaving itself, and its evidence: the probe fingerprint alternating across seven commits,
and **5 disagreements in 22 independently repeated cells**. Two writers did run concurrently and
did overwrite each other. [measured]

And the attribution is now clearer, which is worse for me: the finishing writer ran as a
background task **in this session's own task directory**, labelled *"Relaunch EXP-31"*. **I
started the second runner.** The page above described "two runners, started hours apart" without
saying whose. They were mine.

## What EXP-31 actually found, with its own stopping rule applied

Registered verdicts, from the runner's own summary: **`pass_rate: insufficient_evidence`**
(`qwen 0/5 vs gemma 2/5` fixtures) and **`latency: insufficient_evidence`** (median ratio 1.222,
signs not all the same, 3 censored pairs). The rule fired as written and the honest answer is
insufficient evidence. [measured]

**The observation underneath it is not weak, and it is the one EXP-07 asked for:**

| | attempts | passes | **produced an edit** |
|---|---|---|---|
| `qwen3:8b` | 18 | 0 | **0** |
| `gemma4:31b` | 20 | 10 | **10** |

EXP-07 found `qwen3:8b` produced no file edit in 25 attempts and asked whether that was the model
or the tier. On a **new fixture set**, across four fixtures, `qwen3:8b` again produced **zero**
edits in 18 attempts while a 31B model on the same rig, same harness, same timeout produced ten.
[measured]

**That points at model-specific, not tier-wide** — which was the better outcome and the less
interesting one. It is *not* a registered result: the verdicts say insufficient evidence, the run
is capped at 38 of 50, and it was contaminated by my own second runner. **It should be re-run
clean before it is cited**, and the register entry stays `COMPROMISED`.

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


---

# Correction 05:15 — the timeout mechanism failed catastrophically, so every timing figure here is void

The second runner finished too. **Both were mine**: this session's task list holds *"Run EXP-31 in
the background"* and *"Relaunch EXP-31"*. I launched the same experiment twice and then spent
three hours diagnosing the consequence as though it were someone else's.

Reading the durations against the caps the runner itself applied changes what every
`agent_timeout` in this experiment means.

## The overruns

| | attempts over their own cap | worst overrun | worst as a multiple |
|---|---|---|---|
| writer 29126 | **10 of 28** | **1,771.7 s** | **8.4×** |
| writer 19126 | **16 of 38** | **1,208.8 s** | **6.0×** |

**26 of 66 attempts — 39% — ran past the timeout that was supposed to stop them.** [measured]
One `gemma4:31b` attempt on `windows-wsl-path` ran **2,011.7 seconds against a 240-second cap**.
That is thirty minutes of a process the instrument believed it had killed half an hour earlier.

EXP-07 recorded this defect at **10–269 s**. Under two concurrent runners it reached **1,772 s**.
The mechanism is the one already known: `subprocess.run(timeout=…)` kills the direct child while
Codex descendants keep the pipes open, so the parent returns and the work does not stop.

## What that does to the record

**`agent_timeout` does not mean "the model exceeded the cap and was stopped".** It means **the
stop failed**. The recorded durations are not bounded by the cap and are not measurements of
model latency — they are measurements of how long a runaway process happened to survive.

So: **every duration-derived quantity from this run is void.** The paired first-attempt ratios,
the median ratio, the censoring flags, all of it. The runner's own `latency` verdict already reads
`insufficient_evidence`, which was the right answer for a reason better than the one it gave.

## And it corrects my correction

Twenty minutes ago I wrote that `gemma4` is **"bimodal by fixture — 5/5 or 0/5, never mixed"**,
and called it a capability-or-latency boundary a median would hide. **That reading is confounded
and I should not have stated it as cleanly as I did.**

On `windows-wsl-path`, `gemma4`'s five "timeouts" ran 2,011.7 s, 1,627.5 s, 494.1 s, 446.0 s and
440.7 s. Those are not a model failing to finish inside 240 seconds and being stopped. They are
the instrument losing control. **Whether `gemma4` would have solved that fixture given a working
timeout is unknown**, and this run cannot say.

What survives of it: `gemma4` **did not produce a passing artefact** on those two fixtures in any
attempt, and did on the other two in every attempt. That is still a clean partition. The word
"bimodal" was fine; the causal gloss was not.

## What actually survives, and it is the useful part

**Edit production does not depend on timing at all**, and it replicates across both writers:

| | attempts | **produced an edit** | passes |
|---|---|---|---|
| `qwen3:8b` | **33** | **0** | 0 |
| `gemma4:31b` | 33 | **19** | 19 |

Thirty-three `qwen3:8b` attempts across two independent runs and four fixtures produced **zero
file edits**. EXP-07 saw zero in twenty-five on a different fixture set. That is **58 attempts,
two fixture sets, two runs, no edit.** [measured]

And both writers independently reported the **identical** verdict detail — `qwen 0/5 vs gemma
2/5` — from different cell subsets under different contention. [measured]

**So the capability floor is measurable with this instrument and the latency multiplier is not.**
That is worth more than the experiment's registered question, because it says which half of
EXP-31's design survives contact with the rig: count what the model *produced*, never how long it
took, until the process tree is killed properly.

## Owed, and now unambiguous

The process-tree kill is no longer a tidy-up. **It is a precondition for any duration-dependent
registration**, which the sweep's P9 already said and which this run has now demonstrated at 8.4×
the cap rather than 1.1×. Together with the single-instance lock, it is the whole of what EXP-31
needs before a clean re-run.

Both runners' final states and both stdout streams are preserved in the session scratchpad.


---

# Near miss, 05:27 — removing a dangerous line from a file does not stop a process already running it

While writing the instrument tests I included a cleanup helper that called:

```
taskkill /F /IM python.exe /FI "MEMUSAGE lt 20000"
```

**That kills every Python process on the machine under 20 MB**, not just the strays the test
leaked. On this box that plausibly includes this session's own scratch scripts and whatever
adjacent sessions are running. I noticed it while rewriting the file for a different reason —
the sleeps were too long — and removed it before committing. [measured]

**But I had already launched a test run against the old file.** Editing a file does not stop a
process that has already imported it. The removal protected the commit; it did nothing about the
run in flight.

**Whether it executed is undetermined.** The helper is called at the end of the
broken-pattern test, which blocks for the grandchild's full sleep, and the run was capped at 300 s
against a sleep of 600 s — so on timing it should not have been reached. The task nonetheless
reported exit 0, which a timeout-kill normally would not, so the two signals disagree and I cannot
close it. [asserted]

**Nothing depended on it survived damaged**, and that was checked rather than assumed: 47 product
tests, 5 instrument tests, `mypy --strict` clean, `consil replay` correct, working tree clean but
for the live results file. [measured]

## The lesson, which is not the obvious one

The obvious lesson is "do not write a broad `taskkill`". True, and I had already reached it — that
is why the line was removed.

The one worth keeping is narrower and I did not have it: **a destructive command becomes live the
moment a process reads it, and editing the file afterwards is not a recall.** Tonight this
project twice refused to change an instrument mid-run on the grounds that it would be tampering.
The same reasoning applies in the other direction — a *fix* applied mid-run does not take effect
either, and believing it has is worse than knowing it has not.

Combined with the earlier finding that a runner which cannot be identified cannot be stopped, the
rule is: **anything that can destroy state must be safe at the moment it is written, because there
may be no point afterwards at which it can be recalled or stopped.** [asserted]

Concretely, for this repository's own tooling: no `taskkill` or `kill` may target a process by
**image name or a resource filter**. It targets a specific pid, obtained from a lock file the
target itself wrote — which is precisely the artefact `run_exp31.py` now creates.


---

## Postscript 05:32 — the monitor was doing the thing ADR-0034 forbids

The overnight heartbeat reported `EXP-31 running: 28 runs, 27238B` at check-ins 4 and 5, after
both runners had exited. It had ten more of those to emit over the next seven hours. [measured]

It inferred *running* from a byte count it could read, not from whether the work was progressing —
and the byte count was frozen precisely **because** the work had stopped. **A stalled artefact and
a finished one look identical to a monitor that only reads the artefact.** ADR-0034 chose artefact
progress over PID liveness because PIDs recycle and zombies hold pipes; this is the cost on the
other side, and the ADR does not name it.

The fix is not to go back to PIDs. It is that a monitor must read the **terminal state the work
writes for itself** — here, `complete` and `stop_reason`, both present in the results file and both
saying the run had ended under its wall-clock cap. The heartbeat read the file's size and ignored
its contents.

Stopped, rather than left to repeat a false statement ten more times into the maintainer's morning.
The same reasoning as the replay check: **a signal that reports a state it did not verify is worse
than no signal, because it is read as verification.**

**A near-miss in the same breath.** The check-in also showed VRAM going from 29,436 to 3,489, and I
read that as *"something is now holding 26 GB"* and went looking for what to free. It is the
opposite: the heartbeat reports **used** VRAM, so the number falling means the model unloaded and
the card is idle. `nvidia-smi` says 3,489 used against 28,699 free at 1% utilisation. [measured]
I checked before acting, which is the only reason this is a postscript and not another incident —
**a monitor that does not label its units invites exactly this, and mine did not label them.**


---

# Clean re-run started 08:59, and the fix is verified on the real workload

The register said the run must be repeated. The instrument is repaired, the repair is tested, and
the run takes about three hours — so it is started rather than parked. Under ADR-0033 that is the
harness's call: the registration is unchanged, the execution is reversible, and the alternative is
a COMPROMISED experiment sitting untouched.

## Pre-flight, because a three-hour run that crashes on attempt 1 is worse than not starting

The repaired `run_attempt` was called once against the **real workload** — an actual Codex/Ollama
invocation on `duration-parser` with `qwen3:8b` — under a deliberately short 45-second cap. A
synthetic sleeper would not have tested the thing that broke.

```
outcome            agent_timeout
duration recorded  45.186s
timeout applied    45s
overrun recorded   0.186s
```

**0.186 seconds past a 45-second cap.** [measured] The same code path previously overran by up to
**1,771.7 seconds against a 240-second cap**. From 8.4× the cap to 1.004×.

## The lock, verified in production rather than only in tests

With the run under way, a second launch was attempted deliberately:

```
REFUSING TO START: run.lock is held by pid 21636 (run exp31-20260820T085909-21636),
started 0.3 min ago, within the 180 min wall-clock cap. Two concurrent runners
overwrite each other's results.
```

[measured] That is the exact failure of 20 August, refused at the door, naming the holder. The
lock file carries `pid`, `run_id` and `started_epoch`, and the `run_id` is stamped into the
results payload — so if an interleaving ever does happen again it will be visible in the data
rather than inferred from an alternating VRAM probe.

## What this run can and cannot settle

**Can:** whether `gemma4:31b` clears the capability floor `qwen3:8b` has failed in 58 attempts
across two fixture sets; and whether the fixture-level partition seen before was real or an
artefact of the broken timeout. That second question is only askable now — with the timeout
bounded, a censored run genuinely means "did not finish in 240 s" rather than "the instrument lost
control".

**Cannot:** anything the registration does not already cover. The protocol, fixtures, attempt
budget and stopping rules are unchanged and were not touched. If the verdicts come back
`insufficient_evidence` again, that is the answer.

**One honest caveat.** This is a re-run of a registered experiment whose previous execution this
same session voided. The instrument changed between them, which is exactly why the earlier data
cannot be pooled with this — and pooling it would be the outcome-aware move the project has
refused three times. The two capped datasets stay outside the evidence base.

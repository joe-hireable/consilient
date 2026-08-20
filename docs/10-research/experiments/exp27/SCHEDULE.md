# EXP-27 daily collection — how it is scheduled, and how to tell if it stopped

**Scheduled 20 August 2026** on Joe's instruction. The register's own warning was that a window
specified in days loses a day for every day nobody runs the collector, and that the loss is
silent. This exists so it is neither manual nor silent.

## What is scheduled

| | |
|---|---|
| Task | `Consilience-EXP27-Collector` |
| Runs | daily at **09:00**, first fire **21 August 2026** |
| Action | `docs/10-research/experiments/exp27/run-daily.cmd` |
| Log | `.harness/exp27-daily.log` in the **main checkout** |
| Definition | `scheduled-task.xml`, committed here so the schedule is reproducible rather than folklore |

**Verified at creation**, by artefact rather than by the success message: task `Ready`, next run
21/08 09:00, an on-demand run returned `Last Result: 0`, and the log grew from 11 to 22 lines
with six of six sources reachable. [measured]

## The settings that matter, and why

- **`StartWhenAvailable: true`** — a laptop that was asleep at 09:00 runs the collector when it
  wakes instead of skipping the day. This is the single most important setting here.
- **`RunOnlyIfNetworkAvailable: true`** — a run with no network would record six failures and
  make the day look collected when it was not.
- **`RestartOnFailure`, 3 attempts 30 minutes apart** — a transient outage should not cost a day.
- **`DisallowStartIfOnBatteries: false`** — the default would skip on battery, which on a laptop
  is most of the time.
- **`InteractiveToken`** — runs as Joe when he is logged in, with no stored credentials. The
  trade is that a day he never logs in is a day missed; storing a password to avoid that is not
  a trade worth making for a read-only poll.

## The wrapper, and why it is not a bare `python` call

**A scheduled task that fails silently is worse than no scheduled task**, because the window then
accumulates missing days while looking healthy. `run-daily.cmd` therefore:

- prefers the worktree checkout and **falls back to the main checkout**, so it keeps working after
  this branch is merged and the worktree removed;
- **writes a loud failure to the log if the collector is in neither place** — the specific way
  this could die quietly;
- timestamps every run, records which checkout it used, and preserves the collector's exit code.

## How to tell if it stopped

One command. The day count is the thing that matters, and it comes from the data rather than from
the scheduler:

```
python docs/10-research/experiments/exp27/collector.py
```

It prints `distinct days recorded N of 30`. **If N stops advancing, the window has stalled** —
regardless of what Task Scheduler claims. Running it by hand is safe and idempotent: a second run
on the same day returns `304 unchanged` on every source and adds no events, so the count cannot
be inflated by re-running.

To see the scheduler's own view:

```
schtasks /Query /TN "Consilience-EXP27-Collector" /FO LIST /V
tail -30 ../../../../.harness/exp27-daily.log
```

## Removing it

```
schtasks /Delete /TN "Consilience-EXP27-Collector" /F
```

That is the whole reversal. It touches nothing else, and the collected log survives deletion.

## What is still owed

The registration also requires a **dispatch-time version/capability handshake** (procedure step 4)
and **three injected fixtures** — a community hint, a "limits increased" notice, and an active
outage (step 5). Neither blocks the clock, and **both must land before the window closes or the
run cannot answer its own question.**

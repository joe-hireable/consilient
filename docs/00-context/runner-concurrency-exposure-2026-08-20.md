# Every experiment runner has the defect that compromised EXP-31

**20 August 2026.** After EXP-31 was found running twice into one file
(`exp31-interleaving-2026-08-20.md`), the obvious next question was which other experiments carry
the same exposure. Audited by Cursor (Gemini 3.7 Flash) over every runner in
`docs/10-research/experiments/`; the EXP-07 verdict below was established separately by hand.

**Headline: all four runners that write a results file have it, and only EXP-31's was detectable
— by luck.** [measured]

## Exposure

| Runner | Write mode | Concurrent-safe | Damage detectable later | Second-instance guard | In git |
|---|---|---|---|---|---|
| `exp31/run_exp31.py` | whole-file rewrite of in-memory dict | no | **partly, by accident** — the `probe` block differed between the two processes, and disappears once complete | none | yes |
| `exp07/run_exp07.py` | whole-file rewrite via atomic rename | no | **no** — no run id, no PID, no per-attempt timestamp | none | yes |
| `exp05/run_all.py` | read–modify–rewrite of the whole list | no — races on read-merge-write | **no** — rows name the `agent` but carry no run id or execution time | none | yes |
| `exp01/mine_beta.py` | whole-file rewrite at exit | no | **no** | none | **no** — `data/` is gitignored, so there is no recovery at all |

Scripts that write only to stdout — `exp27/probe_sources.py`, `exp05/run_exp05.py`,
`simulations.py`, `robustness_beta_star.py`, `q3_bimodal_and_q2_sample_complexity.py`,
`probe_delta_ci.py`, `capability_context_beta_star.py` — carry no exposure. [measured]

**Zero runners that write a results file are clean.** The atomic rename in `run_exp07.py` makes
each write atomic, which prevents a torn file and does nothing whatsoever about last-write-wins.

## EXP-07 cannot be cleared, and it is the one that matters

EXP-07 decided ADR-0003. It produced the 17.95× best-of-five multiplier, the capability-floor
finding, and the frozen fixtures and timing controls that EXP-31 imports by reference. It ran
**unattended for 68 minutes** overnight on 20 August.

The same technique that caught EXP-31 — reading the file's own history for a fingerprint that
alternates — was run against it. The result: [measured]

- **One commit** has ever touched `results-exp07.json`, at 01:59:41, already carrying 30 runs and
  `complete: true`. There is no history to compare.
- Its run records carry `fixture`, `model`, `attempt`, `provider`, `outcome`, durations and usage
  — and **no run id, no PID, no per-attempt timestamp**. No fingerprint exists to alternate.
- **No duplicate cells** in the final file, which is consistent with a clean run and equally
  consistent with an interleaved one, since the last writer's file is internally coherent by
  construction.

**EXP-07 is not condemned. It is unverifiable.** [measured] Nothing in the repository can
establish whether it ran once or twice, and that is a worse position than EXP-31's, where the
compromise is at least visible. EXP-31 was detectable only because its probe block happened to
record free VRAM, which happened to differ between the two processes. **That was luck, not
design.**

## Ranked by what it would cost if unsound

1. **EXP-07** — `DONE`, decided ADR-0003, and the direct parent of EXP-31's instrument. Redoing
   it costs roughly 70 minutes of dedicated GPU plus five frontier Codex calls, and reopens
   ADR-0003's status until it lands.
2. **EXP-01** — `IN PROGRESS`, the β measurement itself, cited across ADR-0002, ADR-0012,
   ADR-0013 and five experiments. **Its output is gitignored**, per the privacy rule, so unlike
   the others there is no accidental backup and no possibility of the recovery that rescued both
   EXP-31 datasets. It is also the experiment already found to be measuring the wrong conditional
   — see `beta-axis-defect-2026-08-20.md`.
3. **EXP-05** — `DONE`, decided ADR-0001. Lower risk: short supervised single-ticket
   invocations, and the results file is committed so history exists.
4. **EXP-27 phase A** — negligible. Stdout only, 1.3 seconds, free to re-run.

## The fix, which is to adopt an invariant this project already has

`src/consilient/events.py` is clean and has been all along: append-only writes, a schema
version, RFC3339 timestamps with an explicit offset, and a prefix digest that makes a committed
position immutable. There is a test asserting exactly that. [measured]

**The instruments do not follow the product's own rule.** Four changes, in order of how much
each would have helped:

1. **A single-instance guard.** A lock file, or a per-run results path
   (`results-<exp>-<run_id>.jsonl`), so a second instance refuses to start or cannot collide.
   *This alone would have prevented the EXP-31 incident entirely.*
2. **Append one line per completed cell**, never rewriting. Makes a collision harmless rather
   than destructive.
3. **A `run_id` and a `ts` on every record**, generated once at start-up. Makes an interleaving
   *visible after the fact* — which is the property EXP-07 lacks and cannot now be given
   retrospectively.
4. **Summaries computed as a projection** over the appended stream, grouped by `run_id`, rather
   than written from in-memory state as a monolithic block.

Items 1 and 3 are the ones that matter. The first prevents; the third makes prevention
falsifiable.

**This is working principle 3 turned on the instruments.** The project requires that any declared
invariant ship with the check that enforces it, and applies that rigorously to product code while
its measurement apparatus quietly does the opposite of what the product guarantees.

## What could not be established

- **Whether EXP-07 actually suffered a concurrent run.** Unanswerable from the artefacts, as
  above. External evidence — OS process history, provider-side API logs for the five frontier
  calls — might settle it, and is outside the repository.
- **Whether EXP-01 lost intermediate data.** `exp01/data/` is gitignored, so there is no record
  of what was written before the summary in `findings-exp01.md`.

## What Joe has to decide

1. **Do the four changes land, with a check, before any further experiment is registered?**
   Recommendation: yes, and item 1 alone before anything is re-run.
2. **Is EXP-07 re-run to make it verifiable**, or is its result carried forward with an explicit
   "unverifiable, single unattended run, no run identity" caveat attached wherever it is cited?
   The second is cheaper and honest; the first is what the project's own standards imply.
3. **Does `exp01/data/` stay gitignored?** The privacy rule requires it and the privacy rule is
   right. But it means the β corpus has no recovery path at all, and that trade should be a
   decision rather than a side effect.

# EXP-07 — the wasted-work multiplier, replicated

Run 20 August 2026, 00:19–01:27 (4,106 s elapsed, inside the 5,400 s cap). Protocol frozen
before the run in `experiment-register.md` § EXP-07 and in the instrument-repair amendment.
Raw result: `results-exp07.json`, sha256 `77ad4175…`. [measured]

`complete: true`, `stop_reason: null`, 30/30 attempts, no stopping rule fired. [measured]

## What ran

Five frozen public fixtures. One `gpt-5.6-sol` Codex-subscription attempt at low reasoning
effort per fixture, and five independent serial `qwen3:8b` local attempts through the same
Codex harness. Fresh temporary repository per attempt; identical functional-plus-changed-file
verifier with the fail-closed scope gate. Subscription use stayed at 5% across all five
headroom snapshots. [measured]

## Result

| | frontier | local |
|---|---|---|
| passes | **5 / 5** | **0 / 25** |
| median duration incl. verifier | 44.2 s | 97.7 s |
| range | 39.7 – 81.2 s | 44.4 – 509.3 s |

| multiplier | as recorded | clamped (see instrument defect) | pre-registered verdict |
|---|---|---|---|
| single attempt | median **1.69×** | 1.69× | `insufficient_evidence` |
| best of five | median **17.95×** | **16.75×** | `replicates_2x_trigger` |

Per-fixture best-of-five, clamped: 16.75, 18.58, 5.36, 22.59, 8.22. Every fixture is above
2× under the most conservative reading. [measured]

## The verdict, applied as written

The register fixed this before the run: *"If the multiplier crosses 2× **only** with the
reasoning layer enabled, the finding is 'scaffolding is what makes routing priors worthwhile'
— record it that way rather than as a blanket reopening."*

That is what happened. **ADR-0003 is not blanket-reopened.** [measured] The single unscaffolded
local attempt does not cross the threshold; the serial best-of-five intervention crosses it by
a factor of eight. The wasted work is created by the retry layer, not by the raw local attempt
being slow.

**The n=1 pilot did not replicate on its own terms.** The 19 August pilot measured 5.6× on a
single attempt and that reading is not reproduced: the replication median is 1.69×, and three
of five fixtures sit between 1.20× and 1.69×. [measured] The pilot's headline number was a
single draw from a wide distribution.

The single-attempt verdict is `insufficient_evidence` rather than `fails_to_replicate`,
because two of five pairs are censored and the instrument's own limitation is that a censored
duration "can prove a crossing but can never prove a non-crossing". [measured] That rule is
applied here against the result the author would have preferred.

## The finding the multiplier was hiding

**`qwen3:8b` produced no file edit in any of the 25 attempts.** Every local run recorded
`changed_files: []`, and the verifier tail shows the untouched stub raising
`NotImplementedError`. [measured] One rejected run consumed 30,243 input and 10,664 output
tokens to change nothing.

So the multiplier is not measuring a cheap model writing bad code. It is measuring a cheap
model **consuming tokens and producing no artefact at all**. That is a capability floor, not a
latency finding, and it is more decisive than the multiplier: at this configuration the local
tier is not a viable first rung, and no routing policy can rescue a tier that never emits a
diff. [asserted]

Whether that is `qwen3:8b`, the Codex `--oss` control path, the reasoning mode or the fixture
difficulty is **not established here**. EXP-31 substitutes the installed `gemma4:31b` into the
identical composition and is the registered next step. [asserted]

## Instrument defect found in this run

**The agent timeout overruns.** All six censored runs exceeded their 240 s applied timeout —
by 9.8, 20.6, 21.6, 50.5, 53.2 and 269.3 seconds. [measured] `subprocess.run(timeout=…)` kills
the direct child, but Codex spawns descendants that keep the pipes open, so the parent waits
past the deadline. A censored duration is therefore neither the timeout value nor a clean
lower bound; it is inflated by an unbounded amount.

This inflates any multiplier derived from a censored run, which is 4 of 5 best-of-five pairs.
The sensitivity analysis above clamps every censored duration to its applied timeout — the
most conservative available reading — and the crossing survives at 16.75×. [measured] The
verdict does not depend on the defect.

**The fix is a process-tree kill, not a longer timeout**, and it belongs in the instrument
before any run whose conclusion depends on a censored duration. It is recorded rather than
applied, because changing the instrument after seeing the result and before the register says
so is outcome-aware tampering.

## Checklist items from the handoff manifest

1. **Verifier instrumentation failure distinguished from model scope violation.** 0
   `verifier_error` outcomes and 0 scope violations. All 25 local failures are 19 `rejected`
   and 6 `agent_timeout`. Nothing needed excluding. [measured]
2. **True verifier errors excluded from eligible pairs; model scope failures retained.** No
   instances of either arose. [measured]
3. **Out-of-repository writes are not observable.** The runner invokes Codex with
   `--dangerously-bypass-approvals-and-sandbox`, and the scope gate only inspects the
   temporary repository. A write outside it would be invisible to this experiment. No such
   write is alleged; the point is that this run cannot exclude one. [measured]
4. **Test suite and hash.** 15 tests pass, and `results-exp07.json` hashes identically before
   and after — `77ad4175…`, 36,957 bytes. The autouse temporary-path fixture prevents the
   failure that destroyed the first completed run. [measured]

## Limitations

The instrument's own three stand unchanged: reasoning modes are not matched between
`gpt-5.6-sol` at low effort and `qwen3:8b` at its Ollama default; timed-out attempts are
right-censored; synthetic fixtures can replicate a latency mechanism but cannot establish that
a learned router improves real work. [measured] Added by this run: the timeout overrun above,
and n=5 fixtures on one local model, which is a sample too small to characterise a
distribution the pilot has already been shown to misrepresent. [asserted]

## Publication disposition

**Research note candidate.** [asserted] The protocol was fixed before the run, the instrument
and result are reproducible, the stopping rule was applied unchanged against the author's
preference, and the limitations are explicit. The interesting content is the negative
replication and the no-artefact finding, not the multiplier. G2 novelty has not been checked.
[asserted]

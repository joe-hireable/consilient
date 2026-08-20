# Morning briefing — 20 August 2026

Written for Joe to read over coffee. Ten commits landed overnight across Claude Code, Codex and
Cursor. This page orders what you have to decide; everything else is detail you can reach from
here.

**The short version.** The night was mostly spent finding out that several things we believed
were not true. That reads badly and is the system working — every one of these would have been
far more expensive after v1. The instrument is materially stronger than it was at midnight. The
evidence base is materially less certain.

---

## 1. What you must decide, ordered

### 🔴 A. Which quantity is β?
`beta-axis-defect-2026-08-20.md`

ADR-0002 and `src/consilience/beta.py` define **β = P(checks accept | artefact bad)**.
`exp01/mine_beta.py` computes **P(bad | checks accepted)** — the transpose — and says so in its
own output string. The only empirical β this project has is not the quantity the architecture is
built on.

It hid behind a coincidence: on `jobboard-v2` the denominators are 202 and 203, so the error moves
the number by 0.49%. On `hireable-platform`, in the corpus the whole time, it is 0.4286 against
0.8182.

**Time-critical:** the ~146-pair audit is the largest block of agent-hours queued against EXP-01
and would sharpen an interval on the wrong axis. **Recommend it waits for your answer.**

Nothing in `docs/10-research/` was repaired. Which quantity you want is a design decision, not a
bug fix — P(accept|bad) is what the architecture rests on; P(bad|accept) is arguably what a
practitioner wants from a green build; carrying both roughly doubles the sample-size problem.

### 🔴 B. ADR-0019 forbids standing spend caps. Four later documents assume them.
`cross-family-audit-2026-08-20.md` § 4

ADR-0019: *"Standing authorisation for a class of purchases"* is explicitly forbidden;
*"unattended runs cannot acquire paid capabilities."* ADR-0026, ADR-0028, ADR-0033 and
`v0-draft.md` § 7.2 all assume the opposite. ADR-0019 marked the question **Unresolved** and it
has stayed unresolved while four documents assumed a resolution. Only you can overturn it, and it
is why OpenRouter screening is still blocked.

### 🔴 C. The blind grading pack is ready — 18 decisions, arm labels stripped
`docs/10-research/experiments/exp16/grading-pack.md`

This decides ADR-0020, the whole authority matrix, and spec invariants V0-11 and V0-20. Read the
pack, write your answers down, **then** open `grading-key-SEALED.md`.

Honest limits, all in the key: Arm A versus Arm B — the comparison the stopping rule actually
needs — has no discriminator the builder could find. Arm C is probably identifiable, because it
recorded no dissent on any of the six while A and B recorded it on all six; that asymmetry *is*
structural finding 1, and manufacturing dissent into C would have made the pack blind and
worthless.

All three arms were found living **only in a session temp directory** and are now preserved in
the repo. That experiment was one housekeeping sweep from being unreproducible.

### 🟠 D. Do the experiment runners get the guarantee the product already has?
`runner-concurrency-exposure-2026-08-20.md`

**EXP-31 ran twice, into one file, all night.** Two runners, each rewriting the whole file from
memory, last write wins. Caught because the run count went *backwards*.

All four runners that write a results file have the same exposure. **EXP-07 cannot be cleared** —
it has no run id, no PID, no per-attempt timestamp, so an interleaved run would look identical to
a clean one. It is not condemned; it is *unverifiable*, and it decided ADR-0003.

A single-instance guard alone would have prevented this. A `run_id` per record would have made it
visible.

### 🔴 D2. Gate B2 cannot fail, and it is the only gate β can move
`gate-b2-and-the-unconnected-meter-2026-08-20.md`

Gate B2 asks whether the derived parallelism ceiling exceeds 1. Under the project's own model,
`frac_seen ≤ 1` so `T_eff ≤ T_r`, giving `n_max ≥ 25/8 = 3.125` **for every critic recall and
therefore every β, including β = 1.0** — a critic that catches nothing. A threshold below the
minimum possible value of the quantity it gates passes by tautology. [measured]

ADR-0015 states the false belief plainly: *"If measured critic recall yields a ceiling of 1…"* —
recall cannot lower the ceiling, only raise it.

**Gate B2 is the only gate condition whose value depends on β.** Every other asks whether
something exists, ran, or completed. As things stand, **β gates nothing.**

Verified independently after being raised by an attack run; the ceiling table is also tagged
`[algebra]` while being that formula evaluated on three unmeasured point estimates.

### 🟠 E. Two Ollama upstream reports, drafted not sent
Outward-facing, carries your name. ADR-0036 § 3 holds our outbound work to the standard we ask of
inbound.

### 🟠 F. EXP-27's 30-day clock is not running, and every day is unrecoverable
ADR-0029 cannot promote before ~20 September, later for each day lost. It needs a read-only
collector — no inference, no metered provider — which is inside the observe-only envelope on a
plain reading, but it is new product code and that gate is yours. **One sentence unblocks a
month.**

---

## 2. The finding I would put in front of everything else

**The β meter has never received a single row of its own input.**

60 trajectory events across two days. **60 distinct event kinds. Zero `attempt.outcome` events.
Zero human verdicts.** `consil beta` says, correctly:

```
beta [all]: insufficient data (0 human rejections, need 30)
```

The trajectory is being kept as a **diary**, not as an instrument — every event a one-off kind,
nothing measured twice. Gate A condition 3 counts "seven consecutive days of trajectory capture"
and is being satisfied by narration.

And the arithmetic says what it would take. Using the repo's own `wilson()` against its own
β\* = 0.111: at **0/30** the upper bound is 0.11352 and **fails**; at 0/31 it is 0.11026 and
clears. So `MIN_REJECTIONS = 30` sits exactly one sample below the smallest n at which even a
flawless record could clear the threshold. Realistically: **48** rejections at true β = 0.02,
**62** at 0.04, **137** at 0.06, **368** at 0.08, **3,045** at 0.10, and **never** at or above
0.111 — while EXP-01's two corrected estimates are 0.12 and 0.14.

Stated fairly: the constant is not a bug — it gates the `measured` verdict, not a routing claim.
What the arithmetic shows is that **no routing decision can ever be taken at the evidence floor as
set**, and neither the code nor the specification says so.

**The cheap thing that changes this:** start recording real `attempt.outcome` events with your
verdicts on actual work. Nothing else in the project generates the input its central quantity
needs.

---

## 3. What is genuinely stronger than it was at midnight

- **V0-18 was bypassable and is not now.** `_check_human_authority()` returned early unless
  `human_decision` was present, while `projection._apply_outcome()` read `human_verdict` straight
  off an `attempt.outcome` event into the table β is computed from. **An agent could author the
  human verdict β is measured against.** Closed, with five tests.
  The suite could not see it because the *fixture* built agent-authored verdicts and passed. *A
  fixture that can construct a state the invariant forbids will train the suite to permit it.*
- **Gate A condition 2's check could not fail.** `cmd_replay` built from the log twice and
  compared the two rebuilds, after unlinking the state whose drift it existed to detect. It now
  compares disk against rebuild and reports `compared: false` rather than a pass when there is
  nothing to compare. A new test drifts the database out of band; the old check could not have
  caught it. **The gate's "satisfied" record is withdrawn.**
- **A measured β could be constructed with no evidence behind it.** Zero rejections, an inverted
  interval, a point outside its own interval — all constructible. Now refused, and
  `min_rejections` may only be raised, never lowered.
- **Timestamps are checked in code.** `append()` refuses a `ts` more than 15 minutes from the
  clock. See § 4.
- **45 tests, up from 27.** `mypy --strict` clean.
- **ADR-0026 amended** so unknown headroom disqualifies *unbounded* work only — which is what put
  Cursor to work all night instead of idle.
- **ADR-0016 corrected**: it published skills to npm while ADR-0032 chose Python the same day.
- **V0-02 corrected**: it required byte-identical SQLite state, which SQLite cannot provide. The
  shipped `state_digest` was already stronger than the document.

---

## 4. My own errors, since you should not have to find them

- **I fabricated timestamps.** Six consecutive trajectory events, drifting up to 2h15m ahead — I
  advanced a plausible clock in my head instead of reading one. Two Slack posts headed 06:00 and
  06:30 were actually ~03:55 and ~04:05. The log is append-only so nothing was rewritten; a
  correction event enumerates all seven with their real times. `validate()` checked the *format*
  of `ts` and never asked whether it was true. A format check on a timestamp is not a check on a
  timestamp. Now checked in code.
- **I overclaimed consilience and my own control killed it.** I recorded that two model families
  independently found the β axis defect and called it the first time the project's central claim
  had been tested on itself and passed — and pre-registered the overturning test in the same
  paragraph. Running it took twenty minutes. A **same-family** arm found the same defect, same
  file, same lines, same figures, and reproduced the Gemini arm's counterexample too.
  **The blind leaked and I built the leak:** I had committed the finding to the trajectory log
  *inside the repository the control was told to read*. All three arms also got the same five
  attack angles, so the common cause may be the prompt rather than the corpus.
  **You cannot run a blind experiment inside the repository you write your findings into.** The
  defect survives, stronger for three verifications. The claim does not. We have no measured
  evidence that difference-of-class does anything for us — which is where we were yesterday.
- **I gave Cursor a `docs`-only snapshot** and it correctly reported `src/consilience/` as absent
  — as phantom code with fabricated benchmarks. My staging error, and the lesson belongs in the
  product: *an agent given a partial corpus will report absence as a finding, and absence is the
  one claim a partial corpus cannot support.*
- **I ran an agent at the evidence base** to add publication dispositions, and the safety
  classifier blocked it. It was right: `AGENTS.md` says ask first before touching
  `docs/10-research/`, and I had rationalised that a policy-required section was exempt. Those
  four dispositions are still owed and are yours to authorise.
- **ClickUp is rate-limited to me for ~13 hours**, so the board stops partway. Worth noting
  against the record: EXP-16 concluded rate limits did *not* bite, and sustained low-concurrency
  use overnight contradicted that.

---

## 5. Where the machines are

| Runtime | Did | State |
|---|---|---|
| Claude Code | 14-agent β attack; 9-agent documentation-debt batch with review; same-family control; the fixes and commits | idle, awaiting you |
| Cursor (Gemini) | ADR contradictions; invariant-enforcement audit that found the V0-18 hole; independent β attack; runner exposure audit; verification pass | running |
| Codex (GPT) | numbers-traceability audit — 382 claim bundles, 336 adjudicated, **184 reproduce, 13 do not, 139 untraceable** | report being emitted |
| Ollama / local | EXP-31, compromised | running, results not to be believed |

Codex's report is preserved at `codex-numbers-audit-2026-08-20.md` — 26 of its 33 findings; six
were lost to an output cap I set, which is recorded there rather than papered over.

**The one already acted on, because it is a safety claim.** ADR-0002 said *"the false-safe rate
is **0** at every sample size tested"*. Running the script the ADR names as its own executable
model prints **0.003 at n = 50** and **0.001 at n = 100** for a genuinely unsafe repository at
β = 0.15. The script's own note says the rate *"must be ~0"* — true, and a different claim from
*"is 0"*. **A tilde was dropped in transcription and an approximation became a guarantee.**
[measured]

The exact binomial agrees with the script rather than the prose: 0.0029055 and 0.0015527,
predicting 23.2 and 12.4 false-safes across the 8,000 draws used; observing none at n = 50 has
probability 8 × 10⁻¹¹. **Worse where it matters** — at true β = 0.12, barely above β\* = 0.1119,
the rate at n = 50 is **0.0131**, about 105 in 8,000. The rule is weakest exactly where a
repository is marginally unsafe.

Verified three ways before touching anything: Codex's arithmetic, an independent exact-binomial
computation, and running the script unchanged. The decision rule survives; the zero-error claim
does not. This project's thesis is that tests have error rates — advertising its own rule as
having none is the error it exists to catch, in its founding ADR.

**Not yet verified, and not to be quoted until they are:** EXP-01 carrying three incompatible
audit denominators (32, 40 and 30); ADR-0012's dependence bound; a 69%→28% figure that ADR-0033
and ADR-0035 both lean on while conflicting with the repository's own later full-read
bibliography entry; ADR-0011 and ADR-0019 sharing a corrupted "21 frameworks" denominator; and
EXP-01's β estimates having no retained raw labels, which Codex ranks as the single most
consequential untraceable claim in the repository.

---

## 6. If you only do three things

1. **Answer the β axis question** (§ A) and say whether the ~146-pair audit waits.
2. **Grade the pack** (§ C) — it is built, blind, and blocks the largest open decision.
3. **Say one sentence about EXP-27's collector** (§ F) — it costs a month per day of delay.

And if you have appetite for a fourth: **Gate B2** (§ D2). A gate that cannot fail is worse than
no gate, because it manufactures the appearance of a check — and it is the only place β touches a
decision at all.

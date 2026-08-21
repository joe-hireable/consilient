# Getting started

**PRODUCT**, except the one box marked **machine-local**. Written 21 August 2026.

Every command on this page was run on that date and every quoted output is what it printed.
Numbers carry their evidence: `[measured]` I ran it and read the artefact, `[cited]` a named
source, `[asserted]` my judgement. Anything I could not run is marked **untested** rather than
quietly included.

You do not need to have read anything else. Links at the bottom are for when you want them.

---

## 1. What you can do with this today

Four commands, and not one of them stands between you and your work.

| | |
|---|---|
| `consil record` | append one checked event to the log |
| `consil replay` | rebuild the state from the log and confirm it still matches |
| `consil beta` | report how often the checks were wrong |
| `consil doctor` | report which gates are open |

`[measured]` — that is the whole command set, from `consil --help`.

**It cannot route a task, pick an agent, block a change, hold a gate shut against you, or run
anything unattended.** There is no flag that makes it do any of those. The last line `consil
doctor` prints is:

```
routing/orchestration enabled: no
```

`[measured]` and that is the honest summary of the tool as it stands.

What it *can* do is start a clock. The number this project exists to produce — how often your
checks accept work you would have rejected — cannot be computed until you have rejected things in
front of it. Today it reads zero rejections out of the thirty it needs `[measured]`. Nothing else
in the project moves until that denominator does.

---

## 2. What to type first

> **Machine-local.** Substitute your own checkout path. `<checkout>` is the consilient working
> tree you want to measure; the published tree is the one to use.

```powershell
cd <checkout>
.\.venv\Scripts\activate
consil doctor
```

What it printed today, abridged to the verdicts:

```
Gate A: FAIL
  A1 FAIL: EXP-01 complete on two differently verified repositories with an interval
  A2 PASS: Replay reproduces an identical canonical state digest
  A3 FAIL: Seven consecutive days of trajectory capture with no data loss
    Latest capture run is 3/7 days, 2026-08-19 through 2026-08-21.
Gate B: FAIL
  B1 PASS: EXP-05 complete and adapter two required no shared-interface redesign
  B2 FAIL: The critic tier's own beta is measured, with an interval
  B3 PASS: A one-command bare-Claude-Code fallback is exercised weekly
  B4 FAIL: Twenty non-Consilient tickets complete without harness intervention
    0 of 20 tickets completed on a repository other than this one.
routing/orchestration enabled: no
```

`[measured]` 21 August 2026, run from the published tree against its own log and state.

**It exits 1.** That is correct behaviour while the gates are shut, not a fault, and it means
`consil doctor && something-else` will never run the something-else `[measured]`. Do not chain it.

---

## 3. The one rule that matters more than the rest

**Type `consil`. Never `python -m consilient.cli`.**

Same directory, same log, same day, the two disagree:

| | first Gate A line | exit |
|---|---|---|
| `consil doctor` | **FAIL** | 1 |
| `python -m consilient.cli doctor` | **PASS** | 0 |

`[measured]` — both run from the published tree on 21 August.

The reason is that on this machine `import consilient` resolves to a **different working tree**
(`…\consilient-w-p5\src\consilient\__init__.py`), because of an editable install left on the
system interpreter by another checkout `[measured]`. So `python -m` measures one tree's data with
another tree's code, silently, and the stale code is the one that says the gate passed.

Two things make this survivable rather than frightening:

- `consil` only exists inside a checkout's own virtual environment. In a fresh PowerShell with
  nothing activated, `consil` is **not found at all** `[measured]` — a loud failure, which is the
  good kind.
- You can confirm the instrument in one line. `(Get-Command consil).Source` must print a path
  **inside the checkout you are standing in** `[measured]`.

If a repair lands that makes the tool announce its own provenance, this section shrinks to a
sentence. It had not landed when this was written `[measured]`.

---

## 4. Your first measurement, on your own work

Two events. The first says what your checks decided. The second says what **you** decided. They
are joined by one `attempt_id`, and only the second one moves the number.

Do this the next time you review a change and reject it.

```powershell
# once per session
cd <checkout>
.\.venv\Scripts\activate
$L = "<checkout>\.harness\log"

# 1. what the checks said
$ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
consil --log $L record --event ('{\"v\":1,\"ts\":\"' + $ts + '\",\"event\":\"attempt.outcome\",\"actor\":\"claude-code\",\"data\":{\"repository\":\"joe-hireable/my-side-project\",\"attempt_id\":\"a1\",\"task\":\"TCK-1\",\"task_family\":\"bugfix\",\"verifier_version\":\"pytest\",\"verifier_accept\":true}}')

# 2. what you said
$ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
consil --log $L record --event ('{\"v\":1,\"ts\":\"' + $ts + '\",\"event\":\"attempt.verdict\",\"actor\":\"joe-brown\",\"data\":{\"attempt_id\":\"a1\",\"human_verdict\":\"reject\",\"principal\":\"joe-brown\",\"via\":\"cli\"}}')

consil beta
```

Printed:

```
recorded attempt.outcome -> .harness\log\2026-08-21.jsonl
recorded attempt.verdict -> .harness\log\2026-08-21.jsonl
beta [all]: insufficient data (1 human rejections, need 30)
```

`[measured]` — run in PowerShell 5.1 on 21 August. The count went from 0 to 1.

**PowerShell eats quotation marks**, which is why every `"` above is written `\"`. It has one more
trap: **no spaces inside any value.** With `"task":"fix pagination off-by-one"` the same command
fails with `consil: error: unrecognized arguments: pagination off-by-one…` `[measured]`. Use
identifiers, not sentences — `TCK-1`, `fix-pagination-off-by-one`. In Git Bash the ordinary
single-quoted form works and spaces are fine `[measured]`.

`verifier_accept` is what the automated checks said. `human_verdict` is what you said. `actor`
must equal `principal` — no agent can file your verdict for you, by design.

**Where the records go.** `--log` above points them at the consilient checkout's own log, so a
single `consil doctor` run sees everything `[measured]`. That log is committed and published, so
use repository names you are content to make public. If a name should stay private, point `--log`
at a file outside any repository — and then pass the same `--log` to `consil doctor`, because it
will read the seven-day capture count from that file too `[measured]`.

---

## 5. Getting the number off zero

**Only rejections count.** Accepted work contributes nothing to the number and nothing to the
count you need `[measured]`. Two commands per rejection, none per acceptance.

**The trap that would waste all of it.** If you only ever look at work *after* the checks have
passed it, then every rejection you record has `verifier_accept: true`, the rate comes out at one
by construction, and six weeks of discipline produce a number that measures nothing. Deliberately
review and record some work whose **checks failed** too. Recorded that way, the count moved to 2
rejections of which 1 was a false accept — a half, not a one `[measured]`. Decide this before the
first row, not after the thirtieth.

**How long thirty takes.** Your rejection rate has never been measured, so this is arithmetic over
assumptions rather than a forecast `[asserted]`:

| reviews per working day | you reject | thirty rejections takes |
|---|---|---|
| 10 | 1 in 5 | about 3 weeks |
| 5 | 1 in 5 | about 6 weeks |
| 5 | 1 in 10 | about 12 weeks |

Thirty is only the point at which it will **print** a number rather than refuse. Settling an
actual decision takes more — roughly fifty to a hundred and forty rejections, depending on how bad
the true rate turns out to be. `feeding-the-meter.md` carries the exact figures and measured them.

**What the number looks like elsewhere.** The only rate this project has actually measured is on
its own code: 1,931 faults introduced deliberately, and **0.3132** of them survived every check
the project has `[measured]` — roughly one bad change in three gets through. That is this
codebase's checks measured a different way, not yours. It is the best available guess at what to
expect, and it is why the question is worth six weeks.

---

## 6. What opens the gates

Of the seven conditions `consil doctor` reports, three already pass `[measured]`. Two of the four
failures are yours to move, and only one of those needs anything from you.

**Seven consecutive days of capture** — reads 3 of 7, covering 19 to 21 August `[measured]`. A
scheduled task on this machine (`Consilient-Capture-Health`, next run 22 August 08:00, status
Ready `[measured]`) writes one capture record a day. Four more runs and it reads 7 of 7, on 25
August, provided the machine is on `[asserted]`. **You do not have to do anything.**

**Twenty tickets finished on some other repository** — reads 0 of 20 `[measured]`. This one is the
whole point: **using the harness on real work is the gate.** Two records per finished ticket — the
`attempt.outcome` from section 4, carrying a `repository` field and `verifier_accept: true`, then
a `ticket.completed` naming the same `attempt_id`:

```powershell
consil --log $L record --event ('{\"v\":1,\"ts\":\"' + $ts + '\",\"event\":\"ticket.completed\",\"actor\":\"joe-brown\",\"data\":{\"repository\":\"joe-hireable/my-side-project\",\"ticket\":\"TCK-1\",\"attempt_id\":\"a1\"}}')
```

That pair moved the line from `0 of 20` to `1 of 20` `[measured]`. Twenty tickets of ordinary work,
recorded as you go, opens it. Nothing else does.

The other two failures — a retired history-mining experiment and a blocked measurement of the
critic tier — are project work, not yours `[measured]`.

---

## 7. What will go wrong first

Roughly in the order you will meet them.

**1. You typed `python -m` instead of `consil`.** Symptom: everything looks healthier than section
2 says, and the exit code is 0. See section 3. This has already misled two agents on this machine
in one night `[cited: the diagnosis behind this page]`.

**2. PowerShell mangled the JSON.** Symptom: `error: --event is not valid JSON` or `error:
unrecognized arguments: …`, exit 2 `[measured]`. Cause: a missing `\` before a `"`, or a space
inside a value. Nothing was written; retype it.

**3. The clock.** Symptom:

```
error: event ts 2026-08-21T09:00:00Z is 229 minutes from the current clock, beyond the
15-minute tolerance.
```

`[measured]` `ts` must be now, not when the thing happened. Always generate it with the `Get-Date`
line rather than typing it. To record something older, put the occurrence time inside `data`.

**4. A typo in an `attempt_id` — the one that actually costs you something.** A verdict naming an
attempt with no recorded outcome is **accepted** (exit 0) and then breaks everything that reads the
log afterwards:

```
error: attempt.verdict at position 2 references unknown attempt 'a1-typo'
```

`beta`, `replay` and `doctor` all exit 2 from then on `[measured]`, and appending the missing
outcome afterwards does **not** repair it `[measured]`. On your own log, delete the offending line:

```powershell
$f = "<log dir>\2026-08-21.jsonl"
$keep = Get-Content $f | Where-Object { $_ -notmatch 'a1-typo' }
[IO.File]::WriteAllLines((Resolve-Path $f), $keep)
```

`[measured]` — after which `consil beta` and `consil replay` both returned to normal. Use
`[IO.File]::WriteAllLines`, not `Set-Content -Encoding utf8`: the latter writes a byte-order mark
that makes the first line of the file unreadable, and the tool then discards that line quietly
`[measured]`.

**5. `consil` writes where you are standing.** With no `--log`, it creates `.harness\log\` in the
current directory `[measured]`. Harmless, but you will find stray `.harness` folders if you forget
the flag.

**6. `replay` reports quarantined lines.** Something wrote to the log without going through
`consil record`. The published log carries three such lines, all known and recorded `[measured]`.
New ones are worth looking at.

---

## When you want more

- `docs/00-context/feeding-the-meter.md` — the event schema in full, how to correct a verdict you
  changed your mind about, and the exact sample sizes.
- `docs/20-design/minimum-user-guide-draft-2026-08-21.md` — the five ideas underneath all of this,
  with no commands in it at all.
- `consil doctor --json` and `consil beta --json` — the same results, machine-readable.

---

## What is deliberately not on this page

- **Installing from scratch.** The install instructions belong with the published tree and were
  not re-run for this page. **Untested here.**
- **Anything about routing, dispatch or orchestration.** None of it exists, and section 1 is not
  being modest.

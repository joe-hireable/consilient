# Getting started

**PRODUCT**, except the two boxes marked **machine-local**. Written 21 August 2026 and
**re-measured the same evening** against the published tree after an adversarial read found three
steps that did not do what this page said they did. What that read broke, and what is still broken,
is listed near the end.

Every command below was run and every quoted output is what it printed. Numbers carry their
evidence: `[measured]` I ran it and read the artefact, `[cited]` a named source, `[asserted]` my
judgement. Anything I could not run is marked **untested** rather than quietly included.

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

`[measured]` — that is the whole command set, from `consil --help`, whose own one-line description
of itself is `Observe-only.`

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

Two things about *where* you run it, both of which cost a confused minute if you get them wrong:

- **Stand inside the checkout.** Run `consil doctor` from anywhere else and the twenty-ticket
  condition reports `B4 UNKNOWN: The structural analysis is unavailable` instead of a count
  `[measured]`. That check reads project files by relative path.
- **Run it twice the first time.** `doctor` rebuilds the projection as it goes. Against a
  `state.db` left behind by an older run it reported `A2 FAIL: Compared 106 events; canonical state
  diverged`, and the two runs after it — same command, same log, same file — both reported
  `A2 PASS` `[measured]`. The second answer is the real one. This is why two different reports of
  A2 have been circulating; each was correct about its own first run.

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

`[measured]` 21 August 2026, run from the published tree against a copy of its own log and state.

**It exits 1.** That is correct behaviour while the gates are shut, not a fault, and it means
`consil doctor && something-else` will never run the something-else `[measured]`. Do not chain it.

---

## 3. The one rule that matters more than the rest

**Type `consil`. Never `python -m consilient.cli`.**

Same directory, same log, same day, the two disagree:

| | first line | the `A1` line | exit |
|---|---|---|---|
| `consil doctor` | `Gate A: FAIL` | **A1 FAIL** | 1 |
| `python -m consilient.cli doctor` | `Gate A: FAIL` | **A1 PASS** | 0 |

`[measured]` — both run from the published tree on 21 August. Note that the headline is identical;
it is the sub-line and the **exit code** that diverge, and the exit code is the part a script reads.

The reason is that on this machine `import consilient` resolves to a **different working tree**
(`…\consilient-w-p5\src\consilient\__init__.py`), because of an editable install left on the
system interpreter by another checkout `[measured]`. So `python -m` measures one tree's data with
another tree's code, silently, and the stale code is the one that reports a passing condition and a
clean exit.

Two things make this survivable rather than frightening:

- `consil` only exists inside a checkout's own virtual environment. In a fresh PowerShell with
  nothing activated, `consil` is **not found at all** `[measured]` — a loud failure, which is the
  good kind.
- You can confirm the instrument in one line. `(Get-Command consil).Source` must print a path
  **inside the checkout you are standing in** `[measured]`.

A repair that makes the tool announce its own provenance and refuse a foreign tree exists in
another worktree, and it is **not in the published tree** `[measured]`. Until it is merged, this
section is the defence.

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

consil --log $L beta
```

Printed:

```
recorded attempt.outcome -> …\log\2026-08-21.jsonl
recorded attempt.verdict -> …\log\2026-08-21.jsonl
beta [all]: insufficient data (1 human rejections, need 30)
```

`[measured]` — run in PowerShell 5.1 on 21 August. The count went from 0 to 1.

**`--log` goes on every command, including the reads.** An earlier draft of this page ended the
block with a bare `consil beta`, which reads whatever log sits under the *current directory*
instead. Run against a log kept anywhere else, the two records succeeded and then `consil beta`
printed `insufficient data (0 human rejections, need 30)` at exit 0 — indistinguishable from
having recorded nothing — while `consil --log $L beta` printed `1` `[measured]`. Nothing warns you.
Put `--log $L` on `beta`, `replay` and `doctor` too.

**PowerShell eats quotation marks**, which is why every `"` above is written `\"`. It has one more
trap: **no spaces inside any value.** With `"task":"fix pagination off-by-one"` the same command
fails with `consil: error: unrecognized arguments: pagination off-by-one…`, exit 2 `[measured]`.
Use identifiers, not sentences — `TCK-1`, `fix-pagination-off-by-one`. In Git Bash the ordinary
single-quoted form works and spaces are fine `[measured]`.

`verifier_accept` is what the automated checks said. `human_verdict` is what you said. `actor`
must equal `principal` — no agent can file your verdict for you, by design.

**Where the records go, and who can read them.** `--log` above points them at the consilient
checkout's own log, so a single `consil doctor` run sees everything `[measured]`. **That log is not
committed and never will be**: `.harness/log/` is in `.gitignore`, a test enforces it, and ADR-0057
settled that a user's trajectory is their data `[measured]`. So a repository name in your log does
not leave the machine by accident. If you would rather keep it away from the repository entirely,
point `--log` somewhere outside it — and then pass that same `--log` to every command, `doctor`
included, because the seven-day capture count is read from the same file.

---

## 5. Getting the number off zero

**Only rejections count.** Accepted work contributes nothing to the number and nothing to the
count you need `[measured]`. Two commands per rejection, none per acceptance.

**The trap that would waste all of it.** If you only ever look at work *after* the checks have
passed it, then every rejection you record has `verifier_accept: true`, the rate comes out at one
by construction, and six weeks of discipline produce a number that measures nothing. Deliberately
review and record some work whose **checks failed** too. Recorded that way, `consil beta --json`
returned `n_rejected: 2, n_false_accept: 1` — a half, not a one `[measured]`. Decide this before
the first row, not after the thirtieth.

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
the project has `[cited: docs/00-context/how-this-gets-believed-2026-08-20.md]` — roughly one bad
change in three gets through. That is this codebase's checks measured a different way, not yours.
It is the best available guess at what to expect, and it is why the question is worth six weeks.

---

## 6. What opens the gates

Of the seven conditions `consil doctor` reports, three already pass `[measured]`. Two of the four
failures are yours to move, and only one of those needs anything from you.

**Seven consecutive days of capture** — reads 3 of 7, covering 19 to 21 August `[measured]`. A
scheduled task on this machine (`Consilient-Capture-Health`, state Ready, last run 21 August
08:00:01 with result 0, next run 22 August 08:00 `[measured]`) writes one capture record a day.
Four more runs and it reads 7 of 7, on 25 August, provided the machine is on `[asserted]`. **You do
not have to do anything.**

**Twenty tickets finished on some other repository** — reads 0 of 20 `[measured]`. This one is the
whole point: **using the harness on real work is the gate.** Two records per finished ticket — the
`attempt.outcome` from section 4, carrying a `repository` field and `verifier_accept: true`, then
a `ticket.completed` naming the same `attempt_id`. A bare `ticket.completed` with no verified
outcome behind it does not count, by design.

```powershell
# same session as section 4: $L is still set, and $ts must be re-stamped
$ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
consil --log $L record --event ('{\"v\":1,\"ts\":\"' + $ts + '\",\"event\":\"ticket.completed\",\"actor\":\"joe-brown\",\"data\":{\"repository\":\"joe-hireable/my-side-project\",\"ticket\":\"TCK-1\",\"attempt_id\":\"a1\"}}')

cd <checkout>          # B4 needs the checkout as the working directory
consil --log $L doctor
```

```
B4 FAIL: Twenty non-Consilient tickets complete without harness intervention
  1 of 20 tickets completed on a repository other than this one.
```

`[measured]` 21 August, against the published tree. Twenty tickets of ordinary work, recorded as
you go, opens it. Nothing else does.

> If you paste that snippet into a *fresh* shell it fails loudly — `$L` and `$ts` are empty, and
> `--log` then swallows the word `record`, giving `consil: error: argument command: invalid
> choice`, exit 2 `[measured]`. Re-run the `cd` / `$L` / `$ts` lines first. Nothing is written when
> it fails.

The other two failures — a retired history-mining experiment and a blocked measurement of the
critic tier — are project work, not yours `[measured]`.

---

## 7. What will go wrong first

Roughly in the order you will meet them.

**1. You typed `python -m` instead of `consil`.** Symptom: a condition looks healthier than section
2 says, and the exit code is 0. See section 3. This has already misled two agents on this machine
in one night `[cited: the diagnosis behind this page]`.

**2. You ran `consil` from the wrong place.** Two distinct symptoms, both quiet: `B4 UNKNOWN: The
structural analysis is unavailable` if you are not inside the checkout, and a β of zero if you
forgot `--log` `[measured]`. Neither is an error, and neither will interrupt you.

**3. PowerShell mangled the JSON.** Symptom: `error: --event is not valid JSON` or `error:
unrecognized arguments: …`, exit 2 `[measured]`. Cause: a missing `\` before a `"`, or a space
inside a value. Nothing was written; retype it.

**4. The clock.** Symptom:

```
error: event ts 2026-08-21T09:00:00Z is 254 minutes from the current clock, beyond the
15-minute tolerance. Stamp events from the clock rather than writing the time you believe it
to be. To record something that happened earlier, put the occurrence time in `data` and let
`ts` record when it was written.
```

`[measured]` Always generate `ts` with the `Get-Date` line rather than typing it.

**5. A typo in an `attempt_id` — the one that actually costs you something.** A verdict naming an
attempt with no recorded outcome is **accepted** (exit 0, `recorded attempt.verdict -> …`) and then
breaks everything that reads the log afterwards:

```
error: attempt.verdict at position 0 references unknown attempt 'a1-typo'
```

`beta`, `replay` and `doctor` all exit 2 from then on `[measured]`, and appending the missing
outcome afterwards does **not** repair it `[measured]`. The check runs when the log is *replayed*,
not when it is written, so the bad line is already on disk before anything objects. On your own
log, delete the offending line:

```powershell
$f = "<log dir>\2026-08-21.jsonl"
$keep = @(Get-Content $f | Where-Object { $_ -notmatch 'a1-typo' })
[IO.File]::WriteAllLines((Resolve-Path $f).Path, [string[]]$keep)
```

`[measured]` — after which `consil beta` and `consil replay` both returned to normal. Two details,
both of which bit this page's earlier draft:

- The `@( … )` and the `[string[]]` cast are load-bearing. Without them, a filter that leaves one
  line or none hands `WriteAllLines` a `$null` and it throws `ArgumentNullException` — while the
  broken line is still sitting in the file `[measured]`.
- Use `[IO.File]::WriteAllLines`, not `Set-Content -Encoding utf8`. The latter writes a
  byte-order mark that makes the first line unreadable, and the tool then discards that line
  quietly `[measured]`.

**6. `consil` writes where you are standing.** With no `--log`, it creates `.harness\log\` in the
current directory `[measured]`. Harmless, but you will find stray `.harness` folders if you forget
the flag.

**7. `replay` reports quarantined lines.** Something wrote to the log without going through
`consil record`. The project's own log carries three, all the same known case — an agent filed an
approval attributed to you, which V0-18 forbids — and they are recorded as the historical baseline
`[measured]`. New ones are worth looking at.

---

## What this page could not fix

An adversarial read on 21 August followed this page cold and broke three steps. All three are
repaired above; this is what they were, in case you meet a copy of the older draft.

1. **Section 4 ended with a bare `consil beta`**, which silently reported zero if your log lived
   anywhere but the current directory. Now `consil --log $L beta`.
2. **Section 6's ticket recipe was a no-op** against the published tree for part of that evening.
   It is not any more: the change that broke it — a separate ticket register keyed on a different
   event kind — has been reverted from the published tree, and `ticket.completed` counts again,
   `0 of 20` → `1 of 20` `[measured]` re-run this evening. If a future `doctor` says `0 of 20`
   after you have recorded pairs, that change has landed again and section 6 needs re-measuring,
   not you.
3. **Section 7's recovery recipe threw** instead of deleting the bad line, whenever the filter left
   fewer than two lines. Fixed with `@( … )` and `[string[]]`.

Three things remain broken tonight and are **not** repairable from this page:

- **This page is not yet in the published tree.** It lives on a working branch. Until it merges you
  are reading it from a checkout that is not the one section 2 tells you to stand in — which is
  exactly the hazard section 3 describes, so treat the commands as measured-elsewhere until it
  lands.
- **The stale editable install is still on the system interpreter** `[measured]`. Section 3 is a
  rule you must keep, not a fault that has been fixed. The clean repair is one `pip uninstall`
  against the system Python, and it would break every other live worktree on the machine at the
  same moment, so it has been left alone.
- **A wrong `attempt_id` still kills the log until you edit the file by hand** (section 7, item 5).
  There is a proposed fix — quarantine the bad line instead of refusing the whole log, which is
  already how malformed lines are handled — but it changes three pinned tests and needs an ADR
  first.

---

## When you want more

- `docs/00-context/feeding-the-meter.md` — the event schema in full, how to correct a verdict you
  changed your mind about, and the exact sample sizes.
- `docs/20-design/minimum-user-guide-draft-2026-08-21.md` — the five ideas underneath all of this,
  with no commands in it at all.
- `consil doctor --json` and `consil beta --json` — the same results, machine-readable.

---

## What is deliberately not on this page

- **Installing from scratch.** The published tree already has a working `.venv`, so nothing here
  needed the install path, and it was not re-run. **Untested.**
- **Anything about routing, dispatch or orchestration.** None of it exists, and section 1 is not
  being modest.

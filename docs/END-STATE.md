# Consilient, finished — what it is when it works

*The end-state page. Written for someone who has never seen this repository and does not
write software.*

- **Document class: W** — written prose carrying judgement, admitted under ADR-0073.
- **Review by:** `2026-09-24`
- **Source:** expanded from the end-state section of
  `docs/20-design/documentation-and-surfaces-plan-2026-08-23.md`, build unit 5.
- **Falsifier:** five readers who have never seen this repository read only this page and are
  then asked three questions — what does Consilient do for me, what can it not do today, and
  how do I check that myself. If two or more cannot answer all three unaided, this page is
  wrong and is rewritten, not patched. A second, mechanical falsifier: if any row of the
  distance table below prints a *current value* for live state rather than the command that
  reports it, this page has become a second source of truth and the row is cut.

---

## Read this before you read anything else here

**This page describes the finished thing. It is not a status report.** Every claim about what
exists today sits in the distance table below, and that table names the command to run
rather than an answer that will be out of date by the time you read it. If any sentence
outside that table reads as though a capability is already working, the sentence is wrong —
report it.

---

## The problem

You have more work than you can personally check.

That is the whole ceiling, and it is not solved by a faster model. A model that produces ten
times as much work you must read has made your bottleneck worse, not better. Everything
below follows from taking that sentence literally. [asserted]

---

## What Consilient is

You say what you want, in your own words, and what would count as done.

Consilient takes it from there. It sends the work to whichever agent runtimes you already
use — Claude Code, Codex, Cursor, Grok, opencode, or any other you favour — or to a model
running on your own hardware when none of them fits. It keeps a single record of everything that
happened. It comes back with the result, and with the number nobody else hands you: **how
often its own checks are wrong.**

It does not replace those runtimes. It commands them. They are called *harnesses*. Consilient is not.

---

## The number, and why it is the point

Every agent eventually says *checks passed*. That sentence is worth exactly as much as the
checks behind it, and nobody measures those checks.

Consilient calls that measurement **β** (beta): of the bad work that reaches your automated
checks, the share those checks wave through. A low β means your tests, your type checker and
your build actually catch things. A high β means *checks passed* is close to meaningless on
your work.

Then it conditions its own behaviour on the answer, which is the part that matters:

- **Where the checks are strong**, it runs more work in parallel, unattended, and you read less.
- **Where the checks are weak**, it says so and refuses to route. Parallelism on a weak check
  is a machine for manufacturing work you must review by hand.

That refusal is the product. A tool that runs agents in parallel against checks it has never
measured is selling you review labour and calling it throughput. [asserted]

**β is measured on your work, not on a benchmark.** A published figure for someone else's
repository tells you nothing about whether *your* suite catches *your* mistakes.

---

## What it feels like when it is finished

An organisation you talk to, rather than a tool you operate.

You are the founder. You set direction, give feedback, unblock, and decide the things only
you can decide. Standing agents own areas — growth, data, infrastructure — and keep
progressing them whether or not you are watching. They dispatch specialists of their own,
built for a task in seconds rather than hired over months.

The principal put it this way, and the document that records his words is the source, not a
paraphrase:

> "Each swarm must have its own orchestrator/manager and specialist agents all doing specific
> things. Just like how an organisation works to achieve large collective goals... The user is
> the Founder/CEO and is purely strategic and not hands on."

Source: docs/00-context/the-machine-2026-08-22.md:25

**It decides everything reversible by itself, and records the way back.** Not "asks
permission and then acts" — decides, acts, and leaves you an undo with the reasoning attached.

---

## The things it stops and asks you about

It interrupts you for these, and nothing else. The list is meant to be exhaustive, and adding
to it takes a recorded decision, not a preference. [cited: ADR-0033 §2, PROVISIONAL]

- **Money** leaving an account, or metered spend beyond a cap you authorised.
- **A credential or permission** only you hold.
- **A question of taste** that no fact settles.
- **An action outside the safety floor**, which is reserved by construction.
- **Your verdict on a piece of work** — whether it is actually good. That judgement is the
  ground truth β is measured against, so it cannot be delegated without destroying the
  measurement.
- **Publishing, transmitting or exposing anything** beyond your machine.
- **Lifting a gate, or approving a specification.** It may propose; it never approves on your
  behalf.

**If it asks you anything else, that is a defect, not a preference.** Everything else it
decides itself — and a decision it cannot tell you how to reverse is not a decision, it is an
ask wearing a disguise. [cited: ADR-0033 §1]

The authority rule is structural, not a courtesy. Decisions have been filed in the
principal's name on this project that he never made, so the answer is machinery that makes it
impossible rather than a reminder that it is discouraged. [measured:
`docs/00-context/corrections-2026-08-21.md`]

---

## What it costs

**MIT licensed, open source, free forever, and every capability is in the free version.**
Open source first is a decision the principal took and it is accepted. [cited: ADR-0048,
ACCEPTED] Open-core — holding features back for a paid tier — is foreclosed by ADR-0024 §1,
which is still `PROPOSED`; the intent is settled, the decision record is not, and that
difference is stated here rather than smoothed over. [cited: ADR-0024, PROPOSED]

Bring your own model, whether local weights or your own API keys, and you get the full
product with no degraded route. **That is an intention, not yet a check.** The plan this page
expands claims it is enforced; nothing in this repository enforces it, and until something
does it is exactly the kind of promise-in-prose the project exists to distrust. [measured: no
match for a bring-your-own-model parity check across `tests/` or `.github/scripts/`, searched
24 August 2026]

Paid plans, when they exist, fund maintenance, hosted storage of your record, and hosted
inference for people who would rather not run their own — at minimal margin, prepaid, never
billed in arrears. [cited: ADR-0048, ACCEPTED] No paid code exists, and none will before the
open-source release.

---

## What it refuses to be

A short list, because refusals define a product more sharply than features do:

- **Not a chat that remembers.** No scrollback you scroll to find an answer, no accumulating
  thread, no streamed thinking. If you have to scroll up to learn what β is, the design failed.
- **Not a confidence score.** A model's stated confidence in its own work is not evidence and
  is never gated on. Verifier outcomes and your verdicts are.
- **Not a health index.** No composite number rolling unrelated things up into a colour. β
  carries its sample size and its interval, or it is not shown.
- **Not agreement between agents presented as proof.** Two agents that read the same evidence
  and agree have told you one thing, not two. [cited: `CONSILIENCE.md`, Whewell's second clause]

---

## The distance between this page and the code

**Read the right-hand column, not the middle one.** Every row names the command that answers
the question on this machine. That is deliberate: a value typed into a document is wrong the
moment the code moves, and this repository has measured exactly that happening — two
generated documents had drifted while its own continuous integration reported green, because
the checker that would have caught it was wired into no workflow. [measured:
`docs/20-design/documentation-and-surfaces-plan-2026-08-23.md`, the finding stated in its
opening section]

| What this page describes | Where the code is | Ask it yourself |
|---|---|---|
| Routes work to harnesses, blocks when checks are weak | Not built. `consil` observes only, and a test asserts it cannot route, block or accept | `consil doctor` — read `routing_orchestration_enabled` |
| Measures β on your work | Built for code, where an automated oracle is cheap | `consil beta` — read the value **with its n and its interval** |
| Runs unattended on your repositories | Refused. Supervised dispatch on this repository only | `consil doctor` — read the Gate B conditions |
| Keeps one record of everything that happened | Built. One append-only writer | `consil replay` |
| Standing agents owning areas | Designed, not built | `docs/20-design/` |
| Chat as the control surface | Designed, not built | [the surfaces plan](20-design/documentation-and-surfaces-plan-2026-08-23.md) |
| Works outside software | Open question, not a backlog item | [`open-questions.md`](00-context/open-questions.md), Q24 |
| Free, MIT, no open core | Open source first is accepted (ADR-0048). The open-core foreclosure is ADR-0024, still `PROPOSED` | [`decisions/index.md`](decisions/index.md) |

**On the figure people always ask for.** Against faults deliberately seeded into this
repository's own code, β came out at `0.3132`, interval `[0.2926, 0.3346]`, from 586 real
defects among 1,871 usable mutants — roughly one bad change in three passing every check the
project has. [measured: EXP-47, `docs/10-research/experiment-register.md`, reading taken 20
August 2026] Read it as a dated reading and nothing more. A reading taken on a day stays true
about that day forever, whereas "the current value" is a copy that begins drifting the moment
it is typed, which is why the table above holds commands instead.

**Two caveats, and they are larger than the number.** That figure is *mutation* β: it asks
whether the checks catch faults a script inserted. The β this product is actually about is
**human-labelled** — whether the checks catch work *you* would reject — and it is
**unestimated**, because confirming it needs at least 30 human rejections and the record does
not hold them. [measured: `docs/10-research/experiment-register.md`, the stopping rules for
the conditional-β experiments] And whether `0.3132` measures a property of the work or merely
the coverage of that one test suite is **unexamined**. That is the sharpest open question
about the whole approach, and nobody here has yet asked it properly.

---

## What is honestly open

- **Does β mean anything outside code?** Software has a cheap automated oracle — the tests
  run or they do not. A strategy memo has none. Whether anything plays β's role there is
  open, and the honest answer today is that nobody knows.
- **Does β measure the work, or the test suite?** See above. Nobody has yet asked it properly.
- **Does anyone want this?** No users, and no demand evidence. That is a finding, and it
  belongs on this page rather than in a footnote.

---

## Where to go next

- [`CONSILIENCE.md`](../CONSILIENCE.md) — the one sentence everything here derives from.
- [`getting-started.md`](00-context/getting-started.md) — every command run against this tree
  with its real output pasted in, including the ones that fail.
- [`the-machine-2026-08-22.md`](00-context/the-machine-2026-08-22.md) — the principal's own
  words, verbatim, with the measured distance from the code.
- [`v0-draft.md`](40-spec/v0-draft.md) — the approved implementation boundary and the gates.
- [`open-questions.md`](00-context/open-questions.md) — what is still open.

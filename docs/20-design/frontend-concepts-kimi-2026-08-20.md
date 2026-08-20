# Frontend concepts — an independent design pass (Kimi, 20 August 2026)

**Status:** design exploration, commissioned by the principal's brief of 20 August 2026
(`../../brief-design.md`). **Nothing here is approved for build, and this document changes
nothing.** ADR-0007 — *CLI only, and build no review surface* — is ACCEPTED and still
governs; its reopen conditions are EXP-08 (critic recall) and EXP-19 (verdict-prompt
completion), both blocked. [asserted] Every concept below names the gate that would have to
pass before it could be built. The document exists so that *if* measurement unlocks a
surface, its shape is already derived from the evidence rather than from enthusiasm.
[asserted]

A second model family is designing the same surface concurrently, and the two documents
have not seen each other. That is the method, not an accident: convergence between two
independently derived designs is informative precisely because neither is evidence the
other shared. If they agree, that is a consilience test passed; where they diverge, the
divergence is the finding. Comparing them is the principal's job, not ours. [asserted]

Claims are tagged `[measured]`, `[cited]`, `[algebra]`, `[asserted]`, `[simulated]`. Most
are `[asserted]`. That is honest.

---

## 0. The one sentence the design derives from

The product is **a β-meter with a cascade attached** (`architecture-sketch.md`).
[asserted] A surface is not the product's face; it is the *second lever* on the only
quantity that caps the system:

> `n_max = T_agent_cycle / T_effective_review` — roughly **three** agents at 25-minute
> cycles and 8-minute reviews. [algebra] (`surfaces-and-who-they-serve.md` §1)

A frontend earns its place only by reducing `T_effective_review` **without raising β**.
[asserted] And every surface is an untested intervention on the human half of β, because
the human verdict is the ground truth the instrument is measured against (ADR-0002,
v0-draft §5). [asserted] Those two sentences — not aesthetics, not ambition — generate
everything below.

The strongest positive evidence about what a surface should *do* comes from the
human-factors literature the repository already holds: the only manipulation measured to
eliminate over-reliance was **an error detector rendered in the UI** — the error itself
highlighted — not an explanation (over-reliance ~69% → 0%, Study 3, N=286, exploratory;
Vasconcelos et al., CSCW 2023, arXiv:2212.06823, held `[FULL]` in
`../10-research/bibliography.md`, figure as corrected in ADR-0033). [cited] Hence the rule
that decides the shape of every screen here: **show state, not narrative.** [asserted]

---

## 1. The reframe: the perpetual thing is the record, not a conversation

The brief asks for "seamless access to unlimited intelligence from a single perpetual
conversation". Taken literally, that is a chat box, and a chat box is wrong here. Named,
not designed around:

- **A conversation is an unbounded structure.** V0-20 requires every convened structure to
  carry hard budget, turn and depth caps, with exhaustion escalating. An open-ended chat
  is the one structure that cannot satisfy it. [asserted]
- **A conversation accumulates shared context, which is the echo chamber.** Whewell's
  second clause — convergence is only informative across *different* classes of facts —
  and the theorem behind ADR-0010 both say that participants re-reading one shared stream
  add no assurance. [cited] A UI whose centre is a growing shared stream teaches its user
  the wrong model of what the system is. [asserted]
- **A conversation invites ambient narrative** — presence, typing, streaming — which
  ADR-0041 discards at the boundary and the reliance literature measures as an acceptance
  amplifier (§2). [cited]
- **The harness is not a participant.** It is an instrument. Instruments do not converse;
  they record, measure and report. [asserted]

The brief's want is real, and it is already satisfied by the architecture: the **single
perpetual thing is the trajectory** — one append-only, versioned record of everything that
happened, from which every surface is a lossy, rebuildable projection (ADR-0006,
ADR-0041). [asserted] "One perpetual conversation" is honoured as: **one record, every
surface a rendering of it, any past window re-renderable at any level** (ADR-0035 §1).
[asserted] The user never "catches up with the chat"; they render the record. That is the
whole of the seamlessness on offer, and it is genuinely seamless — the record follows the
user across CLI, window and phone because none of them *is* the thing. [asserted]

---

## 2. What this design refuses, and the evidence that forbids it

Each refusal has a measurement or an invariant behind it. None is taste.

| # | Refused | Why | Source |
|---|---|---|---|
| R1 | A chat box / message thread as the primary surface | §1 | [asserted] |
| R2 | Streaming tokens, typing indicators, presence, read receipts | Ambient status never enters model context; it is discarded at the transport adapter | ADR-0041 §2, V0-13 [asserted] |
| R3 | Model-reasoning / "show your working" panels | Explanations raised relative reliance on the model 29.59% → 38.87% (p=.05) while rejection ability was statistically unchanged; explanations "increased the chance that humans will accept the AI's recommendation, regardless of its correctness" | Schemmer et al., IUI 2023, arXiv:2302.02187 `[FULL]`; Bansal et al., CHI 2021, arXiv:2006.14779 — both held in `bibliography.md` [cited] |
| R4 | Confidence scores, token-level uncertainty highlighting | Confidence displays shifted behaviour (p=.035) with no trust-calibration advantage (p=.66) and no joint-performance gain | Zhang, Liao & Bellamy, FAT* 2020, arXiv:2001.02114 `[FULL]` [cited] |
| R5 | Composite scores, health indices, any single quality number | Sycophantic output was rated 9% *higher* quality while measurably degrading the outcome; satisfaction and quality are anti-correlated through a measured mechanism. V0-21 forbids compositing | Cheng et al., Science 391 (2026), DOI 10.1126/science.aec8352 `[FULL]` [cited]; V0-21 [asserted] |
| R6 | Thumbs-up, "did that help?", satisfaction prompts | Developers reported a 20% speedup after a *measured* 19% slowdown; OpenAI's own postmortem records thumbs-data weakening the reward signal that held sycophancy in check | METR RCT, arXiv:2507.09089 `[FULL]`; OpenAI GPT-4o postmortem `[FULL]` [cited] |
| R7 | Agent avatars, personas, display names as authority | Display name, title and persona are never an authority, capability, admission or routing input | V0-19 [asserted] |
| R8 | A wall-of-agents dashboard | The parallelism ceiling is ~3 [algebra]; a 50-card grid renders a capability the system does not have, and vigilance is "hard mental work and is stressful" | Warm, Parasuraman & Matthews 2008, via ADR-0035 [cited] |
| R9 | Spinners and progress bars as liveness | Liveness is resolved from artefact progress, never process identity; a spinner is a process-identity signal | V0-25, ADR-0034 [asserted] |
| R10 | One-tap verdicts arriving over untrusted channels (Slack, SMS, email, a web button) | A token attributed to "Joe" is insufficient evidence of human authorship; EXP-16 measured identity collapse on exactly these transports | ADR-0041 §3, V0-28 [measured] |
| R11 | Notification badges and unread counts as engagement mechanics | Interrupts are a finite budget spent per period (ADR-0033 §5); a badge is an interrupt that spends it continuously | [asserted] |
| R12 | Cloud custody of the user's provider credentials, under any plan | "Do not put a secret anywhere a public repository can reach… a capability needing one runs locally or not at all" | Joe, 20 Aug 2026 [measured — it is the recorded rule] |

What remains after the refusals is the design space this document works in: **state,
rendered honestly, with the errors surfaced and the narrative withheld.** [asserted]

---

## 3. Concept 1 — the instrument panel: the 0-click default

**Gate:** EXP-08 or EXP-19 (ADR-0007). What exists today is the CLI; this concept's entire
content is the existing `doctor`, `replay` and `beta` JSON contracts rendered, plus a work
list whose contract does not yet exist. [measured — the contracts exist; asserted — the
rendering]

**Answers the brief's question:** *what is on screen when the user opens it and nothing
needs them.*

### Layout

One window, no tabs, no sidebar, no navigation. Three bands and a footer. Everything on
screen is a field of a JSON contract (Concept 4). [asserted]

```
┌──────────────────────────────────────────────────────────────────────────┐
│ consilient — this repository                    level 1 of 3: milestones   │
├──────────────────────────────────────────────────────────────────────────┤
│ INSTRUMENT                                                                 │
│ record     replay identical · 0 new refusals · last event 14:02:11         │
│ capture    day 2 of 7 — gate A3 not yet met                                │
│ gates      A 2/3 · B 1/4 — routing/orchestration: NOT ENABLED              │
│ fallback   last exercised 6 days ago: pass                                 │
│                                                                            │
│ β  (this repo · pytest+mypy+ruff · mutation census, 20 Aug)                │
│   0.3132 [0.2926, 0.3346] · n=1,871 seeded defects · verdict: measured     │
│   the checks accepted 586 of 1,871. synthetic defects; real ones differ.   │
├──────────────────────────────────────────────────────────────────────────┤
│ WORK — ceiling 3 (25-min cycles ÷ 8-min reviews)                           │
│  #121  EXP-31 gemma4 swap       running — last artefact 13:58              │
│  #122  doctor copy fix          checks passed — verdict recorded: accept   │
│  —     third slot empty                                                    │
├──────────────────────────────────────────────────────────────────────────┤
│ NEEDS YOU: nothing.                                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

### What is on screen at rest, line by line

- **Header.** Repository, and the visibility level — the dial is the only control on the
  screen, and it is ADR-0035's, rendered, not reinvented. [asserted]
- **INSTRUMENT band.** The system's honesty about *itself*, from `consil doctor`: record
  integrity (replay digest compared, refused lines counted — never hidden, because a β
  computed over a quietly shortened log is the false confidence the project exists to
  measure, `cli.py` `cmd_beta`), capture run, gate state, fallback freshness. [measured —
  these are the existing contract fields] The example values are this repository's true
  state on 20 August 2026: A1, A2, B1 pass; A3 at 2/7 days; B2, B3, B4 failing;
  `routing_orchestration_enabled: false`. [measured]
- **β block.** Always with task family, verifier version, sample count, window, interval
  and verdict — V0-06 and v0-draft §5 make those fields mandatory wherever β is displayed,
  and `insufficient_data` is a first-class rendering, not an error. [asserted] The caveat
  line ("synthetic defects; real ones differ") is EXP-47 Part 7's competence-difficulty
  gap, rendered because a number without its caveat is a point estimate, and this project
  trades in sign and threshold. [asserted]
- **WORK band.** At most `n_max` rows, and the ceiling itself is shown with its
  derivation, because the ceiling is a measurement, not a preference. [algebra] Each row
  is level-1 state transitions only: dispatched, check outcome, decision taken, stall
  detected, finished (ADR-0035 §2). [asserted] "Running" carries the time of the **last
  artefact**, never a spinner — R9. [asserted]
- **Footer.** `NEEDS YOU: nothing.` — a positive statement, not an absence. The
  difference between "nothing needs you" and "the app is empty because it is broken" is
  the INSTRUMENT band: the record's freshness and the replay digest are the liveness
  truth, artefact-based, never process-based (ADR-0034). [asserted]

### What the user does

Nothing. That is the state working as designed: the harness has decided everything
reversible (ADR-0033 §1), the floor set (ADR-0035 §3) contains nothing, and the screen's
job is to make "nothing is owed" *distinguishable from silence*. [asserted] Optional
acts: turn the dial; open a work unit to render its events at a higher level; read the
evidence references behind any line. Every act is available; none is requested.
[asserted]

### What it refuses to show, and why

R2–R9 from §2, plus: it refuses to say anything evaluative about the work — no
"on track", no "going well", no adjectives — because a summary is an explanation with the
caveats removed (ADR-0035 §5, rule 5). [cited] And it refuses a notification badge: when
the footer has nothing to say, the application says nothing anywhere, including the dock.
[asserted]

### The metric that could prove it wrong

`T_effective_review` (artefact-complete → human-verdict wall-clock, already recorded in
the trajectory) and β stratified by surface. **Falsifier:** the GUI's median
`T_effective_review` fails to come in below the CLI's, *or* β under GUI use exceeds β
under CLI use by more than the wider of the two intervals over ≥20 verdicts per stratum —
the surface is then an acceptance amplifier, and the honest response is to stop building
it, not to adjust the metric (`surfaces-and-who-they-serve.md` §6). [asserted] Sign and
threshold, never a point estimate of delight. [asserted]

---

## 4. Concept 2 — the ask: the moment something DOES need them

**Gate:** none for the mechanism — asks already exist in the CLI's future contracts — but
the *rendering* is gated with Concept 1. [asserted]

**Answers the brief's question:** *what an unavoidable decision looks like.*

An ask exists only in ADR-0033 §2's seven classes: money, credentials, a preferential
question no fact settles, the safety floor, the β verdict, anything leaving the machine,
lifting a gate. [asserted] An ask outside those classes is rejected at configuration load
(V0-23) — so the UI cannot grow an eighth kind of interruption by accretion. [asserted]
Every ask renders the ADR-0033 §3 affordability fields verbatim: **what was tried, the
default if no answer arrives, and what it would cost to resolve without you.** [asserted]

### Layout A — the β verdict (the ask this project exists for)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ NEEDS YOU — a verdict · task #118 · class: β verdict (only you can give it)│
├──────────────────────────────────────────────────────────────────────────┤
│ artefact   branch task/118 · 3 files · +91 −34 · [ open in your editor ]   │
│ boundary   declared: src/consilient/{cli,events,projection}.py             │
│            touched: within boundary                                        │
│ checks     pytest pass · mypy pass · ruff pass — verifier v1.4             │
│                                                                            │
│ if you do nothing: nothing is accepted. #118 waits.                        │
│ your verdict is the ground truth β is measured against.                    │
│                                                                            │
│             [ accept ]          [ reject — and say what you saw ]          │
│                                                                            │
│ not shown: the agent's account of why its diff is right. never shown.      │
└──────────────────────────────────────────────────────────────────────────┘
```

The design decisions, each with its evidence:

- **The artefact opens in the user's own tools.** ADR-0007 already decided the reviewer is
  the one the user already has — worktrees, branches, their editor. [asserted] The screen
  is a *pointer plus two buttons*, not a diff viewer. [asserted]
- **What is shown is what the checks did and saw** — outcomes and boundary conformance —
  because the one manipulation measured to kill over-reliance was surfacing the error
  itself, and when a check fails its output appears here verbatim (Vasconcelos, corrected
  reading, §0). [cited]
- **The model's rationale is never on this screen** — R3. [cited] Neither is a
  recommendation, a confidence, or the critic's enthusiasm — R3, R4. [cited] Check
  *outcomes* are shown because they are the instrument's defined inputs; β is explicitly a
  lower bound on the joint human-plus-checks error, not a property of the checks alone
  (v0-draft §5). [asserted] The residual risk — that seeing "checks pass" nudges acceptance —
  is real, is named, and is what the §10 stratification metric is for. [asserted]
- **The prompt renders identically at every visibility level** (ADR-0035 §3). The GUI may
  not make it richer than the CLI's. This is a hard constraint, not a style. [asserted]
- **Approval latency is recorded, never displayed.** A verdict returned below the
  affordability floor is stored `unread` and does not satisfy V0-18 (ADR-0033 §4). The
  floor is preferential and user-set; showing a countdown would train against it, so the
  screen shows nothing. [asserted]

### Layout B — money (the contrast case)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ NEEDS YOU — money · task #131 · class: spend beyond your £5.00 task cap    │
├──────────────────────────────────────────────────────────────────────────┤
│ asked      £8.40 more on OpenRouter (metered) to finish #131               │
│ state      period ledger £31.20 of £50.00 · task ledger £5.00 of £5.00 —   │
│            hard stop, as configured                                        │
│ tried      local qwen3:8b composition — admitted, emitted no artefact      │
│            (0 of 25 measured attempts, 20 Aug)                             │
│ if you do nothing: #131 stops. no spend. it can be resumed later.          │
│ resolving without you: not possible — it is not the harness's money.       │
│                                                                            │
│    [ authorise £8.40 ]    [ authorise another amount ]    [ decline ]      │
│                                                                            │
│ no recommendation is shown: this is preferential, and it is yours.         │
└──────────────────────────────────────────────────────────────────────────┘
```

Note the asymmetry with Layout A, which is the ADR-0033 §1 rule made visible: a
*reversible* decision would have been taken already and reported with its reversal path;
an ask exists precisely where no reversal path exists (spent money is not recoverable at
any price). [asserted] The "tried" line carries the measured emit-failure of the local
composition (EXP-07, n=25) rather than a hopeful "the local model couldn't quite…" —
state, not narrative. [measured]

### What the user does

Reads the state, opens the artefact if the class demands judgement, decides. Or does
nothing — and the default, printed on the ask, happens, and the outcome (including
"expired, default taken") is recorded. [asserted]

### What it refuses to show, and why

R3, R4, R6, R10; no snooze that silently re-asks (a declined or expired ask records its
outcome and does not re-spend the budget on itself — ADR-0033 §5); no "other users
approved similar diffs" (a satisfaction signal in a trench coat — R6). [asserted]

### The metric that could prove it wrong

Two, both already instrumented by ADR-0033: the **`unread` rate** (approvals below the
latency floor) — if it is high, the asks are unaffordable and the correct response is to
make them cheaper or stop asking, never to add a confirmation step [asserted]; and the
**ask rate against budget** — a breach is a defect in the harness, not in the user
(ADR-0033 §5). [asserted] Thresholds are preferential and named as such; the *sign* is
not: more asks and faster approvals both point the wrong way. [asserted]

---

## 5. Concept 3 — offline / local-weights-only: a state, not a banner

**Gate:** none additional. The candidate set is ADR-0026's admission boundary, and this
concept is that boundary *rendered*. [asserted]

**Answers the brief's question:** *offline is a state, not a banner* — agreed, and here is
the state.

Offline changes **which compositions are admitted**, not the chrome. There is no aeroplane
icon and no amber strip. What changes is the content of the candidate set and the queue,
because admission — `headroom ∧ budget ∧ (remote ∨ hardware_feasible)` (ADR-0026)
[asserted] — evaluates differently when `remote` is false for everything. [asserted]

### Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│ CANDIDATE SET — evaluated 14:02:11 · last remote observation 13:47:02      │
├──────────────────────────────────────────────────────────────────────────┤
│ ADMITTED                                                                   │
│  (coding · opencode · ollama · qwen3:8b)        hardware-fit: ok           │
│    β: insufficient data (n=0) · emitted an artefact in 0 of 25 measured    │
│    attempts (20 Aug) — admission is not capability                         │
│                                                                            │
│ VETOED                                                                     │
│  (coding · claude-code · anthropic · opus-5)    no network since 13:47     │
│  (coding · codex · openai · gpt-5)              no network since 13:47     │
│  (coding · opencode · ollama · gemma4:31b)      fit unknown — no bytes     │
│    transferred (fit is decided before download, never after)               │
├──────────────────────────────────────────────────────────────────────────┤
│ QUEUE    2 runnable-but-unproven · 5 deferred                              │
│          deferred is not failed. deferred work waits; nothing is lost.     │
└──────────────────────────────────────────────────────────────────────────┘
```

### What is on screen, and why each line earns its place

- **Every composition is the explicit `(domain, harness, provider, model)` tuple**
  (ADR-0027), with unknown components shown as unknown, never inferred (V0-07).
  [asserted]
- **Veto reasons are the admission predicate's own terms**, stated plainly. "No network
  since 13:47" is an admission outcome with a timestamp, not a connectivity guess.
  [asserted]
- **The admitted local composition carries its measured emit rate** — 0 of 25 on 20
  August (EXP-07) [measured] — because ADR-0026 records that a composition can pass every
  admission term and still produce nothing, and that the emit/no-emit rate is a named gap
  in the admission predicate until EXP-31 and per-dispatch recording close it. [asserted]
  A screen that showed "qwen3:8b — ready" would be lying; this one says *admitted and
  unproven*. [asserted]
- **β is stratified per composition and honest about n.** Local-model β is a different
  number from frontier β, usually an unmeasured one; the screen says `insufficient data
  (n=0)` rather than borrowing credibility from the frontier figure. [asserted]
- **The queue partitions into runnable and deferred, and deferred is not failed.** Work
  that needs a remote composition waits, labelled as waiting. Nothing is retried in a
  loop burning local compute — convened structures carry caps and exhaustion escalates
  (V0-20). [asserted]

### What the user does

Nothing required. Optional: dispatch the runnable work knowing its composition is
unproven; mark deferred work to run when a remote composition returns; or explicitly
select a download — which triggers the fit gate first (V0-10), because fit is decided
*before* bytes transfer, and infeasible-or-unknown means no transfer. [asserted]

### What it refuses to show, and why

It refuses to download weights because the network returned (or was requested) without a
fit verdict — V0-10. [asserted] It refuses to mark deferred work as failed — a lie that
would corrupt the trajectory the queue is rendered from. [asserted] It refuses to blend
local and remote β into one number — V0-21's anti-compositing rule applied to the
instrument's own headline. [asserted] And it refuses to treat "offline" as degraded
*mode* theatre: it is the admission boundary telling the truth about a smaller feasible
set. [asserted]

### The metric that could prove it wrong

Two checks and one measure. **Check:** any dispatch in the offline state that attempts
network I/O fails CI — the state is a rendering of admission, and admission is a
chokepoint with an enforcement rule or it is not one (working principle 3). [asserted]
**Check:** a deferred task rendered as failed is a rendering defect with a fixture.
[asserted] **Measure:** the per-composition emit rate, recorded per dispatch as ADR-0026's
update requires; if an admitted composition's measured artefact rate stays at or near zero
across a pre-registered n, admission itself is revised — the screen is only ever as honest
as the predicate it renders. [asserted]

---

## 6. Concept 4 — CLI parity by construction, not by effort

**Gate:** none. This is the only concept that exists today, and it is the rule that makes
the other three cheap. [asserted]

The brief asks how a power user does everything without a window. The answer is not a
second interface built to match the first; it is a **rule that forbids the first from
having anything the second lacks**: V0-14 already requires every command to have one JSON
contract, with human output a rendering of the same result rather than a second
semantics. [measured — this ships in `cli.py`] The window is a renderer over
`consil … --json`. It holds no state of its own — what it shows is a projection of the
log, rebuildable at any time, deletable without loss (V0-02). [asserted]

### The mapping

| Screen region | Renders the contract of |
|---|---|
| INSTRUMENT band | `consil doctor --json` · `consil replay --json` · `consil beta --json` [measured — these exist] |
| WORK band | a future `consil tasks --json` — name illustrative; v0-draft §10 deliberately fixes no command names before contracts are approved [asserted] |
| The ask | the floor rendering (ADR-0035 §3); its outcome recorded by a future `consil verdict` / `consil approve` — same caveat on names [asserted] |
| CANDIDATE SET | a future `consil admit --json` [asserted] |
| The dial | `--level 0..3` and `--see ±kind` on any command (ADR-0035 §2) [asserted] |
| Re-entry brief | rendered before anything else on the next interactive invocation after absence (ADR-0035 §5) [asserted] |

### What the power user does

Everything, from a pipe: gates before a run (`consil doctor --json | jq
.routing_orchestration_enabled`), β per task family, replay verification in CI, verdicts,
level changes, the brief. Scripting *is* the power surface; the window is the same
contracts with pixels. [asserted] Configuration is one file both surfaces read; there is
no settings panel unbacked by it. [asserted]

### What it refuses, and why

A private API between the window and the core — the window shells the same commands the
user can. [asserted] GUI-only state, GUI-only verbs, a GUI-only settings store — each is
a second semantics, and V0-14 exists because a second semantics is where instruments drift
apart. [asserted] And parity is enforced, not hoped for: **a contract test asserts every
field rendered in the window traces to a field of a JSON contract, and any GUI-only
semantics fails the build** — the same-commit rule (I1) applied to the surface itself.
[asserted]

### The metric that could prove it wrong

The count of GUI-only semantics, which must be **zero**, mechanically, in CI. [asserted]
If the count's *sign* ever moves — one feature ships window-first "temporarily" — the
renderer rule is dead and the window has become a second product; that observation, not a
review meeting, is the falsifier. [asserted]

---

## 7. Concept 5 — consilient.dev cloud: the hosted, paid surface

**Gate:** ADR-0024 is PROPOSED, not accepted; this concept assumes its shape and inherits
its constraints. [asserted] Everything here is additionally bounded by two recorded rules:
no capability is ever withheld from the open-source version (ADR-0024 §1) [asserted], and
no secret is ever placed where a public repository can reach it — a capability needing one
runs locally or not at all (Joe, 20 August 2026). [measured — the recorded rule]

The brief's framing — "primarily everything is open source… cloud plans to make management
easier… minimal pricing… profitable for anything that costs on my cloud" — survives
contact with those rules, but only just, and the surviving shape is specific: **the cloud
sells operation, never features, and never custody.** [asserted]

### What the cloud is

Three components, in order of increasing cost to run — which is also the order of what the
money honestly pays for. [asserted]

**C1 — encrypted projection sync.** The trajectory's projection (never the authority —
ADR-0041 §1) syncs to consilient.dev so runs are watchable from any device. The cloud is a
dumb store: the projection is encrypted with a user-held key, enrolled devices hold the
key, and there is deliberately **no** "log into the website and see everything" without an
enrolled key — a server that can read your trajectory is a server that can leak it, and
ADR-0024's default is that nothing leaves at all unless the user turns it on. [asserted]
Deleting the cloud copy changes no local `state_digest` — sync is a projection, and that
is a replay-equivalence check, not a promise (V0-13's test, extended). [asserted]

**C2 — floor-event notification fan-out.** The floor set (ADR-0033 §2 asks, safety-floor
events, exhausted stalls, failed or unrun checks) pushes to the user's devices. One
notification per floor event; no badges, no counts, no digests-as-engagement (R11).
[asserted] Acting on one still requires the local CLI — or C3. [asserted]

**C3 — the hardware-attested verdict client.** ADR-0041 §3 forbids human verdicts over
untrusted transports, and names its own exception: a verdict accompanied by hardware
attestation (WebAuthn/FIDO2, or an Ed25519 signature from a secure enclave) whose private
key is inaccessible to agent tools. [asserted] A phone app whose verdicts are signed in
the device's secure enclave is the *only* remote verdict path the architecture admits, and
it is the first component that genuinely justifies a price — app-store distribution,
attestation infrastructure and key enrolment are real, continuing costs. [asserted]

```
watching (C1+C2)                          verdict (C3)
┌──────────────────────────────┐          ┌──────────────────────────────┐
│ consilient — watching        │          │ verdict · #131 · signed here │
│ synced 40 s ago · projection │          │ artefact: 3 files +91 −34    │
├──────────────────────────────┤          │ checks: pass · boundary: in  │
│ #121 running — artefact 13:58│          │ [ open diff on this device ] │
│ #122 accepted (you, via cli) │          │                              │
│ β 0.31 [0.29, 0.33] n=1,871  │          │ [ accept ]    [ reject ]     │
├──────────────────────────────┤          │ signs with this device's     │
│ NEEDS YOU: verdict on #131   │          │ hardware key; the signature  │
│ [ open attested verdict ]    │          │ is what the log records.     │
└──────────────────────────────┘          └──────────────────────────────┘
```

The attested screen obeys Concept 2 unchanged — same fields, no rationale, latency
recorded — plus the one thing only it can add: the signature. The `via` field on the
verdict event records the channel, which is what makes the falsifier below computable.
[asserted]

**A fourth component, later, and only with its own ADR — hosted execution.** ADR-0024 §4
ranks "hosting and operation — running it for people who do not want to" as the
least-conflicting commercial path. [asserted] The only shape compatible with the secrets
rule: the cloud runs tasks on **Consilient's own metered OpenRouter account** (the sole
metered vendor, ADR-0044) behind task-scoped, provider-enforced keys with hard caps
(ADR-0026), billed through at cost recovery; **the user's provider credentials are never
accepted, stored or asked for.** [asserted] The runner's events return to the user's
machine as *untrusted inbound proposals*, validated and appended by the local harness —
the cloud proposes, the local record disposes (ADR-0041 §§1–2). [asserted] If that shape
cannot hold, hosted execution is not built; the rule is the rule. [asserted]

### Pricing shape

Cost recovery, stated plainly on the page: measured marginal cost of storage, bandwidth
and push delivery, plus amortised build and attestation costs for C3, plus a published
margin. [asserted] The free tier is the entire MIT product, locally, forever — ADR-0024 §1
makes "the cloud unlocks features" a permanent refusal, not a pricing decision. [asserted]
The marketing surface obeys V0-21 like every other: no composite claims, no "10×", no
testimonial counters — the product's own rules about unmeasured signals apply to its
shopfront. [asserted]

### What it refuses, and why

R10 (no verdict without attestation — a web button on consilient.dev is an untrusted
transport), R12 (no credential custody), R6 (no satisfaction prompts in the paid app —
paying does not repair the sensor), telemetry of any kind by default (ADR-0024 §2: off
means nothing leaves), and per-use re-consent for any commercial use of contributed data
(ADR-0024 §3a — silence is a decline). [asserted]

### The metric that could prove it wrong

**β stratified by verdict channel.** `via` is recorded on every verdict (ADR-0041's
enforcement already requires it). [measured — the field exists in the schema] Falsifier:
β over attested-mobile verdicts exceeds β over local-CLI verdicts by more than the wider
of the two intervals, over ≥20 verdicts per stratum — the channel is then an acceptance
amplifier (a small screen, a queue of asks, a thumb) and C3 is revoked, not patched.
[asserted] The same stratification by visibility level is EXP-42's machinery, reused.
[asserted] And C1's honesty check: delete the cloud copy, replay locally, compare digests —
any difference fails the build. [asserted]

---

## 8. Where the brief is wrong, named

The brief instructs disagreement where it is wrong. Four places, plainly:

1. **"A single perpetual conversation."** Refused as chat (§1); honoured as the single
   perpetual *record*. The want is real; the metaphor is the echo chamber. [asserted]
2. **"0-click" against "maximal configurability."** The contradiction dissolves only on
   two different axes: *interrupts* versus *parameters*. 0-click means zero unaffordable
   asks (ADR-0033), not zero choices; configurability lives in the file, the flags and the
   dial, and the default user never meets it. [asserted] The residual is real and is
   named rather than designed around: **the floor set, the verdict prompt, the JSON
   contracts and the evidence tags are not settings.** Maximal configurability stops at
   the instrument's integrity, because a configurable instrument is how the system ends
   up grading its own homework (Q32, EXP-13). [asserted]
3. **"Life changing, omni-transformational… whatever touches the harness."** Not a
   specification. The only honest form of the claim is measurable: `T_effective_review`
   down, β not up (`surfaces-and-who-they-serve.md` §6). [asserted] And Q24 is open: β is
   defined where checks exist, and nobody knows what β means for a strategy memo — so
   "whatever touches the harness" is today a claim about coding, and the non-developer
   surface is gated on an open research question, not on design effort. A beautiful
   interface over an unmeasured oracle is the exact failure this project exists to name.
   [asserted]
4. **"Practically unlimited tokens."** ADR-0028: never burn quota for its own sake.
   [asserted] Unlimited budget is not a reason to render, simulate or run anything without
   a falsifiable question attached; it is only the removal of an excuse for not running
   the ones that have one. [asserted]

## 9. What simulated user research is for here — and what it can never show

The brief proposes simulated users and simulated QA. The discipline, per the brief itself
and working principle 2: simulation answers **sign and threshold**, never **what users
want**. [asserted]

- **Legitimate:** fixture-testing the rendering invariants — the floor set survives at
  every level including `silent` with overrides against it; the re-entry brief's order
  puts divergences and failed checks before completed work; the no-adjectives lint holds;
  `--json` is byte-identical across levels (ADR-0035's checks 1–4, 8). [asserted] These
  are tests of the *pipeline's logic*, and synthetic sessions exercise them cheaply.
  [simulated]
- **Illegitimate:** a synthetic user's approval as evidence about β, desirability or
  comprehension. A model grading a model's diff against a model's judgement is the system
  generating its own oracle — Q32's self-grading hazard, pre-registered in EXP-13.
  [asserted] Every simulated result is tagged `[simulated]` and never quoted as a fact
  about real users. [asserted]

## 10. The metrics that could prove this wrong — summary

| Concept | Metric | Sign / threshold that falsifies |
|---|---|---|
| 1 · instrument panel | `T_effective_review`; β by surface | GUI median not below CLI, or β_GUI − β_CLI beyond the wider interval over ≥20 verdicts per stratum → stop building surfaces [asserted] |
| 1 · the dial | level changes per 30 days; briefs followed by action | <3 changes and no followed brief → cut to `--quiet` + floor (EXP-42's pre-registered rule) [asserted] |
| 2 · the ask | `unread`-approval rate; asks per period vs budget | high unread rate → asks unaffordable: make cheaper or stop; budget breach is a harness defect [asserted] |
| 2 · verdict prompt | rendering invariance across levels | any difference fails CI (ADR-0035 §3) [asserted] |
| 3 · offline state | network I/O on offline dispatch; deferred-as-failed | either occurring fails CI [asserted] |
| 3 · admission honesty | per-composition emit rate | admitted composition at ~0 artefacts over pre-registered n → revise admission (ADR-0026's named gap) [asserted] |
| 4 · CLI parity | count of GUI-only semantics | must be 0, mechanically, in CI [asserted] |
| 5 · attested verdicts | β stratified by `via` | β_mobile − β_local beyond interval overlap, ≥20 per stratum → revoke the channel [asserted] |
| 5 · sync | replay-equivalence | deleting the cloud copy changes no local `state_digest` [asserted] |

## 11. What would overturn this document

- **EXP-08 measures critic recall high enough** that the parallelism ceiling rises well
  above three: review-time reduction stops being the binding lever, and Concept 1 drops
  down the priority list rather than up it. [asserted]
- **EXP-42 cuts the dial to `--quiet` plus the floor:** Concept 1's levels collapse to a
  flag, and the window loses its only control. [asserted]
- **Q24 resolves against β outside coding:** the non-developer surface is not harder — it
  is a different product, and this document should say so plainly rather than design
  toward it. [asserted]
- **Any surface is measured to raise β:** the claim in §0 is wrong in its optimistic
  direction, and the honest response is to stop building surfaces, not to adjust the
  metric. [asserted]
- **ADR-0007's reopen conditions never fire:** this document remains what it is — a
  concept, derived and recorded, permanently unbuilt. That outcome is acceptable by
  construction: the CLI is not a limitation (`surfaces-and-who-they-serve.md` §1), and a
  design that cannot survive its own gate did not deserve to. [asserted]

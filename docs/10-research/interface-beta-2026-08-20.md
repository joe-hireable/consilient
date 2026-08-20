# There is no useful β for an interface

**Date:** 20 August 2026
**Status:** `[measured]` for the CLI facts and for every number quoted from a named experiment;
`[algebra]` for the definition of a known-invalid view; `[asserted]` for the rest, which is
most of it.
**Asked by Joe**, commissioning a front end and asking for world-class QA automation with
scientific, mathematical, experimenting decision protocols.

---

## Framing, which is the answer

The question *"what is β for an interface?"* treats β as a brand name for rigorous QA of a
UI. It is not. β is $P(\text{checks accept} \mid \text{artefact bad})$. EXP-47 could measure
it at **0.3132 [0.2926, 0.3346]** over 1,931 mutants, with no human labelling, in 104 seconds,
because a mutant is bad *by construction*. [measured] A confusing screen is not. Asking for
an interface-β as the scientific protocol for front-end QA smuggles in a population of bad
artefacts that nobody has a mechanical way to build, and would produce a number that looks
like 0.3132 and is not.

This is the same category error Q24 already named for a strategy memo, and that
`surfaces-and-who-they-serve.md` already recorded: nobody knows what β means where there is
no cheap automated oracle, and a beautiful interface over an unmeasured one is the failure
this project exists to name. [asserted] The front-end case is not quite as empty as the memo
case, because ADR-0041 gives this architecture an unusual property the memo does not have:
**every surface is a projection of one append-only record.** A projection can be wrong about
the record in ways that are decidable. That class needs no human. It is also not β of an
interface. It is β of a *check* — the object ADR-0012 already has.

Joe asked for two things at once. Usability QA still needs a human. Projection QA does not.
Collapsing them into "interface-β" would launder the second into a number for the first.

---

## What this cannot decide

Stated here, before any definition or experiment, because these are the questions a front-end
commission will actually want answered.

- **Whether a front end should be built.** ADR-0007 is ACCEPTED and still governs: CLI only,
  and build no review surface. Commissioning one is a decision that has to supersede 0007; this
  note does not. [asserted]
- **Whether a surface reduces review time without raising artefact-β.** That is the right
  product claim (`surfaces-and-who-they-serve.md` §6) and it needs a real surface, a real
  repository, and a human verdict. Nothing mechanical here can substitute. [asserted]
- **Whether a layout is confusing, ugly, slow to parse, or missing an affordance a person
  wanted.** Those are not constructable as mutants. A model asked whether a screen is confusing
  is producing its priors. Working principle 5; the cousin of the reason ADR-0040 was
  deprecated; already refused for synthetic users in `qa-automation-and-the-anchor-problem.md`.
  [asserted]
- **The rate of EXP-01's affordance-after-reload class.** That is an existence proof that a
  UI defect can sit in a β population (checks green, feature gone after reload). [measured]
  n=2 confirmed escapes total. It is not a rate, and it is β of the *application's* checks,
  not of an interface-QA suite. [asserted]
- **Whether "world-class QA automation" in the ordinary Playwright / snapshot / simulated-user
  sense finds the defects real users hit.** Q32.1 recorded that the literature measures
  execution accuracy and behavioural fidelity, not fault detection against humans. [asserted]
  This note does not re-open that.

EXP-54, registered below, cannot decide any of the above either. It can only decide whether
the *decidable* class is large enough and guarded enough to be worth naming as a check.

---

## Verdict, ranked by what it would change if believed

1. **Do not name an interface-β, and do not organise the front-end programme around measuring
   one.** Highest impact. A usability-β cannot be defined without a human, so any number
   published under that name would be either a human-labelled rate at solo-founder volume
   (EXP-01: audit-limited, not history-limited) or a simulated-user rate quoted as measured
   within a week. The brief asked whether to say there isn't a useful one. There isn't, for
   the object the question named. [asserted]

2. **Ship a log-anchored view checker as an ordinary invariant, in the same commit as any
   surface.** Working principle 3. The checker compares a view to the log; it does not compare
   a view to the renderer. A test that takes its expected value from the UI code cannot fail
   — that cancellation is `[algebra]` and is the load-bearing identity in
   `qa-automation-and-the-anchor-problem.md`. The log is the specification-anchor this
   architecture already has. This changes the first tests written for a front end: they are
   "does this screen claim a state the log does not support", not "does Playwright match last
   week's screenshot". [asserted]

3. **The existing human-facing surface already fails a named operator of that class.**
   `[measured]` tonight, one fixture: `consil beta --json` reports `"quarantined": 1` on a
   log with one refused line; `consil beta` without `--json` prints
   `beta [all]: insufficient data (0 human rejections, need 30)` and does not mention the
   refusal. V0-14 says human output is a rendering of the same result, not a second
   semantics. The test that claims to enforce it
   (`test_human_output_renders_the_same_result_as_json`) checks that `n_rejected` and the
   words "insufficient data" appear; it does not check `quarantined`.
   `test_beta_reports_what_the_log_refused` asserts the JSON path only. `events.read_all`
   claims every CLI command reports the refusal count; the human `beta` path does not.
   This is an ordinary bug, not a research finding — principle 4 says the fix is a check —
   and it is the existence proof that the decidable class is not hypothetical.

4. **EXP-47 already measured the renderer, and the human-readable path is the weakest-guarded
   product module.** `[measured]` `cli.py`: 1,104 mutants, 440 composite survivors, **400
   true defects**. The findings record that table-alignment, header, and status-text mutants
   survived *because the suite asserts JSON rather than stdout*. `projection.py` is tighter
   (44 true defects / 248) because replay-equivalence has a digest. A front end that reads
   SQLite rather than the JSON contract inherits those 44 plus its own. A front end that
   renders from `--json` inherits tonight's V0-14 hole instead. Either way the human-visible
   form is the one the current suite does not look at.

5. **Implicit oracles (crash, hang, missing accessible name, contrast failure) are worth
   running and are not β.** They are the cheap, high-precision, narrow row in the Q32 table.
   They do not need a new quantity, a simulated user, or a research programme. [asserted]

6. **Simulated personas, visual-LLM judges, and "is this screen confusing?" probes are the
   obvious move and are already refused.** EXP-45 retired one plausible β-analogue that
   looked mechanical (retention 40.71%, consequential loss 0.00%, median session 2.7 minutes):
   the perpetual-memory layer was solving a problem the corpus does not have. [measured] A
   simulated-user β would be the same shape of mistake, with a worse oracle. [asserted]

---

## 1. Why there is no useful interface-β

β needs three things: a population of artefacts, a mechanical definition of *bad*, and a
check that can accept or reject. Mutation testing supplied all three. An interface supplies
the first and the third and fails the second.

| Candidate definition of a bad UI state | Mechanical without a human? | What kind of oracle |
|---|---|---|
| View claims a state the log does not support | **Yes** — compare view to log | Specification-anchored (the log) |
| Crash, hang, uncaught exception, 5xx | **Yes** — the runtime | Implicit |
| Missing accessible name, contrast below a WCAG threshold | **Yes**, narrowly — axe-core and friends | Implicit, incomplete |
| Snapshot differs from last week | Yes, and **blind to whether last week was right** | State-anchored |
| Layout is confusing; copy is misleading; affordance is hidden | **No** | Human |
| A model says the screen is confusing | No — it is a prior | Echo (working principle 5) |

The first row is real and is §2. It is not "β for an interface". Calling it that would let
every later reader quote a projection-checker's false-accept rate as if it were a usability
number. Sign and threshold, never point estimates (working principle 2); a simulated or
mis-named figure will be quoted as measured within a week, which is the failure the brief
already named.

The human rows cannot be rescued by volume. EXP-01's two oracles disagreed on 16 of 75
labels, and the disagreement *was* the finding. [measured] UI correctness has no `pytest`.
Joe cannot cheaply label "is this confusing?" at the volume a β interval needs (ADR-0002:
50–200 labels; `MIN_REJECTIONS` is 30), and asking him anyway would launder an agent
judgement as a human one (ADR-0033). `ground-truth-evaporates-2026-08-20.md` is the measured
case of that, on code, where he at least had a repository. On a UI he has not used, it is
worse. [asserted]

Self-report is a broken sensor in this population even when the human is willing: the
synthesis in `human-success-and-the-human-side-of-beta.md` records METR's experienced
developers reporting a 20% speedup after a measured 19% slowdown. A thumbs-up on a screen
is not an oracle. [asserted, restating that note]

---

## 2. The class that is decidable

ADR-0041: the JSONL trajectory is the sole source of truth; SQLite is its local deterministic
projection; every external surface is a lossy view outbound and an untrusted proposal inbound.
A view of that record can be *wrong about it* in ways a program can decide. The analogue of a
mutant is an operator that makes the view disagree with the log. Badness is then by
construction, with an equivalence class: an operator that changes a field the surface cannot
show is equivalent, the same way a docstring mutant was.

**Named operators, fixed before EXP-54 runs.** Each is a known-invalid view. None needs a
human.

1. **Phantom event** — the view contains an event, outcome, or verdict the log does not.
2. **Dropped refusal** — the log quarantined a line and the view does not say so. (Tonight's
   instance.)
3. **β without its interval** — a measured point shown with no `[low, high]`.
4. **Point outside its interval.**
5. **`measured` with $n < 30$ rejections** — the constructor in `beta.py` forbids this in
   the object; a view can still print it.
6. **`insufficient_data` carrying a point estimate.**
7. **`routing_orchestration_enabled: true` while any named gate condition is not `pass`.**
8. **A `HUMAN_ONLY` decision (`verdict`, `approval`, `gate_lift`, `spend_authorisation`)
   shown as accepted with `via` in `{slack, twilio, email, webhook}` and no signature.**
9. **Events displayed in an order the log does not have, without saying they were reordered.**
10. **A replay digest claiming identity with a log that has since gained or lost a line.**

These are `[algebra]` once the view is a structured object. They are `[asserted]` as a
complete catalogue: there will be others, and EXP-54 is forbidden from adding operators after
the run starts.

Two properties of this architecture make the catalogue cheaper than it would be for a
generic UI.

- **One record.** There is no second store the view can be faithful to instead. A screen that
  matches SQLite and not the log is still wrong (V0-02: delete the database, replay, state is
  identical). [asserted]
- **The JSON contract is already supposed to be the view-model.** V0-14. A front end that
  renders from `consil <cmd> --json` has one hop. A front end that queries SQLite has two,
  and inherits `projection.py`'s surviving mutants. [asserted] Recommendation: render from
  the JSON contract, and make the log-anchored checker the test of that contract against the
  log, not against the renderer. The strongest objection is that JSON-as-view-model still
  failed tonight on the field the human path drops — so the checker has to be run against
  *whatever the human actually sees*, not only against `--json`. [measured]

What this class structurally cannot catch: colour, type, spacing, copy, the presence of a
control the log does not mention because nobody logged the intent, and every usability
failure that is faithful to the record. Faithful and unusable is inexpressible here. That is
not a gap in the catalogue. It is the boundary of the mechanical class.

---

## 3. EXP-54 — is the decidable class large enough to be a check, or only a bug?

Registered because one fixture is an existence proof and a rate needs a census. Also
registered because the tempting move is to declare "interface-β = projection β" and start
quoting it. The stopping rules below include the result that kills that move.

See `experiment-register.md` EXP-54. The design in brief:

- **Artefact:** a view of a fixture log — arm J is the `--json` payload; arm H is a structured
  parse of human stdout (and, later, of a DOM or accessibility tree, which this run does not
  have because there is no front end).
- **Badness:** apply the ten operators. Equivalence = the surface cannot express the field,
  so the mutant is invisible. β is over non-equivalent view-mutants only.
- **Checker:** specified before the run; may read the view and the log; may not read the
  renderer source. A checker that diffs against the renderer is state-anchored and is not
  this experiment.
- **Control:** the existing pytest suite against the same invalid views. If pytest already
  kills every live operator, EXP-54 has discovered a missing test file, not a quantity.

The result that goes against the idea: **if both arms' corrected β lie below 0.05, or if arm
H has fewer than five live (non-equivalent) operators, there is no quantity to name.** Write
the checks. Do not start a research programme. Tonight's quarantine hole is then a one-line
test, which is what principle 4 already says to do.

---

## 4. What a front-end QA programme can actually be here

If a surface is built — which this note does not authorise — the honest stack, cheapest
first:

| Layer | Oracle | β-shaped? | Ship when |
|---|---|---|---|
| Log-anchored view checker, operators 1–10, against the human-visible form | The log | Yes, of the *checker* | Same commit as the surface |
| Implicit oracles: crash, hang, axe-core / equivalent on the accessibility tree | Runtime | No — implicit, narrow | Same commit |
| Replay-equivalence if the surface has its own store | Canonical digest, as SQLite already has | Yes, of that store | Same commit as the store |
| Time from artefact-ready to human verdict, edit distance of accepted diffs | Behaviour, already in the trajectory | No — it is an input to artefact-β, not a UI-β | Free, if the surface is the verdict path |
| Human usability | Joe, or users, on real tasks | No | After ADR-0007 is superseded, and never as a β |

Explicitly not in the stack: simulated personas, visual-LLM "does this look right", snapshot
tests used as an acceptance oracle, confidence displays, explanation panels, composite health
scores, thumbs-up. Each is already refused, with a measurement, in
`surfaces-and-who-they-serve.md` §5 or `qa-automation-and-the-anchor-problem.md`. [asserted]

---

## Evidence against this note

- **The strongest available UI-defect observation cuts against §1.** EXP-01's
  affordance-after-reload escape is a user-visible failure the checks accepted. [measured]
  If that class is frequent, "there is no useful interface-β" is too strong: there is a
  useful β *of application checks on UI behaviour*, which is just β, and the missing piece
  is a specification-anchored check for affordances, not a new quantity. n=2. [asserted]
- **Implicit accessibility oracles are more mechanical than §1's table may read.** Contrast
  ratios and missing names are decidable. A programme that ran only those would already
  outperform a simulated-user β on precision, and this note would look like it had
  under-sold ordinary QA in order to keep the architecture's centre clean. [asserted]
- **V0-14 already specified the correspondence.** Tonight's hole is a test gap, not a
  conceptual discovery. EXP-54 may fire the "write the checks, stop naming quantities" rule
  on the first run, in which case this note's experimental half was unnecessary. That is an
  acceptable outcome and is pre-registered as one. [asserted]
- **ADR-0007's arithmetic may already forbid the surface this would test.** If EXP-08
  measures critic recall high enough that review-time is not the binding lever, the
  developer front end drops down the list (`surfaces-and-who-they-serve.md` §2) and EXP-54
  is measuring a check for a surface that should not be built. [asserted]
- **One fixture, one author, one evening.** The quarantine hole is `[measured]`; the
  catalogue of ten operators is `[asserted]`; the claim that usability-β is not useful is
  an argument. A different reader who started from "Joe is going to ship a UI anyway" would
  reasonably write the checker and skip the philosophy. [asserted]

---

## Cross-references

`CONSILIENCE.md` clauses 1–3 · ADR-0002, ADR-0007, ADR-0010, ADR-0012, ADR-0033, ADR-0040
(deprecated), ADR-0041 · EXP-01, EXP-45, EXP-47, EXP-49, EXP-54 ·
`qa-automation-and-the-anchor-problem.md` · `human-success-and-the-human-side-of-beta.md` ·
`ground-truth-evaporates-2026-08-20.md` · `../20-design/surfaces-and-who-they-serve.md` ·
`../00-context/open-questions.md` Q24, Q32.

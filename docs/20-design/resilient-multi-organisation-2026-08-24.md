# Resilience first, many organisations second

**Design · 24 August 2026 · supersedes nothing; it narrows what an earlier draft proposed.**

Every number below was read or run in this tree on 24 August 2026 between 21:55 and 22:10 UTC+1
unless a tag says otherwise. Where an earlier document in this chain reported a different figure,
mine is later, not better; the trend matters more than either point.

---

## 1. Thesis

**Almost all of the value here is resilience, and multi-organisation is scale rather than
architecture.** The principal asked for two things and they turn out to be very unequally sized.
The six measured failure classes are real, they are all in the orchestration layer, and they
reduce to five properties that are mostly *already built and unwired* in this repository —
wiring them is worth doing today with exactly one organisation. Running many organisations, by
contrast, adds **no new class of facts at the artefact level** (N projects are N disjoint
decision problems) and — this is the correction the adversarial pass forced — **no new class at
the measurement level either, as long as every organisation shares one `dispatch.py`, one
`build_driver.py` and one `recall.py`.** Two things that differ only by a directory name cannot
constitute a different class of facts; agreement between them is echo in Whewell's exact sense.
What genuinely differs is **projects**, and five projects sampled sequentially over five months
give the identical β sample that five run in parallel do. Parallelism buys wall-clock. Nothing
else. So this document proposes **two** multi-organisation mechanisms — both of which are
correctness bugs *today* rather than future features — and spends the rest of its length on
resilience, which is where the risk is. And it opens with the measurement that collapses most of
the crash story into one line of code: **76.7% of the trajectory file that 36 processes contend
over is a list of the events recall decided *not* to read.**

---

## 2. Six classes, five root causes, and the check for each

### 2.0 What I measured, and where it corrects the chain

| Fact | Value, 24 Aug 22:05 | Source |
|---|---|---|
| `crash_history` | **3,108** across **81** units | `.harness/driver-state.json` |
| dominant signature | **2,742** — `EventError: …\.harness\log\2026-08-24.jsonl could not be read after 6 attempts` | ibid. |
| next signatures | 338 `git.EXE` `TimeoutExpired`; 8, 5; 4 cursor-lock; 4 `MemoryError` | ibid. |
| `attempts` | `{0: 79, 1: 26, 2: 3}` over 108 units, cap 3 — **max 2, never bound** | ibid. |
| `review_attempts` | 67 units, **max 27**, no ceiling anywhere in code | ibid.; `build_driver.py:1604-1605` |
| retirement paths | `verified` 22 · `built` 73 · `done` 3 · **`force_done` 23** | ibid. |
| today's trajectory | **40,716,492 B** over **3,079** lines | `.harness/log/2026-08-24.jsonl` |
| **of which `instructions.assembled`** | **31,219,615 B = 76.7%**, n=283, mean **110,316 B** | measured by kind |
| one such event | 85,442 B total, of which `data.recall.omitted` = **84,603 B (99%)**, 454 entries, `selected_event_ids` **empty** | sampled |
| bytes per event by day | 782 → 2,055 → 2,923 → 3,590 → 6,253 → **13,223** | `.harness/log/*.jsonl` |
| `raise` sites in `src/consilient/` | **729** | `grep -c` |
| guard-mutation registry | **3** entries | `check_guard_mutation.py:75` |
| gate scripts / with `def self_test` | **21 / 10** | per-file grep |
| `record_intent` / `starvation()` production callers | **0** (internal + `tests/test_intent.py` only) | grep |
| `.harness/state.db.stale-*` | **292 files, 3.04 GB** | `ls` + `stat` |
| worktrees on the one common git dir | **117** | `.git/worktrees` |
| headroom pools with a usable meter | **1 of 5** (`codex-weekly` 48.0%) | `.harness/headroom.json` |

**[measured] Correction A — the crash story is one field, not one file.** 76.7% of the contended
trajectory is 283 events averaging 110 KB, and 99% of a sampled one is
`data.recall.omitted`, a list of every event recall declined to use, emitted alongside an
**empty** `selected_event_ids`. Per-event size has doubled daily for four days (2,923 → 3,590 →
6,253 → 13,223 B), because a longer log yields more omissions which are inlined into the next
event, which lengthens the log. That is quadratic and it is the amplifier behind 2,742 of 3,108
crashes. The emitter is `_selection_receipt` in `src/consilient/instructions.py:517-535`. **A
document that opens with a crash count and proposes a semaphore over claim admission has stopped
at rung 7 of the ladder; rung 1 is to stop writing the negative space into the audit log.**

**[measured] Correction B — the durability defect is broader than reported.** `git ls-files
.harness` returns `driver-state.json` (719,911 B, the authoritative scheduling record),
`driver-tick.lock` (**a lock file in version control**), `build-loop.out`, `build-loop.err`, and
**two complete extra copies of `src/consilient/`** under `.harness/exp-s02-audit-*/` and
`.harness/s02-mut-*/`. Any `git checkout` can restore the file that decides what is dispatched,
which is exactly how `plan-units.json` silently lost a queued unit. The extra source copies also
make "the module" ambiguous for the guard registry inside a single organisation.

**[measured] Correction C — `review_attempts` is at 27, and rising fast.** It was reported as 12,
then 14, then 21, then 22 earlier today. The increment is two lines (`build_driver.py:1604-1605`)
and there is no comparison to a ceiling anywhere. The adversarial review path is the second class
of facts — it is the entire product — and it is the one dispatch path with no supervision at all.

**[measured] Correction D — `force_done` (23) exceeds `verified` (22) and is 7.7× `done` (3).**
The path that actually retires work in this build is the principal typing an override. Any
argument that scales this system by N must survive that fact first.

### 2.1 The five root causes

| # | Root cause | Structural property | The check that enforces it | Already here? |
|---|---|---|---|---|
| RC-1 | A fact about another party is **inferred by the observer** rather than emitted by the subject | Every predicate over another party's state resolves to an event that party wrote, or to `unknown`; `unknown` fails closed and is a **type**, not a convention | `Liveness = Literal["running","gone","unknown"]` + `mypy --strict` (already in CI) rejects `if liveness:` at every call site | **Half-built, unwired.** `coordination.release_claims_when_worker_gone` already returns exactly those three values; V0-30 already enforces the shape for usage figures |
| RC-2 | Identity of work is **minted by the worker**, so every join is made on content | The initiator mints `work_id` before the process exists; no join on commit subject, brief body, filename or mtime | `commit_gate.py` refuses a commit with no `Consilient-Work-Id:` trailer; a lint refuses `--format=%s` and `brief.read_bytes()[:N]` as identity joins | **Half-built.** `artefact_identity()` already binds review verdicts to an immutable artefact+attempt; builds do not use it |
| RC-3 | Two state stores, and the **authoritative one is not the one decisions read** | One append-only log is the only writable state; every other file is a disposable projection | `test_projection_is_disposable` — delete the projection, rebuild from the log, assert equality; plus `git ls-files` over harness state must be empty | **Substrate built, unwired.** `_write_validated`, `append_transaction`, `register_transition_validator`, `prefix_digest` all exist; the driver appends once |
| RC-4 | **No check has ever been shown an input whose correct verdict is known.** α=1 and β=1 are the same defect: two ways to carry zero information | Every check registers one pinned artefact it must **accept** and one it must **refuse**, both drawn from normal operating state; CI runs both; deleting the check's refusal turns its declared tests red | `check_witnesses.py` (new) + `check_guard_mutation.py` (exists, CI-wired) with coverage as a ratchet that may only rise | **Convention in 10 of 21, required in 0.** `check_private_repo_names.py:132-135` is the pattern, hand-written |
| RC-5 | A resource with **no declared owner** is shared, and contention is discovered by blocking on it | Every mutable resource has exactly one writer named before dispatch; an unpartitionable resource is declared scheduling capacity, not a lock | `test_two_organisations_share_no_git_common_dir`; a lint refusing literal harness paths outside one path function; a digest of the repository *and* global git config across each dispatch | **Validator built, zero emitters.** `organisation.plan.frozen` already requires `owned_paths`, exactly one integration stream, acyclicity, and refuses a theatre-only split; `freeze_plan` is called from tests only |

**RC-4 is the largest** — it covers all of Class 4 and all of Class 6 plus at least four items
filed elsewhere (the `suite_green()` unsupported flag, the id-vs-subject mismatch, the handover
cmdline match, and the reclamation predicate that could not distinguish a healthy 31-minute run
from a dead one). **It is also the only root cause on the β axis.** The other four buy liveness
and isolation, and this document says so in those words wherever it matters.

**[cited] The bar for RC-4 is program mutation testing and the incumbent already lost here.**
mutmut (BSD-3) and cosmic-ray (MIT), registered at EXP-47; EXP-48 measured recall 20.0% at
cluster precision 24.6%, with 68% of catalogued guards living outside Python source entirely, and
a CI gate on "no surviving mutant" would open red on 586 survivors. The declared-guard registry
beats it on precision by construction and loses badly on coverage — **3 of 729**. Raising
coverage is the work; the design question is settled.

**[measured] The K01 exemplar, verbatim.** `.github/scripts/check_heldout_isolation.py` is 24
lines and its `main()` ends `return 2` with no branch. It refuses every argument. Four units
depend on it and no contract-β can ever be measured through it. **An accepting witness would have
failed CI on the day it was written.** That is the entire argument for RC-4 in one file.

---

## 3. The organisation model, sized to what the checks can carry

An organisation is **one directory and one scheduled task**, and this document proposes building
almost none of it now.

```
org_id          a directory name, [a-z0-9-]{1,32}
org_home        ~/.consilient/orgs/<org_id>/     everything mutable it owns
workspace_root  the tree it works on             exactly one, never shared
```

`org_home` holds `log/<date>.jsonl` (the only writable state), `state.json` (a projection),
`plan-units.json`, `runs/<work_id>/`, `loop.lock`, `tick.lock`, `status.json`.

**Why `org_home` sits outside `workspace_root`** [measured]: the three files that decide what runs
are currently tracked git objects in the tree the agents edit, and a gitignore line is not
containment because an agent can edit `.gitignore` and `git checkout` does not consult it for
tracked files. Moving the state out makes "mutable organisation state is not a git object"
structural. **But the whole benefit of that move is available today for the cost of `git rm
--cached` plus three gitignore lines plus one test** — which is why the untracking is a unit and
`org_home` is not.

**Four things this model deliberately does not have.**

- **No `org_id` field on events, claims or leases.** A second spelling of an identity that can
  disagree with the first is a second detector, and `validate()` does not reject unknown
  top-level keys, so nothing would make it mandatory. **An event's organisation is the directory
  it lives in.** The one exception is the commit trailer, and it earns its place only because a
  check compares it against the tree that owns it and refuses a mismatch. The general rule, and
  it is enforceable: *a redundant copy of an identity is permitted only where a check compares it
  against the primary and refuses on mismatch.*
- **No `Organisation` class, no registry object, no registry service.** `listdir` is a projection
  that cannot drift from what exists; a registry beside the directories is Class 3 one level up.
- **No hierarchy.** [cited] Kubernetes archived the Hierarchical Namespace Controller in April
  2025 because hierarchy was not the abstraction teams needed and stronger isolation layered on
  top was.
- **No deontic layer, no roles, no institution — for now.** [asserted] MOISE+, AGR and electronic
  institutions were designed for *open* systems: third-party agents you did not write and cannot
  change. Here every participant is a vendor CLI invoked by a script this repository owns. In a
  closed system the norm and its enforcement collapse into the dispatcher, and writing the norm
  down separately creates the second-spelling problem again. The **one** exception worth keeping
  on the list is the obligation row (`{role, mission, bearer, due}`), because it buys something a
  scheduler structurally cannot: **absence gets an artefact**. Three adversarial reviews crashed
  at startup, three units reached `done` with no cross-family check, and nothing recorded that
  the check had not happened. That is a genuinely different class of fact — a fact about what did
  not occur — and it is ~40 lines of validator. It is on the list, after the resilience work.

**[asserted] And the name.** An organisation here is a directory and a scheduled task. Calling
that a *kernel* would be exactly the failure AGENTS.md forbids. This document has no new nouns in
it.

---

## 4. What is shared, and whether it can be partitioned

Ordered by what it costs when it fails.

| Shared object | Scope | Partitionable? | Answer | Cost |
|---|---|---|---|---|
| **The trajectory log's size** | per organisation | **not the right question** | 76.7% of it is `recall.omitted`. Store a count and a digest, not the list. Log drops ~40 MB → ~9 MB, quadratic growth dies, the contention window mostly closes | **one function** |
| `~/.cursor/cli-config.json` | **per machine** | No — third-party exclusivity | The lock guarding it is at `ROOT/.harness/cursor-agent.lock`. Two organisations in two trees take **two different locks over one file** and the exclusion evaporates. Move it beside the resource; model as `capacity=1` | one path |
| provider quota | **per account** | No — a spent token cannot be reclaimed | `headroom.json` is a per-repository snapshot of a per-account quota; N organisations each believe they hold the whole pool. Move it machine-global, one writer | one path |
| `sys.path` / the installed `consilient` | **per interpreter** | Yes | [measured, `cli.py:43-50`, the code's own words] one interpreter-global editable install already made `consil doctor` report *another tree's* Gate A1 as PASS while this tree reported FAIL. At N organisations that is org A's uncommitted edits executing org B's checks. One venv per organisation; `_foreign_tree` becomes fatal, not loud | **the gap no allowlist covers** |
| the git **common dir** | per repository | Yes, but not by the check that was proposed | [measured] 117 worktrees on one common dir. Two organisations on two worktrees have disjoint `workspace_root` prefixes and still share `.git/config`, `.git/objects`, `.git/refs` and the branch namespace. The WSL agent that wrote `core.worktree` and broke every git command, three times in an hour, was in exactly that topology. **Compare `git rev-parse --git-common-dir`, not `workspace_root`** | one subprocess call |
| `.git/config` (repository **and** global) | per repository / per user | Containment, not policy | Env scrubbing is policy over a file the child can simply open. Give each worktree its own `GIT_CONFIG_GLOBAL`, use the `isolated_git_env`/`full_clone` forms `dispatch.py:312` already implements for arms that have done it, **and digest both configs across a dispatch** | disk + clone time |
| `live_dispatchers()` | **already machine-wide** | Yes | [measured, `build_driver.py:254`] it matches every `python.exe` on the machine whose command line contains `dispatch.py` — no cwd, no org, no workspace filter. Org A saturating makes org B dispatch nothing and record no queue, no lease, no refusal. Count `state["in_flight"]` — a fact the organisation wrote about itself | ~5 lines, and it **deletes** a verify-by-process-identity site |
| the git index | per repository | **Yes — already done** | worktree per unit, F-03's fix | zero |
| machine RAM / process table | per machine | Partially | 4 `MemoryError` recorded. Per-org and machine-wide live-unit caps | ~20 lines |
| **disk** | per machine | No | [measured] 292 `state.db.stale-*` files, **3.04 GB**, beside a live database, one more per A2 run, never deleted. A full volume is the most perfectly cross-organisational failure available, and **no bulkhead in this design is sized against disk** — they are all sized against slots | 4 lines: keep the newest three |
| the escalation queue | per machine | No, deliberately | One queue, one budget: **3 per rolling 24 h across all organisations.** A budget that scales with N is not a budget | small |
| **the principal's attention** | per person | No | §6 and §10 |

**Two refusals, both because the fix would weaken a check.**

- **Do not raise `_READ_RETRIES` from 6.** Refusing rather than returning a partial trajectory is
  correct fail-closed behaviour. Widening a check's acceptance region to make something pass is
  the standing prohibition.
- **Do not suffix-read for the fencing epoch.** `_next_fencing_epoch` deliberately includes
  expired claims to keep the epoch monotone; a suffix read lets it go backwards, weakening the
  fencing that exists to stop the T01 cannibalisation.

**[asserted] And do not move the trajectory to SQLite yet.** It is a real option — WAL mode gives
concurrent readers with one writer, a `BEFORE UPDATE … RAISE(ABORT)` trigger is a *stronger*
append-only guarantee than a text file any process can truncate, and it would delete the
hand-rolled fsync/rollback path. But it is a migration of the product's own evidence artefact, it
is ADR-territory, and the one-function fix above takes the file to ~9 MB and kills the growth
term. **Take rung 1. SQLite is the recorded upgrade path if the log grows again after that.**

**The one genuinely multi-organisation resource bug worth naming as such:** the cursor lock and
the headroom snapshot are anchored to `ROOT`. Neither *degrades* under N organisations. Both
become **unsound the instant a second one exists.**

---

## 5. Supervision, and what supervises the supervisor

### 5.1 The counters, which have never bound

**[algebra] The attempt cap is structurally unreachable.** Three refund paths — expired leash,
artefact silence, and every crash — refund on exactly the failure classes this system suffers.
The cap therefore counts the failures the system does not have, which is why 3,108 crashes
coexist with `max(attempts) == 2` against a cap of 3. [cited] OTP's `supervisor` counts
**restarts**, not classified failures, in a sliding window held across all children, and exceeding
`intensity` per `period` terminates every child and then itself; Kubernetes bounds a Job at
`backoffLimit` (default 6) and resets container backoff after 10 minutes of healthy running. This
driver has neither a window nor a decay.

Three changes, all small, all worth doing at N = 1:

1. **A second, un-refundable `total_restarts`, with a sliding window.** 6 restarts per 10 minutes
   across the whole driver → stop dispatching, write `quarantined`, escalate **once**. Under that
   rule today's fault stops the driver at crash 7, not 3,108. Enforcement per the ratchet: a test
   asserting `total_restarts` is monotonic and that no code path decrements it.
2. **A real `quarantined` state.** Today the 3-identical-deaths branch prints and reclamation
   undoes it on the next tick. supervisord's FATAL and k8s' Failed Job condition are deliberately
   loud terminal states; a print statement in a log nobody reads is not one.
3. **A cap on `review_attempts`**, which has none and stands at 27.

**Machine-wide intensity keyed on error signature is the second — and only other — genuinely
multi-organisation mechanism.** A shared-resource fault presents as N organisations each
*slightly* unhealthy, every per-organisation counter comfortably under its bound, while the
machine burns. That is precisely the shape of 2,742 crashes across 81 units, one level up.
`error_tracking.stable_identity(component, error_type, error_code)` already exists and
deliberately excludes the unit id — reuse it unchanged.

**[asserted] But do not let that key stop anything.** The adversarial pass is right: the signature
space is order tens of buckets, it excludes the organisation by design, and the organisation that
fails *fastest* would set the counter and quarantine a slower, more expensive one. So: **the
signature key escalates once, naming the contributing organisations; stopping stays with the
per-organisation counter,** which is the only one carrying the attribution that would justify it.
The escalation record must carry the contributing `org_id` set and is refused at construction on
an empty set.

### 5.2 One scheduled task per organisation

`.harness/build_loop.py` is genuinely crash-only and it is the best-engineered thing in the
harness: a Windows scheduled task firing every few minutes plus an exclusive lock, so a dead loop
is replaced within one interval and a live one makes the new invocation exit 0. Its docstring —
*"the restart path is the ONLY path, so it is exercised constantly and cannot rot"* — is earned;
it survived both measured loop deaths, including the one where the process ended with an empty
stderr and the per-tick handler never fired. **Generalise it verbatim: one task per organisation,
one `loop.lock` per organisation. Never one loop iterating organisations**, which reintroduces the
shared failure domain this whole exercise exists to remove.

### 5.3 What supervises the supervisor, honestly

**Nothing needs to, for the regress — and that argument is sound.** A scheduled task is a
*periodic re-creation*, not a watcher, so there is no long-lived process to die silently and no
turtle below it. The bottom turtle is Windows Task Scheduler and this document says so.

**But the regress was never the exposure. Availability was, and it has three failure modes that
produce no artefact:**

1. The **registration** is machine-global and unversioned. `schtasks /TN ConsilientBuildLoop` is
   one flat namespace; any tidy-up, any re-run of the setup line (which ends `/F`), any
   `schtasks /Delete /TN Consilient*` silently removes another organisation's supervisor.
2. Task Scheduler's own defaults are silent: `DisallowStartIfOnBatteries` and
   `StopIfGoingOnBatteries` are **on**, `WakeToRun` is **off**. Unplugging a laptop stops every
   organisation's supervisor at once, and nothing distinguishes that from a healthy idle.
3. Running while logged off requires stored credentials — which is a secret on the machine, and
   the standing rule is that a capability needing one is not built.

**One mechanism covers all three, and it is peer observation rather than a new watcher.** Each
loop writes `status.json.last_tick_at`. Each organisation's tick reads *every other registered
organisation's* `last_tick_at`, and when one exceeds three intervals it refuses to dispatch and
escalates once naming that organisation. No new process, no regress, and the fact is one the
subject wrote about itself rather than one an observer inferred. Plus: capture `schtasks /Query
/XML` at registration as an artefact and assert the two battery flags are false. ~15 lines, and
it is the only proposal on the table that catches deletion of the registration — which nothing
currently does.

**At N = 1 this reduces to one line**: the loop writes `last_tick_at`, and the human-facing status
surface leads with "oldest tick M minutes ago". That is worth having now.

---

## 6. The orchestrator is a check, and its β is the product

**[asserted] An orchestrator that marks a unit `done` is a check that accepts work.** Its β is the
rate at which it accepts a bad unit. **Gate B2 — "the critic tier's own β is measured, with an
interval" — has been open since the beginning, and this is the only section of this document that
is the product rather than its plumbing.** It is also the section that is completely unaffected by
whether there is one organisation or fifty.

**The estimand:** β_orch = P(the orchestrator accepted the unit | the unit is bad).

**The sampling condition, which is the whole thing.** The sample must be drawn **uniformly at
random from units the orchestrator accepted** — never from units something else flagged.
`beta.py`'s own docstring is explicit: if artefacts reach a human only when the checks already
accepted them, every rejected row has `verifier_accept=True` and β is 1 by construction rather
than by measurement. `MIN_REJECTIONS = 30` binds, and it is **thirty rejections**, not thirty
samples.

**Three sources of ground truth, ranked, and only one is the verdict.**

1. **The principal's verdict on the diff.** Authoritative under V0-28, whose guard is registered
   and mutation-tested. A genuinely different class: a judgement over fitness for a purpose the
   tests do not encode, not a second reading of the same tests. Cost: reviewer-minutes, the
   binding constraint, which does not scale with N.
2. **Guard-mutation survival on the unit's own diff.** A different class — it asks whether the
   unit's *own* guards carry information, which no accept-time check asks, and it already
   recovered what a hand review found (19 units reviewed cross-family, **0 sound**, 14 carrying a
   guard that could be deleted with the suite still green). It is ground truth on a strict subset
   only. **Use it as a screen that makes the human sample affordable. It may never supply the
   verdict.**
3. **Post-hoc repair** — the unit's lines reverted, rewritten or repaired within N days by work
   that is not the unit itself; cheap once every commit carries a `Consilient-Work-Id:` trailer.
   Genuinely different class: the artefact's *future behaviour*, not a second reading at accept
   time. Two honest defects: it is **censored** (a bad unit nobody touches reads as good) and
   confounded by ordinary churn, so it is a **lower bound on β, not β**. `beta.py` already carries
   the estimand kind for exactly this shape
   (`repository_consequence_false_shipment_cohort_lower_bound`), so the meter is built and has
   received zero rows.

**The Whewell structure:** (1) is the verdict; (3) is a continuous lower bound from an altogether
different class of facts, and **its coincidence with (1) is the test** — an induction from the
principal's judgement jumping together with an induction from what the repository later did to
the code; (2) reduces the reading. This is the right project to solve it in, because the
orchestrator is a check and measuring checks is the whole subject.

**[asserted] The multi-organisation β claim, corrected and downgraded.** An earlier draft
pre-registered *cross-organisation β variance* as the justification for the whole model. **It is
refuted by that draft's own definition of an organisation.** Five organisations sharing one
`dispatch.py`, one `build_driver.py`, one `instructions.py` and one `recall.py` are not
independent draws — they share the orchestrator under test, and a common defect (such as the
one in §2.0) appears in all five identically. What supplies a different class is **a different
project**: a different artefact population, a different suite, different stakeholders. That is
obtainable **sequentially**, and it is what Gate B actually asks. So:

- **The pre-registered claim is cross-*project* β variance**, not cross-organisation.
- **The stopping rule stands:** if β does not differ across independent projects beyond its
  confidence interval, the structure has added no class of facts and must be **reported as scale,
  not architecture.**
- **The admissibility condition stands and is enforceable:** a β sample drawn while that project's
  organisation was starved by the scheduler is **inadmissible**, because the sample is then
  conditioned on the scheduler. `intent.starved` already emits the window; `status.json` records
  it; `beta.py` gains one refusal in the shape of the one it already has. ~10 lines.
- **And note what §4 found:** `live_dispatchers()` starves org B without recording a queue, a
  lease or a refusal, so `intent.starved` never fires for it and the admissibility check silently
  passes on a contaminated sample. **Fixing that counter is a correctness prerequisite for this
  measurement**, not a throughput nicety.

**[algebra] Parallelism makes β harder to measure, not easier.** `MIN_REJECTIONS = 30` × N
projects is 30N personal rejections against a denominator of one human. The bottleneck is already
visible at N = 1: `force_done` 23 > `verified` 22 > `done` 3.

---

## 7. What this does not solve

**Stated in the words it must appear in.**

- **None of §§2–5 touches β.** OTP, Kubernetes, crash-only supervision and durable execution will
  faithfully, promptly and idempotently restart an inverted secret guard. **Better supervision
  makes a stale-but-green unit *less* visible by putting a green light beside it.** This design
  buys **liveness and isolation, not correctness.** §6 is the only part on the other axis.
- **On detection latency this system beats no incumbent and must not claim to.** Kubernetes
  surfaces a crash loop within one probe period; OTP escalates at intensity 1 per 5 s; a
  Chubby-style lease releases in one TTL. Against 3,108 crashes accrued with nobody notified, the
  measured detection channel here is still human.
- **Two witnesses per check is a floor, not a measurement.** It removes the two ways a check
  carries zero information — α=1 and β=1. It does not measure β. Presenting witness coverage as
  "our gates' β" would be the false superlative in a new place.
- **No published fairness bound covers this quota case.** DRF, Kueue, Borg and VTC all assume
  preemption and an authoritative meter; a spent token cannot be reclaimed and **4 of 5 pools
  report no meter at all**. VTC's *metric* (max service difference between two backlogged
  parties) is usable; its proven 2× guarantee is not, and must not be cited as though it applies.
- **[cited] The bar record is out of date and this design beats nothing on fleet management.**
  `docs/10-research/bar-loop-engineering-2026-08-24.md` names a 10,635-star incumbent;
  `stablyai/orca` was reported at 52,758 stars, MIT, pushed the same day, tagline *"the ADE for
  working with a fleet of parallel agents… Run any coding agent with your own subscription"* —
  the principal's request nearly verbatim. **I did not re-fetch the GitHub API this session, so
  that row is [cited] on another agent's measurement and needs a re-check date recorded.** What
  this repository does that it does not: refuse an exhausted pool, refuse an `unknown` headroom
  reading, never shed to on-demand spend, and **measure the verifier rather than check that one
  exists.** Nothing more.

**Adversarial findings left open, each with why.**

| Finding | Status |
|---|---|
| **One interpreter, one installed `consilient`** — org A's uncommitted edits execute org B's checks, including the guard functions the registry protects | **Open, and it is the most dangerous unfixed item.** Not in the unit list because it requires a per-org venv and a fatal `_foreign_tree`, and there is one organisation today. **Do not create a second organisation before closing it.** |
| **The escrow ledger reproduces the fault it was meant to avoid** — `_write_validated` reads and JSON-validates the *whole file* under the exclusive lock on every append, so a machine-wide ledger is O(dispatches × orgs) per append; and `budget.state` is refused unless the filename is `<date>.jsonl`, so the ledger as specified cannot be written by the writer specified | **Open by deferral.** The ledger is not built. When it is: date-partition it (`<pool>/<date>.jsonl`), which bounds append cost *and* satisfies the filename rule already in the writer |
| **`_budget_transaction` uses an advisory lock *file*** (`touch(exist_ok=False)` / `unlink()` in `finally`), 480 lines below a comment boasting that kernel locks are released on death "so a killed writer cannot strand the log the way a lock file does". One `kill -9` or one `MemoryError` (4 measured) strands every budget append permanently | **Closed by a unit** — replace with the `_lock_file` the same module already has. Three lines, and it is a deletion |
| **The no-on-demand-spend rule is a source grep over one repository**; the control lives in the principal's account, and 4 of 5 pools have no meter to notice a breach | **Open.** The honest fix is to probe the account setting and record it as a `budget.state` event, refusing admission on anything but `disabled`. The grep stays as the ratchet; it was never the check. Not scheduled because it needs a probe that does not exist |
| **Leak gates cannot see machine-global paths.** `~/.consilient/escalations/` is outside every repository by design, its records carry free prose about work in trees the boundary forbids publishing, and no `git ls-files`-based detector covers a path no repository tracks | **Open by deferral** — the queue is not built. When it is: scan those roots and refuse escalation *construction* on a body that fails the same detector |
| **The guard registry is repo-relative**, and two divergent tracked copies of `src/consilient/` already make "the module" ambiguous inside one organisation. In another project it resolves to nothing and passes vacuously at 0 of 0, rising monotonically while measuring nothing | **Half-closed.** The untracking unit removes the ambiguity; **the checker must additionally fail when it resolves zero modules** — a check that finds nothing to check must not pass — and that is folded into the witness unit |
| **Claims do not see across organisations.** `open_claim(log, …)` and `claim_ready_work(log, …)` are scoped to one log directory, so under per-organisation logs two organisations cannot see each other's claims at all — on the shared git common dir, a shared library checkout, or `~/.consilient` itself. `canonical_path` makes the comparison correct; it does not make the comparison happen | **Open, and it corrects an earlier claim.** The "claim layer needs no change" line in the previous draft was wrong: the isolation comes from an assumption that trees are disjoint, enforced by a test rather than by the claim layer. That is a chokepoint without an enforcement rule, in the place the draft believed it had one free |
| **`consil`'s defaults are relative** (`Path(".harness/log")`, `Path(".harness/state.db")`) and repository identity is a hard-coded six-name frozenset | **Open.** The lazy fix is a deletion — refuse when neither `--log` nor an explicit org is given — but it changes every invocation in every runbook, so it needs the principal's word |

---

## 8. Sequencing, by risk reduced per unit of the principal's attention

Marked **[N=1]** where the step is worth doing even if there is never a second organisation.

| # | Step | Why it is here | Diff size | N=1? |
|---|---|---|---|---|
| 1 | **Stop writing `recall.omitted` into the trajectory** — store a count and a digest | 76.7% of the contended file; kills the quadratic term; 2,742 of 3,108 crashes are downstream of it | one function + a test | **[N=1]** |
| 2 | **Untrack mutable harness state** and the two tracked `src/consilient/` copies | A `git checkout` can restore the file that decides what is dispatched; it already lost a queued unit once. Also disambiguates the guard registry | `git rm --cached`, 5 gitignore lines, one test | **[N=1]** |
| 3 | **Driver counters and probes** — cap `review_attempts`, add un-refundable `total_restarts` with a 10-minute window, a real `quarantined` state, and read live dispatch from own `in_flight` rather than the machine process table | 27 uncapped review attempts on the product's own verification path; a cap that has never bound; a counter that is already cross-organisational and read as per-organisation | ~40 lines + tests | **[N=1]** |
| 4 | **`_budget_transaction` → the kernel lock the module already has** | One `kill -9` strands every budget append permanently, machine-wide | 3 lines, a deletion | **[N=1]** |
| 5 | **Cap `state.db.stale-*` at the newest three** | 3.04 GB, one more per A2 run, never reaped; disk is the one resource with no bulkhead | 4 lines | **[N=1]** |
| 6 | **Witness registry + `check_witnesses.py`** — every registered check declares one artefact it must accept and one it must refuse, both from normal operating state; coverage is a ratchet; the checker fails when it resolves nothing | The largest root cause and the only one on the β axis. 10 of 21 gate scripts already have the witnesses hand-written | new checker + registry | **[N=1]** |
| 7 | **Promote the three hook-only checkers into CI** | Two of three are leak gates; `--no-verify` bypasses both, and `core.hooksPath` must be set for either to run | workflow edit | **[N=1]** |
| 8 | **Anchor the cursor lock and headroom to the machine** | Both are **unsound the instant a second organisation exists**, not merely degraded | 2 path constants + a test | **N>1** — but it is the cheapest thing on this list |
| 9 | **`work_id` minted by the initiator**; commit trailer; delete both content joins; lint them | Closes the identity class (nine of twelve conflicts) and removes the mtime/brief inference from reclamation. Also the prerequisite for §6's post-hoc-repair lower bound | hours | **[N=1]** |

**Then, in order, and each independently useful:** wire `record_intent`/`starvation()` into the
tick (built, tested, zero callers — the only detector of *work that stopped being selected*);
`agent.started`/`heartbeat`/`finished` plus `Liveness` as a three-member type (`mypy --strict` is
already the enforcement); `test_projection_is_disposable`, then demote `state.json`; the
peer-observation `last_tick_at` check; per-worktree `GIT_CONFIG_GLOBAL` plus a config digest
across each dispatch; the obligation row; and the witness-coverage retrofit against a budget,
ordered by blast radius (`consil doctor` conditions, then the leak gates, then the product
invariants).

**Explicitly not built:** no `Organisation` class; no registry service; no `org_id` event field;
no new event schema version; no hosted durable-execution engine (Temporal, Restate and DBOS each
demand a service, a database, determinism enforcement and workflow versioning to buy exactly-once
resumption for one Python orchestrator on one Windows machine, and would put a server on the
product path of a package with `dependencies = []`); no replay-determinism enforcement (one
driver, one author, and the failure has not been measured once); no PodDisruptionBudget analogue;
no escalation precision feedback loop **at any N** — a negative-feedback control loop on the
notification path, with an unmeasured threshold, whose failure mode is that nobody finds out.

---

## 9. Acceptance tests that can actually be run

Each is runnable today and fails on the defect it names.

1. **Trajectory composition.** After step 1, no single event kind exceeds 20% of a day's
   trajectory bytes, and mean bytes-per-event does not exceed the previous day's by more than
   1.5×. Runnable now as a script over `.harness/log/*.jsonl`; today it fails at 76.7%.
2. **Receipt replay survives the shrink.** `instructions.verify` still reports the recall layer
   as matching for an event recorded before *and* after the change. This is the check that the
   audit property was preserved rather than traded away.
3. **`git ls-files .harness` returns no mutable state** — no `driver-state.json`, no
   `plan-units.json`, no `*.lock`, no `build-loop.*`, no nested `src/consilient/`. One test,
   fails today.
4. **`total_restarts` is monotonic.** A property test over the driver's state transitions
   asserting no code path decrements it, and that crossing the window writes `quarantined` and
   emits exactly one escalation.
5. **`review_attempts` is bounded.** Dispatching reviews for one unit past the cap refuses rather
   than dispatching. Fails today at 27.
6. **A stranded budget lock does not permanently refuse.** Create the lock file, kill the holder,
   assert the next append succeeds. Fails today.
7. **Witness pairs.** For every entry in the registry: the accepting witness exits 0 and the
   refusing witness exits non-zero. And: `check_witnesses.py` **fails when it resolves zero
   entries**, proved by pointing it at an empty registry.
8. **Guard mutation still bites.** `check_guard_mutation.py --self-test` continues to pass, with
   its synthetic surviving guard still *reported*. Coverage is recorded as a number that may only
   rise; the floor starts at whatever step 6 achieves.
9. **Two organisations share no git common dir.** For any two registered organisation records,
   `git rev-parse --git-common-dir` (resolved, casefolded) differs, and no `workspace_root` names
   another organisation's home. Runnable against a two-entry fixture before any second
   organisation exists.
10. **The starvation admissibility check has something to refuse.** Given a synthetic log with an
    `intent.starved` window overlapping a β sample window, `consil beta` returns
    `insufficient_data` rather than a number. This is the accepting/refusing witness pair for the
    one check that protects the product's headline measurement.

---

## 10. Open questions for the principal

Four, each answerable in a sentence.

1. **The escalation ratchets point opposite ways and no fact settles which wins.** My proposal:
   below the 3-per-24 h budget the silence ratchet wins (raise anything meeting the test); at
   budget the friction ratchet wins (rank and drop), and every drop is recorded so a suppressed
   true escalation stays legible. **Yes, or a different rule?**
2. **Step 6 will turn CI red on gates that have shipped for weeks** — K01 refuses
   unconditionally, Gate A3's window can only be satisfied by breaking capture, and the
   review-receipt condition needs `live_dispatchers() == 0`. The standing rule says those reds are
   repaired, never exempted. **Do I land the witness registry knowing the build goes red until
   those three are fixed, or stage it behind their repairs?**
3. **`consil`'s relative defaults (`.harness/log`, `.harness/state.db`) already caused two
   incidents in one night and are the mechanism by which one organisation projects into another's
   database.** The lazy fix is to delete them and refuse when no log is named, which changes every
   invocation in every runbook. **Delete the defaults?**
4. **One interpreter serving N organisations means one editable install decides whose code runs
   every check** — measured once already, reporting another tree's Gate A1 as PASS. **Is a second
   organisation off the table until each has its own venv, or do you want the venv work scheduled
   ahead of the resilience list?**

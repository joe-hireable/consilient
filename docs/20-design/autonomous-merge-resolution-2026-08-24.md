# Autonomous merge conflict resolution

**Author:** CTO worktree · **Date:** 24 August 2026 · **HEAD at measurement:** `71a8433`
**Status:** design. Every number carries a provenance tag. Measurements marked `[measured]` were
run by me today in this worktree; where I inherited a claim from the evidence packs I say so and
say whether I re-ran it. Where my measurements contradict the packs, I say that too.

---

## 1. Thesis

**Do not build a resolver. Run the checks you already own, at the place the merge happens, and stop
two agents designing the same subsystem against a base that has moved.** Of the seven units
escalated as unmergeable today, two are not conflicts — one is already in the driver's own
`force_done` list and still on the escalation banner, and one has 100% of its added lines already in
HEAD under a rewritten subject. The five that remain produce 42 conflict hunks of which at most 26%
are safe to union, 57% are two rewrites of the same non-empty region, and **28 of the 42 come from
two units that re-designed a subsystem HEAD had already changed underneath them.** Meanwhile
`ruff check .` and `mypy --strict src/consilient` — both already wired into
`.github/workflows/invariants.yml` — are **red on HEAD right now, with 49 errors whose signature is
exactly the bad-merge family this design was commissioned to catch**: a 313-line block duplicated
verbatim in `src/consilient/harness.py`, a stray import appended past the end of a test file, three
duplicated test functions, and two uses of a name whose definition a merge dropped. The gate is not
missing. It is installed, correct, red, and read by nobody in the merge path. So: classify on
content (a smaller diff than the code it replaces), gate the merged tree with the tools already
installed, add the two checks those tools genuinely lack (~40 lines), repair what is already in the
tree, and cut the conflict supply at source by rebasing worktrees every tick and refusing to start
two units whose titles name the same subsystem. Narrowing claims is **not** on that list: the file
claimed by 39 units produced zero conflict hunks, and the file claimed by six produced twenty-two.

---

## 2. What conflicts here actually are

### 2.1 The population, with denominators

All figures `[measured]` on 24 August 2026 at HEAD `71a8433`, from `.harness/driver-state.json`, the
live worktrees in `.harness/unit-worktrees/`, and `git`. Scripts left in the scratchpad at
`C:/Users/jpbpr/AppData/Local/Temp/claude/C--Users-jpbpr/4119b9a5-e07e-43de-bc2f-e873fbd124d2/scratchpad/`.

| Quantity | Value |
|---|---|
| Units in the plan | 132 |
| Units built | 72 |
| Units in `state["conflicts"]` | **7** — `AC AI K01 M04 N03 N04 T02` |
| Of those, already in `state["force_done"]` | **1** (`K01`) |
| Retired by `git cherry HEAD <worktree-head>` (patch identity) | **0 of 7** |
| Retired by the driver's own subject-grep | **0 of 7** |
| Retired by text coverage of added lines against HEAD | **2 of 7** (`T02` 100%, `K01` 98.7%) |
| Genuine, with real residual | **5** — `AC` 54.9%, `N03` 47.3%, `N04` 46.3%, `AI` 24.0%, `M04` 14.9% coverage |

**The task brief says fourteen conflicts stand today. Seven do.** The count fell while this work was
in progress, and the fall matters more than the number: *the cheap rungs have already done their
work.* `git cherry` retired six of fourteen this morning and retires **none** of the seven that
remain. The conflict population is adversely selected over time — every classifier pass removes the
easy cases and concentrates the hard ones. Any plan that budgets by today's ratio and expects it to
hold is wrong. `[measured]`

This also revises Evidence 1's headline. Its `git cherry` recommendation is correct and I reproduced
its result, but on the current queue **patch identity retires nothing**, because a unit whose work
landed by hand-merge onto a moved HEAD no longer has the same patch-id. What retires work here is
**content coverage** — asking, for each added non-blank line, whether it is present in HEAD's copy
of the same file. That predicate retires `T02` (1,335 added lines, 0 absent) and `K01` (77 added, 1
absent) where patch-id and subject-grep both fail. `[measured]`

### 2.2 The hunk distribution, and why "overwhelmingly additive" is false

42 conflict hunks across the 7 units, extracted from
`git -c merge.conflictStyle=zdiff3 merge-tree --write-tree --merge-base=<sha>^ HEAD <sha>` — the
merge base of the operation the driver actually performs, a cherry-pick, not the one it currently
predicts. `[measured]`

| Class | Definition | Count | Share |
|---|---|---:|---:|
| import-union | every line on all three sides is an import; base is a name-subset of both | 3 | 7% |
| additive by shape | base region empty; one or both sides add | 11 | 26% |
| **semantic** | base non-empty and both sides rewrote it | **24** | **57%** |
| delete-vs-modify | one side's region empty, base non-empty | 4 | 10% |
| whitespace/comment-only | — | 0 | 0% |

**Union is safe for at most 14 of 42 (33%), and the true figure is lower**, because three of the
eleven additive-by-shape hunks are contradictions wearing an additive costume:

- `N03` h2/h3 in `coordination.py`: base empty, ours adds `fencing_epoch: int | None = None` and the
  call site `fencing_epoch=fencing_epoch`, theirs adds `epoch: int` and `epoch=epoch_raw`. Two names
  for one concept. A union yields a dataclass carrying both fields and a call passing both.
- `M04` h2 in `projection.py`: base empty, ours adds `    _apply_native_work_items(conn, events)` at
  four-space indent, theirs adds `        elif event.kind == CAPABILITY_VERSIONED_KIND:` at eight. A
  union interleaves a bare call and an `elif` at mismatched depth.

**So "the base region is empty on both sides" is a syntactic fact, not a safety property.** This is
the most important correction to Evidence 1, which reads additive shape as licence to union; it is
also sharper than Evidence 2, which measured 59% union-safe on an earlier population. Today it is
26% at best. `[measured]`

`M04` h1 in `projection.py` is the T01 SQL specimen recurring live: base empty, ours adds
`CREATE TABLE native_work_items`, theirs adds `CREATE TABLE capability_versions`, both inside one
`SCHEMA` string literal. Union is probably right and it is exactly where T01 was cut mid-statement.

### 2.3 The cause is co-churn, not staleness and not claim width

For each conflicted unit I counted the commits that landed to *the files that unit touched*, between
its branch base and HEAD. `[measured]`

| Unit | Hours between base and first own commit | Commits to touched files since base | Hunks |
|---|---:|---:|---:|
| AI | 4.4 | 17 | 22 |
| N03 | 21.0 | 4 | 6 |
| AC | 15.4 | 9 | 4 |
| M04 | 1.4 | 7 | 3 |
| K01 | 13.1 | 10 | 3 |
| N04 | 1.5 | 2 | 3 |
| T02 | 3.5 | 3 | 1 |

**Pearson r(commits to touched files, hunks) = 0.81. Pearson r(drift in hours, hunks) = −0.08.**
n = 7, a chosen statistic on a small chosen sample, so treat the coefficient as a direction and not
a number. `[measured]` for the values, `[asserted]` for the causal reading. The experiment that
upgrades it: compute the same pair over the 70 historical `(unit, sha)` conflict records recoverable
from `.harness/*.log`.

Wall-clock age does not predict conflict. **How much other work landed in the same files does.**

And claim count predicts nothing at all:

| File | Units claiming it | Commits since 23 Aug | Conflict hunks today |
|---|---:|---:|---:|
| `src/consilient/events.py` | **39** | 5 | **0** |
| `src/consilient/projection.py` | 33 | 6 | 4 |
| `scripts/dispatch.py` | 31 | 11 | 4 |
| `src/consilient/coordination.py` | 11 | 3 | 7 |
| **`.harness/build_driver.py`** | **6** | **21** | **22** |

`[measured]` The most-claimed file in the repository produced zero hunks. The file claimed by six
produced more than half of all of them. **Evidence 1's claim-width chokepoint is refuted by this
tree, and Evidence 2's "duplicated semantics" reading is confirmed and extended:** there are two
generators, not one, and they are commit rate in the drift window (`build_driver.py`, 22 hunks) and
two units designing one subsystem (`coordination.py`: `N03` "short fencing-token leases replacing
the one-hour claim" against `T02` "atomic readiness, claim and fencing", 7 hunks). Together those
two units account for **28 of 42 hunks — 67% of all conflict volume in the queue.**

Over-declaration is still worth fixing — claims are locks, and 44 units declaring eight or more
paths serialises the queue for no reason. That is a **throughput** cost. It is not why merges fail.

### 2.4 The driver never rebases a worktree until after it has already conflicted

`rebase_worktree` is defined at `.harness/build_driver.py:514` and called from **exactly one place**
— line 918, inside the conflict branch of `merge_unit_worktree`, and only when the unit is
quiescent. `[measured: grep]` A unit is therefore never rebased before its build, nor during it, nor
on any tick while it sits finished and unmerged. `N03` wrote its commit at 16:43 on 24 August against
a base from 19:40 on 23 August — 160 commits and 21 hours behind. `[measured]`

That is not a merge problem. **A unit branched 160 commits back was asked to write a patch against a
repository that no longer exists.** The resolver is being handed a problem the dispatcher created.

---

## 3. The three components, each with the check that makes it real

### 3.1 Component 1 — classify by content, and re-earn every escalation

**The bar.** `git cherry` / `git patch-id` is the built-in, content-addressed primitive for "is this
patch already upstream", and it appears nowhere in `.harness/build_driver.py` `[measured: grep]`.
`git merge-tree --write-tree` predicts a merge without touching the worktree and the driver already
uses it correctly at line 1474. GitHub's merge queue *removes* conflicting PRs rather than
classifying them `[cited, Evidence 1]`. Merge-Bench, ConflictBench and ConGra grade conflict
difficulty and none classifies "already landed under a different sha" `[cited, Evidence 1]`.
Searched and found none; stated as a search result, not a superlative.

**What is wrong today.** Two defects, both live:

1. The already-landed detector at line 1449 greps commit **subjects**:
   `git log --format=%H --fixed-strings --grep <subject> HEAD`. Over the last 646 commits there are
   590 distinct subjects and 14 reused; **9 of the top 12 reused subjects carry different patch
   content**, and one subject spans 24 commits. `[measured, re-run today]` A subject hit retires the
   unit outright. That is a β event inside the driver's own classifier.
2. `state["conflicts"][uid]` is written on merge failure and cleared only by the re-test loop, never
   by retirement. `K01` is in `force_done` and on the escalation banner simultaneously. `[measured]`

**The change.** Replace the subject grep with content coverage — for each added non-blank line of the
unit's own commits, is it present in HEAD's copy of the same file? Retire at ≥99% coverage with at
least 20 added lines; below that, fall through and stay escalated. Keep `git cherry` as the cheap
first rung — it costs one command and it retired six units this morning — but **never let it retire
alone**: patch-id normalises whitespace, and in Python whitespace is the language, so a commit that
moves a statement into a loop carries the same patch-id as one that does not `[cited, adversarial
pass; the mechanism is checkable from `git patch-id` semantics]`. Require that `git cherry` says
upstream **and** `git diff <worktree-head> HEAD -- <touched>` is empty. And clear the conflict entry
wherever a unit is retired, not only in the re-test loop.

> **Enforcement — the chokepoint rule.** `tests/test_build_driver.py` gains two tests in the same
> commit. **R1:** construct two commits with an identical subject and different content; assert the
> classifier leaves the second escalated. **R2:** assert that retiring a unit removes it from
> `state["conflicts"]` — a conflict entry is an assertion the driver re-earns each tick, not a fact
> it accumulates. Without R1 this regresses the first time someone finds the content scan slow.

**What it is worth today:** retires `T02` and `K01`, taking the banner from 7 to 5. `[measured]`

### 3.2 Component 2 — the acceptance gate, which mostly already exists

**The bar, and the finding that reorders this whole document.** `ruff check .` and
`mypy --strict src/consilient` both run in `.github/workflows/invariants.yml` (lines 36 and 39). Run
against HEAD today: `[measured]`

```
ruff check .                     ->  32 errors
mypy --strict src/consilient     ->  17 errors, all in src/consilient/harness.py
```

Their signature is the bad-merge family, entire:

- **`src/consilient/harness.py` contains a 313-line block twice, byte-identical** (`difflib` diff = 0
  lines), duplicating 17 module-level definitions — `GrammarConstraint`, `schema_digest`,
  `derive_grammar_constraint`, `grammar_accepts` and thirteen more. It landed because
  `feat(decoding): constrain generation from the declared schema` was committed **twice**
  (`9053411`, `81ee449`) **with two distinct patch-ids** — the double-build signature, landed twice.
  Because the halves are identical the behavioural harm today is nil; the harm is 313 lines of dead
  code, a file that silently diverges the moment anyone edits one copy, and the fact that **nothing
  in this repository noticed a module grow a verbatim duplicate.** `[measured]`
- `tests/test_recall_receipts.py` ends at line 438 with a stray `from typing import cast` **after the
  last test** — an import hunk unioned to the wrong end of the file. Its subject,
  `feat(recall): emit bounded recall receipts`, also appears twice with two patch-ids. `[measured]`
- `docs/10-research/experiments/exp43/test_exp43.py` has three duplicated test functions and **two
  uses of `LOCK` whose definition a merge dropped** (`F821 Undefined name`). That is silent work
  *loss* — the adversarial pass's finding #7 — sitting in the tree. `[measured]`

**So the acceptance gate is installed, correct, currently red, and not read by anything in the merge
path.** Building a new gate before running the existing one would be the second mistake in the same
family. The honest reading of the evidence packs' "ruff and mypy miss it" is narrower than they
stated: they miss the *variable-rebinding* shape (T01's `KINDS`), and they catch the
*definition-duplication* shape outright.

**The change, in three parts, cheapest first.**

1. **Run what exists, on the merged tree, on the files the cherry-pick touched.** `merge_unit_worktree`
   already computes `touched` at line 872. Run `ruff check <touched>` and
   `mypy --config-file mypy.ini <touched>`; on failure, revert the cherry-pick and re-escalate with
   the output attached. Zero new checks. This would have refused both live artefacts above.
2. **`mypy` must be invoked with `--config-file mypy.ini`, never bare `--strict`.** `warn_unreachable`
   lives in the ini, not in `--strict`. On my specimen, `mypy --strict` from a scratch directory
   reports `Success: no issues found`; the same file under `mypy.ini` reports
   `error: Statement is unreachable`. `[measured]` One flag separates catching T01's dead-code defect
   from missing it.
3. **Add exactly the two checks the existing stack lacks** (§4).

> **Enforcement.** The gate is a script, `.github/scripts/check_merge_acceptance.py`, modelled on the
> existing `.github/scripts/check_guard_mutation.py` — same `--self-test` discipline, stdlib only
> (`ast`, `sqlite3`, `subprocess`). It is called from `merge_unit_worktree` **and** exercised by
> `tests/test_merge_acceptance.py`, so CI runs it without editing a workflow file. A merge that fails
> the gate is **reverted, not logged**: `git cherry-pick --abort` or `git reset --hard` to the
> pre-merge sha, and the unit re-escalates.

### 3.3 Component 3 — cut the supply, which is where the leverage is

**The bar.** ConE (Microsoft, 234 repositories) is the deployed incumbent for conflict avoidance by
early warning: 775 notifications over 26,000 pull requests — **3%** — of which 71.48% were rated
useful, and its authors rejected the academic prediction literature outright because precision of
0.48–0.63 would produce too many false alarms to survive. `[cited, Evidence 1]` AgenticFlict measures
the closest population: agent PRs conflict at 27.67%, rising with change size. `[cited, Evidence 1]`
**The binding constraint: a warning that fires on more than a few percent of dispatches will be
ignored by the second tick.**

**Two changes, both derived from §2.3 and §2.4.**

1. **Rebase every unmerged, quiescent worktree onto HEAD every tick — not only after it has already
   conflicted.** The function exists; it is called from one place, in the failure path. Moving the
   call earlier converts a 160-commit replay into a handful of small ones, each against a tree that
   is nearly current. This is the direct countermeasure to r = 0.81 on co-churn. It must never run
   under a live dispatcher: rebasing rewrites the branch beneath the worker, which is why the
   existing quiescence test is kept unchanged.
2. **Refuse to make two units concurrently startable when their title tokens overlap and they share a
   claimed path.** Measured on this plan: over all 8,646 unit pairs, 1,906 share at least one claimed
   path. Ranking those by stop-worded token-Jaccard over `title + commit`, **`N03/T02` sits at rank
   10 of 1,906 (0.52%)**, sharing `{claim, coordination, fencing}` and two claimed paths — and both
   are escalated right now. `K01` appears in three of the top sixteen pairs (`K01/K02` #4, `AX/K01`
   #8, `AR/K01` #16) and is also escalated. A top-20 cut fires on 1.0% of claim-sharing pairs and
   0.23% of all pairs — an order of magnitude inside ConE's usability budget. `[measured]`

> **Enforcement.** `ready()` at `.harness/build_driver.py:1235` already gates dispatch on declared
> dependencies. Add: a unit is not startable while an undone unit with title-Jaccard above the
> threshold and a shared claimed path is in flight. **Serialise, do not warn** — the second unit then
> plans against a tree that already contains the first. The threshold is a knob and the physical
> world needs tuning: start at the top-20 cut, **log every firing**, and if it exceeds 5% of
> dispatches it is wrong and must be tightened, never tolerated.

**And what is deliberately not done: claim narrowing.** It would not have prevented one of today's
seven conflicts. `events.py`, claimed by 39 units, produced zero hunks. `[measured]`

---

## 4. The acceptance check against the T01 specimen

I rebuilt a 30-line specimen carrying three of T01's four documented artefacts — `KINDS` bound twice
at module level with the second omitting `STATE`, a `CREATE TABLE` cut mid-statement inside a
`SCHEMA` string, and a projection call stranded after a `return` — and ran this repository's own
toolchain against it. Specimen and prototypes at `…/scratchpad/t01/`. `[measured, all rows]`

| Check | Result on the specimen |
|---|---|
| `python -m py_compile` | **PARSES CLEANLY** |
| `ruff check` (repo config) | passes |
| `ruff check --isolated --select ALL` | 6 diagnostics — RET503, RET504, ARG001, SIM103, D103×2. **None names the double binding. None names the SQL.** |
| `mypy --strict`, no `mypy.ini` | **Success: no issues found** |
| `mypy --config-file mypy.ini` | `error: Statement is unreachable [unreachable]` |
| C1 prototype (12 lines of `ast`) | `KINDS: [10, 12]` |
| C3 prototype (15 lines, `sqlite3`) | `OperationalError: near "CREATE": syntax error` |

### 4.1 What the gate catches, failure mode by failure mode

| T01 failure | Caught by | **Not** caught by |
|---|---|---|
| **1. `CREATE TABLE` cut mid-statement** | **C3** — every string constant containing `CREATE TABLE` must survive `sqlite3.connect(":memory:").executescript(...)` | the parser (the SQL is a string literal), ruff at `--select ALL`, mypy under any config. Nothing in this repository executes string literals. |
| **2. Projection call stranded after `return`** | **`mypy --config-file mypy.ini`**, via `warn_unreachable` | `py_compile`; `mypy --strict` invoked without the ini; ruff under the repo config. `--select ALL` flags the function for RET503/RET504, but for the wrong reason, and neither rule is enabled here. |
| **3. Second `KINDS` frozenset shadowing the first, omitting `STATE`** | **C1** — no module-level name bound by `Assign`/`AnnAssign` more than once | ruff at `--select ALL` (pyflakes F811 covers imports, functions and classes, **not variable rebinding**), `mypy --config-file mypy.ini` (`no-redef` does not fire on same-typed reassignment), the parser, and the suite unless a test asserts a malformed `work_item.state` event is *refused*. **This is the fail-open one: a widened guard produces silence, not a failure.** |
| **4. Two branches removed as duplicates** | **nothing in this design, and I say so plainly.** Evidence 2 measured that a blind union *kept* both loops — the removal was a resolver judgement. Since §3 builds no resolver, the artefact cannot arise from this system today. A union-preservation check (C4) is specified in Evidence 2's design and is **deliberately deferred**: its false-alarm rate is unmeasured, one synthetic specimen is not a rate, and as specified it fires on every legitimate body rewrite. | — |

**C1, scoped to exactly the gap.** Because ruff's F811 and mypy's `no-redef` already cover duplicated
defs, classes and imports — proven live on `harness.py`, 4 and 17 errors respectively — C1 must cover
only module-level `Assign`/`AnnAssign` rebinding. Narrowed that far it is **12 lines**, and I
measured its precision on the real tree: **0 flags across 174 parsed files** in `src/`, `scripts/`,
`tests/` and `.harness/`, while still catching the specimen. `[measured]` The wider version I first
wrote flagged three files, two of which were genuine merge artefacts and one of which (`urllib`
imported three times as dotted submodules) was a bug in my own prototype. Narrow it, and the
false-alarm rate on this codebase is zero.

### 4.2 The two criteria that are disqualified, in code and not in prose

**"It parses" is disqualified.** The specimen compiles. `[measured]` Three of T01's four defects were
invisible to the parser.

**"The suite passes" is disqualified.** The `KINDS` defect fails a test only if some test asserts
that a malformed event is *refused*. And the live proof: `tests/test_capability_gaps.py` imports from
`consilient.harness` and passes, while that module has carried a 313-line verbatim duplicate through
an unknown number of green runs. `[measured]`

The gate must therefore be a distinct check that runs on the merged tree — never a reuse of
`suite_green()`.

---

## 5. The β of the resolver — and the circularity the adversarial pass found is not resolved

**There is no resolver in this design, so there is no resolver β to report.** Saying otherwise would
be the false superlative this project has already published once. What can be measured is the β of
the *merge acceptance gate*: the rate at which it accepts a merge the principal rejects.

**How it would be measured.** Per `.claude/skills/measuring-beta/SKILL.md`:

- `MIN_REJECTIONS = 30`. Fewer than 30 principal-authored rejections of gate-accepted merges and the
  honest output is `insufficient_data`. Five genuine conflicts today; this is weeks, not days. An
  underpowered β is worse than none, because it is quotable.
- **Never multiply the per-check rates.** EXP-47 measured joint survival at 33.82% against 26.86%
  predicted by independence, odds ratio 5.15 `[cited, repository]`. Per-check rates are diagnostics;
  the composite is the only routing input.
- **The sampling must not condition on the gate's own verdict.** If only gate-accepted merges reach
  the principal, β is 1 by construction. Sample from all attempted merges, gate-accepted and
  gate-rejected alike, and adjudicate blind to the verdict.
- **The principal authors the verdict** (V0-18). A model adjudicating a model's merge is echo
  arriving through the data layer, and the 2026 calibrated-judge paper's own judge accepted 4 of the
  5 structurally invalid resolutions it was asked to catch `[cited, Evidence 1]`.

**The different class of evidence, and this is the part that must not be fudged.** The gate's checks
are structural and executed facts about the merged tree — a schema that executes or does not, a
statement reachable or not, a name bound once or twice. They are not a second opinion about the diff.
That is genuinely a different class from the induction that produced the merge.
**Adjudication by reading is not.** The adversarial pass is right that a principal reading a
200-line merged diff performs the same induction as the agent that produced it, only more slowly —
and the `harness.py` duplication is the proof, since a 313-line verbatim repeat survived every human
glance it ever got. So the adjudication question must be behavioural: *"the merged tree answers X;
HEAD before answered Y; which is correct?"* — five seconds, executed output, a different class.

**Three things the adversarial pass raised that this design does not resolve. Stated plainly.**

1. **The β population is wrong and I have not fixed it.** The gate governs merges that had a
   conflict. Today that is 5 events against 72 clean landings — roughly 6% of merge traffic. A number
   computed on that stratum will be quoted as the system's false-accept rate. The stated mitigation
   is to define the population as **merge events**, stratified into clean cherry-picks, classifier
   retirements and gated merges, sampled proportionally — but I have not specified how to afford 30
   rejections in the clean stratum, and until I do, any β published here must name its stratum every
   time it is quoted. **Unresolved.**
2. **A clean textual merge can be semantically wrong and this design observes none of it.** The
   adversarial pass demonstrated it in git with no resolver involved: two additive route branches,
   zero CONFLICT lines, and a non-admin reaching an admin route. §3.2's remedy — run the gate on
   every file the cherry-pick touched, not only conflicted ones — closes the *instrument* gap but not
   the *knowledge* gap: nobody has measured how often it happens. **Unresolved, and it is the most
   important open number in this document.** The experiment is A7 in §8.
3. **The gate's scope shrinks as the classifier improves.** Every retirement moves a unit out of the
   gated population and into the ungated one, and retired units flow into `built`, which feeds review
   by a model. The banner gets quieter as more code lands unexamined. §7 prints retirements as their
   own count, which makes it visible; it does not make it safe. **Partially addressed.**

---

## 6. What this does not solve

**Adversarial findings closed by this design.**

- *#1, gate scoped to conflicted files (instrument half).* §3.2 runs it on every file the cherry-pick
  touched.
- *#3, patch-id blind to Python indentation.* §3.1 requires `git cherry` ∧ empty `git diff` before any
  retirement; `git cherry` may never retire alone.
- *#4, L5 runs the unit's own `conftest.py`.* Not applicable — this design drops the execution rung
  entirely rather than fix it. Content coverage is cheaper and does not invite the unit to certify
  itself. The cost is that a unit whose work landed *behaviourally* under a rewritten implementation
  will not retire; it stays escalated, which is the safe direction.
- *#10, rerere generalises across units.* Closed by not enabling rerere (below).
- *The pass's own cheapest repair — `ruff check` belongs in the gate.* Adopted, and promoted from an
  addition to the first thing done; it is the whole of §3.2.

**Adversarial findings NOT closed.**

- *#2, the ladder is a disjunction where Whewell requires a conjunction.* Partially. `git cherry` may
  no longer retire alone, but content coverage still may, on one class of facts. The conjunctive
  version — every rung with an opinion must agree — is right in principle and I have not costed it
  against a queue where both of today's retirements come from that single rung.
- *#5, autonomous class C is licensed for the bug it cannot see.* Closed only by abolition: this
  design licenses **no** autonomous resolution class at all, not even import union. The finding
  stands unrefuted as an argument against ever adding one.
- *#6, C4 tests presence, never order or reachability.* C4 is not built (§4.1), so the hole is
  unfilled rather than fixed. A reordering defect — an earlier catch-all shadowing a later specific
  case — is caught by nothing here.
- *#7, silent work loss is a bad merge and only the other direction is counted.* **Not closed, and it
  is live in the tree**: `exp43/test_exp43.py` uses `LOCK` twice with no definition, a merge that
  kept a use and dropped its binding. Ruff's F821 catches that particular shape, so §3.2 helps by
  accident. The general case — a retirement asserting work has landed when it has not — has no check.
- *#8, β defined over resolutions and quoted for merges.* §5 item 1. Unresolved.
- *#9, adjudication by reading is not a different class.* §5 states the behavioural-question remedy
  and this design does not build the tooling to derive those questions.
- *#11, the reviewer cannot see that a choice was made.* Not built. `git notes` on a resolved commit
  is the right shape and is one call, but with no resolver there is as yet nothing to annotate.
- *#12, escalation moves the queue and the Mergiraf trigger suppresses itself.* Partially — §7
  changes the banner. The trigger metric is not rebuilt.
- *#13, C5 stops at the test-file boundary.* C5 is not built at all. A reverted constant in `src/` is
  caught by nothing here.

**Explicitly not built, with reasons.**

- **No LLM merge resolver.** Best 2026 numbers on real conflicts are ≈55–62% developer-match and
  under 60% on Merge-Bench, with measured overfitting to conflicts repeated in training data
  `[cited, Evidence 1]`. At 57% semantic hunks in this queue, a 60% resolver is a machine for
  generating plausible wrong answers.
- **No Mergiraf yet.** It is the named bar — 84.1% of 21,615 scenarios, Python 84.78%, ~160 ms, git
  merge-driver integration `[cited, Evidence 1]` — and its measured cost on Python is 172 extra
  silently-clean merges to remove 29 spurious conflicts, which *is* β for a merge tool. It is not on
  the critical path at five genuine conflicts, and it must never be adopted before the gate exists.
  Not installed here and there is no cargo on this machine `[measured]`. **Falsifiable trigger:**
  install it when genuine escalations exceed ten at one tick.
- **No `merge=union` on any path containing code.** Git's own documentation says the line order is
  arbitrary and the result must be examined. T01 is the worked example.
- **No `rerere`, yet.** Evidence 1 recommends enabling it as free and reversible. The adversarial pass
  measured it silently applying a *bad* recorded resolution to an unrelated unit's byte-identical
  conflict, with zero markers and no message. It is survivable only because `rerere.autoUpdate`
  defaults false. **Do not enable it before the gate exists**; when enabled, set
  `rerere.autoUpdate false` explicitly and compute the conflicted set from
  `git diff --name-only --diff-filter=U`, never from marker presence.
- **`git config merge.conflictStyle zdiff3`: do set this.** Two seconds, reversible with `--unset`,
  and it is the difference between a resolver — human or model — seeing two alternatives and seeing
  what both sides started from. It is how I extracted the base regions in §2.2 at all, and
  delete-vs-modify is invisible without it. Neither it nor `rerere.enabled` is set in this worktree
  `[measured]`; git is 2.53.0.windows.2, so `ort`, `zdiff3` and `merge-tree` are all available.
- **No claim-width capping as a conflict remedy.** §2.3. Worth doing for throughput; refuted as a
  conflict fix.
- **No merge queue product.** GitHub's removes conflicting PRs rather than resolving them, so it
  would not shorten the list by one `[cited, Evidence 1]`. Speculative merge-group testing is a
  genuinely different class of evidence and belongs in a separate decision; it addresses merge
  *skew*, not conflicts.

**Also noticed and deliberately not touched** (unrelated dead code, per house rules): `src/mine.py`
and `src/x.py` are unparseable one-line files sitting inside the product package, and
`docs/10-research/experiments/exp43/test_exp43.py` is broken — but `docs/10-research/` is the
evidence base and changing it needs the principal's say-so.

---

## 7. Sequencing, by risk reduced per unit of the principal's attention

**Unblocks the queue standing today (hours, not days).**

1. **Content-based retirement plus banner hygiene** — `MRG2`. Retires `T02` and `K01` immediately,
   taking the escalation banner from 7 to 5, and closes the driver's own measured false-accept path
   (9 of 12 sampled reused subjects carry different content). Smaller diff than the code it replaces.
   **Also: print retirements as their own count** — `"5 escalated, 2 retired without review"` — so
   the number he sees grows when the classifier gets busier, rather than shrinking.
   *Cost to him: reading one diff.*
2. **Repair the two live artefacts** — `MRG3`. `harness.py` loses 313 duplicate lines;
   `test_recall_receipts.py` loses a stray import. `mypy --strict src/consilient` goes from 17 errors
   to 0 and `ruff check .` drops 6. This is a CI gate that is red today, and the change is pure
   deletion. *Cost to him: approving a deletion he can verify with one command.*
3. **`git config merge.conflictStyle zdiff3`** — one line, five seconds, reversible.
   *Cost to him: nothing.*

**Longer-term capability (days).**

4. **The gate** — `MRG1`, then the driver half of `MRG2`. The two missing checks are ~40 lines; the
   expensive part is wiring the revert path so a failed gate un-does the cherry-pick rather than
   logging about it. This must exist before any resolver is ever trusted, and before `rerere`.
5. **Cut the supply** — `MRG4`. Rebase every unmerged worktree each tick, and serialise
   duplicate-subsystem units in `ready()`. This is the highest-leverage change in the document by the
   §2.3 measurement, and it is also the one most likely to need tuning against reality, which is why
   it lands after the gate that would catch it misbehaving.
6. **Record merge events for β** — `MRG5`. Recording only. No number is published until 30
   principal-authored rejections exist, and the stratum is named every time it is quoted.

**Not scheduled:** Mergiraf (trigger in §6), any resolver, C4, C5, claim-width capping, rerere.

**A note on how these units are ordered, since it is the design applied to itself.** Three of the five
touch `.harness/build_driver.py` — the file that generated 22 of today's 42 conflict hunks. They are
therefore **serialised by dependency, deliberately**, which is exactly the rule §3.3 asks `ready()`
to enforce. `MRG1` and `MRG3` touch disjoint files and may run concurrently with each other.

---

## 8. Acceptance tests that can actually be run

Each is a command with a stated pass condition, runnable today.

**A1 — the classifier does not retire on subject alone.**
```
python -m pytest tests/test_build_driver.py -k subject_reuse
```
Fixture: two commits, identical subject, different content. **Pass:** the second stays in
`state["conflicts"]`.

**A2 — a retirement clears the escalation.**
```
python -m pytest tests/test_build_driver.py -k conflict_cleared_on_retire
```
**Pass:** no uid appears in both `state["conflicts"]` and `state["force_done"]`. Run against the live
state file today and it **fails** on `K01` — that is the regression this test locks shut.

**A3 — the gate rejects the T01 specimen and accepts the clean control.**
```
python .github/scripts/check_merge_acceptance.py --self-test
```
**Pass:** exit 1 with `KINDS bound at [10, 12]` and `OperationalError: near "CREATE"` on the
specimen; exit 0 on the hand-merged control.

**A4 — C1 does not false-alarm on this repository.**
```
python .github/scripts/check_merge_acceptance.py --scan src scripts tests .harness
```
**Pass:** zero findings. Measured today across 174 parsed files: **zero.** `[measured]` If this ever
exceeds zero on unmerged code, C1 is mis-scoped and must be narrowed — never disabled.

**A5 — the tree the merge produced type-checks and lints.**
```
python -m mypy --config-file mypy.ini src/consilient
python -m ruff check .
```
**Pass:** both exit 0. Today: **17 and 32 errors respectively.** `[measured]` This is the single pair
of commands that decides whether `MRG3` is done.

**A6 — the duplicate-subsystem detector fires on `N03`/`T02` and on ≤5% of dispatches.**
```
python -m pytest tests/test_build_driver.py -k duplicate_subsystem
```
**Pass:** `ready()` refuses to make `N03` and `T02` concurrently startable, and the firing rate over
all 1,906 claim-sharing pairs in `.harness/plan-units.json` is ≤5%. Measured at the top-20 cut: 1.0%
of claim-sharing pairs, 0.23% of all pairs, with `N03/T02` at rank 10. `[measured]`

**A7 — the open experiment, and the number this design most needs.** Replay each of the 72 built
units' cherry-picks against the HEAD of its day, run `mypy --config-file mypy.ini` and `ruff check`
before and after each, and count how many landed clean while introducing a diagnostic. That measures
the **ungated 94%** — the clean-merge population §5 item 2 admits is unobserved — it needs no
resolver, and it decides whether the semantically-wrong-clean-merge finding is the most important
item on this list or merely the most alarming.

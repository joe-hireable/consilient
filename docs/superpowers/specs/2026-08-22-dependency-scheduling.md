# Dependency scheduling: derive the check, isolate the index, fence the lease

- **Document class: W**
- **Review by:** 2026-09-22
- **Falsifier:** EXP-130 kills the derivation check if a dispatch's declared claim cannot be shown to cover the plan dependency graph.

**Class-W contract adopted 22 August 2026.** Mechanical admission only; existing claim wording and evidence tags are unchanged. [asserted]

**Correction:** coordinating concurrent workers through declared inputs is not an unoccupied
category. Bazel, Buck2 and Nix already enforce declared read/write sets by sandboxed execution;
Airflow, Dagster and Prefect already schedule over explicit dependency DAGs; lease-based
coordination with fencing tokens is a solved problem in the distributed-systems literature
(Kleppmann 2016; Chubby, Burrows 2006); and `git worktree` already gives every concurrent worker
its own index. The defensible gap is not any of those mechanisms. It is a *check*: a mechanical
proof that a dispatch's hand-declared claim covers what the dependency graph says the work can
touch, on a repository whose coordination failures are measured, not hypothetical. [cited:
bibliography § 16, all entries [FULL], read 22 Aug 2026]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0091 is PROVISIONAL and its named killing experiment can kill
  the derivation check for this repository. [asserted]
- **Author:** Cursor dispatch `20260822T193039-7269150217`. The principal supplied the question
  ("how can dependency graphs help agents stay organised and maximise parallelism without
  clashing?") and the four measured failures; the design below is this dispatch's answer and has
  not been reviewed by him. [measured]
- **Scope:** research and specification only. This document adds no product code, no CLI surface,
  no dependency, no gate change, no credential, no metered call. `src/consilient/` is AST-locked
  and untouched. [measured]

## 1. The four measured failures, verified

The brief names four failures from this repository's own operation. Each was re-verified against
code or trajectory before any design was proposed. [measured]

**F1 — path claims do not protect the git index.** Claims name working-tree paths; `git add` and
`git commit` serialise on `.git/index.lock`, which no claim covers. Two dispatches with disjoint
declared paths can still collide at commit time in a shared working tree. The mechanism is not a
mystery: the index is per-*worktree*, not per-repository, so a shared worktree means a shared
index regardless of what the claims say. [measured: `scripts/commit_gate.py` stages through the
shared index; cited: git-worktree(1), bibliography § 16 — a linked worktree shares the repository
"except per-worktree files such as `HEAD`, `index`"]

**F2 — check-then-append race in claim admission.** `scripts/dispatch.py` calls
`coordination.conflict(...)` and then `coordination.open_claim(...)` as two separate appends to
the trajectory log. Between the check and the append, another dispatcher can pass the same check.
This is not conjecture: on 22 Aug 2026 runs `20260822T140208-40b9767b0c` and
`20260822T140603-d953f3635e` both re-opened claims 19 seconds apart (14:58:06 and 14:58:25) with
`docs/10-research/experiment-register.md` added to both, and both were live simultaneously for
roughly four minutes. EXP-130's replay confirms the declared-paths rule, correctly applied, would
have refused the second admission. The race is in the admission protocol, not in claim content.
[measured: `.harness/log/2026-08-22.jsonl`; `results-exp130.json` A5]

**F3 — killed dispatches hold claims.** A dispatch that is killed never appends a terminal event;
its claim stays live until `timeout + grace` expires. 14 of 110 claims in the 21–22 Aug window
were opened more than once — widened mid-run by re-dispatch — and the terminal events for the
racing pair above are timeouts at 15:02:10 and 15:06:06, an hour after the work was dispatched.
Expiry is the only reclamation mechanism, and expiry without fencing is unsafe: the expired holder
can wake and write. [measured: `results-exp130.json` A5_context; cited: Kleppmann 2016,
bibliography § 16]

**F4 — hand-derived serial lanes drift.** The build plan's lane table is a second, hand-maintained
copy of the dependency structure. EXP-130 A1 measured it against the plans' own declared
`depends_on` edges: 55 units carrying 127 declared edges and 180 pairs with overlapping declared
claims — and the lanes order only some of them. 122 overlapping pairs share no lane entry; 37 of
those are ordered by nothing at all, neither lane nor dependency. 14 times a unit claims a path
under a lane's file yet appears in no lane's list; 3 times a lane lists a unit that claims nothing
under it. No cycles anywhere — the lanes' failure is incompleteness, not contradiction. [measured:
`results-exp130.json` A1]

## 2. The retrieved bar

| Bar | What it already achieves | Boundary that remains |
|---|---|---|
| **Bazel / Buck2** | Every action declares inputs and outputs; the sandbox makes an undeclared read a build error. Declaration enforced by isolation, not trust. [cited: bibliography § 16] | Declarations are authored per-rule by humans and enforced at action granularity; nothing derives them, and nothing schedules *agents* — the build graph is static per invocation. |
| **Nix** | The output path is a pure function of the declared input set; a missing input changes the hash and cannot silently succeed. [cited: bibliography § 16] | Same as above, at package granularity. |
| **Airflow** | The DAG is the schedule; a task runs when all upstreams succeed. [cited: bibliography § 16] | The DAG is hand-authored — exactly the design F4 measured drifting. |
| **Dagster** | Dependencies are *derived* from asset function parameters, machine-checked by the Python runtime. [cited: bibliography § 16] | Derivation works because the target (function signatures) is runtime-checked; a repository's write surface has no equivalent oracle. |
| **Prefect** | Tasks declare retries/timeouts; dependencies form implicitly from control flow. [cited: bibliography § 16] | Weakest enforcement of the three; the graph is whatever the runtime does. |
| **Kleppmann / Chubby** | Leases made safe by fencing tokens: the *resource* rejects any write whose token has gone backwards, so an expired holder cannot corrupt. [cited: bibliography § 16] | Requires the resource to check the token — a protocol change, not a claim-content change. |
| **git worktree** | Each linked worktree has its own `index` and `HEAD`; two workers staging in different worktrees cannot race on `index.lock`. [cited: bibliography § 16] | Isolates the index and working tree; says nothing about logical coupling between the paths being edited. |
| **Hermes** | SQLite transactions with compare-and-swap status/claim updates — atomic admission in one statement. [cited: `docs/00-context/hermes-teardown-2026-08-22.md`] | A different system's answer; Consilient's authority is the append-only trajectory, not a SQLite row. |
| **Ruflo** | File-claim UX similar to this repository's. [cited: `docs/00-context/ruflo-teardown-2026-08-22.md`] | The cautionary tale: non-atomic claim handling and unlocked JSON read/modify/write — F2's race, shipped. |

**Search record, 22 August 2026:** primary documentation was fetched for Bazel (sandboxing,
rules), Buck2 (rule authoring), Nix (derivations), Airflow (DAGs), Dagster (asset dependencies),
Prefect (tasks), git-worktree(1); the primary post for Kleppmann's fencing tokens and the Google
Research page for Chubby; competitor teardowns already in `docs/00-context/` for ruflo and hermes.
All bibliography § 16 entries are [FULL]. No source was found that *derives* an agent's write-claim
from a repository dependency graph and checks the declaration against it; the closest is Dagster
deriving the read-graph from checked code. "Nothing exists" is a claim requiring evidence: the
search was one session, English-language, first-party sources only — treat the gap as unproven,
not vacant. [measured] [asserted]

## 3. Design question: can a claim set be derived from the dependency graph?

**Measured answer: partially — for Python write-surfaces, yes; for the resources that actually
clashed today, no. Derivation is a check on declared claims, not a replacement for them.**

EXP-130 (pre-registered in `docs/10-research/experiment-register.md` before any output was
inspected; stopping rule fixed in advance; deterministic script, frozen local artefacts, no model
call, no network) built the file-level import graph of this repository with stdlib `ast` —
106 Python files, 165 resolved internal import edges with **zero** unresolved internal imports
(705 unresolved imports are all stdlib/third-party and correctly unresolvable to repository
files), 0 cycles — and evaluated derived claims (declared paths ∪ transitive dependents) against
hand-written ones. [measured: `results-exp130.json`; findings:
`experiments/exp130/findings-exp130.md`]

What derivation buys, measured:

- **It catches what the lanes miss.** 963 conflict edges under derived claims vs 872 under
  declared ones; the derived closure covers the 122 overlapping unit pairs the lane table leaves
  unordered, 37 of which are ordered by nothing at all (F4). [measured: A1, A2]
- **It does not collapse at the median — and it has one real hub.** Median derived claim names
  14 paths, so the pre-registered god-node loss condition (median over half of the 106 Python
  files) did not fire. But `src/consilient/events.py` has 61 transitive dependents — 58 % of the
  repository, the only file at ≥ 50 %; 2 files sit at ≥ 30 %, and 45.95 % of path-claiming
  units' derived claims include `events.py`. A refuse-mode check would serialise nearly half the
  plan on the event schema; that is the measured reason the check ships warn-first. [measured: A2]
- **It refuses more true conflicts.** Replaying 110 real dispatch claims from 21–22 Aug, the
  derived policy refuses 7 admissions where the declared policy refuses 1 — a strict superset,
  so no false admits. [measured: A5]

What it costs, measured:

- **Width.** Maximum safe concurrency over the build plan falls from 9 units (declared) to 7
  (derived). [measured: A2]
- **Blindness.** See § 4.

The pre-registered decision rule — treatment refusals more than twice control's selects
*derivation as a check, not a replacement* — fired: 7 > 2 × 1. The overall shape is mixed by the
pre-declared win/loss conditions (no false admits, no god-node collapse, more true pairs caught,
but strictly less peak width), and is reported as mixed, not rounded to a win. [measured]

## 4. What the graph cannot see

This is the load-bearing negative result. An import graph is a graph of *who reads whom* in one
language. The day's coordination failures lived elsewhere. [measured: A4, A5]

- **The git index.** Not a Python module; no import edge spans it. F1 is invisible to any
  import-derived claim. The fix is a runtime-conformant isolated workspace and index, which needs no
  graph at all.
- **The trajectory log and the admission protocol.** F2's race is between two appends to
  `.harness/log/*.jsonl`; F3's abandonment is a missing append. Both are protocol properties.
  63 event-kind string literals are each shared by two or more files, and 104 file pairs are
  coupled through those literals with no import edge in either direction — through shared data
  files and the trajectory schema. Derived claims extend only along import edges, so derivation
  cannot couple any of these 104 pairs; that follows from the construction, not from a separate
  measurement. [measured: A4 counts; algebra: the blindness]
- **Non-Python surfaces.** 22 of the 139 claimed plan paths name no Python file — specs, ADRs,
  the experiment register, CI workflows. Today's one real concurrent overlap was two claims on
  `docs/10-research/experiment-register.md`: a Markdown file no import graph will ever span.
- **Cross-repository and runtime coupling.** Anything resolved at runtime (plugin registries,
  subprocess dispatch, MCP) leaves no static import edge.

A derived claim that passed its check could still clash on every one of these. That is why
derivation is a *check on* declared claims — which can name docs, data files and schemas the
graph cannot — and never a *source of* them. [asserted]

## 5. The design

Three mechanisms, each traced to a measured failure, each with its check named. No mechanism is
a new orchestrator, registry or CLI surface. [asserted]

**D1 — Runtime-conformant isolated workspace for write work (answers F1 and R4).** A dispatch that
may write, stage or commit receives a per-run workspace and Git index isolated from every other
writer. `scripts/dispatch.py` owns provisioning and selects a linked worktree, an isolated worktree
exposed through `GIT_DIR`/`GIT_WORK_TREE`, or a full clone only when the exact runtime/version has
passed that form's read, write, stage and commit probe; an unprobed or failing form falls back or
refuses. [cited: `docs/20-design/dispatch-layer-requirements-2026-08-20.md` R4;
git-worktree(1), bibliography § 16] Check: exercise every write-admitted runtime/version through an
actual read, write, stage and throwaway commit in its provisioned form, then retain the concurrent
separate-index regression. An `index.lock`-only check is insufficient. [asserted]

**D2 — Compare-and-append admission with a fencing epoch (answers F2, F3).** Claim admission
becomes one atomic operation at the trajectory's single writer: conflict-check and append in the
same critical section, and every claim carries a monotonically increasing epoch that the commit
gate checks at staging time — a write from a superseded epoch is rejected. This is Kleppmann's
fencing token applied to the claim log: expiry alone is unsafe because the expired holder can
wake and write. [cited: Kleppmann 2016; Chubby, bibliography § 16] This is the build plan's
F02/T02/D02 territory; this specification records *why* (the measured 19-second race) and does
not re-decide it. Check: a two-dispatcher interleaving test where the loser's late stage is
rejected by epoch. [asserted]

**D3 — Derived-coverage check on declared claims (answers F4).** Declared claims remain the
authority — they express intent over docs, data and schema surfaces the graph cannot see. At
admission, for each `.py` path in a declared claim, compute the transitive-dependents closure
from the import graph; a declared claim that omits a dependent is *flagged* in the trajectory
(warn first, refuse only after the warning's false-positive rate is measured — the closure is
conservative and one measured hub, `events.py` at 58 % of the repository, would otherwise
serialise half the plan). The lanes stop being a second hand-maintained dependency copy: lane
order is *derived* from the plans' declared `depends_on` edges, which EXP-130 showed are acyclic
and complete where the lanes are incomplete. Check: `run_exp130.py` is the
instrument; the CI form is a test that the lane table agrees with the declared-edge topological
order. [measured: A1; asserted: the warn-then-refuse staging]

What is deliberately **not** built: a general DAG scheduler, a hermetic sandbox, a lock service.
The measured peak concurrency was 18 simultaneously live claims (21 Aug) with exactly 1 real
overlapping pair all day on 22 Aug — the constraint that bit was correctness of admission, not
scheduling throughput. [measured: A5_context]

## 6. Requirements and checks owed by implementation

This specification declares future behaviour; nothing here is enforced today. Each check ships
with its code, in the same commit. [asserted]

| Priority | Requirement | Acceptance check |
|---|---|---|
| P0 | Write dispatches run in runtime-conformant isolated workspaces with independent indexes. [asserted] | For every admitted runtime/version, an actual workspace probe reads a tracked file, writes a file, stages it and creates a throwaway commit; failure excludes that runtime/workspace tuple or triggers a proved fallback. Two concurrent write dispatches use different indexes, and staging in the shared main workspace is refused. [asserted] |
| P0 | Admission is compare-and-append at the single writer; claims carry a fencing epoch. [asserted] | Interleaving test: the loser of a 19-second-apart admission pair is refused; a stage from a superseded epoch is rejected by the commit gate. [asserted] |
| P1 | Derived-coverage warning on Python claims. [asserted] | `run_exp130.py` stays green as the instrument; a declared claim omitting a transitive dependent produces a `claim.coverage_warning` event naming the omitted files. [asserted] |
| P1 | Lane tables are derived, not hand-written. [asserted] | CI test: any hand-written lane ordering that disagrees with the declared-edge topological order fails. [asserted] |

The existing AST lock, secret scan, commit-attribution gate and record-number checker continue to
run. They are necessary and insufficient for the above. [measured]

## 7. Evidence against: the over-engineering case

The strongest objection is that this specification already builds too much, and the experiment's
own numbers make the case. [measured]

- **The width derivation buys is width nobody used.** Peak concurrency today was 8 live claims;
  the derived policy *costs* width (9 → 7). On a day with 1 real overlap in 110 claims, a
  scheduler optimising for parallel width is solving the problem the repository does not have.
- **The clash that actually happened was a protocol race**, which D2 fixes without any graph.
  D1 needs no graph either. Of the four failures, derivation addresses only F4 — and F4's
  cheapest fix is deleting the hand-written lane table in favour of the declared edges the plans
  already carry, no import graph required.
- **Hermetic build systems earned their complexity on codebases far larger than this one.**
  This repository has 106 Python files and 165 internal import edges; Bazel's answer — sandboxed
  enforcement of declared inputs — is a poor fit for a system whose most-contended resources are
  documents. And the one real hub this repository does have (`events.py`, 58 % dependents
  closure) is an argument *against* refuse-mode derivation, not for hermeticity.
- **The closure is conservative and will over-flag.** 2 files reach ≥ 30 % of the repository
  and `events.py` reaches 58 %; a claim on either flags a third to a half of the codebase.
  Warn-first staging exists precisely
  because the false-positive rate is unmeasured.

The honest reading: D1 and D2 are protocol repairs justified by measured failures; D3 is
justified only as a *check* (the pre-registered rule said so), and only if its warning
false-positive rate comes in low. If the killing experiment named in ADR-0091 shows the warnings
are noise, D3 should be deleted and the lane-derivation kept — that is the floor, and everything
above it was interchangeable. [asserted]

## 8. Plain answer and delta

The plain answer is: use a runtime-conformant isolated workspace and index, make claim admission
atomic with a fencing epoch, derive the lane order from the dependencies the plans already declare, and keep
hand-written claims as the authority over everything the graph cannot see. All four are incumbent
mechanisms with primary citations; none is novel. [cited: bibliography § 16]

The delta this project adds is narrow and is the only thing here that is new: a mechanical check
that a declared claim covers its transitive dependents, run by an instrument (`run_exp130.py`)
whose results are committed and re-runnable, on a repository that measured its own coordination
failures first. Beating the bar here means *knowing* the claim is complete, not declaring it —
and the measurement of whether that knowledge prevents clashes is named, pre-registered and
killable. [asserted]

# 0091. Check declared claims against the import graph, and keep declared claims authoritative

- **Status:** PROVISIONAL — EXP-131 can delete the D3 coverage check; EXP-130's result is the
  measured ground for everything else. [asserted]
- **Date:** 2026-08-22. [measured]
- **Deciders:** Joe Brown supplied the question and the four measured failures in the dispatch
  brief; Cursor dispatch `20260822T193039-7269150217` owns this provisional mechanism, which he
  has not reviewed. [measured]
- **Inquiry tier reached:** T3 measure — EXP-130 ran on frozen local artefacts with a
  pre-registered stopping rule; the D3 warning's false-positive rate is unmeasured and is
  EXP-131. [measured]
- **Executable model:** none — the decision variable (check vs replace vs nothing) was settled
  by EXP-130's pre-registered decision rule on counted artefacts, not by a fitted model.
  [asserted]

## Context

**Correction:** coordinating concurrent workers through declared inputs is occupied territory.
Bazel, Buck2 and Nix enforce declared read/write sets by sandboxed execution; Airflow, Dagster
and Prefect schedule over explicit dependency DAGs; fencing tokens make leases safe (Kleppmann
2016; Chubby, Burrows 2006); `git worktree` gives every worker its own index. None of that is
ours to invent. [cited: `../10-research/bibliography.md` § 16, all [FULL], read 2026-08-22]

This repository's dispatch coordination failed four measured ways on 20–22 Aug 2026: path claims
do not protect the git index (F1); claim admission is a check-then-append race (F2) — measured
end-to-end when runs `20260822T140208-40b9767b0c` and `20260822T140603-d953f3635e` both held live
claims covering `docs/10-research/experiment-register.md` for ~4 minutes after re-opening 19
seconds apart; killed dispatches hold claims until expiry with no fencing (F3) — 14 of 110 claims
in the window were re-opened mid-run; and the hand-written serial lanes drift from the plans'
declared dependencies (F4) — of 180 unit pairs with overlapping declared claims, 122 are ordered
by no lane and 37 of those by nothing at all; 14 units claim paths under a lane's file while
appearing in no lane. [measured: `.harness/log/2026-08-22.jsonl`;
`../10-research/experiments/exp130/results-exp130.json` A1, A5]

The open question the brief posed: can a claim set be *derived* from the dependency graph rather
than hand-written, and can the system then verify a declared claim covers its transitive
dependencies?

## Decision

Keep hand-declared claims as the sole authority over a dispatch's write set, and add a mechanical
check against the import graph: at admission, for each Python path in a declared claim, compute
the transitive-dependents closure; a claim that omits a dependent is flagged
(`claim.coverage_warning`), warn-first, never refusing until EXP-131 measures the false-positive
rate. Derive lane ordering from the plans' declared `depends_on` edges and delete hand-maintained
lane tables as a dependency copy. Fix the admission race and abandoned-claim reclamation as
protocol work — compare-and-append at the trajectory's single writer with a monotonically
increasing fencing epoch checked by the commit gate — and give every write dispatch an isolated
workspace and index provisioned in a form its exact runtime/version has passed: linked worktree,
isolated exported Git environment or full clone. A failing or unprobed form falls back or refuses,
so the index race is dissolved without repeating R4's runtime failure. Do not build a general DAG
scheduler, a hermetic sandbox, or a lock service. [cited:
`../20-design/dispatch-layer-requirements-2026-08-20.md` R4] [asserted]

## Evidence

- `[measured]` EXP-130, re-runnable: `python ../10-research/experiments/exp130/run_exp130.py`,
  artefact `results-exp130.json`, findings `findings-exp130.md`. Import graph: 106 files, 165
  resolved internal edges, 0 unresolved internal imports (705 unresolved are all
  stdlib/third-party), 0 cycles; median derived claim 14 paths; the one hub is
  `src/consilient/events.py` with 61 transitive dependents (58 % of the repository; 1 file
  ≥ 50 %, 2 files ≥ 30 %). Replay of 110 real claims: declared-paths policy refuses 1, derived
  policy refuses 7 — a strict superset, no false admits. Pre-registered decision rule (treatment
  refusals > 2 × control ⇒ check, not replacement) fired: 7 > 2. Overall shape mixed by the
  pre-declared win/loss conditions: peak safe concurrency fell 9 → 7.
- `[measured]` What the graph cannot see (EXP-130 A4/A5): 22 of 139 claimed plan paths name no
  Python file; 104 file pairs are coupled through 63 shared event-kind literals with no import
  edge in either direction, and derivation extends only along import edges, so it cannot couple
  any of them; the day's one real overlap was two claims on a Markdown register — invisible to
  any import graph.
- `[measured]` Actual concurrency pressure: peak 18 simultaneously live claims on 21 Aug, 8 on
  22 Aug; 1 actual concurrent overlapping pair in 110 claims.
- `[cited]` Kleppmann, M. (2016), *How to do distributed locking* — fencing tokens: the resource
  rejects any write whose token has gone backwards; expiry alone is unsafe because the expired
  holder can wake and write. Bibliography § 16 [FULL].
- `[cited]` Burrows, M. (2006), *The Chubby Lock Service*, OSDI '06 — sequencers; the resource,
  not the lock holder, checks the token. Bibliography § 16 [FULL].
- `[cited]` git-worktree(1) — a linked worktree shares the repository "except per-worktree files
  such as `HEAD`, `index`". Bibliography § 16 [FULL].
- `[cited]` Bazel sandboxing and rules; Buck2 rule authoring; Nix derivations — declared
  input/output sets enforced by isolation. Bibliography § 16 [FULL].
- `[cited]` Dagster asset dependencies — the one incumbent that *derives* its graph (from
  runtime-checked function parameters) rather than hand-writing it. Bibliography § 16 [FULL].
- `[cited]` `../00-context/ruflo-teardown-2026-08-22.md` — non-atomic claim handling shipped as
  F2's race; `../00-context/hermes-teardown-2026-08-22.md` — SQLite compare-and-swap admission as
  the atomic alternative.
- `[asserted]` Warn-first staging for D3; the closure is conservative and the measured hub is
  not hypothetical: a claim on `events.py` flags 58 % of the repository, and 45.95 % of
  path-claiming units' derived claims include it.

## Evidence against

- `[measured]` **The width derivation buys is width nobody used.** Peak concurrency today was 8
  live claims against a derived-policy width of 7 — and derivation *costs* width (9 → 7). With 1
  real overlap in 110 claims, a scheduler optimising parallel width solves a problem this
  repository does not have. This is the strongest argument that D3 is over-engineering; it is
  why D3 ships as a warn-mode check behind EXP-131 rather than as a refusal.
- `[measured]` **Three of the four failures are invisible to the graph.** F1 is the git index
  (not a module), F2 is a protocol race (the 19-second pair both *declared* the register path —
  correct claim content, broken admission), F3 is a missing terminal event. Only F4 is a
  derivation problem, and F4's cheapest fix is deriving lanes from edges the plans already
  declare — no import graph required. The honest scope of the graph in this decision is one
  check, not the architecture.
- `[cited]` Airflow's hand-authored DAG is exactly the design F4 measured drifting — cited not as
  a bar to copy but as evidence that hand-maintained dependency copies rot. Bibliography § 16.
- Known weaknesses in our own evidence: EXP-130 is a single repository (this one), a single
  language, a two-day replay window, and a snapshot — the import graph is re-derived per run and
  this result does not travel. The replay's treatment refusals are counterfactual; whether
  refusing those 7 admissions would have prevented real clashes is unmeasured (the real clash was
  a protocol race). Single author, no review; the principal has not seen this ADR.
- Searched for a counterexample to "no incumbent derives agent write-claims from a dependency
  graph": first-party docs for Bazel, Buck2, Nix, Airflow, Dagster, Prefect, git-worktree;
  Kleppmann; Chubby; the ruflo and hermes teardowns. Dagster is the nearest miss. One session,
  English-language, first-party sources only — the gap is unproven, not vacant.

## Consequences

**Positive** — F4 gets a mechanical instrument (`run_exp130.py` becomes the check); lane drift
becomes impossible to ship silently because lanes are derived, not maintained; the claim protocol
gets the fencing the literature says correctness requires; the index race is dissolved rather
than policed. Every mechanism traces to a measured failure, and the one speculative mechanism
(D3) is behind a killing experiment.

**Negative** — D3's closure is conservative: a claim on either of the 2 hub files flags ≥ 30 %
of the repository (on `events.py`, 58 %), and the false-positive rate is unmeasured until
EXP-131 runs. Runtime-conformant per-run workspaces add setup and disk cost to every write dispatch;
a full-clone fallback costs more than a linked worktree. Compare-and-append admission serialises claim
opening at the single writer — a throughput cost nobody has measured because peak admission rate
today is far below any plausible limit. Deleting hand-written lanes removes a human-readable
overview some planning sessions used.

**Neutral but load-bearing** — Declared claims remain the authority; nothing here authorises
refusing a dispatch whose claim is complete but unusual. This ADR changes no gate, no CLI
surface, and no claim protocol today: D1/D2/D3 are specifications owed by implementation, each
shipping with its check in the same commit. EXP-98 (organisation-level dependency scheduling) is
a different claim and stays where it is. Gate A and Gate B are untouched.

## Enforcement

This ADR declares one invariant and one boundary; both are prospective and ship with their
implementation, not before.

- Invariant: a hand-written lane ordering that disagrees with the declared-edge topological
  order fails CI. Check: `tests/test_v0_invariants.py` lane-derivation test (owed by the
  implementation commit; `run_exp130.py` A1 is the instrument today). Fails CI: yes, once landed.
  Added in the same commit as the implementation: yes — that commit is future work.
- Boundary: the coverage check warns and never refuses until EXP-131 promotes it. Check: the
  `claim.coverage_warning` event schema carries no refusal path; a refuse-mode flag does not
  exist to be flipped by accident. Fails CI: n/a — structural. Added in the same commit: yes.
- The fencing-epoch and runtime-workspace conformance checks are specified in
  `../superpowers/specs/2026-08-22-dependency-scheduling.md` § 6 and owed by their implementation
  commits. The workspace check enumerates every write-admitted runtime/version and proves read,
  write, stage, commit and index isolation; an `index.lock`-only check does not satisfy it.

## What would overturn this

**EXP-131** kills D3: if false positives exceed true positives over its frozen window (20
warnings or 28 days), the coverage check is deleted and this ADR is superseded to record it. The
lane-derivation half stands on EXP-130 A1 regardless. Separately, a re-run of EXP-130's
instrument on a future tree showing god-node collapse (median derived claim ≥ 50 % of files) or
a false admit overturns the derivation premise itself. A lower-cost overturning result is an
incumbent that already checks declared agent claims against a derived graph with receipts; the
search record above says what was searched.

## Publication candidate?

No. The mechanisms are all incumbent (worktrees, fencing tokens, DAG scheduling); the only
novelty is applying a derivation *check* to agent claims with a pre-registered measurement, and
one mixed-result experiment on one repository is below the bar in `../publications/README.md`.
If EXP-131 produces a clean kill or a clean promotion with the trajectory receipts, the pair
might be worth a short note then.

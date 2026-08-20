# Guards that cannot fail

### Structurally inert checks in a system built to verify itself: an experience report

**Joe Brown** — `joe@gethireable.com` — sole accountable author
Consilient research programme
Draft of 20 August 2026. **Not submitted. Not for circulation.**

---

## Abstract

**Worst limitation.** This is a self-selected experience report from one repository after
seventeen hours and 116 commits, written and audited by one developer with heavy AI assistance.
The same process wrote and selected every defective guard in the catalogue. The evidence
establishes existence, not prevalence, a rate or a comparison. [measured] [asserted]

We report **twenty-five defective guards and one successful control**. Thirteen guards could not
fail under any input, two gate conditions could never pass, and ten checks could pass for reasons
that made the pass uninformative. [measured] The twenty-sixth exhibit is the contrast: a
parent-commit control that prevented five later-suite failures from becoming a counterfactual
$\beta = 1.0$; every parent also failed, so all five pairs were classified as drift. [measured]
[algebra] The control cost one additional checkout and test execution per pair. [measured]

The cleanest failure sits in the file that computes the programme's central quantity. A field
declared that $\beta$ was a lower bound on joint human-plus-check error by default, and a dedicated
test asserted the hard-coded `True`. No collection protocol established the sampling condition
the bound requires. [measured] The repair defaults the claim to false and makes it explicit, but
still trusts a caller's declaration rather than verifying the sampling property. [measured]
[asserted] In the same gate, one condition admitted every possible $\beta$ while another required
twenty uses of behaviour the gate itself forbade until it passed. [algebra]

The common mechanism is that **tests asserted mechanisms rather than properties**. A test can
certify a constant, an early-return path or a comparison while never exercising the property the
guard was meant to secure. [measured] A related hypothesis recurred three times: a fixture able to
construct a forbidden state trains the suite to permit that state. [measured] [asserted] We have
not built the proposed detector or run it on a public corpus. [measured]

The recommendation is deliberately old: exhibit every guard rejecting an input it should reject
and retain that falsification record. [asserted] We claim no new technique; §9 treats mutation
testing as the baseline and records that its sources are not yet publication-depth. [asserted]

**Keywords:** inert checks, vacuity, invariant enforcement, test oracles, agentic software
engineering, experience report, negative results.

---

## 1. Introduction

A check that cannot fail is worse than no check. No check leaves a known gap. An inert check
fills the gap with a green tick, and everything downstream — a gate marked satisfied, an ADR
marked enforced, a reviewer's attention spent elsewhere — is spent against a guarantee that was
never bought.

This is a familiar observation. Formal verification has called the phenomenon *vacuity* since
1997 [3, 12, 13]; mutation testing has been asking whether a test can fail since 1978 [7]; test
oracle assessment [11] and checked coverage [18, 19] both attack the same question with better
instruments than we have. We claim none of that.

What we report is what happened when the question arrived somewhere none of those instruments is
defined. The objects that broke here were not programs under test and not unit-test oracles. They
were: an ADR gate condition; a replay invariant over an append-only log; a dataclass constructor
admitting a "measured" verdict; a CI workflow assertion about a symlink; a publication rule
written in a governance file and enforced by nothing; a boolean field that asserts a mathematical
property, with a passing test that certifies it. Mutation testing has no mutants for a gate
condition written in English. Checked coverage has no dynamic slice for a rule in `AGENTS.md`.
Neither would have found eleven of the thirteen inert checks below.

The system under study makes the case sharper than a random repository would. Consilient is a
meta-harness organised entirely around measuring $\beta$, the false-accept rate of automated
verification — the rate at which the checks say yes to something that is wrong. Its working
principles, written down before any of these defects were found, include:

> **A chokepoint without an enforcement rule is not a chokepoint.** Any invariant this project
> declares must ship with the check that enforces it, in the same commit.

and

> **The Engineering Ratchet.** When something fails, the fix goes in code — a check, a type, a
> constraint — not in a prompt.

Both principles were violated inside the repository that declares them, within a day of declaring
them, in the artefacts the principles were written about. That is not an embarrassment to be
buried; it is the finding. A project that measures verifier false-accept rates shipped verifiers
with a false-accept rate of one.

### 1.1 Contributions

1. **An anchored catalogue** (§4) of twenty-five defective instances, plus one positive control,
   with discovery mode, survival time, repair commit and status, every entry traceable to a file or
   commit in a repository from which we release the instruments. [measured]
2. **A common mechanism** (§5): tests that assert the mechanism rather than the property; and the
   permissive-fixture rule, which we could not locate in the literature and which is mechanically
   detectable.
3. **A discipline** (§6): the *falsification record* — a guard is not a guard until it has been
   exhibited rejecting something, and the exhibit is stored. We give its cost, its failure modes,
   and the one case in this corpus where following it worked, including a check that on its first
   run correctly flagged **itself**.
4. **An honest prior-art position** (§7) which retires most of what a reader might otherwise take
   as novel. [asserted]

### 1.2 Evidence discipline used in this paper

The repository tags every claim with its evidence class, and we carry the same discipline into
this prose as explicit hedges. Tables use a compact column:

| Tag | Meaning in this paper |
|---|---|
| **M** | Measured: we ran it, or read it directly from a committed artefact, at the stated commit. |
| **A** | Asserted: our judgement, with the reasoning given. |
| **C** | Cited: a source says it; read-depth is flagged in §9. |
| **X** | Algebra: it follows from stated premises. |

In prose, an **M** claim reads "we measured", an **A** claim reads "we judge" or "in our
assessment", and a **C** claim names its source. A number produced by a model, not by an
instrument, is never written as an empirical result. Nothing in this paper is upgraded from its
tag without new evidence.

**Anchor.** The original twenty-four-entry catalogue was measured on branch
`worktree-consilience-cto` at commit
`81e7143`, 20 August 2026 11:33:11 +0100, unless a different commit is stated, with Python 3.13.11
and mypy 2.3.1. At that commit the repository has 116 commits, the suite reports `62 passed in
0.44s`, the continuous-integration static gate (`python -m mypy src/consilience`, under the
repository's non-strict `mypy.ini`) reports `Success: no issues found`, `mypy --strict` reports 21
errors in 3 files (exhibit A13), and the private-corpus gate exits 0. The branch was moving while
this was written — two of the catalogue's exhibits were repaired by a parallel session at 11:01 and
11:04 on the day of writing — so every entry carries its status **as of that commit** and not as of
publication. A post-anchor supplement adds A15 and C1, records A5's repair at `9c2fe62`, and records
the still-unaccepted A15 correction proposed at `05bf3ac`; those entries say so rather than silently
mixing snapshots. [measured]

---

## 2. The system, and why it is a hard case

Consilient is a research repository for an open-source meta-harness: an
orchestrator that sits above coding agents and routes work according to how much verification the
artefact needs. It is named after Whewell's 1840 definition of consilience [22], and its central
quantity is derived from the third clause of that definition — convergence is a *test*, and tests
have error rates. $\beta$ is that error rate. At the time of writing its v0 specification is
approved for an **observe-only** increment: the shipped code records trajectory events, projects
them into SQLite and computes $\beta$; it does not route, block or accept anything, and a test
asserts the command-line surface cannot. Routing and orchestration remain behind gates neither of
which has passed — one of which is A2 in the catalogue below.

Three properties make it an unusually demanding setting for the failure we report, and therefore a
more interesting one than a repository picked at random.

**It is small and recent.** At the anchor commit the repository is 116 commits and 17 hours 2
minutes old (initial commit `99e7e81`, 19 August 2026 18:31:30 +0100). Product source is 972 lines
across five files with 62 tests. There is nowhere for a defect to hide in accumulated legacy. We
measured this.

**It declares its invariants numerically and enforces several of them in CI.** The specification
draft names invariants `V0-01` … `V0-26`; the CI workflow runs the suite, a static type check, a
replay assertion on the real trajectory, a secret scan and a skills-mirror assertion. This is not a
repository without checks. It is a repository with an unusual density of them.

**Its written rules forbid exactly this failure.** Principle 3 requires an invariant to ship with
its check in the same commit; principle 4 requires fixes to land as code rather than as prompt
text. The defects below are not violations of an unstated norm.

One further property is relevant and uncomfortable: the code and most of the documents were
written by a language model under human direction, and so were most of the audits. We return to
what that does to the catalogue's validity in §8.

**What $\beta$ is, and what we do not claim about it.** $\beta = P(\text{checks accept} \mid
\text{artefact bad})$. In this repository it has never been measured with sufficient data. Running
the meter at the anchor commit returns, verbatim:

```
beta [all]: insufficient data (0 human rejections, need 30)
```

We measured that today. A retrospective mining study over 356 merged pull requests from two
private commercial repositories produced proxy-labelled contingency tables, but their labels come
from a hotfix heuristic whose audited precision is 1 in 15, and the strong signal — a maintainer
explicitly reverting — fired zero times in 356 pull requests. **This paper does not rest on any
$\beta$ figure.** $\beta$ appears here only as the reason the system exists and as the quantity
several of the broken guards were supposed to protect. Where we use a number from that corpus at
all (§4, exhibits B5 and B6) it is an aggregate count and is labelled as proxy-based.

---

## 3. Method

There was no protocol. This is an experience report and we state its method honestly, including
the parts that make it weaker than a study.

### 3.1 How the defects were found

Findings arrived through five channels, which we record because the channel matters to §8:

1. **A stronger static checker run on a whim.** `mypy --strict` was added and run during an
   unrelated assessment. It found a reachable crash in 0.47 seconds that 24 passing tests had
   missed (commit `ffb3d60`, 01:40:38). We measured this.
2. **Cross-family invariant audit.** A snapshot of `src/`, the tests, the CI workflow, the
   specification and the ADRs was staged outside the repository and handed to a different model
   family (Cursor, Gemini 3.7 Flash) with a single question asked of each numbered invariant:
   *would its check actually catch a violation, and is there a second path to the same state?*
   Three defects in approximately twelve minutes (commit `32eacb8`, 03:52:19). We measured this.
3. **A paid cross-family leak audit** cross-referencing 5,256 real file paths from the two private
   corpora against this tree (commit `fafd1a6`, 10:39:37).
4. **A same-family numbers audit** (Codex, GPT family) over the quantitative claims, adjudicated
   by a third family (commit range `daf688a`…`b164ae9`).
5. **Using the thing.** Several were found by operating the system: a lock file vanished during a
   live run; a monitor reported a state that had ended seven hours earlier; a refused log line
   bricked the reader.

### 3.2 The timeline is shorter than it looks, and we correct the record

An internal brief described these as found "over roughly 48 hours". That is wrong and we measured
the correction: the repository's entire recorded history at the anchor commit is **17 hours 2
minutes**, spanning two calendar days. Sixteen of the original twenty-four entries were recorded on 20
August alone. Where an entry's survival time is given as "the full life of the repository", that
means seventeen hours, not seventeen months. This matters for §8 and we would rather state it than
let a reader infer a longer exposure.

### 3.3 What counts as an entry

We admit a defective instance to the catalogue if a check, gate, assertion or declared rule was,
at some committed state, incapable of distinguishing the condition it named. We add one positive
control as a contrast. [asserted] The four classes are:

- **Class A — structurally inert.** No input, state or execution could have made it fail, or the
  declared guarantee has no executing check at all. Thirteen entries.
- **Class A′ — the inverse.** A declared invariant that could never have passed. Two entries,
  kept because they are the same drift running the other way.
- **Class B — uninformative pass.** The check could in principle fail, but on the corpus and in
  the configuration in which it ran, its pass carried no information about the property. Ten
  entries.
- **Class C — prevented wrong answer.** A control exhibited the failure it existed to distinguish
  and stopped a counterfactual result from being reported. One positive entry. [measured]

The classification is our judgement and a reader may reasonably move two or three entries between
A and B. We flag the contested ones inline.

### 3.4 Reproduction

The four scripts, the product source and the test suite are in the repository. Live checks used in
this paper (`consil beta`, `consil replay --json`, the suite, both mypy invocations, the
private-corpus gate, the Wilson and binomial arithmetic of §4) all run from a clean checkout with
no private data. The retrospective mining figures do not: they read four gitignored artefacts derived from
private commercial repositories, and cannot be reproduced outside the author's machine. See §10.

---

## 4. Results: the catalogue

Tables 1–3 are the result. Everything after them is interpretation.

**Table 1 — Class A: checks that could not fail.** "Survived" is from the commit that introduced
the defect to the commit that repaired it, or to the anchor commit where still open.

| # | The guard, as declared | Why it could not fail | Found by | Survived | Status at `81e7143` | Ev. |
|---|---|---|---|---|---|---|
| A1 | ADR-0015 Gate A condition 2: *delete the database, replay the log, assert the state matches* | `cmd_replay` built the projection from the log **twice** and compared the two rebuilds — identical by construction. Worse, `projection.build()` unlinks the database first, destroying the drift the check existed to detect. The ADR recorded the gate as **satisfied**. | Cross-family invariant audit, ~12 min | to `32eacb8` (03:52) | Repaired; needed two further repairs (`4210ec0`, `66715ab`) | M |
| A2 | ADR-0015 Gate B condition 2: *the derived parallelism ceiling is > 1* | $n_{max} = T_a/(f \cdot T_r)$ with $f \le 1$, so $n_{max} \ge 25/8 = 3.125$ for **every** critic recall and therefore every $\beta$, including $\beta = 1.0$ — a critic that catches nothing. The gate asked whether a quantity with a floor of 3.125 exceeds 1. | Raised in an internal sweep; confirmed by independent verification | initial commit `99e7e81` → `82475a8` (11:01) = **16 h 30 m**, the full life of the repository | Superseded by ADR-0037; we ran the replacement and it exhibits both a PASS and a FAIL row | M, X |
| A3 | `V0-18`: an agent may never author a human's decision — the oracle $\beta$ is computed against | `_check_human_authority()` returned early unless `data["human_decision"]` was present. `projection._apply_outcome()` read `data["human_verdict"]` straight off an `attempt.outcome` event into the `outcomes` table `beta.compute()` reads. The constant `HUMAN_ONLY` already contained `"verdict"`; nothing consulted it on that path. | Cross-family invariant audit | to `32eacb8` | Repaired, 5 tests; `actor` remains unauthenticated, so it stops an accidental forgery, not a determined one | M |
| A4 | `Beta.__post_init__`: a *measured* $\beta$ must be evidenced | It checked only whether `point` and `interval` were **present**. A `measured` verdict with zero rejections, a rate outside $[0,1]$, an inverted interval or a point outside its own interval constructed cleanly and rendered without complaint. `compute()`'s `min_rejections` argument could also *lower* the floor it enforced. | Cross-family invariant audit | to `32eacb8` | Repaired, 6 tests; `min_rejections` may now only be raised | M |
| A5 | `lower_bound_on_joint_error: bool = True`, with `test_beta_declares_itself_a_lower_bound_on_a_joint_error` asserting it is `True` | The field was a hard-coded dataclass default. The test asserted a constant, so it could not fail. The bound requires a sample not conditioned on the verifier's own outcome; no collection protocol established that property. | Cross-family invariant audit | initial → `9c2fe62` (12:22), post-anchor | **Safety-mitigated, not property-verified.** The default is now `False`, direct computation and rendering test both declarations, and undeclared output says `NOT a bound`. A caller may still assert `sampling_unconditioned=True`; the sampling property itself is not checked, and the database path does not propagate the flag. | M (code and tests), A (sufficiency of the sampling condition) |
| A6 | Event schema: `ts` must be a valid timestamp | `validate()` checked the **format** of `ts` and required an explicit UTC offset. Both were impeccable. It never asked whether the value was true. Six consecutive trajectory events carry invented timestamps, drifting up to 2 h 15 m ahead of the wall clock. | The author, in the hour he documented a runner ignoring its own append-only invariant | to `cdd21f7` (04:13) | Repaired: `append()` refuses a `ts` more than 15 minutes from the clock, at append only | M |
| A7 | `AGENTS.md`: *never publish anything from the private corpora* | Declared in a governance file and enforced by nothing. Violated in the **initial commit**. The repository's own sweep was structurally incapable of finding it: the sweep searched for paths *prefixed* with a repository name, and the leak was the same paths written bare, with no prefix to search for. | Paid cross-family leak audit against 5,256 real corpus paths | `99e7e81` → `fafd1a6` = **100 commits, 16 h 08 m** | Repaired: a local pre-publication gate, `--require-corpora` so a missing corpus fails rather than skips | M |
| A8 | `V0-26`: a multi-contributor event must declare a distinct evidence class per contributor — the check for the rule the project is named after | `_check_evidence_class` returns early whenever `contributors` is absent, and nothing requires a multi-agent event to carry the field. We measured the trajectory: **9 of 96 events carry `contributors`; only 3 are multi-contributor.** 87 events are structurally exempt. This is the identical early-return bypass as A3, shipped seven hours after the write-up naming that shape. | This work | landed `f9b7e11` (11:04) → **still open** | **Open.** An opt-in invariant | M |
| A9 | ADR-0014 / `skills-mirror.yml`: `.claude/skills` is a symlink resolving to `../.agents/skills` | The workflow asserts on `ubuntu-latest` that the path is a symlink. Git stores it at mode 120000 and a Linux checkout materialises it, so the assertion largely restates the checkout mechanism. On the author's own machine `core.symlinks=false`, `test -L .claude/skills` fails, and the path is a **17-byte regular file** containing the literal text `../.agents/skills`. The invariant is false in the only environment any agent on this project runs in, and CI cannot see it. | This work | ADR-0014 → **still open** | **Open.** We measured all three facts on the worktree | M |
| A10 | ADR-0023: an admin merge that skips a gate appends to `gate-bypass-log.md` | The log cannot be non-empty, because the audited process has never run. The repository has 116 commits and **zero pull requests**; the four merge commits are local worktree merges. Four of the ADR's five declared checks were never implemented (only DCO exists). The log reads `(empty — no bypasses yet)`. It is empty for the wrong reason. | This work | ADR-0023 → **still open** | **Open.** ADR-0023's own overturn condition is precisely this case | M |
| A11 | `MIN_REJECTIONS = 30` as the evidence floor for a measured $\beta$ | 30 is exactly one below the smallest sample at which even a flawless record clears $\beta^\* = 0.111$. Using the repository's own Wilson function: $0/29 \to 0.11697$ (fails), $0/30 \to 0.11352$ (fails), $0/31 \to 0.11026$ (clears). At the evidence floor as set, **no outcome whatsoever** produces an interval clearing the threshold. | Same-family control audit | initial → **still open** | **Open, and correctly so.** We state fairly that this is not a bug: the constant gates the *measured* verdict, not a routing decision. What is undocumented is that no routing decision can ever be taken at the floor as set. | M, X |
| A13 | *"`mypy --strict` is clean"* — asserted in five internal documents as a standing property, and credited in the project's own autonomy table as the one defect-catching mechanism that is *"Now yes — CI gate"* | The check that found the defect is not the check that shipped. `invariants.yml` runs `python -m mypy src/consilience`, which loads the repository's `mypy.ini` — a configuration that enables `check_untyped_defs`, `strict_optional`, `warn_unreachable` and three warnings, and **none** of `disallow_untyped_defs`, `disallow_any_generics` or `warn_return_any`. Under that config the gate reports success. Under `--strict` it reports **21 errors in 3 files** at the anchor commit (14 `type-arg`, 4 `no-untyped-def`, 3 `no-any-return`) — and **19 errors** at `ffb3d60`, the commit whose message is *"make the check permanent"*, and 19 again at `32eacb8`, the commit whose write-up says strict was clean. It has never been clean. | This work, by running the command the documents claim | `ffb3d60` (01:40) → **closed post-anchor at `9fc6120`** | **Repaired post-anchor at `9fc6120` (closed).** All 32 strict errors across `src/consilient/` were resolved with zero `type: ignore`; `invariants.yml` now runs `python -m mypy --strict src/consilient` with an invariant test enforcing the `--strict` flag in CI. | M |
| A14 | `append()` is the sole writer of the trajectory log, and the only place `validate()` runs — the project's own chokepoint principle, applied to its own instrument | Nothing banned bypass, so the validator ran on almost nothing. We measured the log at the anchor commit: of the 93 events the projection accepts, **92 (98.9%) were written straight to the file by something other than `append()`**, and three of them carried a claim the validator forbids. This is working principle 3 — *a chokepoint without an enforcement rule is not a chokepoint* — reproduced inside the artefact the principle was written about, in the repository that declares it, within a day. | Found when the tightened `V0-18` (A3) made the reader raise on the first offending line and both `consil replay` and `consil beta` died on the real trajectory | initial → `03c239d` (10:17) | Repaired: refused lines are excluded **and named** with reason and line number rather than silently skipped or fatal; a rejection table so `state_digest` covers them; both commands report the count beside the figure; `events.bypassed()`; and a ratchet test grandfathering ≤92 bypassed and ≤3 refused, which may only fall. Its own documented ceiling: canonical-form comparison is a proxy — it catches hand-written JSON, the failure that actually happened, but not a bypassing writer that formats correctly | M |

**Table 1′ — Class A′: the inverse.**

| # | The guard | Why it could never pass | Status | Ev. |
|---|---|---|---|---|
| A12 | `V0-02`, ADR-0006 and ADR-0015 Gate A condition 2 all require **byte-identical** state after delete-and-replay | SQLite files are not byte-stable: the header carries a change counter and a schema cookie, freelist and page allocation depend on insertion history, and WAL adds a random salt. The shipped code already knew and had implemented a canonical ordered row-dump digest instead — so the documents specified an invariant the code correctly refused to implement, and the check that exists is *stronger* than the one written down. | The specification was corrected; **ADR-0006 line 137 and ADR-0015 line 115 still carry the impossible wording at the anchor commit** | M (code and text), C (SQLite non-determinism) |
| A15 | ADR-0015 Gate B condition 4 requires twenty tickets on another repository before Stage 3 | Stage 3 begins only after Gate B, but the condition requires twenty instances of Stage 3 behaviour. The conjunction is unsatisfiable as written: the evidence needed to pass the gate can be produced only after passing it. | **Open post-anchor at `f110882`.** ADR-0039 proposes a correction at `05bf3ac`, but is explicitly not accepted; only the principal may alter the gate. | M (text), X (circularity) |

**Table 2 — Class B: passes that carried no information.** Condensed; each is one paragraph in §4.2.

| # | The guard | Why the pass was uninformative | Status | Ev. |
|---|---|---|---|---|
| B1 | Overnight heartbeat reporting a long run as *running* | It inferred "running" from a byte count it could read, and the byte count was frozen precisely **because** the work had stopped. `complete` and `stop_reason` were sitting in the results file. A stalled artefact and a finished one look identical to a monitor that only reads the artefact's size. Reported *running* at two check-ins after both runners had exited. | Repaired `a2377f8` | M |
| B2 | `subprocess.run(..., timeout=T)` as the stop for a capped agent attempt | 26 of 66 attempts (39%) ran past the timeout; worst 1,771.7 s against a 240 s cap — **8.4×**. `TimeoutExpired` is not raised until surviving grandchildren release the pipes. So the outcome label `agent_timeout` does not mean the model exceeded the cap; it means the **stop failed**. Every duration-derived quantity from that run is void, and one causal gloss was withdrawn. | Repaired `fb2cdda` with process-tree kill and five tests **against real processes** — a mock of `subprocess` would have passed against the broken implementation | M |
| B3 | A single-instance lock, with five passing tests | `release_lock()` deleted a lock it never held. Eight minutes into a clean re-run the author launched a second runner to verify the lock worked; it refused correctly, then ran `release_lock()` in its `finally` block and deleted the live lock. **The act of testing the protection removed it.** All five tests released from the holder; not one exercised release from a process that had been refused — the only path where ownership matters. | Repaired `cbb5331` | M |
| B4 | "No duplicate cells" as evidence that an experiment ran once | All four experiment runners hold results in memory and rewrite the whole file per checkpoint: last write wins. Two runners ran into one results file all night, detected only because a start-up VRAM probe happened to differ between them. EXP-07 has no run id, no PID and no per-attempt timestamp, so no fingerprint exists to alternate: "no duplicates" is equally consistent with a clean run and an interleaved one, because the last writer's file is **coherent by construction**. EXP-07 is not condemned; it is unverifiable, which is worse than a visible compromise. | Recorded `d4d75f4`; runners not yet uniformly repaired | M |
| B5 | "CI red" as a verifier rejection, in the retrospective mining instrument | The instrument called a rollup green iff every conclusion was in `{SUCCESS, NEUTRAL, SKIPPED, None}`. `CANCELLED` falls outside, so a run that produced **no verdict at all** counted as the verifier rejecting. Aggregate counts on the primary corpus: 15 of 75 bad-and-red pull requests (20.0%) and 3 of 23 good-and-red (13.0%) failed only on cancelled runs. Reclassifying moves $\hat\beta$ from 0.6305 to 0.6809 and $\hat\alpha$ from 0.2371 to 0.2128 — **in opposite directions, from one correction.** Separately, an explicitly *informational*, non-blocking check reported failure on 5 pull requests and was counted as a rejection; no pull request failed on informational checks alone, so no further correction follows. All 242 non-passing check instances across both red cells carry `required = false`: on this corpus "CI red" never meant a required gate blocked the merge. | Recorded `a0c2833`; the instrument was deliberately **not** amended (see §6.4) | M, proxy-labelled |
| B6 | The revert arm of the label detector — **the contrast case** | It fired on **zero of 356** pull requests; all 224 bad labels come from the weak hotfix regex. The right response was a positive control, and it was run: 1,511 + 995 = 2,506 commits scanned, six revert-ish subjects, **none** carrying the PR reference the detector matches on. So the zero is a **true negative**, not a broken detector. These are fix-forward repositories and the strong signal does not exist in the corpus at all. That is worse news than a bug — a bug could be fixed. | Recorded `d43de31` | M |
| B7 | ADR-0002: *the decision rule's false-safe rate is 0 at every sample size tested* | An approximation transcribed as a guarantee, on a safety property, in the founding ADR. The ADR's own script prints 0.003 at $n=50$ and 0.001 at $n=100$ for a genuinely unsafe repository at $\beta = 0.15$, and its column note reads "must be ~0". A tilde was dropped. Exact binomial agrees with the script: $P(X\le1 \mid 50, 0.15) = 0.0029055$, $P(X\le5 \mid 100, 0.15) = 0.0015527$. Worse where it matters: at $\beta = 0.12$, barely above $\beta^\*$, the rate at $n=50$ is $0.0131$. The rule survives; the zero-error claim does not. | Corrected `272648d` | M, X |
| B8 | A blind grader's summary tally over randomised labels | Labels were randomised so each letter carried each arm exactly twice — perfect column balance. Both blind graders reported a near-flat letter tally and concluded the spread was noise. **Flat is exactly what a dominant arm produces** under that randomisation. The signal existed only after the key was applied, and the graders were correctly forbidden the key. Recoverable only because both also supplied per-item judgements. | Recorded; rule adopted | M |
| B9 | A newly written gate, run and reported as passing | It was piped into `tail`, which discarded the exit code, so a **failing** gate reported success and work continued on it. The repository is private, so nothing was exposed. | Corrected `33b753e` | M |
| B10 | An external project-management projection as a state store | A write of a state that does not exist in the target system was accepted with no error, leaving the record unchanged. A trajectory log would have carried the write as true. An external projection that cannot fail loudly is not a state store. | Recorded | M |

**Table 3 — Class C: a control that prevented a wrong answer.**

| # | The guard | What it prevented | Status and cost | Ev. |
|---|---|---|---|---|
| C1 | Parent-commit baseline in forward test replay | Five historical children failed a later monolithic suite, but every corresponding parent also failed. The pair classifier therefore marked all five as test-suite drift. Without the parent run, treating the five child failures as five escapes would have produced a counterfactual $\beta=5/5=1.0$. | Retained as a required control. It adds one checkout **and one test execution** per pair. | M (five child/parent FAIL/FAIL pairs), X (counterfactual) |

### 4.1 What the aggregate looks like

Three summary observations, all measured except the stated counterfactual.

**First: at every discovery, the suite was green.** The three defects of A1, A3 and A4 were found
after a 40-test suite passed and the static gate reported success. At the anchor, A5's defect had a
dedicated passing test — it asserted a constant. A3's fixture built forbidden events and every test
passed. B3 shipped with five passing tests.

The write-up of that audit states that `mypy --strict` was also clean at the time. **It was not**,
and we measured the correction while drafting this paper: at `32eacb8` the strict checker reports
19 errors in 3 files (A13). We considered mypy version drift as an alternative explanation and
reject it: all 19 errors are `type-arg`, `no-untyped-def` and `no-any-return`, which correspond to
`disallow_any_generics`, `disallow_untyped_defs` and `warn_return_any` — flags that have been part
of `--strict` for many major versions. We measured with mypy 2.3.1 and cannot rule out a small
version effect, but not one that turns 0 into 19.

**Second: the enforced fraction is 2 of 9.** An independent record of the same session
classified every error that occurred by what caught it. Two were caught by an enforced mechanism;
seven were caught only because an agent happened to look. That ratio is the honest summary of the
state of this system's self-verification, and it is measured, disputable item by item, and
registered as a baseline. It also carries its own failure mode, which the record names: the
enforced fraction can rise because errors stop being *counted* rather than because they stop
happening, so the denominator has to come from somewhere independent of the mechanism being
credited.

**Third: one control rejected the tempting result.** Five historical children failed a later test
suite and every parent failed too, so the classifier rejected all five pairs as drift. [measured]
Calling the child failures escapes without that baseline would have yielded $\beta=1.0$.
[algebra] The control is the same phenomenon from the useful side: it was seen fail in the exact
case it existed to distinguish, and its failure prevented an unsupported number.

### 4.2 Seven exhibits in longer form

**A5, and why the central quantity certified itself.** The programme's own $\beta$ result carried
`lower_bound_on_joint_error=True` by default, while its dedicated test asserted only that constant.
The bound requires sampling not conditioned on the verifier's own outcome, but no collection
protocol established that condition. [measured] The post-anchor repair at `9c2fe62` defaults the
claim to false and exposes an explicit declaration; it prevents accidental overstatement, but a
caller can still set the declaration without evidence and the database path currently drops it.
[measured] Whether an unconditioned sample is sufficient for the bound remains asserted rather
than measured. [asserted]

**A2 and A15, a gate broken in both directions.** Condition 2 compared a derived ceiling with a
threshold below its algebraic minimum, so it admitted every possible $\beta$. Condition 4 requires
twenty instances of behaviour that the same gate forbids until it has passed, so the full
conjunction admits none. [algebra] These are not empirical error rates: no labelled distribution
was sampled. They are opposite failures of discrimination in the same decision rule.

**C1, and the control that earned its cost.** A later suite failed at each of five historical
children, but it also failed at every parent. [measured] The parent baseline converted an alarming
but counterfactual $5/5$ into the recorded result: no evaluable parent-pass baseline and $\beta$
not applicable. [measured] One extra checkout without the extra execution would establish nothing;
the measured cost is both. [measured]

**A3, and why it is the one that mattered.** $\beta$ is *defined* as the rate at which the checks
accept an artefact **the human rejected**. If an agent can author the human verdict, $\beta$ is
not a measurement of anything — it is the agents grading themselves, which is the exact failure
the project is named to prevent, arriving through the data layer rather than through a meeting.
The check existed. It had a name and a number. It returned early on the only path that mattered.

The write-up of A3 then made its own error, which we record because it is the same species: it
demonstrated the hole with a forged `human_verdict: "accept"`, and that variant **does not move
$\beta$** — `compute()` takes its denominator from rows where the verdict is `reject`, so an
accept row changes neither numerator nor denominator. The forgery that actually attacks $\beta$ is
a forged `reject` paired with `verifier_accept: true`, which lands in both. The fix was right; the
severity argument was decorated with an example that does not support it. A test now pins which
variant moves the number. Picking the harmless variant to illustrate a genuine hole is a species
of overclaim, and naming it is cheaper than being caught at it.

**A7, and the check that flagged itself.** The private-corpus rule was declared in the governance
file from the first commit and enforced by nothing. It was violated in that same commit: detailed
internal paths, function and script identifiers, hook filenames, a verbatim quotation from a
private assessment document and a commercial product identity, in one source-material file, plus a
private path in one ADR and seven files naming a private document by filename. We describe the
leak only in class; the content is scrubbed and may not be reproduced.

The repair is the paper's best positive example and we give it in §6.3. Its coda belongs here: on
its **first run against the scrubbed tree, the new check flagged its own docstring — twice** —
because the docstring had used a real private path as its example of a distinctive one. That is
the check working, on itself, at the first opportunity, and it is left recorded in the source
rather than tidied away. In the same incident the check's output was piped into `tail`, discarding
the exit code, so a failing gate reported success (B9). Both facts are in the committed record.

**A11, stated fairly, because overclaim is the thing being corrected.** The evidence floor
`MIN_REJECTIONS = 30` is not a bug. It gates the *measured* verdict, not a routing decision, and a
$\beta$ measured at $n = 30$ is still a number. What the arithmetic shows is narrower and stranger:
against $\beta^\* = 0.111$, the number of rejections needed for the Wilson upper bound to clear the
threshold is 48 at a true $\beta$ of 0.02, 62 at 0.04, 137 at 0.06, 368 at 0.08, 3,045 at 0.10, and
**never** at $\beta \ge 0.111$, searched to 200,000. No routing decision can be taken at the
evidence floor as set, and nothing in the code or the specification says so. We report this as a
documentation defect and a real result about the decision rule, not as a defect in the constant.

**A13, the ratchet installed one notch below the claim.** This is the only entry discovered while
drafting this paper, and it was discovered by the paper's own recommended discipline applied to a
sentence rather than to code: we ran the command the documents say is clean.

The history is exact and it is the cleanest instance of the mechanism in §5.1. At 01:40 on 20
August, `mypy --strict` was run on a whim during an unrelated assessment and found a reachable
crash — `beta.render()` unpacked `self.interval` unconditionally, so a JSON round-trip carrying a
`measured` verdict with a null interval raised `cannot unpack non-iterable NoneType`. Twenty-four
passing tests had missed it, and the suite was *structurally* blind: $\beta$ on the real trajectory
is `insufficient_data`, so the measured render path was never exercised at all. The author's own
gloss is the best sentence in this corpus: *"That is $\beta$ in miniature, on our own code. The
automated check — a test suite written alongside the implementation by the same agent — accepted a
bad artefact. A different and stronger check caught it."*

The fix was correct and is exemplary: the invariant moved into `__post_init__` so the bad state
cannot be constructed, and `render()` restates it as an assertion so the checker can prove it. That
is a constraint, not a guard, and the crash cannot recur. **What went wrong is the ratchet.** The
commit is titled *"make the check permanent"*, and what was made permanent was `python -m mypy
src/consilience` under a `mypy.ini` that does not enable strict mode. The stronger check that
actually found the defect was never installed. Five documents then recorded, over the following ten
hours, that `mypy --strict` is clean — including the autonomy table that credits it as the single
mechanism now enforced, and the cross-family audit that uses it to establish how hard the three
defects of A1, A3 and A4 were to find.

We measured all of it: 19 strict errors at `ffb3d60` itself, 19 at `32eacb8`, 21 at the anchor
commit as the source grew from 636 to 972 lines (peaking at 32 errors). The gate is not worthless — it catches
`strict_optional`, `warn_unreachable` and untyped-def bodies — and we are not claiming the
repository is untyped. We are claiming that **the guarantee in the record was stronger than the
guarantee in the gate, and nothing in the system could have noticed**, because no check checked the
documents against the workflow. Post-anchor, this was resolved at `9fc6120`: all 32 strict errors
across `src/consilient/` were fixed with zero `type: ignore`, the CI workflow was updated to run
`python -m mypy --strict src/consilient`, and an invariant test was installed to ensure `--strict` cannot regress.

---

## 5. The mechanism

Most of Table 1 is one mistake made in thirteen places. We state it, then the two variants that
matter most.

### 5.1 The tests asserted the mechanism, not the property

Every guard has a *property* it exists to secure and a *mechanism* by which it secures it. The
property is a statement about states of the world: *a forged human verdict never reaches the table
$\beta$ is computed from*. The mechanism is a statement about code: *`_check_human_authority`
raises when `human_decision` is present and the actor is not the principal*.

A test that asserts the mechanism passes forever. It keeps passing when the code grows a second
path to the same state, because the second path never touches the mechanism. It keeps passing when
the mechanism's precondition stops holding, because the test supplies the precondition itself. It
keeps passing when the guarded quantity's range moves out from under the threshold, because the
threshold is still there and still compared.

This is the shape of A1 (the mechanism *compare two things* was intact; the property *the state on
disk matches the log* had no subject), A2 (the mechanism *compare $n_{max}$ to 1* was intact; the
property *$\beta$ constrains parallelism* was never true), A3 and A8 (the mechanism ran on a path
the property did not travel), A4 (the mechanism *check the fields are present* was intact; the
property *a measured verdict is evidenced* was not expressed), A5 (the mechanism is a constant),
A6 (the mechanism *the string parses* was intact; the property *the time is true* was never
asked), A9 (the mechanism *assert a symlink* was intact and ran only where the platform
guarantees it), and A13, where the property *the code passes the strict checker* was recorded in
five documents while the mechanism installed in CI was a weaker checker that has never been asked
the question.

The generalisation, and it is our judgement rather than a measurement: **a test written by the
author of a guard, in the same sitting, will assert the mechanism, because the mechanism is what
the author was thinking about.** The property is what the author *meant*, and meaning is not
executable. As one internal record puts it: the tests were not wrong; **they were shaped like the
author** — each time they exercised the path he had in mind while writing the code, which is by
construction the path he did not get wrong.

### 5.2 The permissive fixture

The sharpest single item in this corpus is a one-line rule we could not find stated anywhere in
the test-smell literature:

> **A test fixture that can construct a state the invariant forbids will train the suite to permit
> that state.**

It recurred three times in twelve hours, in three different files, from the same author. We
measured all three.

**Instance 1.** The `attempt.outcome` fixture built agent-authored events carrying
`human_verdict`. Every test passed. The fixture could express the forbidden state, so the suite had
been taught to accept it — and A3 shipped.

**Instance 2, and it is the diagnostic one.** When the clock check landed at 04:13, it immediately
failed **eleven existing tests**, because their fixtures hard-coded the exact timestamp shape the
new check forbids. Those eleven failures are the fixture problem made visible: the suite had been
built on a state the new invariant classes as impossible. When a new guard breaks many old tests,
the old tests were teaching the codebase the guard's negation.

**Instance 3.** The single-instance lock's five tests all released from the holder. Not one
exercised release from a process that had been refused — the only path where ownership matters —
so a `release_lock()` that never checked ownership passed cleanly, and then deleted a live lock in
production (B3).

**Why we think this is worth a paper rather than a footnote.** It is falsifiable, and it is
mechanically detectable without semantic understanding. A fixture is a constructor of states. An
invariant is a predicate over states. Running the invariant's predicate over the states the
fixtures construct is a static-ish, cheap analysis that requires no mutants and no oracle
inference: *does any test helper construct a state that any declared invariant would reject
outside a test marked as a negative case?* We have **not** built that detector and we do not claim
its results. Building it and running it over a public corpus is the obvious next step and it is
the difference between this section and a study (§8.3).

### 5.3 The environment that guarantees the property for free

A9 is a third variant worth naming separately, because it generalises to any project with CI. A
check that runs only where the property holds by construction is inert **and looks maximally
responsible**: it is in CI, it is green, it is cheap.

The skills-mirror workflow asserts on Linux that a git-tracked mode-120000 entry is a symlink.
Linux git materialises it as one. The assertion is nearly a restatement of the checkout mechanism.
Meanwhile on the developer's Windows machine `core.symlinks=false`, the path is a 17-byte regular
file, and the invariant is **false in the only environment any agent on this project actually runs
in** — an environment CI cannot observe. The workflow's own comment states the premise that fails:
"a symlink cannot drift, so the only failure mode is someone replacing it with a stale copy."

The rule that follows: **a check must run at least once in the environment where the property can
be false.** If no such environment is in the check's reach, the check is a description of the
platform, not a test of the system.

### 5.4 The process that never ran

A10 is the fourth variant: an audit artefact that is empty because the audited process has not
occurred. The gate-bypass log is empty after 116 commits — not because no gate was bypassed, but
because every load-bearing change landed directly and there were no pull requests to bypass a gate
on. Four of the ADR's five declared enforcement checks were never written.

Emptiness is the most deceptive success signal there is, and it has an exact precedent in the
prior-repository lessons this project's invariants are named after: a flagship pipeline in a
private commercial codebase had **no producer** — a scheduled job drained a queue nothing ever
filled, undetected because an empty queue is indistinguishable from a healthy one. The rule:
**an audit log must have a recorded non-empty case before its emptiness is evidence.**

### 5.5 The declared chokepoint with no rule banning bypass

A7 and A14 are the fifth variant, and it is the one this project had already written down before it
happened. Working principle 3 exists because of a lesson from a private commercial codebase: a
documented, unified model-access boundary was in practice five access paths, the circuit breaker
and kill switch covered roughly a dozen call sites while the highest-cost paths bypassed them
entirely, and the idea was right while the enforcement was never written.

The principle was recorded in this repository on 19 August and violated in it on both counts within
a day. A7 is the governance instance — a publication rule with no check, violated in the commit
that declared it. A14 is the code instance, and it is the sharper of the two because the chokepoint
was real: `append()` genuinely is the only place `validate()` runs, and 92 of 93 events simply did
not go through it. Nothing forbade the second path, so the validator's silence was not evidence of
anything.

The rule is the principle restated with the failure mode attached: **naming a sole writer does not
make it the sole writer; a check that runs only inside the chokepoint reports on the traffic that
used it.** The measurable form is the one the repair adopted — count the artefacts that did not
pass through, publish that count beside every figure derived from them, and ratchet it downward.

### 5.6 Where the mechanism does not apply

We do not claim the mechanism explains everything in Table 2. B1, B2 and B4 are a different
failure — a signal that reports a state it never verified — which the repository's own standing
rule already covers: *verify by artefact, never by exit code or process identity*. B5 and B6 are
measurement-instrument defects that belong to the mining literature (§7.1). B7 is a transcription
error. B8 is a design defect in a blinding protocol. Grouping all twenty-five defects under one mechanism
would be exactly the overclaim this paper is trying to avoid.

---

## 6. The discipline: falsification records

### 6.1 The rule

> **A guard is not a guard until it has been exhibited rejecting something, and the exhibit is
> stored.**

Operationally, eight clauses. None is novel in its insight, and we say so in §7.

1. **Every guard ships with a test that exhibits it failing.** Not only a test that it passes on
   good input. If you cannot write the failing input, you do not yet know what the guard checks.
2. **Every guard clause gets its own negative test.** An early return is a second guard with its
   own property (*this event is out of scope*). A3 and A8 are the same defect eight hours apart
   because the early return was never treated as a check in its own right.
3. **A threshold must be exhibited on both sides.** Produce one input above and one below. A2
   would have died in seconds: no value of critic recall produces $n_{max} \le 1$, and trying to
   construct one is how you find out.
4. **A fixture may not construct a state an invariant forbids**, except inside a test explicitly
   marked as a negative case. When a new invariant breaks many existing tests, treat that as a
   finding, not as churn (§5.2, instance 2).
5. **Run the check at least once where the property can be false**, on the platform, in the
   configuration and against the corpus where it might not hold (§5.3).
6. **Record the exhibit.** The falsification is the artefact. A green tick from a check that has
   never been seen red is a claim without evidence, and this project's whole discipline is that
   claims carry evidence.
7. **Ratchet at the strength of the check that found the defect, and write down the invocation, not
   the tool.** A13 is the whole argument for this clause: a defect found by `mypy --strict` was
   ratcheted into CI as `mypy`, and the record then described the gate by the name of the check
   that found the bug. Where the two differ, the artefact — the exact command line the workflow
   runs — is the claim, and the prose must quote it.
8. **Replay the parent under the same future check before calling a child failure a defect.** A
   later test suite is evidence only when it passes immediately before the change it is meant to
   judge. C1 shows the control rejecting five tempting classifications as drift.

### 6.2 Cost

We can bound the cost only from this corpus, and the bound is weak, but it is the honest number:
one extra test per guard, and in the three repairs where it was applied deliberately the marginal
work was five or six tests total. The repairs at `32eacb8` shipped five tests for A3 and six for
A4. The replacement for A2 (ADR-0037) shipped an executable model with five tests, and we ran it:
it exhibits both a PASS row ($\beta = 0.630$, +20.0% review throughput) and a FAIL row
($\beta = 0.700$, +15.6%). **The gate is now proven to discriminate**, which is exactly clause 3
discharged and exactly what the old gate never had.

The cost that is not one extra test is clause 5. B2's repair required five tests **against real
processes**, and the record names why: *a mock of `subprocess` would have passed against the broken
implementation, because the defect is that the real thing does not behave as the API suggests.*
One of those tests deliberately reproduces the original defect and fails if it ever stops
overrunning. That is expensive, slow, and the only test that could have caught it.

C1 also corrects the slogan “one extra test per guard”. Its parent baseline adds one checkout and
one execution of the same suite per historical pair. [measured] The checkout alone carries no
verdict; omitting the execution recreates the defect the control prevents. [algebra]

### 6.3 The worked example, including the part where it failed

The private-corpus gate (A7) is the one case in this corpus where the discipline was applied
before the check was trusted, and it is instructive precisely because the check failed its own
first falsification.

1. The check was written to compare this tree against the real file inventories of the two private
   corpora.
2. **It was run against the pre-scrub tree** — the state it should reject. The first threshold
   chosen caught **2 of the 5** known path references, because one path is 15 characters and
   slipped under a minimum-length filter.
3. Thresholds were adjusted (`MIN_DEPTH = 3`, `MIN_LEN = 12`) and re-run against the pre-scrub
   tree until it reported all five.
4. Only then was it run against the scrubbed tree, where it exits 0 — and where, on that first
   run, it flagged its own docstring example twice (§4.2).

Steps 2 and 3 are the falsification record. Without them the gate would have shipped catching 40%
of the known leak and reporting clean, which is the worst possible state: an inert check over a
rule the project cannot afford to break.

Its known ceilings are documented in the source rather than discovered later, which is the other
half of the discipline: it matches **file paths only**, so a leaked function name, CI job name or
commit subject passes; it compares against the corpora's current HEAD, so a since-deleted path is
not in the needle set; and it hard-codes two absolute Windows paths, so it runs on exactly one
machine. It is deliberately **not** a CI job, because the corpora are not on a runner and a check
that silently no-ops is worse than none — hence `--require-corpora`, which makes a missing corpus
a failure rather than a skip.

### 6.4 One protocol choice that looks like a defect and is not

The retrospective mining instrument behind B5 and B6 has never been amended. It still prints a
single transposed ratio, still classifies `CANCELLED` as red, and still discards per-check
identities. This is deliberate: the experiment was under a live audit, and repairing an instrument
mid-run after seeing what it produced is outcome-aware tampering. The corrections live in three
separate read-only scripts that recompute from the retained records without touching the miner.
The consequence — that the raw recorded outputs and the current best estimates live in different
files — is a real cost and we record it as one. **The falsification-record discipline applies to a
check before it is trusted, not to an instrument after it has produced a number you dislike.**

---

## 7. Positioning: what is old here, and what is not

We take the strongest objection first, in the words a hostile reviewer would use.

> *Vacuity detection is 29 years old, mutation testing is 48, OASIs already assesses oracle false
> negatives and improves fault detection by 48.6% on average, checked coverage already flags
> oracles that check nothing, and a July 2026 paper already showed self-authored verification
> cannot close its own gap and proposed an exogenous audit. You have roughly twenty anecdotes from
> a single repository, found by a review of your own code, with no detector, no baseline and no
> corpus.*

Every clause of that objection is true today, and we accept it. What follows is what we think
survives it, stated as narrowly as we can make it.

### 7.1 What is retired

- **"A check that passes for a reason that makes it uninformative" is vacuity** [3, 12, 13]. A2 is
  vacuous satisfaction — a threshold below the algebraic floor of the quantity it gates. A1 is a
  vacuous witness. We use the word deliberately; framing these as a new phenomenon would be wrong.
- **"Can this check fail?" is mutation testing's founding question** [7], and the tooling already
  fails builds on the answer (PIT's `mutationThreshold`, Stryker's `thresholds.break`) [C, snippet
  level]. Oracle assessment has a dedicated technique for oracle false negatives specifically
  [11], and checked coverage is a cheaper instrument for the same question [18, 19].
- **The self-verification framing is occupied.** Guo et al. [9] define the verifier–deployment gap
  for agents that control both policy and tests, prove that self-authored constraints cannot close
  it, and propose a sealed exogenous acceptance loop. That is an independent derivation of this
  project's own exogenous-signal rule, published a month before this draft, **with measurements**.
  We must cite it, and our distinction from it is real but thin: their corpus is self-play with
  agent-authored tests, and ours is a human-directed governance layer where the guards were inert
  as written and no adversary had to defeat anything.
- **"Verifiers for coding agents are weak" is saturated and better funded** [16, 20]. We contribute
  nothing to it and do not claim to.
- **B5 and B6 are known hazards in mining research.** The label-proxy failure is SZZ noise
  [10, 21, 4]; the never-firing revert arm is linkage bias [4]; the size effect behind the
  bad-and-red cell is why SZZ implementations filter bulk commits. The correction arithmetic used
  on that corpus is a hand-rolled Rogan–Gladen estimator [17] — with, we believe, the wrong
  interval, because it propagates Wilson bounds on raw counts rather than accounting for
  uncertainty in the $n=15$ and $n=5$ correction factors. We flag that as a defect in our own prior
  work.

### 7.2 What we think survives, narrowly

**First, the objects.** Vacuity is defined over temporal-logic properties and needs a model
checker. Mutation testing is defined over program source and needs mutants. Checked coverage is
defined over a dynamic slice reaching a test oracle. **None of the three is defined over the
objects that broke here**: an ADR gate condition stated in English and marked *satisfied*; a
replay invariant over an append-only log; a dataclass admission constructor; a CI workflow
assertion about a checkout artefact; a publication rule in a governance file; a boolean field
asserting a mathematical property. A governance layer has no model checker and no mutants, and
that is where the majority of this catalogue lives. We judge this to be the honest delta and it is
a modest one.

**Second, the permissive-fixture rule** (§5.2). The test-smell literature catalogues Assertion
Roulette and Mystery Guest [23], documents bugs in test code empirically [24], and now measures
smells in LLM-generated suites at scale [25]. We could not find *a fixture able to construct a
state its own invariant forbids will train the suite to permit that state* stated in any of it. It
is falsifiable and mechanically detectable, and it explains A3 directly.

**Third, the corpus property.** This repository recorded its own guard failures **as they
happened**, including the ones its author committed *after* documenting the class — A8 shipped
seven hours after a write-up naming the early-return shape, and V0-18 was violated three times by
its own author in the hours after he tightened it. That is a craft contribution and an experience
report, not a research result, and we pitch it as one.

**What we explicitly do not claim.** No prevalence. No rate. No comparison against a baseline. No
claim that a different model family finds these better than the same family — that claim was made
in this project on 20 August and **withdrawn within four hours by its own pre-registered control**,
which found the same defect in the same file from a same-family arm and also recovered the other
arm's contribution (§8.5). We restore none of it.

---

## 8. Threats to validity

We put the worst first.

### 8.1 We wrote the defective checks, and we selected the catalogue

Every entry was found by the people and processes that produced the defect, and every entry was
recorded by them. There is no independent enumeration. The catalogue's **denominator is unknown**:
we can say twenty-five defective guards exist, and we cannot say what fraction of the
repository's checks that is, because the only census available is the one performed by the author
of the census's subject.

This cuts two ways and we state both. It is a strength for *existence*: these are not
reconstructions or inferences from a bug tracker; we have the commit that introduced each defect,
the commit that repaired it where repaired, and in most cases the write-up made within hours. It
is fatal for *rate*: a self-audit finds what the auditor knows to look for, and the last five
entries in Table 1 were found only after the first six had taught us the shapes. A9, A10 and A8 in
particular were found by pattern-matching against a class we had just named — which is exactly how
selection bias operates.

**A reviewer should treat every count in this paper as a lower bound on existence and as no
evidence at all about frequency.**

A13 sharpens both halves of that. It is evidence that the catalogue is a lower bound, because it
was found *during the writing of this paper* by the crudest possible application of §6 — running
the command the prose claims — after four separate audits by three model families had passed over
the same repository, one of which asserted the false claim in its own findings. It is also evidence
for the selection worry, because we only ran that command because §6 told us to, and there is no
reason to think the class of claims we thought to check is representative.

### 8.2 n = 1, and a very unusual 1

One repository, 116 commits, seventeen hours of recorded history, one developer, heavy AI
assistance in both the code and the audits. Product source is 972 lines. The system's declared
purpose is verification, which plausibly makes it *more* densely checked than average and
therefore both a harder case (more checks survived scrutiny) and an unrepresentative one (more
checks exist to be inert). We cannot tell which effect dominates and we do not guess.

The "survived the full life of the repository" figures are seventeen hours. In a mature codebase
the equivalent exposure would be years, and we have no basis to claim the mechanism scales that
way.

### 8.3 Mutation testing cannot mechanically generate this catalogue (EXP-48)

The permissive-fixture rule is the paper's strongest claim and it rests on three instances from one
author in twelve hours. We assert it is mechanically detectable; **we have not built the specialized fixture detector
and have measured nothing outside this repository.** Until that is done, §5.2 is a hypothesis with
three supporting cases, and a reader is entitled to discount it accordingly.

The cheapest potential falsifier — asking whether standard mutation testing over this repository's
codebase identifies the same inert guards, which would render §6 a forty-eight-year-old re-derivation —
was executed in EXP-48 (`mutmut` 3.7.0 against the 1,931 first-order mutants from EXP-47). The result
is decisive: **overall recall was only 20.00% (5/25 recovered)**, far below the 35% equivalence threshold.
68.0% (17/25) of the catalogued guards live completely outside program mutation testing (ADR specifications,
CI workflows, governance rules, and research runners). For the 8 code-resident guards, recall was 62.5% (5/8);
the three missed code guards (A4, A5, A11) had zero surviving mutants because fixing an inert check kills
the very mutants that would have detected it (the regression-test masking paradox). Cluster precision
was also low (24.59% — 15/61 clusters).

This result **strengthens P2**: its manual catalogue method is structurally necessary rather than merely
first; vacuity in socio-technical governance cannot be mechanically generated by syntactic mutation testing.

### 8.4 The catalogue is self-reported from documents written by the same process

Most entries are anchored to a write-up produced by the same agentic process that produced the
defect. We mitigate with commit hashes, timestamps and — for thirteen entries — live re-verification
at the anchor commit, including running the meter, the replay check, the suite, both mypy
invocations at three commits, the private-corpus gate, the Wilson arithmetic and the exact
binomial. Six entries in Table 2 are **not**
independently re-verified in this draft and rest on the committed record: B1, B4, B8, B9, B10 and
the timeout multiplier in B2. We mark that here rather than let a uniform citation style imply
uniform verification.

### 8.5 Discovery-mode attribution is confounded and one claim was withdrawn

Table 1 attributes several findings to a cross-family audit. **That attribution is not evidence
that a different model family finds these better.** The project made exactly that claim on 20
August and withdrew it four hours later when its own pre-registered same-family control fired: a
same-family arm found the same defect in the same file and independently reproduced the other
arm's counterexample. The withdrawal names six reasons, and the first is fatal — the blind leaked
because the control was told to read a repository whose committed trajectory log contained the
finding in plain text, and the orchestrator had put it there. *You cannot run a blind experiment
inside the repository you are writing your findings into.*

One instance in this corpus is a better case, and we state it as a difference of **method grounded
in different facts** rather than a difference of brand: the leak auditor (A7) introduced an
exogenous signal — 5,256 real paths from the private corpora — that the orchestrator's own search
never touched, and the orchestrator's angle could not have found the leak however carefully it was
run. That is n = 1, unmatched arms, and family confounded with the needle corpus, which is the
same confound that killed the first claim. We name it rather than repeat the mistake.

There is one further live risk in the source material a reviewer would find: an unretracted "first
genuine consilience event" claim survives in one internal document, structurally identical to the
withdrawn one, with no control. **We do not use it and we flag it here as unretracted.**

### 8.6 The classification is a judgement, and the boundary is soft

Whether A11 (an evidence floor no outcome can clear) belongs in "cannot fail" is arguable; we
include it with an explicit statement that it is not a bug. Whether A12 belongs at all is arguable;
it is the inverse case and we count it separately. B5's informational-check finding is true of
check *instances* and moves no pull request out of the red cell, and a reader who skims could take
it as a further correction to $\alpha$ or $\beta$. **It is not**, and the adjudication script's own
output says so.

### 8.7 The motivating quantity is unmeasured, and the corpus behind it is private

$\beta$ has never been measured with sufficient data in this system. The meter reports
`insufficient data` at the anchor commit and has received zero prospective rows. The retrospective
figures quoted in B5 and B6 rest on a proxy whose audited precision is 1 in 15 on 40 sampled
labels, measured only on one cell of the contingency table and propagated to a denominator
containing 75 unaudited pull requests from the cell where the proxy is least reliable — their
median file count is 2.6× larger. The corpus is 356 merged pull requests from two private
commercial repositories written largely by one developer with heavy AI assistance. **None of the
paper's claims depend on those figures**, and where they appear they are labelled proxy-based.

### 8.8 The branch moved while this was written

Two exhibits (A2, A8) were repaired by a parallel session at 11:01 and 11:04 on the day of
writing, and A8's repair introduced the new defect recorded in Table 1. Table 1's status column is
correct at `81e7143` and will decay. A separate commit that normalised line endings across the
tree inflates one of those diffstats to roughly 2,000 lines; that number is **not** the size of the
change and should not be quoted as such.

### 8.9 Conflict of interest

The author is building the system under study and has an interest in it appearing rigorous. The
mitigation we can offer is that the catalogue's contents are uniformly unflattering and that the
repository's history preserves the defects, wrong claims and withdrawals in an append-only record.
At the anchor, A5, A9, A10 and A13 were reported **open** rather than repaired; post-anchor, A5 was
safety-mitigated (though still does not verify its sampling property), and A13 was resolved at `9fc6120`
by fixing all 32 strict mypy errors with zero `type: ignore` and enforcing `--strict` in CI. [measured]

---

## 9. Related work

Read depths are flagged, because this project's own worst prior error was a "no prior art found"
claim built on a search of one field. **[FULL]** = read in full or near-full; **[ABS]** = abstract
page read; **[SNIP]** = search-snippet level only, and not admissible as support for a load-bearing
claim.

**Vacuity and sanity checking.** Beer, Ben-David, Eisner & Rodeh [3] and Kupferman & Vardi [12]
define vacuous satisfaction and interesting witnesses; Kupferman [13] generalises to sanity checks
in formal verification. **[SNIP]**. This is the correct name for A1 and A2 and we adopt it. What
does not transfer is the instrument: vacuity detection presupposes a formal property and a model
checker, and a gate condition in an ADR has neither.

**Mutation testing and oracle assessment.** DeMillo, Lipton & Sayward [7]; Jahangirova, Clark,
Harman & Tonella [11] (OASIs, combining test generation for oracle false positives with mutation
for oracle false negatives, reporting a 48.6% average increase in fault detection after
improvement); Schuler & Zeller [18, 19] (checked coverage as a more sensitive oracle-quality
indicator than mutation score). **[SNIP]**. This is the baseline §6 will be measured against, and
§8.3 names the experiment that would retire §6 outright.

**Test smells.** van Deursen, Moonen, van den Bergh & Kok [23]; Vahabzadeh, Milani Fard & Mesbah
[24]; and recent measurement of smells in LLM-generated suites [25]. **[SNIP]**. Closest prior art
to §5.2 and, to our search, not containing it.

**Self-verification in agentic systems.** Guo et al. [9] **[FULL]** is the nearest live threat and
an independent derivation of this project's exogenous-signal rule. The Qwen Team's verification
survey [16] **[FULL]** and the reward-hacking literature [20] **[SNIP]** establish that verifiers
for coding agents are weak; we contribute nothing there, and we distinguish our failure mode
explicitly: **the guard could not have failed under any input, so no adversary and no distribution
shift is required to explain it.**

**Harness optimisation.** Meta-Harness [14] **[FULL, in-repo]** automates search over harness code
and already audits its objective signal for regex leakage — mitigating *leakage* while ignoring
*weakness*. The position this project takes is that it is Meta-Harness's missing precondition, not
its rival, and that position is unchanged by this paper.

**Defect-label mining.** Herbold, Trautsch, Trautsch & Ledel [10] **[ABS]**; Tantithamthavorn et
al. [21] **[SNIP]**; Bird et al. [4] **[SNIP]**; Rogan & Gladen [17] **[SNIP]**. These retire the
general form of B5 and B6, as stated in §7.1.

**Verifier false-accept on agent-emitted artefacts.** SWE-Bench+ [1] **[ABS]** found 31.08% of
passed patches suspicious because tests were too weak; a large evaluation-methodology survey
[15] **[FULL]** reports maintainer merge rates averaging 24.2 percentage points below automated
grader scores for the same pull requests. Neither is our measurement, and this paper claims no
measurement of $\beta$.

**Correlated verifiers.** Knight & Leveson [8] **[SNIP]**; Kohli [5] **[FULL]** measures nine
frontier judges from seven families as worth $n_{eff} = 2.18$ effective votes, with the best single
judge matching or beating the panel. Ao, Gao & Simchi-Levi [2] **[ABS]** prove that without new
exogenous signals a delegated network is dominated by a single decision-maker with the same
information. Together these are why §8.5 is a withdrawal rather than a result.

**Platform-level inert checks.** Practitioner reports document that a *required* GitHub status
check which is skipped — because a dependency failed or a path filter excluded it — is not reported
as failing, leaving the pull request mergeable [6] **[SNIP, practitioner sources]**. We found no
academic treatment. That is a second, non-self-referential instance of a guard that cannot fail,
and it is one of the few places where this paper's subject has a life outside our own repository.

---

## 10. Conclusion

We built a system to measure how often automated checks accept bad artefacts, wrote down a rule
that every invariant must ship with its enforcement, and then shipped thirteen checks that could not
fail — one of them the check for the rule the project is named after, one of them a passing test
asserting an unevidenced mathematical claim, and one of them the type gate that the project
credits, in its own table, as the single mechanism it has successfully ratcheted. Each was found
with a green suite behind it. At the anchor, six of the thirteen were open: A5, A8, A9, A10, A11
and A13. Post-anchor, A5 was safety-mitigated and A13 was resolved at `9fc6120`; the other four statuses are not silently refreshed in
this anchored catalogue. [measured]

The inverse cases sharpen the result: one gate simultaneously contained a condition that admitted
every possible value and a condition whose evidence could be produced only after the gate passed.
[algebra] The positive control shows the other side: five alarming later-suite failures were
classified and excluded as drift because every parent failed too. [measured]

The mechanism is that tests assert mechanisms and properties are what we meant. The variant that
worries us most is the permissive fixture, because it is silent, self-reinforcing and — unlike the
others — a candidate for mechanical detection. The discipline is one extra test per guard, pointed
at input the guard should reject, with the exhibit stored: mutation testing's question, asked of
governance objects that no existing instrument covers.

We report no rate, no prevalence and no comparison. We are the authors of the defects, the
repository is seventeen hours old, and the one claim this project made about a different model
family finding these better was withdrawn by its own control within four hours. What we can offer
is the catalogue, anchored; the mechanism, stated so it can be attacked; and the cheapest possible
next step, which is to build the fixture detector and run it somewhere that is not ours.

<!--
Decision record — 20 August 2026
Reasoning: retain A5 as an existing defective instance with a post-anchor mitigation; add the
unpassable gate condition as A15 and the parent baseline as positive control C1. This yields 25
defects plus one control without counting A5 twice.
Alternative not taken: count both new briefs as additional defective guards. That would inflate the
catalogue to 27 and misclassify the successful parent control.
Reversal: git restore --source=b27906d -- docs/50-publications/P2-guards.md
Falsifier: withdraw the recount if a source-anchored enumeration does not reproduce 13 Class A,
2 Class A-prime and 10 Class B defects, or if the retained replay records contain an evaluable
parent-pass baseline among the five monolithic pairs.
-->

---

## Data availability

**Released.** The product source (`src/consilient/`), the test suite, the
CI workflows, the private-corpus gate (`.github/scripts/check_private_corpus.py`), the four
read-only analysis scripts for the retrospective study, and every decision record and finding cited
in Tables 1–3 are in the repository this paper is drafted in. All live checks reported here —
`consil beta`, `consil replay --json`, `pytest`, both mypy invocations at three commits, the
private-corpus gate, the Wilson bounds of A11 and the exact binomial figures of B7 — run from a
clean checkout with no private data. The private-corpus gate is the one exception: it requires the
corpora to be present and will fail rather than skip without them, which is deliberate.

**Not released, and never will be.** The measurement corpora are two private commercial
repositories. Their code, file contents, excerpts, detailed file paths, CI check names, pull
request titles and commit subjects appear nowhere in this paper and may not be published. Four
gitignored artefacts (the mined pull-request records, the label audit sample and the re-fetched
check evidence) live only on the author's machine, and consequently **no figure in §4 that derives
from that corpus can be independently reproduced.** The mining figures are published only as
aggregate contingency cells:

**Table 4 — the aggregate tables, published in full; nothing finer may be released.** Labels are
proxy-derived (hotfix heuristic; audited precision 1/15 on 40 sampled labels).

| Corpus | merged PRs | bad·green | bad·red | bad·no-CI | good·green | good·red | good·no-CI |
|---|---|---|---|---|---|---|---|
| Primary (strongly checked) | 300 | 128 | 75 | 0 | 74 | 23 | 0 |
| Secondary (weakly checked) | 56 | 18 | 3 | 1 | 24 | 4 | 6 |

Seven pull requests in the secondary corpus have no recorded checks, which is why its denominators
appear as both 21 and 22, and both 28 and 34, in different documents. Any figure derived from these
cells must state which treatment it uses in the same sentence as the number.

**The reproducibility gap this creates is real and it is the project's own policy problem, not the
reader's.** The publication policy already requires a public replication before a private-corpus
result may clear a formal-paper gate. The obvious repair — re-running the mining instrument on a
public corpus of agent-authored pull requests, of which several now exist at greater scale — has
not been done.

## AI-assistance disclosure

Large language models were used extensively in the work this paper reports and in the preparation
of the paper itself. Specifically: the system under study was implemented largely by Claude
(Anthropic) under the author's direction; the audits that discovered most of the catalogue were
performed by Claude, by Cursor running Gemini, and by Codex running a GPT-family model; this draft
was composed by Claude Opus from an evidence base assembled by several agent sessions, and every
load-bearing figure in it was re-verified against the repository by running the relevant script or
command.

No AI system is an author. arXiv, and the venues this work might be submitted to, are explicit
that authorship requires a human who takes responsibility for the content, and this paper is
consistent with that. The defects catalogued here were, without exception, introduced by an
AI-assisted process and found by an AI-assisted process, and §8.1 and §8.5 state what that does to
the evidence.

## Author responsibility statement

**Joe Brown is the sole accountable human author and the only submission principal.** He is
responsible for originality, accuracy, rights, privacy, ethics and correction. This draft is not
submitted, not circulated, and carries no approval. No agent may submit it, transmit it, or
represent it as approved. Before any submission the author must understand the claims and methods,
reproduce or inspect the retained evidence sufficiently to exercise scientific judgement, and
approve every claim and disclosure in it.

---

## References

[1] *SWE-Bench+: Enhanced Coding Benchmark for LLMs.* arXiv:2410.06992. **[ABS]**

[2] Ao, R., Gao, J. & Simchi-Levi, D. *Delegation and information in multi-agent LLM networks.*
arXiv:2603.26993, 2026. **[ABS]**

[3] Beer, I., Ben-David, S., Eisner, C. & Rodeh, Y. *Efficient detection of vacuity in ACTL
formulas.* CAV 1997; *Formal Methods in System Design* 18(2):141–162, 2001. **[SNIP]**

[4] Bird, C., Bachmann, A., Aune, E., Duffy, J., Bernstein, A., Filkov, V. & Devanbu, P. *Fair and
balanced? Bias in bug-fix datasets.* ESEC/FSE 2009. See also Bachmann et al., *The missing links:
bugs and bug-fix commits*, FSE 2010. **[SNIP]**

[5] Kohli, S. *Nine judges, two effective votes: correlated errors undermine LLM evaluation
panels.* arXiv:2605.29800, 2026. **[FULL]**

[6] GitHub community discussions #102709 and #48751; `actions/runner` issue #2566; practitioner
write-ups on skippable required status checks. **[SNIP, practitioner sources; no academic
treatment located]**

[7] DeMillo, R. A., Lipton, R. J. & Sayward, F. G. *Hints on test data selection: help for the
practicing programmer.* *Computer* 11(4):34–41, 1978. **[SNIP]**

[8] Knight, J. C. & Leveson, N. G. *An experimental evaluation of the assumption of independence
in multiversion programming.* *IEEE TSE* SE-12(1):96–109, 1986. **[SNIP]**

[9] Guo, Cao, Yuan, Wang, Wang & Wang. *Self-authored verification is unreliable in heuristic
self-improving agents.* arXiv:2607.24300v1, 27 July 2026. **[FULL]**

[10] Herbold, S., Trautsch, A., Trautsch, F. & Ledel, B. *Problems with SZZ and features: an
empirical study of the state of practice of defect prediction data collection.* *Empirical Software
Engineering*; arXiv:1911.08938. **[ABS]**

[11] Jahangirova, G., Clark, D., Harman, M. & Tonella, P. *Test oracle assessment and improvement.*
ISSTA 2016; OASIs tool demo, ISSTA 2018. **[SNIP]**

[12] Kupferman, O. & Vardi, M. Y. *Vacuity detection in temporal model checking.* 1999/2003.
**[SNIP]**

[13] Kupferman, O. *Sanity checks in formal verification.* CONCUR 2006. **[SNIP]**

[14] Lee, Nair, Zhang, Lee, Khattab & Finn. *Meta-Harness: end-to-end optimization of model
harnesses.* arXiv:2603.28052; COLM 2026. **[FULL, verified in-repo]**

[15] Meng et al. / METR. *Evaluation methodology for agentic software engineering.* v4, 111pp.
**[FULL]** — note: this source's "compositional verification" is separation-logic proof
composition and must not be cited as a verifier-error-rate result.

[16] Qwen Team. *The verification horizon: no silver bullet for coding agent rewards.*
arXiv:2606.26300, 24 June 2026. **[FULL]**

[17] Rogan, W. J. & Gladen, B. *Estimating prevalence from the results of a screening test.*
*American Journal of Epidemiology* 107(1):71–76, 1978. **[SNIP]**

[18] Schuler, D. & Zeller, A. *Assessing oracle quality with checked coverage.* ICST 2011.
**[SNIP]**

[19] Schuler, D. & Zeller, A. *Checked coverage: an indicator for oracle quality.* *STVR*, 2013.
**[SNIP]**

[20] *Reward hacking in RLVR* (arXiv:2604.15149) and *Fuzzing RLVR verifiers* (arXiv:2606.01066).
**[SNIP]**

[21] Tantithamthavorn, C., McIntosh, S., Hassan, A. E., Ihara, A. & Matsumoto, K. *The impact of
mislabelling on the performance and interpretation of defect prediction models.* ICSE 2015.
**[SNIP]**

[22] Whewell, W. *The Philosophy of the Inductive Sciences, Founded Upon Their History*, Vol. II.
London: John W. Parker, 1840. Restated in *Novum Organon Renovatum*, 1858, pp. 70–71. **[FULL, the
definition]**

[23] van Deursen, A., Moonen, L., van den Bergh, A. & Kok, G. *Refactoring test code.* 2001.
**[SNIP]**

[24] Vahabzadeh, A., Milani Fard, A. & Mesbah, A. *An empirical study of bugs in test code.* ICSME
2015. **[SNIP]**

[25] *On the diffusion of test smells in LLM-generated unit tests.* arXiv:2410.10628; TOSEM 2026.
**[SNIP]**

---

## Appendix A — reproduction

Every command below was run at commit `81e7143` on branch `worktree-consilience-cto`, 20 August
2026, and its output is quoted in the paper.

```bash
# §2: the meter has received zero rows
PYTHONPATH=src python -m consilience.cli beta
# -> beta [all]: insufficient data (0 human rejections, need 30)

# §4: A1 repaired, A3's quarantined lines, A14's bypass count
PYTHONPATH=src python -m consilience.cli replay --json
# -> compared:true identical:true events:93 not_written_by_append:92
#    quarantined: 3 (lines 62, 63, 66 — V0-18 violations by the author)

# §2, §8.2: suite green at the anchor commit
python -m pytest -q                            # -> 62 passed in 0.44s

# §4, A13: the gate that runs, and the gate the documents claim
python -m mypy src/consilience                 # -> Success: no issues found in 5 source files
python -m mypy --strict src/consilience        # -> Found 21 errors in 3 files
# and at the two commits that claimed it was clean:
git archive ffb3d60 src mypy.ini | tar -x -C /tmp/a && (cd /tmp/a && python -m mypy --strict src/consilience)
# -> Found 19 errors in 3 files
git archive 32eacb8 src mypy.ini | tar -x -C /tmp/b && (cd /tmp/b && python -m mypy --strict src/consilience)
# -> Found 19 errors in 3 files

# §4, A7: the private-corpus gate, which requires the corpora to be present
python .github/scripts/check_private_corpus.py --require-corpora   # -> exit 0

# §4, A9: the skills mirror is false on this machine
git config core.symlinks     # -> false
test -L .claude/skills       # -> fails
wc -c .claude/skills         # -> 17

# §4, A10
git rev-list --count HEAD    # -> 116
```

**A11 (Wilson bounds, using the repository's own `wilson()`):** $0/29 \to 0.11697$;
$0/30 \to 0.11352$; $0/31 \to 0.11026$; against $\beta^\* = 0.111$.

**A2 (the algebraic floor):** with $T_a = 25$, $T_r = 8$, $n_{max} = T_a/(f T_r)$ and
$f = p_g + (1-p_g)(1-r)$, evaluating over $r \in \{0, 0.5, 1\}$ and $p_g \in \{0, 0.55, 1\}$ gives a
minimum of exactly $3.1250$ and never a value $\le 1$.

**B7 (exact binomial):** $P(X \le 1 \mid n=50, p=0.15) = 0.0029055$;
$P(X \le 5 \mid n=100, p=0.15) = 0.0015527$; $P(X \le 1 \mid n=50, p=0.12) = 0.0130990$.

**A8 (trajectory census):** across `.harness/log/*.jsonl`, 96 events; 9 carry `contributors`; 3 are
multi-contributor. The remaining 87 return early from `_check_evidence_class`.

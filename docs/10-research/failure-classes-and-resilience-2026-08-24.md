# Failure classes and resilience — the deductive half

**Date:** 24 August 2026 · **Status:** PROVISIONAL · **Audience:** the principal, and the
next agent to touch `.harness/`

This document answers a question asked on 24 August 2026: what could break this system that
has *not yet* broken it. The inductive half — six failure classes measured on this machine on
23–24 August — is being reduced to root causes elsewhere and is used here only to calibrate.
What follows is the deductive half: classes drawn from published taxonomies, each with the
component here that is exposed, an experiment that would prove or refute the exposure, and a
remediation that goes into code as a check.

Every claim carries an evidence tag. Where a citation was read by an agent other than the
author of this document, section 6 says so.

---

## 1. The thesis

**This system's weak axis is detectability, not robustness.** Six of its worst failures were
silent; one of them — review receipts consumable only when nothing was running — ran for an
entire build, 0 of 72 units verified, while every internal counter looked healthy. The driver
recovers from a great deal; what it cannot do is notice. That ordering matters because it
inverts the usual priority: a system that fails loudly and often is in better shape than one
that fails quietly and rarely, and every remediation below is therefore ranked first by
whether the class would be *noticed*, and only then by damage. Three findings make the case
concrete and all three were measured today. `.harness/headroom.json` reports four of five
provider pools with `used_percent: null` and `exhausted: false`, and `harness.py:857` returns
`False` for an unknown pool — so *unknown quota reads as healthy quota* on the one path that
can spend the principal's money irreversibly. `built_by` records the harness id and never the
model, so for the eight `cursor-composer` units the reviewer-independence property this
project is named after is **not recoverable from the record at all**. And `state["attempts"]`
holds 108 records whose maximum value is **2**, against an admission gate of `< 3`, while
`state["review_attempts"]` holds 383 attempts across 67 units with a maximum of **27** — the
build counter can never reach its cap because every reclamation refunds it, and the review
counter has no cap to reach. [measured, this worktree, 24 Aug 2026] None of these three
produces an error, a non-zero exit, or a counter moving the wrong way. They are the shape of
everything that has gone wrong here, and the shape of what will.

---

## 2. The failure-class register

Evidence tags follow `AGENTS.md` principle 1. `[cited]` here means *some agent read the
source*; section 6 says which, and which did not.

### 2.1 Already experienced

| Class (published name) | Source | Tag | What happened here |
|---|---|---|---|
| **Gray failure / differential observability** | Huang, Guo, Zhou, Lorch, Dang, Chintalapati, Yao, *Gray Failure: The Achilles' Heel of Cloud-Scale Systems*, HotOS '17, DOI 10.1145/3102980.3103005 | [cited] | `live_dispatchers()` is a PowerShell `Get-CimInstance Win32_Process` command-line match on `dispatch.py` — a health probe that does not exercise the path the work uses, §2.2 verbatim. [measured] The prior `run_dir_progress` read a file written only at completion, so healthy and dead runs were byte-identical for a run's whole life. The re-dispatch that followed cannibalised T01, which gates 22 units: §2.3, "recovery that kills, rather than heals". |
| **Failure-detector completeness vs accuracy** | Chandra & Toueg, *Unreliable Failure Detectors for Reliable Distributed Systems*, JACM 43(2), 1996, 225–267, §2.3 | [cited] | `reclaim_expired_slots()` violated both properties in opposite directions inside 24 hours: nineteen units held slots while eight had written nothing for 43 minutes (completeness), and healthy T01 was suspected and reclaimed (accuracy). `PROGRESS_SILENCE_S = 1800` **is** that tradeoff, chosen implicitly and never measured. |
| **Incorrect handling of a non-fatal error ("errors ignored")** | Yuan, Luo, Zhuang, Rodrigues, Zhao, Zhang, Jain, Stumm, *Simple Testing Can Prevent Most Critical Failures*, OSDI '14, 249–265, Finding 10 | [cited] | The old `load()` returned `{"done": [], "attempts": {}}` on any parse error, so a torn write read as "nothing running". 92% of catastrophic failures in their 198-failure sample are this class. Live instances remain: `consume_review_verdict` wraps five exception types in `except …: pass`; `run_dir_progress` swallows `OSError` and returns `0.0`, which reclamation reads as *dead*. |
| **Crash vulnerability in an update protocol** | Pillai, Chidambaram, Alagappan, Al-Kiswany, Arpaci-Dusseau × 2, *All File Systems Are Not Created Equal* (ALICE), OSDI '14 | [cited] | The same defect from the storage side: truncate-then-write with a swallowing recovery path is a one-crash-point vulnerability. Git is one of the eleven applications they found vulnerable, and this driver's second state store is a git worktree. |
| **Partial failure** + **step repetition (MAST FM-1.3)** | Waldo, Wyant, Wollrath, Kendall, *A Note on Distributed Computing*, Sun TR-94-29, 1994 / Cemri et al., *Why Do Multi-Agent LLM Systems Fail?*, arXiv:2503.13657, NeurIPS 2025 | [asserted] / [cited] | Units dispatched twice built twice; the driver retried the other commit for ever. Nine of twelve reported conflicts. The dispatch acted and the driver did not learn: all three `Popen` sites precede the single terminal `save_state()`. [measured] |
| **Interactive complexity + tight coupling** | Perrow, *Normal Accidents*, 1984 (axes 1 and 2) | [asserted] | Almost none of the measured failures were component faults: a WSL agent wrote `core.worktree` into the shared config and broke every git command three times in an hour; a bulk `git add` staged 66,081 files; a queued unit vanished to a checkout. Each is an interaction between individually correct parts. |
| **Latent conditions** / **live mutants** | Reason, *Human error: models and management*, BMJ 2000;320:768–770 / DeMillo, Lipton & Sayward 1978; Petrović, Ivanković, Fraser & Just, *Practical Mutation Testing at Scale*, IEEE TSE 2022 | [cited] | The inverted secret guard and the routing ceiling that was a stub returning a constant are resident pathogens. "14 of 19 reviewed units carried a guard deletable with the suite green" **is a mutation-testing result reported without the field's name for it** — a live-mutant rate of ~74%, uncorrected for equivalent mutants. |
| **Unaware of termination conditions (MAST FM-1.5)** + **Escalation Failure** | Cemri et al., arXiv:2503.13657 / cobusgreyling/loop-engineering, `docs/failure-modes.md` | [cited] / [asserted] — see §6 | A `--max-turns 20` cap killed every grok dispatch mid-orientation with exit 1 and empty stderr, and read as a provider outage for days. The build loop died twice leaving no trace. |
| **Head-of-line blocking** / **lock convoy** | Karol, Hluchyj & Morgan, IEEE Trans. Comm. COM-35(12), 1987 (saturation at 2−√2 ≈ 0.586) | [cited] | `scripts/dispatch.py` takes an exclusive file lock around every cursor run; B04, L03 and Q02 each burned a full hour blocked on it while startable units waited. The existing fix — `CURSOR_CONCURRENCY = 6`, skip rather than queue — is the textbook remedy, because refusing to commit the server is the cure. |
| **Drift to the boundary of acceptable performance** | Rasmussen, *Risk management in a dynamic society*, Safety Science 27(2–3), 1997, 183–213 | [cited] | `landed = done \| built` — a unit may build on a dependency later judged DEFECTIVE — introduced because "45 units merged, 0 retired" and "the build had stopped behind review throughput". A safety constraint relaxed *precisely because it cost throughput* is Rasmussen's efficiency gradient by definition, and `AGENTS.md` forbids it in prose that did not bind. |
| **Ironies of automation** | Bainbridge, *Ironies of automation*, Automatica 19(6), 1983, 775–779 | [asserted] | The principal found three silent dispatch failures himself by watching a provider usage graph — sustained vigilance over a system that is usually fine, the task humans do worst. |
| **Retry storm without jitter** — *reclassified today* | Brooker, *Exponential Backoff And Jitter*, AWS Architecture Blog, 4 Mar 2015 | [cited] | Registered by one survey as *exposed and not yet hit*. It has been hit, it is the dominant failure in this build, and nobody had named it. `.harness/build-loop.log` records **3,280 `consilient.events.EventError`** dispatch deaths against 469 `TimeoutExpired`, 4 `MemoryError`, 3 `PermissionError` — 87% of all crashes from one cause. [measured, 24 Aug 2026, and still climbing: 2,574 four hours earlier] `events.py:2812` and `:3007` are `time.sleep(_READ_BACKOFF * (2**attempt))` with `_READ_RETRIES = 6`, `_READ_BACKOFF = 0.04` — deterministic exponential backoff, **zero jitter**, on a 40,756,831-byte append-only log contended by ~20 agents. [measured] |

### 2.2 Exposed and not yet hit, ranked by probability × damage

**Rank 1 — Correlated model error under a false independence label.**
*CAPA: Goel, Struber, Auzina, Chandra, Kumaraguru, Kiela, Prabhu, Bethge, Geiping, "Great
Models Think Alike and this Undermines AI Oversight", arXiv:2502.04313, ICML 2025* [cited];
*Lamport, Shostak & Pease, TOPLAS 4(3), 1982, 382–401* [asserted];
*Panickssery, Bowman & Feng, NeurIPS 2024* [cited].
`build_driver.py:487` hard-codes `FAMILY = {"codex":"openai", "cursor-composer":"cursor",
"grok":"xai", "claude":"anthropic"}` — keyed on the **harness id**, ignoring the model.
Reviewer selection is `[a for a in ARMS if FAMILY.get(a[0]) != FAMILY.get(builder)]` then
`reviewers[0]`, unrandomised. The `cursor-composer` harness serves at least two distinct model
families in `ARMS` — `cursor-grok-4.6-high-fast`, `cursor-grok-4.6-medium-fast`,
`composer-2.5`, `composer-2.5-fast` — all wearing one label. [measured]
`src/consilient/harness.py:635 model_family()` already returns `"grok"` for any `cursor-grok*`
id, and the driver does not call it. **Incidence, measured rather than asserted: `built_by`
is `{codex: 26, cursor-composer: 8, grok: 2, claude: 2}`, so 2 of 38 built units (5.3%)
resolve builder-family == reviewer-model-family today** — not "every review", and saying
otherwise would be laundering. Ranked 1 anyway on detectability: the receipt is byte-identical
to a correct one, it passes all eleven validation clauses, and the defect *lowers* measured β.
Compounded by `reviewers[0]` giving n=1, which tolerates f=0 commission faults in a system
whose components fail by producing confident wrong output.

**Rank 2 — Unmetered spend past an unknown pool ceiling.**
*Google SRE Book ch. 3, "Embracing Risk" (Alvidrez)* [cited]; *STPA UCA type 2, Leveson &
Thomas, STPA Handbook 2018* [cited]. Not named by any of the four surveys; found by the
adversarial pass and verified here. `harness.py:857 _is_exhausted` returns
`used_percent is not None and used_percent >= 90.0` — **unknown is not exhausted** — and
`harness.py:977` sets `require_known_headroom=False` on the explicit-`--harness` path, on the
stated grounds that an explicit harness is attended. The driver passes `--harness rh` on every
dispatch, so **the unattended loop is running on the attended path's exemption**.
`.harness/headroom.json` at 21:06 today: `cursor-models` and `cursor-other` both
`used_percent: null, exhausted: false`, note "cursor about probe timed out"; `claude-weekly`
and `grok-weekly` likewise null; only `codex-weekly` carries a number (48.0%). [measured]
Damage is irreversible and is the one class the working agreement reserves to the principal.
**The remedy everyone proposed does not reach it:** deleting `--allow-exhausted` from the
three driver sites gates `codex-weekly` and nothing else, because a null pool is not exhausted
in the first place. Shipping that alone produces a green test over an ungated path, which is
worse than the visible flag we have now.

**Rank 3 — Metastable failure with retry-driven work amplification.**
*Bronson, Aghayev, Charapko & Zhu, HotOS '21, DOI 10.1145/3458336.3465286* [cited];
*Huang et al., "Metastable Failures in the Wild", OSDI '22, Def 3–4, Thm 2* [cited, author
list disputed — see §6].
`build_loop.py` calls `subprocess.run(build_driver.py, timeout=3000)`; `save_state()` is
called at exactly three sites — `build_driver.py:1639`, `:1720`, `:1834` — **all terminal**.
[measured] A tick killed at the deadline persists nothing, and on this machine a `subprocess`
timeout does not kill grandchildren, so each abandoned tick leaves an orphan pytest contending
with the next. The sustaining effect is one line, `build_driver.py:711–717`:
`attempts[uid] = max(0, attempts.get(uid, 1) - 1)` on every reclamation, against an admission
gate of `attempts.get(u, 0) < 3`. **The measured signature is already visible: 108 attempt
records, maximum value 2.** [measured] The counter cannot reach its cap, so w\*_L is unbounded
in time, so by their Theorem 2 `C_stable = C_norm/(w*_L · w*_C) → 0` — the stable region is
empty [algebra]. The only thing between this driver and the metastable state is
`MAX_CONCURRENT = 36`, doing load-shedding work nobody assigned it. Trigger margin: suite
duration must cross 3000 s; the measured amplification is 432 s → 961 s at nine concurrent
pytest processes, so the margin is roughly 3× and shrinking with the test count.

**Rank 4 — Lethal trifecta: indirect prompt injection reaching a tool-using agent.**
*Willison, "The lethal trifecta for AI agents", 16 June 2025* [cited]; *Greshake, Abdelnabi,
Mishra, Endres, Holz & Fritz, AISec 2023* [cited]; *Debenedetti et al., AgentDojo, NeurIPS 2024
D&B; CaMeL, arXiv:2503.18813* [cited].
All three legs are configuration, verified here. Untrusted content:
`.harness/knowledge/sources.json` declares `{"id":"fetch", "command":"uvx",
"args":["mcp-server-fetch"]}` — arbitrary URLs — and `scripts/knowledge_policy.py` contains
**no host allowlist whatsoever** (grep for `allowlist`, `allowed_host`, `netloc` returns
nothing). [measured] Private data: `CONTEXT7_API_KEY` in `credential_env`, `GROK_AUTH_PATH` on
a live subscription credential, and ADR-0063 `--cwd` into other named roots. Exfiltration: the
same fetch connector; a GET with data in the path bypasses `outbound.py`'s egress gate
entirely. Permissions: `--permissions bypass` at 3 of 3 `Popen` sites (`:1621`, `:1743`,
`:1799`). [measured] Agents here are *directed* at arXiv, GitHub and npm by principles 9 and
10, so the attack surface is the surface the working principles mandate using. This is the
cheapest chokepoint in the report: all three legs are statically checkable without running
anything, and no such test exists (`ls tests/ | grep -i trifecta` is empty). [measured]

**Rank 5 — Biased β: coordinated omission, reference-free judging, oracle exploitation, and a
hand-seeded corpus.** *Tene, HdrHistogram* [asserted]; *Zhou, arXiv:2607.05904* [cited —
unverifiable id, §6]; *ImpossibleBench, arXiv:2510.20270* [cited]; *Andrews, Briand & Labiche,
ICSE 2005, via Just et al. FSE '14* [cited].
Four biases converge on one number and the number is the product. β is computed over
dispatches that produced a reviewable artefact; a run killed by a turn cap, reclaimed as
silent, or lost to a torn write produces **no β sample at all**, and those runs are not random
— seven of seven grok dispatches died with artefacts of 509 B to 2.3 KB. So β is measured on
the healthy subset and understates the false-accept rate *in the direction that flatters the
product*. `beta.py` documents the conditioning-on-verifier-outcome hazard carefully and
defaults `lower_bound_on_joint_error` to `False` because of it; it does not document the
omission hazard, which is different and unguarded. Separately, `suite_green()` is a boolean
over the whole suite, so a deleted test and a passing test are indistinguishable to the driver
while builders hold `--permissions bypass` over `tests/`; and `scripts/exp50_faults.py::SMOKE_FAULTS`
is hand-seeded, which Andrews et al. measured is not a valid substitute for real faults — a β
against it is a measurement of a different quantity sharing a name.

**Rank 6 — Premature receipt consumption and the truncating receipt path.** *Not named by any
published taxonomy; nearest is MAST FM-3.3, incorrect verification* [cited].
Three defects, one path. `build_driver.py:1629` opens `f"{uid}-verify.out"` with mode `"w"`,
so **every new review attempt destroys the previous attempt's receipt** — which is why no
`check_error` can be diagnosed after the fact. Consumption is now gated on `st_size > 0`
(`:1447–1453`), so a one-byte partial file is consumed, `json.loads` raises, the empty handler
collapses it to `check_error`, and `review_consumed[uid]` burns that (artefact, attempt)
permanently. And `artefact_identity` is computed from `HEAD:<claimed path>`, so any merge
touching a co-claimed file during the review's hour voids it silently. Measured consequence:
**383 review attempts across 67 units, maximum 27 on a single unit**, and `review_attempts` is
written at `:1604–1605` and never read as a cap. [measured] This is the loop in which build
throughput destroys the only cross-family evidence the β claim rests on.

**Rank 7 — Stale lease: a fencing token the resource never sees.** *Burrows, Chubby, OSDI '06
§2.4; Kleppmann, "How to do distributed locking", 2016* [asserted].
`coordination.py` did the hard half correctly — `_next_fencing_epoch()`, the epoch stamped on
the claim, stale-epoch refusal at admission, and a docstring citing Kleppmann by name. The
residual is the clause the diagram exists to illustrate: the resources are the git worktree
and the filesystem, and **neither can check a token**. A woken expired holder does not
re-claim; it writes. `CLAIM_GRACE_S = 300` is justified in the module docstring by "the runner
kills the process tree at the deadline", which is false on this machine — measured overruns of
10–269 s, and `scripts/dispatch.py` uses `taskkill /T /F` while `scripts/proc_tree.py`
implements Job Objects with `KILL_ON_JOB_CLOSE` and **is never imported by it**. [measured] A
31-second margin between here and two concurrent writers on one worktree is not a design; it
is luck.

**Rank 8 — Lost update and a colliding temp name in `save_state`.** *Gray & Reuter 1993;
Kleppmann, DDIA ch. 7* [asserted]; *ALICE, OSDI '14* [cited].
Durability is genuinely fixed — temp file, flush, fsync, `os.replace`, fatal on corrupt load.
Two defects remain: `build_driver.py:225` uses a **fixed** temp name
`STATE.with_suffix(".json.tmp")`, so two writers can rename each other's partial file into
place — a crash vulnerability with no crash required — while `records.py:137` already does
this correctly with `os.urandom(16).hex()`; and `save_state` is a blind overwrite with no
version and no compare-and-swap over a dict of 25 keys and 843,038 bytes. [measured]

**Rank 9 — No bulkhead, no criticality.** *Nygard, Release It!; Google SRE ch. 21–22* [cited].
`MAX_CONCURRENT = MAX_BUILDS + MAX_REVIEWS` (24 + 12) is one pool, admission written as
`reviews_out >= MAX_REVIEWS or live >= MAX_CONCURRENT` (`:1594`) and
`launched >= MAX_BUILDS or live + launched >= MAX_CONCURRENT` (`:1725`). [measured] Builds,
reviews and resolvers go through three `Popen` sites with identical flags, so **the review
tier — the only different class of facts in the system — is exactly as sheddable as a leaf
build that unblocks nothing.**

**Lower tier, real but not competing for attention.** Bufferbloat with no congestion signal
(Gettys & Nichols, ACM Queue 9(11), 2011) — `force_done` holds 23 entries under a key nothing
reads, `crash_history` 81, and sojourn time is measured nowhere. Alarm flood (EEMUA 191 /
ISA-18.2, second-hand) — 23 unmergeable units in one tick is roughly twice the flood threshold
for one operator position from a single root cause; the budget is not the constraint, the
inhibition rule is. Long-horizon self-conditioning (Sinha et al., arXiv:2509.09677) —
`DEFAULT_TURNS = 150` is exactly the regime measured, and the argument is for smaller units,
never a bigger cap. Lost in the middle (Liu et al., TACL 12, 2024) — `write_verify_brief`
check 7, "did it weaken anything to pass… hunt hardest", sits furthest from either anchor.
Reasoning–action mismatch (MAST FM-2.6) — the reviewer's prose report is read by no code path.
Chained hallucination (Wu, arXiv:2606.14589) — `repair_findings` is model-authored free text
injected verbatim into the next builder's brief, so a fabricated finding becomes a
specification. Claims not enforced at write time (Tang et al., arXiv:2605.29442) —
`unit["claims"]` is checked by a reviewer's eye, not by code.

### 2.3 Structurally impossible here — and how long that lasts

Recording these matters as much as the exposures, because effort spent defending against them
is stolen from §2.2. Three different kinds of "cannot happen", with different lifespans.

**Genuinely architectural.** *Split brain by network partition* — Alquraan, Takruri, Alfatafta
& Al-Kiswany, OSDI '18 [cited]. Every participant is on one Windows host: driver, dispatchers,
git repository, and a trajectory that is one append-only JSONL on one local filesystem. No
replica, no quorum, no leader election, no channel that can partition while both sides
survive. Their failure modes require two live sides with divergent state. **The important part
is what this rules out as a remedy:** two drivers ticking concurrently is a mutual-exclusion
failure, fixed with `TICK_LOCK`; the WSL agent writing `core.worktree` is shared mutable
state, fixed by isolation. Calling either "split brain" imports quorum as the cure, and quorum
solves neither. **Expiry date, and it is short:** their headline is that 88% of failures are
triggered by isolating a *single* node, which is what this system faces the moment any agent
runs across a boundary that can drop messages while both ends live. The WSL boundary already
is one. Enforce with a test that every dispatch target resolves to the local filesystem, which
fails the day a cloud or WSL harness becomes durable — at which point this entry re-opens
rather than being remembered.

**Genuinely architectural, and unclaimed.** *Long-lived orchestrator context degradation.*
`pick_arm`, `ready`, `reclaim_expired_slots`, `consume_review_verdict` and `publish_if_ready`
contain no model call. There is no context window in the control loop, so no run length
degrades a scheduling decision. This is a real advantage the repository has never claimed, and
**the risk is regression, not exposure**: any future "let the planner decide what to dispatch"
refactor imports the whole class in one commit. Make the immunity a checked invariant *before*
someone trades it away — an AST test over `build_driver.py` asserting no import of any
harness-invoking module in the tick path, the technique `tests/test_tier1_imports.py` already
uses.

**Held by one line of code, not by architecture — and the distinction matters.** *Sycophancy
entering the machine verdict channel.* `consume_review_verdict` asserts
`set(inner) == {"v","unit","artefact","attempt","verdict","findings"}` **exactly**,
`verdict in {"SOUND","DEFECTIVE"}`, and cross-checks `artefact_identity(unit) == artefact`
against real git blob hashes. No amount of agreeable prose moves a bit through that channel.
It is a well-built chokepoint. But it is a strict equality on a set literal: any future
proposal to accept an extra field, a free-text rationale or a confidence score re-opens the
class in one diff, and principle 5 already forbids the third. The honest label is **"immune
while this assertion stands"**, and the assertion needs a test naming why it exists. The
immunity does not reach the human β path, where Cheng et al. (*Science* 391, 2026) is the
hazard: sycophantic output is rated *higher* quality and *more* trustworthy while making the
reader's judgement worse — for a principal whose review time is the bottleneck and who is
reading agent-written summaries of agent work.

**Inapplicable rather than impossible — refuse it in the record.** *Chaos Monkey, FIT, ChAP,
Gremlin.* Every mechanism in that lineage bounds damage in a system with redundancy and real
users: Chaos Monkey is safe because another instance serves the request, FIT is informative
because a user bucket gives a control group. This driver has neither, plus one artefact of
record and one user whose review time is the scarce resource. Killing a random live dispatch
tests no failover because there is none; it destroys work. What transfers is blast radius as
*scheduling* (scratch worktrees, which already exist), ChAP's continuous-experiment idea
mapped onto `invariants.yml`, and Netflix's own practice of **simulating** rather than
injecting where injection is too costly — which is the licence the fake-harness approach runs
on. *Full deterministic simulation testing* is disqualified by FoundationDB's own stated
limitation: simulation "is unable to test third-party libraries or dependencies", and they
deleted Zookeeper and rewrote Paxos in Flow to keep the system simulable. This orchestrator's
*function* is spawning `codex`, `cursor-agent`, `grok` and `git` — precisely the dependencies
FDB removed, and they cannot be removed here because they are the product. Both refusals
belong in `docs/decisions/` with their reasons and a re-check date, because the bar moves.

---

## 3. Convergence — adopt the published names

Four surveys drawn from four literatures — distributed systems, agentic-LLM taxonomy,
SRE/safety engineering, and testing methodology — were asked independently what this system's
failures are called. Our six classes were induced from watching this machine; the taxonomies
were induced from other people's production systems. That they name the same six things is
Whewell's test passing, and it is why their *unhit* predictions are live rather than
analogical.

**Retire our private names in favour of these**, per the "no invented terminology" rule:

- "Liveness lies" → **gray failure / differential observability** (Huang et al.).
- "Slot reclamation judged progress wrongly, in both directions" → **failure-detector
  completeness vs accuracy** (Chandra & Toueg). This name is strictly better than ours,
  because it says the two errors are a tradeoff to be *chosen*, not a bug to be eliminated —
  and it tells you the remedy is two published numbers, not a better constant.
- "Non-durable state" → **incorrect handling of a non-fatal error** (Yuan et al.) from the
  handler side, **crash vulnerability in an update protocol** (Pillai et al.) from the storage
  side. Two names because they are two defects that happened to coincide.
- "Identity mismatch" → **partial failure** (Waldo et al.) for the mechanism, **step
  repetition, FM-1.3** (MAST) for the observable.
- "Shared mutable state" → **interactive complexity** and **tight coupling** (Perrow's two
  axes), **Parallel Collision** in the practitioner literature.
- "Checks that do not check" → **latent conditions** (Reason) at the incident level, **live
  mutants** (DeMillo; Petrović et al.) at the measurement level. The second matters most: "14
  of 19 units carried a guard deletable with the suite green" is a live-mutant rate of ~74%,
  and naming it correctly gives the number an incumbent to be compared against (principle 9)
  and converts a one-off audit into a standing gate.

**Keep one of ours.** "Unreachable conditions" — a gate whose precondition is unsatisfiable by
construction — has no published name that fits. Two surveys reached for "metastable failure"
and both are wrong: Bronson et al. are explicit that failures resolving when the trigger is
removed are *not* metastable, and reducing load to zero would have fixed the 0-of-72 receipt
outage, which is the opposite. Adopting "metastable" there would prescribe load shedding for a
defect that needs a code fix. The class stays ours and stays `[asserted]`.

**Two convergences are methodological rather than incidental, and both are evidence.** One
survey reached "raising `MAX_CONCURRENT` cannot raise throughput" from Little's Law (L = λW
with L pinned by the cap, so λ ≤ 36/3600 = 0.01 units/s, and W *grows* with L through
shared-suite contention) and reached the same sign inversion again from Dean & Barroso's tail
argument via fan-in. Another's lineage-driven-fault-injection entry and its Yuan et al. entry
converge independently on "no step may fail silently". Two different classes of facts, one
conclusion, twice. Record those as findings.

**And the single root cause behind a large fraction of §4.** `src/consilient/` already
contains the correct pattern for at least five of the driver's defects: `loop.py` implements
V0-29 (intent persisted before the side effect starts); `events.py::append_transaction` does
locked read-validate-write; `records.py:137` uses `os.urandom(16).hex()` for temp names;
`harness.py:635 model_family()` computes the truthful model family; `beta.py:213` lets
`min_rejections` be raised and never lowered. **The driver uses none of them.** The gap is not
knowledge. It is that `.harness/` was never held to the standard `src/consilient/` is held to,
and that is one CI rule wide.

---

## 4. The remediation plan

Every entry names the **structural property** and the **check that enforces it**. Never a
prompt, never a convention — principle 3 and the Engineering Ratchet. Entries marked
**HALF-BUILT** already exist in this repository and are merely unwired; those are the cheapest
work on the list and should be done first within their tier.

### 4.1 Detection first, because an undetected failure cannot be remediated

**R1 · The record must name the model, not the harness.**
Property: every field that reaches an independence decision is derived from an artefact with a
named producer. `last_arm[uid] = harness` (`:1765`) and
`built_by.setdefault(uid, last_arm.get(uid, "codex"))` (`:1575`) record the harness id, and
`cursor-composer` serves at least two model families, so for 8 of 38 built units the true
model family is **unrecoverable from the record**. [measured] This is STPA's "necessary
controller feedback does not exist", in the exact field the project's name rests on.
Check: record the model id at dispatch; a test asserting `built_by` values resolve under
`harness.model_family()` and that no dispatch writes a bare harness id into it.
**HALF-BUILT:** `harness.py:635 model_family()` exists, is tested, and is never called by the
driver. *Do this before the rank-1 fix, not after: the same-model refusal has no input without
it, and would either throw on missing data and stop every review, or fall back to the harness
id — the defect it replaced, now certified by a passing test.*

**R2 · Evidence must survive its own retry.**
Property: a retry may not destroy the record of what it is retrying. `:1629` opens
`f"{uid}-verify.out"` with mode `"w"`. Check: per-attempt filenames
`f"{uid}-verify-{attempt}.out"`, and a test that a second review dispatch leaves the first
receipt byte-identical. **This must land before any k > 1 reviewer scheme**, or three
reviewers through one filename is one time the evidence and three times the spend.

**R3 · "I could not read it" and "there was nothing to read" are different facts.**
Property: no predicate may manufacture a liveness verdict from a failed read.
`run_dir_progress` swallows `OSError` and returns `0.0`, which reclamation reads as dead — in
a system whose dominant measured fault is that artefact reads fail under contention. Check:
return `None` on `OSError`; reclamation treats `None` as *no evidence* and does not reclaim; a
test asserting reclamation is a pure function of positive evidence. This is `load()` refusing
to invent an empty state, applied one level out.

**R4 · The failure detector must publish its own error rate.**
Property: this repository measures β because a project named after a test of truth is obliged
to measure how good its tests are. `reclaim_expired_slots` is also a test and its error rate
has never been measured. Check: every reclamation appends an event carrying the reclaimed
run's byte count *after* reclamation — cheap ground truth — so completeness (reclaimed ∧ truly
dead / truly dead) and accuracy (not reclaimed ∧ truly alive / truly alive) are computable and
publishable beside β. That converts `PROGRESS_SILENCE_S = 1800` from an unexamined constant
tuned by anecdote into a measured tradeoff with a stopping rule. *Note the completeness hole
the constant hides:* `:711` reads `if newest and now - newest > PROGRESS_SILENCE_S` — a run
that has written **nothing** has `newest == 0.0`, which is falsy, so it is never stale and
holds its slot for the full 3600 s leash. Completeness on the silent-dead class is 0 for the
first hour. [measured]

**R5 · Guard reachability, as a second and independent check beside mutation.**
Property: mutation analysis bounds the inversion and deletion families and says nothing about
unreachability or stubs. Just et al. measured 17% of 357 real faults uncoupled to *any* mutant,
dominated by algorithm modification (37 of 63) and code deletion (7) — which is exactly the
shape of "a routing ceiling was a stub returning a constant" and "a capture gate can only be
passed by breaking capture". `check_guard_mutation.py` reports those guards as perfectly
killed, honestly, because the `raise` fires under test; it just never fires in production.
Check: for every registry guard, assert its refusal branch is exercised at least once by the
full suite under `coverage.py` (already in the tree); a guard whose raise-line has zero hits is
reported. Perturbing the code and observing execution are different classes of facts, and
neither subsumes the other.

**R6 · β's denominator must be the attempted set.**
Property: fail closed, in the spirit of `lower_bound_on_joint_error` defaulting to `False`.
Check: emit a `dispatch.attempted` intent record at every launch and a terminal event at every
exit path *including reclamation*; `beta.compute` **refuses** a sample whose denominator cannot
be reconciled against the attempted count, and refuses to pool `real` and `seeded` corpora into
one number. The intent record is also the partial-failure fix (below), which is why it is one
change and not two.

### 4.2 Refusals — where the correct behaviour is to stop

**R7 · Unknown headroom is exhausted headroom.**
Property: a sensor that returns "I don't know" must not read as healthy. Check:
`harness.py:977` sets `require_known_headroom=True` on the explicit-`--harness` path — one
boolean — so `_blocked` returns "headroom is unknown" and the dispatch is refused even under
`--allow-exhausted`. Then delete `--allow-exhausted` from the three driver sites, in that
order, because the reverse order ships a green test over an ungated path.
**Consequence, stated plainly: this refuses cursor, grok and claude dispatch today and leaves
only codex.** That is the correct answer — refusal is the success path when the scarce resource
is quota, and `harness.py`'s own module docstring says so — and the way to unrefuse it is to
make the probe work, never to widen the gate. Open question 1.
Related and separate: the only quota sensor is an unpinned vendor CLI's undocumented JSON.
`headroom.py` returns `_unavailable(...)` on any failure, and `headroom.json` records the
version it was written against **in prose**, asserted nowhere. A probe that runs successfully
and learns nothing produces a fresh timestamp, so `HEADROOM_MAX_AGE = 15 min` cannot help.
Check: write the observed CLI version into the probe's own event, and a test that
`headroom.json` carries a non-null `used_percent` for every pool named in `ARMS` — it fails
today, and that visible red is the only honest state.

**R8 · The lethal trifecta is a statically checkable configuration property.**
Property: private data + untrusted content + external communication may not be simultaneously
true for any harness. Check: `tests/test_no_lethal_trifecta.py` loads `sources.json`, the
dispatch permission default and the credential environment, and fails if all three legs hold.
It will fail today. Remedy is CaMeL's shape — split the connector set: a quarantined arm with
fetch and no repository write access, a privileged arm with repository access and no network —
plus a fetchable-host allowlist enforced in `knowledge_policy.py` at materialisation. The
honest price is published: 77% of AgentDojo tasks defended versus 84% undefended. Precedent
exists: `src/consilient/` is AST-locked by `tests/test_tier1_imports.py`; the discipline has
simply never been applied to the harness side. **Never widen the allowlist as a remedy.**

**R9 · Split the attempt counter; cap the review loop; escalate rather than retry.**
Property: a counter that is refunded is not a cap. Keep `attempts` refundable — the refund is
correct about *evidence*, since an expired leash is not evidence about the work — and add a
non-refundable `dispatch_count` capping total launches per unit regardless of reason, gating
dispatch on both. Cap `review_attempts` in the same place build attempts are capped. Check: a
test asserting no code path decrements `dispatch_count`, and that exhaustion writes an
escalation event through `consilient.events.append` and stops dispatching that unit.
**Two constraints on the cap, both from the adversarial pass and both binding.** First,
inhibition: one root cause yields one escalation, not one per unit — 23 unmergeable units in
one tick is twice the ISA-18.2 flood threshold for one operator position, and a cap that fires
correctly on an infrastructure fault is a device for converting a fixable bug into permanent
work for the one person who is the bottleneck. Second, ordering: **R14 lands first**, because
the dominant measured failure is infrastructure, not unit badness, and a cap of 3 would retire
the whole Y block into the human queue in a single tick.

**R10 · Reclamation must not free a slot it cannot terminate — and must not kill either, yet.**
Property: freeing a slot without terminating the worker is the positive-feedback edge for a
cascading failure (Google SRE ch. 22: "a failure that grows over time as a result of positive
feedback"). The obvious remedy — wire in the tree-kill — is **refused for now, on sequencing
grounds**: `reclaim_expired_slots` has a recorded false positive (healthy T01, suspected,
reclaimed, cannibalised) and its accuracy is unmeasured. Today a false reclamation costs a
duplicate build; with the kill wired it destroys an hour of work that was about to succeed,
irreversibly, driven by the one component whose error rate is admitted to be unknown. **Never
attach a destructive action to an unmeasured detector.** Order: R4 first, publish the two
numbers, then wire the kill. Until then reclamation refuses to free the slot rather than
freeing it and killing. **HALF-BUILT:** `scripts/proc_tree.py` implements Job Objects with
`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` — the only primitive on Windows that guarantees descendant
termination — and `scripts/dispatch.py` does not import it, using `taskkill /T /F`, which that
file's own docstring records as non-atomic. [measured]

### 4.3 Structure

**R11 · Intent before the side effect.**
Property: V0-29, already implemented in `src/consilient/loop.py` — "the intent record is
appended and the file closed before the side effect starts", giving at-most-once execution with
an explicit abandoned record on resume. All three driver `Popen` sites precede the single
terminal `save_state()`. Check: a persist-intent-then-launch helper, and a test that every
`Popen` starting an agent is preceded by a persisted intent record. **HALF-BUILT**, and the
cheapest high-value change in the report because the correct pattern is already here.

**R12 · Checkpoint after every state-mutating phase; unique temp names; compare-and-swap.**
Property: a killed tick keeps what it earned, and no writer silently overwrites another.
Checks: `save_state` after each mutating phase rather than only at exit; `os.urandom(16).hex()`
in the temp name (copy `records.py:137`); a monotonic `version` field with `save_state` refusing
to write when the on-disk version is not the one it read, treating refusal as a tick abort;
`sh()` requiring an explicit timeout with no default, so an unbounded subprocess is a type error
rather than a habit. Test: two interleaved saves over one base version produce exactly one
success and one refusal.

**R13 · Liveness from artefacts, and a ban that can actually bite.**
Property: verify by artefact, never by process identity. `live_dispatchers()` counts Windows
processes by `CommandLine -match 'dispatch.py'` and gates both admission and the `quiescent`
decision that authorises rebasing under a possibly-live worker. ADR-0034 forbids exactly this
and `tests/test_supervision.py` enforces the ban — but the ban is scoped to `DISPATCH_PATH`
(`scripts/dispatch.py`) and matches only `ast.Name` and `ast.Attribute`, while
`live_dispatchers` expresses the behaviour inside a PowerShell **string literal**. [measured]
**So the guard is out of scope and unmatchable: it cannot fail.** That is class 6 found inside
the check that exists to prevent class 1, and it is the tidiest illustration in this document of
why the Engineering Ratchet has to mean a check that can bite. Checks: extend the ban to
`.harness/build_driver.py`, match `ast.Constant` as well as identifiers, and replace
`live_dispatchers()` with a count derived from run-directory artefacts — `coordination.py`
already projects claim state, so the artefact exists.

**R14 · Full jitter at every retry site.**
Property: contenders that back off deterministically stay a herd; the jitter, not the exponent,
is the part doing the work (Brooker). Two sites, `events.py:2812` and `:3007`, are
`time.sleep(_READ_BACKOFF * (2**attempt))` with no randomness, on a 40.8 MB log contended by
~20 agents, and the failure escalates to a global goodput stop because the budget then fails
closed. Check: one shared `_retry_sleep(attempt)` using `random.uniform(0, base * 2**attempt)`,
used by every retry site, plus a test that fails on any `time.sleep()` whose argument contains
`2**`. **Explicitly not the remedy: raising `_READ_RETRIES` or lengthening the budget**, which
widens the window without decorrelating anything, and is a threshold relaxation. Land the
measurement in the same unit (§5, E1), because jitter is strictly-not-worse at equal offered
load but may not be *sufficient* — if the median contiguous denial burst exceeds the 2.52 s
budget, the remedy is structural (stop reading the whole 40 MB file at dispatch startup;
snapshot or index a prefix), and the experiment discriminates.

**R15 · Bulkheads, criticality, and a reserved lane.**
Property: saturating one lane leaves the other's free-slot count unchanged. Check live builds
against `MAX_BUILDS` and live reviews against `MAX_REVIEWS` separately, never against one shared
`live`; give every dispatch a declared criticality (review > resolve > build) and shed the
lowest first; reserve a lane the retirement suite can always use. Test: saturating one lane
leaves the other unchanged. Four lines and one test — and **do not measure this first**, because
two lines of source already say the answer with certainty (§5).

**R16 · Make the escalation a state transition, not a `print`.**
Property: escalation must free capacity, not annotate a transcript. There are 23 `print()` calls
in `build_driver.py`, two labelled ESCALATION, writing to a loop transcript with no reader;
`grep "def escalat"` over `src/consilient/` returns nothing. Check: an escalated unit consumes
no slot, and a bare `print` containing ESCALATION is a lint failure so the chokepoint cannot be
bypassed the way the prior private repository's LLM boundary was (the case is `AGENTS.md` working principle 3; the repository is not named here because `check_private_repo_names` is a ratchet and this file is not on it). The delivery channel already exists and needs
no new module: append the escalation to the trajectory, which `consil record` and
`consil dashboard` already read. **Explicitly not the remedy: enlarging `MAX_CONCURRENT` to fit
the backlog.**

**R17 · Sign the receipt, and let the dispatcher own its path.**
Property: control instructions must not travel in-band with untrusted data.
`_verdict_candidates` scans the reviewer's entire stdout with a brace-balanced regex and the
consuming loop has **no `break`** — last match wins — while `unit`, `artefact` and `attempt` are
all computable by any agent in the repository. Check: the reviewer writes the receipt to a path
the dispatcher owns; the dispatcher signs it; `consume_review_verdict` calls verify and refuses
anything unsigned. That is Lamport's signed-message relaxation, which makes a wrong verdict
attributable rather than anonymous. **HALF-BUILT:** `scripts/sign_verdict.py` implements SSHSIG
over a canonical JSON body with namespace `consilient.verdict.v1` and an `allowed_signers`
principal, is used for the human β path, and is **not imported by `build_driver.py`**.
[measured]

**R18 · Refuse a same-model review; then raise k from a measured f.**
Property: cross-family selection is the right *independence* property; independence without
redundancy still tolerates zero commission faults, and the two are being conflated. Check:
delete `FAMILY` from `build_driver.py`, import `consilient.harness.model_family`, and assert
`model_family(builder_model) != model_family(reviewer_model)` for every dispatched review — a
same-model review is **refused**, not scored. Then retire on SOUND only when k independent
cross-family reviewers agree, with **k derived from a measured pairwise disagreement rate and
never below 2**, and a single DEFECTIVE always blocking because the cheap side of the asymmetry
should be free. Deps: R1 (there is no builder model to compare until the record carries one), R2
(three reviewers through one truncating filename is one reviewer), and the review channel
returning usable verdicts at all — you cannot estimate disagreement in a channel returning
`check_error` 99% of the time.

### 4.4 Two rules that apply to everything added above

**Derive the scan set from `git ls-files`, never from a filesystem walk.** `.harness/dispatch/`
holds hundreds of run directories including full repository checkouts at older revisions. Two
ordinary `.harness` walks attempted while writing this document — a recursive grep and a
`du -sh` — **each exceeded a 120-second timeout**. [measured, this session] Any repository-wide
AST or grep check written with `Path.rglob` will scan frozen copies of the code it is auditing,
report findings against files nobody can edit, and take minutes on a box whose contention is the
presenting problem. One line, in the same commit as any tree-walking check.

**A detector that reads model prose must be measured against a labelled set before it gates
anything.** A crash detector matching the bare string `"Error"` already produced 20 false
positives here; the proposed "refuse a SOUND receipt whose report matches the defect vocabulary"
rule will bite on a reviewer who writes *"I checked for a weakened assertion and found none"* —
blocking the diligent review and selecting against diligence. That is β applied to the detector,
which is this repository's own discipline, and it is the discipline skipped every time a new
grep is proposed as a chokepoint.

---

## 5. The experiment programme

Basiri et al. (*Chaos Engineering*, IEEE Software 33(3), 2016) require the hypothesis to be
about a metric visible at the **system boundary**, not an internal counter; internal counters
are watched only to abort early. Note the correction one survey found and that should be
carried: "minimise blast radius" is **not** one of that paper's four principles (steady state,
vary real-world events, run in production, automate continuously) but a later addition to
principlesofchaos.org — and the site's current wording drops "distributed" from the definition,
which is the licence for applying any of this to a single-machine orchestrator.

### 5.1 Pre-registered steady state

Primary boundary metric: **verified retirements per hour.** Measured now: 3 SOUND over
16:34–20:48 = **0.71/h**; `verified` = 22 of 137 units. Healthy band, asserted from the plan's
shape and to be revised on first measurement: **≥ 3/h**. [asserted]

| Secondary signal | Measured now | Healthy band |
|---|---:|---|
| Dispatch crashes per hour | ~331 | ≤ 5 |
| Share of crashes from one cause | 87% (`EventError`) | ≤ 30% |
| Review attempts per reviewed unit | 5.7 (383 / 67) | ≤ 1.2 |
| Usable verdicts (SOUND+DEFECTIVE) / consumed | ~1% | ≥ 90% |
| Ticks whose `driver-state.json` content hash changed | not recorded | 100% |

An experiment that cannot move a row of this table does not run.

### 5.2 Shared apparatus, built once (~150 lines)

**A chaos worktree.** `build_driver.py`, `build_loop.py` and `dispatch.py` all derive `ROOT`
from `__file__`, so a second worktree gets its own state, briefs, dispatch dirs, trajectory,
headroom, cursor lock and tick lock. Containment is structural, not disciplinary — including the
cursor lock, so a chaos experiment cannot block the live build's serialisation.
**A fake harness** named `codex`/`grok`/`cursor-agent` earlier on `PATH` (`Harness.binary` is a
bare name), driven by env vars for sleep, exit code, bytes written, streaming interval and
grandchild spawning. No experiment invokes a real provider, so the whole programme costs nothing
and removes `--allow-exhausted` from the risk surface entirely.
**A stubbed `suite_green()`** — the single largest containment control on the list, because the
real one runs the full suite and nine concurrent pytest processes were measured taking it from
432 s to 961 s. An experiment that runs the real suite injects the load whose effects it is
measuring.
**Scale the clock, not the mechanism.** 3000/3600/1800/300 become 30/60/30/5. Every mechanism
here is scale-free in the ratio, which turns a three-hour experiment into four minutes.

**Standing rules — violate any and the experiment does not run.** Nothing writes inside the live
worktree's `.harness/`. No real harness binary, no network, no credential. No invocation of the
real suite. Nothing writes `.git/config`, `core.hooksPath` or the main index. A hard wall-clock
cap per experiment enforced by `proc_tree.py::assign_job`. Concurrency-generating experiments
declare a process budget and run either with the live loop stopped or at ≤ 8 processes with a
baseline measured immediately before and after.
**Abort, escalating:** `TerminateJobObject` on the experiment's job; `touch
chaos-lab/.harness/STOP-LOOP`; for the live build, `touch <live>/.harness/STOP-LOOP` then
`schtasks /End /TN ConsilientBuildLoop`. Undo: `git worktree remove chaos-lab --force`. Both
stop files already exist — the abort was built before the experiments, which is the correct
order.

### 5.3 Run, in this order

**E1 · Trajectory contention: is the retry storm collision-correlated or hold-bound?**
Hypothesis: with W ∈ {1,4,8,16,20} writers appending 13.6 KB events every 200 ms and R readers
polling every 2 s for 300 s, **zero reads fail after 6 attempts**. Live comparator: 3,280
failures. Fault: (a) offered load W; (b) an injected deny-share hold of D ∈
{50,200,1000,2400,3000} ms — 2,400 sits inside the 2.52 s budget, 3,000 outside, and D is the
discriminator. Arms: production backoff vs full jitter at identical offered load, interleaved
trial-by-trial so drift hits both. Prediction if not resilient: failures appear in the
deterministic arm well below D = 2520 ms and rise super-linearly in W while the jitter arm stays
near zero — a synchronised herd, which is what a measured p(deny) ≈ 0.317 per attempt against
3,280 observed failures implies, since six independent attempts at that rate would fail once in
a thousand [algebra]. Also record the distribution of contiguous denial-burst lengths: median
below 2.52 s means jitter is the remedy; median above means jitter cannot help and the remedy is
to stop reading the whole 40 MB file at dispatch startup. **In neither branch is raising
`_READ_RETRIES` admissible.** Blast radius: a scratch `.jsonl` under `tmp_path`; the live file is
never opened for writing. **Damage ceiling: one temp file.** Cheapest version: `multiprocessing`
plus `events.append`/`events.read`, the pattern `tests/test_event_durability.py` already uses —
~60 lines, 5 minutes. **Run this first; every other question is downstream of dispatches that
survive their own startup.**

**E2 · Bounded crash-point enumeration over `save_state`.**
Hypothesis: for every crash point k in the syscall trace, recovery returns the complete old
state or the complete new state and never a third; zero orphan `.json.tmp` files remain; two
concurrent writers over one base version produce exactly one success and one refusal. Fault:
monkeypatch `os.write`/`os.fsync`/`os.replace` to count calls, learn N, then raise at call k for
k in 1..N. Predictions, and I expect all three to fail: every k before `os.replace` leaves an
orphan nothing cleans; the fixed temp name lets two writers rename each other's partial file into
place with no crash required; and the blind overwrite yields two successes and a silent lost
update. Blast radius: `tmp_path`. **Zero.** ~80 lines, seconds. Honest limit for the ADR: this
tests *our* update protocol, not NTFS's guarantees, and `events.py:2353` already records that
directory fsync is a no-op on Windows — so the recovery path must tolerate losing the rename, and
this test proves it rather than assuming it. B3's finding that most crash-consistency bugs
reproduce in three or fewer operations says the bounded form is where the bugs are, not a poor
relation.

**E3 · The premature-consumption race on `-verify.out`.**
Hypothesis: review attempts per reviewed unit ≤ 1.2 and usable verdicts ≥ 90%. Measured: 5.7 and
~1%. Faults, each independently: (a) write a 1-byte partial JSON prefix while a fake reviewer is
"running", then tick; (b) land a merge touching a co-claimed file during the review window so
`artefact_identity` moves; (c) dispatch a second review and check whether the first receipt
survives. Predictions: all three fail, and (c) is already visible on disk. Blast radius:
`tmp_path` with `monkeypatch.setattr(driver, "BRIEFS", tmp_path)` — no loop, no dispatch, no
worktree. ~40 lines, seconds.

**E4 · Grandchild escape and the claim-grace margin.**
Hypothesis: at deadline + 1 s, zero descendants remain, and no second claim is admitted while a
first tree lives. Fault: a fake harness spawning a detached grandchild holding stdout open past
`timeout_s + CLAIM_GRACE_S`. Prediction: it fails, and the code says why — `taskkill /T /F`
versus the unused Job Object. Blast radius: fake harness, chaos worktree, scratch claim registry;
the shim carries a unique marker so stragglers are killable by it. ~60 lines.

**E5 · Detector completeness and accuracy.**
Hypothesis: at the scaled equivalent of `PROGRESS_SILENCE_S`, completeness ≥ 0.95 and accuracy
≥ 0.95. Ground truth is known by construction: four classes × 10 dispatches — dead-fast (exit 1
after 2 s, 509 bytes written, the measured grok shape), dead-silent (exit 1, **nothing**
written), alive-slow (one byte per silence-window + 10 s), alive-fast. Predictions: completeness
= 0 on dead-silent for the whole leash, because `if newest and …` never fires on
`newest == 0.0`; accuracy < 1 on alive-slow, which reproduces the T01 cannibalisation
deterministically in five minutes instead of by losing the unit that gates 22 others. **The
remediation is the experiment** — instrument, run one build, read two numbers.

**E6 · The tick killed at its deadline (metastability).**
Hypothesis: every tick advances state (content hash of `driver-state.json` changes on 100% of
ticks), and goodput returns to band within one tick of the trigger being removed. Fault:
`timeout=30` with a stubbed suite sleeping 35 s for three ticks, then **remove the fault** and
run three more — the trigger-then-remove-trigger sequence nobody runs by accident. Prediction:
the state hash is unchanged across each killed tick, orphans accumulate, goodput stays at zero
after the trigger clears. Blast radius: chaos loop holding its own locks, ≤ 8 processes; the
abort path must log orphan counts before killing, because counting them is the result. Scaled,
the whole thing is under four minutes.

**E7 · The stale lease writing after its epoch is superseded.**
Hypothesis: after a claim expires and a higher epoch is issued, zero bytes written by the old
holder reach merged history. Fault: fake harness A blocks on a sentinel (a portable,
deterministic stand-in for SIGSTOP), its claim expires, B is admitted at epoch N+1, A is released
and commits. Prediction: A's write lands, because the epoch is checked only at claim admission
and the resource cannot check a token. Blast radius: a scratch git repo under `tmp_path`.
**Zero.** ~50 lines.

### 5.4 Deliberately not run

- **The bulkhead measurement.** Two lines of source say the answer with certainty: one shared
  `live` counter, `live >= MAX_CONCURRENT` at `:1594` and `:1725`. **The measurement costs more
  than the fix.** Measuring a certainty is procrastination wearing rigour's clothes.
- **The lethal-trifecta canary.** Not an experiment. The check is static, takes one file, and
  fails today; running an injection first would add risk to a question already answered by
  configuration.
- **Any experiment on `--allow-exhausted` spend.** Never design an experiment whose failure mode
  is money leaving the principal's account. Delete the flag; flip the boolean.
- **The same-model review incidence.** Answered by replay against data already on disk: 2 of 38
  built units, 5.3% [measured]. The remaining question — the pairwise disagreement rate f that
  sets k — is worth measuring and is **blocked on E3**, because you cannot estimate reviewer
  disagreement in a channel returning `check_error` 99% of the time. Register it as blocked
  rather than running it and getting a number made of noise.
- **Chaos Monkey against the live build**, and **full deterministic simulation testing.** Reasons
  in §2.3. Both refusals belong in ADRs with a re-check date.

### 5.5 Register discipline

`.claude/skills/running-experiments/SKILL.md` is explicit that **the experiment number is given,
not taken** — six agents once read the highest number and added one, five chose the same, and the
merge was resolved with "keep both sides". The highest in
`docs/10-research/experiment-register.md` is currently **EXP-143**. [measured] **No numbers are
allocated here.** Each entry needs one from the principal plus the five required fields in order
— Decides · Precondition · Procedure · Measures · Stopping rule — and, per ADR-0050, a *Largest
plausible effect* if it is to block anything.

### 5.6 One thing that is not an experiment and should be done regardless

`crash_history` stores the full repeated exception string per unit — one entry contains 28
byte-identical copies of the same `EventError`. That is unbounded growth in `driver-state.json`
(**843,038 bytes today, up from 578 KB earlier in the day** [measured]) and in the trajectory
(40,756,831 bytes). **The trajectory's size is fed by the failure whose detection requires
reading the trajectory.** Deduplicating a repeated crash string to
`(message, count, first_seen, last_seen)` is a few lines, removes a whole input from E1, and
should be done before E1 runs so the experiment measures contention rather than a bug it did not
mean to include.

---

## 6. Evidence quality, honestly

**What the author of this document read.** `CONSILIENCE.md`, `AGENTS.md`,
`.harness/build_driver.py`, `.harness/headroom.json`, `.harness/driver-state.json`,
`.harness/build-loop.log`, `.harness/knowledge/sources.json`, `src/consilient/harness.py`,
`src/consilient/events.py`, `tests/test_supervision.py`, `scripts/knowledge_policy.py`, and the
file listings for `scripts/proc_tree.py` and `scripts/sign_verdict.py`. Every `[measured]` claim
above was run in this worktree today. **No paper was read by the author of this document.** Every
`[cited]` tag is inherited from the survey that read the source, and the tags below are the
honest state.

**Read in full, this cycle, by a named survey:** Huang et al. HotOS '17 (§1 and §2.2 quoted
verbatim); Bronson et al. HotOS '21; Chandra & Toueg JACM 43(2) §2.3 verbatim; Yuan et al. OSDI
'14 (abstract, §1, Findings); Pillai et al. OSDI '14; Just et al. FSE '14 §3.2 and Table 4;
Petrović et al. TSE 2021; Alquraan et al. OSDI '18 (abstract, §1); Leveson & Thomas, STPA
Handbook pp. 21, 36–37, 44–45; Reason BMJ 2000; Google SRE Book chs. 3, 6, 21, 22; Basiri et al.
IEEE Software 2016; Brooker 2015; Zhou arXiv:2607.05904.

**Named from familiarity, not re-read — correctly tagged `[asserted]`:** Waldo et al. 1994 and
Deutsch's fallacies; Burrows OSDI '06 and Kleppmann 2016; Gray & Reuter 1993; Lamport, Shostak &
Pease 1982; Schlichting & Schneider 1983; Dean & Barroso CACM 2013; Gunawi et al. FAST '18;
Gettys & Nichols 2011 and CoDel; Tene / HdrHistogram; Little 1961; Bainbridge 1983; Perrow 1984;
Cook & Rasmussen 2005; Nygard, *Release It!*; EEMUA 191 and ISA-18.2 (thresholds taken from
secondary summaries and second-hand); Larouzée & Le Coze 2020.

**Defects the adversarial pass found, reported here rather than quietly dropped.**

1. **One paper, two author lists, under a load-bearing theorem.** "Metastable Failures in the
   Wild", OSDI '22, is given by one survey as *Lexiang Huang, Matthew Magnusson, Abishek
   Bangalore Muralikrishna, Salman Estyak, Rebecca Isaacs, Abutalib Aghayev, Timothy Zhu, Aleksey
   Charapko* and by another as *Lexiang Huang, Matthew Garrett, Timothy Zhu et al.* **At least
   one is fabricated**, and both are offered as the source for Theorem 2, on which the
   `[algebra]` claim "the stable region is empty" rests. The first list is the plausible one. The
   rule that matters: **the theorem must be re-read before that algebra ships, not the author
   list.** One survey supplied, unprompted, the best evidence in the whole set for why: a
   summariser returned a complete and confident author list for the gray-failure paper — "Indu
   Baratela, Tanakorn Leesatapornwongsa, Rahul Sharma, Shan Lu" — which is entirely fabricated.
   It did not crash. It answered. Make it a standing rule: **authors and venue come from the
   artefact, never from a summariser.**
2. **A practitioner repository doing taxonomy work it is not qualified for.** Five entries were
   tagged `[cited]` against `docs/failure-modes.md` in one person's GitHub repo, complete with
   S1/S2/S3 severities, and set alongside MAST's peer-reviewed fourteen modes as objects of the
   same kind. They are not: a list retrieved once has no method behind its severity column, and
   three recommendations rested on it, including "name their CLI as the incumbent" under
   principle 9 — which would make the bar one person's repo. **Every such tag is demoted to
   `[asserted]` in this document.** The ideas survive; `loop-context`'s circuit-breaker semantics
   are sensible.
3. **Four load-bearing claims sit on arXiv identifiers nobody in this cycle could verify** —
   arXiv:2607.05904, arXiv:2606.14589, arXiv:2605.29442, and **arXiv:2603.26993 (Ao, Gao &
   Simchi-Levi), which `AGENTS.md` cites as the theorem forcing the exogenous-signal rule.**
   Three surveys repeat the last one from this repository's own `bibliography.md`. **Four agents
   agreeing about a line they all read in the same file is echo, not corroboration** — Whewell's
   rule applied to our own reading, which is the one place it has never been applied. Also flag
   the precision tell: "90.50%" and "91.49%" from a 20,574-session study is the shape of a number
   a summariser reconstructed; two decimal places is not more precise, it is more confident.
4. **Two internally contradictory figures.** MAST per-mode percentages disagree between two
   extractions of the same PDF (41.8/36.9/21.3 vs 44.2 for FC1) — flagged by that survey itself,
   correctly, and **no single-mode percentage may be quoted until the PDF is read.** The
   Aspirator figure appears as "143 bugs and bad practices across 9 systems" in one survey and
   "121 new bugs and 379 bad practices; 143 fixed or confirmed" in another; the second matches
   the paper's structure and is the one to use.
5. **One caution to lift, in the other direction.** Manheim & Garrabrant, *Categorizing Variants
   of Goodhart's Law*, arXiv:1803.04585, was flagged as "identifier from memory, verify before
   citing". The identifier is correct and the four variants — regressional, extremal, causal,
   adversarial — are correct. Say so. Over-cautious tagging costs too: a reviewer who finds one
   needless caution discounts the rest, and the tag stops carrying information.
6. **A survey's premise that the review-tier exposures are dormant is out of date, and the
   correction reorders the plan.** "Not yet hit because 0 of 72 receipts were consumed" is false:
   `review_consumed` holds 71 entries and 383 review attempts have been spent. [measured] The
   `live_dispatchers() == 0` quiescence gate that caused the original outage **has been
   repaired** — consumption is now gated on `st_size > 0` at `:1447–1453` — which retires the
   "unreachable condition" experiment and promotes the premature-consumption race in its place.
   The review-tier exposures are live, not dormant, which is why R2 and R6 rank where they do.

**Enforcement, so this section does not have to be written again.** A `[cited]` entry names the
artefact path or hash of what was read, and the same source may not appear at two evidence grades
in one document. Both are mechanical checks over the prose, in the test file that already fails
an uncited superlative.

---

## 7. What this does not cover

**Adversarial findings left open, none of them closed by anything above.**

- **Is `build_driver.py` scaffolding or product?** Four surveys and a gap analysis produced
  roughly forty remediations and every ranked one is a `.harness/` defect, while
  `src/consilient/` — AST-locked, stdlib-only, `min_rejections` raise-only — comes out well. If
  the driver dies when this build finishes, several proposals here (`.epoch` sentinels, Job
  Objects, criticality classes, per-arm queueing) are permanent architecture for a temporary
  machine. If it is v1 of the orchestrator that ships, it needs the tier-1 import lock and the
  invariant suite, and half these findings collapse into one CI rule rather than forty patches.
  **Every priority in §8 changes on the answer.** Open question 4.
- **`consil doctor`'s evidence-preservation copy has written 3.04 GB** across 292
  `state.db.stale-*` files — 84% of the files in `.harness/`. The branch is guarded by
  `prior is not None and projected != events`, which is the *exact expression* the block eight
  lines below names as merely stale: "Staleness is not drift, and conflating them makes the check
  cry wolf." So a previous adversarial round's remediation, added in good faith to stop a check
  destroying its own evidence, fires on ordinary trajectory growth, forever, at ~10 MB a go. The
  fix is one condition — gate on `prefix_identical is False`, which is already computed twenty
  lines above and never consulted — plus retaining the newest three. Free space is 2.48 TB, so
  nothing is imminent; the shape is the finding, and it is the self-inflicted version of the
  fail-slow trigger.
- **Every proposed check is a level check; nothing anywhere records a slope.** The failure classes
  the surveys worry most about — bufferbloat, fail-slow, drift, comprehension debt — are rate
  phenomena, and every remedy offered for them is a predicate over the present instant. Suite
  duration 432 s → 961 s is quoted three times as a fact about concurrency and is also a two-point
  time series with no recorder. `driver-state.json` at 843 KB, the trajectory at 40.8 MB, the
  stale-DB directory at 3.04 GB — all fine today, all monotonic, and every check proposed anywhere
  in these documents would pass on all of them for months and then fail at once. That is precisely
  the slow degradation the question asked about, and it is absent because **a level check cannot
  see a slope by construction**. Smallest repair: one event per tick carrying four numbers already
  computed — suite seconds, trajectory event count, state bytes, free disk — and one test that
  fails when the newest value exceeds the seven-day median by a recorded factor. Do not build a
  dashboard for it.
- **Nothing measures the principal's absence, and nothing rate-limits the asks.** `beta.py`
  handles absence honestly: below `min_rejections` it returns a `Beta` carrying no number rather
  than a flattering one. What follows and nobody stated: the only authorised author of the verdict
  β is measured against is the principal, so an absent principal produces **no β, indefinitely,
  while the machine spends quota at full rate generating artefacts whose β can never be
  computed.** There is no `last_human_verdict_at` anywhere. The likelier form is worse than
  absence — he does not stop reading, he keeps approving — and a system that generates asks faster
  than one person can genuinely consider them has converted its human gate into a biased coin,
  which is the human-side twin of attaching an irreversible action to an unmeasured detector.
  Smallest repair: record `last_human_verdict_at`; refuse to dispatch a new *build* (not a review,
  not a repair) once it exceeds a recorded threshold. The machine should stop manufacturing work
  nobody can judge.
- **`built_by` for the eight `cursor-composer` units is unrecoverable.** R1 fixes the record going
  forward; it cannot reconstruct the past. Any independence claim about those eight units is
  unavailable, permanently, and should be reported as unknown rather than assumed.

**Also not covered:** ordinary supply-chain risk beyond the harness CLIs (dependency pinning,
`npx -y` and `uvx` fetching connectors at dispatch time); anything about the product's correctness
as distinct from the harness that builds it; ADR authorship for the two refusals in §2.3, which
still need writing; and the reachability of `if True:` at `build_driver.py:1541` — a conditional
whose test was removed but whose block was not, sitting in the merge path, which is the "guard
deletable with the suite green" shape found in the driver itself and is worth a grep for siblings.
[measured]

---

## 8. Sequencing by risk reduced per unit of the principal's attention

He is one person, and that — not model capacity — is the binding constraint on this project. So
the ordering below prefers verification, refusal and deletion over new mechanism, because those
are the only kinds of work that *reduce* his review burden instead of adding to it. Ten diffs he
must read is worse than three he does not.

**Tier 0 — today, zero risk, no worktree, no harness, no quota.**

1. **Full jitter plus the contention measurement (R14 / E1).** Addresses 87% of live dispatch
   deaths. Land the jitter and the experiment in one unit; the experiment tells you whether jitter
   was sufficient or whether the 40 MB read at dispatch startup must go.
2. **Deduplicate `crash_history` (§5.6).** A few lines, and it removes an input from E1.
3. **Crash-point enumeration over `save_state` (E2)** and **the receipt race (E3)**. Both are
   `tmp_path`-only pytest files, seconds to run, and between them they cover the durability and
   identity families that account for most of the measured incident set.

**Tier 1 — this week, one afternoon, and each is a refusal rather than a mechanism.**

4. **Make the record name the model (R1)** and **give each review attempt its own receipt (R2)**.
   These are the two detection changes without which the rank-1 fix and any k > 1 scheme are worse
   than doing nothing.
5. **Flip `require_known_headroom` to True, then delete `--allow-exhausted` (R7).** One boolean
   and three lines, in that order. Halts most dispatch until the probe works — see open question 1.
6. **Write `tests/test_no_lethal_trifecta.py` and run it (R8).** Static, one file, fails today,
   zero risk. The connector split follows once the check names the exposure.
7. **Guard reachability under coverage (R5).** ~30 lines, catches precisely the family mutation
   provably cannot.

**Tier 2 — once tier 1 has paid for the shared apparatus.**

8. Intent-before-side-effect (R11), checkpointing and CAS in `save_state` (R12), the
   non-refundable `dispatch_count` and review cap with inhibited escalation (R9/R16).
9. Detector completeness and accuracy (R4 / E5), **then** the tree-kill (R10). Never the reverse
   order.
10. Liveness from artefacts and the AST ban that can bite (R13); bulkheads and criticality (R15);
    the signed receipt (R17); the same-model refusal and k ≥ 2 (R18).

**Deliberately last, and not because it is unimportant:** the β corpus work (R6 plus a real-fault
corpus reconstructed from this repository's own git history — the inverted secret guard, the stub
routing ceiling, the empty-state loader, the completion-only progress artefact are all real faults
with known fixes and known commits). It is roughly a day, it upgrades β from a measurement against
imagined faults to one against real ones, and it is worthless until the review channel returns
usable verdicts, which is tier 0 item 3.

---

## 9. Open questions

1. **Halt now or at the next natural stop?** Flipping `require_known_headroom` to `True` will
   refuse cursor, grok and claude dispatch immediately, leaving only `codex-weekly` (48.0% used),
   until the `cursor about` probe reports a number again. That is the correct behaviour and the
   alternative is spending against a pool nobody is measuring — but it stops most of the build, so
   the timing is yours.
2. **Is `.harness/build_driver.py` scaffolding that dies with this build, or v1 of the
   orchestrator?** Half the remediations above are permanent architecture under the second answer
   and waste under the first.
3. **What is the cap on concurrent unattended units you can actually review?** It should be a
   constant beside `MAX_CONCURRENT`, not a habit, and only you know the number.
4. **Do you want the two refusals — production chaos injection, and full deterministic simulation
   testing — written as ADRs now?** A rejected option with its reason is the most valuable thing
   in `docs/decisions/` and the first thing people delete.

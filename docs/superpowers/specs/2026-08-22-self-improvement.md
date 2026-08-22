# Self-improvement: experiments propose, the owner activates, the instrument stays sealed

**Correction:** a disabled native promoter already exists, and arXiv:2607.05904 measured judge
reward hacking rather than improved self-consistency; what is absent is a
registered-experiment-to-authenticated-owner promotion loop protected from its own instrument.
[measured] [cited]

- **Status:** PROVISIONAL under ADR-0076; EXP-104 can kill active recursive promotion
- **Date:** 2026-08-22
- **Scope:** persistent changes to the Consilient harness; not model-weight training, gate changes,
  a new command, or a second orchestrator
- **Owner:** the principal remains the only approval authority

## Outcome

Consilient may autonomously register and run experiments, construct and test quarantined
self-change candidates, refuse them, and restore the last owner-approved state. It may not make a
candidate part of the active harness until a sealed evaluator has produced the pre-registered
evidence and a trusted principal-only ingress has approved the exact candidate digest. The
measurement apparatus is not an ordinary promotion surface. [asserted]

The minimum chain is: [asserted]

```text
registered impact contract
  -> existing run_loop sensing tick
  -> candidate work item and existing dispatch claim
  -> isolated execution by the incumbent controller
  -> native promoter proposal
  -> four-sentence owner card
  -> principal approval bound to exact digests
  -> existing commit attribution gate
  -> atomic activation
  -> drift checks or exact rollback
```

No stage or Gate A/B condition changes. `routing_orchestration_enabled` remains `false`; this is a
design for a dormant path until its prerequisites and EXP-104 pass. [asserted]

## Starting point

`src/consilient/promote.py` already classifies path strings, requires measured beta and one
before/after metric, emits `promote.accepted`, `promote.refused` and `promote.reversed` through
`events.py`, and is disabled by default. `scripts/promote_loop.py` executes the fixture candidate
and records a decision; `--apply` only reports refusal and no implementation path applies bytes.
[measured]

That is a refusal-safe prototype, not this design's acceptance instrument. `ExecutionEvidence`
contains one metric pair, `improved()` means only `metric_after > metric_before`, and the existing
reversal function records a claim without restoring or proving state. A checked-in Goodhart fixture
can improve its training score while its held-out score falls to zero. [measured:
`src/consilient/promote.py`; `tests/test_promote.py`]

The commit gate checks declared run/path attribution and overlap. It cannot prove ownership, permits
an explicit `--no-verify` bypass, and reads staged path names rather than staged content. It does not
bind a staged tree to an experiment, impact contract, owner approval or candidate, and a pre-commit
hook cannot yet know the resulting commit SHA. [measured: `src/consilient/commit_gate.py`;
`scripts/commit_gate.py`]

V0-18 currently validates declared provenance, not authenticated authorship: an event passes when
its caller-supplied actor equals its caller-supplied principal and `via` says `cli`. The source says
trusted ingress must later establish authorship, and `consil record` accepts caller-supplied JSON.
Therefore the current event check and `work_item.completed` are not owner approval. [measured:
`src/consilient/events.py`; `src/consilient/cli.py`; `src/consilient/work_items.py`]

## 1. Impact is fixed before the result

Every experiment allowed to propose a persistent harness change must add an **impact contract** to
its register entry before its first outcome is observed. The contract is part of the registration
digest and contains these canonical fields: [asserted]

| Field | Required content |
|---|---|
| `target_surface` | Exact paths or capability identifiers the result could change |
| `baseline` | Immutable owner-approved state, environment and instrument digests |
| `on_confirm` | One bounded change class the result may propose |
| `on_kill` | What is removed, disabled or left dormant |
| `on_other` | The mandatory default `no activation`; it cannot be weakened |
| `confirm_rule` | Direction, minimum effect, interval rule, safety ceilings and denominators |
| `kill_rule` | Direction, harm/boundary triggers and denominators |
| `horizon` | Fixed sample, time or compute end; no optional continuation |
| `largest_effect` | The largest plausible implementation consequence |
| `safety_floor` | Controller-supplied non-overridable authority, instrument, missing-data and beta/alpha limits |

An agent may draft the contract, but cannot author its acceptance policy. The controller inserts the
ADR-0076 safety floor, and the trusted principal-only ingress approves the exact registration digest
before the first treatment artefact, score or human label exists. A weaker confirm rule, omitted
floor, or unapproved digest is ineligible. From then on, changing any contract field creates a new
experiment ID and needs a new approval; it cannot amend the experiment whose data has been seen.
Missing observations stay in the declared denominator and follow `on_other`. [asserted]

The proposal producer performs a mechanical equality check between the recorded result and the
contract. It may emit only the declared `on_confirm`, `on_kill` or `on_other` disposition; prose,
agent confidence, a favourable secondary metric and post-hoc significance do not widen it.
[asserted]

EXP-104 is the first such contract. It can justify proposing owner-gated activation on the existing
non-instrument allowlist, or kill active recursive promotion and leave the sensing/register path
dormant. It cannot lift the owner gate, expose the hold-out set, modify the instrument or change
Gate A/B. [asserted]

## 2. The instrument is outside autonomous control

### Chosen protection

The acceptance instrument is an **incumbent-controlled sealed evaluation package**, and every file,
input and executable which can influence its verdict is off-limits to ordinary autonomous
promotion. It contains: [asserted]

- disjoint development-feedback, one-use qualification and drift-sentinel batches. The candidate
  cannot enumerate, read or write the latter two, and receives no per-item feedback; [asserted]
- the verifier, beta/alpha calculation, acceptance logic and missing-data rules; [asserted]
- a canonical manifest of commands, resolved executable versions, environment, corpus hashes,
  randomisation seed, baseline and epoch anchor; [asserted]
- the trusted transaction role in the existing `promote_loop.py`, running from the last
  owner-approved base rather than the candidate worktree; [asserted]
- an accept/refuse-only candidate interface with a fixed one-query budget. Candidate-visible output
  contains neither aggregates, per-item scores nor hidden items. [asserted]

This capability separation does not exist today: dispatch launches child harnesses in the supplied
repository with bypass permissions. It is a blocking host-level prerequisite, not a property this
document attributes to current dispatch. [measured: `src/consilient/harness.py`;
`scripts/dispatch.py`]

Under that prerequisite, the candidate has no capability to read the privileged result/card projection or raw trajectory,
or to write the controller, instrument, hold-out bank, active base, approval ingress, commit hook or
append-only trajectory. `events.py` remains the single writer; an owner projection may reveal the
aggregate table, while `recall.py` must exclude those fields and event kinds from all candidate and
builder contexts. If that separation cannot be established by the host boundary, evaluation
returns `instrument_unsealed` and activation is impossible. [asserted]

`promote.path_status()` remains the canonical pathname policy, extended rather than duplicated. The
existing script-side I/O boundary must additionally read staged index blobs/tree identity and
resolve the complete installation manifest, symlinks and imports; the pure product function does not
do those things today. Protected prefixes expand to every instrument dependency, approval ingress
and activation gate. An unknown path, symlink escape, alternate import or missing manifest entry is
protected. [measured] [asserted]

The sealed package writes the full aggregate contingency table needed for beta and alpha, its sample
size and pre-declared interval, plus counts of refusal, timeout, quarantine, missing telemetry and
boundary attempts to the privileged owner projection. A zero count is printed; absent telemetry is
`unavailable`, never zero. The candidate receives only accept/refuse. [asserted]

Each qualification batch may judge one candidate lineage once. As soon as its verdict affects an
activation or any aggregate becomes visible outside the privileged projection, that batch is
retired and cannot qualify a descendant. Drift uses a fresh pre-allocated sentinel batch per window.
Batch order, query budget and retirement are sealed before the candidate exists; exhaustion means
`no_fresh_instrument` and no activation, not reuse. Replenishment is an instrument change and needs
the owner-approved bridge path. [asserted]

This is defence in depth, not the fiction that a finite hold-out is infallible. The instrument may
still be wrong, but the candidate cannot improve its score by rewriting the ruler which decides its
promotion. [asserted]

### Why the alternatives lose

| Candidate protection | Why it is insufficient alone | Retained role |
|---|---|---|
| Frozen held-out corpus | Repeated exposure leaks information; the scoring code or environment can still be changed around it. [asserted] | Hidden items inside the sealed package, refreshed only by a separately approved epoch change. |
| Versioned baseline re-run | A corrupt new instrument can make both baseline and candidate look acceptable; a moving predecessor also hides cumulative loss. [asserted] | Re-run both the immediate predecessor and a fixed owner-approved epoch anchor with the same sealed instrument. |
| Different model-family verifier | Model families can share training data and blind spots; model agreement is not task truth. In Zhou's three-family strict ensemble, false positives remained high after optimisation. [cited] | A family may add a fact only where it executes or retrieves an independent source; it never owns the verdict by identity alone. |
| Permanently immutable instrument | It best prevents tampering, but an obsolete or discovered-bad verifier could never be repaired. [asserted] | The autonomous loop cannot change it; the owner can open a new epoch after a separate bridge and recertification experiment. |

The closest direct positive analogue is Guo et al.'s Sealed Exogenous Acceptance Loop: hidden,
outside-agent audit and whole-state rollback materially improved Atari heuristic-policy outcomes in
a small compute-matched pilot. It is encouraging, not decisive: the paper is a preprint, uses three
seeds and Atari rather than coding harnesses, reports no inferential test, links no artefact, and one
sealed run still regressed. [cited: https://arxiv.org/abs/2607.24300]

## 3. The owner gate is a cheap, exact decision

After the promoter matches a result to its impact contract, it creates a proposal event and renders
exactly four deterministic sentences in the privileged owner projection. Templates render facts; a
model does not summarise the proposal after seeing it, and the sentences are not returned through
candidate recall. [asserted]

1. `EXP-104 met <pre-registered confirm rule>; it proposes <bounded target_surface change>.`
2. `Against <predecessor> and <epoch anchor>, sealed held-out outcome was <effect and interval>; beta/alpha were <point, interval, n>; cost and every adverse count were <values>.`
3. `Candidate <digest> descends from <parent digest>, instrument <digest> was unchanged, and this changes <mechanical class> but no gate, spend, credential or outward exposure.`
4. `No reply leaves the baseline active; trigger <fixed trigger> restores <parent digest>, and scratch reversal <event/ref> restored the governed-state digest exactly.`

The card carries two actions: approve the exact candidate or refuse it. Full evidence and diff links
are available but never required to understand what the decision changes. Approval of a summary,
experiment family, branch, future candidate or mutable tag is invalid. [asserted]

The principal action must arrive through a trusted owner-only host ingress outside every child
harness capability. It mints a single-use approval bound to proposal event id, experiment and
impact-contract digest, candidate and parent digests, instrument digest, expiry and decision.
Replay, expiry or any mismatch fails closed. No signing key, bearer token or authentication material
enters the repository, task prompt, trajectory or candidate environment. [asserted]

`events._check_human_authority()` continues to reject agent-attributed authority, but activation
also requires proof from this trusted ingress. Until that ingress exists and its bypass test passes,
the current promoter remains disabled; shell-written `human_decision`, a middle-manager response and
`work_item.completed` are structurally ineligible. [asserted]

## 4. Mechanical autonomy boundary

The controller sorts a proposed effect from staged index paths, the resolved active-installation
manifest, the impact contract and an exact preimage. The agent's description, confidence and claim
of reversibility are not inputs. [asserted]

| Mechanical class | Disposition |
|---|---|
| `candidate_only` — artefacts quarantined outside every active load path | autonomous create, execute, retain or discard |
| `sensing_only` — a registered run against a frozen instrument with no persistent active mutation | autonomous within existing budget and workspace authority |
| `active_harness` — any changed byte reachable by dispatch, instructions, routing, recall, coordination, work items, promotion, commit enforcement or an installed skill/adaptation | principal approval of the exact digest before activation |
| `instrument` — verifier, metric, beta/alpha code, hold-out data, manifest, baseline/anchor, acceptance rule, event writer, approval ingress or their tests | refused by ordinary promotion; principal approval plus a separate recertification/bridge experiment opens a new epoch |
| `exact_rollback` — restoration to a previously owner-approved digest whose recovery proof passes | autonomous when a pre-registered drift or safety trigger fires |
| `existing_principal_effect` — spend, credential, external exposure, gate/spec approval, verdict or surviving preference | refused/unavailable until that effect has its own trusted principal ingress; self-improvement grants no new authority |
| `unknown_or_mixed` — missing manifest, ambiguous path, dependency escape or more than one class | no activation; record a capability gap |

An active harness change is owner-gated even when `git revert` could restore its bytes. Its semantic
failure can corrupt later evidence before anyone knows to revert it. This narrows ADR-0033's broad
reversibility default for self-change while extending ADR-0018's accepted protected apparatus.
[asserted]

One Owner remains accountable. Extra agents are admitted only for a named different class of facts:
for example candidate construction, sealed executable observation, or primary-source retrieval.
Agents rereading the same diff, votes, and family labels without an independent observation are
echo and are cut. A candidate sees one verifier contract; retries do not shop among judges.
[asserted]

## 5. Activation, rollback and drift

### Activation transaction

Before the owner card is eligible, the trusted `promote_loop.py` transaction performs forward and
reverse in an isolated copy. It records the parent, candidate, instrument and impact-contract
digests; applies the candidate; runs the frozen suite and sealed evaluation; restores the parent;
and proves canonical equality over the entire governed tree while the protected-instrument digest
remains unchanged. The proof includes failed commands and adverse counts, not only exit status.
[asserted]

After exact approval, the existing pre-commit script gains one conjunct: parent SHA and staged tree
hash must match the approved candidate, experiment, impact contract, instrument and claimed paths.
An index mutation refuses; a `--no-verify` commit is simply ineligible for activation. A controlled
post-commit `promote_loop.py` step verifies the resulting commit SHA and tree before consuming the
approval. [asserted]

That step atomically replaces a protected, gitignored `.harness/active-harness.json` pointer using
the platform's replace primitive. `promote_loop.py` is its sole updater; `dispatch.py` must become
its sole consumer and resolve the pointer before starting a **fresh** child process. This pointer and
its alpha projection are required extensions, not existing capabilities; an already-running process
with imported modules is not post-activation evidence. [asserted]

The trajectory cannot yet carry this authority: ordinary event append closes a file without an
explicit process lock, flush or fsync. Before activation is implemented, `events.py` must provide one
process-serialised, flush-and-fsync append path (including the parent-directory durability needed for
a new daily file). The event stream is the write-ahead record; no second journal is added.
[measured: `src/consilient/events.py`] [asserted]

Activation ordering is fixed: authenticate approval; append and fsync an exact
`promote.activation_intent`; create the commit; verify its SHA/tree; append and fsync
`promote.commit_bound`; atomically replace and durably flush the pointer; then append and fsync
`promote.observing`. Approval is consumed by the durable intent, so a restart can resume the exact
transaction idempotently. A crash before the pointer swap leaves the old harness active; a crash
after it leaves durable approval/commit evidence from which `promote_loop.py` either enters
observation or rolls back. No candidate byte becomes active before its authorisation record is
durable. [asserted]

Only one self-change may be in its observation window at a time. Exact coordination claims protect
the short editing/execution window but cannot enforce this durable state. `promote_loop.py` therefore
uses one exclusive promotion-transaction lock and a trajectory projection gate which refuses a new
activation while any prior candidate is `activating`, `observing` or `rolling_back`. Recovery is
decided from durable pointer/tree evidence, not a stale lock file. This costs throughput but preserves
attribution; stacking candidates would make a regression's cause unknowable. [asserted]

### Rollback

A pre-registered safety, drift, missing-telemetry or instrument-mismatch trigger autonomously moves
the active pointer back to the last owner-approved parent. The controller then: [asserted]

1. recomputes the governed-tree and instrument digests;
2. requires exact equality with the stored parent and instrument preimages;
3. re-runs the frozen canary and baseline probes; and
4. appends `promote.reversed` only after proof, with trigger, attempted/restored digests, every
   command outcome and verification event ids.

The schema distinguishes `promote.rollback_attempted`, proved `promote.reversed` and
`promote.rollback_unproven`; central validation requires candidate/parent/instrument digests,
trigger, commands, outcomes and verification event ids for each applicable state. If any equality or
probe fails, the harness remains stopped at the last independently known-good controller and records
`rollback_unproven`; it does not report a successful reversal. Append-only history is never rolled
back. The current three-field `reverse()` record is insufficient and must be extended. [measured]
[asserted]

### Slow drift

Every candidate is compared with both its immediate predecessor and the fixed owner-approved epoch
anchor on the same fresh sealed batch. The existing `run_loop.py` sensing cadence consumes the next
pre-allocated sentinel batch after activation and at the registered observation intervals; it
creates no second scheduler and never reuses a batch whose result affected the lineage. [asserted]

For each window, the projection reports joint executable-and-human acceptance, beta, alpha, sample
sizes and intervals; tokens, wall time, model calls and owner review time; refusal, timeout,
quarantine, missing and rollback counts; and change from predecessor and epoch anchor. A cumulative
drift budget is fixed in the impact contract. Crossing it, losing telemetry, changing an instrument
digest or touching a hidden item triggers rollback rather than a request for agent judgement.
[asserted]

Synthetic or self-generated cases may expand training and adversarial search but never replace
human-labelled, task-native or independently retrieved anchor evidence. Shumailov et al. show that
recursive replacement with model-generated data can lose distribution tails; this is a narrow
training-data analogy, not evidence that this runtime loop itself will collapse. [cited:
https://doi.org/10.1038/s41586-024-07566-y]

An instrument change closes the epoch. A separate registered bridge evaluates old and new
instruments on the same frozen human-labelled bank, exposes disagreement and beta/alpha tables, and
requires a new exact principal approval. Old scores are not silently compared across instruments.
[asserted]

## Existing components and required extensions

No new service, database, experiment store, scheduler or CLI command is introduced. [asserted]

| Existing component | Extension when implementation is authorised |
|---|---|
| `experiment-register.md` | canonical impact-contract fields and immutable registration digest |
| `run_loop.py` | cadence, lock, timeout supervision and invocation only; generic interrupted ticks remain abandoned/unknown |
| `work_items.py` / `coordination.py` | one candidate ticket, accountable Owner and exact path claim; completion is not approval |
| `dispatch.py` | candidate construction/execution only, never acceptance; consume the protected active pointer and provide the future isolation boundary |
| `recall.py` / `instructions.py` | `write_brief()` is the future integration point for bounded assembly; current production does not use `instructions.assemble()`; privileged qualification/card fields are excluded |
| `routing.py` / `budget.py` | routing is currently unwired/fail-closed; budget is a necessary refuse-only reservation boundary, never spend authority |
| `promote.py` / `promote_loop.py` | pure policy/projection in the former; sealed evaluate/apply/reverse and idempotent transaction recovery in the existing script role |
| `events.py` | sole process-serialised, flush/fsync validation/append and write-ahead chokepoint; trusted host ingress authenticates separately and supplies a non-secret proof |
| `commit_gate.py` | pre-commit staged-tree/approval binding; post-commit `promote_loop.py` verifies resulting SHA/tree before activation |

The privileged event projection is derived from the append-only trajectory and can be deleted and replayed.
The minimum promotion record binds experiment, impact-contract, candidate, parent, instrument,
hold-out-manifest and result digests; pre/post/rollback state; proposal and trusted-ingress approval;
commit SHA; observation window; beta/alpha tables; costs; adverse counts; and all refusal reasons.
Secret or hidden-item contents never enter the event. Candidate capabilities cannot read the raw
trajectory or this projection; the ordinary recall projection omits its score and card fields.
[asserted]

## State machine and refusal rules

```text
registered -> running -> result_matched -> quarantined -> reversal_proved -> proposed
proposed + exact owner approval -> activating -> observing -> retained
proposed + refusal/expiry/mismatch -> quarantined
observing + trigger -> rolling_back -> rolled_back
any state + instrument/authority/telemetry violation -> refused or rollback_unproven
```

Transitions are monotonic append-only facts. Generic `run_loop.py` ticks retain their current
at-most-once rule and mark interruption abandoned with unknown effects. On a later ordinary cadence
invocation, `promote_loop.py` alone inspects durable pointer/tree artefacts for an incomplete
`activating` or `rolling_back` transaction and either proves rollback or stops
`rollback_unproven`; it never guesses forward. Duplicate, reordered, expired or partially bound
events refuse. [measured] [asserted]

## Bar and killing experiment

The direct bar is not “better than the initial harness”. Wang et al. found that, under matched
five-sample budget on Terminal-Bench 2.1, harness evolution did not significantly improve a disjoint
test split and simple parallel/sequential inference was stronger on several reported measures. The
bar is therefore improvement over matched extra inference/feedback compute on unseen tasks, with no
worse beta/alpha or unit cost—not a training score or candidate count. [cited:
https://arxiv.org/html/2607.12227v1]

EXP-104 pre-registers that comparison. Its full fixed rule lives in the experiment register. It is
separate from EXP-12 (strong/weak verifier compounding), EXP-13 (evolving the verifier), EXP-78
(known-bad promoter false acceptance) and EXP-103 (general recovery-certified autonomy). [measured]

## The strongest case for not building it

The strongest case is that “recursive self-improvement” is an attractive name for adaptive test
overfitting. Direct coding-harness evidence is thin: the strongest matched-budget study found no
significant held-out gain, while the closest sealed-loop evidence is a small unpreregistered Atari
preprint. Reference-free judges can be optimised from apparent success to a very large hidden-truth
gap, and a finite instrument can never prove it contains every failure. [cited]

A loop which changes active behaviour faster than independent labels arrive expands exposure while
making beta less identifiable. Owner cards do not fix a bad instrument, and an owner presented with
cheap but misleading summaries can become a signature oracle. The honest conclusion today is not
that recursive self-improvement works; it is that active recursive promotion stays disabled while
the sealed instrument, authenticated owner ingress and EXP-104 are absent. [asserted]

This specification still records the dormant path because registration, quarantine, sensing and
exact rollback are useful without granting activation authority. EXP-104 is allowed to kill the
active mechanism entirely. If it does, no weaker secondary metric or new name resurrects it; a new
registered experiment with a genuinely different external anchor is required. [asserted]

## Acceptance checks for a future implementation

Implementation is not authorised by this specification. When authorised, each boundary ships with
its bypass test in the same commit: [asserted]

- mutate every instrument dependency and alternate import path; all must refuse before candidate
  execution; [asserted]
- let the candidate improve training while held-out and human outcomes fall; promotion must refuse;
  [asserted]
- try to register a weaker safety floor, run an unapproved contract, query qualification twice, or
  retrieve a prior score/card through recall; all must refuse; [asserted]
- forge actor/principal fields through the current CLI, replay an approval and mutate one staged
  byte after approval; all must refuse; [asserted]
- interrupt each activation/rollback transition and restart; the active digest must end at the last
  owner-approved state or a stopped `rollback_unproven` state; [asserted]
- terminate the process/power boundary after every write-ahead append, commit and pointer replace;
  no active tree may lack a durable approval/commit record, and replay must resume idempotently;
  [asserted]
- apply individually acceptable small regressions until the epoch budget crosses; automatic
  rollback must fire; [asserted]
- delete the projection and replay the trajectory; proposal, approval, active state, adverse counts
  and refusal reasons must be identical; [asserted]
- scan commands and public surfaces: six CLI commands, `routing_orchestration_enabled=false`, no
  gate change, no second event writer and no candidate access to secrets or hidden items. [asserted]
- prove existing dispatch fan-out and model-family agreement cannot emit a promotion verdict;
  only the sealed task-native instrument may apply the registered rule. [asserted]

## Sources

- Wang et al. (2026), *Rethinking the Evaluation of Harness Evolution for Agents*,
  arXiv:2607.12227v1. [Full text](https://arxiv.org/html/2607.12227v1)
- Chenyu Zhou (2026), *More Convincing, Not More Correct: Self-Play Reward Hacking of
  Reference-Free LLM Judges*, arXiv:2607.05904v1. [Full text](https://arxiv.org/html/2607.05904)
- Guo et al. (2026), *Self-Authored Verification Is Unreliable in Heuristic Self-Improving Agents*,
  arXiv:2607.24300v1. [Abstract and paper](https://arxiv.org/abs/2607.24300)
- Shumailov et al. (2024), *AI models collapse when trained on recursively generated data*,
  Nature 631, 755–759. [DOI](https://doi.org/10.1038/s41586-024-07566-y)

# 0076. The owner gates persistent self-change and the acceptance instrument stays sealed

**Correction:** a disabled native promoter already exists, and arXiv:2607.05904 measured judge
reward hacking rather than improved self-consistency; the missing capability is a
registered-experiment-to-authenticated-owner promotion loop protected from its own instrument.
[measured] [cited]

- **Status:** PROVISIONAL — EXP-104 can kill active recursive promotion
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (owner-gated direction, quoted in the dispatch brief); Codex dispatch
  `20260822T125228-71bd955c73` (provisional mechanism)
- **Inquiry tier reached:** T1 ground; T3 registered as EXP-104, not run
- **Executable model:** none — the decision is a fail-closed authority/instrument boundary;
  EXP-104 measures its disputed outcome benefit

## Context

The principal asked for autonomous experiments whose impactful results can update Consilient
through his agents. The result-to-change half is not wired, but the brief's claim that it exists in
no form is too broad: `promote.py` and `promote_loop.py` already provide a disabled, refusal-safe
prototype. [measured]

That prototype is not safe to activate. It accepts one before/after metric when `after > before`,
classifies pathname strings against an allowlist and current beta threshold, and records rather than proves a reversal. Its
Goodhart fixture improves the training metric while held-out performance falls to zero. The commit
gate checks declared run/path attribution and overlap, not ownership or staged content, and cannot
bind a candidate to its experiment, instrument, principal approval or resulting commit. The script
never applies candidate bytes. [measured: `src/consilient/promote.py`; `scripts/promote_loop.py`;
`tests/test_promote.py`; `src/consilient/commit_gate.py`]

The apparent owner check is also incomplete. `events.py` validates caller-declared `actor`,
`principal` and `via=cli`, while the generic record command accepts caller-supplied JSON; the source
explicitly says trusted ingress must later establish authorship. An agent with the same shell
capability can therefore manufacture the current event shape. [measured: `src/consilient/events.py`;
`src/consilient/cli.py`]

ADR-0018 already accepts measured-beta-gated self-modification and keeps the verifier, beta meter,
budget, permissions and trajectory outside self-modification pending EXP-12/EXP-13. This ADR extends
that decision; it does not replace those safeguards. It narrows ADR-0033's broad “reversible means
autonomous” default for changes to active harness behaviour, because a semantically bad change can
corrupt the evidence which would trigger its reversal. [measured] [asserted]

ADR-0049 makes experiments decision inputs rather than permission to construct, ADR-0050 requires
the largest plausible effect, ADR-0051 forbids a second loop/scheduler and self-changing admission
rules, and ADR-0067 defaults to one accountable Owner with extra members only for genuinely
different facts. This decision must compose with all four. [measured]

## Decision

Consilient will extend the existing experiment, event, work-item, dispatch, promotion, run-loop and
commit-attribution paths into one dormant self-improvement chain. A pre-registered impact contract
may create and test a quarantined candidate autonomously, but persistent activation requires a
sealed incumbent-controlled instrument and a trusted principal-only approval bound to the exact
candidate. Ordinary autonomous promotion can never change that instrument. [asserted]

### Pre-registered impact contract

Before the first result, every experiment capable of proposing a harness change records exact
target surfaces, immutable baseline and instrument digests, `on_confirm`, `on_kill`, `on_other`,
confirm/kill rules with denominators and intervals, horizon, and largest plausible effect. The
controller supplies a non-overridable floor: `on_other` is no activation; missing data cannot
confirm; authority/instrument/rollback breaches kill; and fixed beta/alpha safety limits apply. An
agent may draft the rest, but the trusted principal-only ingress must approve the exact contract
digest before any treatment artefact or result. Independently labelled calibration material may
already exist only when sealed before rule drafting and hidden from every proposer, controller,
promoter, analyst and principal. A digest with fields left to fill, a weaker floor or a later change
is ineligible and requires a new experiment ID and approval. [asserted]

The v0 floor is mechanical. `candidate_only`/`sensing_only` permits no active mutation or outward
effect. One `active_harness` candidate on the fixed allowlist requires at least 30 independently
human-rejected self-change conditionals and human-labelled promoter beta 95% upper bound `<0.20`;
candidate-versus-incumbent downstream task-verifier beta and alpha each require at least 30 applicable conditionals and one-sided 95% harm upper bounds
`<=0.05`; the registered joint outcome must improve; only one candidate is exposed/observed at once.
Instrument, principal-only, unknown or escaped effects have zero autonomous exposure and the first
breach kills the active path. Experiments may tighten these constants, never relax them; changing
them needs a new ADR. These are ADR-0076's provisional constants and have no activation authority
until principal adoption. Current human-labelled beta is unestimated. [measured] [asserted]

Here `qualification_accept` is the sealed instrument's candidate verdict before any beta gate, and
`beta_promote = P(qualification_accept | independent human rejects the self-change)`. Calibration
cannot call the final live promotion decision, which already requires measured beta. Downstream
`beta_task = P(task verifier accepts | human rejects the delivered artefact)` cannot substitute for
it. A live decision accepts only a typed `PromoterBetaReceipt` bound to the self-change surface,
instrument, candidate-generation policy, sampling frame and interval; a generic `Beta` or mismatched
distribution refuses. ADR-0018 requires a threshold implied by blast radius but supplies no number:
the `<0.20` interval ceiling is this provisional ADR's strengthening of the current implementation's
point-estimate constant. Current human-labelled promoter beta is unestimated, so promotion refuses
before downstream non-inferiority is considered. [measured] [asserted]

Before data, the principal sees three deterministic sentences: question/target/largest plausible
effect; confirm/kill/no-activation-other thresholds, denominators, horizon and floor version; and the
exact registration digest with “no reply means no run; any edit needs a new ID and approval”. This is
trusted-ingress V0-18 specification approval, not work-item completion. [asserted]

The promoter mechanically matches the completed result to that contract. It cannot substitute a
secondary metric, model confidence, consensus or post-hoc threshold. Missing observations remain in
the fixed denominator and select `on_other`. EXP-104's contract may propose owner-gated activation
only for tracked `.agents/skills/` bytes or kill active recursive promotion; it cannot lift any
owner, instrument, budget, workspace or Gate A/B boundary. `.harness/adapted/` is a trajectory-
projected logical surface rather than a committed blob and remains dormant pending a separately
specified authenticated write-ahead event transaction. [measured] [asserted]

### Sealed acceptance instrument

The acceptance package contains development feedback plus disjoint, one-use hidden qualification
and drift-sentinel batches; verifier and
beta/alpha calculations; missing-data and acceptance rules; resolved commands, executable versions,
environment, seeds and hashes; an immediate baseline and a fixed owner-approved epoch anchor; and
the trusted transaction role in existing `promote_loop.py`. It runs from the incumbent state, not
the candidate worktree. The candidate receives one accept/refuse result; only a privileged owner
projection receives the aggregate table and required adverse counts. [asserted]

The candidate cannot read the privileged projection/raw trajectory or read or write the hold-out,
instrument, controller, anchors, owner ingress, event writer or commit enforcement. This separation
does not exist today: dispatch launches child harnesses in the supplied repository with bypass
permissions, so host isolation is a blocking prerequisite. `promote.path_status()` remains the
canonical pathname policy; the existing script-side I/O boundary must separately inspect staged
blobs/tree identity and resolve manifests, symlinks and imports. Unknown paths, dependency escapes
and missing entries are protected. [measured] [asserted]

Construction and candidate execution use different host capabilities. A builder sees a sanitised
source snapshot and only an allowlisted trusted model broker plus fixed local tool IPC; it holds no
provider credential or general network route. Every command capable of executing candidate-authored
bytes runs in a separate fully offline disposable scratch tree. Both roles deny external
repositories, publishing/payment sinks, devices and non-scratch writes; execution also denies all
network and non-controller IPC, and its deadline kills the whole descendant tree. An unavailable
isolation primitive or escaped effect is `candidate_unexecutable`, not an owner question. Current
dispatch provides neither boundary. [measured] [asserted]

A qualification batch receives one query for one candidate lineage and is then retired when its
verdict affects activation. A fresh pre-allocated sentinel batch is consumed per drift window.
`recall.py` excludes aggregate results and cards from candidate/builder contexts; exhaustion is
`no_fresh_instrument`, not batch reuse. Replenishment follows the owner-approved instrument bridge.
[asserted]

A frozen hold-out alone loses because repeated results leak information and scoring may still move.
A versioned baseline alone loses because a corrupted ruler can bless both candidate and baseline,
and predecessor-only comparisons hide cumulative loss. A different model family alone loses
because correlated blind spots and shared evidence are not task truth. Permanent immutability loses
because a discovered-bad instrument could never be repaired. The chosen composition keeps hidden
items and both baselines inside a sealed package, while reserving instrument replacement to a
separate owner-approved bridge experiment and a new epoch. [asserted]

### Owner gate

The promoter renders exactly four deterministic sentences in the privileged owner projection: the
experiment/rule and candidate digest; candidate versus predecessor/epoch-anchor effect, promoter beta and downstream beta/alpha
with intervals and `n`, cost and every adverse count; the consumer's executed before/after behaviour,
largest plausible effect, parent/instrument digests and untouched protected effects; and no-reply
behaviour plus the tested rollback trigger and restored digest. The trusted controller derives the
semantic sentence from the pre-registered target/consumer manifest and executed probes, not
candidate prose. If it cannot render one bounded observable change, activation refuses; the
principal is not handed a diff to discover the effect. [asserted]

Approval arrives only through a trusted owner-only host ingress outside child-harness capability.
It is single-use and bound to proposal, experiment/impact-contract, candidate, parent and instrument
digests, expiry and decision. Replay, expiry, staged-byte mutation or digest mismatch refuses.
Authentication material is never placed in the repository, candidate environment, prompt or
trajectory. [asserted]

The existing local `consil dashboard` projection displays the card without sending it externally.
An extension of the existing `promote_loop.py` script, not a seventh `consil` command, requests
OS-authenticated owner presence for that proposal and emits a host-verifiable attestation over the
exact bindings. A child cannot invoke the owner broker or write its output. No usable platform
boundary means no token and no activation. [asserted]

V0-18's declared-provenance validation remains necessary but is not treated as authentication.
Until the ingress and its bypass test exist, the promoter remains disabled. A shell-authored event,
agent approval, mutable tag, work-item completion or approval of a candidate family is ineligible.
[asserted]

### Mechanical autonomy boundary

The staged index and resolved installation manifest, not agent judgement, produce one exact class:
[asserted]

- `candidate_only` and `sensing_only` are autonomous while isolated and within existing authority;
  [asserted]
- every `active_harness` byte requires exact principal approval before activation; [asserted]
  **PROPOSED alignment clarification (2026-08-23; principal acceptance required):** this maps to
  ADR-0075's existing top-level `principal_authority` class and V0-18 subtype `approval`; it is not a
  seventh escalation class. The approval remains bound to the exact candidate bytes/tree and cannot
  be agent-authored. [cited: ADR-0075] [asserted]
- `instrument` is refused by ordinary promotion and requires principal approval plus a separate
  bridge/recertification experiment; [asserted]
- `exact_rollback` to a previously owner-approved digest is autonomous after a registered trigger
  and executed recovery proof; [asserted]
- existing spend, credential, external exposure, verdict, gate/spec and genuine-preference classes
  remain refused/unavailable until their own trusted principal ingress exists; [asserted]
- unknown, mixed, missing-manifest or escaped effects refuse activation and record a capability gap.
  [asserted]

One accountable Owner and one candidate remain the default while human-labelled beta is
unestimated. Another agent is admitted only for a named different fact, such as executing the
artefact or retrieving a primary source. Same-evidence reviews and votes are echo. A candidate sees
one verifier contract and cannot shop among judges. [measured] [asserted]

### Activation, rollback and drift

Before rendering the card, trusted `promote_loop.py` applies then reverses the candidate in an
isolated copy and requires exact governed-tree equality to the parent, unchanged instrument digest,
and successful frozen canaries. After exact approval, the existing pre-commit script binds parent
SHA and staged tree hash to the approval; a `--no-verify` commit is ineligible. A controlled
post-commit step verifies resulting SHA/tree and only then consumes approval. [asserted]

The candidate commit exists only in an isolated inactive worktree and is materialised into an
immutable versioned installation directory outside every supported runtime cwd. It never changes
the live source worktree's `.agents/skills/`. A protected gitignored
`.harness/active-harness.json` pointer binds installation directory, commit and tree; `promote_loop.py`
is its sole updater. Every supported product skill-loading path, including dispatch and any direct
harness wrapper, must resolve it before starting a fresh child. If an inactive worktree or source-tree
candidate remains discoverable, active promotion stays disabled. One exclusive promotion transaction
plus a projection gate refuses activation while another candidate is `activating`, `observing` or
`rolling_back`; ordinary expiring coordination claims alone cannot serialize the observation window.
[asserted]

The commit/SHA transaction admits tracked `.agents/skills/` only. It cannot bind an event-projected
adaptation payload, so `.harness/adapted/` refuses activation rather than borrowing a commit's
authority. [measured] [asserted]

Current ordinary event append has no explicit process lock, flush or fsync, so it cannot yet be an
activation authority. Before implementation, `events.py` becomes the single process-serialised,
flush/fsync write-ahead path. Activation durably records `promote.activation_intent` with the exact
approval before commit, verifies the resulting SHA/tree, durably records `promote.commit_bound`,
atomically replaces and flushes the pointer, and only then records `promote.observing`. Restart uses
those durable facts idempotently: before pointer swap the old harness remains active; after swap the
approval and commit record already exist, so `promote_loop.py` observes or rolls back rather than
guessing. [measured] [asserted]

Registered drift, safety, telemetry and instrument-mismatch triggers autonomously restore the last
owner-approved pointer. Success requires parent and instrument digest equality plus a fresh sealed
canary; otherwise the system records `promote.rollback_unproven` and remains stopped. The schema
distinguishes `promote.rollback_attempted`, proved `promote.reversed` and unproved rollback, and pins
the trigger, state/instrument digests, command outcomes and verification ids. Current `reverse()` is
too small and may not emit `promote.reversed` until actual restoration passes. Append-only events are
never reverted. [measured] [asserted]

Each observation window compares the candidate with both its immediate predecessor and its fixed
epoch anchor on the same fresh sentinel batch and reports joint executable/human outcome, beta,
alpha, intervals and denominators;
costs; refusals, timeouts, quarantines, missing telemetry and rollbacks; and cumulative drift.
Crossing the pre-registered epoch budget triggers rollback. `run_loop.py` supplies the existing
sensing/resumption cadence; no second scheduler or result store is added. [asserted]

Synthetic/self-generated evidence may train or probe candidates but never replaces preserved real,
human-labelled or task-native anchor evidence. An instrument change closes the epoch and must bridge
old and new verifier/scorer code on one frozen overlap set before a new principal approval; every
bridge item then retires from candidate qualification. Corpus refresh instead requires independent
provenance/licence and blinded label audit plus untouched new qualification/sentinel partitions—the
old bank cannot validate its replacement. Scores from different instruments are not silently
combined. [asserted]

## Evidence

- `[measured]` The current promoter is disabled, protects specified paths, requires measured beta
  and execution, and admits only `.agents/skills/` and `.harness/adapted/`; it neither consumes the
  experiment register nor authenticates an owner or applies a change.
- `[measured]` `ExecutionEvidence` has one metric pair and `improved()` is only a strict increase;
  the checked-in Goodhart fixture demonstrates training improvement with held-out collapse.
- `[measured]` The commit gate checks declared live run/path attribution and overlap, not ownership,
  experiment/result/approval or exact candidate/commit identity.
- `[measured]` The authority validator itself states that trusted ingress must later establish
  authorship; current CLI JSON is caller supplied.
- `[cited]` [Guo et al. (2026)](https://arxiv.org/abs/2607.24300) report that a sealed external
  audit plus rollback improved nine, tied two and worsened one of twelve Atari model/game
  comparisons; the study is a three-seed preprint without a linked implementation artefact.
- `[cited]` [Zhang et al. (2026)](https://arxiv.org/abs/2505.22954) report held-out
  cross-benchmark transfer for Darwin Gödel Machine: SWE-evolved harnesses moved Polyglot from 14.2
  to 28.9 and Polyglot-evolved harnesses moved SWE-bench from 20.0 to 24.5. The paper also records an
  evaluator-bypass episode and does not measure beta.
- `[cited]` [Zhou (2026)](https://arxiv.org/html/2607.05904) reports a reference-free judge pass
  rate rising from 0.716 to 0.938±0.016 while hidden exact-match accuracy moved from 0.209 to
  0.202±0.005 on one GSM8K/Qwen3-4B condition (1,319 items, three seeds).
- `[cited]` [Shumailov et al. (2024)](https://doi.org/10.1038/s41586-024-07566-y) show distribution
  tails being lost when generated data recursively replaces original data. Applying that result to
  runtime harness records is an analogy, not a measured transfer.
- `[algebra]` Comparing only successive scores admits arbitrarily large cumulative degradation:
  `D_epoch = sum(d_i)` even where each individual `d_i` is below its local alarm threshold.
- `[asserted]` Sealing the ruler outside the candidate's capability and retaining a fixed epoch
  anchor bound instrument corruption and slow drift better than any candidate self-certification.

## Evidence against

- `[cited]` [Wang et al. (2026)](https://arxiv.org/html/2607.12227v1) found no significant held-out
  gain from harness evolution on a disjoint Terminal-Bench 2.1 split: average gain was 0.6 points;
  under matched five-sample budgets, ordinary parallel/sequential inference was stronger on several
  reported measures. This is the closest direct result and argues for spending compute on attempts,
  not building recursion.
- `[cited]` DGM is substantial contrary evidence to a blanket “self-change cannot improve” claim,
  but its SWE-bench component is qualified by [OpenAI's 2026 audit](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
  of material task defects and benchmark exposure; the Polyglot transfer remains promising and
  still does not test a sealed, owner-gated or beta-measured loop.
- `[cited]` Guo et al.'s positive sealed result is Atari heuristic-policy work, not a coding harness;
  it uses three seeds, no inferential test or preregistration, and its finite audit still admitted a
  deployment regression from 17.6 to 13.8 while audit performance rose.
- `[cited]` Zhou's result shows that optimisation can make a verifier much more convinced without
  making the policy more correct. A hidden finite instrument does not eliminate adaptive overfit;
  each accept/refuse bit leaks information to the search.
- `[measured]` Consilient has not measured human-labelled promoter beta at the required denominator,
  the owner ingress is unauthenticated, and rollback currently records rather than proves restore.
  The preconditions for active recursion therefore do not exist.
- `[asserted]` The instrument-corruption problem may be unsolvable, not merely hard. Any finite
  corpus and verifier are proxies; a sufficiently persistent optimiser may find a blind spot without
  reading or rewriting either.
- `[asserted]` A system which changes active behaviour faster than independent labels arrive makes
  beta less identifiable. Owner review of four sentences can become rubber-stamping if those
  sentences are produced by a corrupt instrument.
- `[asserted]` Recursive self-improvement increases attack surface, state-space and attribution
  difficulty. The dormant register/quarantine path is useful, but the active mechanism may add no
  value beyond matched extra inference.

These objections are not answered by claiming the loop is safe. The decision concedes them: active
promotion stays disabled until the instrument/ingress boundaries exist and EXP-104 clears the
matched-compute bar; any breach or kill result removes the active path while retaining evidence and
quarantine. [asserted]

## Consequences

**Positive** — experiment effects are fixed before outcomes, candidates cannot grade themselves,
the principal receives a bounded decision rather than an audit task, and drift/rollback are tied to
exact state. [asserted]

**Negative** — every persistent self-change costs one principal decision; sealed evaluation and
one-at-a-time observation reduce speed; fresh external labels remain expensive; an imperfect
instrument can still accept harm. [asserted]

**Neutral but load-bearing** — `events.py` remains the sole library validation/append chokepoint,
while trusted ingress authenticates separately. The only call direction is `run_loop.py` cadence →
`promote_loop.py` transaction → a `dispatch.py` builder adapter or offline executor. That adapter may
transport one exact request but cannot schedule, route, retry, accept or persist promotion state;
reverse invocation refuses. `promote_loop.py` owns the trusted transaction; `run_loop.py` retains
at-most-once/abandoned generic tick semantics; the
experiment register remains the only experiment system. Fan-out or family agreement can add a named
observation but can never produce the promotion verdict. The CLI remains six commands and
`routing_orchestration_enabled` remains false. [asserted]

## Enforcement

This commit records a specification, this provisional ADR and EXP-104; it changes no product code,
gate, command or routing flag. [measured]

Future implementation must ship, in the same commit as each boundary: staged-index and alternate
load-path classification tests; candidate/hold-out/instrument isolation tests; Goodhart and missing-
telemetry refusals; forged/replayed/mismatched owner-approval refusals; experiment/approval/commit
binding; typed promoter-beta/task-beta substitution refusal; one-query batch retirement and recall
non-disclosure; inactive-installation/direct-load bypass refusal; transaction serialization;
interruption/restart recovery in `promote_loop.py`; exact applied rollback; cumulative drift
rollback; fresh-process pointer consumption; fan-out non-authority; and projection-delete/replay
equality. Termination injection after each append, commit and pointer replace must prove that no
active tree lacks durable approval/commit evidence. Central event validation must reject incomplete
proposal, approval, activation and rollback shapes. [asserted]

Candidate isolation tests also attempt network/IPC, credential, metered-provider, external-repository,
payment/publish, device, parent/instrument/trajectory read, non-scratch write and descendant-process
escape. Any available path refuses implementation. [asserted]

- **Check:** the future checks above; this specification-only commit claims none exists today
- **Fails CI:** no — the active path remains disabled
- **Added in the same commit as the implementation:** required

## What would overturn this

EXP-104 first requires a disjoint calibration with at least 30 independently human-rejected
self-changes and `beta_promote` interval upper bound `<0.20`; otherwise no Arm-C change activates.
It then kills active recursive promotion if it fails to beat matched extra inference on unseen joint
outcomes, breaches the owner/instrument boundary, exceeds the pre-registered downstream beta/alpha
safety margin, or cannot account for every fixed observation. A confirmed result permits only an
owner-gated proposal on the frozen non-instrument surface; it cannot make activation or instrument
change autonomous. [asserted]

One cheaper counterexample kills the relevant surface immediately: any candidate reads or changes a
sealed item/instrument dependency, an agent forges a usable approval, or an asserted successful
rollback does not restore exact governed state. [asserted]

## Publication candidate?

**No.** The direct benefit is unmeasured, the closest direct study cuts against it, and the owner
authentication and applied rollback prerequisites do not exist. [measured] [asserted]

# Model lifecycle: discover automatically, qualify before routing, and train behind a sealed instrument

- **Document class: W**
- **Review by:** 2026-09-22
- **Falsifier:** § 10 (EXP-111 and the named enforcement falsifiers).

**Class-W contract adopted 22 August 2026.** Mechanical admission only; existing claim wording and evidence tags are unchanged. [asserted]

[measured] The brief says there are three problems but specifies four; cost is independently governed,
so this specification keeps **registry, selection, fine-tuning and cost** separate.

**Status:** PROVISIONAL. EXP-111 decides whether an automatically qualified release or a consented
local fine-tune earns better accepted outcomes per unit cost than its frozen comparator. Until that
experiment confirms a path, the current hand-maintained model list remains the operational answer.
[asserted]

**Decision:** discovery may be automatic; routability may not. A revision is quarantined until its
identity, rights, capabilities, outcome vector and costs have been measured on a frozen bank. Matrix
factorisation remains an offline challenger. A local fine-tune is a new revision, not an update in
place, and is evaluated by an instrument the trainer and candidate could not influence. Exact
activation remains the principal's decision. [asserted]

**Related decisions:** ADR-0003, ADR-0005, ADR-0018, ADR-0025, ADR-0054, ADR-0056, ADR-0057,
ADR-0064, ADR-0066 and ADR-0074. ADR-0076 and ADR-0077 are working-tree proposals, not landed
guarantees at the time of this specification; their isolation and exposure rules are therefore
preconditions, not facts about the running system. [measured]

---

## 1. What exists, and what does not

[measured] `scripts/refresh_models.py` can enumerate the local Cursor catalogue and compare it with
the 22-row `MODELS` tuple in `src/consilient/harness.py`. Its `--write` mode rewrites source rows as
bare `ModelOption(...)` values. All 22 current rows consequently use the default
`reasoning_capability="unknown"`.

[measured] The current refusal is only partly fail closed. `scripts/dispatch.py` refuses an explicit
unmapped model with unknown reasoning capability, but exempts any object already present in
`MODELS`. Automatic selection may therefore choose a newly written, registered-but-unknown model on
the basis of pool headroom and registry order. Scheduling `refresh_models.py --write` unchanged would
turn discovery into unqualified adoption. This design forbids that path.

[measured] `dispatch.py` currently imports neither `routing.py` nor `budget.py`. `routing.py` is an
unwired candidate-exposure calculation, not a model selector; `budget.py` atomically refuses or
records caller-declared OpenRouter-labelled spend reservations requested by `loop.py`, but is not
coupled to a provider call. Subscription quota and money already have separate types in `usage.py`.
Dispatch records subprocess duration after queue/lock acquisition; lifecycle end-to-end wall time,
provider-equivalent cost and active human minutes do not yet exist.

[measured] A projection of the private local trajectory at `2026-08-22T14:40:41Z` found 111
`dispatch.outcome` events, zero structured model fields, zero task-family fields, one
`attempt.outcome` and one `attempt.verdict`. It is not a sparse task-by-model outcome matrix: the
required axes and accepted outcomes are absent. These time-bound aggregate counts establish the
design precondition only; no private event, prompt or command belongs in a published artefact.

[measured] The existing consent event validates purpose, retention, withdrawal and per-use commercial
fields, but trusted principal ingress is explicitly absent and no training consumer enforces a live
grant. `harvest.py` can assemble private rows, and `local_fit.py` can estimate/download for hardware
fit, but there is no trainer, sealed evaluator, checkpoint activation pointer or verified rollback.

[asserted] Therefore the minimum honest implementation is an inert lifecycle projection and one
runner around existing components. It is not an automatic updater, learned router or continuous
online trainer.

### Non-goals

- [asserted] No second orchestrator, scheduler, model database or CLI subcommand.
- [asserted] No change to `routing_orchestration_enabled`, Gate A, Gate B or the six-command surface.
- [asserted] No automatic spend, hosted training, secret-bearing provider integration or metered call.
- [asserted] No publication or cross-user reuse of a private trajectory, adapter or evaluation bank.
- [asserted] No self-reported confidence, model agreement or model name as capability evidence.
- [asserted] No recursive or per-request weight update. “Continuous” means repeated, separately
  registered batches; it never means a model changing the state used to judge itself.

---

## 2. One lifecycle over the existing machinery

[asserted] The lifecycle is a projection over events written through the existing event boundary.
The shipped `MODELS` tuple remains a bootstrap allowlist until that projection is implemented and
qualified. Discovery data is untrusted input and must never rewrite product source by itself.

| Existing surface | Lifecycle responsibility | Different class of facts |
|---|---|---|
| `refresh_models.py` | Poll an installed harness or an official release feed and emit an immutable discovery manifest; never mark it routable. | Provider-reported catalogue state. [asserted] |
| `work_items.py` + `coordination.py` | Represent and claim one qualification or training job, including its GPU/worktree paths. | Exclusive execution state, not quality evidence. [asserted] |
| `dispatch.py` | Execute frozen qualification tasks through the existing supervised harness boundary. | Candidate-produced artefacts. [asserted] |
| Task-native verifier + sealed human review | Decide executable correctness and acceptance without candidate influence. | Artefact execution and independent human judgement. [asserted] |
| `events.py` | Append lifecycle manifests, outcomes, consent references and activation proposals. | Durable provenance once the current writer/durability gaps are closed. [asserted] |
| `harness.py` | Consume only the projected `routable` set; refuse every other state and every unknown required capability. | Qualified registry projection. [asserted] |
| `routing.py` | Apply measured beta/exposure ceilings after it is wired; never infer model quality. | Verifier-error bound. [asserted] |
| `budget.py` + `usage.py` | Refuse unauthorised metered spend and preserve provider-native quota separately. | Cash authorisation and provider counters. [asserted] |
| `recall.py` + `instructions.py` | Supply bounded context to a run; never expose sealed bank contents or learned-state controls. | Prior text, not training or approval. [asserted] |

[asserted] A “role” in this table is an evidence contract, not necessarily another agent. The default
is one accountable executor. A second participant is admitted only when it brings a named class that
the first cannot already observe—for example exact bytes and a signature, an executed test result,
or a primary source checked in full. Re-reading the same manifest is echo.

[measured] `consil beta` currently reports insufficient human-labelled evidence, and the unwired
robust rule in `routing.py` refuses an unmeasured `beta_upper`. [algebra] The brief's
`floor(ln(1-e)/ln(1-beta))` is an independence diagnostic, not the operational ceiling; the robust
ceiling is `floor(e / beta_upper)` when its inputs exist. [asserted] EXP-111 therefore permits one
supervised candidate in each isolated qualification attempt, but no automatic or production
candidate exposure. Offline aggregation of sealed attempts does not authorise fan-out during a
decision.

### Lifecycle states

```text
discovered -> quarantined -> qualified -> approval_pending -> routable
                    |             |              |               |
                    +-----------> refused <------+----> stale <---+
                                                                  |
                                          retired <---------------+
```

- **`discovered`:** a source said an identifier exists. It has no capability or safety meaning.
  [asserted]
- **`quarantined`:** identity is recorded and acquisition is contained, but no ordinary dispatch can
  select it. This is the automatic destination for every new release. [asserted]
- **`qualified`:** the exact revision completed the frozen protocol with a complete outcome and cost
  vector. This is an experimental result, not permission to use it. [asserted]
- **`approval_pending`:** a proposal binds the candidate manifest, bank, instrument and result
  digests. Only the principal can move that exact digest onward. [asserted]
- **`routable`:** the principal's authenticated approval exists and every independent gate still
  passes. Since trusted principal ingress and the routing gates are not currently available, this
  transition is unavailable today. [measured] [asserted]
- **`stale`:** identity, availability, licence, capability, price source, verifier contract or base
  digest drifted. A stale revision is removed from automatic selection before requalification.
  [asserted]
- **`refused` / `retired`:** the adverse result and reason remain; the identifier is never silently
  recycled. [asserted]

[asserted] “Automatic adoption” is corrected here to **automatic discovery and qualification**.
Silent production replacement would delegate approval and would make rollback ambiguous. The
principal may approve a proposed exact digest; a manager, model or scheduled process may not approve
for him.

---

## 3. Identity and supply-chain admission

Every candidate manifest must bind the following before any candidate code or weights run:

| Field | Required meaning |
|---|---|
| `candidate_id` | New immutable lifecycle identifier; never a mutable display name. [asserted] |
| `provider`, `harness`, `model_id` | Exact routing coordinates and the pool they consume. [asserted] |
| `revision` | Hosted revision/fingerprint when exposed, or local weight digest. `latest` is not a revision. [asserted] |
| `source` | Official locator, retrieval time and the discovery payload digest. [asserted] |
| `integrity` | Local file SHA-256 and publisher signature status where available; absence remains explicit. [asserted] |
| `rights` | Licence/terms identifier, permitted use, redistribution prohibition and reviewer. Unknown rights refuse acquisition. [asserted] |
| `runtime` | Backend, quantisation, context limit, reasoning posture and measured hardware-fit receipt. [asserted] |
| `parent` | For an adapter: exact base, dataset, training code/environment and prior activation digests. [asserted] |
| `freshness` | Facts that invalidate this manifest; no guessed universal expiry. [asserted] |

[asserted] A hosted alias whose underlying revision cannot be pinned may be measured as an
**unpinnable service observation**, but it cannot silently replace a pinned incumbent. Any observed
drift makes it stale and returns it to quarantine. A local artefact without exact bytes and rights is
refused before execution.

[asserted] Release text, model cards and provider rankings are advisory claims. They can populate a
manifest and choose which checks to run; they cannot populate a measured capability or outcome.
Provider-supplied code executes only inside the existing script boundary, never inside AST-locked
`src/consilient/`.

---

## 4. Qualification before routability

### Frozen bank v1

[asserted] EXP-111 freezes 80 tasks before candidate selection or training: 20 executable code
changes with tests, 20 seeded defect repairs with withheld regressions, 20 review tasks with a sealed
defect inventory, and 20 evidence tasks with primary-source fact keys. Each task binds its starting
tree, allowed context, task-family label, verifier/instrument digest, acceptance rule and cost sources.

[asserted] The four strata supply different outcome oracles; four agents reading the same candidate
would not. The bank is content-balanced and private where necessary. Neither a trainable candidate,
its trainer nor its training-data selector can read any bank item, expected result, verifier source,
human rubric or intermediate score before the candidate artefact is sealed.

### Required checks

1. **Identity and rights.** The immutable manifest above passes; mismatch or ambiguity refuses.
   [asserted]
2. **Feasibility.** The exact runtime is reachable, completes a calibrated local fit/run, respects the
   context ceiling and emits usable usage telemetry. Missing telemetry is `unavailable`, never zero.
   [asserted]
3. **Capability.** Required tool, reasoning and context behaviours are demonstrated by frozen probes.
   An unknown required capability remains fail closed even when the ID is registered. [asserted]
4. **Outcome.** Candidate and comparator receive the same task state and ceilings in isolated runs.
   Refusal, timeout, quarantine, malformed output, missing artefact and failed verification are
   retained as adverse outcomes. No failed task is replaced and no best-of-N sample is selected.
   [asserted]
5. **Independent acceptance.** A task succeeds only when its frozen verifier and blinded human
   reviewer accept the same sealed artefact without material correction. Self-report is excluded.
   [asserted]
6. **Safety accounting.** Report the full verifier-by-human table, beta and alpha with denominators.
   Fewer than 30 human rejections or acceptances is `insufficient_safety_evidence`, not zero error.
   [asserted]
7. **Cost.** Record every dimension in section 7 for every attempt, including zeros and unavailable
   values. [asserted]

[asserted] Qualification never passes Gate A or Gate B and never changes
`routing_orchestration_enabled`. A candidate can complete the experiment while production routing
remains prohibited.

### Drift and rollback

[asserted] Discovery re-checks exact identity and advertised surface. A changed model digest,
unpinnable hosted behaviour, removed licence, failed sentinel, verifier-contract change or material
cost-source change marks the active projection stale before another automatic dispatch selects it.

[asserted] Activation stores the complete previous routable manifest. Rollback restores that exact
manifest, re-hashes every referenced local artefact and runs one frozen smoke task. A reversal event
without successful restoration is a failed rollback, not evidence of recovery.

---

## 5. Matrix factorisation: the bar, the contrary evidence and the decision

### What was searched

[measured] Full primary texts were read on 22 August 2026 after searches for `matrix factorization
LLM routing`, `LLM router cold start unseen model`, `latent factor model selection`, `adaptive LLM
evaluation` and `new model routing`. Generic recommender-system cold-start papers were excluded from
the performance claim because analogy is not a repository outcome. The bounded readings are recorded
in `docs/10-research/bibliography.md`.

| Bar | Measured evidence | Limit that matters here |
|---|---|---|
| [RouteLLM](https://arxiv.org/abs/2406.18665) | 65,000 retained pairwise preferences among 64 models trained its MF router. [cited] | Arena-only MF was worse than random on out-of-domain GSM8K; transfer chooses between a prespecified strong/weak pair, not an arbitrary new N-way candidate. [cited] |
| [EmbedLLM](https://arxiv.org/abs/2410.02223) | A complete 112-model × 36,054-question matrix; its smallest 1,000-question condition still contains 112,000 outcomes. [cited] [algebra] | A new model requires retraining. Benchmark-accuracy predictions had statistically significant Kendall rank correlation on 7/10 benchmarks; the paper reports no significance test for the MF–KNN margin. [cited] |
| [RouterBench](https://arxiv.org/abs/2403.12031) | 405,467 outcomes over 11 models, eight datasets and 64 tasks. [cited] | Learned KNN/MLP routers did not significantly beat the static cost-quality `Zero` router overall. [cited] |
| [GraphRouter](https://arxiv.org/abs/2410.03834) | The held-out-model condition adds 80 measured interactions for each new model. [cited] | It is few-shot routing support, not zero-interaction adoption. The outcomes are benchmark accuracy/F1 [cited], not this repository's artefact-acceptance outcome. [asserted] |
| [IRT-Router](https://arxiv.org/abs/2506.01048) | About 24,000 queries across 20 models provide the response matrix. [cited] | Its metadata-only held-out-model profile has limited generalisation by the paper's own experiment. [cited] |

[asserted] The strongest positive case comes from two results. [cited] RouteLLM transfers a learned
boundary to named new strong/weak pairs, and EmbedLLM reports a small MF prediction advantage at
1,000 questions. [asserted] Neither qualifies an unseen revision: one assumes the pair ordering,
while the other must retrain to add the model.

### Recommendation: not yet

[measured] This repository currently has no structured task×model accepted-outcome matrix. [asserted]
Matrix factorisation now would assign latent factors from names, provider claims or missing values;
that violates the measured-outcome rule rather than solving cold start.

[asserted] Keep ADR-0003's simple policy: the hand-maintained bootstrap registry first; then the static
cost-quality frontier and per-task-family empirical rates when those rates exist; verifier-gated
escalation; provider headroom only as a tie-break between otherwise admissible choices. Unknown or
new task families use the best qualified static comparator, not an inferred factor.

[asserted] Reconsider learned selection only after ADR-0025's conjunctive reopen condition holds:
about 5,000 labelled routing outcomes **and** an applicable measured wasted-work multiplier of at
least 2×; model identity, task family, complete outcome vector and costs must also have adequate
coverage. Five thousand is this repository's simulated break-even, not a literature-derived
universal minimum.

[asserted] The first learned-routing study must hold out both later tasks and an entire model revision,
then compare in order: static best-qualified model, RouterBench-style cost-quality frontier,
per-family empirical rule, KNN over common probe outcomes, and MF. MF remains offline unless its
held-out lower confidence bound beats the strongest simpler rule in joint accepted outcomes per cost
without worsening beta, alpha, missingness or cold-start refusal. A later pre-registration—not
EXP-111—must fix that test after the matrix exists.

---

## 6. On-device fine-tuning

### Consent comes first

[asserted] A general user has granted nothing by using the product. Before selection or training, an
authenticated, current consent receipt must bind: the data subject and owner, exact source/dataset
manifest, training purpose, permitted base and method, retention/expiry, withdrawal effect,
commercial use, sharing/redistribution and the candidate run. Consent for recall, research or one
model does not imply consent for training another.

[measured] ADR-0066 authorises a private corpus for the principal's stated scope; it does not grant
rights over another user's data or third-party material. [asserted] Every row still needs a source
and rights decision. Unknown terms, secrets, credentials, private third-party content and withdrawn
rows are refused. The corpus, manifests, adapters and checkpoints stay gitignored and private by
default under ADR-0057.

[measured] The present principal field is not authenticated and no training consumer checks a grant.
[asserted] Consequently a recorded receipt can support an experiment proposal but cannot activate
training until trusted ingress and use-time consent enforcement exist. An agent may prepare the exact
proposal; it may not manufacture or approve consent.

### First reversible pipeline

1. **Freeze the decision.** Record the exact consent receipt, corpus-manifest digest, base candidate,
   training method, bank digest, stopping rule and deletion/retention disposition before any outcome
   is inspected. [asserted]
2. **Build the private corpus.** Reuse `harvest.py`; link accepted, rejected, refused, timed-out and
   quarantined rows to their actual verdicts; deduplicate; scan for secrets and rights; preserve
   adverse outcomes rather than training only on successes. [asserted]
3. **Seal the split.** Split training rows by provenance/lineage, not merely by row, so derivatives do
   not cross the boundary. The 80 qualification tasks, hidden defect keys, verifier code, rubrics and
   sentinels are never training or tuning data. [asserted]
4. **Pin the base.** The first candidate is the Qwen3-Coder 30B-A3B class named by ADR-0066, but the
   name is not approval. The run must bind an exact licence-cleared revision, weight hash,
   quantisation/runtime and measured RTX 5090 fit. Failure refuses; no substitute is silently chosen.
   [asserted]
5. **Train an adapter.** Use the smallest reversible on-device LoRA/QLoRA-style adapter over the
   frozen base. Record dataset, base, code, environment, seed, hyperparameters, checkpoints, wall/GPU
   time and every failure. This choice adds no dependency at specification time. [asserted]
6. **Quarantine the candidate.** The adapter has a new immutable candidate ID and cannot be selected
   by ordinary dispatch. Training success or loss reduction is not acceptance evidence. [asserted]
7. **Evaluate blind.** Compare the unmodified base, adapter and current hand-maintained incumbent on
   the frozen bank in isolated attempts with equal ceilings. The evaluator runs from the incumbent
   side and receives only sealed artefacts. The trainer/candidate cannot read, write, invoke or choose
   the bank, instrument, controller, trajectory result or human rubric. [asserted]
8. **Reveal once.** The candidate receives at most an opaque accept/refuse receipt after all outcomes
   are sealed; it never receives item scores or hidden failures that could train against the bank.
   [asserted]
9. **Propose, do not activate.** Bind the winning checkpoint, base, data, instrument and result digests
   in an approval proposal. Only authenticated principal action can make that exact manifest routable.
   [asserted]
10. **Monitor and reverse.** Run sealed sentinels on drift and retain the previous exact manifest.
    Consent withdrawal makes the adapter unroutable immediately; retention/deletion then follows the
    recorded grant and owner authority. Any further fitting is a new candidate and experiment.
    [asserted]

[asserted] Process separation, hidden filenames and hashes alone do not seal an instrument. The
runner needs an access boundary the candidate cannot call through, a one-way artefact hand-off and an
incumbent-owned controller. Until the working-tree ADR-0076 proposal lands and that isolation is
proved adversarially, local fine-tuning may prepare data only; it cannot be evaluated for activation.

---

## 7. Cost is a vector, not one invented number

For each attempt and each accepted outcome, record:

| Dimension | Definition | Governing rule |
|---|---|---|
| `actual_metered_usd` | Cash charged for this attempt from provider records. | Reuse `budget.py`'s atomic reservation transaction, but prove that it is coupled to the provider call before treating it as authorisation. Absent data is unavailable, not `$0`. [asserted] |
| `provider_equivalent_usd` | Counterfactual public list-price cost for the same named model/input/output at the retrieval-dated rate. | A comparison label, never claimed as cash saved. No hosted equivalent means unavailable. [asserted] |
| `subscription_quota` | Provider-native pool, amount/percentage, window and reset consumed. | Already-paid quota is not money and is never converted to dollars without an explicit measured contract. [asserted] |
| `wall_seconds` | Start-to-terminal elapsed time, including queue and verifier time. | Reported directly; timeouts retain their full elapsed cost. [asserted] |
| `device_seconds` | Local GPU/runtime occupancy where measurable. | Report separately from wall time; no guessed electricity or depreciation. [asserted] |
| `human_active_minutes` | Active consent, review, correction and recovery time. | Waiting while a worker runs is excluded; missing review timing is unavailable. [asserted] |

[asserted] Keep the vector intact. Quality and safety admission comes first; actual metered spend must
be authorised; among candidates that pass, prefer a Pareto improvement—no known dimension worse and
at least one better. If several remain non-dominated, preserve the existing subscription-first policy
and use measured headroom as a tie-break. Do not sum quota, seconds and human minutes with invented
exchange rates.

[asserted] `cost_per_joint_success` includes every attempted cost divided by joint successes; it is
infinite when successes are zero. A refusal is not free if it consumed quota, time or review.
Unavailable inputs prevent a price confirmation.

[asserted] “Reducing price” must name its quantity. Moving work from an already-paid subscription to
the local GPU may reduce provider-equivalent list price while reducing no actual cash at all. The
honest claim in that case is “lower provider-equivalent cost”; a total-cost or cash-saving claim waits
for measured energy, hardware and metered-spend data.

[measured] The current `budget.py` atomically refuses or records OpenRouter-labelled reservations
requested by `loop.py`; it is not coupled to the arbitrary command that `run_loop.py` later runs.
[asserted] Any later lifecycle caller or permitted vendor must reuse and extend the same
refuse-before-spend transaction and prove provider-call coupling; a second ledger or an after-the-fact
usage note is not enforcement.

---

## 8. EXP-111: the killing experiment

[measured] EXP-111 was reserved by dispatch `20260822T140634-824a8280e8` after exact scans found no
heading or competing exact reservation. Its full pre-registration is in
`docs/10-research/experiment-register.md`; the register, not this summary, is authoritative.

[asserted] The experiment freezes 80 tasks and evaluates two independent contrasts when an eligible
candidate exists:

- an automatically **qualified** unmodified release versus the current hand-maintained incumbent;
- a consented local adapter versus its unmodified base, with the current incumbent as an additional
  routability comparator.

[asserted] No candidate is “automatically adopted” in production. Each arm runs in isolation, every
failure remains, and activation remains unavailable unless the preregistered outcome gates and exact
principal approval both occur. If no eligible release or consented fine-tune exists by the deadline,
that contrast is `not_run_no_eligible_candidate`, not fabricated evidence for or against it.

[asserted] EXP-111 can confirm only a frozen candidate/mixture. It cannot establish general
fine-tuning benefit, solve matrix-factor cold start, pass a gate, authorise spend, delegate consent or
prove a hosted alias immutable.

---

## 9. Evidence against: the honest answer may be “not this year”

### The strongest case

[asserted] A hand-maintained list for another year is defensible and is the current recommendation.
Frontier releases may improve faster than a narrow local adapter can be retrained and requalified;
every requalification consumes scarce human labels; hosted identities may be unpinnable; automatic
download expands the supply-chain boundary; the repository has no factorisable outcome matrix; its
consent ingress, trainer isolation, cost telemetry and exact rollback are incomplete. Automation
could therefore make a worse or compromised model easier to select while producing a polished but
false “continuous improvement” story.

[asserted] RouterBench strengthens that objection. [cited] Its benchmark contains 405,467 inference
outcomes; KNN/MLP routers trained on 70% per-task splits excluding MT-Bench did not significantly beat
its static frontier overall. RouteLLM's MF degraded below random on one out-of-domain benchmark
without in-domain data. EmbedLLM needs retraining to add a model even after learning from a far denser
matrix than exists here. [asserted] The literature does not justify learning our missing factors.

[asserted] Local fine-tuning can also lose twice: a frontier incumbent may move during the training
cycle, and a narrow adapter can improve familiar tasks while regressing general tasks or learning
the evaluator. Provider-equivalent price can fall while total cost rises through GPU time, review,
maintenance and repeated qualification. None of those losses is excluded by training loss.

### Answer, not dismissal

[asserted] Concede the operational conclusion now: keep the static list; make only discovery and
quarantine automatic; run fine-tuning only as an isolated candidate experiment; do not fit MF. The
specification earns implementation only in reversible slices, and EXP-111 is allowed to kill both
automatic qualification and local fine-tune activation.

[asserted] Re-check the “another year” posture on 22 August 2027 or earlier when all four facts
exist: about 5,000 labelled model-attributed routing outcomes, an applicable measured wasted-work
multiplier of at least 2×, one candidate that completes the sealed bank, and trusted consent/approval
ingress with proved rollback. Calendar time alone does not satisfy any condition.

---

## 10. Enforcement, reversal and falsifiers

### Required implementation checks

- [asserted] A registry invariant test proves every non-`routable` and unknown-capability model is
  refused even when its ID is registered.
- [asserted] A discovery test proves new IDs produce quarantined manifests and never rewrite
  `MODELS` or an activation pointer.
- [asserted] A consent-use test proves missing, expired, withdrawn, wrong-purpose and unauthenticated
  grants refuse before reading training rows.
- [asserted] An isolation test gives the candidate hostile paths/tools and proves it cannot read or
  influence the bank, instrument, controller or result stream.
- [asserted] A cost test keeps money, provider-equivalent price, quota, wall time and human minutes
  distinct and makes every missing dimension unavailable.
- [asserted] A rollback test corrupts the candidate pointer and proves exact prior-manifest
  restoration by artefact, not event presence.
- [asserted] Existing AST, six-command, private-corpus, foreign-identifier, secret and gate checks
  remain unchanged.

### Reversal

[asserted] Before activation, reversal is deletion of no evidence: stop the lifecycle runner, keep
all candidates quarantined and continue using the static registry. After activation, restore and
verify the exact prior manifest, mark the failed candidate stale/refused and retain every outcome.
No history rewrite or ID reuse is permitted.

### Falsifiers

[asserted] Reject this decision if any unqualified/unknown revision becomes selectable; any candidate
or trainer can influence its acceptance instrument; withdrawn or unauthenticated data is consumed;
the principal's approval can be forged or delegated; a rollback cannot restore exact bytes; an
unavailable cost becomes zero; MF fails to beat the strongest simple held-out baseline; or EXP-111
shows a quality, beta, alpha, cost or review regression under its fixed rule.

### Publication candidate

No. [asserted] This is an internal lifecycle contract tied to provisional local mechanisms and
private experiments. A later public design must exclude instance data and distinguish implemented,
measured behaviour from this proposed state machine.

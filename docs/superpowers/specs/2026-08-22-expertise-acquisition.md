# Expertise acquisition: propose, prove, assign, retire

**Correction:** the dispatch brief overstates current enforcement: ADR-0074 and ADR-0076 specify
capability manifests and sealed instruments but do not implement them; a different model family is
not a different class of facts by itself; the distribution-free exposure ceiling can be zero rather
than one; `events.py` is a cooperative trajectory writer rather than an enforced durable single
writer; and Gate B forbids unattended/default dependence and device actuation rather than every
supervised dispatch to a principal-allowlisted repository. [measured] [algebra]

**Status:** provisional specification. It changes no gate, routing flag, product code, model or
active capability. EXP-126 is the frozen bundle-versus-generalist test; the model-lifecycle sibling
ADR-0085/EXP-111 owns fitting and checkpoint qualification. [measured] [asserted]

## 1. The plain decision

An expertise is a **versioned capability bundle**, not a model identity and not a standing team. It
contains retrieved sources, a skill, tool configuration, worked examples, a sealed evaluation
contract and outcome history. It may point to a separately qualified tuned checkpoint, but facts do
not become training merely because they are retained or retrieved. [asserted]

An explicit authenticated request to “learn X” authorises bounded local acquisition in quarantine,
which starts only after the independent instrument is frozen. An inferred need starts nothing beyond
private local observation: it creates one evidence-bearing proposal which the user must accept
through the same trusted first-party ingress before the instrument-authoring and acquisition workflow
begins. That ingress does not exist today, so neither transition is operational. [measured]
Neither trigger grants spend, trajectory use as training data, activation, publication, external
actuation or a principal-only verdict. [asserted]

The bundle becomes eligible for direct, supervised, explicitly selected assignment only after it
beats the unchanged eligible generalist on an instrument frozen before acquisition and hidden from
the acquisition path. Losing, tying, refusal and insufficient evidence are normal results: the
specialist assignment is discarded while its provenance and adverse outcome remain addressable.
Automatic library selection remains inert pending EXP-101. [asserted]

## 2. The bar and the delta

The closest inspected incumbent is Ratchet: it synthesises, measures and retires natural-language
skills under a bounded library, and its paper shows that an unmaintained library can drift until a
skill is worse than no skill. The repository's prior-art audit also found evaluator gaming,
regressions or missing denominator-based promotion error across DGM, SICA, HGM, HyperAgents,
Voyager, ADAS, Meta-Harness and Live-SWE-agent. [cited: Zhang et al. (2026), *Ratchet*,
arXiv:2605.22148v3] [measured: `../../10-research/self-extension-prior-art-2026-08-20.md`]

The bar is therefore not “can the machine write a skill or fine-tune a model?”. Existing systems do
that. The bar is a matched, sealed demonstration that a source-provenanced bundle beats the same
generalist, exposes refusals and harmful retrieval, survives stale/conflicting/out-of-scope cases,
and is retired when the comparator catches it. EXP-126 measures that delta. [asserted]

Searches on 22 August 2026 covered self-evolving skill retirement, agentic context engineering and
retrieval-versus-fine-tuning comparisons. The arXiv abstracts found opposed domain results, so no
universal retrieval or tuning winner is claimed; the local matched comparison decides. The two
abstract-only comparison papers were not promoted into the bibliography and carry no numeric claim
in this specification. [measured] [asserted]

## 3. Recognising value: two triggers, two standards

### 3.1 Explicit trigger

One authenticated first-party imperative whose operative meaning is “learn/acquire expertise in X”
is sufficient. Authentication means the future ADR-0075/0076/0078 owner-only ingress, not current
caller-supplied `actor` or `via` fields; until that ingress exists the request can support this design
but cannot open the acquisition transition. The current work item supplies the narrowest evidenced
purpose and postcondition when the wording names only a topic; that reversible scope assumption is
recorded instead of asking a preference question the user has not posed. A mention, question about
learning, pasted quotation or replay is not an imperative. [measured] [asserted]

The explicit request authorises acquisition from licensed public sources and material supplied for
the current task, plus skill/example/tool-configuration compilation and local evaluation for that
scope. It does **not** authorise importing prior private trajectory content into the bundle, whether
as retrieval, examples or training data; a parameter update; a metered provider; deployment;
distribution; or an external effect. Those retain their own consent, budget, evaluation and
authority records. [asserted]

### 3.2 Inferred trigger

An inferred proposal is eligible only when every condition below is true in the private local
trajectory over the preceding 90 days. The thresholds are conservative design values, not measured
constants. [asserted]

1. At least six completed applicable work items span at least 21 days and four distinct calendar
   days. [asserted]
2. They cover at least three distinct frozen postcondition signatures; repeated wording or one
   duplicated task does not create breadth. A model-supplied topic label cannot satisfy this test by
   itself. [asserted]
3. Either two adverse signals from different classes are attributable to missing expertise — a
   human material correction/rejection, an executable-verifier rejection, or a recorded capability
   gap — or at least 180 measured active worker-minutes across three work items were spent
   reacquiring the same sources, procedure or tool setup. Self-reported confidence and model
   agreement never count. [asserted]
4. A conservative reuse estimate remains positive if only half the observed recurrence continues
   for the next 90 days. It counts local/subscription compute, wall time, review time and storage
   separately; unavailable telemetry stays unknown rather than zero. [asserted]
5. No proposal for the same purpose/postcondition fingerprint was rejected or expired in the last
   90 days, unless a new independently observed critical failure occurred. [asserted]

Crossing the threshold appends a private proposal and surfaces it once in the next relevant user
interaction; it does not interrupt unrelated work. The proposal names the qualifying work items,
adverse/cost signals, proposed scope, source/privacy boundary, local time/storage estimate, intended
evaluation author, default bundle components, recheck date and the statement “no model training is
proposed”. Silence expires it after 30 days; rejection suppresses it under condition 5. [asserted]

Acceptance converts the inferred path into the explicit path only when a fresh, single-use
first-party receipt binds the proposal digest, purpose/postcondition, source and privacy boundary,
local resource ceiling, expiry and nonce. A dispatched process must be unable to mint, widen or
replay it. Until that verified receipt exists there is no source fetch, corpus construction,
embedding computation, skill mutation, worked-example capture or training handoff. Computing the
threshold from records already retained under ADR-0057 is observation, and the trajectory never
leaves the instance. The required trusted ingress is unimplemented. [measured] [asserted]

## 4. What an expertise is

One immutable manifest identifies one bundle version. Payload bytes deduplicate by digest, but two
manifests merge only when purpose/postcondition, interface, permissions, destination, trust,
verifier semantics, provenance, consent and licence are equivalent. At most one active head is
eligible for an execution-contract/destination class; old heads remain addressable. Eligibility
allows an exact direct assignment, not automatic selection, until EXP-101 confirms that separate
mechanism. [asserted]

The manifest contains: [asserted]

- purpose, task families, postconditions, explicit exclusions and applicability test;
- source URI/digest, retrieval time, licence, consent, validity interval and recheck trigger;
- retrieval/index configuration and a receipt for what was omitted from bounded context;
- skill/instruction digest, tool inventory/configuration, worked examples and counterexamples;
- permissions, destination classes, largest plausible effect and known failure modes;
- sealed evaluation epoch/digest, comparator identity, outcome counts, refusals and dissent;
- lifecycle state, predecessor/successor links and, only when separately qualified, a checkpoint
  capability reference rather than embedded model bytes.

### ADR-0074 line, step by step

| Step | Persistent artefact | Side of the boundary |
|---|---|---|
| Observe completed interactions and calculate the trigger | proposal evidence only | **Observation**, neither retrieval nor training. [asserted] |
| Fetch and preserve licensed sources | source archive and provenance | **Retrieval/capability**; no learned model state changes. [asserted] |
| Compile a skill, tool configuration, examples or counterexamples | capability payload + manifest | **Retrieval/capability**, even though the files persist. [asserted] |
| Compute embeddings with a frozen encoder | derived index | **Retrieval**; fitting or editing the encoder would be training. [asserted] |
| Freeze and execute the held-out instrument | instrument/result record | **Evaluation**, neither retrieval nor training. [asserted] |
| Fit, edit or optimise model parameters | dataset/run/checkpoint records | **Training**, including optimiser, closed-form and direct edits. [asserted] |
| Assign a bundle or qualified checkpoint to one work item | assignment/outcome record | **Inference/deployment**; it creates no new learning unless parameters mutate. [asserted] |
| Refresh sources or supersede a stale skill | new immutable bundle version | **Retrieval/capability**; retraining a checkpoint remains a separate training run. [asserted] |

Weights never replace the source archive, evaluation record or bundle manifest. A downloaded model
is a model capability; only a data-driven mutation of its learned state is training. [asserted]

## 5. Acquisition and proof

### 5.1 Freeze before study

The accountable work-item Owner appoints one per-work-item instrument author before candidate
acquisition begins — before the acquisition worker fetches a source, drafts a skill, selects an
example or makes a training split. That author is not a standing role and cannot be the acquisition
worker, candidate specialist, training process or promoter. Its evidence class is a hidden
source/time-separated task bank with independently defined truth contracts, not another reading of
the bundle. It pre-allocates a disjoint one-use qualification batch for each registered candidate
lineage; once that batch's verdict affects activation it retires, and exhaustion is
`no_fresh_instrument`, never reuse. [asserted]

The frozen digest binds the expertise scope, candidate lineage and batch purpose, task strata, hidden
items and labels, semantic-sibling exclusion rule, scoring code, generalist comparator and version,
allowed tools, per-arm budget, randomisation seed, missing-data treatment, stopping rule,
critical-error definition and blind human verdict procedure. The candidate sees the contract and
development feedback, never hidden cases, answers, labels or per-item results. [asserted]

For expertise derived from a user's work, the rights-cleared corpus is split before acquisition.
The held-out partition and semantic siblings never enter sources, retrieval indexes, skills, worked
examples or a tuning dataset. If no competent independent author or executable oracle can construct
that separation, the result is `insufficient_evidence` and deployment is refused. [asserted]

ADR-0076's sealed host and authenticated principal ingress do not exist in this tree. “Sealed” is
therefore a required precondition, not a present capability; a file hidden by prompt instruction is
not an acceptance instrument. [measured]

### 5.2 Build the cheap arm first

Acquisition searches licensed primary sources and open data first, records near misses and source
dates, then compiles the minimum bundle. The development loop may edit retrieval, skill, tools and
examples against a separate development bank, but may not inspect the held-out instrument. All
candidate versions remain quarantined. [asserted]

The first comparison is the unchanged eligible generalist versus that bundle under the same
harness, tools and realised ceiling. EXP-126 fixes the 80-task paired design and outcome rule. The
generalist may use its ordinary tools; the treatment receives only the additional frozen bundle, so
the measured delta is the value of packaged expertise rather than a weaker comparator. [asserted]

If the bundle loses or ties the generalist on point joint success, causes one treatment-only critical
error from stale, wrong or unsupported content, breaches privacy/authority, or meets the registered
harm rule, it is discarded from assignment. “Discarded” means quarantined or retired and preserved
as an adverse record, never deleted from history. An inconclusive result stays quarantined. [asserted]

### 5.3 When a tuned model is genuinely warranted

Tuning is an exception, not the meaning of expertise. A bundle may be handed to ADR-0085's model
lifecycle only when all of these are true: [asserted]

1. retrieved facts are correct and current, yet development failures show a stable behavioural,
   representation or latency/cost deficit rather than missing knowledge; [asserted]
2. the target behaviour recurs often enough to repay training and serving before the shortest source,
   model or tool recheck horizon; [asserted]
3. every example has exact rights, consent and provenance, with private trajectory material excluded
   unless a separate first-party record names its use; [asserted]
4. dynamic facts remain in retrieval rather than being baked into weights; [asserted]
5. local hardware is attempted first and no metered run starts without the separately enforced
   provider allowlist and budget authority; [asserted]
6. ADR-0085 owns the sealed checkpoint comparison under its cost, rollback and model-release rules.
   For assignment as this expertise, that evaluation or a successor must also demonstrate
   incremental value over the same bundle without the parameter update. The current EXP-111 design
   compares an adapter with its unmodified base and the incumbent, so it does not by itself isolate
   this bundle-conditioned delta. [measured] [asserted]

The expertise layer hands off the bundle/dataset/consent/evaluation digests, target task contract,
observed bundle-only failure modes, expected reuse and retirement triggers. It does not choose the
base model, fitting method, matrix factorisation, checkpoint format, training schedule, deployment
router or rollback mechanics; ADR-0085 owns those. [asserted]

No empirical frequency is known. The honest v0 frequency is **zero automatically deployed tuned
specialists**: the lifecycle comparison has not run and active promotion refuses. The design expects
tuning to be rare because all six gates must hold; the model lifecycle can qualify a checkpoint, but
only a bundle-conditioned comparison can determine whether it belongs in an expertise assignment.
Tuned expertise remains unavailable until ADR-0085 owns that separately pre-registered, fresh-bank,
same-base-plus-same-bundle comparison. [measured] [asserted]

## 6. Assignment into a specialist squad

A specialist is a per-work-item `R` assignment whose Owner-authored capability request names the
active bundle digest and exact task contract. This is direct assignment; EXP-126 cannot authorise
automatic library selection, which remains inert pending EXP-101. The one accountable Owner remains
`A`; a `C` assignment is admitted
only when it brings a structurally different truth-relevant anchor and may return dissent. It may
make a candidate ineligible only by showing that a necessary condition frozen before acquisition
failed; it cannot decide, vote or rewrite the criterion. `I` receives the sealed outcome and gains no
decision or execution right. These consume ADR-0067 and ADR-0082 rather than creating a specialist
registry or standing organisation. [asserted]

Direct selection reuses `capabilities.py`: exact purpose/postcondition, destination, permissions,
consent, licence, validity, model/tool compatibility, evaluation epoch and active-head uniqueness
must match the Owner-authored request. `instructions.py` assembles the selected bundle, `dispatch.py`
assigns it, `routing.py` applies the candidate-exposure ceiling, `budget.py` accounts for resources,
and `work_items.py`/`coordination.py` hold the task-scoped roles and paths. [asserted]

The default squad is one Owner with the bundle. Adding three agents that all consume it creates one
anchor and three correlated readings, so they are cut. A different model family is metadata only.
For a `full` record or protected disposition under ADR-0081, the conclusion needs a second
structurally distinct anchor such as executed artefact behaviour, a browser observation, a checked
primary source or a novel non-derived corpus/public API. The second role acquires and seals that
anchor independently; it does not reread the bundle or vote. [asserted]

Every squad emits one Owner candidate. At the current 22 August tree state `consil doctor` reports
Gate A FAIL, Gate B FAIL and routing disabled, while unestimated human beta permits no automated
candidate exposure. These documents therefore specify assignment but activate none. [measured]

## 7. Decay, invalidation, supersession and retirement

Every source and tool dependency carries `valid_from`, `recheck_after`, version/digest and a trigger
set. Retrieval time alone is not freshness. The selector checks these before each assignment and
refuses an expired or incompatible bundle. [asserted]

- **Quarantine immediately** on one privacy/authority breach, one critical wrong-or-stale
  bundle-caused outcome, an invalid licence/consent record, instrument contamination or a failed
  digest/compatibility check. [asserted]
- **Re-evaluate** on a source retraction or digest change, tool/API/schema change, evaluation-epoch
  change, materially stronger generalist/model release, or two bundle-attributable human rejections
  in the most recent 20 applicable assignments. Re-evaluation consumes a fresh pre-allocated
  qualification or drift-sentinel batch; it never replays the batch that admitted the bundle. The
  rejection threshold is provisional. [asserted]
- **Invalidate** a version when its evidence, consent, licence or task contract was wrong. Stop
  selection immediately and append the reason; do not rewrite the earlier record. [asserted]
- **Supersede** when a new version passes a fresh one-use qualification batch under the current
  owner-approved evaluation epoch. Link both directions, make only the successor selectable and
  preserve the predecessor and dissent. [asserted]
- **Retire** when the unchanged current generalist matches or beats it, its break-even reuse horizon
  can no longer be reached, its domain disappears, or refresh cannot restore eligibility. Retirement
  removes assignment eligibility, not history. [asserted]

A checkpoint reference inherits every bundle invalidation and adds ADR-0085's base-model, training
data and runtime compatibility triggers. A new frontier release is evidence to re-qualify, never an
automatic reason to migrate or an automatic claim that the specialist is obsolete. [asserted]

## 8. State and reuse: no second orchestrator

The state path is `observed -> proposed -> authorised -> acquiring -> quarantined -> evaluated ->
active -> stale/quarantined -> superseded|retired`. Explicit requests enter `authorised` for the
retrieval/capability scope; inferred triggers enter `proposed`. Training consent and active
promotion are separate joins and cannot be inferred from either transition. [asserted]

Future implementation extends existing components only: `work_items.py` carries the acquisition and
role assignments; `coordination.py` owns claims; `recall.py` supplies bounded verbatim context;
`capabilities.py` stores/selects the manifest; `instructions.py` assembles it; `dispatch.py` runs the
work; `routing.py` enforces exposure; `budget.py` records resources; and `events.py` remains the
trajectory authority after its durability gap is repaired. SQLite, if used, is a disposable
projection. [asserted]

There is no `consil learn`, second router, model registry, scheduler, orchestrator or standing squad.
No implementation ships in this document-only change. The first behavioural slice must add, in the
same commit, checks that: [measured] [asserted]

- distinguish explicit imperatives from mention/quotation and reproduce every inferred threshold;
- refuse explicit or inferred acquisition without a fresh authenticated, scope-bound, single-use
  first-party receipt; reject same-OS child mint, replay and widening; and refuse private-data
  training without separate exact consent;
- classify retrieval, embedding computation, embedding fitting and parameter edits on the ADR-0074
  boundary;
- prove the instrument digest predates acquisition, reject task/answer/semantic-sibling overlap and
  refuse a second query after a qualification batch affects activation;
- prevent candidate, trainer and promoter access to hidden items or labels;
- refuse stale, invalid, incompatible, destination-mismatched and non-unique active heads;
- reject a same-bundle “independent” anchor and preserve sealed dissent;
- quarantine on every critical error and reconstruct invalidation/supersession/retirement by replay;
- prove there is no raw acquisition, assignment or effect path around the existing substrates.

## 9. Gate B and device control: deliberately out of scope

This specification does not define autonomous phone, computer, browser, message, payment,
credential, publication, external-system or physical control. Supervised dispatch to a
principal-named allowlisted repository is already distinct from Gate B passage, but this expertise
design itself runs only in the Consilient repository and grants no actuation. [measured] [asserted]

Before expertise could participate in unattended external work, Gate B and the routing gate would
have to pass for the named root; ADR-0078's typed pre-effect admission, least-privilege adapter,
durable intent/receipt and no-bypass checks would have to exist; the exact user authority, consent,
budget and destination grant would have to match; verifier beta would have to permit the exposure;
and the bundle/checkpoint would have to be active and fresh. Meeting those conditions would make a
separate capability eligible; it would not make ambient device control part of expertise. [asserted]

## 10. EXP-126 and normal failure

EXP-126 is pre-registered in `../../10-research/experiment-register.md` before any acquisition
outcome is inspected. It compares an unchanged eligible generalist with the same generalist plus one
frozen bundle across direct, adjacent-transfer, conflicting/stale-source and out-of-scope/abstention
strata. It reports human and oracle outcomes, cost, harmful retrieval, missingness, refusal and
quarantine rather than one flattering aggregate. [asserted]

The experiment can confirm only direct, supervised, explicitly selected assignment for its frozen
expertise. A loss or bundle-caused critical error retires that assignment; an inconclusive result
leaves it quarantined. It does not
test automatic library selection (EXP-101), tuned weights (ADR-0085/EXP-111), the incremental value
of tuning over this bundle, inferred-trigger consent, squad size, device control or either gate.
[asserted]

## 11. The strongest case against building this

Targeted acquisition may be a losing race. Frontier general models can improve faster than a local
specialist can be collected, evaluated and maintained; by deployment time the comparator may have
closed the gap. A corpus drawn from one user's interactions may learn that person's habits,
terminology and recurring mistakes rather than domain expertise. Every bundle also creates another
stale dependency and another way for retrieved authority to anchor the Owner. [asserted]

The harder objection is that retrieval plus a good skill may capture nearly all useful value at a
fraction of tuning's data, compute, privacy, rollback and decay burden. The repository's strongest
matched-budget adjacent evidence is already unfriendly to self-improvement: Wang et al. found no
significant held-out harness-evolution gain over parallel sampling in its disjoint split, while
Ratchet shows both useful bounded skill retirement and library drift. Neither result establishes
this domain, but together they make automatic fine-tuning the burdened option. [cited: Wang et al.
(2026), *Rethinking the Evaluation of Harness Evolution for Agents*, arXiv:2607.12227v1; Zhang et
al. (2026), *Ratchet*, arXiv:2605.22148v3]

The design concedes that objection. It builds no automatic tuning path here, treats the bundle as
the expertise, makes bundle-versus-generalist the first test, and requires a bundle-conditioned
comparison before a checkpoint can be assigned. If EXP-126 fails, specialist assignment is not
warranted for that expertise; explicit source retrieval and manually selected skills remain useful
without pretending the machine became an expert. Automatic selection remains a separate EXP-101
question whatever EXP-126 reports. [asserted]

## 12. Reversal and limits

Reverse the inferred policy by disabling proposal generation; explicit acquisition still works.
Reverse bundle deployment by marking its active head retired; source/history records remain.
Reverse a threshold by a new ADR and evaluation epoch, never by editing observed outcomes. Reverse a
tuned specialist through ADR-0085's checkpoint rollback. None requires deleting the user's private
history. [asserted]

The current claims are deliberately narrow: the trigger thresholds, promotion margins and decay
counts are asserted; the sealed host, authenticated owner ingress, manifest projection and selector
do not exist; EXP-126 has not run; and ADR-0082/0085 landed during drafting. This is a falsifiable
contract for later construction, not a claim that the Machine can already learn, train or deploy
expertise. [measured] [asserted]

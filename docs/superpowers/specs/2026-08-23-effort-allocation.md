# Effort allocation: decide first, supervise execution, and keep light mode light

**Correction:** two premises in the dispatch brief are wrong. First, the principal's later, verbatim
corrections supersede 80/20 entirely: phase use is measured, while the transition from deciding to
doing occurs when an externally checked better-than-best threshold passes or a predeclared give-up
ceiling fires. Second, ADR-0077 makes beta bound shippable candidate exposure, while ADR-0067
separately governs evidence-role count. The iid logarithmic expression in the brief is diagnostic,
not the current automatic policy; the dependence-robust ceiling is `floor(epsilon / q_upper)`.
[measured: The Machine, 23 August corrections; ADR-0067; ADR-0077]

- **Date:** 2026-08-23. [measured]
- **Status:** specification only; [ADR-0090](../../decisions/0090-allocate-full-mode-effort-before-execution-and-make-light-mode-explicit.md)
  is PROVISIONAL. [measured]
- **Killing experiments:**
  [EXP-133](../../10-research/experiment-register.md#exp-133--does-an-8020-decision-first-budget-beat-threshold-triggered-allocation-the-inverse-and-superpowers-at-equal-total-budget-blocked)
  tests 80/20 against threshold-triggered allocation, its inverse and Superpowers;
  [EXP-134](../../10-research/experiment-register.md#exp-134--does-frontier-supervision-of-weaker-execution-match-frontier-direct-quality-at-lower-frontier-cost-blocked)
  tests supervision economics. Both were verified free and pre-registered before any outcome was
  inspected. [measured]
- **Scope:** decide/do accounting for full application work, a three-phase better-than-best protocol,
  frontier supervision of a weaker executor, the `fast` admission rule, and a named single-model
  `light` mode. [asserted]
- **Non-goals:** another cascade, model-capability matching, a configured 80/20 target, a second
  orchestrator, a seventh CLI command, a new gate condition, implementation, or a claim that tokens
  measure intelligence. [asserted]

## 1. Answer first

Consilient has two modes and two full-mode execution profiles. `light` is a single-model answer that
bypasses the scientific machinery. `full` uses the existing work-item, budget, routing and trajectory
boundaries; inside it, `better-than-best` is the default profile and `fast` must earn admission. Every
full application unit is accounted as `decide` or `do`. Better-than-best additionally runs three
semantic phases: **locate the bar**, **exceed it**, then **realise the selected candidate**. Their
transition is a frozen acceptance threshold, never elapsed percentage. Fast is narrower: it may only
realise an already sealed, low-consequence decision package under its ordinary verifier. The observed
decide/do split is reported, never used for admission. [asserted]

The principal first offered 80/20 as an example, corrected it from a target to a hypothesis, then
superseded the ratio with the better-than-best transition. On the one session he named, docs-only
versus product-touching commit count was 59/17 (78%/22%), but neither commit count nor line count
measures compute. EXP-133 therefore measures dispatch and token use by phase and treats 80/20 as one
arm against threshold-triggered allocation, 20/80 and pinned Superpowers. [measured:
`../../00-context/the-machine-2026-08-22.md`, "The phase transition is a threshold, not a ratio"]

## 2. Sources consumed and what they changed

| Source read | Constraint consumed | What changed here |
|---|---|---|
| `CONSILIENCE.md` | Agreement matters only when inductions touch different classes of facts; tests have false-accept rates. [measured] | A frontier model rereading a worker's prose gets no evidence credit. Supervision relies on executed diagnostic and held-out acceptance checks, and remains a cost strategy rather than a claim that two model roles are consilience. [asserted] |
| The Machine, 23 August section and corrections | The principal superseded the ratio with three phases: locate the bar, exceed it through executable reasoning, then realise the candidate. He also specified frontier instruction/review of cheaper work, no idle parallelism, a better-than-best default and quick single-model chat. [measured] | Every full unit receives decide/do accounting; better-than-best units also receive a semantic phase/category label. The transition is an externally checked bar threshold with a hard give-up ceiling. The ratio is reported, never configured. [asserted] |
| ADR-0002 | The cascade already owns cheap-first escalation and refuses below the measured capability-gap threshold on objectively assessable work. [measured] | No second cascade or model-matching rule appears here. The supervision loop is admitted only with objective diagnostic and acceptance contracts. [asserted] |
| `inquiry-tier.md` | T0 assert, T1 ground, T2 model and T3 measure are selected by reversibility, blast radius, prior dispersion, formalizability and inquiry cost. [measured] | Better-than-best is the quality objective, not permission to run every stage. Modelling and experimentation occur only when their gates fire. [asserted] |
| ADR-0030 | Projected context, reserved output and explicit composition precede selection; silent truncation is forbidden. [measured] | Every phase dispatch declares its context and output reservation before model selection. [asserted] |
| ADR-0067 | One Owner is the default; roles grow only for a concrete, unavailable, decision-relevant anchor; principal authority cannot be impersonated. [measured] | The frontier supervisor is the Owner. A weak executor has no vote or evidence weight, and no management label grants authority. [asserted] |
| ADR-0077 | Candidate exposure, composite verification and evidence fusion are distinct; automatic exposure uses a dependence-robust ceiling. [measured] | Correction drafts remain quarantined, the held-out acceptance verifier runs once, and correction count never becomes squad-size evidence. [asserted] |
| ADR-0081 | High-consequence conclusions require convergent anchors from structurally different acquisition channels; the proposing model cannot self-certify them. [measured] | A high-consequence `bar_beaten` transition needs the frozen margin accepted through ADR-0081's gate. If anchors are absent or disagree, the threshold has not passed. [asserted] |
| ADR-0087 | One Owner answers directly when another observation would not change the decision. [measured] | Direct answer is retained inside full mode; light mode is the stronger, user-visible bypass with explicit losses. [asserted] |
| `reasoning-layer.md` | Task scaffolding and decision inquiry are different; intrinsic self-correction without external feedback is rejected. [measured] | Supervision consumes executed diagnostics, never "review it again" or model confidence. [asserted] |
| `architecture-sketch.md` | A mode is a scheduling pattern, the architecture has five existing components, and orchestration remains outside a new `consil` command. [measured] | `light`, `full`, `fast` and `better-than-best` do not become execution identities, routers or CLI subcommands. [asserted] |
| Current source boundaries | `dispatch.py` caps individual children; `budget.py` admits OpenRouter spend; `work_items.py` carries tasks; `coordination.py` carries claims; `recall.py` bounds context; `instructions.py` assembles it; `events.py` is the sole append-only writer. None records a request-wide phase taxonomy or threshold. [measured: source inspection, 2026-08-23] | Future implementation extends those boundaries with a total request budget, decide/do and category-labelled charges, plus better-than-best transition receipts. A parallel ledger, task store or orchestrator is forbidden. [asserted] |

These decisions are not uniformly accepted: ADR-0002, ADR-0030, ADR-0067, ADR-0077 and ADR-0081 are
PROVISIONAL; ADR-0087 is PROPOSED; the Inquiry tier is an asserted design sketch and is outside the
current v0 architecture. This specification defines future behaviour and claims none exists today.
[measured]

## 3. The retrieved composite bar and the surviving delta

The brief's minimum workflow comparator is Superpowers v6.3.0, tag `v6.3.0`, commit
[`b36e0829c`](https://github.com/obra/superpowers/commit/b36e0829c6d0140e93cfef2ca599b1b07d4a7797), retrieved and matched byte-for-byte to the installed
package on 23 August 2026. Its `brainstorming` skill visibly classifies spike, bounded and
architectural work, explores repository context, asks one question at a time, compares two or three
approaches, obtains human approval, writes a specification and self-reviews it. Its `writing-plans`
skill maps files and interfaces, then emits exact independently testable TDD steps with commands and
commit boundaries. [cited: bibliography section 19] [measured: installed blobs]

The two pinned skills contain no external research/retrieval stage, prior-art record, executable
simulation, pre-registered experiment, phase budget or beta accounting. Superpowers' spike remains a
protocol path: it classifies, presents a probe and waits for approval, so it is not the requested
protocol-free light mode. [cited: bibliography section 19]

Upstream's v6.3.0 evaluation is a serious bar rather than an untested prompt. It reports 65 graded
live repetitions and a 75-call classification micro, while disclosing that the no-router control
matched the shipped router in every micro cell and that small reruns followed two live failures.
[cited: bibliography section 19]

Two primary studies set adjacent, not interchangeable, bars. Yang et al. hold the solver fixed and
run 4,181 primary reasoning problems under direct, self-correction, planner-executor-reviewer and
broadcast protocols. Their cheap direct references remain competitive, and a strong failure-risk
signal predicts whether collaboration may help much better than which expensive protocol will pay;
protocol-specific cost-aware routing remains unresolved. Schmalbach's 64 coding-agent runs and 192
blinded reviews find explicit delegation contracts improved reviewability but not already-saturated
objective correctness, at 13% more agent tokens and 38% more wall time. [cited: bibliography section
19]

No retrieved source establishes the best end-to-end application deciding/execution system. The bar
is therefore composite rather than falsely singular: beat pinned Superpowers on accepted application
outcomes at equal total budget; preserve an explicit authority/evidence return package; and show that
supervision is quality-non-inferior with lower frontier and total cost than direct execution. EXP-133
and EXP-134 test those exact deltas. [asserted]

### Search record and near misses

The installed v6.3.0 release, both pinned skills, release notes, PR #2063 and its evaluation evidence,
the writing-plans evaluation commits, the primary abstracts/listings for arXiv:2608.14927v1 and
arXiv:2606.17099v1, the repository bibliography and tracked references to Superpowers were read on
23 August 2026. Searches covered
`Superpowers brainstorming writing-plans`, `planner executor reviewer cost routing` and `coding
delegation contract reviewability`; only primary upstream sources carry claims. An unmerged
`skeleton-alternative` branch was a near miss: it explores plan skeletons but is not tagged, installed
or on upstream `main`. Neither paper is an application-building comparator: Yang et al. study
reasoning benchmarks; Schmalbach studies small seeded TypeScript tasks. [measured] [cited:
bibliography section 19]

The proposed delta is structural: deciding can acquire current sources and open data, run executable
models and pre-registered experiments, import a genuinely different class of facts, freeze rejected
options and make phase use measurable before implementation. Broader
mechanism coverage is not evidence of better decisions. "Better than Superpowers" remains
`[asserted]` until EXP-133 wins against the pinned comparator at the same total budget. [asserted]

## 4. Mode and profile admission

`mode` and `execution_profile` are separate fields. Conflating them would make a quick but verified
task lose its checks, or make a simple chat pay for a full work item. [asserted]

| Mode/profile | Admission | What runs | Guarantee boundary |
|---|---|---|---|
| `light` | Explicitly named, or automatically selected only for a low-consequence answer-only turn that is answerable from supplied context and needs no current evidence, file change or external effect. [asserted] | One model, current conversation context, no durable task machinery. [asserted] | No beta accounting, consilience gate, squad, discovery, research, simulation, experiment, decision protocol or independent verification. [asserted] |
| `full + better-than-best` | Default for durable artefacts, material recommendations, application builds and work intended for the principal. [asserted] | The warranted deciding stages, then bounded implementation against a frozen verifier. [asserted] | It targets the retrieved bar; superiority remains unproved until EXP-133. [asserted] |
| `full + fast` | All fast gates in section 8 pass for an already sealed decision package. [asserted] | One Owner realises that package under the same authority/budget/record boundary and one frozen objective verifier. [asserted] | Faster treatment, not a lower safety or evidence floor; it makes no better-than-best claim. [asserted] |

Naming `full`, `light`, `fast` or `better-than-best` in conversation selects the corresponding mode
or profile. This adds no CLI subcommand; future chat intake records fields on the existing work item.
[asserted]

## 5. The enforceable boundary: total budget, taxonomy and threshold

### 5.1 What is and is not being counted

Provider-native quotas, local GPU time, metered money, wall time and tokens are not one fungible
quantity. Existing source correctly keeps subscription and metered ledgers separate, and several
harnesses cannot report complete actual token usage. Adding them into "intelligence units" would
invent a number. [measured: ADR-0028; `budget.py`; `events.py`] [asserted]

The enforceable aggregate is `B = (turns, output_tokens)`: the sum of hard `max_turns` and
`max_tokens` reservations for every model dispatch admitted under one application-build request.
The request also freezes wall-clock, provider-native quota, local-compute and monetary ceilings, but
reports them separately rather than forcing them into one invented unit. Actual input/output usage
is recorded by exact composition where available; missing usage is `unavailable`, never zero.
[asserted]

Dispatch count and reported tokens are the two decide/do measures named by the principal. They remain
imperfect: reservations are not actual use, input usage is not universally available, and unlike
model tokens are not equal compute. They can support a controlled comparison; they cannot measure
intelligence or physical FLOPs. [measured] [asserted]

### 5.2 Plan, admission and report

Before the first full dispatch, `effort.plan` freezes total `B`, separate non-fungible ceilings, a
request-specific category forecast and a component-wise `realisation_reserve` sufficient for the
smallest accepted candidate. Better-than-best additionally references ADR-0092's immutable protocol
plan, including its search stop, threshold contract and give-up rule; this record does not define a
second copy. The reserve is atomic: a pre-realisation charge is refused if the resulting remaining
budget would fall below it in any dimension. Every number is task-specific; no percentage is a
default or target. [asserted]

The budget boundary atomically charges every child against total `B` before launch. Each charge binds
one closed ADR-0092 category; `decide|do` is a deterministic projection from that category, never a
second mutable field. Better-than-best also references ADR-0092's semantic phase and handover. Fast
admits only `implementation|verification|delivery` against the `fast_admitted` receipt in section 8.
After every charge, the projection reports dispatch counts, reservations and actual tokens (or
`unavailable`) by decide/do, semantic phase and category. Unused capacity is never burned to make a
ratio look compliant. [asserted]

### 5.3 Transition and give-up

ADR-0092 owns the three semantic phases, closed category enum, bar package, external threshold,
give-up condition and durable handovers. The effort layer consumes those records but cannot author or
reinterpret them. It refuses a pre-realisation charge that would invade `realisation_reserve`, and it
refuses better-than-best realisation without ADR-0092's valid realisation handover. Hard totals cannot
grow inside a work item. Working principle 11 remains visible at delivery: a threshold miss may carry
the best safe candidate forward within the reserve, but it never becomes a better-than-best claim.
[measured: ADR-0092] [asserted]

### 5.4 Record contract

Future implementation adds the minimum structured record through the existing writer. [asserted]

- `effort.plan` freezes request/work-item identity, mode/profile, total ceilings, category forecast,
  component-wise `realisation_reserve`, composition candidates, authority and the ADR-0092 protocol
  plan reference where applicable. [asserted]
- `effort.charge` binds one valid category and protocol reference where applicable, derives decide/do,
  reserves every total-budget dimension before launch, refuses a pre-realisation reservation that
  would leave any dimension below `realisation_reserve`, and later records actual usage or
  `unavailable`, terminal state and artefact reference. [asserted]
- `effort.summary` reports planned and actual decide/do, semantic-phase and category dispatches,
  reservations and tokens without converting missing values to zero or turning the observed ratio
  into an admission rule. [asserted]

`budget.py` owns atomic admission, `events.py` validates and appends, `work_items.py` carries the
request, and `dispatch.py` refuses an unbudgeted child. This is an extension of the existing
chokepoints, not a second ledger or orchestrator. [asserted]

## 6. Consumed work taxonomy and phase protocol

ADR-0092 and its companion specification own the systematic process: locate uses framing, discovery
and research; exceed uses debate, experiment, simulation, synthesis, assessment and planning, with
innovative mechanisms recorded inside synthesis; realise uses implementation, verification and
delivery. Each unit has one closed category, durable output and handover. This effort specification
only derives decide/do accounting and protects the hard envelope around that protocol. [measured:
ADR-0092] [asserted]

Executed retrieval, code, browser observations, simulations and experiments can add world evidence;
debate between models sharing the same facts cannot. The realisation package cannot silently reopen
the goal, threshold or verifier. A verification failure may open a new work item, but it cannot
rewrite the assessment that admitted this one. [measured: ADR-0081; ADR-0092] [asserted]

## 7. Frontier-supervised weaker execution

This loop is not ADR-0002's cascade. A cascade generates cheaply and escalates on verifier failure;
supervision deliberately spends frontier capacity on the instruction and diagnostic review while a
weaker composition produces most artefact bytes. It is allowed only for reversible, objectively
assessable work with a development diagnostic and one held-out acceptance contract. [measured]
[asserted]

### 7.1 Actors and inputs

One frontier **Owner-supervisor** writes the worker instruction from the sealed decision package. The
instruction names the exact objective, allowed paths and effects, authority, context digest, budget,
diagnostic verifier, held-out acceptance verifier, artefact contract and correction ceiling. A weak
executor works in an isolated claimed worktree and returns the artefact, diff, commands, diagnostic
receipts, resource usage and every refusal or timeout. [asserted]

The weak executor has no vote and adds no evidence merely by being another model family. Its
truth-relevant contribution is the repository state and tool output it actually produces. The
frontier reviewer sees the frozen instruction, exact artefact/diff, tool and browser receipts,
diagnostic outputs, usage and prior correction packets. It never consumes hidden reasoning or
self-reported confidence as evidence. [asserted]

### 7.2 Three corrections, then stop

1. **First correction.** The Owner runs or inspects the frozen development diagnostic, maps each
   failure to an acceptance criterion and sends one bounded delta instruction to the same weak
   executor. Unexecuted stylistic doubt is not a correction. [asserted]
2. **Second correction.** If the next draft still fails, the Owner supplies the smallest reproduced
   counterexample, removes unrelated scope and gives the weak executor its final retry. No new goal,
   tool, path or verifier is introduced. [asserted]
3. **Third correction.** If the final weak draft still fails, the weak executor is removed. The
   frontier Owner either performs one bounded direct correction inside the remaining request budget,
   or records `incomplete`. It never sends a fourth weak retry.
   [asserted]

The loop gives up earlier on a structural capability gap, authority/credential requirement,
security boundary, missing objective verifier, exhausted total budget, or when the next review or
correction cannot fit within the frozen request ceiling. The frozen direct-frontier reference cost is
recorded for economic comparison, not used to stop the provisional loop before its own failure can be
measured. A principal-only matter escalates to the principal; an ordinary technical failure escalates
to the frontier direct path or terminates incomplete. "Escalate" never means approve, spend, publish
or lift a gate on the principal's behalf. [asserted]

Development diagnostics may run during correction, but all drafts remain quarantined and the held-
out acceptance verifier runs once, after the Owner freezes the final candidate. If a protocol cannot
separate diagnostic from acceptance evidence, every verifier exposure counts under ADR-0077 and the
loop refuses when the robust candidate ceiling cannot admit it. A failed held-out acceptance is
terminal; there is no post-result repair. [asserted]

The economics can be worse than direct generation. Three full-diff reviews, correction packets and
a final frontier edit can consume more frontier input/output than one clean frontier generation,
before counting the weaker worker or added wall time. EXP-134 treats that as a loss, not an awkward
success. [asserted]

## 8. What earns `fast`

`fast` is a full-mode realisation profile for an already sealed decision package, not light mode and
not a user adjective that bypasses checks. All of these gates must pass before any effect: [asserted]

1. **Reversible:** an exact local rollback exists and is tested or mechanically obvious. [asserted]
2. **Low consequence:** no money, credential, principal-only preference/verdict, safety-floor edge,
   external exposure, personal/private data movement, schema/protocol/public API or gate change is
   involved. [asserted]
3. **Bounded blast radius:** one existing flow and its direct consumers are understood; the task does
   not create a new subsystem or constrain multiple later artefacts. [asserted]
4. **Objectively assessable:** a frozen, cheap, task-native verifier can reject the wrong artefact;
   model confidence and prose review do not qualify. [asserted]
5. **No unavailable decision-changing fact:** current retrieval, discovery or human judgement cannot
   plausibly flip the approach. [asserted]

`fast_admitted` freezes the supplied decision package, all five gate receipts, ordinary success
contract, verifier and rollback. Fast then runs only `implementation|verification|delivery`; it does
not run `locate|exceed`, invoke ADR-0081 or make a better-than-best claim. It retains authority,
spend, beta, claim, trajectory and held-out-verifier boundaries. If a gate becomes false, no further
effect is admitted: the Owner rolls back where needed, closes fast as incomplete and opens a linked
better-than-best work item. A user request for fast that fails admission is declined as a profile and
run full; no confirmation is needed unless the newly exposed issue is itself principal-only.
[asserted]

Concurrency is orthogonal. Independent work units run together only when width shortens the measured
or predicted critical path and claims do not overlap. Evidence roles grow only for distinct anchors;
shippable candidate count remains beta-bounded. Idle capacity, agent count and parallel token burn
are never outcome measures. [asserted]

## 9. Light mode and promotion

### 9.1 Contract the user can name

A user can say `light mode` or `answer lightly`. The response visibly begins `Light — unverified
single-model answer`. Light mode uses one model and supplied conversation context only. It creates no
durable work item, recalls no trajectory, dispatches no child, reads no source, runs no experiment or
simulation, changes no file and takes no external action. The safety floor still applies. [asserted]

Automatic light selection requires every condition below: [asserted]

- the turn asks for an answer, not a durable artefact or action;
- the consequence is low and the answer is reversible by a later correction;
- supplied context is enough, so no current fact, citation, repository inspection or tool result is
  required;
- no user-only authority class is touched; and
- the user did not request verification, better-than-best work or full mode.

### 9.2 What light gives up

Light has **no beta accounting, no consilience gate, no squad, no discovery, no research, no
simulation, no experimentation, no decision protocol, no independent verifier, no durable decision
record and no better-than-best claim**. It is ordinary model output under the safety floor. The mode
line is a limitation, not a quality badge. [asserted]

### 9.3 Promotion without laundering the earlier answer

An automatically selected light conversation promotes to full before the first turn that requests a
file or durable artefact, current/source-backed fact, tool use, material recommendation, autonomous
work, external effect, irreversible choice or principal-only decision. The interface states the
trigger in one line, freezes the conversation as `[asserted]` input under ADR-0030 and starts a new
full work item; no light answer becomes evidence merely because it appears in the transcript.
[asserted]

Explicitly pinned light never promotes silently. It refuses the material continuation, states which
full-mode guarantee is required and lets the user say `full`. This is the cost of making light a mode
the user can rely on rather than an optimisation the system may revoke invisibly. [asserted]

## 10. Authority, evidence classes and acceptance

The Owner may decide reversible technical means inside frozen authority. It may not author the
principal's verdict, approval, gate lift, credential, spend authority, external publication or
genuine preference. Future review and phase events therefore validate as machine outcomes and can
never carry `human_decision` or `human_verdict`; the existing V0-18/V0-23 checks remain the authority
chokepoint. [measured] [asserted]

Another model family, title or correction round is not a different class of facts. Source retrieval,
executed tests, browser behaviour, public data, hostile inputs and authenticated human judgement can
be. A role without a named decision-relevant anchor is removed; a compute actor's output receives no
fusion weight. [measured] [asserted]

Beta conditions whether a candidate may automatically pass the acceptance boundary. It does not set
squad size or concurrency width. Human-labelled beta is currently unestimated, so no paragraph here
opens routing or changes `routing_orchestration_enabled`. [measured]

## 11. Checks owed by implementation

This document writes no product code. Any implementation must ship these checks in the same commit
as the behaviour: [measured] [asserted]

- reject a full application-build child with no `effort.plan`, compatible category, derived decide/do
  projection or atomic charge; reject any child above the frozen request, quota or spend ceiling, and
  reject a pre-realisation charge that would leave any component of `B` below
  `realisation_reserve`; [asserted]
- for better-than-best, require valid ADR-0092 category, semantic-phase and handover references;
  effort accounting cannot create, rename or reinterpret a threshold outcome, and missing actual
  usage renders `unavailable`; [asserted]
- prove no universal 80/20 or other phase ratio is an admission predicate, while planned and actual
  decide/do and protocol-phase dispatches, reservations and tokens remain reportable; [asserted]
- prove fast requires an immutable `fast_admitted` package, never accepts a bar-status receipt, runs
  only realisation categories, makes no better-than-best claim and stops before another effect when a
  gate becomes false; [asserted]
- prove auto-light launches no work item, recall, retrieval, tool, squad or event-writing path;
  explicit light never silently promotes; [asserted]
- prove supervision freezes one instruction, exposes only development diagnostics during at most
  three corrections, runs held-out acceptance once, retains all adverse outcomes and cannot emit a
  human decision; [asserted]
- prove only the Owner freezes the candidate, no correction changes the goal/verifier, and a fourth
  weak retry is structurally unreachable; [asserted]
- prove candidate exposure uses ADR-0077's robust ceiling, role composition uses ADR-0067's distinct-
  anchor rule, and concurrency uses independent work units rather than either quantity. [asserted]

No implementation may add a second append writer, task store, orchestrator, budget ledger or router.
`dispatch.py`, `coordination.py`, `recall.py`, `work_items.py`, `routing.py`, `budget.py`,
`instructions.py` and `events.py` are the extension points. [asserted]

## 12. Evidence against: 80/20 may be backwards

The strongest objection is that deciding is cheap and building is where reality answers back.
Integration, migration, browser behaviour, deployment, debugging and user contact expose constraints
that no pre-build conversation can see. Most projects may fail because execution is hard rather than
because the first approach was wrong; allocating four fifths of scarce inference before an artefact
exists may be a dressed-up waterfall, while an execution-heavy competitor ships, observes and
iterates. That claim is plausible and decision-relevant, but it is `[asserted]`, not established by
the sources read here. [asserted]

The nearest repository measurement cuts against deliberative machinery. EXP-16's single-agent arm
won 9 of 12 substituted model-family judgements while the Owner meeting won 2 of 12 at 4.8 times the
tokens and 3.7 times the wall time. The registered human ground-truth judgement was never obtained,
so this measures substituted grader preference and overhead, not human-labelled quality. [measured]

Superpowers upstream also removed an independent subagent review loop after a five-version by five-
trial comparison added about 25 minutes without measurable plan-quality improvement. That is not a
test of frontier supervision over a weaker executor, but it is direct evidence that review ceremony
can consume time without buying quality. [cited: bibliography section 19]

Schmalbach likewise found explicit delegation contracts bought reviewability rather than objective
correctness on 64 small coding-agent runs, while adding 13% tokens and 38% wall time; Yang et al. found
cheap protocol references competitive and protocol-specific value hard to predict on paired reasoning
tasks. The domains are narrower than application building, but both make unmeasured process overhead
a live adverse outcome rather than a presumed investment. [cited: bibliography section 19]

The 80/20 treatment can also starve implementation so badly that a superior decision never becomes a
working artefact. Research can keep finding new questions, simulation can optimise an invented model,
and experiments can delay the feedback only a build provides. A phase budget does not cure motivated
deliberation; it can institutionalise it. [asserted]

This specification concedes the objection rather than explaining it away. No ratio is configured,
unused capacity is never burned, deciding can end at the externally checked threshold, and EXP-133
includes threshold-triggered allocation, 80/20, its 20/80 inverse and the pinned Superpowers workflow
at equal total budget. A win may justify a successor ADR proposing a numeric default; an inverse or
comparator win keeps 80/20 unconfigured, while a threshold-arm loss can overturn this transition
mechanism. The phase taxonomy, fast admission and light mode do not depend on the ratio. [asserted]

## 13. Plain answer and delta

The plain answer would be: locate the incumbent, decide until independently checked evidence clears
its bar or a hard ceiling fires, then build; let a frontier model review cheaper implementation, use
a fast path for easy work, and add a light chat toggle. [asserted]

The delta is the refusal surface: phase use is explicit without laundering 80/20 into policy; phase
two executes and exits on independent anchors or an honest `bar_not_beaten`; supervision has three
corrections, held-out verification, a total-budget stop and an economic loss rule; fast has five gates;
light names every guarantee it discards; and EXP-133/134 can kill the two unmeasured claims. [asserted]

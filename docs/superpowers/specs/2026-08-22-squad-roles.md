# Squad roles: exact rights, structural consultation, preserved dissent

**Corrections:** the brief's exposure statement is too strong: ADR-0077 makes the current candidate
ceiling at most one for `epsilon <= 0.40`, and zero below the recorded `beta_upper`; a model-family
difference alone is `unmeasured`, not a different evidence class; and ADR-0020 already retains an
Owner/Contributor/Evidence/Informed authority matrix, so R, C and I extend an existing schema rather
than a blank slate. [measured] [algebra]

- **Status:** design only; PROVISIONAL under ADR-0082 and EXP-107. [measured]
- **Extends:** ADR-0067's one accountable Owner, ADR-0020's retained authority matrix,
  ADR-0075's six protected classes, ADR-0077's evidence fusion and ADR-0081's structural-anchor
  vocabulary. [measured]
- **Non-goals:** no product implementation, gate-condition change, routing-flag change, new CLI
  command, new coordinator, second assignment registry, second event writer or second fusion table.
  [measured]

## 1. Answer first

RACI is a per-work-item rights projection over the existing work-item contract. It is not an agent
org chart and does not create a meeting. Exactly one accountable Owner remains the decision-maker;
Responsible produces work artefacts; Consulted contributes a structurally different acquisition and
may preserve dissent or trigger a pre-committed block; Informed receives the result and has no work-
item rights. [asserted]

One runtime normally co-holds Accountable and Responsible. A second runtime is added only when a
consequential decision can use a decision-changing class of facts which the current composition
cannot acquire under the required isolation or capability contract. Role count, headcount and
candidate exposure are separate quantities. [asserted]

The different-class obligation applies to every added evidence-bearing member. A is governance
provenance and I is a recipient projection, not a second induction; neither receives evidence credit
or enlarges active composition. [asserted]

RACI adds no epistemic weight. ADR-0077 continues to fuse completed readings; ADR-0081 continues to
decide whether a high-consequence conclusion has a convergent structurally distinct pair; and the
Accountable role alone dispositions the result. [measured] [asserted]

## 2. The four roles and their exact decision rights

The rights below attach to one `ticket` and `revision`. They end with that assignment and do not
become an agent identity, rank or reusable authority. One actor may hold several compatible roles,
but each role is recorded separately and confers only the rights in its row. [asserted]

| role | cardinality and exact right | may author | may not author | trajectory mapping |
|---|---|---|---|---|
| **A - Accountable Owner** | Exactly one. Decides the scoped non-protected choice and remains accountable after dissent. [cited] (ADR-0067) | The final candidate selection, non-protected `decision.autonomous` content, disposition of every recorded dissent, role plan and closure content. A coordinator may validate and append these records, but may not choose their content. [asserted] | Another Owner, an unstated scope change, evidence it did not acquire, a vote/average, or any principal-protected decision. [asserted] | Existing `work_item.opened.data.accountable`; future closure binds the same Owner, attempt, artefacts, verifier receipts and dissent dispositions. [measured] [asserted] |
| **R - Responsible** | Zero or more assignments. Performs a frozen scope of work and produces its artefacts. The default Owner also holds R. [asserted] | Candidate components, code/doc/data artefacts, attempt and tool receipts, bounded analysis, an experiment pre-registration when assigned the Experimenter contract, and its own terminal outcome or refusal. [asserted] | The final scoped decision, another role's return, a verifier or stopping-rule change after outcomes, a dissent disposition, direct role release, or work-item closure. It gains final rights only through a separately recorded A assignment. [asserted] | Existing attempt/dispatch claims and artefact-bearing events; future `composition` and claims bind `assignment_id`, scope, paths, attempt and expiry. [measured] [asserted] |
| **C - Consulted** | Zero or more admitted assignments. Supplies a completed acquisition from a different structural class. Its typed observation position may become preserved dissent, and it may block acceptance only through a frozen necessary condition; it never decides. [asserted] | Its sealed source-kind event, immutable `evidence_refs`, scope/estimand/limits, a required typed position copied from that event, its own terminal outcome or refusal, and a `blocking_contract_ref` when the observation falsifies that exact condition. [asserted] | Candidate text, final decision, vote, dissent disposition, direct role release, changed acceptance criteria, principal authority, or a rhetorical veto. [asserted] | Existing `verification.outcome`, `knowledge.retrieved` and evidence-bearing `work_item.comment` are partial substrates; no current event records C or proves structural admission. [measured] |
| **I - Informed** | Zero or more recipients. Receives the sealed decision or a pull view and has no input, artefact, block, dissent, decision or closure right. [asserted] | Nothing under this assignment. Receipt telemetry may be appended by the delivery system, not as an I-authored contribution. [asserted] | Every work-item input and state transition. A message from I is ignored for this decision unless a new revision assigns another role before acquisition. [asserted] | No current role field exists. The future `composition` records recipient and release only; I receives no execution claim. [measured] [asserted] |

The Accountable role does not own truth. Responsible does not become Accountable by doing most of
the work. Consulted does not become a co-decider by finding a defect. Informed is not Consulted with
a better title. [asserted]

### Existing ADR-0067 contracts project into these rights

| ADR-0067 contract | per-item RACI projection |
|---|---|
| Domain specialist | R while producing a candidate component; C only when it seals a structurally admitted source/corpus reading outside candidate authorship. [asserted] |
| Executing verifier | C when its completed execution satisfies structural admission; otherwise its output remains a diagnostic event with no C slot. [asserted] |
| Adversary | C only for an executed counterexample, mutation or hostile input from a distinct acquisition; a prose objection over shared context is I. [asserted] |
| Replicator | C only when the reacquisition has a countable channel, distinct observation anchor and known disjoint roots; family difference alone is `unmeasured`. [asserted] |
| Experimenter | R authors and runs the pre-registration; its sealed measured outcome may then supply C evidence if structurally admitted. [asserted] |
| Principal | Outside agent RACI for protected authority; may personally hold A for a preference, but no agent can project or impersonate that assignment. [asserted] |

### Principal authority is outside RACI

No RACI role delegates ADR-0075's six protected classes: `money`, `credential`,
`external_exposure`, `unrecoverable_state_loss`, `principal_authority` and `preference`.
`principal_authority` contains `approval`, `consent`, `gate_lift`, `spend_authorisation` and
`verdict`. Only the principal's exact first-party authority event can authorise one; an Accountable
agent may propose and a Consulted agent may supply evidence, but neither may approve. [measured]
[asserted]

The current product schema has not yet completed ADR-0075's six-class mapping, and its CLI actor
check is declared provenance rather than authenticated identity. This specification therefore makes
the boundary a same-commit implementation requirement and does not claim it is structurally
impossible today. [measured]

## 3. Consulted is an acquired class, not a label

Consulted admission reuses ADR-0081's structural vocabulary and the decision protocol's immutable
reference shape. It does not compare evidence tags, actor names or prose labels. [measured]

Before acquisition, a proposed C assignment freezes: [asserted]

- the conclusion and acceptance-contract digest;
- the deciding induction's complete credited-channel manifest and one ADR-0081 countable
  `acquisition_channel` absent from that manifest and every other proposed C contract;
- an observation-anchor contract, known derivation roots and dependence metadata;
- the sources/tools/context the assignee may see before sealing;
- the possible observation which would change the scoped decision; and
- budget, expiry and terminal refusal behaviour.

After acquisition, the projection admits C only when its immutable reference
`{event_id, event_kind, event_sha256}` resolves to a unique earlier completed source-kind event; the
event validates the contracted channel and observation-anchor identity; that channel differs from
every channel in the frozen deciding manifest and every admitted peer C; its complete derivation
roots are known and disjoint from the deciding induction; and no pre-seal access record shows the
assignee reading the Owner's synthesis or a peer return outside the frozen contract. [asserted]

This is ADR-0081's structural-distinctness test without its convergence condition. Agreement cannot
be an admission requirement because a valid Consulted reading may dissent. Convergence is evaluated
later by ADR-0077/0081 against the frozen alternatives and loss contract. [asserted]

The countable channels remain `artefact_execution`, `browser_observation`,
`primary_source_retrieval` and `novel_corpus_observation`. A different model/provider family,
persona, role, prompt, evidence tag, review pass, unexecuted opinion or majority vote receives zero
structural credit. Family remains correlation metadata under ADR-0077. [asserted]

If the contract lacks a countable channel, decision-changing observation or known distinct anchor,
the assignment is recorded as I with `reclassified_from: consulted` and reason `echo` or
`unmeasured`; it receives no C rights. If a frozen C acquisition later refuses, expires or proves
overlapping, the adverse return remains in the record and the final projection is I; a required C
does not silently become optional, so the candidate remains incomplete or follows ADR-0081's
refusal path. [asserted]

### Blocking is a contract result, not a veto

C may mark `blocking_contract_ref` only when a completed structurally admitted reading falsifies a
necessary condition frozen before acquisition. The work-item projection then makes that candidate
ineligible; the pre-committed contract did the blocking, not C. A may revise the artefact under a new
attempt, terminate adverse or escalate only through ADR-0075. [asserted]

Every other disagreement is dissent. A decides, records the consequence and preserves the dissent;
C cannot demand agreement, and A cannot delete the reading. [asserted]

## 4. Dissent survives mechanically

Before any C work, A freezes a `position_contract_ref` derived from the acceptance contract. It
defines only the canonical type and encoding shared by the observation position and decision
primitive; it contains no adjustable tolerance or compatibility function. [asserted]

Every completed C return is sealed and appended before A receives the set. Its source-kind event
must carry one typed `position` under that contract, and the C return must copy the same position
digest. `neutral` is not a valid C position. An acquisition that cannot produce the contracted
position is adverse `unmeasured`, refusal or timeout, never silent neutrality. [asserted]

`selected_position` is the canonical decision primitive, not an Owner-authored annotation. For a
candidate choice it contains the selected candidate digest and typed acceptance/disposition; for a
non-candidate choice it is the selected Boolean, enum, number, range, ranking or scope value. The
universal append boundary canonicalises that primitive, recomputes its digest and rejects a missing
or mismatched candidate/effect field through both helper and raw-append paths. Explanatory prose is
derived display and cannot override the primitive. [asserted]

The universal projection compares that recomputed digest with every completed C position. Every
non-identical digest is derived dissent and keeps the immutable C return reference; no contributor
Boolean, free-form Owner field or Owner-defined comparator can suppress it. This deliberately over-
records rather than loses numeric/range, ranked or scope differences; disposition, not a tolerance,
decides whether a difference changes the outcome. Failure of a frozen necessary condition also
remains an automatically detected material conflict. Prose sentiment is not used to infer conflict.
[asserted]

An evidence-bearing C `work_item.comment` gains structured fields for `assignment_id`,
`position_contract_ref`, required `position` and `position_digest`, `scope`, `estimand`, `limits`,
immutable `evidence_refs`, optional `material_conflict_id` and optional `blocking_contract_ref`. The
text remains explanatory; the fields carry the state. The closure projection derives the dissent set
from these immutable returns instead of adding a dissent store. [asserted]

Before `work_item.completed`, A must reference every return in the derived dissent set, including
every automatically detected material conflict, and use the existing
task-management vocabulary: `resolved_by_evidence`, `owner_selected_reversible`, `escalated` or
`recorded_unresolved`. A decision against C uses `owner_selected_reversible` only when the options
remain above the acceptance floor and records both consequence branches, the reversal and the
falsifier. Dissent on which success depends remains `recorded_unresolved` and blocks closure; it is
not rewritten as agreement. A later resolution appends a new reference and never overwrites the
dissent event. [measured] [asserted]

This is not a veto. A remains the sole decider unless a frozen necessary condition failed or an
independent ADR-0075 authority boundary applies. The universal event boundary refuses closure with
any undispositioned derived dissent, including when the convenience helper is bypassed. [asserted]

## 5. When the squad grows

The default is one runtime co-holding A and R with every ordinary allowed tool. A role assignment
does not by itself add a runtime, and an I recipient is not an active squad member. [cited]
(ADR-0067)

Add another **R runtime** only when the frozen deliverable contract contains a non-overlapping
artefact/owned-path scope whose failure consequence justifies coordination cost, whose output can
change acceptance, and whose required state, source or capability is unavailable to the current
composition without breaking isolation. A second implementer reading the same brief for speed alone
is not added. Genuinely independent deliverables are separate work items under ADR-0068, each with
its own A/R contract, rather than evidence-free R duplication inside this item. [asserted]

Add a **C runtime** only when the action is consequential under ADR-0077/0081, an available
structurally distinct acquisition could change it, its conservative information value exceeds its
acquisition/delay cost, and the current composition cannot acquire it under the frozen isolation
contract. Difficulty, ambition, seniority and model brand are not triggers. [algebra] [asserted]

If no distinct class is available, no C is created. A reversible low-consequence item proceeds with
labelled single-anchor or `unmeasured` uncertainty; a high-consequence item follows ADR-0081's
bounded acquisition and refusal rule. The principal is contacted only for an independently proven
ADR-0075 class, never to manufacture consultation. [asserted]

Headcount never licenses extra candidates. Multiple R assignments may produce components of one
Owner-selected candidate. Alternative independently acceptable candidates are attempts governed by
ADR-0077's candidate-exposure union; C readings are inputs to ADR-0077's evidence fusion. This
specification adds neither a candidate nor a fusion equation. [algebra] [asserted]

At ADR-0077's recorded mutation-proxy `beta_upper = 0.334582`, the robust candidate ceiling is one
at `epsilon = 0.40` and zero for `epsilon < beta_upper`. Live human-labelled beta remains
unestimated because `consil beta` has only one human rejection against a minimum of 30; routing must
refuse rather than infer a headcount or exposure allowance from that absence. [measured] [algebra]

## 6. Scientific and mathematical method is assigned work

ADR-0079 specifies, but does not yet implement, a future Better-Than-Best threshold path. Under that
path A owns freezing the three threshold inputs and causing
`.agents/skills/better-than-best/SKILL.md` to run; A may not waive or replace a selected run. An
assigned R executes the five stages and produces the bar, search, stress-test, synthesis and killing-
check artefacts. If one runtime co-holds A and R, both obligations remain separately visible in
`composition`. [measured] [asserted]

When a material disagreement is empirical, A assigns an R with ADR-0067's Experimenter contract.
That R owns writing the experiment-register entry and fixing its stopping rule before any outcome is
visible; A freezes the experiment reference in the work item and decides after the sealed result. C
may supply the dissent, falsifier or an independently acquired reading, but may not move the
procedure or stopping rule after observing data. [asserted]

When the disagreement is algebraic, R supplies the derivation or executable model where the Inquiry
tier requires it, and C may check it only through a distinct acquisition such as executed
counterexamples or a retrieved primary source. Another derivation from shared premises is useful
review but is not C. [asserted]

Closure is refused when a selected Better-Than-Best run lacks its required artefact references, or
when an empirical resolution cites an experiment absent from the register or registered after its
first outcome. The skill continues to shape judgement; the work-item structure only decides when it
runs and checks that its artefacts exist. [asserted]

## 7. Assignment, claim and release use the existing trajectory

`work_item.opened.data.accountable` remains the scalar authority source for the single A. The
already-specified `composition` retains exactly one Owner entry and adds R/C/I assignments; that
Owner entry's assignee must equal `accountable`. Each entry carries `assignment_id`, role, assignee,
scope/acceptance digest, authority and budget references, expiry, and the applicable Owner, R
deliverable/owned-path, C acquisition or I recipient contract. Co-held A and R remain separate role
entries. Rights derive from the closed role enum and cannot be widened per assignment. [measured]
[asserted]

`coordination.py` remains the projection and claim boundary. An R or C attempt claim binds the work-
item ticket/revision, `assignment_id`, `attempt_id`, canonical paths or observation-anchor contract,
opened time and expiry. I receives no claim. Acquisition and conflict checking must become one
atomic compare-and-append; the current check-then-open sequence is not sufficient for role rights.
[measured] [asserted]

An assignee may author only its terminal attempt outcome or refusal; that event does not itself
release the assignment. The coordination boundary alone validates the actor, ticket, revision,
assignment and attempt, then projects release from that terminal event, expiry plus adverse closure,
or root work-item completion. Expiry releases the resource claim but does not erase a required role:
it leaves a terminal adverse outcome. A changed assignee, scope, role or evidence contract creates a
superseding work-item revision; no record is reopened or mutated. [asserted]

The current substrate is incomplete: `work_items.py` records only opened/comment/completed;
completion is a bare ticket; `coordination.py` does not bind role, revision or attempt and accepts a
matching completion without checking releaser authority; and generic `events.append()` does not
apply every specialised work-item rule. These are future enforcement gaps, not evidence for a
second registry. [measured]

## 8. Reuse and enforcement

Future implementation extends `work_items.py`, `coordination.py`, `events.py` and the existing
dispatch claim path. `recall.py` continues bounded context, `instructions.py` selects skills,
`routing.py` owns candidate exposure, `budget.py` owns spend and `events.py` remains the sole writer.
No new orchestrator, queue, database, fusion table or CLI command is admitted. [asserted]

The implementation commit must make these checks executable at the universal event/claim boundary:
[asserted]

1. exactly one scalar `accountable` Owner across one work-item revision, equal to the sole A entry in
   `composition`, with only A able to select the candidate, disposition dissent and supply closure
   content;
2. role-scoped authorship: R only artefacts, C only sealed readings/dissent/bounded blocks, and I no
   work-item contribution;
3. C admission from validated acquisition channel, observation anchor and derivation roots, with a
   family/label-only proposal mechanically recorded as I;
4. every selected-position digest recomputed from the canonical decision primitive at the universal
   boundary, every completed C position compared with it and every derived dissent, including every
   automatically detected material conflict, dispositioned before closure;
5. atomic assignment claims and authorised, identity-bound release, including expiry as adverse;
6. exact first-party authority for ADR-0075's six classes, unaffected by any RACI field;
7. removal of the current `family:<model family>` evidence-class fabrication from fan-out; and
8. a source/tree check proving no second assignment registry, writer, coordinator, fusion path or
   seventh CLI command bypasses these rules.

The focused tests belong in the existing `tests/test_work_items.py`, `tests/test_coordination.py`,
`tests/test_v0_invariants.py` and dispatch tests. A helper-only check is insufficient because the
generic append path currently bypasses specialised work-item validation. [measured] [asserted]

No implementation ships with this document. `routing_orchestration_enabled` remains `false`, Gate A
and Gate B are unchanged, and the command set remains six. [measured]

## 9. Falsifier: EXP-107

EXP-107 is written in `docs/10-research/experiment-register.md` with a fixed stopping rule. It reuses
EXP-80's frozen 80-task bank, matched-budget Owner arm, evidence-squad arm, runner, blinding, cost
and safety definitions, and adds only one prospectively frozen ADR-0082 arm. [measured]

The RACI arm must beat both the matched-budget Owner and the existing evidence squad on blinded
human-plus-verifier joint acceptance under the registered quality, safety, cost and protocol-
validity thresholds. Beating the Owner but not the evidence squad attributes the gain to distinct
evidence or compute and cuts the generic RACI layer as cargo. Missing safety denominators remain
insufficient evidence; no outcome changes gates, principal authority or candidate exposure.
[asserted]

## 10. Evidence against: RACI is human-organisation cargo

The strongest objection is that RACI exists because humans need to know whom to invite, whom to
blame and who must sit through a meeting. Agents have none of those needs. The append-only trajectory
already identifies actors and artefacts; ADR-0067 already supplies exactly one Owner, distinct-
anchor admission and preserved conflict; ADR-0075 already reserves principal authority. Adding four
letters can only add schema, hand-offs and respectable-looking echo. [measured] [asserted]

The repository's direct evidence favours that objection. EXP-16's single-agent arm won 9 of 12 blind
judgements against 2 of 12 for the Owner meeting while the meeting used 4.8 times the tokens and 3.7
times the wall-clock. ADR-0020 therefore cut meetings and retained only its authority matrix.
[measured]

Ao, Gao and Simchi-Levi show that delegation with the same exogenous signals cannot improve an ideal
central decision-maker; Kim et al. found task-dependent multi-agent gains and losses under matched
configurations. A role label is not the exogenous signal those results leave room for. [cited]

The objection is substantially conceded. ADR-0082 keeps RACI only as a small permission projection
over fields and events already required for work, evidence and dissent. It creates no meeting,
manager, vote, queue or fusion rule. If EXP-107 does not show incremental accepted-outcome value over
the existing evidence squad, remove the R/C/I projection and keep ADR-0067's Owner, anchors and
dissent. A schema that merely clarifies blame does not survive. [asserted]

## 11. Plain answer and delta

**Plain answer:** keep one Owner, let workers produce artefacts, require independent evidence and
tell everyone else the result. [asserted]

**Delta:** exact per-item authoring rights; C automatically becomes I when structural evidence is
absent; a pre-committed block is separated from non-veto dissent; dissent is closure-blocking until
dispositioned; Better-Than-Best and experiment preregistration have named owners; and EXP-107 removes
the extra role layer if those mechanics do not improve accepted outcomes. [asserted]

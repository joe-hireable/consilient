# 0082. Project RACI onto per-work-item rights and require structural consultation

**Corrections:** the current candidate ceiling is at most one, not one for every
`epsilon <= 0.40`; model family alone is `unmeasured`, not a different evidence class; and
ADR-0020 already retained an authority matrix, so this decision supersedes that retained schema
rather than inventing R, C and I from nothing. [measured] [algebra]

- **Status:** PROVISIONAL - EXP-107 can remove the generic RACI projection while retaining
  ADR-0067's one Owner, structural anchors and dissent
- **Date:** 2026-08-22
- **Deciders:** Joe Brown (product direction, quoted exactly in the dispatch brief: "Agent squads I
  think. RACI to ensure decisions are made but explored thoroughly with scientific and mathematical
  approaches, experimentation."); Codex dispatch `20260822T140208-40b9767b0c` (provisional
  mechanism)
- **Supersedes:** ADR-0020's retained Owner/Contributor/Evidence/Informed matrix only; its cut of the
  meeting mechanism remains in force
- **Inquiry tier reached:** T1 ground; T3 pre-registered as EXP-107, not run
- **Executable model:** none - the role rights and structural-admission predicate are exact; EXP-107
  measures the disputed accepted-outcome and cost effects

## Context

ADR-0067 already establishes exactly one accountable Owner, one candidate, a default composition of
one, structural evidence anchors and preserved disagreement. ADR-0077 already owns candidate
exposure, composite verification and evidence fusion. ADR-0081 already defines countable acquisition
channels, observation anchors, derivation roots and `unmeasured`. Recreating any of those mechanisms
inside RACI would be a second source of truth. [measured]

ADR-0020 previously adapted RACI as Owner/Contributor/Evidence/Informed/Escalation. EXP-16 then cut
the meeting mechanism after the single-agent arm won 9 of 12 blind judgements against 2 of 12 for the
Owner meeting at 4.8 times the tokens and 3.7 times the wall-clock, while retaining the authority
matrix as schema. The useful question is therefore whether exact role rights add value without
recreating the failed meeting. [measured]

Current work items persist `accountable`, comments and bare completion; coordination persists
expiring path claims. No current record represents R, C or I, proves a Consulted acquisition
structurally distinct, preserves typed dissent through closure, atomically acquires an assignment or
projects identity-bound release through the coordination boundary. Current fan-out also emits model
family as an
`evidence_class`, contrary to ADR-0067 and ADR-0081. [measured]

The principal specified squads and RACI as product direction. He did not specify the event schema,
role rights, composition trigger or experiment below; those remain this ADR's provisional design.
[measured]

## Decision

Consilient will represent RACI as a closed, per-work-item rights projection over the existing
trajectory and coordination substrate. It will not create an org chart, manager, meeting, vote,
queue, assignment database or fusion table. [asserted]

### Exact rights

1. **A - Accountable Owner:** exactly one, recorded by the existing scalar `accountable`. A alone
   selects the final candidate, authors the scoped non-protected decision content, dispositions every
   recorded dissent and supplies closure content. A may not author a principal-protected decision.
   [asserted]
2. **R - Responsible:** zero or more per-item assignments. R performs frozen work and authors work
   artefacts, receipts and, when assigned the Experimenter contract, the experiment pre-registration.
   R may author its own terminal outcome or refusal but may not decide, disposition dissent, directly
   release a role or close the item. The default Owner also holds R. [asserted]
3. **C - Consulted:** zero or more structurally admitted acquisitions. C authors a sealed reading,
   immutable evidence references, limits, a required typed position copied from its source-kind
   event and its own terminal outcome or refusal. Its position may become preserved dissent. It
   may make a candidate ineligible only by
   tying a completed observation to a necessary condition frozen before acquisition. It may not
   decide, vote, rewrite criteria or exercise a rhetorical veto. [asserted]
4. **I - Informed:** zero or more recipients. I receives the result and has no input, artefact,
   block, dissent, decision, assignment, release or closure right. [asserted]

Roles attach to one ticket/revision and end with the assignment. An actor may co-hold compatible
roles, but the rights do not become a persistent identity or rank. Role count does not imply
headcount, and headcount does not imply candidate count. Every added evidence-bearing member must
name a different class; A is governance provenance and I is a recipient, so neither receives
evidence credit or enlarges active composition. [asserted]

### Consulted admission and echo

A proposed C acquisition freezes the conclusion/acceptance digest, the deciding induction's complete
credited-channel manifest, one ADR-0081 countable `acquisition_channel` absent from that manifest and
every other proposed C contract, observation-anchor contract, known derivation roots, allowed pre-
seal context, decision-changing possible observation, budget and expiry. [asserted]

After acquisition, C is admitted only when its immutable reference
`{event_id, event_kind, event_sha256}` resolves to a unique earlier completed source-kind event with
the contracted channel and observation anchor, a channel different from every frozen deciding and
admitted peer channel, known derivation roots disjoint from the deciding induction and no disallowed
pre-seal peer access. Agreement is not required: a structurally distinct reading may dissent.
ADR-0077/0081 evaluate convergence later. [asserted]

The admitted channels are ADR-0081's `artefact_execution`, `browser_observation`,
`primary_source_retrieval` and `novel_corpus_observation`. Model/provider family, role, persona,
prompt, evidence tag, repeated context, unexecuted opinion and vote receive zero structural credit.
A proposed C lacking a countable, decision-changing, structurally distinct acquisition is recorded
as I with reason `echo` or `unmeasured` and receives no C rights. [asserted]

### Dissent and blocking

Before C work, A freezes a `position_contract_ref` derived from the acceptance contract and defining
only the canonical type and encoding shared by observation and decision. It contains no configurable
tolerance or comparator. Every completed C source event and return carries the same required typed-
position digest; `neutral` is invalid, and inability to produce the position is adverse `unmeasured`,
refusal or timeout. [asserted]

`selected_position` is the canonical decision primitive, not a free-form Owner annotation: for a
candidate it contains the candidate digest and typed acceptance/disposition; otherwise it is the
selected typed value. The universal append boundary canonicalises it, recomputes its digest and
rejects a missing or mismatched candidate/effect field through helper and raw paths. Prose is derived
display. The projection then derives dissent for every non-identical C digest. No contributor Boolean,
free-form Owner field or Owner-defined comparator can suppress it. This deliberately preserves
numeric/range, ranked and scope differences; failure of a frozen necessary condition remains an
automatically detected material conflict. [asserted]

Before closure, A must reference every return in the derived dissent set, including each
automatically detected material conflict, and record one existing disposition:
`resolved_by_evidence`, `owner_selected_reversible`, `escalated` or `recorded_unresolved`. A may use
`owner_selected_reversible` only when every option remains above the acceptance floor and it records
the consequence branches, reversal and falsifier. Success-dependent unresolved dissent blocks
closure; a later resolution appends another event rather than overwriting dissent. This is not a
veto: A still decides unless a pre-committed necessary condition failed or an independent ADR-0075
authority boundary applies. [asserted]

### Composition, method and authority

The default is one runtime co-holding A and R. Another R runtime requires a consequential,
non-overlapping artefact scope whose decision-changing output needs state/source/capability absent
from the current composition under the required isolation. Another C runtime requires a
consequential decision, a structurally distinct acquisition whose possible observation changes the
action, information value above acquisition/delay cost, and isolation the current runtime cannot
preserve. Another implementer reading the same brief for speed is not added; independent deliverables
become separate ADR-0068 work items. Difficulty, ambition, title and model brand are not triggers.
[algebra] [asserted]

If no distinct class is available, no C is created. Reversible low-consequence work proceeds under
labelled single-anchor or `unmeasured` uncertainty; high-consequence work follows ADR-0081's bounded
acquisition/refusal rule. Added members feed one Owner-selected candidate. Alternative shippable
candidates remain ADR-0077 attempts and evidence readings remain ADR-0077 fusion inputs. [asserted]

A owns causing ADR-0079's specified future Better-Than-Best threshold path to invoke the retained
skill once that path exists; an assigned R executes its five stages. When a disagreement is
empirical, A assigns an R-Experimenter;
that R owns writing the register entry and fixing the stopping rule before outcomes, while A freezes
the reference and later decides. C may supply the dissent or falsifier but cannot change the
procedure after data. [asserted]

RACI conveys no authority over ADR-0075's `money`, `credential`, `external_exposure`,
`unrecoverable_state_loss`, `principal_authority` or `preference` classes. A role may propose or
bring evidence; only the principal's exact first-party event can authorise the protected effect.
Role assignment can never mint or substitute that authority. [asserted]

### Assignment and release

`work_item.opened.accountable` remains the scalar authority source for A. Its already-specified
`composition` retains exactly one Owner entry, whose assignee must equal `accountable`, and adds R/C/I
assignments with stable id, assignee, scope, contract, authority/budget refs and expiry.
`coordination.py` binds R/C attempt claims to the same ticket/revision, assignment, attempt, paths or
observation anchor and expiry. I receives no claim. [asserted]

Acquisition is one atomic compare-and-append. An assignee may author its terminal outcome/refusal but
cannot directly release the assignment. The coordination boundary alone validates the same ticket,
revision, assignment, attempt and actor, then projects release from that terminal event, expiry plus
adverse closure, or root completion. Expiry releases resources but does not erase a required role.
Any role, scope, assignee or contract change creates a superseding work-item revision. The trajectory
remains the only registry. [asserted]

The complete protocol is specified in
`../superpowers/specs/2026-08-22-squad-roles.md`. EXP-107 is written in
`../10-research/experiment-register.md` with its stopping rule fixed before any EXP-80/107 outcome.
[measured]

## Evidence

- `[measured]` ADR-0067 and the task-management specification already require one scalar Owner,
  structural composition and conflict disposition; current source persists only part of that
  contract.
- `[measured]` ADR-0020 already retained an authority matrix after cutting meetings; this ADR is a
  supersession of that matrix, not the first RACI design.
- `[measured]` EXP-16's single-agent arm beat the Owner meeting 9/12 to 2/12 at substantially lower
  token and wall-clock cost.
- `[measured]` ADR-0081 now supplies the acquisition-channel, observation-anchor, derivation-root and
  `unmeasured` vocabulary; this ADR does not create a parallel class system.
- `[measured]` EXP-107 exists in the register and reuses EXP-80's task bank and controls, adding only
  one prospective role-enforced arm.
- `[algebra]` Evidence-role headcount feeding one candidate does not increase candidate exposure;
  independently acceptable candidates do. ADR-0077 owns that union.
- `[cited]` Ao, Gao and Simchi-Levi (2026), arXiv:2603.26993, show that delegation with the same
  exogenous signals cannot improve an ideal central decision-maker.
- `[cited]` Kim et al. (2026), doi:10.1038/s42256-026-01268-y, find task-dependent gains and losses
  across matched multi-agent configurations.
- `[asserted]` Exact role rights, structural C-to-I demotion and closure-bound dissent will improve
  accepted outcomes enough to repay their coordination cost. EXP-107 is the killing test.

## Evidence against

The strongest case is that **RACI is human-organisation cargo**. Humans need to know whom to invite,
whom to blame and who must attend a meeting. Agents do not. The trajectory already records actors
and artefacts; ADR-0067's one Owner plus distinct-anchor rule already determines who decides and what
extra evidence is admissible; ADR-0075 already reserves the principal. Four letters can add nothing
but schema, hand-offs and respectable-looking echo. [measured] [asserted]

EXP-16 is direct evidence for that objection: the structured Owner meeting lost badly to one agent
while costing several times more. Ao, Gao and Simchi-Levi make the information objection exact when
roles add no exogenous signal, and Kim et al. show that multi-agent overhead often degrades matched
outcomes. [measured] [cited]

The objection is conceded unless EXP-107 defeats it. This ADR keeps RACI only as a permission
projection over work-item fields already needed for accountability, evidence and dissent. It adds no
meeting, manager, vote, queue or fusion rule. If the RACI arm does not improve blinded accepted
outcomes over both the matched-budget Owner and the existing evidence squad under the fixed safety
and cost conditions, the R/C/I layer is removed and ADR-0067's simpler rules remain. [asserted]

Known weaknesses remain: structural channel difference is not statistical independence; role
validators can reward schema-compliant filler; automatic C-to-I projection can discard useful but
poorly instrumented expertise; and strict dissent closure can turn missing metadata into delay.
[asserted]

## Consequences

**Positive** - work-item authoring rights become exact; echo cannot occupy C; typed dissent
survives closure; scientific synthesis and experiment preregistration have named owners; the
principal's authority stays outside the role system. [asserted]

**Negative** - composition, comments, claims and closure gain fields and validation; assignments need
atomic acquisition and authorised release; valid but uninstrumented advice becomes I; incorrect
metadata can refuse useful work. [asserted]

**Neutral but load-bearing** - one Owner, one candidate, ADR-0077 fusion/exposure, ADR-0081's
high-consequence gate, the six protected classes, six-command CLI and false routing flag remain
unchanged. [asserted]

## Enforcement

This documentation commit implements no role layer and changes no product code or gate condition.
[measured]

- **Universal role check:** future `tests/test_work_items.py` fixtures prove exactly one A,
  role-scoped authorship, I with no contribution rights and Owner-bound closure through both helper
  and raw append paths. [asserted]
- **Consulted check:** family/label/repeated-context proposals project to I; only completed valid
  acquisition-channel/anchor/root references admit C; dissenting distinct observations remain C.
  [asserted]
- **Dissent check:** raw and helper appends recompute the selected-position digest from the canonical
  decision primitive, reject a mismatched candidate/effect field, compare every completed C position
  and refuse any undispositioned dissent, including numeric, ranked and
  scope alternatives, and preserves the earlier event after a later resolution. [asserted]
- **Coordination check:** future `tests/test_coordination.py` fixtures prove atomic acquisition,
  assignment-bound claims and authorised release; another actor cannot release the claim. [asserted]
- **Authority check:** every role-shaped path still refuses all six protected classes without exact
  first-party authority; assigning A to an agent cannot mint principal authority. [asserted]
- **Bypass check:** remove family-derived evidence credit and scan for a second assignment registry,
  coordinator, event writer, fusion path or CLI command. [asserted]
- **Fails CI:** no - no implementation ships in this commit. [measured]
- **Added in the same commit as implementation:** required. [asserted]

## What would overturn this

EXP-107 kills the generic RACI projection if its role-enforced arm fails the registered accepted-
outcome, safety, cost or protocol-validity thresholds against either the matched-budget Owner or the
existing evidence squad. Beating the Owner but not the squad credits distinct evidence or compute,
not RACI. The one-Owner, structural-anchor and preserved-dissent rules survive. [asserted]

A cheaper counterexample blocks activation immediately: a family/label-only C is admitted; I
authors an input; R or C authors the decision; typed dissent disappears at closure; an unrelated
actor directly releases an assignment; or any role authorises a protected effect. [asserted]

Passing EXP-107 would support supervised use only for its frozen task mixture. It would not establish
statistical independence, universal squad benefit, a gate pass, principal authority or permission to
expose another candidate. [asserted]

## Publication candidate?

**No.** The role layer is unimplemented and its incremental outcome benefit is unmeasured.
[measured] [asserted]

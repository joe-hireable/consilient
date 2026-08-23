# Corpus alignment audit — 23 August 2026

The brief's census is wrong: at the pre-report census the live tree contained **21 specifications, seven plans, 87 numbered ADR records plus three support Markdown files, 29 design documents, 56 research documents and 43 context documents**; the 22-record new ADR set is `0067`, `0068`, `0070`–`0087`, `0089` and `0091`, not `0067` plus the nonexistent `0088`/`0090` implied by `0070`–`0091`. [measured: directory census, 2026-08-23T01:50:20Z]

- **Run:** `20260823T010635-50d626e8cd`. [measured]
- **Audit time:** 2026-08-23T01:50:20Z / 02:50:20 BST. [measured]
- **Tree basis:** branch `worktree-consilience-cto`, commit `c605f6ed28c0945be283a5d371dbaddef75ade99`, plus the live uncommitted edits to `docs/superpowers/plans/2026-08-22-foundation-task-delivery-plan.md`; the other dirty paths were not treated as authored by this audit. [measured]
- **Direct verdict:** **do not dispatch the complete build programme as written.** Candidate admission/closure, write-work workspace provisioning, the specification inventory and the stale experiment-registration units require correction first; the acknowledged source-contract conflicts should be normalised before their owning units run. [asserted: findings C-01–C-10]

## Counts

| Class | Count | Consequence |
|---|---:|---|
| Contradictions | **10** | Five are live-state or launch-contract defects; four have a plan ruling but divergent source contracts; one is explicitly amended by a later ADR. [measured] |
| Ignored constraints | **3** | One activation-authority boundary, one declared-path boundary and one documentation contract. [measured] |
| Rediscoveries | **3** | One was costly and is now acknowledged in the live plan; two repeat settled research premises without citing their source documents. [measured] |
| Missing context | **4** | Each omitted source would change an experiment, implementation boundary or surface contract. [asserted] |
| Orphaned design paths | **4** | Three are v1+ paths and one is an intentionally withheld sharing path; none should be silently represented as covered. [measured] |

## Coverage and method

- A full-text mechanical pass decoded and searched all **259 pre-report Markdown files**, 65,765 lines and 4,816,126 bytes then ran exact-heading, status, filename-reference, evidence-tag and local-link scans; all 467 pre-report files below `docs/` were inventoried. [measured]
- I close-read the complete 21 specifications, seven plans, 22 new ADRs, `docs/40-spec/v0-draft.md`, `CONSILIENCE.md`, every priority design document named by the brief, `docs/10-research/findings.md`, the relevant experiment-register entries and `docs/00-context/corrections-2026-08-21.md`. [measured]
- The remaining older ADR, research and context Markdown received the full-text pass and candidate-based semantic inspection rather than an equal-depth paragraph-by-paragraph review; the 208 non-Markdown files were inventoried and sampled where a finding or cited mechanism depended on them, while bytecode and other binary artefacts were not semantically audited. [measured]
- This is a Codex-family audit of a corpus containing substantial Codex-authored work as well as Cursor-authored work; it adds corpus breadth and live measurements, but it is not an independent-family review of the Codex-authored claims. [measured] [asserted]
- The local-link scan found three pre-existing broken local links outside the new set, and `python .github/scripts/check_record_numbers.py` currently refuses five `EXP-58` headings at `docs/10-research/experiment-register.md:1528`, `:1719`, `:2438`, `:2578` and `:2715`; these are corpus-integrity failures but are excluded from the alignment counts because no audited new document created or consumes them. [measured]
- A fresh isolated projection reported human-labelled beta as `insufficient_data` with one rejected item and one false accept, and `consil doctor --json` reported Gate A fail, Gate B fail and `routing_orchestration_enabled: false`. [measured: commands run 2026-08-23]

## Verification status

- The report's 84 full path-and-line citations resolve inside the live tree, every required section is present and `git diff --check` reports no whitespace error. [measured]
- `python -m pytest tests/test_v0_invariants.py -q` passes 258 tests, `python -m mypy --strict src/consilient` reports no issue in 24 source files, `python scripts/build_requirements.py --check` matches all 36 requirements and the ADR-trail check passes while reporting its 13 pre-pin candidates. [measured]
- The full suite is **not green**: it reports 931 passed, one skipped and one failure in `tests/test_coordination.py::test_build_command_cursor_family_selection_picks_the_family`. [measured]
- That failure exercises the already-dirty model-pool change in `src/consilient/harness.py`, where automatic Kimi selection now refuses an unverified pool; this report changes only Markdown and does not repair or stage that other run's work. [measured: working-tree diff and failing assertion]

## 1. Contradictions

### C-01 — Critical: the cold-start policy converts missing beta into one admitted candidate

Task management admits one verifier-exposed candidate when authenticated human beta is unestimated, and D04 implements that as machine closure marked unreviewed. [measured: `docs/superpowers/specs/2026-08-22-task-management.md:199-211`; `docs/superpowers/plans/2026-08-22-foundation-task-delivery-plan.md:414-428`]

ADR-0077 says the robust ceiling may be zero, records that the live beta path refuses on insufficient data, and requires automatic exposure to consume a measured upper bound; the approved v0 boundary likewise permits only directly measured composite beta with an `insufficient_data` state. [measured: `docs/decisions/0077-separate-candidate-exposure-from-verifier-fusion-and-measure-both.md:21-29`, `:108-109`; `docs/40-spec/v0-draft.md:240-247`]

The build plan notices a related Done-state conflict but rules “exactly one” by assertion; an asserted organisational default is not a numeric `beta_upper`, so it cannot open a routing refusal. [measured: `docs/superpowers/plans/2026-08-22-build-plan.md:38-43`] [algebra]

**Correction before build:** freeze D04 and every automatic verifier-exposure path until either a separately authorised cold-start protocol explicitly supersedes ADR-0077 or absent beta continues to admit zero; machine closure may remain representable, but it must not be reached by an exposure the routing contract refused. [asserted]

### C-02 — High: worktree-per-run repeats a measured runtime failure

Dependency scheduling and ADR-0091 require every write dispatch to use a per-run linked worktree, and the named conformance check proves only that two Git indexes do not contend. [measured: `docs/superpowers/specs/2026-08-22-dependency-scheduling.md:152-162`; `docs/decisions/0091-check-declared-claims-against-the-import-graph-and-keep-declared-claims-authoritative.md:41-50`]

R4 had already measured Codex degrading to read-only in a linked worktree and Cursor/WSL failing to resolve its `.git` file, then required the dispatcher to choose a linked worktree, exported Git environment or full clone per runtime. [measured: `docs/20-design/dispatch-layer-requirements-2026-08-20.md:65-75`]

**Correction before build:** make “separate index and workspace” the invariant and preserve R4's runtime-dependent provisioning choices; the conformance test must exercise each admitted runtime's read, write, stage and commit path, not only `index.lock`. [asserted]

### C-03 — High: the documentation gate freezes 17 specifications while 21 exist

The master plan says 12 specifications are the current set, while the living-documentation plan freezes an exact 17-file Class-W inventory and makes an eighteenth file fail. [measured: `docs/superpowers/plans/2026-08-22-build-plan.md:19-23`; `docs/superpowers/plans/2026-08-22-memory-documentation-plan.md:377-405`, `:490-498`]

Four live specifications are absent from that inventory: `2026-08-22-answer-quality.md`, `2026-08-22-autonomous-qa.md`, `2026-08-22-dependency-scheduling.md` and `2026-08-22-one-surface.md`. [measured: `docs/superpowers/specs/2026-08-22-answer-quality.md:1`, `docs/superpowers/specs/2026-08-22-autonomous-qa.md:1`, `docs/superpowers/specs/2026-08-22-dependency-scheduling.md:1`, `docs/superpowers/specs/2026-08-22-one-surface.md:1`; directory-to-L04/L05 set difference]

These additions satisfy the plans' own amendment conditions: the master plan says a future specification needs a plan amendment, while L05 makes any unlisted new specification fail. [measured: `docs/superpowers/plans/2026-08-22-build-plan.md:19-23`; `docs/superpowers/plans/2026-08-22-memory-documentation-plan.md:398-405`] Executing L05 unchanged therefore either rejects the live corpus or institutionalises an incomplete allowlist. [asserted]

**Correction before build:** regenerate the inventory from the 21 deliberately admitted paths, review the four additions, and change the test fixture and acceptance text in the same plan amendment. [asserted]

### C-04 — High: five “absent” experiment headings now exist

The plans say EXP-104, EXP-105, EXP-110, EXP-111 and EXP-126 have no register headings, and PC00, EX00 and ML00 are units whose deliverable is to create three of them. [measured: `docs/superpowers/plans/2026-08-22-build-plan.md:49`; `docs/superpowers/plans/2026-08-22-human-self-improvement-plan.md:15-27`; `docs/superpowers/plans/2026-08-22-evidence-decision-action-plan.md:737`; `docs/superpowers/plans/2026-08-22-portability-expertise-plan.md:22-29`, `:341-367`, `:573-601`]

The live register contains EXP-110, EXP-126, EXP-105, EXP-104 and EXP-111 respectively. [measured: `docs/10-research/experiment-register.md:4167`, `:4857`, `:4960`, `:5056`, `:5309`]

The existing unit steps refuse on a collision, so this is fail-closed rather than silent duplicate creation, but the programme would stop at obsolete prerequisite work and retain false activation explanations. [measured] [asserted]

**Correction before build:** remove or convert PC00/EX00/ML00 into read-only prerequisite verification, update EXP-104/105 blockers from “unregistered” to their actual `BLOCKED` state, and re-evaluate every review-by trigger. [asserted]

### C-05 — Medium: answer quality says its ADR-0077 owner is absent

Answer quality and ADR-0087 repeatedly say ADR-0077's fusion owner is absent from the tracked tree. [measured: `docs/superpowers/specs/2026-08-22-answer-quality.md:70`, `:167`, `:353`; `docs/decisions/0087-return-one-answer-with-decision-relevant-checks.md:1-3`, `:38-40`]

ADR-0077 is present and PROVISIONAL, with an explicit exposure/fusion decision. [measured: `docs/decisions/0077-separate-candidate-exposure-from-verifier-fusion-and-measure-both.md:1-9`, `:35-50`]

**Correction before build:** replace “absent” with a live dependency on ADR-0077, while retaining ADR-0087's independent PROPOSED status because EXP-128 remains unwritten. [asserted]

### C-06–C-10 — Acknowledged contract conflicts

The build plan already names these five conflicts, which is better than silently choosing a side, but a plan-local ruling does not by itself make every source contract say the same thing. [measured: `docs/superpowers/plans/2026-08-22-build-plan.md:40-48`]

| ID | Both sides | Current disposition |
|---|---|---|
| **C-06** | ADR-0068 requires expected predecessor artefact digests before production, while task management says future bytes have no digest and binds the actual digest only at closure/claim. [measured: `docs/decisions/0068-decompose-each-request-into-the-fewest-verifiable-dependent-streams.md:164-168`; `docs/superpowers/specs/2026-08-22-task-management.md:221-226`] | The S-02 ruling is sound: freeze identity/revision/hand-off-contract digest, then bind actual artefact/verifier digests. Amend ADR-0068 or add an explicit correction pointer before T01/T02. [algebra] [asserted] |
| **C-07** | Chat correction adds `pause`, while the task-state vocabulary has no `paused`. [measured: `docs/superpowers/specs/2026-08-22-chat-conversation.md:266-289`; `docs/superpowers/specs/2026-08-22-task-management.md:148-161`] | S-03 maps pause to `blocked` with typed cause; encode that mapping in both source contracts before C03. [asserted] |
| **C-08** | ADR-0078 requires an independently granted live capability, while ADR-0075 permits one recovery-proved local/restorable mutation without another approval. [measured: `docs/decisions/0078-admit-only-gated-typed-effects-and-record-every-effect.md:43-52`, `:101-109`; `docs/decisions/0075-prove-reversibility-close-escalation-and-ratchet-friction.md:181-187`] | S-05's bounded controller-baseline interpretation must become an explicit grant kind/scope, not remain plan prose, before A02/A04. [asserted] |
| **C-09** | Action surface places `decision.autonomous` after the effect receipt, while ADR-0079 requires decision → intent → reach → receipt. [measured: `docs/superpowers/specs/2026-08-22-action-surface.md:217-226`; `docs/decisions/0079-require-a-durable-decision-before-material-actuation-and-keep-judgement-in-the-skill.md:39-47`, `:64-77`] | ADR-0079 explicitly amends the earlier order, so this contradiction is normatively resolved; annotate the stale action-surface clauses and implement ADR-0079. [measured] [asserted] |
| **C-10** | ADR-0075 closes escalation to six classes, while ADR-0076 requires exact principal approval for every active-harness byte. [measured: `docs/decisions/0075-prove-reversibility-close-escalation-and-ratchet-friction.md:88-106`; `docs/decisions/0076-owner-gates-persistent-self-change-and-the-instrument-is-sealed.md:173-181`] | S-07 treats activation as the existing `principal_authority: approval` subtype; add that cross-reference to ADR-0076 before S04 so no seventh class or agent-authored approval appears. [asserted] |

## 2. Ignored constraints

### I-01 — High: C04 schedules product behaviour governed only by PROPOSED documents

ADR-0070 is PROPOSED, says it changes no product behaviour and requires a matched chat-versus-command trial before moving beyond PROPOSED; the one-surface specification independently says it authorises no product implementation. [measured: `docs/decisions/0070-make-chat-a-compiler-to-versioned-work-item-commitments.md:1-7`, `:156-193`; `docs/superpowers/specs/2026-08-22-one-surface.md:282-290`]

C04 nevertheless schedules a behavioural local intake compiler whose Done condition sends an unprotected sentence into a start record. [measured: `docs/superpowers/plans/2026-08-22-foundation-task-delivery-plan.md:439-464`]

**Correction before build:** either obtain an accepted/superseding decision or mark C04 as an inactive experiment-only path that cannot become the default before the matched trial reports; construction permission and product activation must be separate. [asserted]

### I-02 — Medium: F05's fallback writes an undeclared path

F05 claims only `scripts/dispatch.py`, its test and its report, but its required failure branch edits `src/consilient/harness.py`. [measured: `docs/superpowers/plans/2026-08-22-foundation-task-delivery-plan.md:532-544`, `:566-578`]

ADR-0091 makes declared claims the sole write authority, and F04 already owns `harness.py`; the fallback therefore creates an unclaimed cross-lane write. [measured: `docs/decisions/0091-check-declared-claims-against-the-import-graph-and-keep-declared-claims-authoritative.md:41-49`; `docs/superpowers/plans/2026-08-22-foundation-task-delivery-plan.md:482-491`]

The current HEAD took F05's success branch, so this did not affect commit `c605f6e`; the plan remains unsafe to replay or reuse until `harness.py` is claimed and ordered, or deregistration becomes a separate unit. [measured] [asserted]

### I-03 — Medium: the corpus violates its new Class-W contract before the checker exists

The living-documentation specification defines every judgement-bearing document as Class W and requires both a falsifier and review-by date, yet only one of the 21 specifications currently contains a `Review by:` field. [measured: `docs/superpowers/specs/2026-08-22-living-documentation.md:73-83`; exact specification scan]

The build plan already admits this defect, and L04/L05 are meant to repair it; affected specifications should not be treated as admitted living inputs before that tranche is updated for all 21 files. [measured: `docs/superpowers/plans/2026-08-22-build-plan.md:52`; `docs/superpowers/plans/2026-08-22-memory-documentation-plan.md:330-405`] [asserted]

## 3. Rediscoveries

### R-01 — High, now acknowledged: Cursor Models versus Other Models

The 21 August quota document had already measured `claude-opus-5` 135, `gpt-5.6-sol` 86, `kimi-k3` 2, zero Grok and zero Composer rows, and recorded that Cursor Models means Cursor Grok/Composer while third-party models consumed Other Models. [measured: `docs/20-design/quota-pools-and-routes-2026-08-21.md:68-75`, `:128-134`]

F04 re-diagnosed the mapping from the 23 August billing surface after another day of routing, but the live plan now cites the earlier document and instructs the worker to confirm rather than re-derive it. [measured: `docs/superpowers/plans/2026-08-22-foundation-task-delivery-plan.md:493-509`]

This rediscovery is textually corrected in the current working tree; the prevention is the new prior-art step, not the repeated screenshot diagnosis. [measured] [asserted]

### R-02 — Medium: composite beta under dependence

The 20 August dependence report already established that a cheap oracle should measure the composite directly, keep marginals diagnostic and never replace the available joint measurement with a bound. [measured: `docs/10-research/composite-beta-under-dependence-2026-08-20.md:15-22`, `:90-101`]

Evidence fusion re-derives the same intersection bounds and reaches the same direct-composite rule while citing ADR-0012 but not the report that already performed the derivation and prior-art audit. [measured: `docs/superpowers/specs/2026-08-22-evidence-fusion.md:90-119`; filename-reference scan]

**Correction:** retain the short product contract, cite the 20 August report for the algebra and spend new text only on candidate-union versus verifier-intersection behaviour not already settled there. [asserted]

### R-03 — Medium: model family is not a different class of facts

The 20 August echo report already defined a different class as a truth-relevant, conditionally non-redundant source signal and explicitly rejected model-family labels and parallel worktrees as evidence classes by themselves. [asserted: `docs/10-research/formalising-echo-2026-08-20.md:284-301`, `:363-375`]

Evidence fusion independently reconstructs the same anchor rule and the same zero-credit family-label conclusion without citing that report. [asserted: `docs/superpowers/specs/2026-08-22-evidence-fusion.md:157-170`; filename-reference scan]

**Correction:** make the formal echo definition the source contract and let evidence fusion specify acquisition receipts and calibration, avoiding two definitions that can drift. [asserted]

## 4. Missing context

### M-01 — High: EXP-98 does not distinguish itself from EXP-29's topology question

ADR-0068 and EXP-98 test minimum-stream decomposition across atomic, separable and tightly coupled requests. [measured: `docs/decisions/0068-decompose-each-request-into-the-fewest-verifiable-dependent-streams.md:72-134`, `:294-312`; `docs/10-research/experiment-register.md:2167-2263`]

The earlier scope/fan-out report and EXP-29 already identify task topology and different-class yield as the moderator and preregister unitary versus evidence-separable fixtures. [cited] [asserted: `docs/10-research/unnecessary-scope-and-fanout.md:45-60`, `:79-106`, `:130-136`; `docs/10-research/experiment-register.md:805-860`]

Citing and reusing EXP-29 would force EXP-98 to state its actual delta—request-to-dependent-stream organisation and integration coherence rather than candidate fan-out—and would avoid rebuilding topology labels and fixtures. [asserted]

### M-02 — Medium: portable capability work omits the existing “inherit or adopt, build none” boundary

The context-loading and capability-layer designs say delegated runtimes inherit native tool search, while only a native/open-model path may adopt one commoditised retrieval layer; neither path should rebuild discovery. [measured: `docs/20-design/context-loading.md:22-30`; `docs/20-design/capability-layer.md:70-89`]

Portable capability correctly reuses `capabilities.py`, `instructions.py` and per-harness bindings, but neither the specification nor its plan cites those boundary documents. [measured: `docs/superpowers/specs/2026-08-22-portable-capability.md:86-110`, `:162-185`; `docs/superpowers/plans/2026-08-22-portability-expertise-plan.md:58-139`; filename-reference scan]

The missing citation should narrow the implementation contract: task selection and run-local binding are in scope; first-party delegated-tool search, retrieval ranking and global capability installation are not. [asserted]

### M-03 — Medium: non-coding reach lacks Q24's oracle-latency contract

Q24 says non-coding decisions require an attributable exogenous oracle, per-domain latency and an `unverified` state until that oracle arrives; some domains may have no admissible oracle. [asserted: `docs/20-design/q24-oracle-latency-2026-08-20.md:61-70`, `:77-104`]

One-surface discusses absorbing general knowledge, design, office and scheduled/project work but assesses the surface mainly through accepted completion and attention cost, without binding those domains to Q24. [asserted: `docs/superpowers/specs/2026-08-22-one-surface.md:250-263`, `:282-290`; filename-reference scan]

Adding Q24 would narrow every non-coding claim to a named oracle/latency/attribution contract and keep outputs visibly unverified where no such oracle exists. [asserted]

### M-04 — Low: the new observability surface omits the accepted surface ADR

ADR-0053 already authorises exactly one local file-based `consil dashboard`, requires it to render rather than decide and preserves the ban on a server or review surface. [measured: `docs/decisions/0053-build-one-local-observability-surface-that-renders-the-record.md:46-79`]

Observability and steering reaches a compatible “one local live projection” and reuses `dashboard.py`, but does not cite ADR-0053. [measured: `docs/superpowers/specs/2026-08-22-observability-and-steering.md:19-32`, `:208-236`; filename-reference scan]

The citation would make “same projector, no server, never decides” a consumed accepted constraint rather than a coincidental restatement and would prevent a later live client becoming a second surface. [asserted]

## 5. Orphaned design paths

### O-01 — Work modes beyond chat/task

The design defines six modes—Chat, Project, Task, Scheduled, Background and Parallel background—and gates unattended modes on measured beta, critic recall, review capacity and Q24. [asserted: `docs/20-design/work-modes.md:11-23`, `:54-78`]

The new corpus specifies chat/task delivery and says “run in the background”, but it contains no complete Project, Scheduled or Parallel-background contract, attention budget or mode-admission plan. [measured: `docs/superpowers/specs/2026-08-22-chat-delivery.md:335-348`; whole-new-corpus term scan]

This is a plan gap, not authority to implement the missing modes; record them as deliberately deferred or add future units only after their existing gates pass. [asserted]

### O-02 — Inquiry-tier escalation

The inquiry design defines T0 assert, T1 ground, T2 executable model and T3 measurement, with reversibility, blast radius, prior dispersion and formalisability gates. [asserted: `docs/20-design/inquiry-tier.md:26-61`, `:70-89`]

The new decision and consilience protocols define consequence/evidence gates but never preserve this four-tier escalation or its executable-model artefact contract. [measured: `docs/superpowers/specs/2026-08-22-decision-protocol.md:98-178`; `docs/superpowers/specs/2026-08-22-consilience-gate.md:112-187`; whole-new-corpus term scan]

The programme must either name inquiry tier as intentionally cut/superseded or assign its decision-to-experiment path; a different consequence gate is not silent coverage. [asserted]

### O-03 — Reasoning-layer enforcement

The reasoning design requires a tri-state per-model/per-task dispatch and refuses prompt scaffolding when native reasoning is present, while explicitly reusing existing registries. [cited] [asserted: `docs/20-design/reasoning-layer.md:7-19`, `:21-36`, `:92-112`]

Model lifecycle records a reasoning posture and the foundation plan fails closed on `reasoning: unknown`, but no unit enforces the task-class decision or the “do not stack scaffolds” rule. [measured: `docs/superpowers/specs/2026-08-22-model-lifecycle.md:29-32`, `:148-185`; `docs/superpowers/plans/2026-08-22-foundation-task-delivery-plan.md:513-523`]

This is partial schema coverage, not implementation coverage; record the behavioural layer as deferred rather than implying model lifecycle completes it. [asserted]

### O-04 — Consented trajectory sharing

The sharing design specifies principal-authored grant/withdrawal, purpose `improve-consilient`, retention, preview/export byte identity, redaction checks and a deliberately withheld exporter. [asserted: `docs/20-design/trajectory-sharing-consent-2026-08-21.md:1-5`, `:120-178`, `:272-300`]

The new specs and plans cover consent for training, capabilities and protected actions but contain no trajectory-sharing grant, withdrawal, retention or exporter path. [measured: whole-new-corpus exact-term scan]

That omission is safe today because the existing design forbids the pipeline until its checks exist, but it is still an uncovered product path and should be recorded as intentionally deferred. [asserted]

## 6. Areas that are well aligned

- The plans preserve `routing_orchestration_enabled: false`, keep Gate A and Gate B unchanged and reject a seventh `consil` command. [measured: `docs/superpowers/plans/2026-08-22-build-plan.md:25-32`; corroborated across all seven plans]
- The plans preserve the `src/consilient/` AST boundary and keep subprocess, network, credentials and third-party execution in outer scripts or fake/refusal-only fixtures. [measured: `docs/superpowers/plans/2026-08-22-evidence-decision-action-plan.md:19-25`; `docs/superpowers/plans/2026-08-22-portability-expertise-plan.md:9-15`, `:823`; `docs/superpowers/plans/2026-08-22-squads-observability-plan.md:277`]
- The new work consistently reuses `events.py`, `work_items.py`, `coordination.py`, `recall.py`, `capabilities.py`, `instructions.py`, `routing.py`, `budget.py` and `dispatch.py`; it does not propose a second authoritative event writer, task database, router or orchestrator. [measured: `docs/superpowers/specs/2026-08-22-memory-and-capability.md:40-50`, `:205-211`; `docs/superpowers/specs/2026-08-22-portable-capability.md:86-110`; `docs/superpowers/plans/2026-08-22-build-plan.md:149`]
- Principal authority is structurally separated from machine closure: unverified feedback is excluded from beta, protected actions remain first-party, and agent roles do not acquire approval power. [measured: `docs/superpowers/specs/2026-08-22-task-management.md:257-302`; `docs/superpowers/specs/2026-08-22-verdict-supply.md:16-34`, `:234-280`; `docs/superpowers/plans/2026-08-22-build-plan.md:97-101`, `:142-145`]
- Refusals, timeouts, quarantines, missing artefacts, dissent and absent verdicts remain explicit rather than being dropped from outcomes or denominators. [measured: `docs/superpowers/plans/2026-08-22-build-plan.md:30-33`; `docs/superpowers/specs/2026-08-22-task-management.md:150-178`, `:318-352`]

## 7. Minimum correction set

1. Keep absent human beta as zero automatic exposure unless a separately authorised cold-start protocol explicitly supersedes ADR-0077; amend S-01, D04 and the Done predicate together. [asserted]
2. Replace “linked worktree for every writer” with a runtime-conformant isolated workspace contract and test all admitted runtimes through write, stage and commit. [asserted]
3. Refresh every live inventory and experiment prerequisite: 21 specs, five now-present experiment headings, and ADR-0077 present; remove or convert obsolete preregistration units. [measured] [asserted]
4. Turn S-02, S-03, S-05 and S-07 from plan-local rulings into explicit source amendments/cross-references; annotate C-09's already-valid ADR-0079 supersession. [asserted]
5. Separate C04 construction from activation, repair F05's claim set, and complete the Class-W metadata/inventory tranche before treating these documents as admitted build inputs. [asserted]

After those corrections, the local/refusal-only event, projection, bounded-memory and explicit/manual capability slices are consistent enough to re-audit unit by unit; this report does not pass Gate A, Gate B, routing, product activation or publication. [asserted]

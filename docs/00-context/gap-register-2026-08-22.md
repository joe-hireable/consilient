# Competitive sufficiency gap register — 22 August 2026

Correction: EXP-118 now has a late, explicitly `BLOCKED` register entry; it was not pre-registered before the teardown said that it was, and no EXP-118 result exists. `[measured: experiment-register.md, EXP-118; hermes-teardown-2026-08-22.md, "The comparison and the mechanism"]` This is a **single-family audit with zero independent cross-family readings per finding**; rerun it with a genuinely different model family before treating the register as independent confirmation. `[measured][asserted]`

**Audit stamp:** 2026-08-22T17:34:49+01:00. `[measured]`

**Scope:** all seventeen files in `docs/superpowers/specs/`, ADR-0067 and ADR-0070–ADR-0086, all seven files in `docs/superpowers/plans/`, and the four incumbent reviews named in the dispatch brief were inspected. `[measured]`

**Citation convention:** a short name such as `decision-protocol.md` denotes `docs/superpowers/specs/2026-08-22-decision-protocol.md`; a short plan name denotes the corresponding `docs/superpowers/plans/2026-08-22-*-plan.md`; `ADR-NNNN` denotes its file in `docs/decisions/`. `[measured]`

**Evidence boundary:** no head-to-head result artefact exists for EXP-118, and no permitted evidence contains a measured total ordering of ChatGPT Work, Hermes and Ruflo. `[measured: hermes-teardown-2026-08-22.md, "Head-to-head criteria" and "The comparison and the mechanism"; product-bar-2026-08-22.md, "Method and evidence boundary"; ruflo-teardown-2026-08-22.md, "Threats to validity"]`

### Fixed audited population

The working tree was dirty and changed during the audit, so “seventeen” means these exact working-tree blobs captured while repository HEAD was `6cd6c940d4e9ff62f9f2a8d2235b439149f6b2a0`: `action-surface` `f7044d4ae0d4d57d7f03a9ff15486c227b403e9e`, `autonomy-and-friction` `dee8848ea11aaf4aa546227d6bc1b691ac4441b9`, `chat-conversation` `e5d5e5301af2da4a0979308c475b941db2003926`, `chat-delivery` `44ec815d9339328366ea0e4795bd20ee98a934b1`, `consilience-gate` `708736f76bb737e25291b240293304f5920573f8`, `decision-protocol` `bbf4cfe7d2997c44479d882fe224d630cf391cd0`, `evidence-fusion` `070dc581c1615233ae121b7691663cbfa9dffb24`, `expertise-acquisition` `a16aa796eca81ef2b086cd63306119a8a0a862bf`, `living-documentation` `66a91db2438af5ed45ad01a8ee8aaa626d58b338`, `memory-and-capability` `54ee4b7b94369d494ce5b3b999af71006edf98cf`, `model-lifecycle` `26bdac3e3c8623ad5f6359c60b30b74a8e433a1a`, `observability-and-steering` `8125ac29bb831f3d598fa9c0fe95cebaaf8d660c`, `portable-capability` `5471bcfe9b7c080cf0aa9acf735d19700cfe0ada`, `self-improvement` `903dee5e933852666eb065b3e04bb5ada89ba799`, `squad-roles` `bacf9da384c491e93befd97dc1483398e7076dbc`, `task-management` `6f09f13f2543d0a6967a9825c844dcab730aa10d`, and `verdict-supply` `48851185672dea81ac07d37bf41ce4b3a1758df7`; every short name expands under `docs/superpowers/specs/2026-08-22-*.md`, and every digest is a `git hash-object` blob identity. `[measured]` HEAD moved again during validation while all seventeen blob identities remained unchanged, so the blobs—not the moving branch tip—define the population. `[measured]`

A separate run claimed `2026-08-22-answer-quality.md` 35 seconds after this dispatch opened, and its untracked file appeared while this report was being validated; it is not one of the mandated seventeen blobs. `[measured: trajectory events for runs 20260822T162010-0d04fcc3c9 and 20260822T162045-1b18d15367]` Its own §§1 and 6 say that the response policy is not a demonstrated quality advantage and that proposed EXP-128 is absent from the register, so including it would change confirmed gap 3 from “no specification” to “new specification, no registered or run proof”, without changing the final verdict. `[measured: answer-quality.md §§1 and 6]`

Three delegated read-only passes separately inspected incumbent evidence, the seventeen specifications, and the ADR/plan/register chain; two same-family adversarial passes then checked the synthesis. `[measured]` Those are independent work assignments and partially disjoint source classes, not independent model-family truth; the cross-family count remains zero for every finding. `[asserted]`

## Direct verdict

**No. Perfectly implementing all seventeen audited specifications tomorrow would not make Consilient the demonstrated best product in the world at any user outcome.** It would create a comparatively rigorous set of mechanisms for evidence provenance, bounded delegation, adverse-outcome accounting and principal authority, but it would still be gated off, uncalibrated against human truth, untested against the named products, and missing a whole-product quality, reach, reliability and economics contract. `[measured: fixed seventeen-specification population; consil doctor --json during this audit; experiment-register.md, EXP-118]`

The strongest surviving proposition is narrower: Consilient could become unusually good at **joined proof**—showing accepted outcome, terminal acceptance error, structurally distinct or exogenous evidence anchors with dependence kept visible, authenticated authority and full cost in the same record. `[asserted]` Structural difference is not statistical independence, which remains measured, declared or unknown rather than inferred. `[measured: evidence-fusion.md §§4–5; consilience-gate.md §1]` No inspected artefact proves that this joined protocol is already world-leading, and none proves that users prefer its answers or that its discipline repays its overhead. `[measured: product-bar-2026-08-22.md, "The candidate gaps, tested rather than assumed"; the seventeen specifications]`

## The incumbent is axis-specific, not resolved to one product

| Axis | Defensible incumbent at the audit stamp | Margin and limit |
|---|---|---|
| General usable product breadth | ChatGPT Work is the product-bar review's medium-confidence leader; OpenAI documents long-running work, files, apps, schedules and cross-device continuation. `[asserted][cited: product-bar-2026-08-22.md, "Products a person can use now"; OpenAI, "ChatGPT Work and Codex" and "Workspace Agents"]` | No independently measured accepted-outcome, reliability or acceptance-error margin was found. `[measured: product-bar-2026-08-22.md, "Decision, ranked by consequence"]` |
| Durable delegated coordination | Hermes leads the inspected implementation comparison through its transactional SQLite board, claiming and crash recovery. `[cited: hermes-teardown-2026-08-22.md, "Kanban: a real board, separate from delegation"; Hermes Kanban documentation]` | No matched kill/restart outcome margin exists. `[measured: hermes-teardown-2026-08-22.md, "Head-to-head criteria"]` |
| Cross-vendor meta-harness structure | Ruflo is the closer structural comparator because it has Claude/Codex orchestration and cross-process persistent memory. `[asserted][cited: ruflo-teardown-2026-08-22.md, "The genuine dual-mode meta-harness" and "Local persistence proof"]` | Its vendor GAIA record and flywheel do not establish a general outcome or reliability lead, and live dual operation was not reproduced locally. `[cited][measured: ruflo-teardown-2026-08-22.md, "Correctness measurement and β" and "Threats to validity"]` |
| Acceptance error, human authority and outcome-normalised efficiency | **Unresolved.** No inspected product clears these axes with comparable evidence. `[measured: hermes-teardown-2026-08-22.md, "Head-to-head criteria"; product-bar-2026-08-22.md, "Testable criteria for a credible ‘best’ claim"; ruflo-teardown-2026-08-22.md, "What it does not measure"]` | The margin is unknown on every axis. `[measured]` |

There is therefore no supported ordering such as `ChatGPT Work > Hermes > Ruflo` or `Ruflo > Hermes > ChatGPT Work`. `[measured]` The usable bar is a vector: Work for breadth, Hermes for inspected coordination, Ruflo for cross-harness structure, and no incumbent yet established for the joined proof Consilient proposes. `[asserted]`

The frozen Ruflo teardown is already partly stale: it inspected release 3.38.16 at revision `5234333`, while `main` had moved to release 3.38.18 at revision `127a654` by this audit; the intervening changes include Windows installation and dependency repairs relevant to two reproducibility findings, but do not supply atomic task claims, one accountable Owner or a terminal acceptance-error table. `[cited: ruflo-teardown-2026-08-22.md, "Reproducibility, tests and known failure modes"; public comparison 5234333...127a654, retrieved 2026-08-22]`

## CONFIRMED gaps, ranked by damage to “best globally”

### 1. There is no global outcome contest

Eight specifications promise component gains against different local controls, but none compares the composed product with ChatGPT Work, Hermes and Ruflo on one frozen task mixture. `[measured: decision-protocol.md §2; evidence-fusion.md §3; expertise-acquisition.md §§1–2; memory-and-capability.md §3; model-lifecycle.md opening decision; self-improvement.md §1; squad-roles.md §9; task-management.md §10]` EXP-118 compares only Hermes with one Consilient configuration, is blocked, has no execution plan, and has not run. `[measured: experiment-register.md, EXP-118; all seven plans]`

**Cost to the claim:** fatal; component wins cannot establish a whole-product or global win. `[asserted]`

### 2. The specified product remains unreachable

The chat, delivery, task, observability and action specifications define separate mechanisms, but no specification composes them into one installable, reachable, non-technical operator product. `[measured: chat-conversation.md §§1 and 6; chat-delivery.md §§1 and 6; task-management.md §§3–7; observability-and-steering.md §§3–7; action-surface.md §§1 and 5]` During this audit, Gate A and Gate B failed and `routing_orchestration_enabled` was `false`; the product code remains observe-only and the plans preserve those boundaries. `[measured: consil doctor --json during this audit; build-plan.md, "Global constraints"]`

**Cost to the claim:** fatal for a product claim; a person cannot prefer or benefit from a surface they cannot reach. `[asserted]`

### 3. The fixed seventeen-file population does not target visibly better answers or perceived impact

Chat conversation measures turns and principal attention, chat delivery says trust with less attention is unmeasured, and observability expressly declines visual design. `[measured: chat-conversation.md §2; chat-delivery.md §2; observability-and-steering.md opening scope and §4]` None of the fixed seventeen measures blind user preference, helpfulness, insight, coherence, task impact or adoption against an incumbent; the concurrent answer-quality specification now proposes that missing comparison but has no registered or run EXP-128. `[measured: fixed seventeen specifications; answer-quality.md §§1 and 6]`

**Cost to the claim:** fatal for the requested “magic and impact”; better governance is not evidence of a better answer. `[asserted]`

### 4. Acceptance error remains unestimated

The live beta artefact contains one caller-declared rejection classified as a false accept, with six quarantined records and no interval or point estimate; because caller-supplied principal identity is unauthenticated, it supplies **zero authenticated human-labelled rejections**, while EXP-118 requires thirty rejected artefacts per arm. `[measured: consil beta --json during this audit; task-management.md opening correction; verdict-supply.md §5, "First-party authorship is the floor"; experiment-register.md, EXP-118]` Verdict supply specifies how to obtain authenticated labels and several specifications impose non-regression, but none supplies the independent deliberately-flawed calibration bank required to show a terminal false-accept upper bound below one per cent. `[measured: verdict-supply.md §§1, 5 and 6; product-bar-2026-08-22.md, criterion 3]`

**Cost to the claim:** fatal to the project’s truth-testing distinction until measured. `[asserted]`

### 5. Whole-product cost and latency have no competitive contract

Model lifecycle records a cost vector, and several component specifications require cost non-regression, but no specification joins provider-equivalent spend, tool/worker time, operator/review minutes, completion latency and accepted outcome for the composed product. `[measured: model-lifecycle.md §7; memory-and-capability.md §9; evidence-fusion.md §10; self-improvement.md §1; squad-roles.md §9]` EXP-118 permits both spend and human minutes to reach `1.25×` Hermes, whereas the broader product-bar proposal requires the upper 95% paired-bootstrap interval to be at most `1.05×` separately for spend and review; a passing EXP-118 arm could therefore be materially dearer on both recorded dimensions. `[measured][algebra: experiment-register.md, EXP-118; product-bar-2026-08-22.md, criterion 7]`

**Cost to the claim:** fatal to economic superiority and a major threat to adoption. `[asserted]`

### 6. Principal authority is specified but not yet authenticated end to end

Action surface, autonomy, verdict supply and self-improvement define strong boundaries, and ADR-0080 selects a user-verification-required WebAuthn ceremony. `[measured: action-surface.md §6; autonomy-and-friction.md §5; verdict-supply.md §5, "First-party authorship is the floor"; self-improvement.md §§3–5; ADR-0080, "Decision"]` The audited WebAuthn dependency or OS-isolated broker and the private HTTPS relying-party origin/network exposure remain unapproved, unimplemented and untested. `[measured: ADR-0080, "Enforcement"]` The fixed specifications contain no completed reserved-action attack, false-refusal, enrolment, recovery or revocation result; extending that campaign across every supported ingress is a missing scope recommended by this audit. `[measured: the seventeen specifications; product-bar-2026-08-22.md, criterion 6; hermes-teardown-2026-08-22.md, "Head-to-head criteria"][asserted]`

**Cost to the claim:** fatal to a safe-autonomy lead; a structural intention is not authenticated authority. `[asserted]`

### 7. Generality across domains is untested

EXP-118 freezes coding tasks, while the global product bar separately requires floors across professional artefacts, software, browser/desktop work, research, governed actions and recurring work. `[measured: experiment-register.md, EXP-118; product-bar-2026-08-22.md, criterion 2]` No specification owns that domain matrix or a no-hidden-domain-loss rule. `[measured: all seventeen specifications]`

**Cost to the claim:** fatal to the word “globally”; success on one coding mixture cannot establish general superintelligence. `[asserted]`

### 8. Reliability is componentised, not composed

Chat delivery specifies checkpoints and restart, action surface specifies effect receipts, task management specifies claim and dependency recovery, and self-improvement specifies rollback. `[measured: chat-delivery.md §§4–6; action-surface.md §5; task-management.md §§5–6 and 10; self-improvement.md §§4–5]` No specification sets an end-to-end availability, deadline-completion, power-loss, storage-corruption, transport-loss or full-request recovery SLO; chat delivery explicitly excludes sudden power loss and storage corruption. `[measured: chat-delivery.md §5; all seventeen specifications]`

**Cost to the claim:** prevents a reliability lead even if each component passes its isolated checks. `[asserted]`

### 9. Cross-harness persistence and subscription reach are parity work

Ruflo’s two-process proof falsified broad novelty for durable cross-harness memory, and Hermes source and documentation support handing a complete turn to the Codex app-server runtime using a ChatGPT subscription; no receipt-measured delegated turn was inspected. `[cited: ruflo-teardown-2026-08-22.md, "Local persistence proof"; subscription-reach-2026-08-22.md, "Hermes — Sense A: subscription quota"]` Portable capability tests bounded Claude/Codex equivalence for one package and explicitly refuses a broad claim; it does not test Cursor, Grok, incumbent import/export or task outcome. `[measured: portable-capability.md §§2 and 11]`

**Cost to the claim:** removes two proposed differentiators and leaves connector breadth behind shipped products. `[asserted]`

### 10. Learning is fragmented into four separate contests

Capability reuse, model revision, persistent self-change and expertise assignment are governed separately by EXP-101, EXP-111, EXP-104 and EXP-126. `[measured: memory-and-capability.md §9; model-lifecycle.md §8; self-improvement.md §§1–5; expertise-acquisition.md §§5–10]` No specification uses one frozen workload and budget to decide which learning surface produces the best held-out accepted-outcome gain without regression. `[measured: all seventeen specifications]`

**Cost to the claim:** prevents a product-level learning advantage even if one local mechanism works. `[asserted]`

### 11. Reproducibility and incumbent drift are outside the product contract

Living documentation detects some local contradictions and model lifecycle checks revision drift, but no specification freezes external product versions, retains every adverse trial and refreshes the incumbent comparison quarterly. `[measured: living-documentation.md §§3–6; model-lifecycle.md §§4 and 8; product-bar-2026-08-22.md, criterion 8]` Ruflo changed twice between its teardown and this audit, demonstrating that this is an active failure mode rather than a theoretical nicety. `[cited: public comparison 5234333...127a654, retrieved 2026-08-22]`

**Cost to the claim:** any lead could expire without being noticed. `[asserted]`

### 12. The plans do not deliver the registered comparisons reliably

No plan mentions or executes EXP-118. `[measured: all seven plans]` Several plans also call EXP-104, EXP-105, EXP-110, EXP-111 or EXP-126 “absent” even though the live register contains each as `BLOCKED`, and the umbrella build plan stops at ADR-0081 and omits the two newest plans. `[measured: build-plan.md; evidence-decision-action-plan.md; human-self-improvement-plan.md; portability-expertise-plan.md; experiment-register.md]`

**Cost to the claim:** a perfect implementation plan can finish while the decisive evidence is still absent or duplicated incorrectly. `[asserted]`

### Cheapest observations that would remove or downgrade each confirmed gap

Every confirmed finding has zero independent cross-family readings; these are the smallest decisive observations, not claims that the observations already exist. `[asserted]`

| Rank | Cheapest falsifying observation |
|---|---|
| 1 | A prospectively registered, blinded global contest reports the required positive lower bound against every product and specialist comparator. `[asserted]` |
| 2 | A clean-install, non-technical submit/interrupt/resume/recover trial completes through one reachable surface while the authoritative gates permit the arm. `[asserted]` |
| 3 | Registered EXP-128 or its global-contest equivalent reports a positive blind-preference and task-impact result without correctness loss. `[asserted]` |
| 4 | An independent deliberately-flawed bank supplies at least 300 terminal labels and a one-sided false-accept upper bound below 1%. `[asserted]` |
| 5 | A matched whole-product run reports the upper 95% paired-bootstrap interval at or below `1.05×` separately for spend and review, with accepted outcome as denominator. `[asserted]` |
| 6 | The implemented WebAuthn ingress records zero protected false authorisations across at least 300 attempts against each reserved action class and reports false refusals. `[asserted]` |
| 7 | The frozen multi-domain contest clears every predeclared product and specialist floor. `[asserted]` |
| 8 | A composed fault-injection run clears accepted-and-on-time SLOs across kill, restart, power, storage, transport and quota faults. `[asserted]` |
| 9 | A receipt-bearing task run shows outcome-preserving capability and subscription use across every claimed harness, not merely format conformance. `[asserted]` |
| 10 | One matched-budget learning contest selects a surface with a positive held-out outcome bound and no alpha, beta, cost or stale-data regression. `[asserted]` |
| 11 | A fresh-machine reproduction at the moved incumbent revisions passes, and an automated refresh demonstrably downgrades a deliberately stale claim. `[asserted]` |
| 12 | A plan dry-run resolves every live experiment heading exactly once and produces a dispatchable EXP-118 work path without inventing or duplicating a registration. `[asserted]` |

## SUSPECTED gaps

These are risks supported by structure or incomplete evidence, not observed comparative results. `[asserted]`

1. **Consilient is likely to be slower and dearer per accepted artefact unless its error reduction or outcome lift repays the extra reads, gates, records and human review.** `[asserted]` No matched result supports a direction or margin, so “will be slower and dearer” must not be upgraded to measured. `[measured: no EXP-118 result; no whole-product cost artefact]`
2. **A quiet, evidence-heavy interface may feel less capable than streamed incumbent products even when it is safer.** `[asserted]` Chat delivery itself records streaming as the strongest alternative and requires a matched trial. `[measured: chat-delivery.md §9]`
3. **The two-anchor high-consequence gate may refuse correct actions supported by one authoritative source.** `[asserted]` ADR-0081 records this objection, and EXP-109 has not resolved it. `[measured: ADR-0081, "Consequences" and experiment-register.md, EXP-109]`
4. **The current refusal may sacrifice useful search before beta is sufficiently measured to admit even one live candidate.** `[asserted]` ADR-0077 makes live routing refuse when human beta is unestimated; the one-candidate value comes from the mutation-proxy/cold-start ceiling and is not permission to substitute that proxy for authenticated human beta. `[measured][algebra: ADR-0077, "Evidence"; task-management.md opening correction; consil beta --json during this audit]` No outcome experiment quantifies the opportunity cost of the refusal. `[measured]`
5. **A user may value broad connector availability, installation ease and cross-device polish more than audit depth.** `[asserted]` Neither the fixed seventeen nor the concurrent answer-quality specification contains a completed adoption or blind-preference result that can settle that trade-off. `[measured]`

## EXP-118 criterion-by-criterion register

The seven criterion names below reproduce the Hermes teardown exactly. `[measured: hermes-teardown-2026-08-22.md, "Head-to-head criteria"]`

| Criterion | Leader today and measured margin | Specification that would contest it | Lead, parity or neither if delivered exactly | Missing decision, specification or experiment |
|---|---|---|---|---|
| **Reachable product** | Hermes leads the frozen Hermes comparison by availability; ChatGPT Work leads broader usable breadth by an asserted product review. The proposed twenty-task comparison has not run, so the margin is unknown. `[asserted][measured]` | Chat conversation §§1, 4 and 6; chat delivery §§1, 4–6; task management §§3–7; observability and steering §§3–7; action surface §§1 and 5. `[measured]` | **Neither.** These mechanisms do not lift Gate A or B, enable routing, define installation/onboarding, or compose one reachable surface. `[measured]` | A whole-product composition and reach specification; gate evidence; an installed-product submit/interrupt/resume/recover comparison. `[asserted]` |
| **Accepted task outcome** | No measured leader. Hermes is operational; Work is the asserted breadth leader; Ruflo’s vendor artefact reports 31/53 GAIA Level-1 passes but is not comparable or independently reproduced. The EXP-118 margin is unknown. `[cited][measured]` | Decision protocol §2; evidence fusion §3; expertise acquisition §§1–2 and 5; memory and capability §§3 and 9; model lifecycle opening and §8; self-improvement §1; squad roles §9; task management §10. `[measured]` | **Possible component lead only.** Each uses a different local comparator; none establishes a global whole-product lead. `[measured]` | A global outcome specification, frozen multi-domain bank, blind independent judging, Work/Hermes/Ruflo arms, specialist floor arms for Cursor, Copilot Cowork and OpenClaw, and an EXP-118 execution plan. `[asserted]` |
| **Acceptance error** | Unknown for every incumbent. Hermes publishes no calibrated terminal error; Ruflo exposes no machine-accept × independent-truth table; Work has no comparable public confusion matrix. Consilient has one caller-declared rejection but **zero authenticated human-labelled rejections** toward the required thirty. `[measured]` | Verdict supply §§1, 3–6; consilience gate §§3–10; evidence fusion §§5–6; model lifecycle §4; memory and capability §§3 and 9. `[measured]` | **Measurement capability and non-regression, not a lead.** `[measured]` | An independent ≥300 deliberately-flawed calibration bank with a one-sided upper bound below 1%, followed by the paired EXP-118 error comparison. `[asserted: product-bar-2026-08-22.md, criterion 3]` |
| **Human authority** | No inspected product clears the proposed standard. Work documents roles and write confirmation but no adversarial authorship proof; Hermes permits machine review; Ruflo has no single accountable Owner. The margin is unknown. `[cited][measured]` | Action surface §6; autonomy and friction §5; verdict supply §5; self-improvement §§3–5; ADR-0080. `[measured]` | **Unproven parity at best.** The WebAuthn ceremony is selected, but no approved verifier boundary/origin or attack result establishes a lead. `[asserted][measured]` | Approve and implement trusted ingress; specify enrolment, recovery, revocation and channel binding; run ≥300 attempts against each reserved action class spanning prompt injection, non-owner invocation, replay and confused-deputy attacks, with zero protected false authorisations and reported false refusals. `[asserted: product-bar-2026-08-22.md, criterion 6; hermes-teardown-2026-08-22.md, "Head-to-head criteria"]` |
| **Durable coordination** | Hermes leads the inspected implementation with transactional SQLite claiming and crash recovery; the numeric outcome margin is unknown. Ruflo’s principal task/claim stores are non-atomic JSON. `[cited][measured]` | Task management §§3–6 and 10; chat delivery §§4–6; action surface §5; observability and steering §§5–7. `[measured]` | **Feature parity, with a possible local-control lead after EXP-98.** EXP-98 compares against one capable Owner, not Hermes. `[measured]` | A matched kill/restart/power-loss contest against Hermes, including duplicate work, lost claims, accepted-and-on-time completion, human recovery time and full adverse counts. `[asserted]` |
| **Learning without regression** | No measured outcome leader. Ruflo has a substantive inspected evaluation mechanism; Hermes persists learned skills and Work persists memory, but no comparable held-out outcome lift exists. `[cited][measured]` | Expertise acquisition §§5–10; memory and capability §§3 and 9; model lifecycle §§4 and 8; self-improvement §§1–5. `[measured]` | **A plausible component lead, not a product lead.** The four contests are separate and blocked. `[asserted][measured]` | One matched-budget learning contest across the four surfaces, with held-out outcome lift, alpha/beta/cost bounds, stale-data challenges and rollback. `[asserted]` |
| **Extra cost** | No efficiency leader. Hermes is available, while Work, Hermes and Ruflo lack comparable provider-cost-plus-human-time per accepted outcome. The margin is unknown. `[measured]` | Model lifecycle §§4 and 7–8; memory and capability §9; evidence fusion §10; self-improvement §1; squad roles §9. `[measured]` | **Neither.** Instrumentation and component non-regression do not establish whole-product efficiency; EXP-118 allows 1.25× Hermes. `[measured]` | A common whole-product cost/latency specification and result, using accepted outcomes as denominator, missing usage as adverse, zero success as infinite cost, and an upper 95% paired-bootstrap interval ≤1.05× rather than a raw 1.25× ceiling, separately for spend and review. `[asserted]` |

## Criteria the seven omit

| Omitted field criterion | Current position | Specification coverage | Gap |
|---|---|---|---|
| **Blind user preference, answer quality and impact** | No leader or margin was established in the permitted evidence. `[measured]` | None of the fixed seventeen; the concurrent answer-quality specification proposes EXP-128, but it is unregistered and unrun. `[measured]` | Add its blind preference and task-impact outcomes to the prospectively registered global contest. `[asserted]` |
| **No hidden domain loss** | Work has the strongest asserted general breadth; no comparable domain-floor result exists. `[asserted][measured]` | None owns the six-domain matrix. `[measured]` | Predeclare domain floors and make any material domain regression a loss. `[asserted]` |
| **Reliable completion by deadline** | Unknown; shipped reach and crash recovery are not accepted-and-on-time completion. `[measured]` | Chat delivery covers estimates/checkpoints; task management covers claims; neither composes an SLO. `[measured]` | Measure p50/p95 completion, abandonments, quota exhaustion, refusals, quarantines, interventions and recovery. `[asserted]` |
| **Connector, subscription and interoperability reach** | Work/Claude have broader managed catalogues; Hermes has arbitrary MCP reach and source-supported Codex subscription use; Ruflo has structural Claude/Codex support. `[cited: subscription-reach-2026-08-22.md]` | Portable capability §11 tests one package on Claude/Codex only. `[measured]` | Add task-scoped connector/subscription conformance, import/export and outcome testing across supported harnesses. `[asserted]` |
| **Privacy and security beyond authorship** | No unified comparative result exists for prompt injection, secret disclosure, sandbox escape, non-owner access or destructive effects. `[measured]` | Action surface and authority specs cover some effects, not one adversarial product criterion. `[measured]` | Add a threat-modelled adversarial campaign and false-refusal burden to the release gate. `[asserted]` |
| **Reproducibility and drift** | No inspected product lead; the moving Ruflo baseline already changed during the audit day. `[cited][measured]` | Living documentation and model lifecycle cover internal drift only. `[measured]` | Freeze versions/configuration, retain adverse trials and rerun the bar at least quarterly. `[asserted]` |
| **Installation, onboarding and accessibility** | Shipped products lead by availability; no measured margin exists. `[asserted][measured]` | None owns setup completion, account/session recovery, cross-device continuation, notification delivery or accessibility. `[measured]` | Add an operator-access specification and test with non-technical participants. `[asserted]` |

## Exhaustive seventeen-specification audit

Passing a component comparator is marked **lead** only on that named component; it is not promoted to a world-product claim. `[asserted]` Every numeric or “beats” clause in the middle column is an asserted prospective contract found in the specification, not an observed result; `[measured: specification text]` attests only that the text contains the contract. `[measured][asserted]`

| Specification and decisive sections | Prospective requirement found in the text | Competitive sufficiency finding |
|---|---|---|
| **Action surface**, §§1, 5, 6 and 8 | The specification requires typed constrained actuation, a complete effect record and structural authority bounds, and says its effect-level delta is not demonstrated. `[measured: specification text]` | Mechanism only; no comparative product outcome, reach or authority result. `[measured]` |
| **Autonomy and friction**, §§1, 5, 7 and 8 | The specification requires fewer avoidable escalations with non-inferior human outcome against a local baseline. `[measured: specification text]` | Component-lead contract on friction only; no provider-cost or global outcome contest. `[measured]` |
| **Chat conversation**, §§1, 2 and 4–7 | The specification requires fewer user turns and less attention without worse commitment errors or resumability. `[measured: specification text]` | Interaction-lead contract against CLI if its trial passes; no visibly better answer and no reachable product. `[measured]` |
| **Chat delivery**, §§1–6 and 9 | The specification requires estimates, quiet liveness, restart, verifier-bound completion and 80% delivery-window coverage. `[measured: specification text]` | Reliability mechanism; trust and streaming preference remain unmeasured, and sudden power/storage loss is outside scope. `[measured]` |
| **Consilience gate**, §§3–5, 7–8 and 10 | The specification requires structural evidence anchors, preserved disagreement and acquisition of a missing anchor. `[measured: specification text]` | Safety mechanism only; the specification says calling it safer before EXP-109 would be false. `[measured]` |
| **Decision protocol**, §§2, 4, 6–7 and EXP-106 | The specification requires independent-outcome improvement sufficient to repay mediation overhead. `[measured: specification text]` | Component-outcome lead only if EXP-106 passes; not a whole-product comparison. `[measured]` |
| **Evidence fusion**, §§3, 5–6 and 10 | The specification requires a better outcome than the same-budget single-Owner control without unacceptable beta, cost or latency. `[measured: specification text]` | Strong component-lead contract; error and cost are parity floors, and the comparator is not an incumbent product. `[measured]` |
| **Expertise acquisition**, §§1–2, 5, 7 and 10 | The specification requires better outcomes than an unchanged generalist while exposing harmful/stale retrieval and retiring regressions. `[measured: specification text]` | Component-learning lead only if EXP-126 passes; no product reach or incumbent arm. `[measured]` |
| **Living documentation**, §§3, 5–6 and EXP-99 | The specification requires better contradiction handling than maintained prose with explicit provenance classes. `[measured: specification text]` | Documentation-reliability lead only if EXP-99 passes; none of the seven product criteria is won. `[measured]` |
| **Memory and capability**, §§3–5 and 9 | The specification sets a prospective `+0.10` paired joint-success threshold, no cost increase and bounded alpha/beta harm against no automatic reuse. `[measured: specification text]` | Strong local component-lead contract; cross-harness persistence itself is parity after Ruflo’s proof. `[measured][cited]` |
| **Model lifecycle**, opening decision and §§4, 7–8 | The specification requires better accepted outcomes per unit cost for qualified model/release choices with safety non-regression. `[measured: specification text]` | Component-efficiency lead only if EXP-111 passes; no whole-product economics or global model-product comparator. `[measured]` |
| **Observability and steering**, §§3–7 and EXP-108 | The specification requires four projection depths plus attach, redirect, stop and takeover without worse burden or outcome. `[measured: specification text]` | Feature-parity contract with incumbent live control; no visual-design, trust or outcome superiority. `[measured]` |
| **Portable capability**, §§2–6 and 11 | The specification requires bounded native/portable equivalence for one package on Claude and Codex, with semantic-loss refusal. `[measured: specification text]` | Explicit parity, not leadership; Cursor, Grok and general outcome benefit remain unmeasured. `[measured]` |
| **Self-improvement**, §§1–5 and the bar | The specification requires held-out unseen-task improvement over matched extra compute/feedback without worse alpha, beta or unit cost. `[measured: specification text]` | Strong learning-lead contract only if EXP-104 passes; automatic reuse remains inert and no product comparator exists. `[measured]` |
| **Squad roles**, §§2–5 and 9 | The specification requires a RACI arm to beat matched-budget single-Owner and evidence-squad controls under quality, safety and cost thresholds. `[measured: specification text]` | Component-composition lead only if its experiment passes; no reachable surface, and live routing refuses while human beta is unestimated. `[measured]` |
| **Task management**, §§3–7 and 10 | The specification requires evidence-bound work items, claims, dependencies, disagreement and recovery to beat one capable Owner under EXP-98. `[measured: specification text]` | Possible durable-coordination component lead; no matched Hermes recovery or UI comparison. `[measured]` |
| **Verdict supply**, §§1, 3–6 | The specification requires authenticated preparation and capture of human verdicts without letting consequence or critic signals enter beta. `[measured: specification text]` | Label-supply mechanism; it deliberately permits zero automated verdicts and contests no product outcome. `[measured]` |

No specification is wholly orphaned from the seven plans; the failure is missing integration, stale plan-to-register references and absent comparative execution. `[measured: all seventeen specifications and all seven plans]`

## Specifications that would only reach parity

Only the first item is a whole-specification parity claim; the others name parity subfeatures inside specifications that also contain unproved deltas. `[measured]`

- **`2026-08-22-portable-capability.md` — whole specification:** bounded Claude/Codex conformance for one package; the specification explicitly withholds a broad portability claim. `[measured: portable-capability.md §11]`
- **`2026-08-22-observability-and-steering.md` — control subfeatures:** attach, redirect, stop and takeover match familiar incumbent controls; the provenance/beta/authority join is a proposed delta, not a measured operator-experience lead. `[measured: observability-and-steering.md §4 and EXP-108]`
- **`2026-08-22-memory-and-capability.md` — persistence subfeature:** cross-harness persistence reaches a capability already demonstrated by Ruflo; only measured beneficial reuse could lead. `[cited][measured: ruflo-teardown-2026-08-22.md, "Local persistence proof"; memory-and-capability.md §3]`
- **`2026-08-22-task-management.md` — board, claim and recovery subfeatures:** delivery could match Hermes’s inspected coordination mechanics; EXP-98 could establish only a local lead over one capable Owner until Hermes is an arm. `[measured: task-management.md §§3–10; hermes-teardown-2026-08-22.md, "Kanban: a real board, separate from delegation"]`
- **`2026-08-22-chat-conversation.md` and `2026-08-22-chat-delivery.md` — interaction and delivery subfeatures:** the specified journey can match shipped submit/status/resume/delivery features; its friction, trust and preference deltas remain unrun. `[measured]`
- **`2026-08-22-verdict-supply.md`, `2026-08-22-consilience-gate.md` and `2026-08-22-action-surface.md` — truth/authority instrumentation:** these can reach structural measurement and confirmation features, but no calibrated error or protected-authority result establishes leadership. `[measured]`

## Missing specifications to dispatch

These are scopes, not drafted specifications. `[asserted]`

### A. End-to-end product composition and operator reach

Specify the one normal operator journey from installation and identity enrolment through task submission, clarification, interruption, recovery, delivery and authenticated verdict. `[asserted]` Bind the existing chat, delivery, task, observability, action and capability contracts into one terminal success/adverse schema, without changing Gate A, Gate B or the pinned CLI surface. `[asserted]`

### B. Global accepted-outcome and user-impact benchmark

Specify a frozen, licensed, multi-domain bank with blind independent judging against ChatGPT Work, Hermes and Ruflo, plus specialist floors against Cursor for software, Copilot Cowork for governed actions and OpenClaw for recurring work. `[asserted]` Report joint success, domain floors, blind user preference, helpfulness/impact, abstention, quarantine, refusal, intervention and missing-task counts; a governance win without a quality win must lose. `[asserted: product-bar-2026-08-22.md, criteria 1 and 2]`

### C. Whole-product economics and latency

Specify provider-equivalent spend, quota consumption, tool and worker time, wall/device time, operator/review minutes and p50/p95 completion latency per accepted outcome. `[asserted]` Missing usage is adverse, zero accepted outcomes cost infinity, and the upper 95% paired-bootstrap interval must remain at or below `1.05×` the best incumbent separately for spend and review, rather than EXP-118’s raw `1.25×` ceiling. `[asserted: product-bar-2026-08-22.md, criterion 7]`

### D. Independent verifier calibration

Specify an immutable bank of at least 300 deliberately flawed artefacts, labelled independently of the candidate and verifier, plus uncontaminated valid controls. `[asserted]` Require a one-sided terminal false-accept upper bound below 1%, retain every quarantine/refusal, and prohibit proxy or repair-loop signals from entering beta. `[asserted: product-bar-2026-08-22.md, criterion 3]`

### E. Composed reliability and deadline SLO

Specify accepted-and-on-time completion across clean execution, timeout, process kill, power loss, storage corruption, transport loss, quota exhaustion and restart. `[asserted]` Report p50/p95 recovery and completion, duplicates, lost claims, abandoned tasks, interventions and human recovery time against the incumbent. `[asserted]`

### F. Connector, subscription and interoperability reach

Specify task-scoped capability discovery, binding and safe credential isolation across each supported harness and connected service, including import/export or explicit refusal where semantics cannot travel. `[asserted]` Measure successful real task completion, setup burden and cost rather than catalogue size, and do not treat one Codex-subscription path as broad multi-subscription leadership. `[asserted]`

### G. Unified learning-surface selection

Specify a matched-budget contest among capability retrieval, expertise acquisition, model selection/fine-tuning and harness self-change on the same held-out task mixture. `[asserted]` Promote only a positive lower confidence bound on accepted-outcome gain with no alpha, beta, cost or stale-data regression, and require rollback from the durable record. `[asserted]`

### H. Reproducibility and incumbent drift

Specify frozen revisions, environment/configuration capture, executable reproductions and preservation of every adverse denominator for each competitive claim. `[asserted]` Refresh the incumbent search and decisive comparisons at least quarterly, and automatically downgrade any claim whose comparator moved or whose reproduction no longer passes. `[asserted]`

## Missing decisions and experiments

1. **Approve the concrete WebAuthn verifier boundary and relying-party origin.** ADR-0080 already selects a user-verification-required ceremony, but leaves the audited dependency or OS-isolated broker and the private HTTPS origin/network exposure to separate approval. `[measured: ADR-0080, "Decision" and "Enforcement"]` Bind and test enrolment, recovery and revocation as part of that approved ingress. `[asserted: verdict-supply.md §5]`
2. **Write an execution plan for the already registered EXP-118.** It must cover the 80 paired tasks, sealed disjoint banks, blinding, matched runtime, missing-task treatment, provider GBP, human minutes, authority breach rule and result artefact. `[measured: experiment-register.md, EXP-118; all seven plans]`
3. **Prospectively register a separate global product contest; do not silently rewrite EXP-118.** It should add ChatGPT Work, Ruflo and a matched single-Owner Consilient arm to the qualified-composition and Hermes arms, plus Cursor, Copilot Cowork and OpenClaw as specialist floor comparators: without the Owner arm, a Consilient win cannot be attributed to composition; without the product, structural and specialist arms, the global bar remains outside the contest. `[asserted]` Freeze the multi-domain bank and blind judging before any run; require a joint-success lower bound above `+0.05` against the best incumbent, no domain-floor loss, the calibration and authority floors above, and an upper 95% paired-bootstrap interval at or below `1.05×` separately for spend and review, with any protected-authority breach or missing denominator an adverse stop. `[asserted: hermes-teardown-2026-08-22.md, "The comparison and the mechanism"; ruflo-teardown-2026-08-22.md, "Exact experiment that would decide the bar"; product-bar-2026-08-22.md, "Testable criteria for a credible ‘best’ claim"]`
4. **Pre-register the chat-versus-command trial described in ADR-0070.** The entry should freeze task bank, matched runtime, clarification/commitment-error outcomes, user turns, attention time, resumability and killing thresholds before any run. `[measured: ADR-0070, "What would overturn this"]`
5. **Pre-register the quiet-versus-streaming trial described in ADR-0071.** The entry should freeze matched tasks and measure blind preference, trust calibration, abandonment, attention, time to useful information, accepted completion and cost. `[measured: ADR-0071, "What would overturn this"]`
6. **Repair plan/register drift before execution.** Replace the false “absent” status for EXP-104, EXP-105, EXP-110, EXP-111 and EXP-126 with the live `BLOCKED` status, and extend the umbrella plan’s inventory beyond ADR-0081; this report does not make those edits. `[measured: the seven plans and experiment-register.md]`

None of these statements is a pre-registration; the experiment register was not changed by this audit. `[measured]`

## Cost and latency verdict

**Confirmed:** the fixed seventeen specifications cannot show that delivered Consilient is cheaper or faster per accepted artefact than Hermes, Ruflo or ChatGPT Work, because no common outcome-normalised cost/latency artefact or whole-product contract exists. `[measured]` EXP-118’s raw `1.25×` ceiling is too loose to support economic leadership even if it passes. `[asserted: product-bar-2026-08-22.md, criterion 7]`

**Suspected:** Consilient will be slower and dearer where additional evidence acquisition, verification, write-ahead decisions, append-only records and human verdicts do not cause enough extra accepted outcomes or prevented false accepts to repay themselves. `[asserted]` The direction and margin remain unknown; claiming either as measured would repeat the defect this audit is meant to prevent. `[measured]`

The decision rule should therefore be economic, not rhetorical: the discipline survives only where its accepted-outcome gain or error reduction clears an upper 95% paired-bootstrap interval ≤`1.05×` separately for spend and review; elsewhere the cheaper incumbent wins. `[asserted]`

## What survives the three falsifications

Cross-harness memory, broad subscription reach and verifier evaluation are not defensible novelty claims. `[cited: ruflo-teardown-2026-08-22.md; subscription-reach-2026-08-22.md; product-bar-2026-08-22.md, "The candidate gaps, tested rather than assumed"]` What remains is:

- explicit admission of different evidence classes rather than counting same-evidence agreement as consilience; `[measured: evidence-fusion.md §§2–6; consilience-gate.md §§3–8]`
- terminal acceptance-error accounting tied to authenticated human truth, with quarantine and refusal retained; `[measured: verdict-supply.md §§1–6; consilience-gate.md]`
- one accountable Owner, recorded dissent and a beta-conditioned ceiling on candidate exposure; `[measured][algebra: squad-roles.md §§2–5; ADR-0077]`
- append-only provenance, adverse-outcome retention and explicit separation of generated, written and projected state; `[measured: living-documentation.md §§3–6; action-surface.md §5]`
- bounded recall and explicit semantic-loss refusal rather than pretending every capability travels unchanged; `[measured: memory-and-capability.md §4; portable-capability.md §§3–6]`
- authenticated, non-delegable principal authority as a design requirement; `[measured: autonomy-and-friction.md §5; verdict-supply.md §5; ADR-0080]`
- a proposed joined decision over outcome, error, authority and full cost rather than a single benchmark score. `[asserted: experiment-register.md, EXP-118; product-bar-2026-08-22.md, "Testable criteria for a credible ‘best’ claim"]`

The first five are concrete in the specifications; the authority mechanism is specified but unresolved, and joined proof remains a proposed synthesis. `[measured]` None is evidence of product superiority, and the record does not establish “most careful”, let alone “best”. `[asserted]`

## Final answer

If every one of the fixed seventeen specifications were delivered perfectly tomorrow, the result would be a well-governed but unreachable and competitively unproved system. `[asserted][measured: current gate state and fixed specification set]` The concurrent answer-quality specification adds a missing response policy and proposed comparison, not a result. `[measured]` With or without it, Consilient has **no demonstrated world lead** in reachable product, accepted outcome, acceptance error, authority, coordination, learning, cost, latency, user preference, domain breadth or reliability. `[measured]`

The exact thing it could eventually lead is **auditable joined proof of whether delegated work should be trusted**: structurally distinct or exogenous anchors with dependence visible, terminal human-truth calibration, non-delegable authority, adverse-outcome retention and outcome-normalised cost in one provenance chain. `[asserted]` To claim even that, Consilient must deliver the missing scopes above and win the measurements; until then, “best globally” is not a product fact but an unpassed research hypothesis. `[asserted]`

## What I did not check

- No different model family read any finding; the independent cross-family count is zero throughout. `[measured]`
- No EXP-118 or EXP-128 result was run or inferred; EXP-118 is blocked and EXP-128 is not registered. `[measured]`
- ChatGPT Work, Hermes and Ruflo were not run end to end on a common task bank; external claims remain bounded to the cited official/public artefacts and the pinned local teardowns. `[measured]`
- The concurrent answer-quality specification and ADR-0087 were not audited criterion by criterion because they were claimed after this dispatch opened; only the specification’s stated evidence boundary and EXP-128 status were checked for impact on the verdict. `[measured]`
- The specialist products named by the broader bar were not freshly re-run or re-sourced in this pass. `[measured]`
- No private repository, credentialed connector, metered API, protected action or external publication was inspected or exercised. `[measured]`
- Any change to a fixed blob above, the experiment register, gate state or an incumbent revision invalidates the affected negative finding and requires a fresh audit. `[asserted]`

## Sources

- [Hermes teardown](hermes-teardown-2026-08-22.md), especially “Head-to-head criteria” and “The comparison and the mechanism”. `[measured]`
- [Ruflo teardown](ruflo-teardown-2026-08-22.md), especially “Durable memory across models and harnesses”, “Correctness measurement and β”, and “Exact experiment that would decide the bar”. `[measured]`
- [External product bar](product-bar-2026-08-22.md), especially “Testable criteria for a credible ‘best’ claim”. `[measured]`
- [Subscription reach](subscription-reach-2026-08-22.md), especially “Direct answer”. `[measured]`
- [OpenAI: ChatGPT Work and Codex](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex) and [OpenAI: Workspace Agents](https://help.openai.com/en/articles/20001143), retrieved 2026-08-22. `[cited]`
- [Hermes Kanban documentation](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/kanban.md) and [Codex app-server runtime](https://github.com/NousResearch/hermes-agent/blob/261a4ef/website/docs/user-guide/features/codex-app-server-runtime.md), retrieved 2026-08-22. `[cited]`
- [Ruflo pinned audit revision](https://github.com/ruvnet/ruflo/tree/5234333c3462640ab348363ba4a142945fd2bc47) and [same-day drift comparison](https://github.com/ruvnet/ruflo/compare/5234333c3462640ab348363ba4a142945fd2bc47...127a6546c40899c7ee9a9d54f35adb8bdbca6825), retrieved 2026-08-22. `[cited]`

# Decision index

> **Producer:** `scripts/build_decision_index.py`
> **Source:** `docs/decisions/[0-9][0-9][0-9][0-9]-*.md`
> **Source SHA-256:** `5be7b95fe9b7bad844f9c02316b4b5b76d780cc7e4629a6a00b1727926d8c249`
> **Do not hand-edit:** regenerate with `python scripts/build_decision_index.py`.

| ADR | Decision | Status | Supersession |
|---|---|---|---|
| [0001](0001-build-a-meta-harness-not-a-harness.md) | Build a meta-harness above existing coding agents, not a standalone harness | SUPERSEDED | superseded by 0027 |
| [0002](0002-organise-around-beta-verifier-false-accept-rate.md) | Organise the system around β, the verifier false-accept rate | PROVISIONAL | — |
| [0003](0003-no-learned-routing-policy-in-v0.md) | Ship no learned routing policy in v0 | ACCEPTED | — |
| [0004](0004-licence-mit-dco-and-the-cla-question.md) | Licence MIT, and require a DCO — plus an unresolved question about a CLA | PROPOSED | — |
| [0005](0005-local-model-library-with-hardware-gating.md) | Ship a local model library with hardware-gated downloads | SUPERSEDED | — |
| [0006](0006-ticket-store-sqlite-plus-git-log.md) | Ticket store: SQLite for coordination, append-only JSONL in git for the record | ACCEPTED | — |
| [0007](0007-cli-only-no-review-surface.md) | CLI only, and build no review surface | SUPERSEDED | superseded by 0053 |
| [0008](0008-name-the-project-consilience.md) | Name the project Consilience | SUPERSEDED | superseded by 0038 |
| [0009](0009-route-per-task-not-per-step.md) | Route per task, not per step | PROVISIONAL | — |
| [0010](0010-name-the-different-class-of-facts.md) | Every multi-agent structure must name its different class of facts | ACCEPTED | — |
| [0011](0011-evidence-merge-not-meeting.md) | Replace the "meeting" primitive with an evidence merge | SUPERSEDED | superseded by 0020 |
| [0012](0012-composite-beta-with-per-check-diagnostics.md) | Measure the composite β directly; keep per-check β as diagnostics | ACCEPTED | — |
| [0013](0013-evaluate-on-repo-history-not-benchmarks.md) | Evaluate on our own repository history, not a public benchmark | ACCEPTED | — |
| [0014](0014-portable-skills-agents-md.md) | Adopt SKILL.md and AGENTS.md as the portable instruction format; `.agents/` is the source of truth | ACCEPTED | — |
| [0015](0015-dogfooding-gate.md) | Dogfooding gate — do not depend on Consilience until it clears three tests | ACCEPTED | superseded by 0037 |
| [0016](0016-skill-distribution-mcp-plugins.md) | Skill distribution: consume via `skills` with a vetting gate; publish via bundled npm | PROPOSED | — |
| [0017](0017-bootstrap-harness.md) | The bootstrap harness — Claude Code configured as a working prototype of Consilience | PROPOSED | — |
| [0018](0018-self-modification-gated-by-measured-verifier.md) | Self-modification is gated by measured verifier reliability, and the verifier is not self-modifiable | ACCEPTED | — |
| [0019](0019-paid-capability-acquisition.md) | Paid capability acquisition — off by default, four conditions, never automatic | PROPOSED | — |
| [0020](0020-meetings-and-authority-matrix.md) | Meetings, and the Owner/Evidence authority matrix | CUT / RETAINED | supersedes 0011 |
| [0021](0021-pushback-protocol.md) | The pushback protocol — decision hygiene, and two challenges then comply | PROPOSED | — |
| [0022](0022-safety-floor-and-moderation.md) | Safety floor, maximal configurability above it, and an honest account of moderation | PROPOSED | — |
| [0023](0023-pr-review-gates.md) | PR review gates — evidence proportional to irreversibility | PROPOSED | — |
| [0024](0024-commercialisation-and-telemetry.md) | Commercialisation and telemetry — private by default, consent per purpose, no capability withheld | PROPOSED | — |
| [0025](0025-model-discovery-and-capability-probing.md) | Model discovery and capability probing — listen, probe, derive; no learned router, no GNN | PROPOSED | — |
| [0026](0026-admit-only-budget-and-hardware-feasible-backends.md) | Admit only budget- and hardware-feasible backends to routing | PROVISIONAL | superseded by 0028; supersedes 0005 |
| [0027](0027-compose-domain-harness-provider-and-model.md) | Compose domain, execution harness, provider and model as separate routing layers | PROVISIONAL | supersedes 0001 |
| [0028](0028-optimise-expiring-subscription-capacity-for-verified-value.md) | Optimise expiring subscription capacity for verified value | PROVISIONAL | supersedes 0026 |
| [0029](0029-separate-runtime-resource-state-from-change-intelligence.md) | Separate runtime resource state from vendor change intelligence | PROVISIONAL | — |
| [0030](0030-size-orchestration-by-usable-context-and-measured-outcomes.md) | Size orchestration roles by usable context and measured outcomes | PROVISIONAL | — |
| [0031](0031-implement-v0-in-python-with-a-stdlib-only-core.md) | Implement v0 in Python, with a stdlib-only core | SUPERSEDED | superseded by 0032 |
| [0032](0032-single-language-python-for-the-orchestrator.md) | Single-language Python for the orchestrator — supersedes 0031 | ACCEPTED | supersedes 0031 |
| [0033](0033-decide-by-default-ask-only-where-the-user-is-the-only-valid-decider.md) | Decide by default; ask only where the user is the only valid decider | PROVISIONAL | — |
| [0034](0034-detect-stalls-by-artefact-progress-and-default-to-diagnosis.md) | Detect stalls by artefact progress, and default to diagnosis rather than killing | PROVISIONAL | — |
| [0035](0035-user-controlled-visibility.md) | Visibility is a user-controlled rendering of the record, never a second record | PROVISIONAL | — |
| [0036](0036-upstream-first-adopt-contribute-never-silently-fork.md) | Upstream-first — adopt, contribute, and never silently fork | PROPOSED | — |
| [0037](0037-replace-gate-b2-with-measured-critic-throughput-gain.md) | Replace Gate B2 with measured critic review-throughput gain — supersedes 0015 Gate B2 | SUPERSEDED | superseded by 0045; supersedes 0015 |
| [0038](0038-rename-the-project-consilient.md) | Rename the project Consilient — the predicate, not the phenomenon | ACCEPTED | supersedes 0008 |
| [0039](0039-stage-3-entered-on-approval-gate-b-gates-dependence.md) | Stage 3 is entered on approval; Gate B gates dependence, not construction | ACCEPTED | — |
| [0040](0040-decide-from-evidence-not-from-pretraining.md) | The harness decides from evidence, not from pretraining — and runs the experiment when it has none | DEPRECATED | — |
| [0041](0041-transports-are-projections-not-authority-and-untrusted-channels-cannot-deliver-verdicts.md) | Transports are lossy projections, not coordination authority — and untrusted channels cannot deliver human verdicts | ACCEPTED | — |
| [0042](0042-admit-connectors-by-capability-probing-credential-isolation-and-fail-closed-boundaries.md) | Admit connectors by zero-inference capability probing, credential isolation, and fail-closed spend caps | ACCEPTED | — |
| [0043](0043-gate-a3-counts-new-refusals-not-historical-ones.md) | Gate A3 counts new refusals, not historical ones | ACCEPTED | — |
| [0044](0044-openrouter-is-the-only-metered-vendor-and-budgets-are-a-capability.md) | OpenRouter is the only metered vendor, subscriptions cover everything else, and budgeting is a required capability | ACCEPTED | supersedes 0019 |
| [0045](0045-give-gate-b2-and-b3-success-criteria-they-never-had.md) | Give Gate B2 and B3 the success criteria they never had | ACCEPTED | supersedes 0037 |
| [0046](0046-gate-b3-is-evidenced-by-a-dated-result-not-by-a-schedule-trigger.md) | Gate B3 is evidenced by a dated result, not by a schedule trigger | ACCEPTED | — |
| [0047](0047-promote-the-adapter-contract-and-retire-adapter-count-as-evidence.md) | Promote the adapter contract, retire adapter count as evidence, and start measuring what an adapter costs | ACCEPTED | supersedes 0001 |
| [0048](0048-open-source-first-and-facilitation-is-prepaid-never-in-arrears.md) | Open source first, and paid facilitation is prepaid — never in arrears | ACCEPTED | — |
| [0049](0049-experiments-inform-they-do-not-gate.md) | Experiments inform; they do not gate construction | ACCEPTED | — |
| [0050](0050-gate-on-effect-size-not-on-uncertainty.md) | Gate on effect size, not on the mere existence of uncertainty | ACCEPTED | — |
| [0051](0051-a-tick-is-an-attempt-and-only-execution-runs-unattended.md) | A tick is an attempt, only execution-bearing work runs unattended, and there is no offline consolidation phase | PROVISIONAL | — |
| [0053](0053-build-one-local-observability-surface-that-renders-the-record.md) | Build one local observability surface that renders the record, and keep building no review surface | ACCEPTED | supersedes 0007 |
| [0054](0054-route-by-measured-capability-against-a-verifier-contract-never-by-a-harness-label.md) | Route by measured capability keyed on task family, and credit evidence to the anchor, never to the harness's label | PROVISIONAL | — |
| [0055](0055-simulated-users-produce-runs-not-verdicts.md) | Simulated users produce runs, not verdicts — and the same run is how we test whether a non-expert can use this | PROVISIONAL | — |
| [0056](0056-schedule-work-across-prepaid-quota-pools-and-never-shed-to-spend.md) | Treat prepaid quota pools as a first-class scheduling constraint, shed a near-exhausted pool onto an idle one, and never shed onto spend | PROVISIONAL | — |
| [0057](0057-a-users-trajectory-is-their-data.md) | A user's trajectory is their data, private by default, and shared only by consent | ACCEPTED | — |
| [0058](0058-orchestration-ships-as-a-script-until-the-cli-surface-is-settled.md) | Orchestration ships as `scripts/dispatch.py`; the `consil` CLI surface stays the principal's to settle | ACCEPTED | — |
| [0059](0059-package-the-discipline-as-skills-and-separate-instance-from-product.md) | Package this project's discipline as skills, keep agent files as wiring, and separate instance configuration from product | PROVISIONAL | — |
| [0060](0060-adopt-open-design-portable-contract-and-critique-for-design-work.md) | Adopt Open Design's portable contract and critique for design work; the desktop app is an optional local tool, not a runtime dependency | PROVISIONAL | — |
| [0061](0061-the-descriptor-is-agent-command-post.md) | The descriptor is Agent Command Post | ACCEPTED | supersedes 0062 |
| [0062](0062-call-consilient-a-command-post-not-a-meta-harness.md) | Call Consilient a command post, not a meta-harness | ACCEPTED | superseded by 0061 |
| [0063](0063-instance-cwd-allowlist-is-supervised-dispatch-not-a-gate-pass.md) | An instance cwd allowlist is supervised dispatch, not a Gate B pass | ACCEPTED | — |
| [0064](0064-add-training-providers-and-supersede-openrouter-as-sole-metered-vendor.md) | Add training and inference providers; OpenRouter is no longer the sole metered vendor | ACCEPTED | supersedes 0044 |
| [0065](0065-what-is-native-what-is-adopted-and-what-is-a-marketplace.md) | What is native, what is adopted from upstream, and what is a marketplace | ACCEPTED | — |
| [0066](0066-principal-harvest-is-a-private-training-corpus.md) | The principal's Consilient usage is a private training corpus; fine-tunes are native backends; the data is never published | ACCEPTED | — |
| [0067](0067-front-one-chat-with-one-owner-evidence-squads.md) | Front one chat with one-owner squads whose added roles bring distinct evidence | PROVISIONAL | — |
| [0068](0068-decompose-each-request-into-the-fewest-verifiable-dependent-streams.md) | Decompose each request into the fewest verifiable dependent streams before composing squads | PROVISIONAL | — |
| [0070](0070-make-chat-a-compiler-to-versioned-work-item-commitments.md) | Make chat a compiler to versioned work-item commitments before dispatch | PROPOSED | — |
| [0071](0071-commit-to-a-delivery-window-and-prove-liveness-with-sealed-checkpoints.md) | Commit to a delivery window, prove liveness with sealed checkpoints, and send only exceptions before delivery | PROVISIONAL | — |
| [0072](0072-close-native-work-items-only-against-evidence-and-project-them-outward.md) | Close native work items only against evidence and project them outward | PROVISIONAL | — |
| [0073](0073-living-documentation-is-generated-checked-or-append-only.md) | Living documentation is generated-and-checked or append-only — never maintained | PROVISIONAL | — |
| [0074](0074-preserve-records-version-capabilities-and-reserve-training-for-parameter-updates.md) | Preserve records, version capabilities and reserve training for parameter updates | PROVISIONAL | — |
| [0075](0075-prove-reversibility-close-escalation-and-ratchet-friction.md) | Prove reversibility, close escalation to six classes, and ratchet friction | PROVISIONAL | — |
| [0076](0076-owner-gates-persistent-self-change-and-the-instrument-is-sealed.md) | The owner gates persistent self-change and the acceptance instrument stays sealed | PROVISIONAL | — |
| [0077](0077-separate-candidate-exposure-from-verifier-fusion-and-measure-both.md) | Separate candidate-exposure unions from verifier-fusion intersections and measure both | PROVISIONAL | — |
| [0078](0078-admit-only-gated-typed-effects-and-record-every-effect.md) | Admit only gated typed effects and record every effect | PROVISIONAL | — |
| [0079](0079-require-a-durable-decision-before-material-actuation-and-keep-judgement-in-the-skill.md) | Require a durable decision before material actuation and keep judgement in the skill | PROVISIONAL | — |
| [0080](0080-keep-consequence-signals-out-of-human-beta.md) | Keep consequence signals out of human-verdict beta | PROVISIONAL | — |
| [0081](0081-refuse-high-consequence-single-anchor-conclusions.md) | Refuse high-consequence single-anchor conclusions and acquire another anchor | PROVISIONAL | — |
| [0082](0082-project-raci-onto-per-work-item-rights-and-require-structural-consultation.md) | Project RACI onto per-work-item rights and require structural consultation | PROVISIONAL | supersedes 0020 |
| [0083](0083-expose-squad-state-only-on-pull-and-record-steering-before-it-acts.md) | Expose squad state only on pull and record steering before it acts | PROVISIONAL | supersedes 0053 |
| [0084](0084-compile-portable-capabilities-per-harness-and-refuse-semantic-loss.md) | Compile portable capabilities per harness and refuse semantic loss | PROVISIONAL | — |
| [0085](0085-qualify-model-revisions-before-routing-and-seal-fine-tune-evaluation.md) | Qualify model revisions before routing, defer matrix factorisation, and seal fine-tune evaluation | PROVISIONAL | — |
| [0086](0086-acquire-expertise-as-a-proven-capability-bundle-and-tune-only-after-retrieval-loses.md) | Acquire expertise as a proven capability bundle and tune only after retrieval loses | PROVISIONAL | — |
| [0087](0087-return-one-answer-with-decision-relevant-checks.md) | Return one answer with decision-relevant checks and answer directly when convergence adds no value | PROPOSED | — |
| [0088](0088-make-zero-cost-a-native-fail-closed-routing-ladder.md) | Make zero-cost a native, fail-closed routing ladder | PROVISIONAL | — |
| [0089](0089-use-one-front-door-and-preserve-native-specialist-surfaces.md) | Use one front door and preserve native specialist surfaces | PROPOSED | — |
| [0090](0090-allocate-full-mode-effort-before-execution-and-make-light-mode-explicit.md) | Allocate full-mode effort before execution and make light mode explicit | PROVISIONAL | — |
| [0091](0091-check-declared-claims-against-the-import-graph-and-keep-declared-claims-authoritative.md) | Check declared claims against the import graph, and keep declared claims authoritative | PROVISIONAL | — |
| [0092](0092-classify-durable-work-and-stop-deliberation-at-an-external-threshold.md) | Classify durable work and stop deliberation at an external threshold | PROVISIONAL | supersedes 0090 |
| [0093](0093-compose-agent-roles-from-worker-method-and-subject-expertise.md) | Compose agent roles from worker method and subject expertise, and cut evidence-free specialists | PROVISIONAL | — |
| [0094](0094-make-scientific-execution-a-pinned-evidence-producing-profile.md) | Make scientific execution a pinned evidence-producing profile, not a second laboratory platform | PROVISIONAL | — |
| [0095](0095-project-orchestration-from-consumed-evidence-and-interrupt-on-decision-change.md) | Project orchestration from consumed evidence, isolate contributions, and interrupt on decision change | PROVISIONAL | — |
| [0096](0096-render-record-derived-observability-graphs-without-generated-explanations.md) | Render record-derived observability graphs without generated explanations | PROVISIONAL | — |
| [0097](0097-keep-automatic-triggered-recall-inert-until-it-beats-pull.md) | Keep automatic triggered recall inert until it beats deliberate pull | PROVISIONAL | — |
| [0098](0098-permit-one-authenticated-local-surface-and-supersede-the-blanket-prohibition.md) | Permit one authenticated local surface, superseding the blanket prohibition | ACCEPTED | — |
| [0099](0099-fund-by-sponsorship-alone-and-stay-outside-trader-status.md) | Fund by sponsorship alone, and stay outside trader status | ACCEPTED | — |
| [0100](0100-measure-beta-prospectively-from-live-dispatch-and-retire-history-mining.md) | Measure β prospectively from live dispatch, and retire history mining | PROVISIONAL | — |
| [0101](0101-widen-the-scope-to-any-domain-and-keep-coding-as-v0.md) | Widen the scope to any domain, and keep coding as v0 | ACCEPTED | — |
| [0102](0102-keep-telephony-out-of-the-open-source-tree-at-launch.md) | Keep telephony out of the open-source tree at launch | ACCEPTED | — |
| [0103](0103-make-contract-beta-the-gate-quantity-and-keep-human-beta-unblocking.md) | Make contract-β the gate quantity, and keep human-β as alignment rather than a blocker | PROVISIONAL | — |
| [0104](0104-re-derive-both-halves-of-beta-star-from-evidence.md) | Re-derive both halves of β\\\* from evidence, and let the arithmetic fall where it does | PROVISIONAL | — |
| [0105](0105-baseline-the-22-august-capture-loss.md) | Baseline the 22 August capture loss under its own pinned ratchet | ACCEPTED | — |
| [0106](0106-admit-third-party-maintainer-verdicts-as-human-beta.md) | Admit identified third-party maintainer verdicts as human-β authors | PROPOSED | — |
| [0107](0107-a-unit-may-merge-into-a-red-tree-but-nothing-may-publish-from-one.md) | A unit may merge into a red tree; nothing may publish from one | ACCEPTED | — |
| [0108](0108-rotate-dispatch-across-a-users-own-accounts-per-harness.md) | Rotate dispatch across a user's own accounts, per harness, where the vendor allows it | PROVISIONAL | — |

# Decision index

51 ADRs, 21 Aug 2026. [measured] Format and rules: [`README.md`](README.md).
This table is maintained by hand and has drifted before (C3, `../00-context/corrections-2026-08-21.md`): it read "39 ADRs" while the directory held 48.
`python .github/scripts/check_record_numbers.py` catches two ADRs sharing a number; nothing
catches a row missing from this table, which is the argument for generating it rather than
editing it. 0002 and 0027 appear twice by design, in the highlight section and in their own.

**Status key:** ✅ ACCEPTED · 🟡 PROVISIONAL (rests on simulated/asserted evidence, has a
named experiment) · 📋 PROPOSED · ⛔ SUPERSEDED/DEPRECATED

## The load-bearing four

Read these before anything else. Everything downstream depends on them.

| # | Decision | Status |
|---|---|---|
| [0002](0002-organise-around-beta-verifier-false-accept-rate.md) | **Organise the system around β**, the verifier false-accept rate. Contains the closed form β\* = (1−α)·e^(−kΔ) and the distribution-free result. | 🟡 |
| [0010](0010-name-the-different-class-of-facts.md) | **Every multi-agent structure must name its different class of facts.** The theorem. | ✅ |
| [0027](0027-compose-domain-harness-provider-and-model.md) | **Compose domain, execution harness, provider and model separately**; public benchmarks are priors, local outcomes decide. | 🟡 |
| [0018](0018-self-modification-gated-by-measured-verifier.md) | **Self-modification gated by measured verifier reliability.** The project's likely novel contribution. | ✅ |

## Architecture

| # | Decision | Status |
|---|---|---|
| [0003](0003-no-learned-routing-policy-in-v0.md) | No learned routing policy in v0 | ✅ |
| [0001](0001-build-a-meta-harness-not-a-harness.md) | Meta-harness above coding agents (superseded in part by 0027's compositional boundary) | ⛔ |
| [0005](0005-local-model-library-with-hardware-gating.md) | Local model library with hardware gating (superseded by 0026) | ⛔ |
| [0006](0006-ticket-store-sqlite-plus-git-log.md) | Ticket store: SQLite for coordination, append-only JSONL in git for the record | ✅ |
| [0007](0007-cli-only-no-review-surface.md) | CLI only, and **build no review surface** | ✅ |
| [0009](0009-route-per-task-not-per-step.md) | Route per task, not per step | 🟡 |
| [0011](0011-evidence-merge-not-meeting.md) | Evidence merge (superseded by 0020) | ⛔ |
| [0012](0012-composite-beta-with-per-check-diagnostics.md) | Measure composite β directly; per-check as diagnostics | ✅ |
| [0020](0020-meetings-and-authority-matrix.md) | **Meetings + the Owner/Evidence authority matrix** | 📋 |
| [0025](0025-model-discovery-and-capability-probing.md) | Model discovery + capability probing; GNNs considered and rejected with reopen conditions | 📋 |
| [0026](0026-admit-only-budget-and-hardware-feasible-backends.md) | **Admit only budget- and hardware-feasible backends to routing**; superseded in part by 0028's subscription allocation | 🟡 |
| [0027](0027-compose-domain-harness-provider-and-model.md) | **Compose domain, execution harness, provider and model separately**; OpenRouter is a standalone provider | 🟡 |
| [0028](0028-optimise-expiring-subscription-capacity-for-verified-value.md) | **Allocate expiring included subscription capacity by incremental verified value**; never burn quota for its own sake | 🟡 |
| [0029](0029-separate-runtime-resource-state-from-change-intelligence.md) | **Separate authenticated resource state from first-party change intelligence**; change feeds invalidate but never create headroom | 🟡 |
| [0036](0036-upstream-first-adopt-contribute-never-silently-fork.md) | **Upstream-first** — adopt over build, PR rather than fork, and outbound PRs meet the same bar as inbound | 📋 |
| [0035](0035-user-controlled-visibility.md) | User-controlled visibility dial (draft, from the overnight design pass) | 📋 |
| [0034](0034-detect-stalls-by-artefact-progress-and-default-to-diagnosis.md) | **Detect stalls by artefact progress**, never by process identity; escalate rather than kill | 🟡 |
| [0033](0033-decide-by-default-ask-only-where-the-user-is-the-only-valid-decider.md) | **Decide by default**; ask only in seven named classes, and only when the user can afford to answer | 🟡 |
| [0032](0032-single-language-python-for-the-orchestrator.md) | **Single-language Python for the orchestrator**; TypeScript/Node stays a spawned sidecar. Supersedes 0031 | ✅ |
| [0031](0031-implement-v0-in-python-with-a-stdlib-only-core.md) | Implement v0 in Python with a stdlib-only core (superseded by 0032) | ⛔ |
| [0030](0030-size-orchestration-by-usable-context-and-measured-outcomes.md) | **Size orchestration roles by usable context and measured outcomes**; Opus 5 senior default, Gemini 3.7 Flash High candidate | 🟡 |
| [0041](0041-transports-are-projections-not-authority-and-untrusted-channels-cannot-deliver-verdicts.md) | **Transports are lossy projections, not coordination authority**; untrusted third-party channels cannot deliver human verdicts | ✅ |
| [0042](0042-admit-connectors-by-capability-probing-credential-isolation-and-fail-closed-boundaries.md) | **Admit connectors by zero-inference capability probing, credential isolation, and fail-closed spend caps** | ✅ |
| [0043](0043-gate-a3-counts-new-refusals-not-historical-ones.md) | **Gate A3 counts new refusals, not historical ones** — A3 is unpassable as written; the only way to satisfy it is to lose a day of capture | ✅ |
| [0044](0044-openrouter-is-the-only-metered-vendor-and-budgets-are-a-capability.md) | **OpenRouter is the only metered vendor**; subscriptions cover everything else; weekly and monthly budgets are a required capability | ✅ |
| [0045](0045-give-gate-b2-and-b3-success-criteria-they-never-had.md) | **Gate B2 and B3 get success criteria they never had** — B2 measures the critic's own β; B3 needs a dated, machine-readable fallback result | ✅ |
| [0046](0046-gate-b3-is-evidenced-by-a-dated-result-not-by-a-schedule-trigger.md) | **Gate B3 is evidenced by a dated result, not a schedule trigger** — no secret may reach a public repository, so the exercise runs locally | ✅ |
| [0047](0047-promote-the-adapter-contract-and-retire-adapter-count-as-evidence.md) | **Promote the adapter contract; retire adapter count as evidence** — seven backends fit unchanged, but the newest adapter is 3.8× the smallest | ✅ |
| [0048](0048-open-source-first-and-facilitation-is-prepaid-never-in-arrears.md) | **Open source first; paid facilitation is prepaid, never in arrears** — every capability usable by someone who pays nothing and contacts no server | ✅ |
| [0049](0049-experiments-inform-they-do-not-gate.md) | **Experiments inform; they do not gate construction** — an unrun experiment justifies a PROVISIONAL assumption with a falsifier, not a stop | ✅ |
| [0050](0050-gate-on-effect-size-not-on-uncertainty.md) | **Gate on effect size, not on the mere existence of uncertainty** — an entry that does not state its largest plausible effect cannot block a build | ✅ |
| [0051](0051-package-the-discipline-as-skills-and-separate-instance-from-product.md) | **Package the discipline as skills; agent files are wiring; instance is separate** — a rule may not be introduced in an agent definition three of four runtimes cannot read | 🟡 |

## Behaviour and safety

| # | Decision | Status |
|---|---|---|
| [0019](0019-paid-capability-acquisition.md) | Paid capability acquisition — off by default, four conditions. **Condition 3 superseded in part by 0044** | ⛔ |
| [0021](0021-pushback-protocol.md) | **Pushback protocol** — decision hygiene, two challenges then comply | 📋 |
| [0022](0022-safety-floor-and-moderation.md) | Safety floor, maximal configurability above it, honest moderation limits | 📋 |

## Process, method and project

| # | Decision | Status |
|---|---|---|
| [0004](0004-licence-mit-dco-and-the-cla-question.md) | Licence MIT, DCO, and the **open CLA question** | 📋 |
| [0008](0008-name-the-project-consilience.md) | Name the project **Consilience** (superseded by 0038) | ⤴ |
| [0013](0013-evaluate-on-repo-history-not-benchmarks.md) | Evaluate on repository history, not benchmarks | ✅ |
| [0014](0014-portable-skills-agents-md.md) | SKILL.md + AGENTS.md; `.agents/` is source of truth | ✅ |
| [0015](0015-dogfooding-gate.md) | **Dogfooding gate** — three stages, measured gates (Gate B2 superseded by 0037) | ✅ |
| [0037](0037-replace-gate-b2-with-measured-critic-throughput-gain.md) | **Superseded by 0045.** Replace Gate B2 with measured critic review-throughput gain**; supersedes 0015 Gate B2 | ⛔ |
| [0038](0038-rename-the-project-consilient.md) | **Rename the project Consilient** — the predicate, not the phenomenon; supersedes 0008 | ✅ |
| [0039](0039-stage-3-entered-on-approval-gate-b-gates-dependence.md) | Stage 3 entered on approval; Gate B gates dependence not construction; would supersede 0015 Gate B4 | ✅ |
| [0040](0040-decide-from-evidence-not-from-pretraining.md) | **DEPRECATED 20 Aug 2026** — no mechanically complete decision-and-provenance discriminator exists for the proposed EXP-46 [algebra] | ⛔ |
| [0016](0016-skill-distribution-mcp-plugins.md) | Skill distribution, MCP, plugins — and the supply-chain rule | 📋 |
| [0017](0017-bootstrap-harness.md) | Bootstrap harness — Claude Code as a working prototype | 📋 |
| [0023](0023-pr-review-gates.md) | PR review gates by blast radius; admin bypass is logged | 📋 |
| [0024](0024-commercialisation-and-telemetry.md) | Commercialisation and telemetry — private by default, per-use re-consent | 📋 |

## Standing invariants

From [`../00-context/decisions-so-far.md`](../00-context/decisions-so-far.md) — these apply
to every ADR and every PR:

- **I1.** Any declared chokepoint ships with the check that bans bypassing it, in the same
  commit.
- **I2.** Any documented behaviour ships with the test that proves it.
- **I3.** No claim in `docs/` without an evidence tag.

## Outstanding

- **0004** — CLA or DCO alone. Must be settled before the first external PR; effectively
  unrecoverable afterwards.
- **0008 / 0038** — trademark clearance not run for either name. 0008 checked live
  registries for the noun; nothing has been checked for the adjective. Owed and cheap.
- **0002, 0009** — PROVISIONAL pending EXP-01 and EXP-06.
- **0026** — PROVISIONAL pending EXP-21.
- **0027** — PROVISIONAL pending EXP-22.
- **0028** — PROVISIONAL pending EXP-23.
- **0029** — PROVISIONAL pending EXP-27.
- **0030** — PROVISIONAL pending EXP-30.
- **0018** — decision 2 conditional on EXP-12 *and* EXP-13.

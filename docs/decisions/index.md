# Decision index

24 ADRs, 19 Aug 2026. Format and rules: [`README.md`](README.md).

**Status key:** ✅ ACCEPTED · 🟡 PROVISIONAL (rests on simulated/asserted evidence, has a
named experiment) · 📋 PROPOSED · ⛔ SUPERSEDED

## The load-bearing four

Read these before anything else. Everything downstream depends on them.

| # | Decision | Status |
|---|---|---|
| [0002](0002-organise-around-beta-verifier-false-accept-rate.md) | **Organise the system around β**, the verifier false-accept rate. Contains the closed form β\* = (1−α)·e^(−kΔ) and the distribution-free result. | 🟡 |
| [0010](0010-name-the-different-class-of-facts.md) | **Every multi-agent structure must name its different class of facts.** The theorem. | ✅ |
| [0001](0001-build-a-meta-harness-not-a-harness.md) | Build a **meta-harness**, not a harness. | ✅ |
| [0018](0018-self-modification-gated-by-measured-verifier.md) | **Self-modification gated by measured verifier reliability.** The project's likely novel contribution. | 📋 |

## Architecture

| # | Decision | Status |
|---|---|---|
| [0003](0003-no-learned-routing-policy-in-v0.md) | No learned routing policy in v0 | ✅ |
| [0005](0005-local-model-library-with-hardware-gating.md) | Local model library — **wrap, don't build** | ⛔ in part |
| [0006](0006-ticket-store-sqlite-plus-git-log.md) | Ticket store: SQLite for coordination, append-only JSONL in git for the record | ✅ |
| [0007](0007-cli-only-no-review-surface.md) | CLI only, and **build no review surface** | ✅ |
| [0009](0009-route-per-task-not-per-step.md) | Route per task, not per step | 🟡 |
| [0011](0011-evidence-merge-not-meeting.md) | Evidence merge (superseded by 0020) | ⛔ |
| [0012](0012-composite-beta-with-per-check-diagnostics.md) | Measure composite β directly; per-check as diagnostics | ✅ |
| [0020](0020-meetings-and-authority-matrix.md) | **Meetings + the Owner/Evidence authority matrix** | 📋 |
| [0025](0025-model-discovery-and-capability-probing.md) | Model discovery + capability probing; GNNs considered and rejected with reopen conditions | 📋 |

## Behaviour and safety

| # | Decision | Status |
|---|---|---|
| [0019](0019-paid-capability-acquisition.md) | Paid capability acquisition — off by default, four conditions | 📋 |
| [0021](0021-pushback-protocol.md) | **Pushback protocol** — decision hygiene, two challenges then comply | 📋 |
| [0022](0022-safety-floor-and-moderation.md) | Safety floor, maximal configurability above it, honest moderation limits | 📋 |

## Process, method and project

| # | Decision | Status |
|---|---|---|
| [0004](0004-licence-mit-dco-and-the-cla-question.md) | Licence MIT, DCO, and the **open CLA question** | 📋 |
| [0008](0008-name-the-project-consilience.md) | Name the project **Consilience** | ✅ |
| [0013](0013-evaluate-on-repo-history-not-benchmarks.md) | Evaluate on repository history, not benchmarks | ✅ |
| [0014](0014-portable-skills-agents-md.md) | SKILL.md + AGENTS.md; `.agents/` is source of truth | ✅ |
| [0015](0015-dogfooding-gate.md) | **Dogfooding gate** — three stages, measured gates | ✅ |
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
- **0008** — trademark clearance on "Consilience" not yet run.
- **0002, 0009** — PROVISIONAL pending EXP-01 and EXP-06.
- **0018** — decision 2 conditional on EXP-12 *and* EXP-13.

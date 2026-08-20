# Origin-alignment audit — 19 August 2026

## Verdict

The earliest recoverable Cowork, Claude Code and Codex records remain aligned with the
current repository: Consilience is still an open meta-harness organised around provenance,
genuinely different classes of facts and measurement of verifier false acceptance.
[measured] No broad rewrite is warranted. [asserted]

The audit found stale operating instructions and several enforcement/registration gaps, not
a change of thesis. [measured] Those defects are corrected in the same change as this
record. [measured]

## Source coverage

| source tier | recoverable coverage | use in this audit |
|---|---|---|
| Original Cowork session | The remote transcript was not recoverable locally in full; a local application store retained only fragments. [measured] | Treated as partial evidence and corroborated only through `conversation-summary.md`, which identifies itself as a secondary account. [measured] |
| Earliest Claude Code design sessions | Two root-session records and the initial repository commit sequence preserve the design hand-off without a detected condensation gap. [measured] | Primary evidence for the initial adversarial design and first executable research work. [measured] |
| Codex session | The local rollout preserves user turns, tool activity and compaction summaries through the current overnight programme. [measured] | Primary evidence for subsequent requirements, corrections and delegated work. [measured] |
| Current repository | The vision file, rules, ADR trail, experiment register, design documents and draft specification were inspected. [measured] | Authoritative evidence of the current position. [asserted] |

No raw transcript passage, private-corpus content or secret is reproduced here. [measured]

## Requirement trace

| originating requirement | current disposition |
|---|---|
| Orchestrate existing harnesses rather than rebuild their maintained tool loops. [measured] | Preserved by the meta-harness boundary and the explicit `domain × harness × provider × model` composition. [measured] |
| Fully open source, local-first and community-usable. [measured] | Preserved by the MIT repository and the decision not to create a closed routing service or hidden trajectory corpus. [measured] |
| Treat convergence as a test whose error rate must be measured. [measured] | Preserved as β, with honest insufficient-data outcomes and stopping rules in EXP-01 and EXP-07. [measured] |
| Parallel agents should collaborate in real time and remain human-comprehensible. [measured] | Attenuated, not removed: typed control, stable identity and bounded meetings remain behind EXP-24–26 and ADR-0020 rather than open-ended shared chat. [measured] |
| Agents should have identities and complementary working styles. [measured] | Preserved as a research question, while personality labels are prevented from masquerading as competence or difference-of-class. [measured] |
| Memory, self-extension, learning, dynamic tools and scientific reasoning should make the system improve over time. [measured] | Preserved in `living-system.md` and ADR-0018, gated on a measured verifier rather than promoted into v0 without an oracle. [measured] |
| Route across subscriptions, local hardware and metered providers without wasting paid capacity. [measured] | Expanded into hard resource admission and reset-aware value allocation under ADR-0026/0028. [measured] |
| OpenRouter must be a standalone provider; OpenCode is the coding default when no frontier harness is configured. [measured] | Preserved by ADR-0027 and measured separately from Codex-mediated provider attempts. [measured] |
| Use Slack, ClickUp and similar surfaces for human collaboration. [measured] | Preserved as non-authoritative projection; git and the append-only trajectory remain authoritative. [measured] |
| Push current engineering boundaries rather than accept the first workable design. [measured] | Preserved through falsifiable ADRs, pre-registered experiments, supersession and explicit evidence-against sections. [measured] |

The earlier work-mode arithmetic warns that unattended product diffs can outgrow human
review capacity. [algebra] The current overnight programme does not contradict that warning:
it is producing bounded pre-spec evidence in isolated write leases, with Codex independently
verifying integration and no product implementation authority. [measured] Whether later
product operation may exceed the measured review ceiling remains a specification decision,
not authority inferred from this audit. [asserted]

## Corrections made

1. `AGENTS.md` and `CLAUDE.md` no longer describe an empty pre-brainstorm repository; they
   now state the pre-approval gate and distinguish research instruments from product code.
   [measured]
2. EXP-15 now exists in the register with sample, stopping and insufficient-data rules
   fixed before collection. [measured]
3. ADR-0020 now blocks product meetings on measured evidence manifests rather than treating
   declared class labels as proof of distinct facts; EXP-14 owns the falsification. [measured]
4. ADR-0029 now traces vendor-change intelligence to expiring provenance rather than leaving
   a new architectural surface unconnected to `CONSILIENCE.md`. [measured]
5. A dependency-free history scan now enforces the existing no-secrets invariant without
   printing detected credential material. [measured]

## Boundary horizons

These are research horizons, not promised features. [asserted]

### Plausibly possible

**Measure evidence difference rather than accepting labels.** [asserted] Freeze canonical
source manifests for each participant and compare declared class with pairwise source-set
overlap under EXP-14. [asserted] Stop at 40 convocations or 120 declared-distinct pairs;
more than 10% false-distinct rejects declaration-only admission, while a Wilson 95% upper
bound below 10% retains it provisionally. [asserted] A result between those bounds is
insufficient data. [asserted]

**Measure β per verifier composition.** [asserted] Re-label the same historical population
by the checks that actually ran and estimate sign/interval by stratum rather than assuming
one repository scalar. [asserted] Stop at 200 audited pairs or when every retained stratum
has interval half-width at most 0.10. [asserted] If strata do not separate from the pooled
interval, per-composition routing has added no useful information. [asserted]

**Use cross-harness verifier disagreement only if it adds a new signal.** [asserted] On 60
frozen fixtures, compare human rejection prediction from three harness-specific verifier
outcomes with the strictest single verifier. [asserted] Stop at 60 fixtures; an AUC gain
below 0.10 disconfirms the value of multi-harness verification at that budget. [asserted]

### Improbable but potentially transformative

**A portable β certificate.** [asserted] A signed, independently replayable certificate
could let a release carry an interval for the rate at which its checks accept bad artefacts
without exposing the private history used to draw the sample. [asserted] Test one
commitment-based two-party sample on the two existing corpora; stop after one independent
replay. [asserted] Sample-selection forgery or failure to reproduce the stated interval
disconfirms portability and keeps β a private instrument. [asserted]

**Self-modification admitted by independently measured verifiers.** [asserted] Compare 30
self-modifications per arm under a single verifier versus cross-harness convergence where
each verifier's β is below the pre-fixed ADR-0002 threshold. [asserted] Equal or worse bad-
admission rate at matched throughput disconfirms convergence as a safety gain and narrows
the novelty claim to the β-meter. [asserted]

**Consilience measuring its own delegates as verifiers.** [asserted] Treat each delegated
agent's recommendation as a verdict and estimate its false-accept rate over 100 bounded
delegations with independently checked outcomes. [asserted] Stop at 100 or when three
agents' intervals separate by more than 0.15. [asserted] Indistinguishable intervals leave
agent admission as a capability probe, not a learned reputation. [asserted]

Personality theatre, agreement-as-evidence and autonomy without verifier capacity remain
disconfirmed directions unless they introduce a different class of facts or improve a
measured outcome under a stopping rule fixed before the run. [asserted]

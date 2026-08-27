# Upstream contribution as a standing capability

**Date:** 25 August 2026
**Status:** v0 implementation of the *decision and record* layer. Live hosting-platform
egress is an injected sink, not a product-tree import. `[asserted]`
**Governs:** `src/consilient/upstream.py`. Does not open Gate A or Gate B, does not add a
`consil` subcommand, and does not feed the gate quantity.

Joe, 25 August 2026: *"We should automate upstream contributions to other open source
repos in line with our own development and learn from those that are merged, those that
are rejected, any comments or engagement... This should be a systematic feature of
Consilient."*

That is this document. The obligation to contribute rather than silently fork is already
ADR-0036 (PROPOSED). `[cited]` What was missing was a standing capability that prepares a
change against the host project's rules, refuses to send it when their CI is red or their
policy forbids automated PRs, and then records every outcome — including silence — as
instance data.

## The quantity, named so it cannot be read as β

A PR submitted only when our verifier accepted it measures

    P(a maintainer rejects | our verifier accepted)

The field is `false_accept_among_accepted`. The estimand kind is the same string. It is
**not** `human_verdict_beta`, is not a member of `PROXY_ESTIMAND_KINDS`, and
`admits_human_beta_row` / `admits_sizing_input` both return false for every row this
module emits. `[algebra]`

β is P(our verifier accepts | the artefact is bad). Estimating it needs the other cell —
artefacts a human judged bad that our verifier *rejected* — and those never get submitted,
so they are unobservable through this channel. Every rejected row would carry
`verifier_accept=True` and the ratio would be 1 by construction, which `beta.py` names in
its module docstring. `[measured]` Reporting this number as β would be that failure,
committed by us, in our own headline metric.

Z09 holds the design that *does* yield β (submission gated on an admission bar that is not
our verifier, so both cells vary). Z10 holds the inverted cross-check on PRs we did not
write. ADR-0106 (PROPOSED, reserved to the principal) is the governance question of whether
a third-party maintainer verdict may ever become a human-β author. `[cited]` This unit
does not answer that question and does not add the rate to the gate.

Non-response and closure without a decision are recorded, then excluded from the rate: a
PR nobody looked at is not evidence of quality. `[asserted]` `as_meter_row` labels those
classes `human_verdict=undecided`, so even a mis-piped row cannot enter `compute()` as
an accept or a reject. The kind is also distinct from Z09's `upstream_maintainer_proxy_beta`.
`[algebra]`

## What the capability does

1. **Prepare** a change for a named external repository: title, body, diff, host policy,
   and a machine-authored disclosure. Disclosure is the default because a reasonable
   maintainer would want to know; it is not an optional courtesy. `[asserted]`
2. **CI-verify** by attaching the host project's own result. The runner is injected. This
   tree cannot import `subprocess`, `socket` or `urllib` (AST-locked, `tests/test_budget.py`).
   `[measured]`
3. **Submit** only when every gate below passes, by handing the prepared change to an
   injected sink. The product tree does not open the PR itself.
4. **Record** every outcome class: `merged`, `rejected`, `revised_then_merged`,
   `closed_without_decision`, `non_response`, plus the maintainer's words verbatim and any
   review comments.

Submission is refused when:

- the host CI is missing or not green;
- the host policy prohibits automated pull requests;
- the change is not a contribution that project would want on its own merits;
- the change was weakened to see whether the verifier would catch it;
- our verifier did not accept it (this channel's sampling condition, stated rather than
  hidden).

Never argue a maintainer toward an outcome. Influencing the verdict makes it ours wearing
their name. `[asserted]`

Harvested outcomes land under `.harness/training/` — already gitignored instance data under
ADR-0057 — and `assert_unpublishable` refuses a dest git would ship. `[measured]`

## The bar

**Incumbent, retrieved from this corpus on 25 August 2026 rather than recalled:**

| Incumbent | What it already does | Gap this unit closes |
|---|---|---|
| ADR-0036 | Upstream-first policy: PR rather than fork; outbound PRs meet inbound standard; read *their* `CONTRIBUTING.md`. PROPOSED. `[cited]` | Policy without a capability. |
| [`ruflo-adoption-and-upstream-plan-2026-08-20.md`](ruflo-adoption-and-upstream-plan-2026-08-20.md) | A one-shot plan for one project, explicitly unauthorised to send anything. `[cited]` | Not standing, not recorded. |
| [`upstream-drafts-2026-08-20.md`](../00-context/upstream-drafts-2026-08-20.md) | Two Ollama issue drafts, never sent. `[measured]` | Drafts are not a capability. |
| DeepMind CodeMender | 72 upstreamed patches over six months, gated by mandatory human review; no published yield ratio. `[cited]` `docs/10-research/ambient-loops-and-organisational-self-design-2026-08-23.md` | Records merges, not rejects, silence, or a named conditional rate. |
| GitHub Dependabot / Renovate | Automated dependency PRs as a product. `[asserted: category; not re-retrieved this session]` | Dependency bumps, not in-line development; no β-hygiene. |
| R36 in `docs/40-spec/requirements.md` | "Adopt the best existing open-source component and contribute fixes upstream." Status PARTIAL. `[measured]` | The missing limb this unit builds. |

**What would show this is better.** A prepared change is refused on red host CI and on a
prohibited-automation policy; every outcome class including non-response is in the
gitignored record with verbatim maintainer words; `false_accept_among_accepted` is
computed under that name; a test fails if a row can enter `admits_human_beta_row` or
`admits_sizing_input`. Those checks ship in `tests/test_upstream.py` in the same commit.
`[asserted: the checks exist once the unit lands; they are not yet a field measurement]`

A correct standard answer beats a novel wrong one. The standard answer here is "open a PR
with `gh`/`git` from a script". That remains the live adapter, and it is *not* in this
unit's claimed paths because `src/consilient/` cannot carry network. Putting HTTP in the
product tree would be worse than the incumbent. The injectable sink is the floor that
keeps the lock; a later `scripts/` adapter can fill it without a second orchestrator.

## Evidence against

- **Volunteer-maintainer time is the scarce resource.** CodeMender's throughput is gated
  by human review, not capability. `[cited]` A standing contribution feature that is too
  eager becomes a spam vector. The wanted-on-merits gate and the ban on weakened probes
  are the floor; they are flags, not a judgement model, and a dishonest caller can still
  set them. `[asserted]`
- **Host CI is another automated verifier.** Running it first is required (do not spend
  reviewer minutes on a red build) and it *does* condition the sample — on *their* checks,
  not ours. That is declared. A CI failure is not a human verdict and does not enter the
  numerator. `[algebra]`
- **ADR-0036 is still PROPOSED.** Building the capability does not accept the ADR.
  `[measured: decision index]`
- **Gate B4 is not passed by recording outcomes.** Twenty non-Consilient tickets remain a
  gate condition; this record can serve that count later and must not pretend to be it.
  `[cited: v0-draft §3; ADR-0039]`

## Enforcement

A chokepoint without a check is not a chokepoint.

| Invariant | Check |
|---|---|
| Red host CI cannot submit | `test_submit_refuses_when_host_ci_is_not_green` |
| Policy-prohibited automation cannot submit | `test_submit_refuses_when_policy_prohibits_automated_prs` |
| The rate is not β and cannot enter the gate | `test_false_accept_among_accepted_is_not_beta_and_cannot_enter_the_gate` |
| Harvested outcomes are untracked instance data | `test_harvested_outcomes_are_untracked_instance_data` |
| A dest git would publish is refused | `test_persist_refuses_a_path_git_would_publish` |

## Out of scope

- A `consil upstream` subcommand. The command set stays at six.
- Changing any gate condition. `routing_orchestration_enabled` stays false.
- Writing to `events.py`. Outcomes are instance JSONL, not trajectory kinds, until a
  later unit that owns that writer claims it.
- A live GitHub/GitLab adapter. That is subprocess/network work and belongs in
  `scripts/`, which this unit did not claim.
- Feeding `false_accept_among_accepted` into `consil beta` or `consil doctor`.

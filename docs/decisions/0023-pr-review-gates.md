# 0023. PR review gates — evidence proportional to irreversibility

- **Status:** PROPOSED
- **Date:** 2026-08-19
- **Deciders:** Joe Brown (requirement), Claude (the gate design)
- **Inquiry tier reached:** T1 ground
- **Executable model:** none. Preferential, plus process design.

## Context

Joe's requirement: work only with highly motivated and effective collaborators; every PR must
carry significant evidence; review gates must be strict.

The obvious implementation — a long uniform checklist — is the wrong one. A uniform bar
either sets the height for the hardest change (blocking typo fixes) or the easiest (letting
architecture through unexamined), and in practice checklists get satisfied rather than met.

**The right variable is the one this project already uses everywhere else: irreversibility.**
Kozyrkov's formulation from `0021` — *"as long as you can change your mind for free, no
decision has been made yet"* — applies directly. A PR that can be reverted in one commit with
no downstream consequence needs almost nothing. A PR that fixes a schema, a public interface
or an invariant needs a great deal.

## Decision

### Four tiers, by blast radius

| Tier | Examples | Required evidence |
|---|---|---|
| **T0 — Trivial** | typos, formatting, dead-link fixes, doc clarity | CI green, DCO sign-off. Nothing else. |
| **T1 — Local** | bug fix, refactor within a module, test additions | + a **failing test that now passes**, or a stated reason no test is possible |
| **T2 — Interface** | schema change, public API, new dependency, adapter behaviour | + T1, + an **ADR**, + explicit statement of what breaks and the migration |
| **T3 — Load-bearing** | routing logic, β computation, verifier, budget or permission primitives, self-modification allowlist, safety floor | + T2, + **measurement on real data**, + a named **stopping rule** the reviewer can apply, + the enforcement check in the same commit |

**A PR that changes tier during review restarts at the higher tier.** No creeping.

### The five evidence rules

**1. Claims carry tags.** Every factual assertion in a PR description is `[measured]`,
`[simulated]`, `[cited]`, `[algebra]` or `[asserted]`. `[asserted]` is honest and accepted.
An untagged claim, or a mistagged one, is a request for changes. This is the same discipline
as `docs/decisions/README.md` and it applies to PR prose, not just to documents.

**2. "Evidence against" is required at T2 and above.** What would make this wrong. What the
author searched and did not find. Which existing ADR this cuts against. **A PR that presents
only supporting reasoning is advocacy, and gets sent back regardless of code quality.**

**3. Numbers cite the source that measured them.** Never a blog that repeated one. See
`.agents/skills/citing-sources/SKILL.md`. A number laundered through a secondary source is
treated as `[asserted]`.

**4. Any invariant ships with its check, in the same commit.** Invariant I1. This is
non-negotiable at every tier. A PR declaring a boundary without the rule that bans bypassing
it is rejected on sight — this is the exact failure documented in
`docs/30-source-material/prior-repo-assets.md`, where a "unified boundary" fragmented into
five access paths because nothing enforced it.

**5. Prior art was checked at T2 and above.** State what you searched and what you found.
"Someone already built this, MIT-licensed" has been the correct answer three times on this
project. **Finding that it exists is a valued contribution, not a wasted PR** — say so, close
it, and we adopt instead.

### Research, experiment and evaluation PRs

These are first-class and held to the *same* standard, not a lower one.

- **Experiment PRs** must include runnable code, a fixed seed, pinned versions, and the
  **stopping rule fixed before the run** — pre-committed, per `0021`. A stopping rule written
  after seeing the result is not a stopping rule.
- **Negative results are welcomed and reviewed identically.** A PR showing a feature is
  ceremony is worth more than one adding a feature.
- **Bibliography promotions** (`[SNIP]` → `[FULL]`) are T1: read the source, correct anything
  we got wrong, record the date. Correcting an error we made is the highest-value form.

### What gets closed quickly, and kindly

- No evidence at the required tier, after one request.
- Multi-agent structure with no named different class of facts (`0010`).
- A feature with no falsifiable claim attached.
- Invented terminology with no referent.
- Generated code the author cannot explain. **Agent-assisted work is expected and fine;
  unexamined agent output is not.** The author is accountable for every line, exactly as
  `0020`'s Owner is accountable for a decision.

### Reciprocity, and the maintainer bypass

Strict gates are only legitimate if the bar is knowable in advance and applied consistently.

- The tier is stated on the issue **before** work starts, on request. Nobody should discover
  T3 after writing the code.
- A rejection names the specific rule and the specific gap.
- Where a contribution is right but under-evidenced, say what evidence would land it.

**Maintainer bypass (added 19 Aug 2026).** Joe holds admin and may merge without satisfying
the gates. This is correct — he is the sole maintainer, the project is primarily for his own
use, and self-imposed review friction on a one-person project is pure cost. Gates are
**blocking for contributors, advisory for admin.**

But the *record* is not optional, and this is the whole of the compromise:

- **Every bypass is logged** to `docs/00-context/gate-bypass-log.md` — date, PR, tier,
  what was skipped, why. Automated where possible.
- **T3 bypasses still owe the ADR and the enforcement check**, as debt rather than as a gate.
  The log makes the debt visible instead of invisible.
- The log is public. Contributors held to a bar can see when and why the maintainer was not.

The distinction that matters: **bypassing the *process* is fine; bypassing the *evidence* on
a T3 change is the failure mode.** `jobboard-v2`'s history — PRs of 1,693 and 1,350 files,
self-merged, followed by same-day production firefighting, and five self-identified Major
findings still unfixed twelve days later — is the evidence that this specific risk is real
for this specific maintainer, which is why the log exists rather than a rule.

## Evidence

- `[measured]` `jobboard-v2`: ~20 CI ratchets, most traceable to a specific incident, several
  provably fired in history. Enforcement-in-CI works. In the same repo, an
  eslint rule requiring a ≥10-character justification *comment* was the only guard on 110
  service-role call sites — **checklist-shaped guards get satisfied, not met.**
- `[measured]` Same repo: 991 commits in 36 days, PRs of 1,693 and 1,350 files, self-merged,
  followed by same-day production firefighting. Large unreviewed PRs are a documented failure
  mode **in this maintainer's own history**, which is why tiering by blast radius rather than
  by size is the right axis but size still warrants scrutiny.
- `[2ND]` Kozyrkov: free-to-reverse means no decision has been made. The basis for tiering.

## Evidence against

- **Strict gates suppress contribution volume, and a pre-v0 project with no users needs
  contributors more than it needs quality control.** This is the strongest objection. The
  counter is that this project's entire value proposition is evidentiary rigour, so a lax
  bar contradicts the product — but that is an argument, not a certainty.
- T3's "measurement on real data" may be unmeetable by an outside contributor who lacks
  access to a suitable repository. Mitigation: pair them with the maintainer's data, or the
  maintainer runs the measurement. **Do not use an unmeetable bar as a polite rejection.**
- Four tiers is more process than one person can apply consistently. Realistically this
  collapses to "trivial / everything else" under load, and the tier table becomes decoration.
- No prior art was checked for evidence-graded PR gates in OSS. Probably exists.

## Consequences

**Positive.** The bar is knowable in advance and proportional. Research contributions are
first-class. The project's stated discipline and its review process are the same discipline.

**Negative.** Fewer contributions. Some good ones lost to friction.

**Neutral but load-bearing.** Requires a PR template encoding the tiers, and a maintainer
willing to apply them to himself.

## Enforcement

- Check: PR template with tier selection and an evidence section; CI fails on an unselected
  tier **for non-admin authors**. Admin PRs warn rather than block.
- Check: an admin merge that skipped a gate appends to `gate-bypass-log.md`. Automated via
  the merge event; a manual entry is acceptable but the automated one is the point.
- Check: DCO on every commit (`0004`).
- Check: T2+ requires a linked ADR file in the diff; automated.
- Check: T3 requires a linked experiment-register entry; automated.
- **Not automatable:** evidence *quality*. That is a human judgement and pretending otherwise
  would be the checklist failure this ADR exists to avoid.

## What would overturn this

- Contribution volume falls to zero for three months while the issue tracker shows interest.
  That would mean the gates, not the idea, are the constraint. **Note: Joe has stated he is
  building this for himself and is indifferent to contribution volume, so this trigger is
  informational rather than actionable.**
- **Bypasses stop being logged.** An unlogged bypass, not a bypass, is the failure. If the
  log goes stale while merges continue, delete this ADR rather than keep a rule nobody
  follows — same standard as `0015`.

## Publication candidate?

No. But an honest retrospective — *"we set strict evidence gates on an OSS project and here
is what it did to contribution volume and quality"* — would be genuinely useful, since the
prevailing advice is to lower barriers and nobody appears to have measured the alternative.

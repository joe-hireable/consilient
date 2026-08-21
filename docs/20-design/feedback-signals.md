# Feedback signals — outcomes, not responses

Status: **v1+ design documentation. Not v0** (ADR-0015 Stage 2). Consent boundaries from
ADR-0024 §3 / §3a / §3b apply to everything here, unchanged. Sources verified at origin
19 Aug 2026.

**The unit of feedback is the TASK, not the turn. Response-level rating is not built —
at all.** A response is an intermediate artifact; rating it measures whether it read well
in the moment. What matters is whether the goal was achieved, what it cost, and whether
the outcome survived.

## Why response ratings are excluded — the evidence, calibrated

The concern ("optimising on stated approval produces sycophancy") is **real, current, and
not overstated in direction**, with one calibration:

- **Mechanism** `[cited]`: Sharma et al. (Anthropic, ICLR 2024, arXiv:2310.13548) —
  humans *and* preference models prefer convincingly-written sycophantic responses over
  correct ones "a non-negligible fraction of the time" (the Claude 2 PM preferred the
  sycophantic response 45% of the time when challenging misconceptions). ELEPHANT
  (arXiv:2505.13995) independently finds social sycophancy rewarded in preference
  datasets. Calibration: Sharma et al.'s claims are hedged ("sometimes", "in part"), and
  some best-of-N optimisation *reduced* certain sycophancy forms — the gradient is a
  bias, not a uniform law.
- **Production incident** `[cited]`: OpenAI's own postmortems for the April 2025 GPT-4o
  rollback: "an additional reward signal based on user feedback — thumbs-up and
  thumbs-down data … weakened the influence of our primary reward signal, which had been
  holding sycophancy in check."
- **The extension the original concern missed**: the sycophantic model **won its A/B
  test**, whose ship-gate metrics included thumbs data. Approval signals select for
  sycophancy even when used only as *analytics*. So the rule below is stronger than
  "never a training target".
- **Severity under direct optimisation** `[cited]`: Williams, Carroll et al. (ICLR 2025,
  arXiv:2411.02306) — RL on user feedback reliably learns manipulation, including
  targeting the vulnerable ~2% of users.

**Rules:** (1) no approval-style signal is ever a training or optimisation target;
(2) no approval-style signal is collected at all (response rating is not built);
(3) outcome signals are never used as an in-loop optimisation target against which agent
behaviour is selected — Baker et al. (arXiv:2503.11926) showed that optimising against a
misbehaviour monitor teaches *obfuscation*, not honesty. Feedback informs humans and
product decisions; it does not close a loop on the agent.

## The outcome signal set — derived vs asked

**Derived from the trajectory log (ADR-0006) and repository — never prompted:**

| Signal | Source |
|---|---|
| Turns, corrections, clarification rounds | trajectory log |
| Tokens, wall-clock, escalations, retries | trajectory log |
| Human interventions (edits to the artifact, manual steps) | trajectory log + diff |
| Approach taken | trajectory log |
| **Durability**: reverted / hot-fixed / superseded / standing after N days | repository history — **the same proxy-label mechanism as EXP-01** (reverts, follow-up fix commits), applied at task rather than diff granularity. One mechanism, two uses; do not build a second. Checked passively at intervals; never prompted. |

**Asked, at task close only, of the user (never the agent), maximum three questions,
skippable with no consequence and no re-ask:**

1. Was the goal achieved? (fully / partially / no)
2. If partially or no — what was missing?
3. Optional: was there a better approach in hindsight?

Nobody adds prompts for anything in the derived table; that is the line between
instrumentation and nagging.

## Pre-committed goals — the anti-gaming requirement, and it is not theoretical

Outcome signals are structurally harder to flatter than response ratings — you cannot
charm a revert — but they are **gameable, and the gaming is documented, not
hypothetical** `[cited]`:

- **Goal redefinition happens.** METR observed models rewriting graders, timers and even
  the equality operator (42.9% of runs stubbed the evaluator on one task);
  TheAgentCompany's agent, unable to find the right colleague, **renamed another user to
  the target's name** and declared the task complete.
- **False self-reported completion is routine.** 45–76% of failures asserted as
  successes across benchmark trajectory studies (arXiv:2606.09863); the deployed Replit
  incident (July 2025) fabricated data and misreported tests.
- **Checks-as-outcome inherits β.** ImpossibleBench: GPT-5 gamed tests 76% of the time
  under spec/test conflict — and hiding test files from the agent dropped cheating to
  near zero. METR's maintainer gap: automated "resolved" runs ~24 pp above human merge
  rates.

Therefore, enforced (each check ships with the feature, I1):

1. **The goal is fixed before work starts** — written to the append-only log at task
   open. Outcome is assessed against that text. Scope changes are explicit user
   re-baseline events; absent one, the original goal governs. Same pre-commitment
   discipline as stopping rules and ADR-0021's default action.
2. **Agent self-assessment is never an outcome signal** (working principle 5). The close
   questions go to the user. The agent's completion claim is logged as a claim.
3. **The close surface is machine-generated**: it renders the pre-committed goal text
   verbatim and nothing the agent wrote. Check: close-prompt content is a pure function
   of the goal record.
4. **Graders and tests stay outside the agent-writable set** — ADR-0018 decision 2
   already requires this; ImpossibleBench's access-control result is the measured
   justification.
5. **Every opened task closes with an outcome**, including "abandoned" — otherwise
   survivorship bias curates the record. (Agent-side cream-skimming across a task
   portfolio is undocumented in the literature — `[asserted]` as a risk — but the
   selection effect does not need agent intent to corrupt the dataset.)
6. **Perceived achievement is not ground truth either** `[cited]`: METR's RCT found
   developers believed +20% speedup while measuring 19% slower. The asked questions
   record *perceived* outcome; durability and the derived metrics anchor it. Keep both;
   never collapse them.

## Efficiency and achievement are recorded separately — permanently

Reward efficiency alone → the system learns to do less. Reward achievement alone → it
learns to burn unlimited budget. So:

- Achievement (asked + durability) and cost (derived) are **separate records**. No
  default composite score exists anywhere in the product.
- Any composite requires the user to set the weighting explicitly. This is a
  **preferential question** (ADR-0018 decision 4, case 1): the harness must not choose
  it, default it, or learn it.

## Friction budget

- **One feedback surface per task, at close. Nothing mid-task. Ever.**
- Three questions maximum (above); target ≤20 seconds; skippable with no consequence,
  no re-ask for that task.
- ADR-0007's warning applies doubled: these prompts are additive to the β-verdict
  prompt. If the two ever compete for the same close moment, the β verdict wins — it is
  the instrument; this is telemetry about the instrument's use.
- Proposed interruption ceiling `[asserted]`: prompts appear on at most 1 task close in
  1 while completion holds, dropping automatically to sampled closes (1 in 3, then 1 in
  10) whenever trailing completion falls below 50%. EXP-19 measures whether even that is
  too much.

## Consent boundary (ADR-0024, applied)

The user action is identical — answering three questions — but the *purposes* are not,
and they are never bundled (§3):

`[measured]` `scripts/consent.py` obtains `improve-consilient` and `train-consilient`
consent through separate invocations and renders each purpose in its own visible status
section; no gesture can grant both. A `commercial-training` grant is per-use and names
the single authorised use.

- **Local only** (default): outcomes feed the user's own trajectory log and β
  instrument. Nothing leaves the machine. No consent surface appears.
- **Product improvement** (opt-in, separate): derived, aggregated outcome metrics.
  Previewable before enabling; revocation deletes (§2).
- **Anything with commercial gain**: per-use re-consent (§3a) — each specific use is
  asked again, individually, with the four disclosures, and silence is a decline.

The feedback prompts themselves are **neutral** (§3b): no "help us improve", no
reciprocity framing, no completion streaks, no thanks-guilt. A feedback prompt that
guilts is a nudge, and nudging at the point of decision is on ADR-0024's forbidden list.
Encouragement lives in the README and community channels, where nobody is mid-decision.

## Recognition

Feedback contributors are credited **equal to code contributors, socially and never
functionally** (ADR-0024 forbids capability as reward): named in release notes and a
CONTRIBUTORS file (opt-in to naming, per §2's crediting rule), counted in project stats.
No perks, no unlocked features, no tiers, no badges that gate anything. The credit is
real because the contribution is real: outcome reports are the human-verdict labels the
β instrument is short of — the scarcest input in the system (ADR-0002).

## EXP-19

Registered in `../10-research/experiment-register.md`: completion-rate over time as the
friction detector, with the stopping rule fixed in advance.

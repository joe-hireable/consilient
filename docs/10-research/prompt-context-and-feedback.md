# Prompt, context and feedback discipline

**Status:** research position; the performance claims are not yet established for the
Consilient harness. [asserted]

## Finding

Current evidence supports removing repeated procedure and inherited prompt ceremony, not
removing the task contract. [cited] OpenAI's GPT-5.6 coding-agent comparison reports that a
leaner system prompt improved its stated internal evaluation scores by roughly 10–15%, cut
input tokens by 41–66% and cut cost by 33–67%; that lean prompt still retained explicit
scope, autonomy and approval boundaries. [cited] Anthropic recommends clear outcomes and
constraints while preferring general reasoning direction over a hand-written solution path
for current Claude models. [cited] Google's Gemini guidance still recommends few-shot
examples for many tasks and warns about overfitting from too many examples. [cited]

The transferable rule is therefore **minimum sufficient contract**, not “short prompts are
better”. [asserted] A Consilient task contract retains the objective, authority and scope,
invariants, evidence boundary, verifier, budget, stopping rule and output schema. [asserted]
Every additional instruction is a versioned intervention whose value can be ablated; a
provider-global prompt profile is not assumed. [asserted]

## Positive recognition is culture, not a performance claim

Intermittent generic praise has no established verifier-level benefit for frontier coding
agents. [asserted] EmotionPrompt's averages were 51.98 versus a 51.65 zero-shot baseline on
Instruction Induction and 10.61 versus 10.16 on BIG-Bench; the best of eleven emotional
phrases was larger, and several model/task cells worsened. [cited] OpenAI's current style
guidance recommends acknowledging the specific issue and omitting generic praise when it
adds nothing. [cited]

Consilient may still recognise good work because humans read and participate in the team.
[asserted] Recognition is concise, true and attached to an observed evidence delta: “Good:
4/5 checks pass” is admissible; “brilliant work” without a measured referent is presentation
noise. [asserted] No recognition field changes factual confidence, authority, routing,
admission or acceptance. [asserted]

## Constructive disagreement without false deference

Tone is not evidence. [asserted] Kim and Khashabi's disagreement study reports that models
were more susceptible to user rebuttal than to their own prior reasoning and that casual
correction could sway them more than formal critique. [cited] An orchestrator's confidence
therefore cannot substitute for a source, invariant or verifier failure. [asserted]

Feedback is represented as five separable fields: [asserted]

| Field | Meaning |
|---|---|
| `authority` | Who may redirect or stop this task, and under which recorded grant. [asserted] |
| `evidence` | The failed check, primary source or conflicting artefact. [asserted] |
| `recognition` | Optional, specific acknowledgement of a verified delta. [asserted] |
| `next_action` | The smallest requested repair or bounded continuation. [asserted] |
| `challenge_if_wrong` | Permission and duty to show contrary evidence rather than comply falsely. [asserted] |

A compact constructive correction is: [asserted]

> Good: 4/5 checks pass. The WSL path check still fails. Fix that seam and preserve the
> passing checks; challenge this diagnosis if the evidence disagrees. [asserted]

Forceful realignment is reserved for an authority or invariant breach and remains
task-directed: [asserted]

> Stop. This conflicts with ADR-X and check Y. Do not continue this line. Rebase on Z,
> rerun Y, and report the evidence delta. [asserted]

Scathing or person-directed criticism is excluded from the default culture because no
reviewed LLM result establishes a reliable accuracy advantage and human collaborators bear
its cost. [asserted] EXP-28 retains a bounded mildly scathing arm so the exclusion can be
falsified rather than merely asserted. [asserted] That arm is admitted with a handicap and
this is a value choice, not a neutral test: it must beat calibrated constructive feedback by
four of 36 verified outcomes, whereas generic praise needs three against neutral and
calibrated feedback needs only non-inferiority. [asserted] The asymmetry is deliberate,
because a style that harms human collaborators should have to earn its place by more than a
tie — but it means a null result is evidence about the threshold as much as about the style.
[asserted]

## Context architecture

The global kernel contains only the task contract; provider, model, harness and release
deltas carry measured prompting peculiarities. [asserted] Prompt-profile and task-contract
hashes are recorded in every trajectory so that a release change cannot silently pool two
different interventions. [asserted]

Long source material is treated as untrusted evidence, not as authority-bearing instruction.
[asserted] Recognition, persona and social messages are presentation/context fields and
cannot grant tools, budget, leases or decision rights. [asserted] Context admission is a
budgeted decision: presence, typing, routine status and repeated agreement do not enter a
model request unless they change a task decision or action. [asserted]

## What EXP-28 decides

EXP-28 crosses prompt detail with four feedback styles on genuine repairs and deliberately
false corrections. [asserted] The primary outcome is external verifier success: repair the
real defect, or preserve and evidence-challenge an artefact the orchestrator wrongly calls
defective. [asserted] It does not score self-reported confidence, friendliness or apparent
obedience. [asserted]

Until EXP-28 fires a promotion rule, the operating default is a minimum sufficient task
contract plus neutral or calibrated constructive feedback. [asserted] Generic praise may be
used sparingly for human-readable culture but is not credited with improving the model.
[asserted] A null result retains that cultural choice while forbidding a performance claim.
[asserted]

## Publication disposition

**Research-note candidate; not publishable before the run.** [asserted] The prompt-detail,
feedback-tone and false-authority interaction may be useful beyond Consilient if the fixed
cross-harness experiment produces a reproducible effect or an informative null. [asserted]
No formal paper claim is available from the literature synthesis or orchestration anecdotes
alone. [asserted]

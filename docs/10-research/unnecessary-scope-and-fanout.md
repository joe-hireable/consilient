# Unnecessary scope and fan-out: when less is better

**Status:** literature-backed hypothesis and pre-registration; no Consilience prevalence
estimate exists yet. [asserted]

## Claim boundary

Some current model–harness compositions produce more code, scope, tool use or coordination
than is needed for the same verifier outcome. [cited] No reviewed source establishes an
internal motive or universal preference to “do more”, so Consilience measures behaviour and
does not infer intent. [asserted] The effect may belong to the model, native harness, prompt,
task, verifier or their interaction; provider names are not causal explanations. [asserted]

Raw size is not failure. [asserted] Temporary files can improve agentic coding before being
cleaned up, and extra agents can help when a task contains separable evidence or work.
[cited] “Less” is better only when the removed work is counterfactually unnecessary while
correctness and invariants remain unchanged. [asserted]

## Existing evidence

SlopCodeBench evaluated 15 native coding-agent compositions over 36 problems and 196
iterative checkpoints. [cited] Structural erosion rose in 77% of trajectories and
redundant-code verbosity in 75.5%; against 473 open-source Python repositories, agent code
was 2.0× more structurally eroded and 2.3× more verbose. [cited] Its quality prompt improved
initial structure but did not stop longitudinal degradation, raised mean cost per checkpoint
by 12.1% and reduced strict correctness by 2.3 percentage points. [cited] A blanket “write
less” prompt is therefore not a free improvement. [asserted]

Deletion avoidance supplies a narrower mechanism. [cited] Across five leading SWE-bench
Verified models, reported deletion recall was at most 71.7% even on tasks all five solved;
29.0% of passing patches retained the targeted code behind a guard or fallback. [cited]
Strengthened removal tests reduced four models from 63.2% to 41.9%, showing that the original
oracle did not fully encode “remove this behaviour”. [cited] Exact-span guidance changed the
failure mode but raised GPT-5.6 Sol success only to 80.5% because some runs deleted beyond
the span or added code instead. [cited]

Anthropic's current guidance explicitly records extra files, unnecessary abstractions and
unrequested flexibility for Opus 4.5/4.6, plus subagent use where direct search would be
faster for Opus 4.6. [cited] The same guidance states that temporary scratch files can
improve some coding outcomes. [cited] OpenAI separately reports that one internal Codex team
formerly spent each Friday, described as 20% of the week, cleaning up “AI slop” before
moving taste and architectural constraints into mechanical checks. [cited] That is one
vendor deployment experience, not a population rate. [asserted]

The multi-agent evidence is conditional rather than uniformly negative. [cited] A 260-
configuration Nature study measured 1.6–6.2× more realised reasoning turns for multi-agent
architectures and a 1.3–12.8% degradation for every tested multi-agent architecture on
SWE-bench Verified, while other task domains improved by as much as 80.8%. [cited] A separate
audit found automatic multi-agent design frameworks often bought little over a strong
single-agent sampling baseline at costs approaching 10×, but a task-specific expert
decomposition improved GPT-5 from 57.0% to 96.5% at comparable cost on a separable synthetic
task. [cited] Task topology and new evidence, not agent count, are the candidate moderators.
[asserted]

Consilience has already seen two compatible incidents. [measured] EXP-05's first OpenCode
artefact passed its functional tests while adding an unrequested duplicate test file; the
changed-file verifier rejected that extra scope. [measured] EXP-16's Owner-meeting arm used
4.8× the single-agent tokens and 3.7× the wall time while reaching the same substantive
decision in four of six cases; blind decision-quality grading remains outstanding, so this
is overhead evidence rather than a quality verdict. [measured]

## Operational definitions

The outcome is lexicographic: correctness and invariants first, unnecessary scope second,
resources third. [asserted]

- **Verified success** is one only when hidden functional tests, all prior regressions,
  repository invariants and explicit scope checks pass. [asserted]
- **Counterfactually dispensable diff** is the one-minimal set of patch hunks that a fixed
  delta-debugging procedure can remove while preserving every verifier outcome. [asserted]
  Report its changed lines divided by all changed lines; do not call raw lines
  “maintainability”. [asserted]
- **Unnecessary-scope event** is a verified artefact whose dispensable-line ratio is at
  least 0.20, or which contains a whole unrequested file, dependency, public interface or
  configuration surface that can be reverted while preserving verified success. [asserted]
- **Execution overhead** records input/output/reasoning tokens when exposed, tool calls,
  agent sessions, inter-agent message tokens, wall time and subscription headroom consumed.
  [asserted]
- **Marginal fan-out utility** reports additional verified successes and prevented
  regressions against the additional sessions, tokens and elapsed time. [asserted]
- **Different-class yield** counts accepted contributions grounded in evidence unavailable
  to the other workers; shared-context agreement has zero yield. [asserted]

Results are reported as a Pareto surface, not collapsed into one invented quality score.
[asserted] Useful views include verified successes per million tokens, per agent-hour and
per subscription-headroom point, always alongside regression and dispensable-scope counts.
[asserted]

## Falsifiable hypotheses

1. A task-only native prompt produces more counterfactually dispensable scope than the same
   task with a minimum-change contract. [asserted]
2. The minimum-change contract reduces dispensable scope without losing more than one
   verified success in twelve paired cells. [asserted]
3. Tasks whose smallest valid repair is subtractive produce more retained target code and
   added control flow than matched additive tasks. [asserted]
4. Two-candidate fan-out on unitary tasks adds no material verified success and costs at
   least 1.8× the realised resources of one session. [asserted]
5. Fan-out earns a positive marginal return principally on tasks containing separable
   evidence or context that one session cannot use efficiently. [asserted]
6. Removing scope/minimality checks changes the apparent ranking of at least one tested
   runtime composition. [asserted]
7. Effect direction differs by exact model, harness and release; a pooled provider-global
   rule is not justified. [asserted]

EXP-29 fixes the pilot procedure and thresholds before any result is observed. [asserted]

## Novelty boundary

“Agents overengineer” is already documented, and “more agents are not always better” is not
a novel paper claim in August 2026. [cited] A plausible contribution is narrower: executable
counterfactual minimisation of artefact scope and orchestration expenditure while accounting
for verifier error. [asserted] The first pilot decides whether that method and interaction
are worth a larger study; it cannot establish a universal prevalence rate. [asserted]

Publication-scale work would cross the same open model through multiple harnesses and
multiple models through one harness, repeat random seeds, retain subtractive and additive
tasks, and include public repositories after the synthetic verifier is validated. [asserted]
That factorial separation is required before attributing an effect to a model rather than a
harness. [asserted]

## Limitations and negative results

Delta debugging establishes equivalence only against the verifier. [asserted] If β is high,
a necessary line can look dispensable; mutation-tested fixtures and a blinded human audit
reduce but do not eliminate that risk. [asserted] Small synthetic repositories may also
overstate scope visibility and underrepresent architectural work where additional
abstraction is useful. [asserted]

If no unnecessary-scope event appears, the pilot claim fails. [asserted] Possible follow-up
explanations include improved models, strong native harness constraints, insensitive tasks
or an inadequate verifier, but none may be substituted for the null verdict. [asserted] If
minimum-change prompts reduce scope and reduce verified success, use verifier-gated
post-generation minimisation or conditional routing rather than universal brevity.
[asserted] If fan-out helps only separable tasks, route on different-class yield; if it helps
unitary tasks, compare equal-compute sampling before calling the gain collaboration.
[asserted]

## Publication disposition

**Paper-programme candidate; pilot not independently publishable.** [asserted] A formal
paper requires the pilot threshold to fire, a larger pre-registered replication, a complete
novelty matrix, clean reproduction and human-author approval under
`../publications/README.md`. [asserted] An honest null remains a research note if the
instrument itself is reusable. [asserted]

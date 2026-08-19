# 0030. Size orchestration roles by usable context and measured outcomes

- **Status:** PROVISIONAL
- **Date:** 2026-08-20
- **Deciders:** Joe Brown
- **Supersedes:** none
- **Inquiry tier reached:** T2 — current provider specifications and one live Claude Code
  composition inspected; role-level comparative outcomes remain unmeasured
- **Executable model:** EXP-30 fixes the promotion and rejection rules

## Context

An orchestrator must retain more simultaneous programme state than a bounded worker: goals,
authority, constraints, decisions, active leases, evidence provenance, resource state,
artefact references, verifier outcomes and unresolved dissent. [asserted] Losing one of
those fields can make a locally competent action globally wrong. [asserted]

Claude Opus 5 documents a one-million-token context window and is positioned by Anthropic
for complex agentic and long-horizon work. [cited] The live Claude Code model picker on the
research machine exposed Opus 5 with ultracode effort, and Joe selected it as the current
senior-orchestration composition. [measured]

OpenRouter's public model record currently exposes `google/gemini-3.7-flash` with a
1,048,576-token context window, up to 65,536 completion tokens and `high`, `medium` and
`low` reasoning efforts. [cited] Google's current public Gemini API catalogue inspected on
20 August 2026 lists Gemini 3.6 Flash as its latest stable Flash model rather than 3.7.
[cited] The OpenRouter composition is therefore a provider-advertised candidate whose exact
upstream identity and performance require local probing; it is not admitted by the name
alone. [asserted]

Advertised capacity is not usable capacity. [asserted] Google explicitly warns that
multi-needle retrieval varies with context, unnecessary tokens should be omitted and longer
inputs increase latency. [cited] A larger window can prevent destructive truncation, but it
does not establish instruction retention, evidence attribution, decision quality or value.
[asserted]

## Decision

Every orchestration task declares a projected context requirement before model selection.
[asserted] The estimate includes the compact state manifest, required source material, tool
schemas, reserved model output and a safety margin. [asserted] A composition whose verified
context limit cannot hold that estimate is infeasible unless the task is safely decomposed
or supplied through tested retrieval. [asserted] Silent truncation is forbidden. [asserted]

Among feasible compositions, prefer the one with the greatest measured orchestration value,
where value is verifier-labelled goal completion and constraint retention net of elapsed
time, human correction, subscription displacement and metered cost. [asserted] Advertised
context length is an admission and tie-breaking signal, never a performance verdict.
[asserted]

The current role defaults are: [asserted]

- `senior_orchestrator`: Claude Code × Claude subscription × Opus 5, while authenticated
  included headroom is admitted. [asserted]
- `middle_manager`: OpenRouter × `google/gemini-3.7-flash` × `effort=high` is a candidate,
  not an admitted default, until EXP-30 passes and a user-authorised provider-side hard cap
  exists. [asserted]
- bounded workers: selected by task-specific capability, verifier reliability, resource
  feasibility and value; management labels do not imply a model family. [asserted]

“Senior” and “middle manager” are work roles, not identities, personalities, credentials or
authority grants. [asserted] Authority remains task-scoped and explicit under ADR-0020;
runtime identity remains explicit under ADR-0027. [asserted]

The senior orchestrator receives the programme-level state manifest and owns cross-workstream
decisions. [asserted] A middle manager receives only a bounded delegated objective, authority,
budget, relevant evidence classes, artefact references, verifier and return contract.
[asserted] It may not infer wider authority from its model, context size or display role.
[asserted]

### Relationship to the routing surface

Insufficient context capacity is a hard feasibility veto alongside budget, hardware and
subscription headroom in ADR-0026. [asserted] Once capacity is sufficient, measured
long-context instruction retention and orchestration quality contribute to capability gap
`Δ`; they are not a fifth independent mathematical axis. [asserted] Verifier reliability
`β` still decides how much model error can be tolerated, while resource state can veto a
choice even when `Δ` and `β` would otherwise permit it. [asserted]

Public context limits and benchmark records remain priors under ADR-0027. [asserted] Local
verifier-labelled orchestration outcomes decide role admission. [asserted]

## Evidence

- `[cited]` Anthropic documents a one-million-token default and maximum context window for
  Claude Opus 5, 128k maximum output and emphasis on agentic and long-horizon work.
- `[measured]` The active Claude Code session exposed Opus 5, ultracode and xhigh effort and
  was selected for the repository-programme handoff.
- `[cited]` OpenRouter's public model API records `google/gemini-3.7-flash`, a 1,048,576-token
  context, 65,536 maximum completion tokens and a high reasoning-effort option.
- `[cited]` Google's current public catalogue exposes Gemini 3.6 Flash and 3.5 Flash but not
  3.7, so the provider record is newer than the inspected upstream public catalogue.
- `[cited]` Google's long-context guidance states that multi-needle performance varies,
  unnecessary tokens should be excluded and latency generally rises with input length.
- `[measured]` Earlier Consilience work required compact handoffs after context compaction;
  no controlled comparison has yet measured which composition best preserves programme
  state.

## Evidence against

- `[cited]` One-million-token advertised capacity does not imply uniform retrieval or
  reasoning across that window.
- `[asserted]` Opus 5 and Gemini 3.7 Flash differ in training, harness, provider, effort,
  latency and accounting, so a direct role comparison cannot identify context length as the
  cause of any outcome.
- `[asserted]` A compact manifest plus retrieval may outperform carrying the whole history
  and can reduce latency, token use and stale-context interference.
- `[asserted]` Mapping human management titles to named vendors risks ossifying a temporary
  model ranking and confusing role with authority.
- `[measured]` OpenRouter is metered and no numeric cap has been authorised for EXP-30, so
  the middle-management candidate cannot run yet.

## Consequences

**Positive** — programme-level work defaults to a composition with enough advertised room
to retain its state, while smaller workers receive bounded contracts. [asserted] Role
assignment remains explainable and replaceable when measured performance changes.
[asserted]

**Negative** — context-demand estimation, retrieval qualification and role-specific evals
add admission work. [asserted] The current Opus preference rests partly on provider claims
and user judgement until EXP-30 runs. [asserted]

**Neutral but load-bearing** — the rule is “prefer sufficient usable context and measured
outcomes”, not “always choose the largest window”. [asserted]

## Enforcement

This ADR declares no product implementation during pre-approval work. [measured] Its
implementation commit must include all of the following checks. [asserted]

- Check: every orchestration dispatch records role, projected context demand, verified
  context capacity, reserved output and the admission verdict.
- Check: a composition below the projected demand is rejected; no adapter may silently
  truncate the state manifest.
- Check: provider/model/effort and resource ledger remain explicit; a management label
  cannot select a hidden model or bypass a hard cap.
- Check: senior and middle-management prompts carry explicit task authority and cannot
  acquire credentials, leases or decision rights from the role name.
- Check: public benchmarks and advertised context enter through the prior/probe boundary;
  only local verifier outcomes can promote a role default.
- Fails CI: yes, once implementation exists.
- Added in the same commit as implementation: **required**.

## What would overturn this

EXP-30 decides the provisional defaults. [asserted]

- If a compact-manifest or retrieval composition with a smaller effective window matches
  the senior default within the fixed non-inferiority boundary at materially lower resource
  use, largest-window preference is removed. [asserted]
- Any critical authority, constraint or evidence-provenance miss removes that composition
  from unattended orchestration for the failed role until fixed and re-run. [asserted]
- A newly admitted composition that beats the current default under the same fixtures,
  verifier and resource accounting supersedes the named model default. [asserted]

## Publication candidate?

**Potentially.** [asserted] A controlled result separating advertised capacity, usable
context, retrieval strategy and hierarchical role performance could be useful beyond this
repository; a two-model pilot alone is not a paper-sized claim. [asserted]

# 0027. Compose domain, execution harness, provider and model as separate routing layers

- **Status:** PROVISIONAL
- **Date:** 2026-08-19
- **Deciders:** Joe Brown
- **Supersedes in part:** ADR-0001
- **Inquiry tier reached:** T3 — vendor interfaces read; two OpenRouter coding
  compositions run live and their failure layers inspected
- **Executable model:** none — this is an identity and responsibility boundary; EXP-22 tests
  whether one input to the boundary, public benchmark data, earns quantitative weight.

## Context

ADR-0001 correctly put Consilience above existing coding harnesses, but it treated a
coding agent as the indivisible backend. [asserted] EXP-05 then labelled Codex-hosted
Ollama and OpenRouter calls as if Ollama and OpenRouter were themselves execution
harnesses. [measured]

That conflation produced a false diagnosis on first live OpenRouter contact: the scratch
repository was unchanged, the verifier failed, Codex reported unrelated global MCP
authentication errors, and OpenRouter key usage was zero at the immediate observations.
[measured] A delayed cumulative provider counter later rose after the OpenCode run, so paid
usage cannot be attributed between the earlier Codex attempts and the OpenCode session.
[measured] The trajectory therefore measured a failed `Codex × OpenRouter × Qwen`
composition before artefact production; it did not measure Qwen task capability.
[measured]

Consilience is intended to be domain-blind even though coding is v0. [asserted] OpenRouter
must therefore be usable as an inference provider for non-coding domains, while coding may
place OpenCode, Codex or another coding harness above the same provider. [asserted]

OpenRouter exposes model discovery, pricing, capability fields, benchmark feeds, provider
routing, standardised tool calls and a domain-general Agent SDK with tool execution and
stop conditions. [cited] OpenCode separately exposes coding tools and OpenRouter as a
built-in provider. [cited] These are different responsibilities and should remain
replaceable independently. [asserted]

## Decision

A routable action is the explicit tuple

```text
action = (domain, harness, provider, model)
```

with version, provider endpoint and model revision recorded where observable. [asserted]
No single `backend` string may silently collapse these fields. [asserted]

- The **domain** owns the task schema and verifier contract. [asserted]
- The **execution harness** owns tools, permissions, sandboxing, session state and artefact
  production. [asserted]
- The **provider** owns model discovery, authentication, inference transport, upstream
  availability, accounting and provider-side budget enforcement. [asserted]
- The **model** is the capability target whose measured outcomes update the routing
  evidence. [asserted]

OpenRouter is a standalone provider adapter across domains. [asserted] A simple
non-agentic task may call its provider seam directly; an agentic non-coding task should
wrap OpenRouter's Agent SDK or another existing domain harness rather than make
Consilience build a generic tool loop. [asserted] Coding tasks use an existing coding
harness such as OpenCode or Codex above the OpenRouter provider. [asserted] Claude Code,
Codex and Cursor subscription paths remain valid compositions whose providers may be
vendor-managed and only partly observable. [asserted]

### Coding harness default and authentication gate

OpenCode is the default coding execution harness when no vendor-native frontier harness is
authenticated. [asserted] This is a harness default, not a provider or model verdict:
ADR-0026 must still admit an authenticated provider/model composition for OpenCode, such
as a hardware-feasible local model or an explicitly budgeted OpenRouter model. [asserted]

Claude Code, Codex and Cursor become routing candidates only after their adapter confirms
the required subscription login or API credential; finding an installed executable is not
sufficient. [asserted] On the measured machine, `claude auth status --json`, `codex login
status` and `cursor-agent status` each expose an authentication verdict, although only the
first two identify the subscription authentication method in their local output.
[measured]

This default prevents an unconfigured vendor CLI from becoming an accidental dependency
of provider-neutral coding. [asserted] It does not prefer OpenCode over an authenticated
frontier subscription when the router's safety and resource rules select that subscription.
[asserted]

Antigravity is another vendor-native coding harness candidate once a live plan-tier/quota
snapshot and a successful structured execution probe pass ADR-0026 admission. [asserted]
The Antigravity/Google-plan composition, a direct Gemini API-key provider and an
OpenRouter/Gemini provider are three distinct actions even when they select a model from
the same Gemini family. [asserted] Subscription capacity, Google API billing and
OpenRouter billing must therefore remain separate provider and accounting identities.
[asserted]

### Public benchmarks are priors, not verdicts

OpenRouter's models and benchmark APIs may supply candidate discovery, tool-support,
context, price, latency, throughput and externally measured capability priors. [cited]
Every ingested datum retains source, benchmark, task type, `as_of`, API version and
citation or licence metadata when supplied. [asserted]

Consilience's mathematics consumes those data only as a pre-registered prior over model
capability or as a reason to probe a candidate. [asserted] The paired local probe in
ADR-0025 supplies `Δ̂` and `φ̂`; repository outcomes supply `β̂`; ADR-0026 supplies the
feasibility vetoes. [algebra] A public per-model benchmark cannot by itself measure local
model-failure correlation `φ` or a repository verifier's false-accept rate `β`.
[algebra]

Consilience selects the model for β-sensitive unattended work. [asserted] OpenRouter may
select the upstream provider for that fixed model using native price, throughput,
availability, tool-reliability and data-policy controls. [cited] OpenRouter's automatic
cross-model router is an EXP-22 baseline, not the production Consilience decision, because
the selected model is known only after dispatch and its policy does not contain the
repository's measured `β`. [asserted]

## Evidence

- `[measured]` The first OpenRouter-labelled EXP-05 run produced no diff or usage telemetry
  and failed inside the Codex-hosted composition; its immediate provider counter was zero,
  but delayed cumulative billing prevents a zero-cost attribution.
- `[measured]` Existing EXP-05 results already contain two distinct compositions sharing
  the Codex harness: Codex with its subscription provider and Codex with local Ollama.
- `[measured]` OpenCode 1.18.18 was installed in WSL from its official installer. One
  `OpenCode × OpenRouter × qwen/qwen3-coder` run reached inference, implemented the
  requested function and passed functional tests in 24.1 seconds, but also created an
  unrequested test file; the strengthened artefact-scope verifier rejects it.
- `[measured]` The exported OpenCode session records provider and model separately and
  retains the model's incorrect completion claim alongside the failed artefact verdict.
- `[cited]` OpenRouter's Models API exposes model identity, pricing, supported parameters,
  context and live routing heuristics; its Benchmarks API exposes sourced, dated benchmark
  records from multiple producers.
- `[cited]` OpenRouter standardises user-defined tool calls while leaving their execution
  to the client; its Agent SDK supplies automatic multi-turn execution, validation, cost
  and step stop conditions.
- `[cited]` OpenRouter documents model-fixed provider routing and a built-in OpenCode
  integration; OpenCode documents coding tools independently of provider choice.
- `[cited]` Antigravity exposes a native coding harness and Google-plan authentication;
  Gemini API keys and OpenRouter-hosted Gemini are separate metered provider paths.
- `[algebra]` `(benchmark prior, Δ̂, φ̂, β̂, feasibility)` cannot collapse to a public
  benchmark score because `φ̂` is a paired outcome and `β̂` is a local verifier property.

## Evidence against

- `[cited]` OpenRouter's Agent SDK deliberately combines provider access and an execution
  loop, so the boundary is operationally blurrier than the four-field schema suggests.
- `[cited]` OpenRouter already offers automatic model routing and provider selection;
  retaining Consilience's own model decision duplicates part of a maintained commercial
  service.
- `[asserted]` More explicit dimensions increase adapter, fixture and trajectory-schema
  work, especially when a subscription agent hides its provider or selected model.
- `[measured]` No non-coding OpenRouter trajectory has yet been run through a domain
  harness. The single OpenCode trajectory covers one trivial coding task only.
- `[asserted]` Public benchmark priors may prove too stale, contaminated or weakly related
  to the user's task distribution to save any local probe work.

## Consequences

**Positive** — OpenRouter can serve non-coding domains without masquerading as a coding
agent, while coding harnesses remain reusable across providers. [asserted] Results can
attribute a failure to the harness, provider or model instead of blaming a conflated
backend. [asserted]

**Negative** — every trajectory and reservation must carry the composition, and hidden
model/provider identity becomes explicit missing data rather than a convenient label.
[asserted]

**Neutral but load-bearing** — ADR-0001's meta-harness decision survives, but its unit of
orchestration is now a composed action rather than an indivisible coding-agent name.
[asserted] ADR-0013 still forbids public benchmarks from measuring `β`; ADR-0025 decides
how priors meet local probes; ADR-0026 vetoes infeasible compositions. [asserted]

## Enforcement

This ADR changes experimental schemas during pre-spec work but declares no product
implementation yet. [measured] The implementation commit must include all checks below.

- Check: the trajectory schema requires `domain`, `harness`, `provider` and `model`, with
  an explicit `unknown` reason where a field is not observable.
- Check: routing code consumes benchmark records only through the prior/probe boundary;
  a lint rule bans raw benchmark fields from producing a route verdict.
- Check: OpenRouter automatic cross-model routing is rejected for unattended β-sensitive
  work unless a future ADR supersedes this rule and ships its admission check.
- Check: an installed but unauthenticated Claude Code, Codex or Cursor executable is not a
  feasible coding composition; a fixture covers each authentication transition.
- Check: when no vendor-native frontier harness is authenticated, coding harness selection
  defaults to OpenCode and still requires an independently admitted provider/model pair.
- Check: provider calls outside registered provider adapters fail lint.
- Fails CI: yes, once implementation exists.
- Added in the same commit as implementation: **required**; EXP-05's experimental result
  schema and tests are updated with this ADR.

## What would overturn this

- EXP-22 shows that an OpenRouter benchmark/automatic-router prior reaches the same local
  routing verdict with materially fewer probes and no additional false admits under its
  pre-registered stopping rule; the prior may then gain quantitative weight. [asserted]
- Three non-coding domain adapters require materially different provider contracts rather
  than different harness tools; that would falsify the shared standalone-provider seam.
  [asserted]
- A maintained external harness exposes domain tools, provider identity, model identity,
  verifier hooks and hard budgets for both coding and non-coding tasks; wrapping that one
  boundary would be simpler and should supersede this composition. [asserted]

## Publication candidate?

**No.** [asserted] The benchmark-prior calibration in EXP-22 may be publishable if it
produces a robust negative or a reproducible probe-saving result. [asserted]

# 0084. Compile portable capabilities per harness and refuse semantic loss

- **Status:** PROVISIONAL — EXP-110 can kill automatic portable binding for its frozen Claude/Codex
  package; EXP-101 still governs whether automatic capability reuse improves outcomes. [asserted]
- **Date:** 2026-08-22. [measured]
- **Deciders:** Joe Brown supplied the portable-capability outcome recorded in the dispatch brief;
  Codex dispatch `20260822T140603-d953f3635e` owns this provisional mechanism, which he has not
  reviewed. [measured]
- **Inquiry tier reached:** T1 ground — current source and retrieved incumbent surfaces were read;
  T3 is preregistered as EXP-110 and has not run. [measured]
- **Executable model:** none — adapter support and semantic preservation are categorical conformance
  questions; EXP-110 is the executable cross-harness test. [asserted]

## Context

**Correction:** portable multi-harness configuration already exists. Rulesync v16.14.0 targets
Claude Code, Codex CLI, Cursor and Grok CLI across rules, MCP, skills and hooks, while OpenAI imports
Claude/Cursor skills, memories, MCP configuration and hooks into Codex. Portability by itself is not
a defensible differentiator. [cited: [Rulesync supported tools, retrieved
2026-08-22](https://rulesync.dyoshikawa.com/reference/supported-tools.html); [OpenAI import,
retrieved 2026-08-22](https://learn.chatgpt.com/docs/import)]

Current Consilient selection is nonetheless unwired as a capability. `capabilities.py` emits only
kind, name, provenance and reason; `dispatch.py` appends that JSON to task text; every harness is
told to read the resulting brief. No payload, tool handle, MCP configuration, skill body, hook or
connection is activated. Bounded recall text reaches every child, but production dispatch bypasses
`instructions.assemble()` and silently drops recall on read/value errors. [measured:
`src/consilient/capabilities.py:171-194`; `scripts/dispatch.py:701-721,766-898,1248-1272`]

ADR-0074 already fixes immutable manifests, provenance, destination boundaries and the ownership
chain: `capabilities.py` selects, `instructions.py` assembles, `dispatch.py` calls and `events.py`
writes. ADR-0078 already requires typed gated effects, pre-effect intent and a least-privilege
adapter. A new format, loader or orchestrator would violate both decisions. [asserted]

## Decision

We will extend ADR-0074's canonical manifest with a discriminated runtime description, optional
lifecycle trigger, required semantics and opaque credential references, then derive a run-local
native binding in the existing per-harness `build_command()` boundary. Every selected capability
will be recorded before launch as `applied`, explicitly `degraded` for optional loss, or `refused`
for required loss. Prompt guidance will never stand in for permissions, blocking hooks, credentials
or typed-effect enforcement. [asserted]

The existing kind set does not change. Hook behaviour is trigger metadata on a `skill`, `tool`, `mcp`
or `plugin`; memory stays a separately referenced ADR-0074 recall contract and receipt, never a
capability kind. [asserted]

Skills, memory, MCP, tools and hooks are not promised equal portability. Agent Skills and bounded
recall bytes form the highest portable floor; MCP is portable subject to host/auth differences;
tools travel only through MCP or a constrained local executable contract; lifecycle hooks travel
only where timing and blocking semantics match. Vendor-native extensions remain destination-specific
or unavailable. [cited] [asserted]

Credentials will not be passed to the model process. An instance-private dispatcher broker resolves
opaque references and exposes capability-scoped local IPC; manifests, generated files, commands,
briefs, transcripts and trajectory receipts contain no credential value. A native surface that
requires inline or ambient model-visible credentials is unsupported and refuses. Spawn-time
environment separation is not sufficient under today's same-user permission-bypass launch: the
credential path also refuses until the independently tested outer boundary isolates the broker's
process/security namespace and admits only its run-scoped operations. [measured:
`src/consilient/harness.py:40-59`] [asserted]

One filtered recall pack and receipt will be produced from a pinned trajectory prefix after
workspace, consent and destination admission. Claude and Codex receive the same bytes and digest;
vendor memory is non-authoritative and must be disabled, isolated or reported uncontrolled.
[asserted]

Effective target effects are the union of the declared capability, generated adapter surface and
harness ambient reach. An adapter may narrow this set and record the loss; unknown or widened reach
refuses under ADR-0078. A dispatched process cannot reuse or mint the principal's approval, consent,
verdict, gate-lift or spend authority. [asserted]

Automatic reuse remains inert under ADR-0074 pending EXP-101. EXP-110 decides only whether one
no-live-credential composite package preserves its observable contract across frozen Claude Code and
Codex versions; it promotes no capability and changes no gate. [asserted]

Automatic binding begins only after selection and does not authorise promotion or fan-out. Every
additional role must still name a different class of facts in `work_items.py`, and `routing.py` still
enforces the measured-beta squad ceiling; replaying the same capability and evidence through another
model is echo rather than consilience. [asserted]

The complete fields, per-harness mapping, credential path, memory boundary, portability ranking and
EXP-110 protocol are fixed in
`../superpowers/specs/2026-08-22-portable-capability.md`. [asserted]

## Evidence

- `[measured]` The live source path validates and injects selection metadata but has no capability
  consumer, endpoint, transport, payload or per-harness support/degradation receipt.
- `[measured]` A timestamped 22 August exact search under `.harness/dispatch` and `.harness/log`
  returned zero selection-context matches; no retained run demonstrated use.
- `[measured]` `write_brief()` embeds one bounded recall pack for every harness but converts recall
  I/O/value errors to empty context without a receipt.
- `[cited]` Rulesync v16.14.0 already generates multiple native capability formats for every named
  harness and documents simulated/target-specific behaviour: https://rulesync.dyoshikawa.com/.
- `[cited]` OpenAI's import surface migrates setup and memory while warning that permissions, MCP
  authentication and hooks require review: https://learn.chatgpt.com/docs/import.
- `[cited]` Agent Skills standardises the portable text/package floor while marking `allowed-tools`
  experimental: https://agentskills.io/specification.
- `[cited]` MCP standardises host/client/server transport but leaves host security/consent and
  optional authorisation material to implementations:
  https://modelcontextprotocol.io/specification/2025-06-18/architecture.
- `[asserted]` Per-task binding receipts, fail-closed semantic loss and a model-external credential
  broker are the smallest material delta over the retrieved incumbents.

## Evidence against

The strongest case is that portability is a mirage and one harness should be chosen. Current native
documentation exposes materially different enforcement surfaces: Claude supports command, HTTP,
MCP-tool, prompt and agent hook handlers and hosted-tool events, while Codex currently executes
command handlers, excludes hosted tools, permits specialised local paths to opt out and describes
hooks as a guardrail rather than a complete enforcement boundary. [cited:
https://code.claude.com/docs/en/hooks; https://developers.openai.com/codex/hooks] Clean file
translation therefore does not prove equivalent control. [asserted]

Rulesync's target overrides, simulated features and warnings expose the maintenance burden rather
than eliminating it. Four CLIs changing independently produce a capability-by-version conformance
matrix; adapter lag can silently weaken a safety boundary unless stale versions refuse. [cited]
[asserted]

Going deep on Claude Code would preserve its documented combination of native skills, plugins, MCP,
hooks and memory, reduce compatibility work and make one verifier surface easier to calibrate.
[cited: https://code.claude.com/docs/en/skills; https://code.claude.com/docs/en/plugins;
https://code.claude.com/docs/en/hooks; https://code.claude.com/docs/en/memory] It would likely ship
sooner. It would also abandon the principal's explicit multi-harness outcome, concentrate
provider/quota failure and discard the option to route through separately subscribed families.
[asserted]

This decision therefore concedes that native extensions do not travel. It keeps a tested common
floor, refuses semantic substitution, and names the experiment that can remove automatic binding.
Before implementing a format compiler, a version-pinned Rulesync comparison must show whether it can
satisfy the same receipts and security boundaries; a suitable result should be adopted under
ADR-0065 instead of rebuilt. [asserted]

Known weaknesses are material: no binding implementation, broker or proved outer sandbox exists;
EXP-110 is blocked; no cross-harness outcome has been observed; the live trajectory can record task
text and child output; and the current effect boundary is itself provisional. [measured]

## Consequences

**Positive** — capability selection can become observable application rather than advisory prose;
shared memory has one authority; unsupported semantics are visible; credentials remain outside the
model/trajectory; and vendor drift fails closed. [asserted]

**Negative** — four adapters require continuing conformance work; run-local profiles and a broker add
startup cost; the common floor discards useful native features; strict refusal can reduce available
harnesses; and EXP-110 may show that the layer earns none of its cost. [asserted]

**Neutral but load-bearing** — ADR-0074 remains the manifest/selection authority, ADR-0078 remains
the effect boundary, EXP-101 remains the automatic-reuse outcome gate, no principal authority is
delegated, and `routing_orchestration_enabled` remains `false`. [asserted] [measured]

## Enforcement

This commit specifies and preregisters the boundary; it does not implement or activate it. Current
permission-bypass dispatch gives raw shell-capable harnesses wildcard effects under ADR-0078, so
automatic binding and EXP-110 must refuse until an independently tested outer sandbox proves the
frozen effect exclusions. [measured: `src/consilient/harness.py:40-59`;
`scripts/dispatch.py:732-898`] [asserted] Existing
AST, secret, private-corpus, record-number and commit-attribution checks continue to run, but none
currently proves that a selected capability is applied, that a credential stays out of trajectory,
or that two harnesses preserve semantics. [measured]

Each implementation increment must ship its matching check: [asserted]

- a source ratchet keeps `capabilities.py` as selector, `instructions.py` as assembler and
  `dispatch.py` as caller; [asserted]
- per-harness fixtures require `applied`, explicit `degraded` or pre-launch `refused`, and reject a
  required-to-prompt downgrade; [asserted]
- a process/IPC-boundary check proves only the broker receives secret-bearing environment; a hostile
  same-user child cannot discover broker secrets, connect without run-scoped authentication or
  retrieve a raw credential; and raw, canonical-encoding and split-form canaries stay absent from
  child-visible and durable sinks; [asserted]
- cross-root, unconsented-destination and escaping-path fixtures refuse before content is rendered;
  [asserted]
- unsupported blocking hooks and widened/unknown effect surfaces refuse before the fake primitive
  or child process; [asserted]
- an outer sandbox conformance fixture proves process, file, network and IPC exclusions from outside
  the child before automatic binding or EXP-110 may run; [asserted]
- adapter-version drift returns `stale` until the focused conformance bank passes; and [asserted]
- EXP-110 is the activation test for its frozen Claude/Codex package, while EXP-101 remains the
  broader reuse-outcome test. [asserted]

- **Check:** future `tests/test_portable_capabilities.py`, the existing invariant/privacy scanners,
  and EXP-110. [asserted]
- **Fails CI:** no for the future checks today; yes when their implementation lands. [measured]
- **Added in the same commit as the implementation:** this commit has no implementation; same-commit
  enforcement is required for every later increment. [measured] [asserted]

## What would overturn this

EXP-110 kills automatic portable binding if any required component is silently absent, any portable
arm differs from its native observable contract, a credential enters child-visible/durable bytes, or
a protected effect escapes. Native arms must first pass every contract check and absent arms must fail
their canaries; otherwise the instrument is invalid, binding stays inert and no portability conclusion
is drawn. Every launched attempt has a fixed 600-second budget. A timeout is terminal and receives no
retry; a resume runs only attempts that never started. A started attempt without a terminal
checkpoint makes the epoch incomplete and draws no conclusion. Once the instrument is valid,
portable-arm refusals, timeouts, degradations and missing outputs are failures. [asserted]

A lower-cost overturning result is a version-pinned Rulesync or vendor-native import path that meets
the manifest provenance, receipt, credential, memory and effect checks with less code. In that case
Consilient adopts the adapter and deletes the redundant compiler plan without changing this
boundary. [asserted]

If maintaining passing adapters consumes more accepted-outcome-normalised time than choosing one
reference harness, or if capability fidelity repeatedly contracts to prompt text, supersede this ADR
with a one-harness decision. [asserted]

## Publication candidate?

**No.** The portability premise required correction, the mechanism is unimplemented and EXP-110 has
not run. A later negative equivalence result or measured receipt boundary may be useful; this ADR is
not that result. [asserted]

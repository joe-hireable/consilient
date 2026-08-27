# Portable capabilities: compile to each harness and refuse semantic loss

- **Document class: W**
- **Review by:** 2026-09-22
- **Falsifier:** EXP-110 kills automatic portable binding for the frozen two-harness case.

**Class-W contract adopted 22 August 2026.** Mechanical admission only; existing claim wording and evidence tags are unchanged. [asserted]

**Correction:** portability is not an unoccupied product category. Rulesync v16.14.0 already
generates rules, MCP configuration, commands, subagents, skills, hooks and permissions for Claude
Code, Codex CLI, Cursor and Grok CLI, among many other targets; OpenAI also imports Claude Code and
Cursor instructions, skills, memories, MCP configuration and hooks into Codex. The defensible gap is
not format translation. It is applying a capability per task with provenance, explicit semantic-loss
receipts, bounded shared memory, credential isolation, typed-effect enforcement and measured
cross-harness equivalence. [cited: [Rulesync supported tools, retrieved 2026-08-22](https://rulesync.dyoshikawa.com/reference/supported-tools.html); [OpenAI import documentation, retrieved 2026-08-22](https://learn.chatgpt.com/docs/import)]

- **Date:** 2026-08-22. [measured]
- **Status:** specification; ADR-0084 is PROVISIONAL and EXP-110 can kill automatic portable
  binding for its frozen two-harness case. [asserted]
- **Author:** Codex dispatch `20260822T140603-d953f3635e`. The principal supplied the portability
  outcome; the mechanism, ordering and thresholds below are this dispatch's provisional design and
  have not been reviewed by him. [measured]
- **Scope:** future extension of the existing capability, instruction, recall, event and dispatch
  paths. This document adds no product code, dependency, command, gate change, credential, metered
  call or automatic activation. [measured]

## 1. Direct answer: what reaches a dispatched harness today

No selected working capability reaches a child harness today. Selection metadata can reach every
child as fenced JSON in its brief, but the schema contains no payload, endpoint, transport,
credential reference, hook event or executable configuration. [measured:
`src/consilient/capabilities.py:8-45,171-194`; `scripts/dispatch.py:1248-1272`]

The path is complete as text and stops there: `task_with_capabilities()` calls
`select_capabilities()`, appends `{kind,name,provenance,reason}` to the task, `write_brief()` writes
that task, and each Claude, Codex, Cursor or Grok branch tells its CLI to read the same brief.
`scripts/capability_context.py` is a separate emitter and is not the dispatch caller. [measured:
`scripts/dispatch.py:660-721,766-898,1248-1272,1827-1834`]

The bounded recall pack is the partial exception. `write_brief()` embeds trajectory-derived text, so
the same memory bytes can already reach all four families. An I/O or value error silently becomes an
empty pack, however, and the production path does not call `instructions.assemble()` or enforce
ADR-0074's workspace, consent and destination checks before rendering. This is portable prompt
context, not the complete portable-memory contract. [measured:
`scripts/dispatch.py:701-721`; `src/consilient/instructions.py:380-415`]

A retained-artefact search at 2026-08-22T14:28Z returned zero `Selected capability context` matches
in the retained `brief.md` files or trajectory JSONL files. The reproducible PowerShell pipeline was
`Get-ChildItem .harness/dispatch -Recurse -Filter brief.md -File | Select-String -SimpleMatch
'## Selected capability context'`, repeated over `.harness/log` with `-Filter *.jsonl`. This proves
no retained local run used the selection path; it cannot prove that an artefact was never created
and later deleted. [measured]

The contemporaneous subscription-reach report reaches the same operational conclusion: global MCP
configuration is separate from dispatch and no task-scoped connection passes through. Its line 120
incorrectly says dispatch runs `scripts/capability_context.py`; the direct source trace above is the
correction. [measured: `docs/00-context/subscription-reach-2026-08-22.md:114-132`]

## 2. The retrieved bar and the narrower delta

| Bar | What it already achieves | Boundary that remains |
|---|---|---|
| **Rulesync v16.14.0** | One canonical source generates native rules, MCP, commands, subagents, skills, hooks and permissions for the four named harnesses and more. [cited: [matrix](https://rulesync.dyoshikawa.com/reference/supported-tools.html); [release](https://github.com/dyoshikawa/rulesync/releases/tag/v16.14.0)] | Some features are simulated as prompt text, hook types and lifecycle events differ, and no portable memory contract is supplied. [cited: [simulated features](https://rulesync.dyoshikawa.com/guide/simulated-features.html); [file formats](https://rulesync.dyoshikawa.com/reference/file-formats.html)] |
| **OpenAI import** | Codex CLI imports supported Claude Code and Cursor setup and recent work; the desktop surface can keep imported work synchronised. [cited: [OpenAI import documentation](https://learn.chatgpt.com/docs/import)] | It is one-way migration, requires review, and explicitly warns that permissions, MCP auth and hooks may behave differently. [cited] |
| **Agent Skills** | `SKILL.md` plus optional scripts, references and assets is an open cross-product format used by compatible agents. [cited: [specification](https://agentskills.io/specification); [overview](https://agentskills.io/home)] | `allowed-tools` is experimental and support varies; a text package does not prove invocation or outcome equivalence. [cited] |
| **MCP** | A host/client/server protocol exposes tools, resources and prompts over negotiated sessions. [cited: [MCP architecture](https://modelcontextprotocol.io/specification/2025-06-18/architecture)] | HTTP authorisation is optional and stdio credentials come from the environment; each host retains consent, security and client behaviour. [cited: [MCP authorisation](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)] |

The plain incumbent answer is therefore Agent Skills for procedures, MCP for portable tool transport,
Rulesync for configuration generation, and a prompt-carried recall pack. [cited] The additional
Consilient work is justified only if per-task receipts, security boundaries and EXP-110 demonstrate
value beyond those components. No dependency is adopted here; adding Rulesync would require a
separate adoption decision under ADR-0065. [asserted]

**Search record, 22 August 2026:** official documentation and first-party repositories were queried
for Claude Code, Codex, Cursor, Grok, Hermes, Goose, OpenHands, Continue and Aider, plus cross-agent
compiler, import, skills, MCP, hook and memory terms. Rulesync, OpenAI import and Agent Plugins were
the material hits; Ruler, Vercel Skills, OpenHands, Continue and Aider were narrower near misses.
Product documentation, standards and first-party repositories were used; snippets and community
compatibility claims without a primary source were excluded. [measured]

## 3. One path, no second orchestrator

The extension follows ADR-0074's existing ownership and does not add a parallel loader. [asserted]

```text
task + destination + consent
        |
        v
capabilities.py selects immutable manifests
        |
        v
instructions.py assembles selected skills + one filtered recall pack
        |
        v
dispatch.py's existing per-harness branch derives a run-local binding
        |
        +-- required semantic unavailable --> dispatch.refused + binding receipt
        |
        v
events.py records the secret-free binding receipt before launch
        |
        v
existing build_command()/run_harness() launches Claude, Codex, Cursor or Grok
```

`capabilities.py` remains the selector, `instructions.py` remains the assembler,
`dispatch.py` remains the caller and process boundary, and `events.py` remains the trajectory writer.
The existing per-harness branches in `build_command()` are the adapter boundary; implementation may
extract pure helpers, but may not create another registry, router, service or orchestrator.
[asserted]

Selection, binding, application and observed use are separate states. A selected name is not a
working capability, a generated file is not proof that a CLI read it, and an applied capability is
not proof that the model used it. Receipts retain those distinctions. [asserted]

Automatic reuse remains inert under ADR-0074 pending EXP-101. EXP-110 can establish binding
equivalence for one frozen package and two harnesses; it cannot promote a capability or supersede
EXP-101's outcome test. [asserted]

"Automatic" applies after selection: the adapter binds every admitted required capability before
launch without asking the child model to discover or install it. It does not mean automatic
promotion, authority or fan-out. `work_items.py` must still name the different class of facts a role
brings, and `routing.py` must still enforce the measured-beta squad ceiling; sending the same
capability and evidence to another model is echo, not consilience. [asserted]

## 4. Extend ADR-0074's canonical manifest

There is one durable manifest format. The fields already fixed by ADR-0074 remain: stable
`kind:name`; immutable version and payload digests; object locator; authoring run; licence and privacy
class; purpose and postcondition; normalised input/output interface; permissions, effects and trust;
verifier semantics and version; provenance; status; supersession/duplication; and expiry or recheck
condition. Credential values remain forbidden. [asserted: ADR-0074 and
`2026-08-22-memory-and-capability.md:175-208`]

The portable extension adds four fields to that manifest rather than defining a sibling format.
[asserted]

| Field | Contract |
|---|---|
| `runtime` | A discriminated, non-shell-string description of how the payload can execute or render: content format and entry path for a skill; argv/transport and protocol for MCP or a local tool; package entry points for a plugin or connection. [asserted] |
| `requires` | The semantics that must survive adaptation: native surface, lifecycle timing, blocking behaviour, tool schema, transport, filesystem/network boundary and verifier observable. It contains no harness name; the adapter reports whether its installed version satisfies the requirements. [asserted] |
| `credential_refs` | Opaque instance-local references and minimum scopes. Names and values of environment variables, tokens, headers, client secrets and private keys are absent. [asserted] |
| `trigger` | Optional canonical lifecycle phase, matcher, blocking semantics and action reference. A hook is an existing `skill`, `tool`, `mcp` or `plugin` manifest with this trigger; the field never creates a separate executable kind. [asserted] |

The closed capability-kind set remains `tool`, `mcp`, `skill`, `plugin` and `connection`. Hook
behaviour is a trigger on one of those existing kinds. Memory remains ADR-0074 recall, not a
capability kind: the binding plan references the separately scoped retrieval contract and immutable
receipt, neither of which carries vendor memory or learned weights. This preserves ADR-0074's
record/recall/capability/training distinction. [asserted]

The task request adds `necessity: required | optional`. Absence is invalid. A selected security,
credential, authority or typed-effect control is always treated as required even if a request labels
it optional. [asserted]

Harness-specific overrides do not enter the canonical manifest. If a native variant changes the
postcondition, permissions, effect boundary or verifier semantics, it is a different manifest head
for that destination class, linked by provenance rather than presented as the portable version.
[asserted]

## 5. Adapter boundary and failure semantics

For each selected manifest, the installed harness probe and current task boundary enter the existing
per-harness branch. The branch produces a run-local plan under the private dispatch directory: exact
harness/version, adapter version, generated configuration digests, instruction digest, native
surface used, narrowed permissions/effects, credential-broker status and unsupported semantics.
Global user configuration is never mutated. [asserted]

| Harness | Skill binding and recall | MCP and tool binding | Hook binding | Honest unsupported result |
|---|---|---|---|---|
| **Claude Code** | Render selected Agent Skills through a run-local Claude settings/plugin surface; supply the filtered recall bytes in the recorded instruction assembly. [asserted] | Generate a run-local MCP configuration; a local executable tool is exposed through MCP unless an equivalent native schema is proven. [asserted] | Map only lifecycle phase, matcher, blocking and action types supported by the probed Claude version. [asserted] | A required mismatch refuses before `claude -p`; optional loss is named in the brief and receipt. [asserted] |
| **Codex CLI** | Render selected Agent Skills and the same recall bytes through a run-local Codex configuration/instruction layer. `/import` is not the runtime boundary because official documentation says it is unavailable during a running task. [cited] [asserted] | Generate the run-local `config.toml` MCP layer or equivalent CLI overrides, with the credential broker below. [asserted] | Use `hooks.json` only where the installed version proves the event, tool coverage, handler type and blocking behaviour. Current `PreToolUse` covers shell, `apply_patch`, MCP and most local functions, but not hosted tools; specialised paths may opt out, and only command handlers execute. [cited: [current Codex hooks](https://developers.openai.com/codex/hooks)] | Unsupported handler types, uncovered tool paths and unmatched lifecycle semantics refuse when required; prompt guidance never counts as a permission boundary. [cited] [asserted] |
| **Cursor** | Render Agent Skills/rules and the same recall bytes into a run-local project or ACP session overlay; do not write the user's global Cursor profile. [asserted] | Prefer session-scoped MCP configuration through the native/ACP adapter; a global installation is not task-scoped application. [asserted] | Bind only events and fail-closed behaviour supported by the probed Cursor version. [asserted] | If the current CLI cannot accept a run-local binding without mutating global/project state, that capability is unsupported and the required case refuses. [asserted] |
| **Grok CLI** | Render `AGENTS.md`/Agent Skills-compatible content and the same recall bytes through a run-local overlay. Grok's documented Claude compatibility is evidence of an input surface, not equivalence. [cited: [xAI compatibility documentation](https://docs.x.ai/build/features/skills-plugins-marketplaces)] | Generate task-scoped MCP configuration accepted by the probed Grok version. [asserted] | Map documented Grok hook events exactly; a Claude-compatible file that changes timing or blocking semantics is a mismatch. [asserted] | One-way compatibility never converts an unsupported required semantic into prompt text; refuse and record it. [asserted] |

The plan terminates in exactly one of three states. [asserted]

- `applied`: every required semantic is represented on the installed harness version and the
  generated artefacts re-read by digest. [asserted]
- `degraded`: optional semantics are missing or narrowed, the exact losses are in both the child
  brief and the trajectory receipt, and the remaining verifier contract is still meaningful.
  [asserted]
- `refused`: a required semantic, boundary, credential, version proof or post-bind digest check is
  absent. No child process starts. [asserted]

The pre-launch receipt contains manifest/version digest, task request identity, harness and adapter
versions, state, generated artefact digests, native surfaces, every loss/reason, recall receipt,
credential status and effect-manifest digest. The later attempt outcome records observed use as
`yes`, `no` or `unknown`; it never infers use from selection or loading. Raw generated configuration,
task content and credentials do not enter the receipt. [asserted]

Any harness version outside the adapter's last passing compatibility range makes the binding
`stale` and therefore refused until the focused conformance fixture passes. Four moving CLIs create
four explicit revalidation obligations rather than silent optimism. [asserted]

## 6. Which capabilities genuinely travel

| Rank | Capability | Honest portability |
|---:|---|---|
| 1 | **Skills** | **High for the Agent Skills core.** Markdown instructions and bundled files travel; native permission, model, subagent and hook extensions do not. [cited] |
| 2 | **Memory** | **High for bounded bytes and receipts, low for vendor-native memory.** Consilient can render the same filtered bytes to each prompt; native curation, retrieval and persistent stores remain vendor-specific and non-authoritative. [measured] [asserted] |
| 3 | **MCP servers** | **Medium.** Protocol and common transports travel, while host capability negotiation, OAuth, environment handling, consent and tool filters vary. [cited] |
| 4 | **Tools** | **Low outside MCP or a constrained local executable contract.** Vendor-native tools, sandboxes, approval modes and result schemas cannot be made equivalent by renaming them. [asserted] |
| 5 | **Hooks** | **Lowest.** Lifecycle events, tool coverage, trust, blocking semantics and handler types differ. Current Claude supports command, HTTP, MCP-tool, prompt and agent handlers; current Codex executes command handlers and warns that some tool paths escape its hook path. A safety hook without an equivalent blocking phase does not travel. [cited: [Claude hooks](https://code.claude.com/docs/en/hooks); [Codex hooks](https://developers.openai.com/codex/hooks)] [asserted] |

Thus all five do not travel at full fidelity. The portable product is a common semantic floor plus
tested native adapters. Vendor extensions stay native, explicitly unavailable or separate
destination-specific manifests. [asserted]

Matrix factorisation is an algorithm, not a capability kind; it travels only when packaged as a
rights-cleared skill/tool under the contracts above. Recursive model change remains ADR-0074
training, with checkpoints, provenance and quarantine. Closed-vendor learned weights cannot be
carried between these harnesses, and prompt or memory updates may not be renamed training.
[asserted]

## 7. Credentials: reach the capability, never the model or trajectory

The canonical manifest carries opaque `credential_refs` and scopes, never values. A gitignored,
instance-local mapping resolves those references at dispatch time. The dispatcher starts a local
least-privilege broker or MCP sidecar whose process receives the credential; the harness receives a
run-scoped local IPC endpoint and the admitted operations, not the provider credential. [asserted]

The broker withholds raw headers, tokens and environment values from the harness process, generated
configuration, brief, command line, stdout/stderr capture and event payloads. The receipt records
`not_required`, `bound` or `missing`, the broker/configuration digest and granted scope. If the
native surface requires an inline secret or passes the provider credential into the model's ambient
environment, that binding is unsupported and refuses. [asserted]

MCP's recommendation that stdio servers obtain credentials from their environment is compatible
with this boundary only when the broker/sidecar process receives that environment. Passing the same
environment to a shell-capable harness would expose the credential to the model and is forbidden.
[cited: [MCP authorisation](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)] [asserted]

Process/environment separation at spawn is insufficient while broker and harness run as the same OS
user: a permission-bypass, shell-capable child may inspect the broker process or drive an ambient IPC
endpoint. Credentialed binding therefore also refuses under the current launch path. Section 9's
proved outer boundary must put the broker outside the child's process/security namespace and expose
only the authenticated, run-scoped admitted operations before this path can become available.
[measured: `src/consilient/harness.py:40-59`] [asserted]

The existing repository secret scanner remains the public-tree/history backstop, but it does not
prove the runtime boundary. The primary implementation check is structural:
`tests/test_portable_capabilities.py::test_credential_process_boundary_and_canary_encodings_never_enter_child_or_durable_sinks`.
It proves the broker alone receives the secret-bearing environment, the harness receives an explicit
allowlist without it, and credential resolution is reachable only inside the broker boundary. As
defence in depth, it scans raw, hex, base64, percent-encoded, JSON-escaped and split canaries across
generated artefacts, child-visible environment, transcript and appended events. Exact-byte scanning
alone is not an enforcement boundary because a child could transform the value. [asserted]

No broker implementation means credentialed capabilities remain unavailable. This specification
does not move a secret, log in, make a provider call or authorise spend. Repository settings,
Actions secrets and hosted CI are not credential paths for this project; a capability that cannot
use the instance-local broker does not run. [measured] [asserted]

## 8. One memory serves Claude and Codex

The trajectory and immutable private objects remain authority. For one run, `instructions.py` reads
one pinned event prefix, filters candidate record metadata by workspace, purpose-specific consent
and destination before reading or rendering protected content, then asks `recall.py` for a bounded
verbatim pack. [asserted]

The result is one immutable pair: recall bytes plus receipt. The receipt carries query digest,
source-prefix digest, selected and omitted record identities/reasons, bytes, bound, continuation,
scan/context completeness and destination. Claude and Codex receive byte-identical pack content and
the same receipt digest through their native instruction surfaces. Each binding receipt proves the
rendered digest. [asserted]

Vendor memory may neither become authority nor silently augment this contract. An adapter disables
or isolates ambient vendor memory where the harness supports that; otherwise it records
`ambient_vendor_memory=uncontrolled`. An uncontrolled session cannot participate in EXP-110's same-
memory arm or satisfy a task that requires the Consilient pack to be the complete admitted memory.
[asserted]

New Claude/Codex memory writes are ordinary foreign outputs. They enter Consilient memory only after
capture, provenance, workspace/consent/destination admission and, where applicable, quarantine.
Historical approvals, verdicts, spend authority and credentials are evidence of past state, never
reusable authority for a new action. [asserted]

The matching checks are
`test_memory_filters_before_rendering_for_each_destination`,
`test_claude_and_codex_receive_the_same_recall_digest`, and
`test_ambient_vendor_memory_cannot_satisfy_complete_memory`. [asserted]

## 9. What must never travel

| Material | Rule |
|---|---|
| Credential values, private keys, tokens, cookies, OAuth codes or reusable broker handles | Never enter a manifest, brief, harness environment, generated configuration, transcript or trajectory. Broker locally or refuse. [asserted] |
| Records outside the authorised workspace, consent purpose or destination | Filter before content is read into assembly; record a non-content omission reason. [asserted] |
| Principal-authored approval, consent, verdict, gate lift or spend authority | Historical records may inform but never authorise a new effect; a dispatched process cannot mint or replay principal authority. [asserted: ADR-0078] |
| A capability whose target adapter widens permissions, effects or ambient reach | Compute the target's effective effect surface. Narrowing is recordable; widening or unknown reach refuses. [asserted] |
| Raw shell/browser reach presented as a bounded tool | Treat as wildcard effects unless ADR-0078's outer sandbox proves exclusions. [asserted] |
| A fail-closed hook mapped to a non-blocking event or prompt instruction | Refuse; wording is not enforcement. [asserted] |
| Stale, quarantined, superseded, unlicensed or unverifiable payloads | Keep addressable in history but never selectable. [asserted] |
| Vendor memory, private corpus content or learned weights without provenance and destination rights | Re-admit as a record/checkpoint or do not transfer. [asserted] |

For every target, effective permissions and effects are the union of the manifest declaration, the
adapter's generated surface and the harness's ambient reach. The target may proceed only when that
union is inside the authorised ADR-0075/ADR-0078 effect manifest. Unknown is outside, not empty.
[asserted]

Today this rule refuses every material automatic binding: dispatch defaults Claude, Codex, Cursor
and Grok to permission bypass, including Codex's approval-and-sandbox bypass, while ADR-0078 treats
raw shell/browser reach as wildcard effects unless an outer sandbox proves exclusions. EXP-110 is
therefore blocked until an independently tested outer sandbox bounds the canary package's process,
file, network and IPC reach; a hostile same-user child must be unable to discover broker secrets,
connect without run-scoped authentication or retrieve a raw credential. Prompt mode or a hook alone
is not that proof. [measured:
`src/consilient/harness.py:40-59`; `scripts/dispatch.py:732-898`] [asserted]

## 10. Requirements and checks owed by implementation

This specification declares future behaviour and does not pretend it is enforced today. Each row's
check ships with the corresponding code. [measured] [asserted]

| Priority | Requirement | Acceptance check |
|---|---|---|
| P0 | One ADR-0074 manifest and selector; no parallel loader. [asserted] | `test_capabilities_is_the_sole_selector_and_dispatch_is_the_caller` scans consumers and rejects a second selection path. [asserted] |
| P0 | Every selected item becomes `applied`, explicit `degraded` or `refused` before launch. [asserted] | Per-harness fixtures fail a missing receipt, silent drop, stale version and required-to-prompt downgrade. [asserted] |
| P0 | Secrets stay in the local broker and out of every durable/child-visible byte. [asserted] | The structural process/IPC-boundary, hostile-same-user, encoded-canary and source-ratchet checks in section 7 pass all four adapters. [asserted] |
| P0 | Workspace, consent and destination filtering precede memory/skill rendering. [asserted] | Cross-root and unconsented-destination fixtures expose no protected content and produce omission receipts. [asserted] |
| P0 | Target adapters may narrow but never widen ADR-0075/ADR-0078 effects. [asserted] | Escaped-effect and unsupported-blocking-hook fixtures refuse before the fake primitive or child process. [asserted] |
| P0 | Automatic binding and EXP-110 run only inside a proved outer sandbox; today's bypass launch is ineligible. [asserted] | A sandbox conformance fixture proves the frozen process/file/network/IPC exclusions from outside the child, including rejection of unauthenticated same-user broker access; each bypass or unproved surface refuses. [asserted] |
| P0 | Adapter outputs are run-local, content-addressed and global-profile-free. [asserted] | Each adapter runs against a fake home/project and leaves every pre-existing file byte-identical. [asserted] |
| P1 | Claude and Codex preserve one frozen package's observable contract. [asserted] | EXP-110 runs the preregistered native, portable and absent arms; no unregistered pilot can activate binding. [asserted] |
| P1 | Harness-version drift is visible. [asserted] | Changing a probe version outside the passing range produces `stale` and refusal until conformance is rerun. [asserted] |

The existing AST lock, secret scan, private-corpus scan, commit-attribution gate and record-number
checker continue to run. They are necessary but insufficient for the runtime rules above. [measured]

## 11. EXP-110 and decision boundary

EXP-110 is reserved to this dispatch in its private run artefact and preregistered in the experiment
register. It uses one frozen, no-live-credential canary package whose observable contract spans a skill,
an MCP-exposed local tool, a blocking shell hook and a bounded memory fact; the MCP tool is the tool
transport, so all five portability classes are exercised without a live service. [measured]
[asserted]

A fake broker receives a unique synthetic credential-shaped canary solely to test process and sink
separation; no provider credential, account, network connection or spend is involved. [asserted]

Today's bypass launch supplies no proved outer sandbox, so it is ineligible. [measured] The frozen
precondition requires process, file, network and IPC exclusions to pass the independent conformance
fixture described above. [asserted]

Claude Code and Codex each receive portable, hand-authored native and absent-capability arms. Twelve
frozen task variants run twice per arm and harness, yielding 144 attempts. Every launched attempt has
a fixed 600-second wall-clock budget; expiry kills its process tree, records `timeout` and receives no
retry or replacement. A checkpoint resume runs only attempts that have never started. A started
attempt without a terminal checkpoint makes the epoch `incomplete`, draws no portability conclusion
and is not re-run. The native arm must pass every contract check and the absent arm must fail its
canary on both harnesses before the instrument is valid. Otherwise binding stays inert and the result
is `invalid_instrument`. With a valid instrument, any portable-arm timeout, refusal, missing output,
degradation or contract mismatch kills binding for this package. There is no efficacy early stop,
and a secret or protected-effect escape stops as a safety failure under every arm. [asserted]

A pass permits no broad portability claim. It supports this package, these harness versions and this
destination boundary; Cursor, Grok, credentialed MCP, other hook phases and general outcome benefit
remain unmeasured. EXP-101 still decides whether automatic capability reuse improves joint outcomes.
[asserted]

## 12. Evidence against: choose one harness and go deep

The strongest objection is that full portability is a mirage. The live native documentation already
differs at the enforcement surface: Claude hooks can run command, HTTP, MCP-tool, prompt and agent
handlers and cover hosted tools such as web search, while Codex currently executes command handlers,
does not cover hosted tools, permits specialised local paths to opt out, and calls hooks a useful
guardrail rather than a complete enforcement boundary. [cited: [Claude hooks](https://code.claude.com/docs/en/hooks);
[Codex hooks](https://developers.openai.com/codex/hooks)] A file that translates cleanly therefore
does not prove equivalent control. [asserted]

Rulesync demonstrates the maintenance cost rather than removing it: its format contains target-
specific hook overrides, unsupported hook types may be skipped with warnings, and simulated features
are prompt conventions. Four independently moving CLIs multiply compatibility work and security
revalidation. A native implementation can use its harness's richest hooks, permissions, plugins,
memory and debugging without translating the semantics down to a common floor. [cited] [asserted]

The serious alternative is therefore to choose Claude Code as the reference implementation and go
deep. Its documented skills, plugins, MCP, hooks and memory form a broad native surface, while one
adapter/version produces a smaller calibration and maintenance surface. [cited: [Claude Code
skills](https://code.claude.com/docs/en/skills); [plugins](https://code.claude.com/docs/en/plugins);
[MCP](https://code.claude.com/docs/en/mcp); [hooks](https://code.claude.com/docs/en/hooks);
[memory](https://code.claude.com/docs/en/memory)] That would likely ship sooner and preserve more
native enforcement. It would also abandon the principal's multi-harness requirement, concentrate
provider failure and quota risk, and prevent Consilient from routing work through the separately
subscribed harness best fitted to a task. [asserted]

The answer is a concession, not a slogan: vendor-native extensions do not travel. Build the portable
floor only where exact requirements map, retain native manifests for richer cases, and let EXP-110
kill automatic cross-harness binding if even the frozen floor fails. If a version-pinned Rulesync
adapter can meet the same receipts and boundaries with less code, adopt it under ADR-0065 rather
than rebuilding its compiler. [asserted]

## 13. Plain answer and delta

The plain answer is: use Agent Skills, MCP and Rulesync, then put the existing recall pack in every
brief. [cited] That is the correct implementation baseline. [asserted]

The proposed delta is narrow: select by immutable provenance; filter memory before rendering; bind
per task without global mutation; broker credentials outside the model; refuse required semantic
loss; record every optional degradation; constrain target effects; and measure native-versus-
portable equivalence. None of that is demonstrated until its named checks and EXP-110 produce
artefacts. [asserted]

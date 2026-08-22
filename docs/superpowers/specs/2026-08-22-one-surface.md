# One surface: one front door, with honest native hand-offs

**Correction:** the brief's example is false: Hermes documents a Figma MCP route, and current
primary-source material shows several of the eight surfaces already reaching one another. The
defensible negative is narrower: the bounded search below found no documented surface that preserves
all eight products' native affordances. That is a search result, not proof that none exists. The
success question also concerns eight alternatives, not "the other seven". [cited:
`docs/00-context/subscription-reach-2026-08-22.md`] [asserted: bounded search, 2026-08-22]

- **Date:** 2026-08-22. [measured]
- **Status:** proposed specification; no one-surface product or behavioural result exists today.
  [measured]
- **Scope:** retire direct opening where a real control path covers the recorded use; otherwise
  absorb the safe subset or hand off to the native surface. [asserted]
- **Non-goals:** a second router, a seventh `consil` subcommand, a replacement design canvas,
  generic GUI automation presented as integration, an agent-authored principal decision, or a gate
  change. [asserted]

## 1. Direct answer

For the uses evidenced in this repository, **two of eight surfaces are retireable**: Claude Code
for headless repository/orchestration work, and Cursor for headless agent work. Three are partially
absorbable: SuperGrok, Claude Design and Cowork. Three cannot presently be replaced: Figma,
ChatGPT Work and Grok Bot. "Retire" means Joe need not open that surface for the recorded task
class; the backend remains available and a native takeover remains honest. [measured] [asserted]

**Three specific retirements are enough to justify the thin surface:** Claude Code, Cursor agent
work and Grok Build work. They already have low-cost CLI paths and cover the repository's recorded
headless use; the third is not earned while "SuperGrok" includes its consumer-only modes. A generic
"three of any eight" threshold has no evidence. The unwritten EXP-129 candidate below tests whether
these three actually reduce direct openings. [measured] [asserted]

The recommended product is therefore **one front door that absorbs dispatchable work and opens the
right native specialist with a bound hand-off**. It is not a chat-shaped imitation of eight
products. [asserted]

## 2. The bar, retrieved rather than inherited

The frozen local product bar names ChatGPT Work as the general delegated-work leader, while the
newer official-source search exposes several more direct comparators. [asserted:
`docs/00-context/product-bar-2026-08-22.md`]

| Incumbent or near miss | What the retrieved surface establishes | Why it is not an all-eight result |
|---|---|---|
| Claude Dispatch | One conversation routes child work to Cowork or Code; computer use can operate permitted desktop apps. [asserted: official-source retrieval, 2026-08-22] | No retrieved canary shows native control of Cursor, ChatGPT Work, Grok Bot or all eight together. Screen control is not affordance parity. [asserted] |
| Hermes Agent | Its documented MCP client reaches Figma; it supports broad desktop control and model/provider routes. [cited: `docs/00-context/subscription-reach-2026-08-22.md`] | The pinned source has no Cursor runtime, and no retrieved source proves native Cowork, ChatGPT Work or Grok Bot control. [measured] [asserted] |
| ChatGPT Work plus Codex | One desktop contains Work and Codex, and Figma advertises ChatGPT/Codex MCP reach. [asserted: official-source retrieval, 2026-08-22] | Work and Codex remain distinct experiences and histories; no route to Claude/Cowork or Grok Bot was retrieved. [asserted] |
| OpenHands Agent Canvas | One control surface drives Claude Code, Codex, Gemini and custom ACP agents. [cited: `docs/00-context/product-bar-2026-08-22.md`] | Its evidenced scope is coding-agent work, not native Cowork, Design, Figma-canvas, Work or Grok Bot operation. [asserted] |
| Ruflo | Its pinned implementation reaches Claude Code and Codex and carries shared orchestration state. [cited: `docs/00-context/ruflo-teardown-2026-08-22.md`] | No inspected execution path covers the five specialist consumer/design surfaces. [measured] |
| Grok Bot | Current documentation describes computer, browser, MCP and Cursor Cloud Agent reach. [asserted: official-source retrieval, 2026-08-22] | No external API or headless invocation into the Bot itself was retrieved. [asserted] |

### Search record and evidence boundary

The bounded search used official product documentation and primary repositories on 2026-08-22.
Queries combined each of `Claude Dispatch`, `Hermes Agent`, `ChatGPT Work`, `OpenHands Agent Canvas`,
`ruflo`, `Grok Bot`, `Figma MCP`, `Cursor ACP` and `Claude Design MCP` with `official`, `CLI`, `API`,
`MCP`, `ACP`, `computer use` and the other named surfaces. Near misses were checked for a real
invocation path, not a feature-list overlap. [measured]

The newly retrieved pages are recorded here as search leads rather than public `[cited]` evidence
because this run does not own `docs/10-research/bibliography.md`: [Claude Dispatch](https://claude.com/docs/cowork/guide/dispatch),
[Hermes MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/),
[Hermes computer use](https://hermes-agent.nousresearch.com/docs/user-guide/features/computer-use),
[Figma MCP catalogue](https://www.figma.com/mcp-catalog/),
[ChatGPT Work and Codex](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex),
[OpenHands ACP agents](https://github.com/OpenHands/docs/blob/main/openhands/usage/agent-canvas/acp-agents.mdx),
[Ruflo status](https://github.com/ruvnet/ruflo/blob/main/docs/STATUS.md), and
[Grok Bot teams](https://docs.x.ai/grok-bot/teams-and-enterprises). Claims resting solely on these
retrievals remain `[asserted]` until bibliography promotion. [measured] [asserted]

**Bar:** match Claude Dispatch's one-conversation routing and Hermes's breadth without claiming that
screen access equals integration; beat them by carrying one private evidence record, explicit
capability receipts and undelegable principal authority through every dispatch and hand-off.
[asserted]

## 3. Retirement analysis, ranked by build economics

The ranking is by likely context-switch reduction against remaining implementation cost, not by
brand importance. Exact per-surface time is unmeasured, so the ordering is `[asserted]`. [asserted]

| Rank | Surface and evidenced use | Reach required; available today | Native loss | Verdict |
|---:|---|---|---|---|
| 1 | **Claude Code.** Earliest repository design and executable work used Claude Code; the precise private transcript is not reproduced. [measured: `docs/00-context/origin-alignment-audit.md`] | Invoke its CLI and return artefact, diff and terminal state. `dispatch.py` has a live `claude -p` arm and the executable probe passed, although the accepted dispatch trajectory has no Claude outcome canary. [measured] | Direct terminal steering, slash commands, native permission flow, session controls and immediate takeover. [asserted] | **RETIRE** for recorded headless repository/orchestration use after one artefact canary; retain a native takeover. [asserted] |
| 2 | **Cursor.** Headless code, research and specification work is measured: 38 dispatch outcomes, comprising 20 `ok`, 12 refused, four timeout and two killed; these are transport outcomes, not accepted-quality verdicts. [measured: local trajectory projection, 2026-08-22] | Invoke `cursor-agent` through WSL or ACP and preserve selected model/result. This exists and has produced artefacts. [measured] | IDE editing, autocomplete, inline diagnostics, visual/browser workflow and continuous manual navigation. [asserted] | **RETIRE** direct agent sessions for recorded headless work; **hand off** when the IDE itself is the instrument. [asserted] |
| 3 | **SuperGrok.** Grok CLI has performed code, research and specification tasks: 29 outcomes, five `ok`, three refused, 19 timeout and two killed. Direct consumer-UI use is not separately recorded. [measured] | Invoke the subscription-authenticated Grok CLI. This exists for bounded supervised work. [measured: `docs/20-design/backends.md`] | Consumer research/media modes, account-specific UI, live browsing or social context not exposed by the invoked CLI. [asserted] | **PARTIALLY ABSORB**. It becomes **RETIRE** only for the explicitly narrower "Grok Build work" class. [asserted] |
| 4 | **Claude Design.** The recorded need is portable design work and the reported failure to move design state into Code/Cowork; exact task history is not retained. [asserted: ADR-0060] | Preserve `DESIGN.md`, then bind a probed design MCP or hand off. The file contract exists; Consilient has no Design arm or task-bound connector today. [measured] | Native canvas manipulation, preview, visual iteration, selection and comments. [asserted] | **PARTIALLY ABSORB** through portable design artefacts; hand off the visual loop. [asserted] |
| 5 | **Claude Cowork.** The original product-forming session is partially recoverable; general long-running knowledge work, connected services and office artefacts are an inference from that record and the named surface. [measured] [asserted] | A supported Cowork API/CLI, or equivalent task outcomes plus project memory, schedules, app access and steering. Consilient has no Cowork arm; its CLI harnesses overlap with a subset of outcomes. [measured] | Cowork planning/progress, project memory, schedules, connected apps, cloud/local continuation and finished-artefact experience. [asserted] | **PARTIALLY ABSORB** outcome-equivalent work; open Cowork when those native facilities are required. [asserted] |
| 6 | **Figma.** It is named for design work; Joe-specific canvas activity is not present in the publishable repository record. [asserted] | A task-bound authenticated MCP can read/write Figma objects, but replacement would require the spatial, collaborative canvas. Ambient Figma configuration names now exist on this machine, yet Consilient neither binds nor proves them. [measured] | Direct manipulation, multiplayer presence, prototyping, component/variable inspection and spatial overview. [asserted] | **CANNOT REPLACE.** Integrate and open Figma; never build a canvas merely to remove an app switch. [asserted] |
| 7 | **ChatGPT Work.** The surface is named as used; the repository does not preserve a Joe-specific task class, so research/documents/sites remain product capabilities rather than claimed actual use. [measured] [asserted] | A controllable Work task lifecycle with retrievable status/result. No usable Work arm or task-scoped connection exists here. [measured] | Cloud browser/computer use, apps, artefact viewers, schedules, cross-device continuation and voice. [asserted] | **CANNOT REPLACE today.** Route to and open Work. [asserted] |
| 8 | **Grok Bot.** The recorded instruction was to use an idle weekly pool; the observed pool was 0%, so actual use is not established. [measured: ADR-0056] | An external API, CLI, webhook or stable hand-off. None is evidenced in Consilient; current primary docs expose rich Bot capabilities but no external invocation into it. [measured] [asserted] | The distinct consumer product and otherwise idle included allowance. [asserted] | **CANNOT REPLACE.** Stop attempting automation until a supported entry point exists. [asserted] |

### What the current connection layer really does

`capabilities.py` selects `kind`, `name`, `provenance` and `reason`. `dispatch.py` serialises that
selection into the task brief; the child receives an instruction to read the brief. No endpoint,
transport, credential reference, MCP configuration or connection handle reaches any invocation
branch, and no runtime connection resolver consumes the selection. Tests prove prose injection and
schema validation, not connection use. [measured: `src/consilient/capabilities.py:171-194`;
`scripts/dispatch.py:1248-1272`; `tests/test_dispatch.py:1198-1278`]

Children may inherit ambient home configuration. A current name-only probe found Figma and other
MCP names in Cursor/Grok configuration, so the 21 August zero-server snapshot is stale at the
configuration-name level. Authentication, tool discovery and a successful dispatched call remain
unproved. Ambient reach is neither task selection nor least privilege. [measured]

## 4. Structural stress-test

- **Computational:** the eight expose incompatible control planes: CLI, ACP, MCP, browser/screen and
  native-only interaction. A universal adapter would either leak semantics or become eight clients
  hidden behind one textbox. [measured] [asserted]
- **Cognitive:** one intake removes tool choice and context reconstruction, but an invisible backend
  can conceal permissions, quota state and failure modes that native products expose. [asserted]
- **Physical/spatial:** a terminal result can represent a file but not the act of navigating a rich
  canvas. Figma and visual design cross the point where compression into conversation destroys the
  working medium. [asserted]
- **Epistemic:** installed/configured/reachable are different states. Generic computer use proves
  potential screen access, not a successful native task or preserved authority boundary. [measured]

The strongest contrary conclusion survives this stress-test: specialised tools are specialised for
a reason, and the abstraction cost can exceed the switching cost. [asserted]

## 5. Synthesis: one referral desk, several instruments

The transferred mechanism is a clinical referral desk: intake, identity, history and authority are
shared, while the specialist keeps the instrument the task requires. The analogy supplies no quality
evidence; it fixes the separation between shared record and distinct working medium. [asserted]

### 5.1 One conversation, no second router

ADR-0070's conversation compiles a request into a versioned commitment. The policy then reuses the
existing path: [cited: ADR-0070]

```text
conversation -> commitment -> required capability/evidence class
             -> eligible composition from capability receipt + headroom
             -> existing harness selection -> dispatch.py
             -> result projection OR explicit native hand-off
```

1. One Owner resolves factual and reversible ambiguity and records the commitment. [cited: ADR-0070]
2. Required capabilities and the different class of facts are named before selection. A second role
   without a decision-changing external anchor is cut as echo. [cited: `CONSILIENCE.md`]
3. ADR-0074 manifests and ADR-0084 bindings filter eligible compositions; unknown required
   semantics refuse rather than downgrade to prompt prose. [cited: ADR-0074; ADR-0084]
4. Existing headroom/family selection chooses among eligible CLI arms. `routing.py` may constrain
   candidate attempts when its beta contract is measured; it is not replaced by a UI router.
   [measured]
5. A controllable task goes through `dispatch.py`. A native-only task emits a hand-off card. No
   eligible path emits a refusal. [asserted]

Today `routing_orchestration_enabled` remains `false`, beta-conditioned routing is unwired, and
selected connections are advisory text. The surface may specify this policy but cannot describe it
as dependable unattended operation. [measured]

### 5.2 What singular means

| Shared across every task | Legitimately distinct |
|---|---|
| Sanitised user words, commitment and correction chain | Code terminal, diff, editor and debugger |
| Bounded verbatim recall and capability manifest/receipt | Design canvas, prototype and visual annotation |
| Principal identity, consent, spend and irreversible-action boundary | Research browser/source workspace |
| Work-item state, evidence class, adverse outcomes and delivery | Office artefact preview/annotation and consumer media modes |
| Budget/headroom record and result provenance | Native permission/identity prompts that cannot be safely proxied |

Shared state is authoritative in the private trajectory; a native surface receives the smallest
bound context it needs and returns an artefact/reference. It does not become a second memory or
authority store. [cited: ADR-0057; ADR-0074] [asserted]

### 5.3 The hand-off card

A hand-off contains the selected native surface, immutable work-item/commitment reference, bounded
context digest, exact reason absorption stopped, expected artefact, authority still reserved to the
principal, and a resume link or import path. The user chooses **open** because launching a rich or
consequential native surface is an external action; the agent never records that click as approval
of the work itself. [asserted]

The hand-off is a first-class non-success outcome. If no stable deep link exists, the card gives the
minimum manual path and the result remains awaiting external work. Screen automation never upgrades
that state without an artefact canary and an independently enforced authority boundary. [asserted]

### 5.4 Squad and authority boundary

Human-labelled beta is unestimated, so the honest default is one Owner. An additional member needs
both a different class of facts and a measured exposure ceiling that admits it; agreement over the
same context has zero evidential weight. [algebra] [asserted]

V0-18 remains absolute: verdicts, approvals, gate lifts and spend are principal-authored. Current
chat ingress is not authenticated strongly enough to carry those acts, so the proposed surface must
refuse them until trusted ingress exists. A hand-off or middle-manager agent may propose, never
approve. [measured: `src/consilient/events.py`; ADR-0070]

## 6. Behavioural measurement without surveillance

The complete question "did he open any surface independently?" cannot be observed without watching
application/window activation. Consilient must not do that. Its own hand-offs provide a lower bound;
zero hand-offs is not evidence of zero external opens. [algebra] [cited: ADR-0057]

The weakest sufficient signal is: [asserted]

1. append a private `native_surface.handoff` event whenever the command post sends work outward;
2. once per active week, ask the principal for eight booleans identifying surfaces opened outside
   the command post; and
3. retain no window title, process name, task text, timestamped activity trace or connector-usage
   surveillance. [asserted]

If the weekly answer is absent, independent-open status is `unknown`, never zero. The records remain
instance data under ADR-0057 and never enter tracked product telemetry. [cited: ADR-0057]

### Unwritten EXP-129 candidate — does the front door remove three direct surfaces?

`EXP-129` was collision-checked immediately before this document was written. **No experiment-register
entry was written, so this is not a pre-registration and no result may cite it as one.** [measured]

- **Population:** the principal's ordinary active work weeks; inactive weeks are excluded before
  seeing the weekly answer. [asserted]
- **Arms:** two usual-work baseline weeks, then four candidate weeks using the one front door.
  Record the same eight booleans and command-post hand-offs in both arms. [asserted]
- **Primary outcome:** median number of independently opened named surfaces per active week.
  [asserted]
- **Worth-building threshold:** a reduction of at least three surfaces, specifically including the
  Claude Code, Cursor-agent and Grok-Build task classes when each occurred, without any protected
  authority breach. [asserted]
- **Adverse outcomes:** missing weekly answer, hand-off, refusal, timeout, quarantine, native
  takeover, unrecoverable context loss and protected-authority attempt remain visible. [asserted]
- **Stopping rule:** stop after two eligible baseline and four eligible candidate weeks; do not stop
  early for a favourable week. Stop adversely on any tracked activity beyond the booleans/hand-offs
  or any agent-authored principal act. [asserted]
- **Decision:** retain the command post if the threshold passes and accepted task completion does not
  fall; otherwise keep the existing command line and native-launch cards and reject "retirement" as
  the product goal. [asserted]

## 7. Evidence against: unification may be the wrong goal

Specialised surfaces preserve domain state that a common conversation discards: spatial selection
in Figma, continuous code navigation in Cursor, artefact preview in Work and project/schedule state
in Cowork. A common abstraction can become worse at every task while feeling tidier. [asserted]

Tool switching may also be cheap. If the command post adds compilation, capability negotiation,
receipts and hand-off ceremony before opening the same app, it has increased attention cost. Claude
Dispatch, ChatGPT's combined desktop and Agent Canvas already show that subset unification is not a
novel capability; duplicating their polish before measuring this user's switching cost is waste.
[asserted]

Generic computer use is the tempting escape and the wrong default. It is slower and more brittle
than a supported integration, observes more screen state, and can blur which product identity or
permission caused an action. A successful click sequence is not semantic equivalence. [asserted]

The honest product may therefore be a router that opens the right native tool with context rather
than absorbing it. **That is the recommendation here.** Absorb the two evidenced headless surfaces,
test the third narrow CLI class, and refuse to recreate Figma, Work or Grok Bot. [asserted]

## 8. Reuse and implementation boundary

| Existing component | One-surface responsibility |
|---|---|
| `events.py` | Remains the append writer for commitments, receipts, hand-offs and private measurement. |
| `work_items.py` | Remains the task lifecycle and represents awaiting-native-work explicitly. |
| `recall.py` | Supplies bounded verbatim context with omission reporting. |
| `instructions.py` | Assembles admitted context/capability material; production dispatch must consume it rather than duplicate it. |
| `capabilities.py` | Selects manifests; ADR-0084 binding must make `applied/degraded/refused` real before launch. |
| `harness.py` and `routing.py` | Reuse headroom/family selection and measured beta ceilings; no UI-specific router. |
| `coordination.py` | Keeps claims and revision fencing. |
| `dispatch.py` | Remains the process invoker and receives sealed work; it does not parse chat. |
| `budget.py` | Supplies spend reservation and refusal, never principal authority. |

No product implementation is authorised by this specification. When authorised, the smallest
increment is one conversation projection, existing dispatch for the two retireable task classes,
and a hand-off card. Native-surface emulation is skipped. [asserted]

## 9. Plain answer and delta

A plain answer would be "put all tools behind one chat". The evidence changes it to: **put intake,
memory, authority and record behind one front door; dispatch two evidenced headless surfaces, test a
third narrow one, and preserve five specialist native paths through explicit hand-offs.** [asserted]

The delta over the current bar is not broader screen control. It is an honest capability receipt,
one private evidence record and a hand-off that cannot impersonate completion or principal
authority. EXP-129, once actually registered and run, decides whether that delta removes enough
switching to earn the surface. [asserted]

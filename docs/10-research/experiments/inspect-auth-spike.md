# X03 spike — can inspect-ai drive a subscription-auth agent?

**Status:** spike result, 24 August 2026. Not a registered experiment; no EXP number
was allocated and none is taken here. British English. Throwaway: none was built.

VERDICT: no

`sandbox_agent_bridge()` cannot drive Claude Code under the CLI's own subscription
login. It is designed to *replace* that login with Inspect's model provider. A live
task through that API would have been a metered provider call, not a subscription
turn, so it was not run. **Do not commit a harness architecture on the strength of
this spike.**

---

## What was asked

Build unit 3 of `docs/20-design/measurement-and-efficiency-2026-08-23.md`: one task
via `sandbox_agent_bridge()` against Claude Code under subscription auth. Written
result either way, before any harness commitment. [asserted: the design's own
wording]

The closed question: can Inspect AI (UK AISI / Meridian Labs) drive a coding agent
that spends an already-paid consumer subscription, rather than an API key?

---

## What was run

No Inspect eval, no Docker sample, no model call, no secret read. The cheapest
thing that settled the question was the published implementation, then a local
probe that did not infer. [measured]

| Probe | Result | Tag |
|---|---|---|
| `importlib.util.find_spec("inspect_ai")` / `inspect_swe` | both missing | [measured] |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN` in the process environment | all unset | [measured] |
| `claude --version` | `2.1.238` on PATH | [measured] |
| `claude auth status` (no prompt, no completion) | `loggedIn: true`, `authMethod: claude.ai`, `apiProvider: firstParty`, `subscriptionType: max` | [measured] |
| `docker version` server | `29.6.1` | [measured] |
| `pyproject.toml` runtime dependencies | still `[]`; no `inspect-ai` | [measured] |

Claude Code is therefore present and subscription-authenticated on this machine.
Inspect is not installed. The named API was not invoked.

---

## What the named API actually does

Retrieved 24 August 2026, not recalled.

Inspect's agent-bridge documentation states that agents are bridged so that "their
native model calling functions are routed through the current Inspect model
provider", and that `sandbox_agent_bridge()` runs a proxy in the sandbox on port
13131 which "relays requests to the current Inspect model provider". The agent is
told to set `ANTHROPIC_BASE_URL=http://localhost:13131`. [cited:
https://inspect.aisi.org.uk/agent-bridge.html, retrieved 2026-08-24]

The implementation matches the page. `sandbox_agent_bridge` in
`UKGovernmentBEIS/inspect_ai` `src/inspect_ai/agent/_bridge/sandbox/bridge.py`
starts that proxy and documents the same rewrite. [cited: raw source retrieved
2026-08-24]

Inspect SWE is the packaged Claude Code agent the docs point at. Its subprocess
environment is not the host login. `claude_code_agent_env()` in
`meridianlabs-ai/inspect_swe` `src/inspect_swe/_claude_code/env.py` sets:

- `ANTHROPIC_BASE_URL` to `http://localhost:{bridge_port}`
- `ANTHROPIC_AUTH_TOKEN` to a dummy `sk-ant-api03-…` placeholder
- `IS_SANDBOX=1`

and the caller comment says the presented model identities are "cosmetic; the
bridge routes to the real model". [cited: raw source retrieved 2026-08-24]

`claude_code()` then enters `async with sandbox_agent_bridge(...)` and execs the
binary with that environment. Its docstring is explicit: `model_config` "is
purely the displayed identity — calls are still bridged to the served Inspect
model regardless." [cited: `src/inspect_swe/_claude_code/claude_code.py`,
retrieved 2026-08-24]

So the CLI binary runs; its subscription session does not. Inference is Inspect's
`--model` provider. Inspect's first-party Anthropic provider requires
`ANTHROPIC_API_KEY`, or `ANTHROPIC_AUTH_TOKEN` as an Anthropic API OAuth bearer
(`oauth-2025-04-20`), not `claude auth login`. [cited:
`src/inspect_ai/model/_providers/anthropic.py`, `_create_client`, retrieved
2026-08-24]

That is why a "one task under subscription auth" through this API is not a
skipped live run. It is the thing the API is built not to do.

---

## Prior art already in this repository

Searched before writing. Nothing had already run this spike. Several documents
already decide the surrounding question.

| Document | What it changed here |
|---|---|
| `docs/20-design/measurement-and-efficiency-2026-08-23.md` | Names Inspect as "Adopt, after BU3" with cost "API tokens only", and BU3 as this spike. The cost column was already the right prediction; the adoption line is not. |
| `docs/20-design/backends.md` and EXP-05 `adapter_claude_code.py` | Already drives Claude Code headless under the CLI's own login (`claude -p …`). One comparison ticket passed. [measured] That is the incumbent for *subscription-auth agent driving*, and it does not use Inspect. |
| `docs/00-context/subscription-reach-2026-08-22.md` | Third-party OAuth against Anthropic is not the same as spending Claude Code's included Max allowance; Hermes's Claude path consumes purchased extra-usage. [cited there] So even Inspect's host-side `ANTHROPIC_AUTH_TOKEN` path, if it worked, would not be the subscription the unit named. Not re-tested here. |
| `docs/20-design/quota-pools-and-routes-2026-08-21.md` | Capability filters; quota schedules. A runner that can only spend API tokens is a different pool from Claude Max. |
| ADR-0044, as amended by ADR-0064 | Subscription-first for inference. Metered calls are the exception. Inspect's documented path is the exception. |
| ADR-0013 | Evaluate on repository history with known human outcomes, not a public benchmark, and never for β. Inspect as a benchmark runner does not measure β even if it ran. |
| ADR-0027, ADR-0065 | Harness, provider and model are separate layers; a component whose error rate must be measured is native. Adopting Inspect would be adopting a runner, not the β instrument. |
| ADR-0031 / 0032, `pyproject.toml` | Stdlib-only core; adding a dependency is a decision, not a spike side-effect. |
| `docs/40-spec/v0-draft.md` | Approved observe-only increment plus gated orchestration. A third-party eval harness in `src/consilient/` would exceed it. This write-up does not. |
| `docs/10-research/experiment-register.md`, `findings.md`, `literature-review.md`, `competitive-landscape.md`, `bibliography.md` | No Inspect AI experiment, finding, review entry or bibliography row. Absence recorded; not claimed as "nothing exists" beyond this search. |
| `docs/decisions/index.md` | 90 ADRs at the index this worktree carries. None authorises committing Inspect as infrastructure. |

The 23 August quota-pool rediscovery named in the dispatch brief is the same
failure mode this search is meant to stop: the answer was already in
`quota-pools-and-routes-2026-08-21.md`. For *this* question the missing piece was
Inspect's own source, not a Consilient document.

---

## The bar (working principle 9)

Full five-stage synthesis is ceremony here once the source is in hand: the
decision is a yes/no on a published API, and the API's own code answers it.
What the protocol still requires is naming the incumbent.

**Incumbent for driving a subscription-authenticated coding agent:** this
repository's EXP-05 Claude Code adapter, which already completed a live ticket
through `claude -p` under subscription login. [measured: `backends.md`] Hermes
Agent's Codex app-server path is the nearest third-party analogue for handing a
whole turn to another CLI's login; its Claude path is not. [cited:
`subscription-reach-2026-08-22.md`]

**Incumbent eval harness for sandboxed coding agents:** Inspect AI plus Inspect
SWE. That is the published bar for *evaluating a model through Claude Code's
scaffold*. It is not a bar for subscription spend. [cited: inspect.aisi.org.uk
and inspect_swe source, 2026-08-24]

Inspect is better than Consilient at graded agent evals (scorers, sandboxes,
stderr beside accuracy). Consilient is better than Inspect at spending an
already-paid CLI login, because that is what EXP-05 already does and what the
bridge is built to prevent. Those are different jobs. Adopting Inspect to answer
the second would be worse than the incumbent. [asserted: the comparison, not a
new measurement]

Killing check for this verdict: a published Inspect or Inspect SWE path that
execs `claude` without rewriting `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN`,
and a live sample whose provider receipt is the CLI subscription rather than
Inspect's model provider. Until that exists, the verdict stays no.

---

## Why the live task was refused

The unit asked for one task through `sandbox_agent_bridge()`. Doing that
honestly requires:

1. adding Inspect (a dependency; AGENTS.md says ask first; this spike forbids
   committing the architecture);
2. an Inspect model provider credential, which on Anthropic is an API key or an
   API OAuth bearer — a metered call, which this dispatch forbids;
3. Docker, which is present, and a sandbox image with Claude Code inside it.

Step 2 would not have been "Claude Code under subscription auth". It would have
been Claude Code as a scaffold in front of Inspect's provider. Running it would
have laundered a no into a yes. The host `claude auth status` already shows the
login the bridge would have discarded.

Inspect's Anthropic provider *does* accept `ANTHROPIC_AUTH_TOKEN` as a bearer.
That is host-side Anthropic API OAuth, not the CLI session. Whether such a token
debits Max, Pro, extra-usage or console is a different experiment, and
`subscription-reach-2026-08-22.md` already warns that third-party Claude OAuth
is not base-plan spend. It was not probed. [asserted: not run]

---

## What this does not decide

- Whether Inspect is a good eval runner when the caller *intends* API-key
  billing. It is the published harness for that job. [cited]
- Whether to adopt Inspect later under ADR-0065's "errors are self-evident"
  tier, as a marketplace runner, with OpenRouter or another permitted metered
  path. That is a separate decision and still must not land from this spike.
- β. Inspect does not supply human reject/accept labels. ADR-0013 still holds.
- Any other Inspect surface than `sandbox_agent_bridge()` / Inspect SWE
  `claude_code()`.

---

## Search log

Queries, 24 August 2026:

- This tree: `inspect-ai`, `inspect_ai`, `sandbox_agent_bridge`,
  `inspect-auth`, `Inspect AI`, `UK AISI` across `docs/`, `tests/`,
  `docs/10-research/experiment-register.md`, `findings.md`,
  `literature-review.md`, `competitive-landscape.md`, `bibliography.md`,
  `docs/40-spec/v0-draft.md`, `docs/decisions/`.
- Near misses: EXP-05 adapters; `subscription-reach-2026-08-22.md`;
  `quota-pools-and-routes-2026-08-21.md`; ADR-0013, 0044, 0064, 0065.
- Retrieved: https://inspect.aisi.org.uk/agent-bridge.html;
  https://inspect.aisi.org.uk/tutorial.html (coding-agents section);
  https://inspect.aisi.org.uk/providers.html (Anthropic);
  `UKGovernmentBEIS/inspect_ai` `bridge.py` and Anthropic provider;
  `meridianlabs-ai/inspect_swe` `claude_code.py` and `env.py`.

Bibliography.md was not in this unit's claim list, so these sources are
recorded here and not promoted there.

---

## Throwaway

Nothing to delete. Inspect was not installed. No eval log, image, or adapter
was written. The only committed artefact of the spike is this file.

A pytest check for the closed verdict was written first and then refused by
the commit-attribution gate: `tests/test_inspect_auth_spike.py` was not in
the dispatch claim list. Working principle 4 wanted it; the claim list and
the gate forbade it. The check is not committed. That is recorded rather
than forced.

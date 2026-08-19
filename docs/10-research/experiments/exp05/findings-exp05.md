# EXP-05 findings — the adapter surface, measured

Run on 19 August 2026 against six coding compositions through seven control paths in
`docs/10-research/experiments/exp05/`. [measured]

## Verdict

**ADR-0001's original adapter-maintainability stopping rule does not fire, but its
indivisible-backend model is superseded in part by ADR-0027.** [measured]

The second adapter did not require an interface redesign. The third exposed a genuine
ticket-schema question: repository paths live in the backend's namespace, not necessarily
the host's. A per-adapter path-translation seam absorbed that difference without changing
the common ticket/result contract. [measured]

Adapter #5 exposed a second genuine schema question: a coding result belongs to a
`domain × harness × provider × model` composition, not to a provider-shaped `backend`
label. [measured] Explicit composition fields absorbed that correction without changing
the common ticket, diff, usage, duration or verifier fields. [measured]

That is evidence for keeping the meta-harness boundary, not evidence that every future
composition will fit it. Only six coding compositions and one comparable ticket have
been exercised. [asserted]

## Adapter results

| # | composition or control path | state | interface consequence |
|---:|---|---|---|
| 1 | Claude Code | Live run passed | Established the initial ticket/result shape. [measured] |
| 2 | Codex | Live run passed | Fit the same shape; no redesign. [measured] |
| 3 | Cursor CLI | Live run and verifier passed; four path-seam tests passed | Required host-to-WSL path translation inside the adapter. Its final JSON also exposed input/output/cache usage that the pre-live adapter had discarded. [measured] |
| 4 | Codex × Ollama × `qwen3:8b` | Live run completed; verifier failed | Runner completion and artifact acceptance must remain separate; Ollama was the provider, not the harness. [measured] |
| 5 | Codex × OpenRouter × `qwen/qwen3-coder` | Live coding run failed before artefact production; verifier failed | Forced the harness/provider/model identity correction. The final isolated attempt returned `Server tool request failed`, made no edit and emitted no usage telemetry; delayed cumulative billing prevents a zero-cost attribution. [measured] |
| 6 | OpenCode × OpenRouter × `qwen/qwen3-coder` | Runner completed and functional tests passed; artefact-scope verifier failed | Validated that the provider-neutral harness reached OpenRouter/Qwen, but it created an unrequested `test_runner.py`. The key crossed into WSL through the environment rather than the command line or a stored OpenCode credential. [measured] |
| 7 | Cursor via ACP v1 over stdio | Live run and strengthened verifier passed | Drove the same Cursor subscription composition through `initialize` → `authenticate` → `session/new` → `session/prompt`; two execution requests were granted once and retained in the experimental transcript. [measured] |

Cursor's path issue is not cosmetic. A ticket containing
`C:\work\repo\file.py` is invalid for a Linux-only process until the adapter translates
it to the mounted WSL namespace. The common schema can carry a repository-relative path;
the adapter owns conversion to the backend's execution namespace. [measured]

The earlier finding that Ollama and OpenRouter “share a model-backed adapter” conflated
provider with execution harness. [measured] Both measured paths actually used Codex as
the coding harness. [measured] OpenRouter remains a standalone provider for other domain
harnesses, while OpenCode or Codex can compose with it for coding work. [asserted] ADR-0027
records the corrected boundary. [measured]

Cursor consumes MCP servers as tools, but its measured external-control protocol is Agent
Client Protocol v1 over newline-delimited JSON-RPC on stdio. [measured] A future Consilience
MCP tool may accept an authorised delegation request from another agent, but the request
must enter the coordinator before that coordinator drives Cursor through ACP. [asserted]
Allowing an MCP caller to spawn Cursor directly would bypass the proposed authority,
resource-admission and trajectory chokepoints. [asserted]

## First comparable coding runs

One synthetic Python ticket was run through six coding compositions. Cursor was added
after WSL authentication; the OpenRouter credential was then supplied and the
Codex × OpenRouter composition was exercised. [measured]

| backend | runner `ok` | verifier | elapsed | reported input tokens | reported cost |
|---|---:|---:|---:|---:|---:|
| Claude Code | true | pass | 25.6 s | 8 | $0.53987225 |
| Codex | true | pass | 20.4 s | 87,356 | unavailable |
| Codex × Ollama × `qwen3:8b` | true | fail | 114.2 s | 559,095 | unavailable |
| Cursor | true | pass | 47.0 s | 74,781 + 92,160 cache read | unavailable |
| Codex × OpenRouter × `qwen/qwen3-coder` | false | fail | 100.9 s | unavailable | unavailable; immediate counter $0 |
| OpenCode × OpenRouter × `qwen/qwen3-coder` | true | fail (functional tests pass; scope fails) | 24.1 s | 40,918 + 40,138 cache read | $0.0170272 session; provider attribution unresolved |
| Cursor via ACP | true | pass | 29.7 s | unavailable | unavailable |

The direct Cursor and ACP rows are two control paths to the same subscription composition,
not independent provider/model observations. [measured] The ACP run changed exactly
`util.py`, passed both tests and retained two allow-once execution requests. [measured]
Its lower elapsed time than the direct Cursor run is one uncontrolled observation and does
not establish that ACP is faster. [asserted]

The token fields are backend-native counters and are not comparable units in this run.
Claude's field counted a narrow reported input; Codex and Ollama reported larger
context-processing totals; Cursor separated input, output, cache-read and cache-write
tokens in its final JSON. [measured]

Inspection of the saved Ollama scratch repository found that `util.py` was unchanged,
`tests/test_util.py` still imported the missing `add` function, and `git diff` was
empty. The saved raw output ended with “no last agent message”; therefore the evidence does
**not** support saying that the model self-reported success. The process-level runner
returned zero and the adapter recorded `ok=true`, while the verifier correctly rejected
the artifact. [measured]

This is direct evidence for working principle 5: backend completion is not an acceptance
signal. The verifier must remain the gate. It is also the cascade's critic function
rejecting a cheap failed attempt on first contact. [measured]

The first OpenRouter-labelled attempt inherited unrelated global MCP configuration from
Codex; the adapter now passes `--ignore-user-config`. [measured] A second attempt waited on
inherited stdin before dispatch; the adapter now closes stdin and a regression check
enforces both isolation properties. [measured] The final diagnostic retained Codex's
structured `Server tool request failed` event, produced no diff, and the OpenRouter key's
usage was zero at the immediate observations. [measured] The later cumulative provider
counter prevents saying the attempts cost nothing. [measured] It remains a failed
coding-harness composition, not a Qwen capability observation or OpenRouter benchmark.
[measured]

The OpenCode composition then reached the same provider/model and implemented the requested
`add(a, b)` function. [measured] It also created an untracked `test_runner.py` duplicating
the two fixture tests; this explained why the initial tests-only verifier reported four
passes rather than two. [measured] The Engineering Ratchet now requires the changed-file set
to be exactly `util.py`, with a regression fixture proving a functionally passing extra file
is rejected. [measured] Re-running that strengthened verifier on the saved repository gives
`tests_passed=true` and `passed=false`. [measured]

The exported OpenCode session fixes the composition identity as provider `openrouter`,
model `qwen/qwen3-coder`, harness version 1.18.18. [measured] Its final response declared
the task complete and treated creation of the extra test runner as successful verification,
despite the explicit “change nothing else” constraint. [measured] This is the
working-principle-5 case the Ollama run itself did not supply: model-reported success is not
an acceptance signal, while the strengthened critic rejects the artefact. [measured]

OpenCode's JSONL step events reported 40,918 input tokens, 40,138 cache-read tokens and
$0.0170272 session cost. [measured] The key-status endpoint reported zero immediately, then
$0.045138255 cumulative usage at a delayed observation. [measured] Because several earlier
Codex attempts may have settled late, the provider total cannot be attributed to the
OpenCode session alone. [measured] The run validates inference transport through
`OpenCode × OpenRouter × Qwen`; it does not validate artefact acceptance. [measured]

## Consequence for EXP-07 and ADR-0003

The failed local attempt took 5.6 times the Codex success latency, 4.5 times the Claude
Code success latency and 2.4 times the Cursor success latency. [measured]

ADR-0003 says a wasted-work multiplier of at least 2× reopens the “no learned routing
policy in v0” decision. This one-task pilot crosses that threshold against the Claude and
Codex frontier successes. Cursor's 2.4× ratio also crosses numerically, but its selected
model identity was not recorded, so it is supplementary rather than a third frontier
comparison. [measured]

It does not establish the population multiplier: this is n=1, on one trivial task, with one
local model and one failed trajectory. [asserted] It does make EXP-07 the highest-priority
routing experiment because the pre-registered threshold has been crossed at the first
observation. [asserted] At a 5× multiplier, ADR-0003's simulation reports +0.123 headroom,
the largest value in its sensitivity table. [simulated]

The honest current verdict is: **ADR-0003 is reopened for investigation, not overturned.**
[asserted]

## ADR-0001 stopping-rule audit

ADR-0001 would be overturned if the second adapter forced enough interface redesign to
show that the proposed boundary was really a Claude-specific wrapper. Adapter #2 did not
do that. Adapter #3 introduced one genuine portability requirement, but it was contained
within the adapter and left the common ticket/result interface intact. Adapters #4, #5 and
the follow-up #6 also fit without redesign. [measured]

The stopping rule therefore does not fire: adapters #2 and #3 did not force successive
incompatible ticket/result interfaces. [measured] ADR-0027 nevertheless supersedes
ADR-0001 in part because the provider-shaped backend identity caused a measured
misattribution even though the outer ticket/result fields remained stable. [measured]

## Limitations

- The comparison has one task and no task-family variation. [measured]
- The failed Codex composition emitted no usage telemetry; delayed cumulative billing means
  neither a zero charge nor a per-attempt provider charge can be recovered. [measured]
- The completed OpenCode composition is one trivial task. Its event-reported cost had not
  appeared in the OpenRouter key-status counter at the immediate follow-up observation,
  and its artefact failed the strengthened scope verifier. [measured]
- Cost fields mix a measured Claude charge with unavailable subscription/local marginal
  costs; “free” must not be inferred from `null`. [measured]
- Elapsed time includes different backend setup and protocol work, so it measures
  end-to-end user wait for this run, not pure inference speed. [measured]
- The Ollama failure identifies a gate and a routing risk; it does not estimate local-model
  failure probability. [asserted]

## Status

**DONE for the original five-adapter surface question; the OpenCode and Cursor ACP
follow-ups are also complete.** [measured] Cursor passed through both its direct CLI and
ACP control paths; the Codex × OpenRouter composition failed before
artefact production; OpenCode reached OpenRouter/Qwen but failed artefact scope; and the result schema
now records domain, harness, provider and model separately. [measured] A domain-general
standalone OpenRouter provider remains follow-up work under ADR-0027 and EXP-22. [asserted]

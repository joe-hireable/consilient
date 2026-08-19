# EXP-05 findings — the adapter surface, measured

Run on 19 August 2026 against the five backend adapters in
`docs/10-research/experiments/exp05/`. [measured]

## Verdict

**ADR-0001's stopping rule does not fire.** [measured]

The second adapter did not require an interface redesign. The third exposed a genuine
ticket-schema question: repository paths live in the backend's namespace, not necessarily
the host's. A per-adapter path-translation seam absorbed that difference without changing
the common ticket/result contract. [measured]

That is evidence for keeping the meta-harness boundary, not evidence that every future
backend will fit it. Only five adapters and one comparable ticket have been exercised.
[asserted]

## Adapter results

| # | backend | state | interface consequence |
|---:|---|---|---|
| 1 | Claude Code | Live run passed | Established the initial ticket/result shape. [measured] |
| 2 | Codex | Live run passed | Fit the same shape; no redesign. [measured] |
| 3 | Cursor CLI | Live run and verifier passed; four path-seam tests passed | Required host-to-WSL path translation inside the adapter. Its final JSON also exposed input/output/cache usage that the pre-live adapter had discarded. [measured] |
| 4 | Ollama-local | Live run completed; verifier failed | Fit through the model-backed adapter; runner completion and artifact acceptance must remain separate. [measured] |
| 5 | OpenRouter | Adapter written; live run blocked on `OPENROUTER_API_KEY` | Uses the same model-backed seam; no interface redesign observed in code, but no live result yet. [measured] |

Cursor's path issue is not cosmetic. A ticket containing
`C:\work\repo\file.py` is invalid for a Linux-only process until the adapter translates
it to the mounted WSL namespace. The common schema can carry a repository-relative path;
the adapter owns conversion to the backend's execution namespace. [measured]

The Ollama and OpenRouter adapters also weaken the original two-path description of
“delegated harness” versus “native open-model execution”. Both can share a model-backed
adapter boundary while differing in transport, credentials, accounting and locality.
[measured]

## First comparable backend run

One synthetic Python ticket was run through every ready backend. Cursor was added after
WSL authentication; OpenRouter remains excluded by its credential blocker. [measured]

| backend | runner `ok` | verifier | elapsed | reported input tokens | reported cost |
|---|---:|---:|---:|---:|---:|
| Claude Code | true | pass | 25.6 s | 8 | $0.53987225 |
| Codex | true | pass | 20.4 s | 87,356 | unavailable |
| Ollama `qwen3:8b` | true | fail | 114.2 s | 559,095 | unavailable |
| Cursor | true | pass | 47.0 s | 74,781 + 92,160 cache read | unavailable |

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

## Consequence for EXP-07 and ADR-0003

The failed local attempt took 5.6 times the Codex success latency, 4.5 times the Claude
Code success latency and 2.4 times the Cursor success latency. [measured]

ADR-0003 says a wasted-work multiplier of at least 2× reopens the “no learned routing
policy in v0” decision. This one-task pilot crosses that threshold against all three
frontier successes.
[measured]

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
within the adapter and left the common ticket/result interface intact. Adapters #4 and #5
also fit without redesign. [measured]

The stopping rule therefore does not fire. Cursor's live capability is now measured;
OpenRouter remains unmeasured until a key is available, so this is not a claim of universal
backend portability. [measured]

## Limitations

- The comparison has one task and no task-family variation. [measured]
- OpenRouter has not completed a live run. [measured]
- Cost fields mix a measured Claude charge with unavailable subscription/local marginal
  costs; “free” must not be inferred from `null`. [measured]
- Elapsed time includes different backend setup and protocol work, so it measures
  end-to-end user wait for this run, not pure inference speed. [measured]
- The Ollama failure identifies a gate and a routing risk; it does not estimate local-model
  failure probability. [asserted]

## Status

**DONE for the five-adapter surface question.** Cursor's follow-up live validation passed;
the OpenRouter key is the remaining backend-validation blocker and is not a reason to keep
ADR-0001's stopping-rule test open. [measured]

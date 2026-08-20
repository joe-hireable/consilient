# Backends — how to run the harness work on any of them

Status: working setup, 19 August 2026. Adapters live in
`../10-research/experiments/exp05/`; this file is the operator's view.
[measured]

One ticket and one outcome schema currently reach six coding compositions through seven
control paths. [measured]

```bash
cd docs/10-research/experiments/exp05
python run_all.py                      # every backend that is ready
python run_all.py claude codex         # or name them
python run_all.py cursor-acp           # Cursor's native external-control protocol
python run_all.py antigravity:gemini-3.7-flash-low  # manual; plan readiness is blocked
python run_all.py ollama:qwen3:8b      # local provider
python run_all.py opencode+openrouter:qwen/qwen3-coder
```

## The six measured coding compositions

| Composition | Adapter | Auth | Accounting | Live state |
|---|---|---|---|---|
| **Claude Code** | `adapter_claude_code.py` | subscription login | reports cost and a narrow token field | Passed the comparison ticket. [measured] |
| **Codex** | `adapter_codex.py` | ChatGPT subscription login | reports session-scale tokens, not cost | Passed the comparison ticket. [measured] |
| **Cursor** | `adapter_cursor.py` | `cursor-agent login` inside WSL | final JSON reports input/output/cache tokens, not cost | Passed the comparison ticket and four path-seam tests. [measured] |
| **Codex × Ollama × `qwen3:8b`** | `adapter_model_backed.py::run_local` | none for Ollama; Codex supplies the harness | no provider charge reported; local resources still have a cost | Runner completed but the verifier failed the comparison ticket. [measured] |
| **Codex × OpenRouter × Qwen** | `adapter_model_backed.py::run_openrouter` | `OPENROUTER_API_KEY` | metered | Failed before artefact production with no diff or usage telemetry; delayed cumulative billing prevents per-run attribution. [measured] |
| **OpenCode × OpenRouter × Qwen** | `adapter_opencode.py` | `OPENROUTER_API_KEY`, passed into WSL without storing it in OpenCode | OpenCode reports tokens and cost per step | Reached inference and passed functional tests, but failed artefact scope after creating an unrequested test file. [measured] |

Cursor also passed through `adapter_cursor_acp.py`, which controls the same Cursor
subscription composition through Agent Client Protocol v1 over stdio. [measured] It is a
second control path, not a seventh provider/model composition. [measured]

OpenRouter is the provider in the last two rows, not the coding harness. [measured] Its
standalone use for non-coding domains is part of ADR-0027 but has not yet produced a live
trajectory. [measured]

OpenCode is the default coding harness when no vendor-native frontier harness is
authenticated. [asserted] Claude Code, Codex and Cursor are candidates only after their
adapter confirms the required login or credential; an installed executable is not enough.
[asserted] Provider/model admission beneath OpenCode remains governed by capability,
verifier reliability, budget and hardware constraints. [asserted]

## First comparable run

One synthetic Python ticket was run through all six compositions. The two OpenRouter rows
hold provider/model constant while changing the coding harness. [measured]

| backend | runner `ok` | verifier | elapsed | reported input tokens | reported cost |
|---|---:|---:|---:|---:|---:|
| Claude Code | true | pass | 25.6 s | 8 | $0.53987225 |
| Codex | true | pass | 20.4 s | 87,356 | unavailable |
| Ollama `qwen3:8b` | true | fail | 114.2 s | 559,095 | unavailable |
| Cursor | true | pass | 47.0 s | 74,781 + 92,160 cache read | unavailable |
| Codex × OpenRouter × `qwen/qwen3-coder` | false | fail | 100.9 s | unavailable | unavailable; immediate counter $0 |
| OpenCode × OpenRouter × `qwen/qwen3-coder` | true | fail (tests pass; scope fails) | 24.1 s | 40,918 + 40,138 cache read | $0.0170272 session; provider attribution unresolved |
| Cursor via ACP | true | pass | 29.7 s | unavailable | unavailable |

The direct Cursor and ACP rows are two control paths to the same subscription composition,
not independent provider/model observations. [measured] The ACP run changed exactly
`util.py`, passed both tests and retained two allow-once execution requests. [measured]
Its lower elapsed time than the direct Cursor run is one uncontrolled observation and does
not establish that ACP is faster. [asserted]

The saved Ollama repository had no file change and the raw output had no final
agent message. The adapter's process-level `ok=true` therefore did not mean
that the artifact was acceptable; the verifier correctly rejected it.
[measured]

The failed local attempt took 5.6 times as long as the Codex success, 4.5
times as long as the Claude success and 2.4 times as long as the Cursor
success. [measured] This n=1 result crosses
EXP-07's pre-registered 2× investigation threshold, but it does not estimate a
population wasted-work multiplier. [asserted]

**Superseded 20 August 2026 — the caution above was vindicated and the crossing did not
replicate.** EXP-07 ran the pre-registered replication at n=30. The **single-attempt median
multiplier is 1.69×**, which does **not** cross the 2× threshold; three of the five fixtures sit
between 1.20× and 1.69×. Only best-of-five crosses, at 17.95× (16.75× when every censored duration
is clamped to its applied timeout). ADR-0003 was **not** reopened, and the registered finding is
that the *retry scaffolding* creates the wasted work rather than the raw local attempt.
[measured]

So the 5.6× above was one draw from a wide distribution, and this paragraph's own hedge — *"does
not estimate a population wasted-work multiplier"* — was the correct reading at the time. Retained
rather than deleted because a pilot that prompted a replication and was then contradicted by it is
worth being able to find.

**Read alongside a defect in the same instrument:** EXP-07's agent timeout overruns by 10–269 s,
and EXP-31 later showed that the timeout can convert a run that would have *passed* into a
censored one. [measured] Durations from either run should be treated as censored-above rather than
exact. See `../00-context/exp31-interleaving-2026-08-20.md`. Cursor's selected model identity
was not recorded, so its 2.4× ratio is supplementary and not a third identified
frontier comparison. [measured]

The token fields are backend-native counters and were not comparable in this
run. Cursor's live JSON separated input/output/cache usage, correcting the
pre-live assumption that it exposed no tokens, but still supplied no cost.
A cross-backend accounting design must use a defined harness measure or a
provider billing measure, not treat these fields as interchangeable. [measured]

The completed OpenCode row reported $0.0170272 in its step events. [measured] OpenRouter's
key-status counter remained zero immediately and later rose to $0.045138255 cumulative
usage. [measured] Several earlier Codex attempts may have settled late, so that provider
total cannot be attributed to the OpenCode session. [measured]

OpenCode added the requested function but also wrote an untracked `test_runner.py`, so the
tests-only verifier initially false-accepted the artefact. [measured] The verifier now
requires exactly the requested changed-file set, and a regression check proves an extra
functionally passing file is rejected. [measured]

The exported session identifies `providerID=openrouter` and
`modelID=qwen/qwen3-coder`. [measured] The model declared the task complete and described
the extra test runner as verification; this self-report remains diagnostic text and cannot
override the failed artefact verdict. [measured]

## Setup notes worth keeping

**The official Cursor CLI build is not installable on Windows.** The official
installer, build 2026.08.11, exited “Unsupported operating system” outside
Linux and Darwin. It is installed in WSL Ubuntu at
`~/.local/bin/cursor-agent`; the adapter drives it through WSL and translates
`C:\…` to `/mnt/c/…`. [measured]

**Do not install `cursor-agent` from npm.** The package found under that name
was an unrelated individual's “Task sequence creator”, last published in
2025, rather than Anysphere's CLI. The official installer is the source used
by this experiment. [measured]

**The local tier did not require a second harness architecture.**
`codex exec --oss --local-provider ollama` supplied the agent loop, so
locality was a provider/adapter choice for this run. [measured] Whether every
open-model backend can use that seam remains untested. [asserted]

**OpenCode is installed in WSL Ubuntu from the official installer.** Version 1.18.18 ran
the comparison through its non-interactive JSON event stream. [measured] The adapter uses
direct WSL arguments rather than a shell command, translates the repository path at the
adapter boundary, closes stdin and passes the provider key only through `WSLENV`.
[measured]

**Cursor's native external-control surface is ACP, not MCP.** The measured ACP client used
newline-delimited JSON-RPC over stdio and retained both allow-once execution requests.
[measured] Cursor remains an MCP client for tool access. [cited] A future Consilient MCP
façade should submit a delegation intent to the coordinator; only the coordinator should
drive Cursor through ACP, so MCP cannot bypass authority, admission or trajectory logging.
[asserted]

**Antigravity is installed but not admitted.** The official Windows installer supplied
Antigravity CLI 1.1.15, and `agy models` returned eleven current Gemini 3.1/3.5/3.6/3.7
variants through a saved keyring identity. [measured] A correctly formed structured
print-mode probe selected `gemini-3.7-flash-low`, silently authenticated a Google
business/GCP profile, then failed before inference with `invalid location: ""` and zero
tokens. [measured] The experimental adapter therefore records the provider as
`google-account:plan-unverified` and is not selected by default. [measured]

The Antigravity CLI documents `useG1Credits=false` as the default, and no CLI-specific
settings file currently overrides it. [cited] The adapter fails closed if that setting is
explicitly true or the settings JSON is invalid; a regression check covers missing, false,
true and malformed states. [measured] Google AI Plus, Pro and Ultra are real subscription
tiers, but Antigravity documents five-hour baseline refreshes specifically for Pro and
Ultra while other plans receive a weekly baseline. [cited] Admission must therefore use
the CLI's live `plan_tier` and quota map, not infer Antigravity headroom from the marketing
name alone. [asserted]

## What the Cursor CLI actually exposes, 20 August 2026

Probed read-only with no inference and no metered call. [measured]

```bash
cursor-agent about  --format json    # cliVersion, model, subscriptionTier, userEmail
cursor-agent status --format json    # authentication state and user identity
cursor-agent models                  # models available to this account
```

Four results, and the fourth matters most: [measured]

1. **There is still no remaining-allowance surface.** `about` returns `subscriptionTier`
   but no quota, no consumed figure and no reset window. ADR-0026's exclusion of Cursor from
   unattended routing therefore stands, re-measured nine days after the original observation.
   [measured] Supervised use under a recorded user attestation remains the only admitted
   mode. [asserted]
2. **Model identity is now machine-readable.** `about --format json` reports the configured
   model — `Gemini 3.7 Flash High` on this account. [measured] EXP-07 recorded that
   "Cursor's selected model identity was not recorded, so its ratio is supplementary"; that
   limitation is now removable by probing before dispatch, which would let a future run treat
   Cursor as a full third comparison rather than a supplementary one. [asserted]
3. **The plan tier is confirmed first-party as `Ultra`.** [measured] EXP-27's delegated
   research reported `pro`; the trajectory already recorded that as a misreport, and this
   closes it with a first-party observation rather than a correction of a correction.
   [measured]
4. **The Ultra subscription already exposes `gemini-3.7-flash-high`.** [measured] ADR-0030's
   middle-management candidate is reachable on included capacity, so the question EXP-30 asks
   does not have to wait for an authorised OpenRouter cap. Under ADR-0027 this is **a
   different composition**, not a cheaper route to the same one: Cursor × Gemini differs from
   OpenRouter × Gemini in harness, system prompting, tool surface and context handling, and
   the two may never be pooled. [asserted]

The same listing marks the Fable entries `claude-fable-5-thinking-high` and
`-xhigh` as **NO ZDR** — no zero data retention. [measured] Any Cursor work that could touch
`../hireable-3.0` or `../jobboard-v2` must account for that before it runs. [asserted]

## Change intelligence is not quota state

Claude Code and Codex publish first-party machine-readable release feeds; Cursor's
inspected first-party changelog is HTML. [measured] Claude, OpenAI and Cursor also expose
public machine-readable service-status data. [measured] These surfaces can invalidate
cached adapter, model, accounting or availability knowledge and require a new capability
probe. [asserted]

They cannot report the remaining allowance for this authenticated account and therefore
cannot increase subscription headroom. [asserted] A quota-policy announcement requests a
fresh authenticated observation; it does not credit the ledger. [asserted] Community
forums or Discord messages may trigger a grounding task but never a routing transition.
[asserted]

Resource windows remain provider-native and separately keyed; a five-hour, seven-day or
monthly bucket is not flattened into one generic reset. [asserted] A current user
attestation can authorise a bounded supervised run where a provider exposes no
machine-readable individual counter, but is labelled user authority rather than provider
measurement and cannot admit unattended work. [asserted] See ADR-0029 and EXP-27.

## What this unlocks

- **EXP-07** now has its first cheap-tier/frontier comparison. Its stopping
  threshold was crossed on n=1, making replication across tasks and models the
  highest-priority next routing measurement. [asserted]
- **EXP-20** can pair a frontier reference with a local tier while holding the
  Codex harness path constant. [asserted]
- **EXP-17 / EXP-18** can use the local adapter once model-download hardware
  admission is specified. [asserted]
- **EXP-16 Arm A′** can use Codex and Cursor to test whether the earlier
  decision convergence survives a model-family change. [asserted]

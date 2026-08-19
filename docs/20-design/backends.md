# Backends — how to run the harness work on any of them

Status: working setup, 19 August 2026. Adapters live in
`../10-research/experiments/exp05/`; this file is the operator's view.
[measured]

One ticket and one outcome schema currently reach five execution paths.
[measured]

```bash
cd docs/10-research/experiments/exp05
python run_all.py                      # every backend that is ready
python run_all.py claude codex         # or name them
python run_all.py ollama:qwen3:8b      # local provider
```

## The five paths

| Backend | Adapter | Auth | Accounting | Live state |
|---|---|---|---|---|
| **Claude Code** | `adapter_claude_code.py` | subscription login | reports cost and a narrow token field | Passed the comparison ticket. [measured] |
| **Codex** | `adapter_codex.py` | ChatGPT subscription login | reports session-scale tokens, not cost | Passed the comparison ticket. [measured] |
| **Cursor** | `adapter_cursor.py` | `cursor-agent login` inside WSL | final JSON reports input/output/cache tokens, not cost | Passed the comparison ticket and four path-seam tests. [measured] |
| **Ollama (local)** | `adapter_model_backed.py::run_local` | none | no provider charge reported; local resources still have a cost | Runner completed but the verifier failed the comparison ticket. [measured] |
| **OpenRouter** | `adapter_model_backed.py::run_openrouter` | `OPENROUTER_API_KEY` | metered | Adapter written; live run blocked on a key. [measured] |

## First comparable run

One synthetic Python ticket was run through four ready backends. Cursor was
added after WSL authentication; OpenRouter remains excluded because its
credential prerequisite is unavailable. [measured]

| backend | runner `ok` | verifier | elapsed | reported input tokens | reported cost |
|---|---:|---:|---:|---:|---:|
| Claude Code | true | pass | 25.6 s | 8 | $0.53987225 |
| Codex | true | pass | 20.4 s | 87,356 | unavailable |
| Ollama `qwen3:8b` | true | fail | 114.2 s | 559,095 | unavailable |
| Cursor | true | pass | 47.0 s | 74,781 + 92,160 cache read | unavailable |

The saved Ollama repository had no file change and the raw output had no final
agent message. The adapter's process-level `ok=true` therefore did not mean
that the artifact was acceptable; the verifier correctly rejected it.
[measured]

The failed local attempt took 5.6 times as long as the Codex success, 4.5
times as long as the Claude success and 2.4 times as long as the Cursor
success. [measured] This n=1 result crosses
EXP-07's pre-registered 2× investigation threshold, but it does not estimate a
population wasted-work multiplier. [asserted]

The token fields are backend-native counters and were not comparable in this
run. Cursor's live JSON separated input/output/cache usage, correcting the
pre-live assumption that it exposed no tokens, but still supplied no cost.
A cross-backend accounting design must use a defined harness measure or a
provider billing measure, not treat these fields as interchangeable. [measured]

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

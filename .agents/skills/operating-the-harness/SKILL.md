---
name: operating-the-harness
description: Use when the operator wants to run Consilient themselves — dispatch a task, read the gates, record a verdict, or stop orchestrating from a chat window. Covers the live command set, the script-not-subcommand split, exhausted-pool refusal, and how to tell the work happened.
---

# Operating the harness

```
THE INTERFACE IS THE COMMANDS. A CHAT WINDOW THAT DISPATCHES FOR YOU IS A DETOUR.
```

Joe's words, 21 August 2026: he is orchestrating via chat and wants the interface
to move to the harness itself. This file is that move. Use it when someone asks
to "run consil", "dispatch", "feed the meter", or "stop talking to the agent and
just use the tool".

## What to type

From this checkout, with this tree on `PYTHONPATH` or installed into the venv
(`pip install -e .`). An interpreter-global install of another worktree will
silently answer with the other tree's code. [measured]

```
python -m consilient.cli --help
python -m consilient.cli doctor
python -m consilient.cli usage
python -m consilient.cli dashboard
python scripts/dispatch.py --probe
python scripts/dispatch.py "the task"
python scripts/dispatch.py --permissions prompt "ask me before tools"
python scripts/verdict.py reject "what was wrong" --checks pass
```

`consil` is observe-only: `record`, `replay`, `beta`, `usage`, `doctor`,
`dashboard`. It does not route. [measured]

Orchestration is `python scripts/dispatch.py`. That is a deliberate split
(ADR-0058): a shipped test pins the `consil` command set, and growing it
without the principal is how a surface change gets laundered.

## Exhausted pools

`--probe` prints installed harnesses and used-percent. The default selector
refuses an exhausted pool. `--allow-exhausted` spends one; only the principal
may pass that flag. Claude weekly has been nearly exhausted on this machine;
Cursor and Grok have not. [measured]

Dispatched children default to **bypass** permissions (`claude --dangerously-skip-permissions`,
`codex --dangerously-bypass-approvals-and-sandbox`, `grok --always-approve`,
`cursor-agent --force --trust`). Override with `--permissions prompt` or
`.harness/permissions.json`. The meta-harness owns that flag, not the child.

Do not open a Claude Code chat to work around a refused pool. That is the
behaviour this skill exists to stop.

## Verify by artefact

A launcher that exits 0 is not evidence the work ran. Open the transcript
under `.harness/dispatch/<run-id>/` and the trajectory under `.harness/log/`.
If either is missing, the dispatch did not happen.

## What this is not

It is not a licence to point the harness at another repository. Gate B still
governs dependence. It is not a licence to put a secret in a public remote.

## Harness support

The commands are stdlib Python. They run under Claude Code, Codex, Cursor and
Grok CLI. Runtimes that cannot read this file get the command list pasted into
the brief.

## Adapted from

The command split is ADR-0058. The refuse-exhausted rule is ADR-0056 D5 /
`scripts/dispatch.py`. The "chat is a detour" rule is the principal's 21 August
instruction, not a design preference.

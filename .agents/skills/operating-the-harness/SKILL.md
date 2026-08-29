---
name: operating-the-harness
description: Use when the operator wants to run Consilient themselves — dispatch a task, read the gates, record a verdict, or stop orchestrating from a chat window. Covers the live command set, the script-not-subcommand split, exhausted-pool refusal, and how to tell the work happened.
---

# Operating the harness

```
THE INTERFACE IS THE COMMANDS. A CHAT WINDOW THAT DISPATCHES FOR YOU IS A DETOUR.
```

Joe's words, 21 August 2026: he is orchestrating via chat and wants the interface
to move to Consilient itself. This file is that move. Don't ask a model. Ask the
Agent Command Post (ADR-0061). Use it when someone asks to "run consil", "dispatch",
"feed the meter", or "stop talking to the agent and just use the tool".

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
python scripts/dispatch.py --task-file brief.md --cwd <this repo, or an instance-allowlisted root>
python scripts/dispatch.py --permissions prompt "ask me before tools"
python scripts/work.py open --ticket PM-1 --accountable joe-brown "the task"
python scripts/recall.py --log .harness/log --query dispatch
python scripts/ingest_transport.py --log .harness/log --file payload.json
python scripts/harvest.py
python scripts/harvest.py --out <a folder outside this repository>
consilient-harvest
python scripts/outbound.py email --to a@b.c --subject "s" --body "t" --authorise-egress "why"
python scripts/outbound.py sms --to +447... --body "t" --authorise-egress "why" --authorise-spend "Twilio SMS 0.04 GBP"
python scripts/computer_use.py --url https://example.com --task "open home" --authorise-egress "look"
consilient-outbound email --to a@b.c --subject "s" --body "t" --authorise-egress "why"
python scripts/verdict.py reject "what was wrong" --checks pass
```

`consil` is observe-only: `record`, `replay`, `beta`, `usage`, `doctor`,
`dashboard`. It does not route. [measured]

Orchestration is `python scripts/dispatch.py`. That is a deliberate split
(ADR-0058): a shipped test pins the `consil` command set, and growing it
without the principal is how a surface change gets laundered.

## The build loop: stopping it, and starting it again

Not `consil`, and not a command you type more than once. The loop is
`.harness/build_loop.py`, run by a Windows scheduled task that fires every five
minutes and has never been stopped. It ticks `.harness/build_driver.py`, which
does everything. [measured]

**To stop it**, and prefer this to killing the task — a tick killed mid-suite
leaves a worktree half-judged:

```
touch .harness/STOP-LOOP
```

The token is read twice per iteration: before a tick, and again after the driver
returns. The loop finishes the tick it is in, writes
`loop: STOP-LOOP present, exiting cleanly after N tick(s)` to
`.harness/build-loop.log`, and exits 0. Nothing is killed and no state is
rewritten on the way out. [measured]

**To start it again**, the whole procedure is one deletion:

```
rm .harness/STOP-LOOP
tail .harness/build-loop.log      # confirm it ticked, within five minutes
```

There is no confirmation step and no second gate. The scheduler kept firing all
through the pause, so the token is the only thing holding it — which is why the
preconditions below are checked *before* the deletion, not around it.

**Do not run `.harness/resume_loop.py`.** It is the only file in the tree whose
name suggests resuming, and it is not the restart command: it force-retires a
hard-coded list of units frozen on 24 August 2026 and starts the loop in the same
breath. It refuses without `--apply` for that reason. [measured]

**Before removing the token**, four things, because the loop is unattended once
it starts:

- `git rev-list --count public/main..HEAD` — and confirm
  `.harness/STOP-PUBLISH` exists unless publishing that backlog is intended.
  Publication is the only irreversible act the driver performs, and
  `publish_if_ready` re-runs the suite itself rather than trusting a stale result.
- One green suite run inside `SUITE_TIMEOUT_S` (900s). `suite_green()` fails
  closed, so a red or timed-out suite means the loop spends its build slots on
  work it cannot then land. Run it in a throwaway clone: `tests/test_supervision.py`
  writes a fixture git identity into the local config, so a full run is not
  read-only. [measured]
- The claims in `.harness/plan-units.json` still name files that hold behaviour.
  Claim disjointness is the driver's real concurrency guard and dispatch refuses
  on overlapping *paths*, so a unit claiming a file whose logic has moved into a
  sibling either writes logic back into a facade or edits a path no claim covers,
  where two apparently disjoint units collide with nothing to detect it.
- `.harness/driver-state.json` `conflicts` is empty, or each entry is one you
  intend a resolver to pick up. Expired `in_flight` slots reap themselves;
  conflicts do not.

## Exhausted pools

`--probe` prints installed harnesses and used-percent. The default selector
refuses an exhausted pool. `--allow-exhausted` spends one; only the principal
may pass that flag. Claude weekly has been nearly exhausted on this machine;
Cursor and Grok have not. [measured]

Dispatched children default to **bypass** permissions (`claude --dangerously-skip-permissions`,
`codex --dangerously-bypass-approvals-and-sandbox`, `grok --always-approve`,
`cursor-agent --force --trust`). Override with `--permissions prompt` or
`.harness/permissions.json`. The Agent Command Post owns that flag, not the child harness.

Do not open a Claude Code chat to work around a refused pool. That is the
behaviour this skill exists to stop.

## Verify by artefact

A launcher that exits 0 is not evidence the work ran. Open the transcript
under `.harness/dispatch/<run-id>/` and the trajectory under `.harness/log/`.
If either is missing, the dispatch did not happen.

## What this is not

It is not a Gate B pass. `consil doctor` still reports the gates shut.
`--cwd` outside this repository requires a root named in the gitignored
instance file `.harness/allowed-cwds.json` (ADR-0063). There is no
`--gate-b-approved`. The unattended loop still refuses a foreign workspace.
Cursor launches take an exclusive lock at `.harness/cursor-agent.lock`
(they race a shared CLI config). WSL cursor exports `GIT_DIR` and
`GIT_WORK_TREE` so a linked worktree is a repository to WSL git.
It is not a licence to put a secret in a public remote, and it is not a
licence to commit another repository's contents into this one. Harvest
(`scripts/harvest.py`) is a private local corpus (ADR-0057); it does not
publish, and it does not start a training run. Outbound email/SMS and
computer-use live in `consilient_connectors`, not the refuse-only product
package. Playwright is instance, not a Consilient dependency. A screenshot
is not a human verdict.

## Harness support

The commands are stdlib Python. They run under Claude Code, Codex, Cursor and
Grok CLI. Runtimes that cannot read this file get the command list pasted into
the brief.

## Adapted from

The command split is ADR-0058. The refuse-exhausted rule is ADR-0056 D5 /
`scripts/dispatch.py`. The "chat is a detour" rule is the principal's 21 August
instruction, not a design preference.

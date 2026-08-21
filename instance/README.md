# Instance configuration

**INSTANCE, not PRODUCT.** Everything in this directory configures *one user's* Consilient
instance. Nothing here may be load-bearing for anyone else: delete the directory and the
repository must still build, test and make sense.

The split exists because Joe asked for it on 21 August 2026: *"Make sure there is clear
differentiation between building the actual consilient harness project and configuring it for me
to work with as the first user."*

## Which bucket is this in?

| | PRODUCT | INSTANCE |
|---|---|---|
| Useful to a stranger who forks the repo? | yes | no |
| Names a person, subscription, machine or private repository? | never | yes |
| Deleting it breaks the build? | possibly | never |
| Lives in | `src/`, `docs/`, `.agents/`, `.github/` | here |

The test that decides a borderline case: **would a stranger's fork be wrong without it, or merely
unconfigured?** Wrong is PRODUCT. Unconfigured is INSTANCE.

Worked example from 21 August: *"a clone with `core.symlinks=false` loads no project skills"* is
PRODUCT — it is true for every Windows contributor and lives in `.agents/skills/README.md`.
*"run `git config core.symlinks true` in each of Joe's forty-odd clones"* is INSTANCE and lives
below.

## Two hard rules for anything in this directory

1. **No secret. Ever.** Not a key, not a token, not a fragment, not an example that looks like
   one. This is stronger than "do not commit one": nothing here may reference a credential a
   public repository could reach. A capability that needs one runs locally or does not run.
   (Joe, 20 August 2026.) `check_secrets.py` scans this directory like any other.
2. **No absolute machine paths, and no assumption about the machine.** Paths here are
   repository-relative. Anything that genuinely needs `C:\Users\...`, a drive letter or a
   WSL mount point is **not committed** — it belongs in a scratchpad outside the repository. The
   reason is not tidiness: this directory is published with everything else, and an absolute path
   is both a machine assumption and a small leak.

## The first user's runtimes

Four runtimes are in use. What each reads matters more than what each costs, because a rule
placed where a runtime cannot see it is not a rule.

| Runtime | Reads | Role here |
|---|---|---|
| Claude Code (Opus) | `CLAUDE.md` → `AGENTS.md`, `.claude/skills/`, `.claude/agents/` | Senior orchestrator; the only one with the agent definitions |
| Codex | `AGENTS.md` | Second family for audits and refutation |
| Cursor | `AGENTS.md` | Third family; ran the cross-family audit that found three holes |
| Grok CLI | `AGENTS.md` | Fourth family; adapter measured, see `docs/20-design/backends.md` |

All four are subscription plans held by the principal. **Use them to create verified value, never
to spend allowance.** No metered API call without a separately authorised numeric hard cap —
`AGENTS.md` and ADR-0044 govern this, not preference.

Only Claude Code reads `.claude/agents/`. That is why every agent definition is a thin wrapper
around a skill, and why the skills carry a *Harness support* section: on the other three, the
brief pastes the portable core in.

## GitHub authentication (no PAT in a settings file)

A personal access token in `~/.claude/settings.json` `env` is readable by every agent
that loads that file. Do not put one there. [measured]

1. Revoke the old token at GitHub → Settings → Developer settings → Personal access tokens.
2. In a terminal you control, not a chat:

```
gh auth login --hostname github.com --git-protocol https --web
gh auth status
```

That stores the credential in Windows Credential Manager. Git and `gh` read it from there.
3. Confirm `GITHUB_PERSONAL_ACCESS_TOKEN` is absent from `~/.claude/settings.json`.
4. If an MCP server still demands an env var, set it in your **user** environment for the
   current session (`$env:GITHUB_PERSONAL_ACCESS_TOKEN = (gh auth token)`) and never write
   the value into a file in this repository, a settings.json, or a gist.

## Local repair after cloning, on Windows

Git for Windows defaults to `core.symlinks=false` without developer mode. A clone made that way
checks `.claude/skills` and `.claude/agents` out as ordinary text files, and **Claude Code then
silently loads no project skill and no project agent.** Once per clone:

```
git config core.symlinks true
rm -rf .claude/skills .claude/agents && git checkout -- .claude/skills .claude/agents
ls -la .claude/
```

Both entries must show as arrows. Verify by looking at the listing, not by the command exiting 0.

## What is deliberately not here

- **Joe's working preferences** — recorded in his own `~/.claude/CLAUDE.md` under *Working with
  Joe* and *Failure modes measured on this machine*. They are personal and global; copying them
  here would create a second copy to drift.
- **Credentials of any kind**, including anything in a harness's own settings file.
- **The names, paths or contents of the private commercial repositories.** `AGENTS.md` permits
  their names and aggregate measured metrics only, and `check_private_corpus.py` enforces it.
- **Per-machine invocation notes** — absolute paths, WSL mount translation, PTY identifiers.
  Machine-specific by definition, so they stay outside the repository.

# Tracked Git and agent hooks

Hooks that live only in `.git/hooks` are not a chokepoint: a fresh clone has none.
This directory is the source. `python scripts/install_hooks.py` points Git at it.

Agent harnesses (Claude Code, Cursor, Grok CLI) load the Python hooks via the
project settings next to this file (`.claude/settings.json`, `.cursor/hooks.json`,
`.grok/hooks/`). They call `python`, not `bash`, because the bash copies under
`~/.claude/hooks/` fail on this Windows machine — Git Bash eats backslashes in
the path. [measured 21 August 2026]

| Hook | What it refuses |
|---|---|
| `pre-commit` | credential-shaped material in the index; while dispatch claims are live, a commit that names no committer, stages a path another live run claims, or exceeds what its own run declared |
| `pre-push` | a push to the public remote that fails the three publication gates |
| `protect-files.py` | edits of `.env`, credential files, lockfiles |
| `auto-format.py` | nothing — formats Python if ruff is present, never fails the edit |

# Cross-platform status

**Measured 21 August 2026** on Windows 11 by static inspection of every tracked `.py`,
`.cmd`, `.yml` and `.md` file in this repository, plus a clean install and CLI run.
Every line reference below was checked in the file. [measured]

Nothing here has been *executed* on Linux or macOS. The claims are about what the code
does, not about a run that happened. Where a claim is an inference from the code rather
than an observation, it is tagged `[asserted]`.

## The short version

| Area | Status |
|---|---|
| `src/consilient/`, `tests/`, `scripts/*.py`, `.github/scripts/` | **Portable.** CI runs all of it on `ubuntu-latest`. |
| The `consil` CLI and `scripts/release_check.py` | **Portable.** Standard library only, `pathlib` throughout, `sys.executable` rather than `"python"`. |
| `docs/10-research/experiments/` | **Windows-bound in ~15 files.** Itemised below. CI never executes any of it. |
| `scripts/run-capture-health.cmd`, `docs/10-research/experiments/exp27/run-daily.cmd` | **Windows only.** No `.sh` or cron/launchd counterpart exists. |
| `.github/scripts/check_private_corpus.py` | Runnable off-Windows **only** via `CONSILIENT_CORPORA`; see below. |

**The structural point.** All four workflows run on `ubuntu-latest`, and `pytest.ini` sets
`testpaths = tests`, so nothing under `docs/10-research/experiments/` is imported or
executed in CI. `ruff check .` *is* repository-wide, which is why the Windows-bound code is
invisible: it is syntactically perfect and semantically Linux-hostile. Conversely, no
workflow runs on `windows-latest`, so nothing verifies the only platform this project is
actually developed and scheduled on. Both halves are untested, in opposite directions.
[measured]

## Fixed on 21 August 2026

- **`.github/scripts/check_private_corpus.py`** hard-coded two absolute `C:\` corpus
  locations, so the leak gate could only be *run* on one machine. `CONSILIENT_CORPORA`
  (an `os.pathsep`-separated list) now overrides them. Behaviour with the variable unset is
  unchanged. Verified both ways: with the corpora present it still reports
  `checking against 2854 distinctive paths from 2 corpora`; with the override pointing at
  a non-existent path and `--require-corpora`, it exits 1 rather than passing. [measured]
  The gate remains local-only by design — the corpora are not on CI and must not be.
- **`scripts/release_check.py`** reports a gate that could not run as `UNAVAILABLE`, never
  as a pass, and exits non-zero for it. A leak scan that silently no-ops off-Windows is the
  A7 defect in `docs/50-publications/P2-guards.md` reintroduced.
- **`tests/test_budget.py`** wrote a trajectory line with `write_text` and no `encoding=`,
  the only such call in the CI-executed suite. Platform default is cp1252 on Windows and
  UTF-8 on Linux; it passed on both by luck, because the payload happened to be ASCII.

## Known limitations, not fixed

These are research instruments, not shipped product. They are recorded rather than repaired
because repairing them means re-running the experiments that produced the published numbers,
which is a decision for the principal, not a tidy-up.

### Would fail, or silently mislead, on Linux or macOS

| File | Line | What happens off-Windows |
|---|---|---|
| `docs/10-research/experiments/exp27/handshake.py` | 156, 169, 170 | `cmd.exe` is the **first** Codex probe and the **only** help probe. `_run_cmd` swallows `FileNotFoundError` in a bare `except Exception` (line 74), so `full_help` is empty and every Codex capability reports `unobservable` / `usable: false` — with no error. A capability-admission probe that answers "no capabilities" is worse than one that crashes. |
| `docs/10-research/experiments/exp57/run_exp57.py` | 491 | `_kill_process_tree` has a `taskkill` branch under `os.name == "nt"` and **no `else: os.killpg(...)`**. The identical function in `exp49/run_exp49.py:492-495` has one. `exp57` creates the tree with `start_new_session=True` (line 545), so on POSIX a timeout orphans it. This is B2 in the guard catalogue — a stop that does not stop. |
| `docs/10-research/experiments/exp47/run_exp47.py` | 144, 158, 172 | `["python", ...]` rather than `sys.executable`. macOS and most current Linux distributions ship no `python` on `PATH`. |
| `docs/10-research/experiments/exp49/run_exp49.py` | 512 | Same. |
| `docs/10-research/experiments/exp05/adapter_cursor.py`, `adapter_cursor_acp.py`, `adapter_opencode.py`, `run_all.py` | various | Invoke the tool through `wsl -d Ubuntu`. On Linux those CLIs are native, so the indirection is backwards; `adapter_cursor.py:113` raises `RuntimeError("wsl not found; Cursor CLI is linux/darwin only")` on the one platform where it runs natively. |
| `docs/10-research/experiments/exp05/adapter_antigravity.py` | 15 | `Path(os.environ.get("LOCALAPPDATA", "")) / "agy" / "bin" / "agy.exe"` at module scope. Off-Windows this silently becomes the relative path `agy/bin/agy.exe`. |
| `docs/10-research/experiments/exp01/red_cell_adjudication.py` | 28 | Absolute `C:\` data path. |
| `docs/10-research/experiments/exp01/independent_replicate.py`, `exp43/run_exp43.py`, `exp45/run_exp45.py`, `exp05/adapter_grok.py`, `exp05/run_all.py`, `exp27/handshake.py` | various | Absolute `/mnt/c/...` or `/home/<user>/...` paths. These are WSL paths on *this* machine, not portable Linux paths. |
| `scripts/run-capture-health.cmd`, `docs/10-research/experiments/exp27/run-daily.cmd` | 12–13 | Windows batch throughout, and both point at a checkout directory that is **not this one** — stale even on Windows. |
| `docs/10-research/experiments/exp27/scheduled-task.xml` | 47 | Windows Task Scheduler XML with an absolute `C:\` command. No cron or launchd equivalent exists. |

### Encoding and newlines

- **Eleven** `subprocess` calls use `text=True` with no `encoding=`, so the decoder is
  cp1252 on Windows and UTF-8 on Linux for the same bytes. The three in
  `exp47/run_exp47.py:143, 157, 171` decide mutation-test outcomes by parsing that output.
- **Seventeen** more pass `encoding="utf-8"` but no `errors=`, so one malformed byte from an
  agent raises `UnicodeDecodeError` mid-run. All are under `docs/10-research/experiments/`;
  `src/`, `tests/`, `scripts/` and `.github/scripts/` already pass both arguments.
- `.gitattributes` sets `* text=auto eol=lf` and no tracked text file contains CR. But 26
  artefact writers call `write_text` / `open(..., "w")` without `newline="\n"`, so on Windows
  they emit CRLF. `src/consilient/events.py:463` gets this right; `scripts/run_fallback.py:89`
  — which writes the committed `.harness/fallback-result.json` that `consil doctor` reads —
  does not. `docs/40-spec/v0-draft.md:441` makes byte-identical replay on Windows and one
  non-Windows environment a release condition, so this is owed. [asserted]

### `.claude/skills` is not a symlink here

Tracked at mode `120000`, but on this machine it is a **17-byte regular file** containing
the literal text `../.agents/skills`. Consequences, both measured: `git status` reports a
permanent ` T` typechange, so "working tree clean" can never hold on this machine; and
`skills-mirror.yml`'s `test -L .claude/skills` passes on `ubuntu-latest` for a reason that
has nothing to do with the invariant — a Linux checkout materialises the symlink from the
stored mode. This is **A9** in `docs/50-publications/P2-guards.md`, still open, and it is
recorded here only because it makes `git diff --check` in the release checklist misleading.

## What would settle this

Add a `windows-latest` leg to `invariants.yml`, and run the experiment instruments once on
Linux. Until one of those happens, the honest claim is the one at the top of this file: the
portable core is verified portable by CI, and the rest is unverified in both directions.

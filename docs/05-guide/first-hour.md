# Your first hour

- **Document class:** W
- **Review by:** 2026-09-24
- **Falsifier:** an adversarial cold follow of this page finds a command that does not do what the page says. That is how the source page was rewritten on 21 August 2026; the same rule applies here.

Class-W admission only. [asserted]

---

You should leave this page installed, and having seen what `consil beta` prints on this checkout. It may refuse to print a rate — that refusal *is* the measurement, and it is the honest one.

The long, command-by-command measurement of install and the traps that broke an earlier draft live in [`docs/00-context/getting-started.md`](../00-context/getting-started.md). This page is the human-entry cut. It is not a byte-for-byte move: the source restates live gate output and a generated rate, both of which this plan forbids in written prose.

## 0. Install

Python **3.13 or newer** — the only version the suite has been run on. No runtime dependencies.

```bash
git clone https://github.com/joe-hireable/consilient
cd consilient
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                            # drop [dev] if you only want the CLI

consil --help
```

Type `consil`. Never `python -m consilient.cli`. On this machine the two have been seen to disagree, silently, because an editable install of a different checkout was on the system interpreter. `consil` only exists inside this checkout's virtual environment; if it is not found, you are not in that environment.

Confirm which tree you imported:

```bash
python -c "import consilient; print(consilient.__file__)"
```

The printed path must sit inside the checkout you are standing in.

## 1. The six commands, and the one that is not a command

`consil --help` lists exactly these:

| | |
|---|---|
| `consil record` | append one checked event to the log |
| `consil replay` | rebuild the state from the log and confirm it still matches |
| `consil beta` | report how often the checks were wrong |
| `consil usage` | report provider headroom and spend ceilings |
| `consil doctor` | report which gates are open |
| `consil dashboard` | render a one-shot HTML summary of the trajectory |

`consil` is observe-only. It cannot route, block or accept anything.

To dispatch work, do not open another chat and do not look for a seventh subcommand:

```
python scripts/dispatch.py --probe
python scripts/dispatch.py "the task"
```

That is a script, not a `consil` command. It is supervised, and it is not a licence to point this harness at a repository you have not named.

## 2. What to type first

Stand **inside the checkout**. Then:

```bash
consil doctor
consil beta
```

`consil doctor` is the authority on whether routing is on. Do not trust a copy of its output in a document; the last time this project kept one, three of four claims were wrong. A non-zero exit is a report, not a crash — do not chain it with `&&`.

`consil beta` reports the rate, or that there is not yet enough data. On a fresh clone it will refuse to invent a number. That is the instrument working.

**`--log` goes on every command** if your log is not the default under the directory you are standing in. A bare `consil beta` reads whatever log sits here; it will print a confident zero if you recorded somewhere else.

## 3. Your first measurement, on your own work

Two events. The first says what your checks decided. The second says what **you** decided. They are joined by one `attempt_id`, and only the second one moves the number.

Do this the next time you review a change and reject it. The exact quoting is shell-dependent and has already bitten this project; the measured PowerShell and bash recipes, including the traps, are in [getting started](../00-context/getting-started.md) §4. The shape is:

1. `consil record` an `attempt.outcome` with `verifier_accept` set to what the checks said.
2. `consil record` an `attempt.verdict` with `human_verdict` set to what you said. `actor` must equal `principal` — no agent can file your verdict for you.
3. `consil --log <the same log> beta`

Only rejections count. If you only ever look at work *after* the checks have passed it, the rate comes out at one by construction and measures nothing. Deliberately review some work whose checks failed too.

## 4. What will go wrong first

1. You typed `python -m` instead of `consil`.
2. You ran `consil` from the wrong directory, or forgot `--log`.
3. PowerShell ate a quotation mark or a space inside a JSON value.
4. A typo in `attempt_id` is accepted on write and then breaks every read. Repair is in [getting started](../00-context/getting-started.md) §7, not here.

When you want more: [what this is](what-this-is.md), [how this is funded](how-this-is-funded.md), [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

---

## Notes for the project, not for the reader

- The plan's exit criterion for this page mentions a bundled fixture and `consil beta --demo`. That is unit 10 of the same plan, not this one, and it does not exist yet. This page therefore sends the reader to `consil beta` on a real checkout, which is what ships today. [asserted]
- `docs/00-context/getting-started.md` is not deleted: this unit's claim list does not include it, and `tests/test_persona_qa.py` still reads it. [measured]

# 0111. Derive the source-file cap from named corpora, raise it to 1,000, and keep it reversible

- **Status:** ACCEPTED
- **Date:** 2026-08-29
- **Deciders:** Drafted in the CTO worktree. **Accepted by Joe on 29 August 2026**, in his own
  words — "ADR accepted" — having read the one-way-door consequence and the evidence against.
  `AGENTS.md` records that a loosening filed under the principal's signature by an orchestrator
  is "the failure worth remembering", which is why it was drafted as PROPOSED and left there
  until he said otherwise.
- **Inquiry tier reached:** T3 measure
- **Executable model:** none — the claim is about what real codebases contain, which is settled
  by counting them rather than by modelling them. The counting scripts are named under Evidence.

## Context

On 28 August 2026 the principal found `.harness/build_driver.py` at 4,101 lines and asked how it
had passed adversarial review. The answer was structural: nothing measured file size, and the
review brief forbade filing a concern that could not be expressed as a failing check. The repair
was `.github/scripts/check_file_length.py` — `LIMIT = 500` with a ratchet, `CEILING` being the
number of offenders allowed today, lowerable and never raisable.

**The rule worked.** Offenders went 59 → 3. Nothing here disputes that a cap should exist.

Three things surfaced on 29 August that the original rule did not anticipate.

**The number came from one unnamed reference codebase.** The checker's docstring justifies 500
against a single comparison tree (median 94, 90th percentile 261, 1.7% of files over 500).
Working principle 9 requires the bar be *recorded so it can be re-checked*; an unnamed reference
cannot be re-checked by anyone, and if it is a tree whose metrics may never be published here,
the bar is permanently unfalsifiable — a wall wearing a measurement's clothes. Principle 10 says
to reach for open data first. That was not done, and doing it now changes the answer.

**The cap manufactured two of its own three remaining violations.** Of the three offenders, two
are over the line only because of the re-export block the cap itself forced:

| file | lines | imports | `__all__` | docstring | actual code |
|---|---|---|---|---|---|
| `src/consilient/events.py` | 596 | 196 | 167 | 38 | ~195 |
| `scripts/dispatch.py` | 544 | 168 | 132 | 35 | ~209 |

Both hold roughly 200 lines of content. Driving `CEILING` to its stated target of 0 requires
`events.py` to shed its remaining logic and become a ~420-line pure manifest — 165 names
re-exported from siblings, zero behaviour. A cap whose terminal state is a file of nothing but
imports is optimising the wrong quantity.

**This is a one-way door as the checker is currently written, and that is the part that matters
most.** The check fails in *both* directions, so raising `LIMIT` to 1,000 forces `CEILING` from
3 down to 1 in the same commit. Restoring 500 afterwards requires *raising* `CEILING`, which the
file's own docstring forbids absolutely. The anti-loosening mechanism would become the mechanism
that welds the loosening shut. **Any acceptance of this ADR that does not also take § Decision
point 2 makes the change irreversible**, and a reversible-decision-made-irreversible is exactly
the class the principal reserves to himself.

## Decision

Replace the cap's justification with named, permissively-licensed, re-measurable corpora, and set
`LIMIT = 1000`. In the same commit, decouple `CEILING` from `LIMIT` so the change can be undone;
add the per-function ratchet that published practice and the empirical literature both point at,
which a per-file cap cannot substitute for; and set the splitter's default budget to the cap
rather than well below it. Merge no existing family back.

Concretely, and all five parts ship together or none do:

1. `LIMIT = 500` → `1000`, with the docstring's single unnamed reference replaced by the corpora
   in § Evidence, each named, versioned and reproducible by a script in the repository.
2. `CEILING` records the limit it was set against — `CEILING = 1` alongside `CEILING_AT_LIMIT =
   1000` — and the monotonicity rule becomes "may only fall *at a given limit*". Lowering `LIMIT`
   back to 500 then re-derives the ceiling instead of failing. Without this, point 1 is a one-way
   door and must be refused.
3. A monotonicity check on `LIMIT` itself, so the cap cannot drift upward without another ADR.
   Working principle 3: a chokepoint without an enforcement rule is not a chokepoint, and the
   absence of one is precisely how 500 came to be changeable by anybody.
4. Enable `ruff`'s `PLR0915` (max-statements) and `C901` (complexity) on `src/`, `scripts/` and
   `.harness/`, ratcheted the same way. This is where the published weight of practice sits, and
   it is the only one of the five that would actually catch `build_driver.py`'s 777-line `main`.
5. `scripts/layer_module.py --budget` default 430 → 900, so a future split targets the cap rather
   than 14% below it.

## Evidence

- `[measured]` **CPython 3.13.11 standard library**, `Lib/` at the pyenv-win build, tests,
  `idlelib`, `lib2to3` and generated tables excluded; 564 hand-maintained files, 270,371 lines.
  **Median 252, 90th percentile 1,184, max 6,351** (`_pydecimal.py`). **27.3% of files exceed
  500 lines** and hold 73.8% of all code; 12.2% exceed 1,000 and hold 51.3%. `typing.py` is
  3,831 lines, `inspect.py` 3,469, `tarfile.py` 3,070. Under this repository's current rule the
  Python standard library would post **154 offenders**. Counted with the checker's own counter,
  `sum(1 for _ in handle)`; script and exclusion rule recorded in the scratch note referenced by
  this ADR's commit, and the measurement is reproducible from any CPython checkout. 29 Aug 2026.
- `[measured]` **Twelve mature third-party libraries** already installed on the workstation —
  mypy 2.3.1, pytest 9.0.3, pydantic 2.13.2, rich 15.0.0, fastapi 0.135.3, starlette 1.0.0,
  click 8.4.2, httpx 0.28.1, jinja2 3.1.6, attrs 26.1.0, urllib3 2.6.3, requests 2.33.1 — with
  vendored trees, test suites and auto-generated tables excluded. 616 files, 305,457 lines:
  median 208, 90th percentile 1,144. **28.4% over 500 lines, holding 77.7% of all code.** Every
  one of the twelve has files over 500; ten of twelve have files over 1,000. Dropping mypy, the
  heaviest contributor, moves the 90th percentile only to 1,016 — the shape is not an artefact of
  one package. 29 Aug 2026.
- `[measured]` **The unnamed reference behind the current cap is an outlier against both.** Its
  90th percentile of 261 is close to the *median* of the two corpora above (252 and 208), and its
  1.7% over-500 rate is one sixteenth of theirs. It may be an excellent codebase; it is not
  representative of the language, and a hard enforced cap was calibrated to it alone.
- `[cited]` **The published per-file bar is 1,000, and 500 appears nowhere.** pylint `C0302`
  `max-module-lines` defaults to **1000** and is enabled by default (`pylint/checkers/format.py`).
  SonarQube `python:S104` "Files should not have too many lines of code" is **1000**, tagged
  `brain-overload`. Checkstyle `FileLength` is 2000. ESLint `max-lines` is 300 but ships **off**,
  and `eslint-config-airbnb-base` explicitly sets it to `'off'`. Retrieved 29 Aug 2026.
- `[cited]` **Most tools and style guides have no per-file cap at all**: `ruff` (pylint's `C0302`
  is unimplemented), `flake8`/`pycodestyle` (`E501` is per *line*), PEP 8, the Google Python
  style guide, LLVM, Django and the Linux kernel coding style. Thirteen tools and guides were
  searched and none names 500. Retrieved 29 Aug 2026.
- `[cited]` **Published practice caps functions, not files.** Google Python: "if a function
  exceeds about 40 lines, think about whether it can be broken up". Linux kernel: functions
  "should fit on one or two screenfuls". Checkstyle `MethodLength` 150; ESLint
  `max-lines-per-function` 50; pylint `max-statements` 50, which `ruff` implements as `PLR0915`.
  This is the load-bearing citation for Decision point 4: **a facade split satisfies a per-file
  cap without improving a single function**, which is what happened here.
- `[measured]` **The tree is over-split against its own cap, so the cap is not the whole cause.**
  Running this repository's own planner and splitter over the ten pre-split modules taken from
  `601a11c`: at a 500 budget the eight that complete need **22 files**; the tree contains **38**.
  `layer_module.py --budget` defaults to 430, and the file-length distribution of
  `src/consilient` shows 24 files in 400–449, 10 in 450–499 and **zero** in 500–549 — a censoring
  cliff at the wall. 29 Aug 2026.

## Evidence against

This section is longer than the case for, because the case against is real.

- `[cited]` **The strongest empirical finding points the other way from a *raise*.** Hatton
  (*Re-examining the fault density / component size connection*, IEEE Software 14(2), 1997)
  reports a **U-shaped** defect-density curve with the optimum around **200–400 LOC** — which is
  *below* the current cap, not above it. Read alone, Hatton argues for tightening to 400.
- `[cited]` Koru et al. (*Theory of relative defect proneness*, Empirical Software Engineering
  13, 2008) cuts the other way — defect proneness rises **sub-linearly** with size, so smaller
  modules are proportionally *more* defect-prone. El Emam et al. (IEEE TSE 27, 2001) found that
  of 24 object-oriented metrics only four survived controlling for class size. **The literature
  is equivocal, and this ADR does not resolve it.** What can be said honestly is that no study
  found supports "smaller files are safer" at the file level, so the cap must be justified on
  review cognition — Sonar's own tag is `brain-overload` — and not on defect reduction. Any
  future prose claiming the cap reduces defects is unsupported.
- `[asserted]` **The corpora measure what respected maintainers tolerate, not what is optimal.**
  CPython's large modules are frequently cited as maintenance burdens. "The incumbent does it"
  is an appeal to practice, and this project's own working principle 9 exists because appeals to
  practice go stale.
- `[measured]` **The yield from the cap change alone is small.** Only three of fourteen families
  were under 1,000 lines before splitting (781, 611, 540). Merging them back recovers 428 lines
  against roughly 3,562 lines of diff — 8.3 lines read per line saved — which is why Decision
  merges nothing. Most of the benefit here is future-facing, and a future benefit is a weaker
  thing than a measured one.
- `[measured]` **A 1,000 cap does not fix the file that caused all this.** `build_driver.py` is
  4,101 lines and remains an offender at any cap under 4,000. Decision point 4 is the part that
  addresses it; points 1–3 do not.
- `[asserted]` **The governance objection, stated at full strength.** Raising a limit because
  meeting it proved expensive is the move `CLAUDE.md` forbids: "do not repair a condition by
  loosening it without an ADR the principal accepts." If this ADR is read as arguing from the
  cost of compliance, it should be rejected. It argues from the evidence base being wrong, and
  the distinction has to survive contact with a sceptical reader or the ADR has failed. Note also
  that **no ADR ever established 500** — a grep of `docs/decisions/` returns no mention of the
  cap or the checker — which means the cap and any change to it are both under-documented, and
  writing this ADR is the repair for the first as much as the second.

## Consequences

**Positive** — the cap becomes re-checkable by anyone with a Python install, which is what
principle 9 asks and what the current rule cannot offer. A future split of a 1,000–2,000-line
module produces two files rather than five, and the facade cost falls with the file count. The
per-function ratchet reaches the 777-line `main` that no file cap will ever catch. And the
splitter stops targeting 14% below the wall, which is what produced 16 more files than the
current cap ever required.

**Negative** — two files that fail today would pass tomorrow, and `events.py` at 596 lines stays
61% plumbing rather than being fixed. The tree keeps 99 files in `src/consilient` where 29 would
do; this ADR does not undo the split and explicitly declines to. Accepting it means accepting
that a rule created ten days ago in response to a real failure was set to the wrong number, which
is a cost to the credibility of every other threshold in the repository, and that cost is not
recovered by being right about this one.

**Neutral but load-bearing** — after this, `CEILING` no longer means "offenders allowed" but
"offenders allowed at `CEILING_AT_LIMIT`". Every future reader of the ratchet must understand
the pair or they will misread the history. The twelve prior ceiling steps (48→47→29→25→24→20→17
→11→10→5→4→3) were all taken at `LIMIT = 500` and remain comparable only to each other.

## Enforcement

- Check: `.github/scripts/check_file_length.py` — `LIMIT`, `CEILING`, `CEILING_AT_LIMIT`, and a
  new assertion that `LIMIT` may not rise without a matching ADR reference in the file.
- Check: `ruff` `PLR0915` and `C901` via `pyproject.toml`, ratcheted per-directory.
- Check: a test asserting `LIMIT == 1000` and `CEILING_AT_LIMIT == LIMIT`, so a silent drift of
  either fails. Today **no test asserts `LIMIT` at all** — `tests/test_living_document_ci.py`
  only asserts the command is wired into `invariants.yml` — which is the gap that let the cap be
  changeable by anyone, this ADR's author included.
- Fails CI: yes, via `.github/workflows/invariants.yml`.
- Added in the same commit as the implementation: **required**. Points 1 and 2 must not be
  separable, because point 1 without point 2 is irreversible.

## What would overturn this

**The experiment that would settle it, and it is this project's own subject.** Measure β — the
rate at which automated checks accept a bad artefact — against the file length of the file each
unit edited, using the trajectory data the harness already records. If β is materially higher in
files above 1,000 lines than below, the cap is doing real work and should come back down to
wherever the inflection sits. If β is flat across the range, or higher in the small facade-heavy
files, then file length is not the quantity to govern and Decision point 4 should absorb points
1–3 entirely.

That experiment is **still not registered**, and this paragraph records the discrepancy rather
than quietly dropping it. The draft said registering it was "a precondition of moving this ADR
from PROPOSED to ACCEPTED under working principle 11". Acceptance came first: Joe accepted on
29 August 2026 and the implementation shipped the same day. The precondition was the author's own
bar, not a machine-enforced one — `test_provisional_adrs_name_a_live_experiment` binds
`PROVISIONAL` ADRs only — but it was written down, and it was not met in the order stated.

It remains unregistered because `AGENTS.md` makes `docs/10-research/` ask-first and "ADR accepted"
is not permission to edit the evidence base. **Registering it needs Joe's separate go-ahead**, and
until then the cap rests on the corpora above: a measurement of what respected codebases tolerate,
never a measurement of what is optimal here. It would be the first per-file cap anywhere justified
by a measured oracle rather than a style opinion, which is the only version of this decision worth
the project's name — and it is owed.

Two cheaper things would also overturn it. A pooled 90th percentile at or below 500 across five
or more named corpora with the statistic pre-registered before looking would refute the evidence
base outright. And if a reviewer finds a defect that a 500-line cap would have caught and a
1,000-line cap would not, the negative consequence above stops being hypothetical.

## Publication candidate?

**No** — but the measurement underneath it might be, later. "What file-length caps do real Python
codebases actually satisfy, and does any of them correlate with escaped defects?" is a question
with a public answer and no good published one, and the β half of it is unique to this project.
That is a paper only after the experiment above has run; the corpus measurement alone is a blog
post at best.

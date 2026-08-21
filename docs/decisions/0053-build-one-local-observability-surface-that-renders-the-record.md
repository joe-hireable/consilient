# 0053. Build one local observability surface that renders the record, and keep building no review surface

- **Status:** ACCEPTED
- **Date:** 2026-08-21
- **Deciders:** Joe Brown (the principal — the decision and its authorisation); Claude Opus 5 (the mechanism and its limits)
- **Supersedes:** [0007](0007-cli-only-no-review-surface.md), in part — see §"What of 0007 survives"
- **Inquiry tier reached:** T1 ground — a construction over an existing record, plus published measurements taken from ADR-0035's bibliography, none of them run on this system
- **Executable model:** none. The model gate (`docs/20-design/inquiry-tier.md`) needs a one-way door, dispersed priors *and* a formalizable objective. This is not a one-way door: the surface is a pure function of the log, so deleting `dashboard.py` and the `consil dashboard` subcommand restores the prior state exactly, and no schema changes to accommodate it. Nothing to model.

## Context

ADR-0007 decided, on 19 August 2026, that v0 would be CLI-only and would **build no review
surface**. That decision has stood for two days and constrained everything since.

On the night of 20–21 August 2026 the principal asked for the opposite, verbatim:

> "I want visibility with different view style optionalities including agent graphs and
> agent raci graphs showing the user beautifully what is being done by what agents. Usage
> across all configured agents amd subscriptions and usage limits in 1 place. A full
> observability dashboard at v1."

Under V0-18 only the principal may author his own decision, and he has authored this one.
That settles authorisation. It does not settle whether ADR-0007 was *wrong*, and an ADR
that recorded "the principal changed his mind" and stopped there would be a worse record
than none. The interesting question is what ADR-0007 got right, what it over-reached on,
and which of its reasons no longer hold.

**A condition changed that ADR-0007 did not model.** ADR-0007 reasoned about the ceiling
`n_max = T_agent_cycle / T_effective_review` — a human reviewing diffs one at a time. At
the time it was written the system ran roughly one agent. As this is written the repository
has **23 live git worktrees** on branches named `fleet-*`, `wt/*` and `cursor/*`.
`[measured]` — `git worktree list`, 21 Aug 2026.

`n_max` prices the human's cost of *reviewing* work. It never prices the human's cost of
*finding out what is running*. With one agent that cost is zero and correctly omitted. With
nineteen concurrent jobs it is the binding cost, and the only instrument for it tonight was
asking an orchestrator to summarise — which is a narrative, produced by the same agent whose
work is in question, with no way to check it against the record.

**And the record cannot see the fleet either.** The trajectory holds 108 lines across two
daily files, of which 105 validate and 3 are the historical refusals ADR-0043 pins. Those
105 events carry 5 distinct top-level `runtime_identity` values, rising to a roster of 21
once the identities named inside `contributors` are counted. `[measured]` So 23 concurrent
worktrees project to 21 identities, none of them connected: **zero** of the concurrency
structure is visible, because no field on any of the 105 events names a parent, a spawn, a
session or a lifecycle state — each searched for by name and found on 0 events. `[measured]` This ADR therefore authorises a surface that renders what
the record *does* hold and states plainly what it does not — not one that fills the gap with
inference.

## Decision

**Build exactly one observability surface: `consil dashboard`, which renders a single
self-contained HTML file from the trajectory and its SQLite projection, and writes it to
disk.** No server, no port, no auth, no bundler, no frontend dependency, no second language.
The file is opened from the filesystem by the user.

**It renders; it never decides.** The surface accepts no artefact, routes nothing, blocks
nothing, and grants no authority. It has no write path to the trajectory at all. Under
ADR-0006 and V0-02 it is a projection, in exactly the sense the SQLite database is, and
under ADR-0035 §1 it is a rendering of the record and never a second record.

**It is an observability surface, not a review surface.** It does not render diffs, does not
collect verdicts, and does not replace git, the editor or the pull request. ADR-0007's
prohibition on a diff-review interface stands unamended and is restated in §Enforcement.

**Where the record cannot answer a question the surface was asked for, it says so in the
place the answer would have gone.** A named absence is the artefact; an inferred graph is
the defect this project exists to catch.

### What of ADR-0007 survives

ADR-0007 made four claims. Three survive.

| ADR-0007 claim | Status |
|---|---|
| No TUI, no desktop app | **Survives.** Nothing here is either. |
| No local web *server* — "a server, a port, an auth question and a second codebase in a second language" | **Survives, and is the reason for the file-not-server form.** A rendered file costs none of the four. |
| A diff-review UI is a bad use of effort, because the lever is the critic tier, not per-diff review speed | **Survives. The arithmetic is untouched** — and this surface does not attempt it. |
| Therefore build **no** review surface at all, and by extension no visibility surface | **Superseded.** This is the over-reach: an argument about the marginal value of *diff-review time* was generalised into a prohibition on *all* visibility, over a cost — finding out what is running — that the arithmetic never contained. |

## Evidence

- `[measured]` 23 live git worktrees against a trajectory whose 105 valid events carry no
  parent, spawn, session or lifecycle field at all — `parent`, `parent_id`, `spawned_by`,
  `session_id`, `started_at`, `finished_at`, `reads`, `inputs`, `accountable`, `consulted`
  and `informed` each appear on exactly 0 of them. The gap between what is running and what is recorded is not an inference; it is
  a count. `git worktree list` and a field census over `.harness/log/*.jsonl`, 21 Aug 2026.
- `[measured]` `consil doctor` reports `routing_orchestration_enabled: false`, with **4 of
  7 gate conditions failing** (A1, A3, B2, B4) and 3 passing (A2, B1, B3), 21 Aug 2026 on
  this worktree. A surface that renders this as anything other than a stopped system would
  be the exact defect the project measures — which is *why* the gate panel is the first
  thing the page renders, above the agent views the request was actually about.
  *(An earlier draft of this ADR recorded 3 failing and 1 unknown. That figure was taken
  from a `python -m consilient.cli` invocation that silently resolved `consilient` to a
  different agent's worktree through an editable install, rather than to this one. The
  reading was of the wrong tree. It is corrected here rather than quietly overwritten,
  because “verify by artefact, never by process identity” is a rule this project wrote
  down and this is what breaking it looks like.)*
- `[measured]` β on the real trajectory is `insufficient_data` at 0 human rejections against
  a floor of 30 (`consil beta`). The dashboard reproduces `Beta.render()` rather than
  recomputing, so it cannot disagree with the CLI about the number.
- `[algebra]` The surface is a pure function of `read_all()` and `projection.build()`, both
  already the only readers of the record. It introduces no new state, so V0-02 — delete the
  database, replay, get identical state — is unaffected by construction rather than by
  testing. Nothing new can drift because nothing new is stored.
- `[cited]` Over-reliance on an automated recommendation fell from ~69% to **0%** when a
  salient display surfaced the error itself, whereas written explanations moved it from ~68%
  to ~66% — Vasconcelos et al. (CSCW 2023, arXiv:2212.06823). This is the finding that fixes
  the surface's shape: **show state, not narrative.** Taken from ADR-0035's bibliography, not
  read first-hand for this ADR; see Evidence against.
- `[asserted]` Rendering to a file rather than serving over HTTP keeps the standing rule that
  no secret reaches a public repository or a hosted service trivially satisfied, because
  there is no service and no network path. The file is written to `.harness/dashboard.html`, which
  this commit adds to `.gitignore` — it was not covered by the existing `.harness/`
  entries, which name only the SQLite projection, and an uncommitted check confirmed it
  was committable before this change. `[measured]` A rendering that embeds the whole
  record must not become a second, unreviewed copy of it in git.

## Evidence against

- `[cited]` **The strongest objection is that this surface is an explanation surface, and
  explanations are measured to make things worse.** Explanations "increased the chance that
  humans will accept the AI's recommendation, regardless of its correctness", with no
  complementary team improvement — Bansal et al. (CHI 2021, arXiv:2006.14779); corroborated
  by Schemmer et al. (IUI 2023, arXiv:2302.02187), where relative AI reliance rose from
  29.59% to 38.87% (p=.05) while relative self-reliance was statistically unchanged (71.87%
  to 69.45%, p=.54) — reliance moved, discrimination did not. A beautiful dashboard is
  precisely the intervention those papers measured, and ADR-0035 already named it "an
  untested intervention on the human half of β". **We decided anyway, on three grounds, none
  of which is that the objection is wrong:** the request is the principal's and this is his
  instrument to choose; the Vasconcelos result says the *error-surfacing* variant is the one
  that helps, so the failing gates are rendered most prominently and no rationale is
  generated for them; and nothing here touches the verdict path, so the β instrument is not
  varied by it. The objection is not answered, only bounded.
- `[cited]` Reducing active involvement produced out-of-the-loop performance decrements in
  decision time after an automated system failed, with correspondingly low situation
  awareness — Endsley & Kiris (1995), *Human Factors* 37(2), 381–394,
  DOI 10.1518/001872095779064555. A dashboard that *substitutes* for reading the record
  would move the user in exactly that direction.
- **Weakness in our own citations, stated plainly:** all four papers above are taken from
  ADR-0035's bibliography rather than read from source for this ADR. ADR-0035 is a
  PROVISIONAL draft. The tags are `[cited]` because ADR-0035 cites them with page-level
  detail, but this ADR adds no independent verification of them and should not be read as
  having done so.
- **No usability evidence of any kind was gathered**, which is the same weakness ADR-0007
  admitted about itself. Two ADRs now decide the opposite thing on the same absent evidence.
  That is worth saying out loud: the reversal is driven by a changed *scale condition* and a
  principal's instruction, not by a measurement that either ADR could have run and did not.
- **Conflict of interest.** This ADR was written by the agent that then built the surface it
  authorises, in the same session. ADR-0007 was likewise written by an agent asked to "decide
  and argue for it". Neither had an independent reviewer.
- **Searched and found nothing against, in one specific place:** no measurement anywhere in
  `docs/10-research/` bears on whether a visibility surface changes β on this system. EXP-42
  is named in ADR-0035 as the experiment that would decide the related question and it has
  not been run.

## Consequences

**Positive.** The 23-worktree fleet becomes inspectable from the record rather than from an
orchestrator's summary. The failing gates acquire a place where they are impossible to miss.
The absences in the schema — no spawn edge, no lifecycle, no reads, no RACI — become visible
as named gaps rather than remaining invisible as unasked questions, which is the cheapest
route to fixing them.

**Negative.** A new rendering surface must be kept honest as the schema changes: any field
the dashboard reads and the log stops writing becomes a silently empty panel. It adds a
second place where a number about β or the gates appears, and two places can disagree — the
enforcement below exists specifically for that. And per Bansal et al., it may raise
acceptance without raising discrimination, which we cannot currently detect.

**Neutral but load-bearing.** The surface is now the most likely first impression of the
project. Whatever it renders prominently becomes what the project appears to be about, which
is why the gate panel outranks the agent graph the request was actually about. It also fixes
the file-not-server form: a later decision to serve this over HTTP is a new ADR and reopens
every question ADR-0007 closed about ports, auth and a second codebase.

## Enforcement

- **Check:** the dashboard's β and gate figures are produced by calling `cmd_beta`,
  `cmd_doctor` and `beta_mod.Beta.render()`, never recomputed. A test asserts the dashboard
  payload's gate conditions and β verdict are equal to the CLI's for the same inputs, so the
  two surfaces cannot drift into disagreeing.
  Fails CI: yes. Same commit as the implementation: yes. (**V0-30**, in
  `tests/test_v0_invariants.py`.)
- **Check:** a failing or unknown gate condition must never render in the passing style. A
  test builds a payload with a failing condition and asserts the emitted HTML carries the
  failing state class for it and does not report the system as enabled. Fails CI: yes.
  Same commit: yes. (**V0-30**.)
- **Check:** ADR-0007's surviving prohibitions. A test asserts the rendered page contains no
  `<script src>`, `<link rel=stylesheet href>` or any other external URL reference, and that
  `consilient` still imports nothing outside the standard library (ADR-0031). This is what
  keeps "rendered file" from drifting into "web app". Fails CI: yes. Same commit: yes.
  (**V0-30**.)
- **Not checked, and named as such:** nothing prevents a future dashboard panel from
  displaying a value the trajectory does not contain. The three checks above bind β, the
  gates and the dependency surface. A panel added later over an invented field would pass all
  of them. The upgrade path, if that ever happens, is to require every panel to declare the
  event field it reads and to fail when that field is absent from the schema.

## What would overturn this

- EXP-42, or any measurement, showing that rendering this surface changes the human verdict
  rate without changing discrimination — the Bansal effect reproduced on this system. That
  would not merely amend the design; it would mean the surface corrupts the instrument, and
  it should then be deleted rather than tuned.
- The fleet shrinking back to one or two concurrent agents, which removes the cost this ADR
  is built on and restores ADR-0007's arithmetic as the whole of the picture.
- Any requirement that the surface be reachable from another machine. That is a server, and
  ADR-0007's four objections — port, auth, second codebase, permanent maintenance surface —
  come back in full and were never refuted here.

## Publication candidate?

No.

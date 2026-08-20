# What to port from Joe's existing repos

> **Scrubbed 20 August 2026 for publication.** This file previously carried detailed internal
> file paths, function and script identifiers, hook filenames, a verbatim quotation from a
> private assessment document, and the commercial product the repository belongs to. All of
> that is forbidden by `AGENTS.md` — *"their code, file contents, excerpts and detailed file
> paths may never be committed here"* — and it had been present since the initial commit.
>
> Found by a pre-publication leak audit run by `cursor-agent` (`gemini-3.7-flash-high`) under
> WSL, cross-referencing 5,256 real paths from the private corpora against this tree. The
> orchestrator's own scan had searched for paths *prefixed* with the repository name and
> structurally could not have found paths written bare. A different model family searching a
> different way is the whole point of the rule this project is named after. [measured]
>
> **What survives here is every lesson and every aggregate measurement. What is gone is
> everything that identifies or reconstructs the private codebase.** The repository names and
> aggregate metrics are explicitly permitted; nothing else from those repositories is.
>
> The material is still in this repository's git history, in the initial commit. Scrubbing the
> tip does not remove it from a clone. See the publication note at the end.

Read 19 Aug 2026 via filesystem access: `jobboard-v2` and `hermes`.

`hermes` is an empty `create-next-app` scaffold. Nothing to take.

Everything below is from `jobboard-v2`. **Most of v0 already exists there**, scattered across a
commercial product.

---

## 1. The single most valuable asset: the assessment methodology

A prior multi-agent codebase assessment in that repository documents its own method, and the
shape is the useful part: a fan-out of read-only discovery agents over separate sources;
independent verification of every lead against primary evidence; a second fan-out of scoring
agents over a fixed rubric; a citation-fabrication audit sampled per scorer; then synthesis.

The aggregate outcome, which is what may be quoted: **197 leads, of which 185 confirmed, 11
nuanced and 1 fabricated and excluded; a fabrication audit of 5 citations per scorer across 50
sampled, with 0 failures. A measured hallucination rate of roughly 0.5%, and it was caught.**
Validated on a real codebase of about 3,900 files. [measured]

This is a working multi-agent system with an adversarial verification tier. It is also the
bounded-meeting primitive, already built — and it respects the multi-agent theorem, because
discovery agents work independent sources and verification agents re-derive from primary
evidence. Neither is debate.

**Port this shape first.** It becomes the critic tier.

## 2. The ratchets — this is the β instrumentation, already written

That repository carries roughly twenty CI-blocking check scripts. Their *kinds* are what
transfers:

| Kind of ratchet | What it enforces |
|---|---|
| Documentation-count check | Headline counts in docs against the codebase, within a tolerance |
| Coverage ratchet | Test coverage cannot drop |
| Test-deletion guard | Tests cannot be deleted to move the bar |
| Skipped-probe guard | The number of skipped probes cannot increase |
| Row-security coverage | Every table read under row-level security has a policy |
| Governing-document hash | Drift in a governing document requires an ADR in the same PR |
| Action pinning | CI actions are SHA-pinned, and the check pins itself |
| Invariant-probe coverage | A fixed set of invariant probes stays covered |

Most are traceable to a specific documented incident — a migration-journal drift, an index
lost to a schema push, production schema drift — each of which produced its guard afterwards.
**This is the Engineering Ratchet, implemented and proven to fire.** It is also exactly the
kind of verifier suite whose β you would want to measure.

## 3. The cascade skeleton

A provider-routing layer selecting by model-id prefix, with a circuit breaker and a kill
switch; a separate resolver choosing a model by task class; and decode-time schema enforcement
on structured output, hardened in response to two documented production incidents.

## 4. The permission model

A tool registry of roughly 72–82 tools registered at module load, filtered at turn time by
channel, sender kind, relationship state and role, **fail-closed**, before the model sees the
catalogue. Tool errors return a structured result that **loops back to the model** rather than
aborting the run.

## 5. The guard layer

Editor hooks that block writes to secret-bearing files before the edit lands, alongside
formatting and workflow nudges. Plus a hermetic test setup that neutralises leaked environment
variables and dead-ends the database URL, so tests can never reach a staging environment.

## 6. Other patterns worth stealing

- **Closed error contract**: an RFC7807-style problem type plus a registry, with a test that
  walks every call site and fails on an unregistered code. Zero ad-hoc error JSON across
  roughly 206 routes.
- **Async-by-default model work**: no model call in any user-facing request path; queue
  drainers claim work transactionally.
- **Transactional row claiming** — directly reusable for ticket claiming by parallel agents.

---

## The lesson that must not be repeated

The assessment's first major finding was that a documented, unified model-access boundary was
**in practice five access paths**. The circuit breaker and kill switch covered roughly a dozen
call sites, while the **highest-cost paths — the agent turn loop and the judge — bypassed them
entirely**. Seven modules constructed their own SDK clients. Two different vendor SDKs for the
same provider. [measured]

The idea was right. The enforcement was never written — despite the same repository containing
the exact pattern that would have fixed it: a custom lint rule banning raw HTTP calls in the
agent layer.

> **A chokepoint without a lint rule banning bypass is not a chokepoint.**

Under agentic development this drift happens faster. It is invariant **I1**, and it is the
reason this project must never ship a declared boundary without its enforcement in the same
commit.

**It has already happened here, in this repository, to this repository's own append-only
trajectory log.** `append()` was the documented sole writer and the only place validation ran;
on 20 August 2026, 92 of 93 logged events had been written straight to the file by something
else, and three of them carried a claim that the validator forbids. [measured] The lesson was
written down in this file on 19 August and violated in the same repository within a day. I1 is
not a historical anecdote.

Second lesson, same assessment: a flagship pipeline had **no producer** — a scheduled job
drained a queue that nothing ever filled, undetected because an empty queue is
indistinguishable from a healthy one. Hence invariant **I2**: documented behaviour ships with
the test that proves it.

---

## Publication note

Scrubbing this file does not remove the original text from git history; it was introduced in
the initial commit. Publishing this repository publicly with its history intact would publish
that text. Three options, and the choice is Joe's because it concerns his private commercial
material:

1. Rewrite history over this file and `0006` before making the repository public. One-time,
   changes every commit SHA, and the untouched history can be kept in a private mirror.
2. Publish a fresh public repository from the scrubbed state with a squashed initial commit,
   keeping the full history private.
3. Keep the repository private.

Nothing here is exposed while the repository is private.

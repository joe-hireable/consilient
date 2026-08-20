# 0036. Upstream-first — adopt, contribute, and never silently fork

- **Status:** PROPOSED
- **Date:** 2026-08-20
- **Deciders:** Joe Brown (the principle), Claude Opus 5 (the mechanism)
- **Inquiry tier reached:** T1 ground — a policy, plus this repository's own record of it
  working three times
- **Executable model:** none. The thresholds are preferential.

## Context

Joe, 20 August 2026: *"adopting generally accepted world class baselines and standards instead
of always reinventing the wheel unless it provides significant value… if we use mempalace or
something or mem0 or graphify or a combination we should PR upstream rather than custom
engineering everything… We should also always be experimenting, always be contributing —
never accept the status quo but start from the best and if we find improvements, share them."*

And: *"Upstream PRs should be treated with the same care and rigour that we expect. Setting an
example for other contributors."*

**Half of this is already policy.** ADR-0005 wraps rather than builds a model library.
ADR-0017 says *"Adopt, don't build. Three layers, all existing tools."* ADR-0023's fifth
evidence rule requires a prior-art search at T2 and above and records that *"'Someone already
built this, MIT-licensed' has been the correct answer three times on this project. Finding
that it exists is a valued contribution, not a wasted PR."* The v0 specification says
Consilience *"wraps rather than builds"* hardware fit. [cited]

**What is new is the obligation to give back.** Adoption is settled; contribution is not
written anywhere, and neither is the standard our outbound work must meet.

## Decision

### 1. Prior art is a build gate, not only a review gate

ADR-0023 requires a documented prior-art search before a T2+ change is *merged*. That is too
late: by then the thing is built. The search happens **before implementation starts**, and its
result is recorded whichever way it goes. [asserted]

Building something that already exists is permitted only where the existing thing has been
tried and found wanting **on a stated, checkable dimension** — not because integrating it
looked like more work than writing it.

### 2. When an adopted dependency needs to change, the default is a pull request upstream

Not a fork. Not a vendored copy. Not a monkey-patch that quietly diverges.

This applies to every dependency the project adopts, and to the specific candidates named so
far: MemPalace, Graphify, `llmfit`, and any harness adapter surface. [asserted]

### 3. An outbound pull request meets the same standard as an inbound one

This is the clause that makes the rest more than a preference. ADR-0023 gates contributions to
*this* project by blast radius, with claims tagged, "Evidence against" required at T2+, numbers
citing the source that measured them, and any invariant shipping with its check. **The same
tier applies to what we send out.** [asserted]

Concretely, a pull request from this project to another carries:

- a reproduction or a failing test that the change makes pass, or a stated reason none is
  possible;
- the measurement behind any number in the description, citing the source that measured it —
  never a figure laundered through a summary;
- what the change might break and how the author checked;
- the honest limits of the evidence, including sample size;
- and, where the change asserts an invariant, the check that enforces it.

**With one important restraint.** Rigour is proportional to blast radius in *their* project,
not ours, and their conventions govern their repository. A two-line typo fix does not get an
evidence section. Turning up with this project's document format uninvited is not setting an
example, it is being a nuisance. Read their `CONTRIBUTING.md` first and follow it. [asserted]

### 4. A fork or local patch is debt, logged and paid

Where an upstream fix is needed before it can land — a blocking bug, an unresponsive
maintainer, a rejected but necessary change — a local patch is permitted, and is recorded with
the upstream issue or PR link, the reason, and what would let it be removed. It follows the
pattern already proven by `docs/00-context/gate-bypass-log.md`: the deviation is allowed, and
made countable. [cited]

**A fork with no upstream attempt recorded is not permitted.** [asserted]

### 5. Contribute findings, not only code

Where an experiment here produces a result that bears on an upstream project — a measured
defect, a benchmark that contradicts a claim, a limitation nobody has written down — it is
offered to them as an issue, in their terms, whether or not it suits this project.

Tonight produced two candidates already: Ollama's static estimator has no `gemma4` case, so
its pre-load KV estimate for that architecture is out by roughly an order of magnitude
(`fs/ggml/ggml.go` v0.21.1, the sliding-window correction gated on `Architecture()=="gemma3"`);
and Ollama silently downgrades an oversized context rather than failing, so a model can appear
to fit while delivering a context too small to use. [measured] Both are useful to that project
and neither has been reported.

### 6. Error tracking is the worked example, and the answer is not to build one

Joe asked for *"error tracking and self-correction natively… we need a native version or an
adopted open source version"*. This ADR's own rule answers it: **do not build one.** Sentry is
already connected here and self-hostable; GlitchTip and OpenTelemetry are open alternatives.
Collection is solved. [asserted]

The part nobody's error tracker does is the part that matters here. Working principle 4 — the
Engineering Ratchet — says that when something fails, the fix goes into code as a check, a type
or a constraint, never into a prompt. **No error tracker knows whether a fix became a check.**
So the native piece is not collection; it is the link from an error record to the enforcement
that now prevents it, and the detection of a recurrence, which is proof the ratchet did not
fire. [asserted]

That has a measurable purpose already registered. EXP-34 counts what catches each error — an
enforced check, or somebody noticing — and its baseline of 2 in 9 came from an agent
hand-enumerating its own mistakes at the end of a long session. [measured] That is not an
instrument. An adopted error tracker, plus the ratchet link, is what makes EXP-34's denominator
real rather than recalled.

## Evidence

- `[cited]` ADR-0023 rule 5, and its record that prior art was the correct answer three times
  on this project.
- `[cited]` ADR-0005 and ADR-0017 already choose adoption over building, with named tools.
- `[measured]` Tonight's local-model work produced two upstream-reportable findings within a
  single session, which suggests the supply of them is not the constraint.
- `[measured]` `gate-bypass-log.md` is the proven pattern for permitting a deviation while
  keeping it countable, and it exists because a documented boundary in `jobboard-v2`
  fragmented into five access paths when nothing enforced it.

## Evidence against

- **Upstream pull requests are slow and may be rejected**, and this project has one maintainer.
  A blocking dependency change could stall work for weeks. §4 is the release valve, and it will
  be used more often than §2's framing implies. [asserted]
- **Our rigour is ours.** A maintainer who wants a one-line fix may find an evidence-tagged
  description tiresome, and "setting an example" can shade into lecturing someone in their own
  repository. §3's restraint is load-bearing and easy to forget. [asserted]
- **Adoption has its own supply-chain cost**, which ADR-0016 already records. Every adopted
  dependency is a trust decision, and "use the best existing thing" is not free when npm is
  being actively wormed. [cited]
- **The contribution obligation is unbudgeted.** Nothing here says how much of a solo
  maintainer's week may go to other people's repositories, and an obligation with no budget is
  either ignored or unbounded. [asserted]
- **This ADR asserts a cultural norm and enforces only its documentable parts.** Whether the
  project actually contributes is not decidable from a lint rule. [asserted]

## Consequences

**Positive.** Less bespoke code to maintain, and improvements benefit everyone rather than
sitting in a private tree. The project's own evidence discipline becomes visible outside it.

**Negative.** Slower when a dependency blocks us, and real time spent in repositories that are
not ours.

**Neutral but load-bearing.** Every adopted dependency now carries a standing relationship
rather than a one-off decision.

## Enforcement

- Check: a vendored or forked dependency without a recorded upstream issue or PR link fails a
  lint over the dependency manifest and the patch directory.
- Check: a local patch entry without a removal condition fails the same lint.
- Check: a new module that duplicates a declared dependency's stated capability fails review
  unless a prior-art record exists naming the dimension on which that dependency was
  insufficient.
- Check: the error-tracking integration records, for each distinct error, the enforcement that
  now prevents it or an explicit `no_check_yet`; a recurrence of an error marked prevented
  fails CI, because that is the ratchet slipping.
- These ship with the code that implements them, not before it. [asserted]

## What would overturn this

- Two or more upstream pull requests rejected on grounds that make the adopted dependency
  unusable, which would make §2's default the wrong default for that dependency and force an
  honest fork with its reasons recorded.
- A measured case where adopting cost materially more than building — integration, supply-chain
  review and upstream negotiation exceeding the build — which would move the default for that
  class of component.
- The contribution obligation consuming a share of the maintainer's week that visibly damages
  this project's own progress. That is measurable from the trajectory, and it should be
  measured before anyone claims it is not happening.

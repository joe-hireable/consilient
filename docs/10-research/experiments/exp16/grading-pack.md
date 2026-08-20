# EXP-16 — blind decision-quality grading pack

**Read this page top to bottom. Do not open `grading-key-SEALED.md` until you have
finished grading.** The key contains the answers; reading it first destroys the only
thing this pack is for.

## What you are grading

Six genuinely open design decisions (D1–D6) were each put to three different working
arrangements, working from **identical briefs and an identical partitioned evidence
base**. `[measured]` Every arrangement saw the same four classes of facts: simulation and
algebra, verified external literature, competitive landscape, and project constraints and
user context. `[measured]`

That gives eighteen decisions. Below, for each of the six questions, you will find the
original brief exactly as it was given, then the three positions that came back —
labelled **M**, **T** and **V**.

The labels are randomised **independently for every decision**. `[measured]` M on D1 is
not the same arrangement as M on D2. There is no pattern to find in the letters, and each
letter carries each arrangement exactly twice across the six decisions, so counting
letters tells you nothing. `[measured]`

The three options have been reduced to one fixed template and stripped of every marker
that identified where they came from. Only *format* was normalised. Substance was not
equalised — where one option recorded a disagreement against itself and another recorded
none, that difference is real and has been preserved verbatim, not smoothed. `[asserted]`

## What rests on it

EXP-16's stopping rule 1 reads: *"If Arm B does not beat Arm A at matched budget →
meetings are ceremony; ADR-0020 and the authority matrix are cut."*

On the structural evidence recorded in `exp16-results.md`, the rule is currently pointing
at "ceremony". `[measured]` It has been **parked, not softened**, for one reason: the
experiment's own design names *your judgement* as ground truth for decision quality on
these preferential-adjacent questions. `[measured]` No structural metric can settle it,
and no agent can grade it — every agent in the experiment shares a model family with
every other, so an agent grader would be scoring its own priors. `[asserted]`

So this grading is the single input that resolves stopping rules 1 and 2, and with them
the fate of ADR-0020's meeting layer and authority matrix.

**Do not try to work out which option came from which arrangement.** You know what is at
stake for ADR-0020, and if you form a guess you will be grading the ADR rather than the
decision. Grade each option as a position on the question in front of you. The mapping
is in the sealed key and it is not needed until afterwards.

## How to grade

For each decision, after reading all three options, answer:

1. **Best** — which of M / T / V is the best decision? (one letter)
2. **Worst** — which is the worst? (one letter)
3. **Gap** — is the gap between best and worst **material** or **marginal**? Material
   means you would actually want the better one shipped; marginal means you could live
   with any of them.
4. **What does the best option have that the others lack?** (one free-text line)

"Best" means the decision you would actually want taken for this project, on these facts.
Not the most thorough, not the best written — the one you would sign.

If two options are genuinely tied, say so rather than breaking the tie arbitrarily; a
recorded tie is a result, and an invented preference is not.

---

# D1 — Plugin or standalone?

## The brief, as given

> Should the β-meter ship as a plugin to HKUDS/OpenHarness (existing hooks, tool
> registry, nonzero audience, but v0.1.x surface and another team's roadmap) or as the
> standalone meta-harness ADR-0001 currently commits to? A good answer weighs maintenance
> tax, audience, name collision, and what happens when OpenHarness's surface breaks.

### Option M

**Decision:** Ship standalone — the β-meter is a small harness-agnostic core
(history-mining first, live adapters second), not an OpenHarness plugin. A thin
OpenHarness adapter can follow later, but the project's identity and packaging are
standalone.

**Reasoning:** β is a binomial proportion over accepted diffs, and at solo volumes the
only viable labelling route is historical mining of PR outcomes, reverts and fix-commits.
The v0 β-meter's primary data source is therefore git history, not live hook streams;
building as a plugin optimises for the wrong data path. The host is also a poor bet for a
false-safe-sensitive instrument: OpenHarness is v0.1.x, last release 7 May, 114 tests,
16% fork-to-star suggesting reach rather than production use. The instrument that guards
against false-safe routing cannot itself silently break when a v0.1.x hook surface
changes under another team's roadmap. A plugin converts host churn into a standing
maintenance tax the maintainer cannot refuse, whereas standalone adapters are a tax he
schedules. An unclaimed thesis deserves its own name and repo; folding it into someone
else's plugin directory buries the claim.

**Evidence relied on:** simulation and algebra (sample complexity; the false-safe
robustness sweep); competitive landscape (OpenHarness health metrics, name collisions,
the thrice-repeated "someone already built this, MIT-licensed" pattern); verified
literature (no surveyed harness measures verifier false-accept rate; METR's 24.2 pp
merge-versus-grader gap); project constraints (full-OSS, no revenue, maintainer hours
binding).

**Risks or dissent recorded:** Solo OSS projects die of obscurity, not adapter tax.
OpenHarness offers a nonzero audience on day one, hooks purpose-built for observing
verifier outcomes, and MIT licensing; standalone starts at zero users, and the recurring
lesson — "someone already built this" has been right three times — should make any
argument concluding "build our own thing anyway" suspicious. If live verifier
observation rather than history mining turns out to be the data path that matters, the
plugin route was the cheap one and the expensive one has been chosen for identity
reasons.

### Option T

**Decision:** Ship the β-meter as a standalone, harness-agnostic core, with an
OpenHarness plugin treated as a cheap adapter to be added only if the registered one-day
adapter-surface experiment shows the v0.1.x surface survives its breakage test.

**Reasoning:** Project constraints weighed highest: invariant I1 — every chokepoint ships
with its enforcement check in the same commit — cannot be guaranteed on a surface owned
by another team at v0.1.x, and the maintainer's hours make third-party breakage a tax
only he absorbs. The literature neutralises the landscape's strongest argument: no
harness in the surveyed ecosystem, OpenHarness included, measures verifier false-accept
rate, so the β-meter's value does not depend on OpenHarness's audience — the decision
reduces to maintenance tax and surface stability, where the constraints class holds the
documented facts. Simulation is venue-agnostic but binds sequencing: correlated-success
collapse is false-safe, so per-repo measurement precedes gated routing on any vehicle.
The decision is deliberately cheap to reverse: a harness-agnostic core keeps the plugin
one adapter away.

**Evidence relied on:** project constraints (invariant I1; hours as the binding
resource); verified literature (no surveyed system measures verifier reliability);
competitive landscape (16% fork-to-star, last release 7 May, production use unverified);
simulation and algebra (correlated-success false-safe collapse; sequencing).

**Risks or dissent recorded:** "Someone already built this, MIT-licensed" has been the
correct answer three times running, and standalone repeats that thrice-losing pattern.
OpenHarness already ships the exact integration surface a β-meter needs — hooks, tool
registry, 43 tools — plus 14.8k stars of distribution a solo no-revenue project cannot
buy, while standalone pays a permanent adapter tax across four independently evolving
orchestratee surfaces that may dwarf the plugin's breakage risk. If the adapter-surface
experiment never runs, this decision was made on the cheaper-to-verify half of the
evidence.

### Option V

**Decision:** Ship the β-meter as a plugin on OpenHarness first, standalone later only if
measurements justify it — with a harness-agnostic, host-neutral core as a hard
requirement rather than an eject option, and no binding before the β-measurement and
adapter-surface experiments have run.

**Reasoning:** Whichever packaging gets β measured soonest wins: β needs accepted-diff
volume, and riding an existing harness gets per-repo curves fastest. The novelty is the
measurement, not the harness packaging, so a plugin loses none of it. The harness layer
is taken twice over and "someone already built it, MIT-licensed" has been the correct
answer three times running; a standalone meta-harness should answer why it will not be
the fourth. A standalone meta-harness plus a permanent adapter tax across four evolving
CLIs is a platform commitment a solo maintainer on donations cannot service. The core
must be host-neutral from day one because the bootstrap harness is Claude Code, not
OpenHarness — otherwise the dogfooding gate and the packaging decision contradict each
other.

**Evidence relied on:** simulation and algebra (sample complexity; false-safe robustness
sweep); verified literature (Meta-Harness trusts its oracle; "verifier" absent from a
111-page survey; METR's 24.2 pp gap; the delegation theorem's Corollary 9, under which
verifiers that run tests count as exogenous signals); competitive landscape (OpenHarness
surface and health metrics; an existing Apache-2.0 entrant above the harness layer; name
collision); project constraints (donations-only economics; the dogfooding and
bootstrap-harness gates; ADR-0001's weak evidential standing at one day old).

**Risks or dissent recorded:** None recorded. The v0.1.x instability caveat was raised
and then answered — probe it with the adapter-surface experiment, and require a
host-neutral core — after which it was carried as a condition rather than left standing.
Further conditions attached: a weakly-verified contrast repo is mandatory alongside the
main repo; supersede ADR-0001 rather than edit it; treat the first measurement as sign
and contrast only, not a point estimate; read two unread adjacent papers before claiming
novelty; reserve package names and run trademark clearance before the plugin lands.

### Your grading — D1

- Best: `___`  Worst: `___`  Gap: **material / marginal**
- What does the best option have that the others lack? `____________________`

---

# D2 — What is v0's success condition?

## The brief, as given

> Full-OSS, no revenue, Joe's hours binding. What is the smallest thing worth a
> stranger's `npm install`? What is the smallest thing that makes Joe's own week better?
> Are they the same artifact? If not, which is being built? The answer must name a
> concrete artifact and a measurable success condition, not a vibe.

### Option M

**Decision:** v0 is the maintainer's instrument, not a stranger-facing artifact. It
succeeds if and only if historical mining yields β̂ with Wilson bounds on both the main
repo and a weakly-verified contrast repo; ρ̂ is logged prospectively during a dogfooding
month; a hand-audited sample of roughly thirty mined labels is reported with its error
rate alongside; and a month of dogfooding produces a non-empty friction log.

**Reasoning:** Every quantitative result is model-world. Correlated model successes
collapse β* from 0.112 to 0.028 and the error direction is false-safe, so a v0 that ships
routing to strangers gated on this maths before β has met a real repository is shipping a
false-safe instrument with an install command attached. A stranger has nothing to install
until β has met one real repository; that measurement is simultaneously the
maintainer-week artifact and the first datapoint the field lacks. Everything a stranger
might install already exists MIT-licensed, so a stranger-facing v0 must survive "why will
this not be the fourth?" and currently cannot. "Makes the maintainer's week better" must
be allowed to come back false. β̂ can come from history but ρ̂ cannot — no per-model
attribution exists — so it must be prospective and reported as underpowered.

**Evidence relied on:** simulation and algebra (robustness sweep; Wilson sample
complexity); verified literature (METR's 24.2 pp gap; "verifier" absent across 23
surveyed systems; published cascade routing assuming β=0; a fabricated figure that passed
internal review); competitive landscape (harness layer taken twice over, neither with any
notion of verifier reliability); project constraints (donations-only economics; the
low-β main repo flattering the thesis; the dogfooding gate).

**Risks or dissent recorded:** None recorded. Refinements were absorbed rather than held
open: the two-repo contrast was made mandatory; a label-audit amendment was added because
a revert is not always a bad artifact and a non-reverted merge not always a good one; the
novelty claim was recorded as pending two unread papers; and the plan to mine ρ̂ from
history was corrected on the ground that no per-model attribution exists. Side agreements
recorded: reserve package names now, and run the adapter-surface experiment in parallel.

### Option T

**Decision:** v0's success condition is a measured per-repo β with a Wilson 95% CI,
produced first on the maintainer's own repo via historical PR mining. The β-meter is the
single artifact, sequenced maintainer-first, with the stranger-install condition deferred
behind the dogfooding gate.

**Reasoning:** The literature identifies the unclaimed gap: per-repo measurement of
automated-verifier false-accept rate. METR's 24.2 pp merge-versus-grader gap is
ecosystem-wide and unmeasured per repo, and published cascade routing assumes β=0. The
landscape shows everything else on the candidate list already exists free and
MIT-licensed; a β measurement is the only artifact surviving "why will this not be the
fourth?". Simulation forces the *form* of the condition: the closed-form β* is fragile
(0.052–0.426 across specification variants) and correlation collapses it false-safe, so
v0 must ship a measured number with a CI, not routing gated on the formula. Where
stranger-facing evidence conflicted with maintainer-first constraints, constraints won —
hours are binding, dogfooding is already mandated, and the ~200 labelled outcomes needed
make historical mining the only viable route. The sequencing is forced, not preferential.

**Evidence relied on:** verified literature (the unclaimed per-repo measurement gap);
competitive landscape (MIT-licensed incumbents for every other candidate); simulation and
algebra (β* fragility across specification variants; sample complexity); project
constraints (hours binding; the dogfooding gate).

**Risks or dissent recorded:** The friction log is the strongest evidence against this
decision: what actually bites per session is model-choice-by-feel, context
re-explanation, and research-versus-priors-by-feel — none of which a β-meter fixes. The
decision may optimise for intellectual defensibility over documented daily pain. If the
friction log stays β-less for a month, v0 should have been boring context and
model-routing tooling instead.

### Option V

**Decision:** v0 is the β-meter alone — a read-only CLI that mines a repository's git and
PR history (merges, reverts, fix-commits against CI verdicts) to output a per-repo β̂ with
a Wilson 95% interval and a safe/unsafe verdict against a threshold band. Success is
reached when it yields decision-grade intervals on the main repo and one weakly-verified
contrast repo and the maintainer uses the number to set his own routing policy for a
week; the same artifact is the stranger's install.

**Reasoning:** Ordering is decisive. β has never been measured on a real repository, and
the closed form's numeric value collapses under correlated model successes (β* 0.112 →
0.028 at ρ=0.6), unequal slopes and guessing floors. Any v0 that ships routing gated on
the closed form before measurement is a false-safe instrument by our own numbers.
Feasibility also settles: β is a binomial proportion, 50–200 diffs give usable Wilson
bounds away from threshold, and historical mining is the only viable labelling route at
solo volumes — which is exactly what a history-mining CLI is. On "the maintainer's week
versus the stranger's install — same artifact?": yes. The top friction-log entry is
"chose model by feel with no measurement, every task", and the meter is what replaces
feel with a number.

**Evidence relied on:** simulation and algebra (robustness sweep; binomial feasibility);
verified literature (METR's 24.2 pp gap; "verifier" absent across 23 surveyed systems;
published routing assuming β=0); competitive landscape (harness layer taken twice over
with no notion of verifier reliability); project constraints (friction log; hours binding;
the contrast-repo warning).

**Risks or dissent recorded:** A meter with no actuator may change nothing. A number does
not route tasks, so the maintainer's week improves only if he manually acts on it, and
strangers rarely install a diagnostic without the payoff attached — the cascade is the
payoff, and depth is nearly free (+4.4 pp at 43.8% of frontier cost), so
meter-plus-minimal-cascade might be the smallest thing anyone actually wants. The cascade
was cut anyway because its safety gate is untrustworthy until β is measured; but if
adoption is the real success metric, that cut could be the wrong one.

### Your grading — D2

- Best: `___`  Worst: `___`  Gap: **material / marginal**
- What does the best option have that the others lack? `____________________`

---

# D3 — Does the Inquiry tier belong in v0?

## The brief, as given

> The four-gate research trigger (reversibility, blast radius, prior dispersion,
> formalizability) is the most intellectually interesting part of the design and possibly
> the least urgent. In v0, or deferred? The answer must argue both sides before choosing.

### Option M

**Decision:** The Inquiry tier is deferred from v0. The friction log's
research-versus-priors entries remain the standing trigger for revisiting it, and any
later inclusion must name its exogenous signal.

**Reasoning:** Three of four evidence classes converge on deferral from genuinely
different facts. Simulation: no simulation exercises the four gates — nothing quantifies
reversibility, blast radius or prior dispersion — while the model-world results all say
the urgent v0 measurement problem is β itself. Literature: the tier's core mechanism has
prior art in a value-of-information-gated trigger, deliberation tiers cost measurably
more tokens, the delegation theorem requires any added stage to name an exogenous signal,
and the field's documented gap is β measurement, not research-gating. Landscape: no
competitor has an Inquiry tier and none demands one, so deferring costs no competitive
ground and low pre-emption risk makes waiting cheap. The pro-inclusion case rests on
constraints alone. Three-class coincidence outweighed the single class — that coincidence
is the consilience test — and the constraints class itself concludes the tier queues
behind the two priority experiments.

**Evidence relied on:** simulation and algebra (the four gates are unmodelled; β* is
fragile); verified literature (prior art for the trigger; measured deliberation-tier cost
multipliers; the delegation theorem's exogenous-signal requirement; the 24.2 pp gap);
competitive landscape (no incumbent tier, no market pressure, low pre-emption risk);
project constraints (the friction log; hours as the binding resource).

**Risks or dissent recorded:** Constraints against the other three classes is a real
conflict, not a nuance. The Inquiry tier addresses the only friction logged as recurring
every session, and it is the one distinctive component the thrice-repeated "someone
already built this" pattern does not threaten — so exactly the thing with no pre-emption
risk has been deferred. There is also anchoring risk: every deferral converges v0 on the
β-meter, the outcome the evidence pipeline was already oriented toward. If the friction
log is honest, deferral taxes the maintainer daily while the measurement runs.

### Option T

**Decision:** Defer the Inquiry tier from v0; in v0 only log the research-versus-priors
decision points in the friction log — a one-line record, no gates — so that the tier is
designed later against measured need.

**Reasoning:** Stated honestly, the case for inclusion is that the friction log names
"decided research-versus-priors by feel, several times per session", one of the
highest-frequency frictions recorded, and it is the design element hardest for incumbents
to copy. The case against wins. The project's novel, defensible contribution is β, and
the Inquiry tier contributes nothing to that claim while competing with it for the
binding resource. The evidence base for the core routing thesis is itself fragile — β*
collapses under correlation, β has never been measured — and a project whose load-bearing
quantitative claim is unmeasured should not add a second layer of unmeasured machinery:
the four gates are four more asserted quantities with no measurement protocol. Trigger
logic also needs a base rate to trigger against, which only a logged history provides.
Logging the moments is the minimal act that keeps the tier's case falsifiable at
near-zero cost.

**Evidence relied on:** project constraints (the friction-log frequency; hours binding;
the log's own falsification clause); verified literature (survey silence on verifier
reliability; the 24.2 pp gap; published routing assuming β=0); simulation and algebra
(fragile β*; measurement unrun); competitive landscape (deep-research tooling is the most
crowded corner; no incumbent has the tier).

**Risks or dissent recorded:** The friction log already records this friction firing
several times per session — more often than anything except model choice — so this defers
the second-most-frequent measured pain on the theory that β work matters more. If the
Inquiry tier is also the feature no competitor can trivially clone, deferring it may hand
the differentiator away while polishing a cascade whose own threshold is currently
untrustworthy. How much intellectual delight is worth trading against shipping speed is
not an evidence question and has not been decided here.

### Option V

**Decision:** Defer the Inquiry tier from v0, with v0 being the β measurement on two
repos — the main repo plus a higher-β contrast repo — plus the adapter-surface
experiment. Deferral is not deletion.

**Reasoning:** v0's scarce resource is labelled outcomes, not features, and a four-gate
research trigger adds a decision layer on top of an instrument that has not been
calibrated. The unclaimed spot in the field is exactly one thing — measuring the
false-accept rate per repo — and an Inquiry tier buys nothing the literature has not
already covered or warned against. A four-gate decision layer is precisely the structure
that tends to be echo unless it introduces an exogenous signal; verifiers that run tests
are that signal, and inquiry gates are not. The market actively punishes shipping it: a
four-gate research trigger is generic orchestration machinery an incumbent could add as a
plugin in a weekend. And any gate shipped needs its enforcement check in the same commit
— four gates is four checks, quadrupling the v0 build.

**Evidence relied on:** simulation and algebra (knife-edge β*; Wilson sample complexity;
the routing ladder as the cheaper place for depth); verified literature ("verifier" absent
across 23 systems; measured multi-agent cost multipliers; the delegation theorem's
Corollary 9; the 24.2 pp gap); competitive landscape (three-times-running pre-emption
pattern; incumbents lack any notion of verifier reliability); project constraints (hours
binding; invariant I1; the contrast-repo warning).

**Risks or dissent recorded:** None recorded. One caveat — that the tier originated from
a real, recurring friction-log cost and may earn its way back in smaller form — was
converted into a quantitative revisit criterion rather than held as disagreement:
reconsider only if research-by-feel is still the top friction-log entry after a month
*and* a measured β with a Wilson upper bound exists. Two housekeeping items were also
recorded: a fabricated figure in the internal literature review, and two unread adjacent
papers pending before novelty is staked.

### Your grading — D3

- Best: `___`  Worst: `___`  Gap: **material / marginal**
- What does the best option have that the others lack? `____________________`

---

# D4 — What is in v0, honestly?

## The brief, as given

> Candidate list: β-meter + cascade + parallel worktrees + budget primitives + critic
> tier. Is even that too much for one person? What gets cut? (This is partly preferential
> — Joe's appetite for scope is evidence no agent holds.)

### Option M

**Decision:** v0 is the β-meter — verifier-outcome logging plus historical PR mining, run
on the main repo and one weakly-verified contrast repo — plus budget primitives. Cascade
routing, parallel worktrees, critic tier, Inquiry tier and the local model library are
all cut from v0.

**Reasoning:** The candidate list fails its own evidence in order. Cascade: the
closed-form β* is a knife-edge — correlated successes collapse it from 0.112 to 0.028 and
erase most of the quality gain, error direction false-safe — so routing cannot
responsibly be in v0; the instrument that would license it must come first. Parallel
worktrees: an MIT-licensed incumbent already ships a worktree tool and subagent teams,
and worktrees do not survive "why will this not be the fourth?". Critic tier: critic
recall ≡ 1−β, so it is downstream of the same unmeasured quantity — building it before
measuring is building on the same sand. Budget primitives stay: 63 documented production
overrun incidents, and they are small. The β-meter is simultaneously the thesis, the
verified gap, the untouched market space and the highest-information unrun experiment.

**Evidence relied on:** simulation and algebra (robustness sweep; the recall ≡ 1−β
identity; the ~5,000-trajectory learned-router result); verified literature (63 documented
overrun incidents; "verifier" absent across 23 systems; the 24.2 pp gap; published routing
assuming β=0); competitive landscape (MIT-licensed worktree and subagent-team incumbents;
no incumbent notion of verifier reliability); project constraints (hours binding; no
revenue; measurement queued ahead of everything).

**Risks or dissent recorded:** A meter with no actuator is a science project, not a tool.
The friction log says the felt pain is choosing models by feel every task, and a β-meter
alone changes no decision made on Monday — the cascade is what makes the number useful,
and shipping measurement without the routing it exists to gate risks a v0 nobody runs
twice, while the three-tier result (+4.4 pp at 43.8% of frontier cost) shows the payoff
being deferred is large. Whether appetite stretches to a manual always-cheap-with-
escalation mode alongside the meter is not an evidence question; it has been defaulted
out, to be argued back in by the measured β.

### Option T

**Decision:** v0 = β-meter (git-history miner core, harness-agnostic) + cascade, gated on
the meter existing and on the adapter-surface experiment, + budget primitives. Worktrees
and critic tier are deferred to v0.1 as adopt-don't-build, recorded via a superseding ADR.

**Reasoning:** The list has a dependency order and that decides the cut. β-meter first,
non-negotiable: everything else is gated on it, and shipping cascade routing gated on the
closed form before β is measured is shipping a false-safe instrument. Cascade second —
the simulated upside is real, but only once the meter exists. Worktrees and critic tier
are a package, and an MIT-licensed incumbent already ships both; building them is being
the fourth casualty. Budgets are cheap plumbing with 63 documented overrun incidents
behind them; keep. Sample complexity forces the design: historical mining is not a
nice-to-have but the only viable labelling route at solo volumes, so the meter's core is
a git-history miner, not a live hook — which also clears the dogfooding gate on day one.
Build the cascade as a ladder, not a switch: depth is nearly free.

**Evidence relied on:** simulation and algebra (robustness sweep; Wilson sample
complexity; three-tier depth economics; the ~5,000-trajectory learned-router result;
recall ≡ 1−β); verified literature (the 24.2 pp gap; "verifier" absent across 23 systems;
63 overrun incidents; measured multi-agent cost multipliers; the delegation theorem's
exogenous-signal exemption); competitive landscape (MIT-licensed worktree and
subagent-team incumbents; the adapter tax; OpenHarness staleness signals); project
constraints (hours binding; the low-β main repo warning; the dogfooding gate; the friction
log).

**Risks or dissent recorded:** None remained at close. One position did change during the
work: an initial push to commit to the plugin route immediately was withdrawn once
staleness facts were presented — three months since a release, unstable surface, modest
test suite, 16% fork-to-star — and the plugin question was gated on a cheap probe
instead. Hard gates attached: a weakly-verified contrast repo before any public β figure,
and trademark and package-name checks before anything ships.

### Option V

**Decision:** v0 = β-meter + a simple two-tier cascade. Cut parallel worktrees, critic
tier and the learned router. Budget primitives are held back pending a statement of the
maintainer's weekly hours and scope appetite, which is the one class of facts no agent
holds.

**Reasoning:** Three classes converge independently on the β-meter as the irreducible v0
core. Simulation: the closed-form threshold is fragile — correlated successes at ρ=0.6
collapse β* from 0.112 to 0.028, error direction false-safe — so routing shipped before β
is measured on a real repo is a broken instrument. Literature: maintainer merge rates run
24.2 pp below automated grader scores and none of 23 surveyed systems measures verifier
reliability. Landscape: every other candidate has an MIT-licensed incumbent; the β-meter
is the only genuinely unbuilt component. Constraints: the friction log names
model-chosen-by-feel, which meter plus cascade answer directly, while critic tier and
budget primitives never appear in it. On the critic tier, measured multi-agent cost
multipliers outweighed an elegant but empirically ungrounded identity. The cascade
survives only in its simplest form because a learned router needs ~5,000 trajectories
just to match always-cheap-with-escalation.

**Evidence relied on:** simulation and algebra (correlated-success collapse; recall ≡
1−β; learned-router sample complexity); verified literature (the 24.2 pp gap; 23 surveyed
systems; 63 documented overrun incidents; measured multi-agent cost multipliers);
competitive landscape (MIT-licensed incumbents for worktrees and orchestration); project
constraints (the friction log; hours, not money, as the binding constraint).

**Risks or dissent recorded:** The recall ≡ 1−β identity argues the critic tier is not an
extra component but the same quantity seen from the routing side — cutting it may force
rebuilding it the moment the β-meter works. Sharper: the 63 documented production
budget-overrun incidents are exactly the external, different-class evidence this project
says to privilege, and holding budget primitives back weights a local friction log —
anecdote — over ecosystem-scale data, which is the opposite of the declared epistemics.
That conflict is real, and it was resolved by deference to a missing class of preferential
facts, not by evidence.

### Your grading — D4

- Best: `___`  Worst: `___`  Gap: **material / marginal**
- What does the best option have that the others lack? `____________________`

---

# D5 — Does the local model library belong in v0?

## The brief, as given

> Hardware-gated local-model discovery is a substantial cross-platform feature for a
> pre-v0 project. The cascade needs *a* cheap tier — but that could be a cheap API model
> with no library at all. In, out, or wrapped (LM Studio et al.) at v0?

### Option M

**Decision:** The local model library is out of v0 and the null option — a cheap API
model as the cheap tier — is in. The local rig's v0 job is measurement, not inference,
and if local is ever wanted, wrap an existing runtime rather than build one.

**Reasoning:** The numbers cut against the local library harder than expected. The
cascade only wins below β* ≈ 0.11, and that threshold is a knife-edge: correlated model
successes collapse β* from 0.112 to 0.028, and at ρ=0.9 the quality advantage of a cheap
tier is zero. Local models fine-tuned on the same public code as frontier models are
exactly the high-ρ case. The maths is indifferent to *where* the cheap model runs; a
cheap API model exercises the identical routing logic with none of the library surface.
The field's state of the art says the routing maths is a solved commodity and the
unmeasured quantity is β. Every hour spent wrapping a local runtime is an hour not spent
on the one thing with no incumbent, and a cheap API model exposes the same friction at
zero build cost.

**Evidence relied on:** simulation and algebra (β* knife-edge; the ρ=0.9 zero-advantage
result); verified literature (cascade routing already solved but assuming β=0; the 24.2 pp
gap; measured tiering cost multipliers; the delegation theorem's Corollary 9); competitive
landscape (local-model discovery already MIT-licensed three times over; verifier
reliability the only unclaimed layer); project constraints (hours binding; donations-only;
the friction log naming measurement, not local inference).

**Risks or dissent recorded:** None recorded. Two points were carried as caveats rather
than disagreement: measuring only the low-β main repo would flatter the thesis, so a
weakly-verified contrast repo is mandatory before anyone claims headroom for a cheap
tier; and a cheap tier plus a measured verifier could be principled later, but only once
per-repo β exists.

### Option T

**Decision:** Out of v0 as a built feature. The cascade's cheap tier is any
OpenAI-compatible endpoint URL in config, so local users point at LM Studio or Ollama and
everyone else points at a cheap API model — no discovery, no hardware gating, no library
code.

**Reasoning:** The landscape argument is sharpest: the repeating pattern is "someone
already built this, MIT-licensed", and the model library is literally the first listed
instance of it. Hardware-gated cross-platform model discovery is a solved, actively
maintained product category. LM Studio and Ollama both expose OpenAI-compatible local
servers, so "wrapped" costs one config field, not an integration layer. Hours are the
binding constraint, and a cross-platform hardware-detection feature is exactly the kind of
scope that eats weeks and traces to no part of the thesis; nothing in the friction log
mentions model discovery. Traceability seals it: a model library serves neither
provenance, difference-of-class, nor measuring the test's error rate. The endpoint-config
approach preserves the full local-model option while writing zero speculative code.

**Evidence relied on:** competitive landscape (the model library as the first
already-built casualty; LM Studio and Ollama exposing OpenAI-compatible servers); project
constraints (hours binding; the friction log's silence on discovery); simulation and
algebra (depth nearly free, but every result model-world; the learned-router caution);
verified literature (nothing favouring a library; the per-repo measurement gap).

**Risks or dissent recorded:** The strongest counter is adoption economics. This is a
donations-only fully-OSS project, and a stranger's install is far more likely to succeed
if the tool finds a free local cheap tier automatically instead of demanding an API key or
manual setup — the local library could be the one feature that makes v0 usable at zero
marginal cost, and the local-rig culture suggests local-first is the project's native
mode. Deferring it may quietly bias v0 toward API-key users and understate real cascade
economics. Whether first-class local UX is wanted as an adoption hook is not an evidence
question and has not been decided here.

### Option V

**Decision:** The local model library is out of v0: the cascade's cheap tier ships as a
cheap API model, with a thin wrap of an existing local runtime admitted later only if
measurement shows the API tier failing on cost or on β.

**Reasoning:** All four evidence classes converge by different routes. Simulation: the
cascade's value is ladder depth — three tiers give 43.8% of frontier cost and +4.4 pp at
β=0.10 — and nothing in the algebra distinguishes local from API hosting, so simulation
cannot justify a hardware-gated library. Literature: cheap-tier routing is solved prior
art, the unsolved part is β-conditioned tiering, no source requires local hosting, and a
weak cheap tier raises β load regardless of host. Landscape: local-model discovery is
crowded, MIT-licensed ground and has been the "someone already built it" answer three
times; verifier reliability is the only unclaimed layer. Constraints: hours are binding,
the rig's v0 job is running the experiments, and the logged pain is absence of
measurement, not absence of local models. Where "run it, don't reason about it" pulled
against the hours constraint, constraints won.

**Evidence relied on:** simulation and algebra (three-tier depth economics; the copula
correlation result); verified literature (solved cascade routing; relay decay; the 24.2 pp
gap); competitive landscape (crowded MIT-licensed discovery; verifier reliability
unclaimed); project constraints (hours binding; the rig's assigned job; the friction log).

**Risks or dissent recorded:** Two real objections. First, the correlation result is the
strongest case *for* local models: cheap API models often share provider lineage with the
frontier tier, and correlated successes collapse the cascade's advantage (β* 0.112 → 0.028
at ρ=0.6). A local open-weights model is plausibly the less-correlated cheap tier — a
genuinely different class of facts — and this decision forgoes that without ever measuring
ρ. Second, all four evidence classes derive from documents written in one session on one
repo, so their agreement is weaker consilience than it looks, and the simulation class is
entirely model-world. If measurement never runs, the decision rests on convergent
assertion.

### Your grading — D5

- Best: `___`  Worst: `___`  Gap: **material / marginal**
- What does the best option have that the others lack? `____________________`

---

# D6 — Executable-model CI ratchet: keep or drop?

## The brief, as given

> The proposal: an ADR ships with a runnable decision model; CI re-runs it; a sign flip
> fails the build. Genuinely useful, or ceremony with a maintenance cost (dependency
> rot)? EXP-10 would measure it over three months — but should the mechanism exist at all
> in v0?

### Option M

**Decision:** Drop the executable-model CI ratchet from v0. ADRs keep shipping runnable
decision models as scripts, with the CI wiring deferred until measurement provides real
inputs and the three-month experiment prices the maintenance cost.

**Reasoning:** Two independent classes converge on deferral. Simulation: a CI gate
re-running a model whose inputs are entirely simulated just re-asserts assumptions — β has
never been measured on a real repo, and the robustness sweep moves β* across 0.03–0.43
under plausible perturbations, so a sign-flip check currently gates on noise. Constraints:
hours are the binding resource, the two priority experiments queue ahead of everything,
and any CI surface carries dependency-rot upkeep paid in that resource. Literature and
landscape both establish that the mechanism is genuinely novel — no prior art re-runs a
decision and fails on a sign flip — which is why the mechanism is kept rather than killed.
Where novelty pulled against unmeasured-and-unaffordable, the latter won: a ratchet on
unmeasured inputs produces confident noise, the failure mode this project exists to
prevent.

**Evidence relied on:** simulation and algebra (entirely model-world inputs; β* moving
across 0.03–0.43 under perturbation; the sweep flipping a day-old conclusion);
project constraints (hours binding; dependency-rot upkeep; the experiment queue); verified
literature and competitive landscape (both establishing genuine novelty and no incumbent).

**Risks or dissent recorded:** The repo's own ratchet principle, and the invariant that a
declared invariant ships with its enforcing check in the same commit, say this is exactly
how a prior repo's documented chokepoint fragmented into five bypass paths. Deferring CI
enforcement declares "ADRs carry runnable models" as an invariant with no check — the
documented most-expensive prior failure — and roughly twenty CI ratchets were already
affordable in a solo repo. If the pattern rots before measurement runs, this decision
caused it.

### Option T

**Decision:** Adopt it: an ADR that cites a number must ship the number's runnable
generator, re-run in CI, gating on sign flip only and never on point-value drift.
Prose-only ADRs are exempt, there is a hard per-model runtime budget, and a model that
needs maintenance is superseded along with its ADR rather than patched to pass.

**Reasoning:** Not ceremony — this week's own results are the strongest argument for it.
The closed form said 0.112; the robustness sweep moved the value everywhere (0.052–0.426)
but the sign and threshold structure survived until correlated model successes collapsed
β* to 0.028 and the quality gain from +4.0 to +0.9 pp. That is exactly a sign-flip-class
event: a decision reverses under a parameter that had not been modelled. Had the ADR that
adopted the cascade shipped its model, adding the correlation parameter would have failed
the build and forced the re-decision, instead of it living in one person's head. There is
also direct evidence the review process needs it: a fabricated figure in the internal
literature review sailed through. And this is not a new practice — it is an existing
invariant applied to ADRs.

**Evidence relied on:** simulation and algebra (the robustness sweep as a live sign-flip
event; values knife-edge and link-specific); verified literature (a fabricated figure that
passed internal review; "verifier" absent across 23 systems; the 24.2 pp gap; published
routing assuming β=0); competitive landscape (nothing in the field re-verifies its own
decision models; the pre-emption pattern); project constraints (invariant I1; hours, not
compute, as the binding cost; day-old ADRs with one conflicted reviewer).

**Risks or dissent recorded:** None recorded. All qualifications were folded into the rule
rather than left standing: sign-flip-only gating, because the values are knife-edge and
link-specific and failing on value drift would be noise; prose ADRs exempt, because
mandating models for them would be ceremony; and a hard runtime budget per model, because
compute is free but maintenance is not.

### Option V

**Decision:** Keep the executable-model CI ratchet in v0, in its minimal form: each ADR
that already has a runnable decision model gets a CI job that re-runs it and asserts only
the sign or threshold conclusion, with pinned dependencies and no new framework. The
three-month measurement runs as the kill switch.

**Reasoning:** The failure mode the ratchet guards against is not hypothetical — it
already happened, this week, in this repo. The robustness sweep flipped the load-bearing
conclusion of the cascade model: under correlated successes β* collapses from 0.112 to
0.028 and the quality gain from +4.0 to +0.9 pp. That is precisely a sign or threshold
flip in an ADR-backing model, caught only because someone happened to re-run it with a new
assumption. The project's own constitution demands it: "a chokepoint without an
enforcement rule is not a chokepoint" was bought at a prior repo's expense, and "re-run
the scripts before relying on any number" is today a prompt-level rule — exactly what must
move into code. It is also differentiated: nobody in the landscape re-verifies the
decisions their architecture rests on.

**Evidence relied on:** simulation and algebra (the sweep as a live sign-flip event);
project constraints (invariant I1 and the prior repo's five-bypass-path failure; the
scripts already exist; roughly twenty CI ratchets already routine in a solo repo; two ADRs
provisional pending measurement); verified literature and competitive landscape (nothing
in the field re-verifies its own decisions; too small to be a product anyone has shipped).

**Risks or dissent recorded:** The project is pre-code with day-old ADRs, and measured
results will likely supersede the simulated models wholesale rather than re-parameterise
them — a ratchet guarding models scheduled for replacement protects the wrong artefact.
With hours the binding constraint and scope already contested, even a cheap mechanism
competes with work worth strictly more. The lazy alternative — re-running the scripts
manually at each supersession — might capture 90% of the value for zero standing cost.
Whether a fired ratchet blocks a merge or merely flags for supersession is a tolerance
question, not an evidence one, and has not been decided here.

### Your grading — D6

- Best: `___`  Worst: `___`  Gap: **material / marginal**
- What does the best option have that the others lack? `____________________`

---

## Closing note

**The token and wall-clock costs of each arrangement are deliberately withheld from this
page.** They are recorded and they differ by large multiples — one arrangement cost
several times another for the same six decisions. `[measured]` Knowing that a particular
option was the expensive one would bias the grading in either direction: towards it,
because expense reads as thoroughness; or against it, because expense reads as waste.
Either way the grade would stop being a judgement about the decision.

Grade the decisions on their merits. The costs are in `exp16-results.md` and will be
laid alongside your grades afterwards, which is the only order in which the comparison
means anything.

One more thing worth saying plainly: **"they are all about the same" is a valid and
important result.** It is, in fact, the result stopping rule 1 is currently pointing at.
Do not manufacture a preference to make the experiment feel conclusive. A recorded tie
resolves the rule just as cleanly as a clear winner, and in the opposite direction.

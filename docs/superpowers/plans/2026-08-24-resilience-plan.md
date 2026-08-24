# 2026-08-24 — resilience remediation plan

Two research workflows ran on 24 August 2026 against the published failure literature and
against this repository's own measured behaviour. Between them they surveyed 78 named failure
classes and found 51 this system is exposed to but has not yet hit. This plan holds the six
units that came out of that work, plus the defects found by hand the same night.

**Every claim below is measured on this machine unless it carries a citation.** Where a source
is cited it was read in that session, and where it was named from familiarity rather than
re-read, the unit note says so.

## The rule these units share

The Engineering Ratchet, from `AGENTS.md`: when something fails, the fix goes in code — a
check, a type, a constraint — not in a prompt. Every unit below therefore ships its check in
the same commit as its fix, and several of them exist *because* an earlier fix shipped without
one.

**None of these units may be closed by widening a check.** Raising `_READ_RETRIES`, lengthening
a timeout, raising `MAX_CONCURRENT` or relaxing a cap are named as forbidden remedies in the
units where they would be the tempting shortcut. Sharpen the discriminator; do not move the
threshold.

## The units

| Unit | Defect | Status when written |
|------|--------|---------------------|
| Z01 | The trajectory log doubles daily because every `instructions.assembled` event inlines the full omitted list | **Live and causing crashes** |
| Z02 | Four unbounded counters in the driver, and a machine-wide process count read as a per-organisation fact | Live |
| Z03 | A killed tick persists nothing; `sh()` has no timeout; orphaned grandchildren survive | Latent, ~10× margin |
| Z04 | Mutable driver state is tracked in git, so a checkout can restore an older copy | Live, has already lost a unit once |
| Z05 | Every retry backoff is exponential with zero jitter, on a resource ~20 agents contend for | Latent |
| Z06 | Build and review lanes share one admission pool, so either can starve the other | Live |

### Z01 — stop the trajectory log doubling every day

The urgent one. `.harness/log/` by day: 21,137 → 166,465 → 792,359 → 1,069,904 → 5,865,602 →
40,771,519 bytes. `_selection_receipt` inlines every omission into the event, the omission list
grows with the log, so each event is larger than the last and the growth compounds. One sampled
event was 85,442 B of which 84,603 B — 99% — was `data.recall.omitted`, while
`data.recall.selected_event_ids` was empty.

This is not a tidiness problem. Dozens of concurrent dispatchers now collide on Windows
byte-range locks over a 40 MB file, and `could not be read after 6 attempts: observed access
denial` is the single commonest crash signature in driver state. **This defect degrades every
other unit's run**, which is why it carries the highest priority in the queue.

The fix records an `omitted_count` and an `omitted_digest` instead of the list. The audit
property survives because `instructions.verify` compares through the same function: a replay
producing a different omission set produces a different digest.

### Z02 — bound the driver's counters

Four defects in one file, all measured in `driver-state.json`:

- **The review path is uncapped.** `review_attempts[uid]` is incremented and compared to a
  ceiling nowhere. One unit reached 27.
- **The attempt cap has never bound.** Three refund paths return every failure class this
  system actually suffers, so a cap of 3 counts only the failures it does not have.
- **No quarantine.** The three-identical-deaths branch prints and continues; reclamation
  refunds next tick, so nothing is ever terminal.
- **`live_dispatchers()` counts machine-wide processes** matching `dispatch.py`, with no cwd or
  workspace filter — the fifth measured verify-by-process-identity site in this repository.

The fix adds a **second, non-refundable** counter rather than replacing the existing one. The
refund is right about evidence and wrong about load; both facts need to be represented.

### Z03 — checkpoint the tick, bound every subprocess

Cited: Bronson, Aghayev, Charapko & Zhu, *Metastable Failures in Distributed Systems*,
HotOS '21; Huang et al., *Metastable Failures in the Wild*, OSDI '22.

`save_state()` is called at exactly three terminal places, so a tick killed at its 3000 s
deadline persists **nothing** — consumed receipts, reclaimed slots and cleared conflicts all
vanish and the next tick redoes the work. Two concurrent drivers were already measured putting
nine pytest processes on the box and taking the suite from 432 s to 961 s, a degradation factor
of about 2.2. Per this machine's own recorded lesson, a subprocess timeout does not kill
grandchildren, so each abandoned tick leaves an orphan behind to contend with the next.

Once suite duration exceeds the deadline, goodput is zero and removing the original cause does
not recover it. That is the definition of a metastable failure, and the only thing between this
driver and it is a margin that shrinks with every test added.

**Do not buy margin by raising the deadline.** That widens the window without removing the
amplification.

### Z04 — untrack mutable harness state

`git ls-files .harness` returns the authoritative scheduling record, the unit plan, a **lock
file**, loop stdout/stderr, and two complete extra copies of `src/consilient/` — so it returns
three `consilient/events.py`. Any checkout can restore an older copy of the file that decides
what gets dispatched, and this has already happened once: `plan-units.json` silently lost a
queued unit and nobody noticed. `.harness/log/` is already gitignored and has never suffered it.

### Z05 — full jitter on every retry

Cited: Brooker, *Exponential Backoff And Jitter*, AWS Architecture Blog, 4 March 2015.

Both retry sites are exponential with **zero** jitter, on resources this repository's own
comments describe as contended by roughly twenty concurrent agents. Twenty readers evicted by
one writer all sleep 40 ms, then 80, then 160, in lockstep. The budget then fails closed, and
the code comment records what that costs: it "failed the suite — which then blocked retirement,
merging and publication at once". A synchronised herd on one file escalates to a global goodput
stop.

Z01 removes most of the offered load on this path; Z05 removes the synchronisation. Both are
wanted, and neither substitutes for the other.

### Z06 — bulkhead the lanes

Cited: Huang et al., HotOS '17 §2.3; Google SRE Book ch. 22; Nygard, *Release It!*

`MAX_CONCURRENT = MAX_BUILDS + MAX_REVIEWS` is a single pool, so a review backlog consumes
slots builds need. This was observed live: 64 reviews in flight while builds could not start.
`MAX_CONCURRENT` is currently doing load-shedding work nobody assigned it, documented only as
"a load cap on the machine" — **a safety property held by an incidental constant is itself the
finding**, so the shedding is to be made explicit and tested.

## Fixed by hand the same night, recorded here so the trail survives

These were not queued as units because they were blocking the queue itself.

1. **Windows `MAX_PATH` was silently killing every review.** A review clones into
   `.harness/dispatch/<run-id>/workspace/full_clone/<run-id>/`, and that prefix plus this
   repository's descriptive ADR filenames exceeds 260 characters. The clone succeeded and the
   checkout failed, so every review died at setup with an empty stdout — indistinguishable,
   from the driver's side, from a review that found nothing. Fixed by `core.longpaths`, set
   globally because only the global config is inherited by fresh clones, and added to
   `self_heal` so a fresh machine repairs itself.

2. **`MAX_REVIEWS` had never bound.** `reviews_out` was re-initialised to 0 each tick, so it
   counted only what that tick launched and never what was still running: the cap was a
   per-tick rate, and reviews climbed 12, 24, 36, 48, 64. Each review full-clones a 136 MB
   workspace, so sixty-four of them thrash the machine badly enough that none finish — the
   verification tier looked maximally busy and produced almost nothing.

3. **Dead runs leaked their slots.** The crash handler released `in_flight` and
   `resolve_dispatched` but never `review_dispatched`, and the three-identical-deaths
   escalation `continue`d before any cleanup at all — Y02 died the same way 77 times while
   still counted as in flight.

4. **A guard-mutation test corrupted the tracked tree.** Three ratchets in
   `tests/test_persona_qa.py` wrote broken text to real documentation and restored it in a
   `finally`. A `finally` does not run when the process is killed, and the suite runs under
   timeouts: `getting-started.md` was found still carrying the test's own mutation string,
   pointing operators at a file that does not exist. They now patch the read in memory and
   never touch the tree.

5. **`src/mine.py`, `src/x.py` and `docs/theirs.md` were tracked test fixtures** — 23, 20 and
   26 bytes of `content of <name>`. `src/mine.py` is not valid Python, so the diagram build
   refused the whole tree.

## What is not decided, and is the principal's

**The A3 refusal baseline.** ADR-0105 adds three 2026-08-22 digests to the operational Gate A
condition 3 tolerance, taking it from three to six. The facts check out — all six digests hash
real log lines, and unit AB's torn-append refusal is in the tree with its test passing — but
`tests/test_v0_invariants.py` already refuses this exact widening in prose and in an assertion,
and ADR-0105's recorded acceptance could not be corroborated. Pinning the incident and widening
the gate are separate acts; the pin is applied, the widening is not. See the module docstring
of `tests/test_doctor_a3_baseline.py` for the full reasoning and how to resolve it either way.

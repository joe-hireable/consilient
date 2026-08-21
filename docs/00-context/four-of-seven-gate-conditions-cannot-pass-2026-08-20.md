# Four of the seven gate conditions cannot pass, and every one that currently fails is one of them

**Date:** 20 August 2026
**Status:** `[measured]` for every status and count, all produced by running `consil doctor` and by
executing the two probe scripts named below; `[algebra]` for the A3 and B2 arithmetic; `[asserted]`
for the unifying reading and the proposed rule.
**Supersedes nothing. Collects** `gate-b-cannot-be-passed-2026-08-20.md` and
`gate-a-cannot-be-passed-either-2026-08-20.md` and adds two conditions neither of them covered.

---

## The census

Seven conditions stand between this repository and Stage 3 — the harness routing real work.

| | condition | state | can it *ever* pass? |
|---|---|---|---|
| A1 | EXP-01 complete on two differently verified repositories | **PASS** | yes |
| A2 | Replay reproduces an identical canonical state digest | **PASS** | yes |
| A3 | Seven consecutive days of capture with no data loss | FAIL | **only by losing a day of data** |
| B1 | EXP-05 complete; adapter two forced no redesign | **PASS** | yes |
| B2 | EXP-08 measured critic throughput gain ≥ 20% | UNKNOWN | **no — no `pass` branch exists** |
| B3 | A one-command bare-Claude-Code fallback exercised weekly | FAIL | **no — no `pass` branch exists** |
| B4 | Twenty non-Consilient tickets without harness intervention | UNSATISFIABLE | **no — circular** |

> **Every condition that is not currently passing is a condition that cannot pass.** Not one of the
> four is merely work that has not been done yet.

## The two nobody had noticed

A3 and B4 were established earlier today. B2 and B3 are new, and they fail in a way the other two
do not: **their success path was never written.**

`_fallback_condition()` (B3) has four branches. Enumerated and executed across every reachable
arrangement of the workflows directory: `[measured]`

```
no workflows dir           -> unknown   No workflow evidence source exists.
workflows, no schedule     -> fail      All 1 workflows were checked; none has a schedule trigger.
workflows with schedule    -> unknown   A scheduled workflow exists, but no machine-readable
                                        fallback result exists.
```

The string `"pass"` does not appear in the function. **No artefact anyone could build makes B3
pass**, including the scheduled workflow its current FAIL message asks for. Adding that trigger
moves it from FAIL to UNKNOWN and no further.

B2's arm of `_experiment_conditions()` is the same: three branches, all returning `unknown`. The
last one is the giveaway — *"No machine-readable EXP-08 outcome exists"* — which is a placeholder
for a format that was never defined.

Both are honest stubs. Neither says so anywhere a reader would look, and both render in `doctor` as
though the work were merely outstanding.

## The pattern, which is the point of collecting these

Each condition names a **property** and is implemented as a test of a **proxy** the system cannot
produce while the gate is shut.

| | the property it wants | the proxy it tests | why the proxy is unproducible |
|---|---|---|---|
| A3 | capture is working and losing nothing | zero refusals inside the window | refusals are permanent in an append-only log; only a **capture gap** clears them |
| B2 | β is measured well enough to route on | a machine-readable EXP-08 outcome | the format was never defined, and no branch reads one |
| B3 | the bare-agent fallback still works | a machine-readable fallback result | same — the success path was never written |
| B4 | the harness is trustworthy on other people's work | twenty tickets already orchestrated elsewhere | doing that is precisely what passing the gate permits |

A fifth case sits just outside the pattern and is worth stating beside it, because it is the same
failure of arithmetic rather than of construction. `MIN_REJECTIONS = 30` is the evidence floor for a
measured β. Using this repository's own Wilson function on a **flawless** record: `[algebra]`

```
0/29 -> [0.00000, 0.11697]   fails
0/30 -> [0.00000, 0.11352]   fails      <- the floor as set
0/31 -> [0.00000, 0.11026]   clears
```

**At the floor as set, no outcome whatsoever clears β\* = 0.111.** The floor is one below the
smallest sample at which a perfect record can succeed. This is `P2-guards.md`'s A11, still open.

## The rule this suggests

> **A gate condition must name an artefact that the system can produce while the gate is still
> shut, and its check must have a reachable success path.**

Both halves earn their place. B4 violates the first: its artefact can only be made after the gate
opens. B2 and B3 violate the second: their artefact might be producible, but nothing would read it.

## The ratchet `[measured]`

Working principle 4 says the fix goes in code. `test_every_gate_condition_has_a_reachable_pass_state`
reads `_condition(...)` call sites out of the AST, resolves each status argument — including the
ones assigned through a local variable — and asserts that every identifier in `REQUIREMENTS` can
emit `"pass"`.

B2, B3 and B4 are grandfathered **by name**, and the set may only shrink. Adding an identifier is
not permitted; removing one is the entire purpose.

B4 is in that set for a different and honest reason from the other two: it reports
`structurally_unsatisfiable`, which is an accurate description of a circular condition and is
exactly what that status exists for. B2 and B3 report FAIL and UNKNOWN, which are not.

The test found something on its first run: **B4 was not in my original grandfather list, and the
test said so.** I had reasoned about A3, B2 and B3 and missed the one I had already documented.

## What was not done

**No condition was made passable and no gate was moved.** Defining what counts as a machine-readable
fallback or EXP-08 outcome is defining what evidence satisfies a gate, which is ADR-0015's territory
and Joe's. Building the bare-Claude-Code fallback in CI additionally needs credentials in a public
repository, which is outward-facing and not an agent's call.

The proposals that already exist for two of the four are ADR-0043 (A3) and ADR-0039 (B4). B2 and B3
have none yet, because the right proposal depends on what Joe wants the fallback to prove.

## Reversal and falsifier

**Reversal:** `git revert` this commit; the test and this document disappear and the four conditions
go back to looking like outstanding work.

**Falsifier:** the AST scan is a proxy for reachability, not a proof of it. A condition could contain
the literal `"pass"` on a branch that no input reaches, and this test would be satisfied by a wall.
The behavioural version — construct inputs and check that some arrangement passes — is stronger and
was only done by hand for B3. If a condition is later found with an unreachable `"pass"` branch, this
test is too weak and should be replaced rather than patched.

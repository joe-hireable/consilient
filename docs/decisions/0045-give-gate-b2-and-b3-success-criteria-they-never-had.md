# 0045. Give Gate B2 and B3 the success criteria they never had

- **Status:** **ACCEPTED 20 August 2026.** Criteria chosen by Joe Brown in the orchestration chat
  (*"I accept all the recommendations"*), recorded in the trajectory as `decision.gate_criterion`
  authored by the principal.
- **Date:** 2026-08-20
- **Deciders:** Joe Brown. The criteria are his; the diagnosis, the mechanism and the objections are
  mine.
- **Supersedes:** [`0037`](0037-replace-gate-b2-with-measured-critic-throughput-gain.md) entirely —
  its throughput threshold is withdrawn. Amends [`0015`](0015-dogfooding-gate.md) Gate B condition 3.
- **Inquiry tier reached:** T1 ground. The defect is `[measured]` by execution; the replacements are
  `[asserted]` policy.

## Context — both conditions were walls, not gates

`consil doctor` implements seven gate conditions. Executing every reachable input on 20 August 2026
found that **B2 and B3 have no `pass` branch at all.** [measured]

`_fallback_condition()` (B3), across every arrangement of the workflows directory:

```
no workflows dir           -> unknown
workflows, no schedule     -> fail      "none has a schedule trigger"
workflows with schedule    -> unknown   "no machine-readable fallback result exists"
```

The literal `"pass"` does not appear in the function. Adding the schedule trigger its own FAIL
message asks for moves it to `unknown` and no further. B2's arm of `_experiment_conditions()` is the
same shape: three branches, all `unknown`, the last one a placeholder for a format nobody defined.

**B2 has now been broken in both directions across two ADRs.** ADR-0037 replaced it precisely
because the original *could never fail* — `n_max ≥ 3.125 > 1` identically, for every β. Its
replacement threshold *can never pass*. A condition that has been unfalsifiable and then
unsatisfiable, both by construction, is evidence that the underlying question was never operational.

## Decision

### B2 — measure the critic's error rate; withdraw the throughput threshold

> **Gate B condition 2 is satisfied when the critic tier's own β has been measured, with an
> interval, by an instrument that does not depend on human rejections.**

ADR-0037's 0.6296 throughput-gain threshold is **withdrawn**. It was derived from a model whose
inputs (`T_a = 25`, `T_r = 8`, `p_good`) were assumed, and its evaluation requires a measured
repository β, which requires human rejections, of which there have been **zero**. [measured]

What replaces it is cheaper and more direct. Since EXP-47, measuring a verifier's β takes 104
seconds and no human labels: mutation testing gives the false-accept rate of any check suite,
including a critic's. The property Gate B2 wants — *the critic tier earns its place* — is better
served by knowing its error rate than by a modelled throughput figure.

### B3 — a dated, machine-readable fallback result

> **Gate B condition 3 is satisfied when a scheduled workflow exists, and a machine-readable
> fallback result is present, dated within the last 14 days, recording a pass.**

The result is one JSON object at a fixed path, carrying at minimum: the timestamp, the exact command
run, the outcome, and a reference to the run that produced it.

Fourteen days is two weekly cycles — one missed run is tolerated, two are not. **A stale result
fails.** A fallback exercised three months ago is evidence about three months ago.

## Evidence against

- **Both criteria were written after the conditions were found unpassable, by the party they
  constrain.** That is the objection to state first. A gate whose bar is set in response to
  discovering it could not be cleared is not obviously a gate. The mitigation on offer is thin but
  real: the criteria are *stricter in kind* than what they replace — B3 gains a recency requirement
  it never had, and B2 gains a measurement requirement where it previously had a number nobody could
  compute.
- **B2's replacement measures a different thing from what B2 asked.** Gate B2 asked whether the
  critic *increases throughput*. This asks whether the critic's error rate is *known*. Those are not
  the same question, and a critic with a perfectly measured and terrible β would satisfy this
  condition. **That is deliberate** — an unmeasured critic is the thing ADR-0010 and working
  principle 5 forbid relying on — but it should not be described as preserving ADR-0037's intent,
  because it does not.
- **Fourteen days is arbitrary.** It is two cycles of a weekly schedule, which is a reason but not a
  measurement. No evidence establishes that a fortnight-old fallback result is informative and a
  three-week-old one is not.
- **Neither criterion is satisfied today, and B3 cannot be satisfied by an agent.** Running bare
  Claude Code in CI needs a credential in a public repository. That is a separate act by the
  principal and has not been taken.
- **A cheaper alternative was not taken and should be named.** Gate B condition 3 could be
  *deleted*: the "bare-agent fallback remains permanent" rule in `v0-draft.md` is a design
  commitment, and testing it weekly may be ceremony rather than evidence. Deleting a gate condition
  is a larger claim than repairing one, and it remains available.

## Consequences

**Positive.** Two of the four unpassable conditions become passable in principle, and `doctor` can
report progress toward them instead of a permanent wall. The reachable-`pass` ratchet's grandfather
set shrinks from three to one — B4, whose `structurally_unsatisfiable` status is accurate and
deliberate.

**Negative.** ADR-0037 is withdrawn less than a day after being accepted. The supersession trail is
the honest record of that, and it is the second thing ADR-0037 got wrong about the same condition.

**Neutral but load-bearing.** B3 now depends on an artefact produced outside this repository by a
scheduled workflow. That is the first gate condition whose evidence is not derivable from the working
tree and the log.

## Enforcement

Ships with this acceptance:

- **Check:** `_fallback_condition()` gains a `pass` branch requiring a schedule trigger, a
  well-formed result, an outcome of `pass`, and a timestamp within 14 days. A malformed or undated
  result **fails**; it does not report `unknown`.
- **Check:** B2's arm gains a `pass` branch requiring a recorded critic-β measurement with an
  interval.
- **Check:** `test_every_gate_condition_has_a_reachable_pass_state`'s grandfather set shrinks to
  `{"B4"}`. The set may only shrink, so this is enforced by the existing ratchet rather than by
  anything new.
- **Check:** a stale fallback result fails, tested with a fixture dated 15 days back.

## What would overturn this

If the fallback job runs weekly for a quarter and passes every time without ever catching a real
regression, B3 is ceremony and should be deleted rather than kept green — the deletion option above,
taken on evidence instead of preference.

If a critic tier is ever admitted whose β is measured and poor, and it improves outcomes anyway,
then B2's replacement is measuring the wrong property too, and the question should be retired rather
than replaced a third time.

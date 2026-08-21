# Consilient in five ideas — draft user guide

**PRODUCT.** This is the candidate user-facing surface for ADR-0055 clause 6, and it is the
material handed to arm A of EXP-71. It is a **draft under test**, not approved documentation.

It obeys its own rule: nothing below names an interval, an estimator, a gate identifier, an ADR
number or an evidence tag. Those all still exist, in the record, unchanged. This page is what a
person has to hold in their head; the record is what the project has to be able to prove.

---

## 1. The job

You say what you want and what would count as done. Not how — what.

"Done" has to be something a machine can look at afterwards and agree happened. *"The signup form
works"* is not a job. *"A new person can create an account and log back in tomorrow"* is.

If you cannot say what done looks like, nothing below can help you, and the harness will say so
rather than guess.

## 2. Checked, or not checked

Everything the harness produces is one of two things: **checked** by something that could have
said no, or **not checked**.

Both are fine. Only one of them is a result. The harness will always tell you which, and it will
never quietly upgrade the second into the first.

## 3. How often the check is wrong

This is the number that matters and it is the reason this project exists.

A check that can say no still gets it wrong sometimes. It lets bad work through. We measure how
often, on your code, and we tell you.

> **On this project's own code, right now: roughly one bad change in three gets past every check
> we have.** That is not a confession, it is the instrument working. Most projects have a number
> like this and cannot tell you what it is.

So when the harness says *checked*, ask the follow-up it will already have answered: **how often
is that check wrong here?** If it does not know yet, it says *not measured yet*, and you should
treat the work like a draft.

**A harness that never says "don't rely on me here" has to be watched constantly. One that says it
accurately can be left alone.** That is the whole trade.

## 4. What it will not decide without you

Five things. It will stop and ask, every time, and it will not infer your answer from something
you said earlier:

- money leaving an account
- anything to do with passwords, keys or logins
- anything published, sent, or made visible outside your machine
- deleting or overwriting something that cannot be got back
- a genuine matter of taste, where no fact settles it

Everything else it decides itself, and records how to undo it. If it asks you something outside
this list, that is a fault in the harness, not a question you need to answer.

## 5. Undo

Every decision the harness makes on its own is recorded with the way back. You can ask for that
way back at any point, and it is a command, not a description of one.

If a decision has no way back recorded, it was not allowed to be made without you — see 4.

---

## That is the whole surface

There is a great deal more underneath: the maths behind the number in 3, the record that makes 5
possible, the reasons for every design choice, and the experiments that could prove any of it
wrong. All of it is open, all of it is written down, and **none of it is yours to carry.** If you
want it, it is in `docs/`. If you do not, the five above are enough to use this and enough to know
when not to trust it.

---

## Notes for the project, not for the reader

- **Under test, not settled.** EXP-71 measures whether an operator holding only this page can
  complete seven core tasks; EXP-72 measures whether collapsing five evidence tags into "checked"
  and "not measured yet" changes any decision a reader would make. Either can kill this page.
- **The one-sided rule applies.** If a simulated operator fails with this page, that is evidence a
  person would fail. If it succeeds, that is **not** evidence a person would, and must not be
  reported as one. Only EXP-73 can lift that.
- **The number in section 3 is real.** β = 0.3132 on this repository's own checks, 1,931 mutants,
  EXP-47. `[measured]` It is quoted in words above because the estimator is deliberately hidden
  from this surface and the rate deliberately is not.
- **What this page is not allowed to become.** An explanation panel. Showing the harness's
  reasoning raised reliance on it without improving anyone's ability to reject it. `[cited]` This
  page explains the *contract*, never the *reasoning*.

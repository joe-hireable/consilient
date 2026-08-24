# What this is

- **Document class:** W
- **Review by:** 2026-09-24
- **Falsifier:** EXP-75 arm A below arm B on any task kills the five-idea claim; EXP-76 kills collapsing evidence tags on this surface.

Class-W admission only. The reader body names no experiment, ADR or evidence tag. [asserted]

---

Five ideas. Nothing else has to sit in your head to use this, and nothing else is yours to carry.

## 1. The job

You say what you want and what would count as done. Not how — what.

"Done" has to be something a machine can look at afterwards and agree happened. *"The signup form works"* is not a job. *"A new person can create an account and log back in tomorrow"* is.

If you cannot say what done looks like, nothing below can help you, and the harness will say so rather than guess.

## 2. Checked, or not checked

Everything the harness produces is one of two things: **checked** by something that could have said no, or **not checked**.

Both are fine. Only one of them is a result. The harness will always tell you which, and it will never quietly upgrade the second into the first.

## 3. How often the check is wrong

This is the number that matters and it is the reason this project exists.

A check that can say no still gets it wrong sometimes. It lets bad work through. We measure how often, on your work, and we tell you. That rate is **β**: the share of bad work that survives every check. That number decides what can run unattended.

When the harness says *checked*, ask the follow-up it will already have answered: **how often is that check wrong here?** If it does not know yet, it says *not measured yet*, and you should treat the work like a draft. Run `consil beta` for the figure it will stand behind; a copy of that figure in a document is not the figure.

**A harness that never says "don't rely on me here" has to be watched constantly. One that says it accurately can be left alone.** That is the whole trade.

## 4. What it will not decide without you

It will stop and ask, every time, and it will not infer your answer from something you said earlier:

- money leaving an account
- anything to do with passwords, keys or logins
- anything published, sent, or made visible outside your machine
- deleting or overwriting something that cannot be got back
- a genuine matter of taste, where no fact settles it
- your own authority — a yes or no that belongs to you: a verdict, an approval, a gate lifted, spend authorised

Everything else it decides itself, and records how to undo it. If it asks you something outside this list, that is a fault in the harness, not a question you need to answer.

## 5. Undo

Every decision the harness makes on its own is recorded with the way back. You can ask for that way back at any point, and it is a command, not a description of one.

If a decision has no way back recorded, it was not allowed to be made without you — see 4.

---

## That is the whole surface

There is a great deal more underneath: the maths behind the number in 3, the record that makes 5 possible, the reasons for every design choice, and the experiments that could prove any of it wrong. All of it is open, all of it is written down, and **none of it is yours to carry.** If you want it, it is in `docs/`. If you do not, the five above are enough to use this and enough to know when not to trust it.

Next: [for your field](for-your-field.md), then [your first hour](first-hour.md).

---

## Notes for the project, not for the reader

- Under test, not settled. The killing experiments are in the [experiment register](../10-research/experiment-register.md). Either can kill this page. [asserted]
- The draft this page is taken from quoted a measured rate in words. This page does not: a restated figure is a second source of truth, and every restatement measured here has drifted. [measured: `docs/20-design/documentation-and-surfaces-plan-2026-08-23.md`]
- The original draft listed five things the harness will not decide. The end-state this plan is written from lists six; the sixth is your own authority. The list above follows the later document. [asserted]
- What this page is not allowed to become: an explanation panel. This page explains the *contract*, never the *reasoning*. [asserted]

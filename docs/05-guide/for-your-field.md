# For your field

- **Document class:** W
- **Review by:** 2026-09-24
- **Falsifier:** this page is false the moment Q24 is no longer listed as Open in `docs/00-context/open-questions.md`; rewrite it, do not patch the sentence.

Class-W admission only. [asserted]

---

If you write software, the previous page is the whole contract. If you do not — strategy, research, design, operations, a field that has no test suite — read this one before the first hour.

## What you get today

You say what you want and what would count as done. A person, or a supervised script, turns that into work. What happened is written down in one inspectable record, and you can ask how often the checks were wrong.

That is the useful product today. It is not small: most tools that send work to an agent cannot tell you when their own checks are lying.

The finished form compiles a sentence into committed work without you operating a tool. That form is designed, not built. Do not read a design document as a status report.

## What is open, and said as open

β is only defined where something can say no to bad work automatically — a test, a type checker, a build. Coding is where this project starts *because* those checks exist and are cheap.

If your work has no such check, **β is undefined**. We do not know whether anything plays its role for a strategy memo, a research note, or a design critique. We say so rather than pretend a number exists. Until that question is answered, nothing here will tell you that a non-coding result was *checked* in the sense of the previous page. It may be recorded, and it may be useful, and it is not a result the way a passing test is a result.

A beautiful interface over an unmeasured check is the failure this project exists to name. We will not build you one.

## What that means for you

- You can keep an inspectable record of work in your field today.
- You cannot yet ask this system how often its checks are wrong in your field, because the checks do not exist or have not been measured.
- If you can name a check — a rubric a stranger could apply, a citation that must resolve, a number that must reproduce — say so. That is the different class of facts the rest of this project is waiting on.

Next: [your first hour](first-hour.md). The ideas underneath are in [what this is](what-this-is.md).

---

## Notes for the project, not for the reader

- Q24 is the named open question: does the β thesis survive in domains without an automated oracle? [asserted: `docs/00-context/open-questions.md`] The 23 August critic observed that hard-coding "Q24 is open" in recruiting prose makes this page a lie when it closes, with no falsifier firing. The falsifier above *is* that close, and `tests/test_guide_entry_path.py` fails when the table row is no longer Open.
- Do not claim the chat compiler, standing remits, or unattended non-coding loops as shipped. v0 is observe-only. [measured: `docs/40-spec/v0-draft.md`]

# Contributing

Thanks for considering a contribution.

**Stage 3 is active** — the repository ships `src/consilient/`, a full test suite, and runnable
research instruments. The most useful contributions are still argument and measurement: read
`docs/00-context/open-questions.md`, try to break the thesis in
`docs/20-design/architecture-sketch.md`, and ship the check with any invariant you add. Issues
that kill an idea are worth more than issues that agree with it.

## Licence

The Project is licensed under the [MIT Licence](LICENSE). Contributions are accepted on the
same terms.

## Two things every contribution needs

### 1. A DCO sign-off (every commit)

Every commit must carry a `Signed-off-by` line certifying the
[Developer Certificate of Origin](DCO):

```
git commit -s -m "your message"
```

which appends:

```
Signed-off-by: Your Name <your.email@example.com>
```

Use your real name and a real email address. CI rejects unsigned commits. To fix a branch:
`git rebase --signoff main`.

### 2. A Contributor Licence Agreement (once)

> **Status: DRAFT — not yet in force.** The CLA is under legal review and is not being
> requested from anyone yet. Until it is finalised, contributions are accepted under the
> MIT Licence and the DCO alone.

When in force, a one-time CLA signature will be required before your first pull request is
merged. A bot will comment on your PR with a link.

- Individuals: [`docs/legal/ICLA.md`](docs/legal/ICLA.md)
- If your employer owns IP in your work: [`docs/legal/CCLA.md`](docs/legal/CCLA.md)

**Read this before you sign.** The CLA asks for something a bare MIT contribution does not:
the right to distribute your work under different licence terms, including commercial ones.
You keep ownership of your contributions and can use them however you like. But the ask is
real, so it comes with a binding counterweight — the
[Relicensing Promise](docs/legal/RELICENSING-PROMISE.md), which is incorporated into the CLA
and commits the Maintainer to: released code stays MIT permanently; no retrospective
closure; attribution preserved; 90 days' public notice before any non-open-source
distribution; and the promise transfers with the project if it is ever sold.

If you're not comfortable with that, forking is a legitimate choice and won't be treated as
hostile.

## Project conventions

Read [`AGENTS.md`](AGENTS.md) — it applies to humans as well as agents. In particular:

- **Claims carry evidence tags.** `[measured]` / `[simulated]` / `[cited]` / `[algebra]` /
  `[asserted]`. `[asserted]` is honest; mislabelling is not.
- **Sign and threshold, never point estimates** from simulations.
- **A chokepoint without an enforcement rule is not a chokepoint.** Any invariant ships with
  the check that enforces it, in the same commit.
- **Multi-agent structures must name their exogenous signal** — see `AGENTS.md` §6.
- British English in prose; conventional identifiers in code.

## Architecture decisions

Non-trivial decisions get an ADR. See [`docs/decisions/README.md`](docs/decisions/README.md)
and use [`docs/decisions/_template.md`](docs/decisions/_template.md). The "Evidence against"
section is required, not optional.

## Experiments

There's an RTX 5090 rig available for benchmarking — see
[`docs/10-research/local-experimentation.md`](docs/10-research/local-experimentation.md).
If a question can be answered by running something, run it. That's what turns `[simulated]`
into `[measured]`.

## Conduct

Be decent. Attack ideas hard; don't attack people. The Maintainer reserves the right to
decline contributions or block participants at his discretion.

# EXP-43 findings — retro-verification via forward test replay

Run 20 Aug 2026. Evaluated forward test suite replay against historical commit pairs
in `jobboard-v2` using isolated scratch clone execution, process-tree timeout control,
and parent-commit baseline discrimination.

Per the privacy rule (`AGENTS.md`): per-PR records live in scratch/gitignored locations;
this file carries aggregates only.

## Ranked objections to the retro-verifier thesis `[asserted]`

1. **Structural blindness to greenfield additions (Near-Fatal):** When a commit introduces
   a new component/API, its parent lacks the symbols entirely. Future tests fail on the parent
   (`ImportError`/missing export), causing the parent-commit control to classify all failures
   as un-attributable drift. The oracle can only evaluate modifications/refactors to pre-existing
   interfaces, not greenfield feature additions.
2. **Shared survivorship bias with hotfix proxy:** While the *verification mechanism* is a
   different class of facts (bytecode execution vs NLP commit mining), the *test coverage*
   shares the defect-discovery channel (developers write tests for surfaced bugs). It fixes the
   proxy's false-positive rate (~33–48% noise) but cannot sample latent unfound defects.
3. **Monolithic test suite interface/schema drift:** Over long time horizons, full test suites
   accumulate expectations of newer migrations, config flags, or mocks, causing both parent
   and child to fail.
4. **Nondeterminism & cost:** Full suite execution across 1,511 commits is computationally
   prohibitive (~35 s per commit, ~29 hours total) and vulnerable to flaky integration tests.

## Measured pilot results `[measured]`

Two experimental arms were evaluated:

| Metric | Subsystem Unit Suite (`services`) | Monolithic Unit Suite (`tests/unit`) |
|---|---|---|
| Pairs evaluated ($N$) | 15 | 5 |
| Total tests per run | 68 | 8,418–8,508 |
| Median pair duration | 2.997 s (~1.5 s/commit) | 71.188 s (~35.6 s/commit) |
| Parent PASS, Child PASS (`clean`) | 15 (100%) | 0 (0%) |
| Parent FAIL, Child FAIL (`drift`) | 0 (0%) | 5 (100%) |
| Parent PASS, Child FAIL (`defect`) | 0 (0%) | 0 (0%) |
| Parent FAIL, Child PASS (`enhancement`) | 0 (0%) | 0 (0%) |
| Drift rate | 0.0% | 100.0% |
| Evaluable parent-pass baseline | 15 | 0 |
| Stopping rule fired | `inconclusive` (n=15, β=0.0 [0.0, 0.2039]) | `rejected_high_drift` (>80% drift) |

## Did the parent-commit control discriminate? `[measured]`

**Yes, decisively.** On the monolithic suite, all 5 historical commits failed 3–7 tests when
replayed with HEAD's tests. Without the parent-commit control, a naive retro-verifier would have
falsely classified 100% of these commits as defective ($\beta = 1.0$). The parent-commit control
revealed that parent commits failed identically (3–7 tests), correctly classifying them as
test suite drift rather than artefact defect escapes.

On isolated subsystems, parent baseline pass rate was 100%, enabling valid regression verification.

## Verdict on Whewell's "Different Class of Facts" `[asserted]`

- **Mechanically:** Yes. Replaying executable test assertions is an empirical runtime test,
  independent of git commit messages and PR metadata. It eliminates false-positive regex noise.
- **Epistemologically:** Partial. Because tests are written for surfaced defects, it measures
  $\beta_{\text{regression \| surfaced}}$, not general $\beta$. It is a high-precision regression
  oracle, not a universal ground truth.

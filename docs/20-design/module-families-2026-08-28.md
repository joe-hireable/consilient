# Module families: how a large module is split here, and what enforces it

**Author:** CTO worktree · **Date:** 28 August 2026 · **HEAD at measurement:** `38b21a1` [measured]

- **Document class:** W
- **Review by:** 2026-11-28
- **Falsifier:** a split passes `verify_split` and the whole suite, and a reviewer still finds a
  behaviour change in the diff. The claim in § 5 is then wrong and these checks are decoration.

**Status:** design. Every number below was measured in this worktree today. The method is
`[measured]` because it was arrived at by running things that failed; the claim that it is the
*best* method is `[asserted]` and the section "Where the bar is" says what it was compared against.

---

## 1. What a family is

Fifteen modules are now families: an **entry point** keeping the original filename, and siblings
named `<stem>_*.py` beside it. Ninety-two files across those fifteen. `events.py` is sixteen
files, `dispatch.py` thirteen, `dashboard.py` and `harness.py` eight each. [measured]

Three properties hold for every one, and each is enforced rather than asserted. [measured]

- **The entry point keeps its public surface.** It re-exports what left it, so
  `from consilient.events import validate` still resolves and no importer elsewhere changed.
  **Narrowed on 29 August 2026 to the public surface only**, which is what this bullet always
  meant and not what it originally said. A private name that no file outside the family reaches
  is no longer re-exported: 231 such names were removed, and `tests/test_facade_surface.py`
  refuses new ones. § 6 records why, and the promise for public names is unchanged. [measured]
- **Files are layered.** Each file references only files below it in the family. There is no
  mutual import, so there is no import cycle to reason about.
- **Siblings are `<stem>_*.py`.** Not a style preference:
  `tests/test_repo_shape.py` finds the members of a governed family by globbing exactly that, so a
  sibling named otherwise is invisible to the guard that keeps the self-editing promoter out of the
  code deciding its own promotions.

## 2. Why layering, and not a shared core

The obvious way to split a module is by subject: group what belongs together, put the common
helpers in a `_shared` module. **That was tried and it failed twenty-one times out of
twenty-one.** [measured]

A subject-shaped seam drags half the module into the shared core, because pulling one symbol down
exposes the next — the moved symbol has its own references, and the closure is a fixpoint. Run
blind against a 450-line budget. [measured]

| module | shared core reached | outcome |
|---|---|---|
| `recall.py` | 686 lines | refused |
| `work_items.py` | 561 lines | refused |
| `projection.py` | 530 lines | refused |

The graph answers it without a judgement. `scripts/layer_module.py` condenses the strongly-
connected components of the symbol reference graph, sorts the condensation topologically, and
packs bottom-up. Each file then references only files below it, **so no shared module is needed at
all**, and a split is refused only when one mutually-recursive component is itself over budget —
a real finding about the module rather than an arithmetic accident. [measured]

All three modules refused above layer cleanly. [measured]

## 3. The constraint that is not about size

`monkeypatch.setattr(module, "name", fake)` binds an attribute on **one module object**. A caller
written `name(...)` resolves that name in its own module's globals, so once caller and callee are
in different files the patch reaches nothing — and it does not raise, because the facade still
binds the name and the import still succeeds. The real function runs and the test goes on
asserting something it is no longer testing. [measured]

This is why `.harness/build_driver.py` and `scripts/dispatch.py` were recorded as unsplittable.
The record was wrong about the cause: measured without the constraint, `build_driver` has 105
symbols in 105 components and `dispatch` likewise has no cycles. Pinning each patched name to
every caller is what welded sixty symbols into one 3,272-line component. [measured]

A caller written `mod.name(...)` resolves the attribute **at call time** against the object the
patch mutates, so one patch reaches every caller in every file. `scripts/seam_rewrite.py` performs
that conversion; `tests/test_seam_rewrite.py` proves the property by running it rather than by
inspecting the diff, because a text assertion would pass while the mechanism silently failed. [measured]

Of ninety-nine patch targets in the suite, exactly one was invalidated by a split, and finding it
needed an AST sweep — a single-line regex misses a `setattr` spanning two lines. [measured]

## 4. What enforces each part

| Property | Enforced by |
|---|---|
| A split moved code and did not rewrite it | `scripts/verify_split.py` — symbol body hashes, comment multiset, module-docstring prose |
| Files stay under the ceiling | `.github/scripts/check_file_length.py`, which fails in **both** directions |
| Every governed family member is protected | `tests/test_repo_shape.py` |
| No test patches a name its module only re-exports | `tests/test_patch_targets_resolve.py` |
| A split script still runs standalone | `tests/test_seam_rewrite.py` |
| The splitter's own rules | `tests/test_split_module.py` |

The file-length check failing in both directions is deliberate: it refuses a tree with **more**
files over the ceiling and a tree with **fewer** where the ceiling was not tightened, so progress
cannot be silently un-ratcheted.

## 5. Where the bar is, and what beat it

Splitting a module is not novel and this claims no novelty. The incumbents are ordinary: an IDE's
"extract module", `rope` and `libcst` codemods, and a human reading the file.

What is different here is narrow and checkable — **the split is proved to be a move.**
`verify_split` compares symbol body hashes, the family's comment multiset and its module-docstring
prose across the two trees, so "behaviour did not change" stops being a promise in a commit
message and becomes something that fails. That check earned its place three times on 28 August
2026: it caught a destroyed 58-line docstring carrying two `[cited: FULL]` flags with retrieval
dates, a thirteen-line incident record orphaned by a blank line, and a five-line loss when a tool
was run without the wrapper that preserves an entry point's docstring. [measured]

**The falsifier.** If a future split passes `verify_split` and the suite, and a behaviour change is
nonetheless found in review, the claim in this section is wrong and the checks are decoration. The
honest state today is that every defect found was found by one of them, and none by reading. [measured]

## 6. What the facade cost, and the decision taken on 29 August 2026

The paragraph this section replaces called trimming the facade "a decision, not a refactor" and
left it there. The decision has now been taken, because the cost was larger than the line count
suggested and was measured rather than argued.

**The lines.** 4,815 of the package's 33,130 — **15%** — were facade import blocks and `__all__`.
Against the 6,273 lines the fifteen splits added in total, plumbing was **77% of the growth**.
[measured]

**The marker, which was the real cost.** 391 underscore-prefixed names appeared in an entry
point's `__all__` — **34% of the exported surface**. A leading underscore is the only signal this
package has for "internal to this module", so at that share it signalled nothing: a reader could
not tell a deliberate cross-module helper from a symbol the splitter happened to lift. `__all__`
had stopped describing a boundary and started describing where the splitter put things. [measured]

**What was removed.** Of the 391, **231 were reached by no file outside their own family** and
were not used by the facade itself. Those are gone from both `__all__` and the sibling import.
The remaining private exports each have a caller that justifies them. Result: 33,130 → 32,666
lines, private share of the surface 34% → **26%**. `events.py` alone went 796 → 596. [measured]

**What it cost.** The § 1 promise, read literally, said every name importable before a split
still is — and for these 231 private names that is no longer true. It is now narrowed to the
public surface. Nothing outside the families referenced them, ruff, `mypy --strict` and 2,197
tests pass unchanged, and the one diagram edge that disappeared
(`work_items → work_items_schemas`) was a dependency the entry point genuinely no longer has.
[measured]

**What enforces it.** `tests/test_facade_surface.py` fails when a facade re-exports a private
name that no file outside the family mentions and the facade itself does not use. Without it the
splitter re-accumulates the same surface on its next run, which is working principle 4: the fix
goes in code, not in a note like this one. Its second test asserts the rule is actually
discriminating, and the guard was verified by reintroducing a removed name and watching it fail.
[measured]

Three tracked files remain over 500 lines, and none is another split away: [measured]

- `.harness/build_driver.py` (4,101) — a single 777-line `main`. Any file holding it lands near
  820, so this needs helpers *extracted*, which is a code change `verify_split` cannot prove.
- `src/consilient/events.py` (596) and `scripts/dispatch.py` (544) — still mostly facade, now an
  honest one. Going further means trimming *public* re-exports, which would break importers and
  is a different decision from the one taken here.

The redundant-alias form (`from x import y as y`) would halve what remains and preserve the
promise exactly; it is still not adopted, because realising it means re-applying every family and
a mixed style across fifteen families is worse than the lines it saves. [asserted]

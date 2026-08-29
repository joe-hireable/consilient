"""S02 — containment is established by the probe, never by the caller's claim
(ADR-0076).

Separated from the rest of the family because these are the tests that must *not* use
its contained-execute double. A caller-supplied `contained=True` is an assertion, not
evidence: `evaluate_sealed` runs the containment probe through the same `execute` it
will score with, and these pin that it does — the probe source, both probe prompts, and
the refusal when either comes back escaped. A socket bind or a write outside scratch
that gets through makes the run `candidate_unexecutable`; it never becomes a score.

The last test drives the real execute path on purpose. The isolated child can still bind
a socket and write outside scratch — that is the measured residual after Y02 process
isolation — so the real path must refuse, and scoring through it would be a false accept
of an uncontained candidate. That is the whole of β on this path: the check accepting a
bad artifact."""

from consilient.promote import (
    CONTAINMENT_DENIED,
    CONTAINMENT_PROBE_SOURCE,
    CONTAINMENT_SOCKET_ESCAPED,
    CONTAINMENT_SOCKET_PROMPT,
    CONTAINMENT_WRITE_ESCAPED,
    CONTAINMENT_WRITE_PROMPT,
    EvaluationPackage,
    EvaluationRefusal,
)
from promote_instrument_helpers import (
    _evaluate,
    _exp78,
    _manifest,
    _run_candidate,
)


def test_uncontained_real_candidate_records_candidate_unexecutable():
    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        contained=False,
    )
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "candidate_unexecutable"


def test_claimed_containment_does_not_skip_the_execute_probe():
    """A caller-supplied contained=True is not evidence. The probe is."""
    seen: list[tuple[str, tuple[str, ...]]] = []

    def execute(source: str, prompts: list[str]) -> tuple[bool, list[str | None]]:
        seen.append((source, tuple(prompts)))
        return True, [CONTAINMENT_DENIED] * len(prompts)

    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        execute=execute,
        contained=True,
    )
    assert seen, "evaluate_sealed never called execute"
    assert seen[0][0] == CONTAINMENT_PROBE_SOURCE
    assert seen[0][1] == (CONTAINMENT_SOCKET_PROMPT, CONTAINMENT_WRITE_PROMPT)
    assert isinstance(result, EvaluationPackage)


def test_socket_escape_through_execute_is_candidate_unexecutable():
    def execute(source: str, prompts: list[str]) -> tuple[bool, list[str | None]]:
        if list(prompts) == [CONTAINMENT_SOCKET_PROMPT, CONTAINMENT_WRITE_PROMPT]:
            return True, [CONTAINMENT_SOCKET_ESCAPED, CONTAINMENT_DENIED]
        raise AssertionError("scored a candidate after a socket escape")

    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        execute=execute,
        contained=True,
    )
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "candidate_unexecutable"


def test_out_of_scratch_write_through_execute_is_candidate_unexecutable():
    def execute(source: str, prompts: list[str]) -> tuple[bool, list[str | None]]:
        if list(prompts) == [CONTAINMENT_SOCKET_PROMPT, CONTAINMENT_WRITE_PROMPT]:
            return True, [CONTAINMENT_DENIED, CONTAINMENT_WRITE_ESCAPED]
        raise AssertionError("scored a candidate after an out-of-scratch write")

    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        execute=execute,
        contained=True,
    )
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "candidate_unexecutable"


def test_real_execute_path_escape_is_candidate_unexecutable():
    """The isolated child can still bind a socket and write outside scratch.

    That is the measured residual after Y02 process isolation. Scoring through
    that path is a false accept of an uncontained candidate.
    """
    manifest = _manifest()
    result = _evaluate(
        manifest,
        candidate=_exp78("helpful.py"),
        baseline=_exp78("solver.py"),
        execute=_run_candidate,
        contained=True,
    )
    assert isinstance(result, EvaluationRefusal)
    assert result.reason == "candidate_unexecutable"

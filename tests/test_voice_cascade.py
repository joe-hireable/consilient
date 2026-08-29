"""B06 — the local voice cascade: budget, refusals and utterance-to-action.

Every check here fails if the unit's guarantees are undone: no telephony reaches the
public tree (ADR-0102), no unadopted component runs, voice proposes and never commits,
and the 2 GB criterion is decided by measurement rather than by declared weights.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from consilient.local_fit import FRAMEWORK_FLOOR_BYTES


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "voice_cascade.py"


def _load_admission():
    """The sibling holding the GPU reading, which is where `subprocess` now lives.

    voice_cascade.py was split on 28 August 2026; `nvidia_used_bytes` and its `subprocess`
    import moved to voice_cascade_admission.py. Patching the entry point raised rather than
    silently missing, which is the loud version of the facade hazard.
    """
    _load_script()  # puts the scripts directory on sys.path via the entry point bootstrap
    return sys.modules["voice_cascade_admission"]


def _load_script():
    name = "consilient_voice_cascade_script"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


vc = _load_script()


class _Backends:
    """A cascade whose stages are supplied by the caller, so the pipeline is exercisable
    without a model. Absence of a model is never a fabricated transcript."""

    def __init__(self, *, speech: bool = True, endpointed: bool = True, text: str = ""):
        self._speech = speech
        self._endpointed = endpointed
        self._text = text

    def speech(self, frames: bytes) -> bool:
        return self._speech

    def endpointed(self, frames: bytes) -> bool:
        return self._endpointed

    def transcribe(self, frames: bytes) -> str:
        return self._text


def _adopted(*names: str) -> list[dict[str, str]]:
    return [
        {"name": name, "licence": "MIT", "status": "supplied", "verified": "2026-08-24"}
        for name in names
    ]


def _all_adopted() -> list[dict[str, str]]:
    return _adopted(*[stage.component for stage in vc.CASCADE])


# --- the 2 GB criterion -------------------------------------------------------------


def test_marginal_projection_is_the_declared_weights_only() -> None:
    assert vc.projected_weight_bytes() == sum(
        stage.declared_weight_bytes for stage in vc.CASCADE
    )


def test_cold_projection_adds_the_repositorys_own_framework_floor() -> None:
    assert vc.projected_cold_bytes() == (
        vc.projected_weight_bytes() + FRAMEWORK_FLOOR_BYTES
    )


def test_todays_cascade_clears_the_budget_marginally_and_exceeds_it_cold() -> None:
    """The B6 criterion of 2 GB holds for weights and fails once the driver floor the
    repository already recorded is added. Both numbers are projections, never measured."""
    projection = vc.budget_projection()
    assert projection["evidence"] == "projected"
    assert projection["marginal_verdict"] == "within"
    assert projection["cold_verdict"] == "exceeds"
    assert projection["budget_bytes"] == 2 * 1024**3


def test_a_projection_is_never_reported_as_a_measurement() -> None:
    assert vc.budget_projection()["evidence"] != "measured"


def test_the_measured_verdict_is_a_delta_not_an_absolute_reading() -> None:
    before = 3 * 1024**3
    after = before + 1_500_000_000
    result = vc.measured_footprint(before, after)
    assert result["evidence"] == "measured"
    assert result["delta_bytes"] == 1_500_000_000
    assert result["verdict"] == "within"


def test_a_measured_delta_over_budget_is_reported_as_exceeding() -> None:
    result = vc.measured_footprint(0, 3 * 1024**3)
    assert result["verdict"] == "exceeds"


def test_an_unreadable_gpu_is_unmeasured_and_never_zero() -> None:
    result = vc.measured_footprint(None, None)
    assert result["evidence"] == "unmeasured"
    assert result["verdict"] == "unmeasured"
    assert result["delta_bytes"] is None
    assert "nvidia-smi" in str(result["reason"])


def test_a_shrinking_reading_is_refused_rather_than_reported_as_a_fit() -> None:
    result = vc.measured_footprint(4 * 1024**3, 1 * 1024**3)
    assert result["verdict"] == "unmeasured"


# --- ADR-0102: no telephony in the public tree --------------------------------------


def test_a_configured_telephony_sink_is_refused() -> None:
    refusals = vc.telephony_refusals("route the reply over the twilio number")
    assert refusals
    assert any("twilio" in refusal for refusal in refusals)


def test_ordinary_speech_is_not_refused_as_telephony() -> None:
    assert vc.telephony_refusals("read the file scripts/voice_cascade.py") == ()


def test_the_module_names_no_telephony_provider_outside_its_own_prohibition() -> None:
    """ADR-0102's enforcement, scoped to this unit: the tokens may appear only in the
    denylist that states the rule, exactly as the private-repo names may."""
    # Across the whole family: the split moved the denylist into a sibling, and reading only
    # the entry point raised StopIteration rather than checking anything. The rule is about
    # the unit, and the unit is now several files.
    rest_parts: list[str] = []
    for path in [SCRIPT, *sorted(SCRIPT.parent.glob(f"{SCRIPT.stem}_*.py"))]:
        lines = path.read_text(encoding="utf-8").splitlines()
        start = next(
            (
                index
                for index, line in enumerate(lines)
                if line.startswith("TELEPHONY_TOKENS")
            ),
            None,
        )
        if start is None:
            rest_parts.append(chr(10).join(lines))
            continue
        end = next(
            index for index in range(start, len(lines)) if lines[index].rstrip() == ")"
        )
        rest_parts.append(chr(10).join(lines[:start] + lines[end + 1 :]))
    rest = chr(10).join(rest_parts).casefold()
    for token in vc.TELEPHONY_TOKENS:
        assert token not in rest, f"telephony token {token!r} outside the prohibition"


def test_a_telephony_sink_stops_the_utterance_before_any_transcript() -> None:
    result = vc.run_utterance(
        b"frames",
        _Backends(text="read the file notes.md"),
        sink="twilio",
        components=_all_adopted(),
    )
    assert result["outcome"] == "refused"
    assert result["transcript"] is None


# --- ADR-0065: an unadopted component does not run ----------------------------------


def test_every_cascade_stage_is_unadopted_today() -> None:
    """The four models are cited in the design and recorded nowhere. Live execution is
    therefore refused, and this test fails the moment one is adopted without review."""
    record = vc.load_components()
    assert vc.adoption_refusals(vc.CASCADE, record) != ()


def test_a_copyleft_stage_is_refused_even_when_recorded() -> None:
    stage = vc.Stage(
        role="tts",
        component="rhasspy/piper1-gpl",
        licence="GPL-3.0",
        declared_weight_bytes=1,
        evidence="[cited] embodiment design, voice section",
    )
    record = [
        {
            "name": "rhasspy/piper1-gpl",
            "licence": "GPL-3.0",
            "status": "supplied",
            "verified": "2026-08-24",
        }
    ]
    refusals = vc.adoption_refusals((stage,), record)
    assert any("copyleft" in refusal for refusal in refusals)


def test_live_execution_is_refused_while_a_stage_is_unadopted() -> None:
    result = vc.run_utterance(
        b"frames",
        _Backends(text="read the file notes.md"),
        live=True,
        components=[],
    )
    assert result["outcome"] == "refused"
    assert result["transcript"] is None


# --- utterance to action ------------------------------------------------------------


def _run(text: str, **kwargs):
    kwargs.setdefault("components", _all_adopted())
    return vc.run_utterance(b"frames", _Backends(text=text), **kwargs)


def test_silence_produces_no_transcript_and_no_action() -> None:
    result = vc.run_utterance(
        b"frames",
        _Backends(speech=False, text="read the file notes.md"),
        components=_all_adopted(),
    )
    assert result["outcome"] == "no_speech"
    assert result["transcript"] is None
    assert result["intent"] is None


def test_an_unfinished_turn_keeps_listening_rather_than_cutting_in() -> None:
    result = vc.run_utterance(
        b"frames",
        _Backends(endpointed=False, text="read the file"),
        components=_all_adopted(),
    )
    assert result["outcome"] == "listening"
    assert result["intent"] is None


def test_a_reversible_utterance_reaches_a_proposal_end_to_end() -> None:
    result = _run("read the file notes.md")
    assert result["outcome"] == "proposal"
    assert result["transcript"] == "read the file notes.md"
    assert result["intent"] == "read_file"
    assert result["parameter"] == "notes.md"
    assert result["reversibility_class"] == 1


def test_voice_proposes_and_never_commits() -> None:
    """Voice proposes, the click commits — supervision design, rule 6, cited to a
    measured drop from 7.4 errors per 100 words to 0.3%."""
    result = _run("read the file notes.md")
    assert result["gate"] == "propose_only"
    assert result["commit_channel"] == "non_voice"
    assert result["executed"] is False


def test_an_irreversible_capability_is_refused_by_voice_entirely() -> None:
    result = _run("search the web for parakeet benchmarks")
    assert result["outcome"] == "refused"
    assert result["reversibility_class"] == 4
    assert result["gate"] == "voice_refused"


def test_a_principal_authority_intent_is_refused_at_any_reversibility_class() -> None:
    """V0-18. An approval, verdict, gate lift or spend is his to author; the channel
    cannot be made safe enough to carry one."""
    result = _run("approve the dispatch for run 20260824")
    assert result["outcome"] == "refused"
    assert result["gate"] == "voice_refused"
    assert "V0-18" in " ".join(result["refusals"])


def test_the_readback_carries_a_distinguishing_token_and_not_a_bare_yes() -> None:
    result = _run("read the file notes.md")
    readback = str(result["readback"])
    assert "notes.md" in readback
    assert "yes" not in readback.casefold()


def test_a_non_understanding_moves_on_rather_than_asking_for_a_repeat() -> None:
    """Never say sorry, could you repeat that — measured into the bottom tier alongside
    saying nothing; MoveOn and Help top the ranking."""
    result = _run("the quarterly figures look encouraging")
    assert result["outcome"] == "not_understood"
    speech = str(result["speech"]).casefold()
    assert "repeat" not in speech
    assert "sorry" not in speech


def test_no_intent_carries_a_credential() -> None:
    for intent in vc.INTENTS:
        assert "credential" not in " ".join(intent.effect_classes)


# --- the countermeasures the design owes --------------------------------------------


def test_an_unverified_claim_is_spoken_as_unverified() -> None:
    """Speech cues raised perceived accuracy independent of correctness, N=2,165. The
    evidence tag becomes the spoken hedge, or the sentence is not spoken."""
    assert vc.spoken("the run finished", "asserted").startswith("Unverified")
    assert vc.spoken("the run finished", "measured") == "the run finished"


def test_an_unknown_evidence_tag_is_hedged_rather_than_trusted() -> None:
    assert vc.spoken("the run finished", "vibes").startswith("Unverified")


def test_barge_in_truncates_the_turn_to_what_was_actually_played() -> None:
    """A transcript containing sentences the human never heard is the bug on an
    irreversible action."""
    assert vc.truncate_to_played("one two three", 7) == "one two"
    assert vc.truncate_to_played("one two three", 0) == ""
    assert vc.truncate_to_played("one two three", 99) == "one two three"


# --- the record ---------------------------------------------------------------------


def test_the_cascade_writes_nothing_to_the_trajectory() -> None:
    """Third-party speech is personal data of people who never consented; the cascade
    returns it to its caller and persists none of it. `events.py` stays the sole writer
    and this module is not one of its callers."""
    source = SCRIPT.read_text(encoding="utf-8")
    assert "consilient.events" not in source
    assert "import events" not in source


def test_every_stage_declares_a_licence_a_size_and_where_they_came_from() -> None:
    for stage in vc.CASCADE:
        assert stage.licence
        assert stage.declared_weight_bytes > 0
        assert stage.evidence.startswith("[cited]")


def test_the_orchestrator_is_outside_the_cascade_budget() -> None:
    """The 2 GB is the cascade; the model that thinks is separately budgeted, which is
    how this reconciles with the 16 GB tier in the supervision design."""
    assert {stage.role for stage in vc.CASCADE} == {"vad", "endpoint", "asr", "tts"}


def test_main_reports_without_touching_a_model(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify by artefact: a zero exit with no JSON would not prove a report."""
    assert vc.main(["--report"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["budget"]["evidence"] == "projected"
    assert payload["adoption_refusals"]
    assert "refused" in str(payload["telephony"]).casefold()
    assert {stage["role"] for stage in payload["stages"]} == {
        "vad",
        "endpoint",
        "asr",
        "tts",
    }


def test_the_gpu_reading_queries_memory_used_not_total(monkeypatch: pytest.MonkeyPatch) -> None:
    """The 2 GB criterion is a used-memory delta, not the card's total VRAM."""
    seen: dict[str, list[str]] = {}

    class Completed:
        stdout = "1536\n"

    def fake_run(argv: list[str], **kwargs: object) -> Completed:
        seen["argv"] = list(argv)
        return Completed()

    monkeypatch.setattr(_load_admission().subprocess, "run", fake_run)
    assert vc.nvidia_used_bytes() == 1536 * 1024 * 1024
    assert "--query-gpu=memory.used" in seen["argv"]


def test_nvidia_used_bytes_is_none_when_the_binary_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(argv: object, **kwargs: object) -> object:
        raise FileNotFoundError("nvidia-smi")

    monkeypatch.setattr(_load_admission().subprocess, "run", fake_run)
    assert vc.nvidia_used_bytes() is None


def test_cc_by_is_not_refused_as_copyleft() -> None:
    """Parakeet's CC-BY-4.0 needs a recorded decision; it is not share-alike."""
    stage = next(item for item in vc.CASCADE if item.role == "asr")
    record = [
        {
            "name": stage.component,
            "licence": "CC-BY-4.0",
            "status": "supplied",
            "verified": "2026-08-24",
        }
    ]
    refusals = vc.adoption_refusals((stage,), record)
    assert not any("copyleft" in refusal for refusal in refusals)


@pytest.mark.parametrize("role", ["vad", "endpoint", "asr", "tts"])
def test_each_role_appears_exactly_once(role: str) -> None:
    assert sum(stage.role == role for stage in vc.CASCADE) == 1

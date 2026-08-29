"""B06 — the local voice cascade: utterance to a proposed action, local only.

The cascade is Silero VAD -> Smart Turn -> Parakeet TDT -> orchestrator -> Kokoro, as
specified in `docs/20-design/observability-steering-and-embodiment-2026-08-23.md`. This
module is the part that decides *whether the cascade may run and what an utterance is
allowed to become*. It is deliberately not an audio runtime: Pipecat (BSD-2) and LiveKit
Agents (Apache-2.0) already orchestrate this exact stage graph and are named in
`docs/20-design/supervision-escalation-and-sessions-2026-08-23.md` § 8 [cited]. Writing
a third one would be the second orchestrator this project forbids. The four stage
backends are injected; when none exists the cascade refuses rather than fabricating a
transcript.

Four things it enforces, each with a check in `tests/test_voice_cascade.py`:

* **No telephony.** ADR-0102 keeps a dialler out of the public tree. A provider token may
  appear in this file only inside `TELEPHONY_TOKENS`, which is the rule stating the
  prohibition, and a sink naming one stops the turn before a transcript exists.
* **No unadopted component runs.** All four models are cited in the design and recorded
  in neither `docs/legal/adopted-components.json` nor `docs/decisions/adopted-deps.json`,
  so live execution is refused today. Parakeet's CC-BY-4.0 needs a recorded decision, and
  a copyleft stage is refused outright — `piper1-gpl` is the case the design names.
* **Voice proposes; the click commits.** A human review stage cut dictation errors from
  7.4 per 100 words to 0.3% in production [cited, Zhou et al., JAMA Netw Open 2018].
  Nothing here executes, and a principal-authority utterance — approval, verdict, gate
  lift, spend — is refused at any reversibility class under V0-18.

Every `[cited]` reference in this module is second-hand: it is quoted from the two design
documents named above, which retrieved it. None of the underlying papers was read here.
* **The 2 GB criterion is decided by measurement.** Declared weights are a projection.
  The repository already recorded that a fit needs W + KV + G + F and that G cannot be
  predicted without loading the model — see `local-model-fit-arithmetic.md` §§ 5-6 under
  `docs/10-research/` [cited] — so `nvidia-smi` is read as a *delta* around a load. An
  absolute reading is not the cascade's footprint; that document says so of its own number.

Nothing is persisted. Inbound speech is personal data of people who never consented, and
neither embodiment design has a data-protection section — so the transcript is returned
to the caller and written nowhere. `events.py` remains the sole writer and this module
is not one of its callers.

The stage table, the intent vocabulary and the refusal predicates now live beside this
file in `voice_cascade_admission.py` — `Stage`/`CASCADE`, `Intent`/`INTENTS`,
`Backends`, the telephony and copyleft token lists, `telephony_refusals`,
`adoption_refusals`, `load_components`, the speech shaping (`spoken`,
`truncate_to_played`, the parse and the readback), and the GPU reading
(`nvidia_used_bytes`, `measured_footprint`, `projected_weight_bytes`). What remains here
is the composition: the budget projection, `run_utterance`, the report and the command
line."""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# This directory is not a package, so a sibling module is importable only when it is on
# sys.path. Running this file as a script puts it there; loading it through importlib by
# path does not. A no-op in the script case.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from typing import Sequence
from voice_cascade_admission import (
    BUDGET_BYTES,
    Backends,
    CASCADE,
    INTENTS,
    Intent,
    ROOT,
    Stage,
    TELEPHONY_TOKENS,
    _outcome,
    _parse,
    _readback,
    adoption_refusals,
    load_components,
    nvidia_used_bytes,
    projected_weight_bytes,
    spoken,
    telephony_refusals,
)

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from consilient.capabilities import classify_reversibility
from consilient.local_fit import FRAMEWORK_FLOOR_BYTES

from voice_cascade_admission import (
    COMPONENT_RECORD,
    COPYLEFT_TOKENS,
    ROOT,
    SPEAKABLE_UNHEDGED,
    _copyleft,
    _normalise,
    measured_footprint,
    truncate_to_played,
)

__all__ = [
    "BUDGET_BYTES",
    "Backends",
    "CASCADE",
    "COMPONENT_RECORD",
    "COPYLEFT_TOKENS",
    "INTENTS",
    "Intent",
    "ROOT",
    "SPEAKABLE_UNHEDGED",
    "Stage",
    "TELEPHONY_TOKENS",
    "_copyleft",
    "_normalise",
    "_outcome",
    "_parse",
    "_readback",
    "adoption_refusals",
    "budget_projection",
    "load_components",
    "main",
    "measured_footprint",
    "nvidia_used_bytes",
    "projected_cold_bytes",
    "projected_weight_bytes",
    "report",
    "run_utterance",
    "spoken",
    "telephony_refusals",
    "truncate_to_played",
]


def projected_cold_bytes(stages: Sequence[Stage] = CASCADE) -> int:
    """Weights plus the driver/allocator floor the repository already recorded at
    ~0.8 GiB on a Windows box with a display [cited, local-model-fit-arithmetic.md § 5]."""
    return projected_weight_bytes(stages) + FRAMEWORK_FLOOR_BYTES


def budget_projection(stages: Sequence[Stage] = CASCADE) -> dict[str, object]:
    """Both readings of the 2 GB criterion, tagged as the projections they are.

    The unit's done criterion holds against declared weights (~1.61 GB) and fails once
    the framework floor is added (~2.47 GB). That is not a contradiction to argue away:
    it means the criterion is about the *marginal* footprint, and only a measured delta
    around a real load can settle it.
    """
    marginal = projected_weight_bytes(stages)
    cold = projected_cold_bytes(stages)
    return {
        "evidence": "projected",
        "budget_bytes": BUDGET_BYTES,
        "framework_floor_bytes": FRAMEWORK_FLOOR_BYTES,
        "marginal_bytes": marginal,
        "cold_bytes": cold,
        "marginal_verdict": "within" if marginal <= BUDGET_BYTES else "exceeds",
        "cold_verdict": "within" if cold <= BUDGET_BYTES else "exceeds",
        "note": (
            "Declared weights, not resident footprints. The compute-graph term cannot be "
            "predicted without loading the model, so only a measured delta decides this."
        ),
    }


def run_utterance(
    frames: bytes,
    backends: Backends,
    *,
    sink: str = "local",
    live: bool = False,
    components: Sequence[dict[str, object]] | None = None,
    intents: Sequence[Intent] = INTENTS,
) -> dict[str, object]:
    """Run one utterance to a proposed action. Nothing is executed and nothing is stored.

    The gates run before the transcript exists, so a refused turn never produces one.
    """
    refusals = telephony_refusals(sink)
    if refusals:
        return _outcome(refusals=refusals, speech=spoken(refusals[0], "cited"))

    if live:
        record = list(components) if components is not None else load_components()
        refusals = adoption_refusals(CASCADE, record)
        if refusals:
            return _outcome(refusals=refusals, speech=spoken(refusals[0], "cited"))

    if not backends.speech(frames):
        return _outcome(outcome="no_speech", gate="propose_only")

    if not backends.endpointed(frames):
        # Semantic endpointing, not a silence timer: a pause before authorising
        # something is exactly when a timer cuts people off.
        return _outcome(outcome="listening", gate="propose_only")

    transcript = backends.transcribe(frames).strip()
    parsed = _parse(transcript, intents) if transcript else None
    if parsed is None:
        # Never "sorry, could you repeat that" — measured into the bottom tier alongside
        # saying nothing; MoveOn and Help top the ranking.
        return _outcome(
            outcome="not_understood",
            transcript=transcript or None,
            gate="propose_only",
            speech="I can read a file, run the tests, or list what needs you.",
        )

    intent, parameter = parsed
    if intent.principal_authority:
        refusal = (
            f"V0-18: an approval, verdict, gate lift or spend is authored by the "
            f"principal; voice cannot carry {intent.name!r}"
        )
        return _outcome(
            transcript=transcript,
            intent=intent.name,
            parameter=parameter or None,
            reversibility_class=classify_reversibility(
                intent.kind, intent.tool, effect_classes=intent.effect_classes
            ),
            refusals=(refusal,),
            speech=spoken(refusal, "cited"),
        )

    reversibility = classify_reversibility(
        intent.kind, intent.tool, effect_classes=intent.effect_classes
    )
    if reversibility == 4:
        refusal = (
            f"{intent.name!r} is reversibility class 4 — irreversible and consequential; "
            f"voice is refused for it"
        )
        return _outcome(
            transcript=transcript,
            intent=intent.name,
            parameter=parameter or None,
            reversibility_class=reversibility,
            refusals=(refusal,),
            speech=spoken(refusal, "cited"),
        )

    readback = _readback(intent, parameter)
    return _outcome(
        outcome="proposal",
        transcript=transcript,
        intent=intent.name,
        parameter=parameter or None,
        reversibility_class=reversibility,
        gate="propose_only",
        readback=readback,
        speech=readback,
    )


# --- the operator surface -----------------------------------------------------------


def report(measure: bool = False) -> dict[str, object]:
    """What the cascade would cost and why it will not run. No model is touched."""
    payload: dict[str, object] = {
        "stages": [
            {
                "role": stage.role,
                "component": stage.component,
                "licence": stage.licence,
                "declared_weight_bytes": stage.declared_weight_bytes,
                "evidence": stage.evidence,
            }
            for stage in CASCADE
        ],
        "budget": budget_projection(),
        "adoption_refusals": list(adoption_refusals(CASCADE, load_components())),
        "telephony": "refused by ADR-0102; no provider is reachable from this module",
    }
    if measure:
        used = nvidia_used_bytes()
        payload["gpu_memory_used_bytes"] = used
        payload["gpu_reading"] = (
            "an absolute reading, not a cascade footprint; a footprint needs a "
            "before/after delta around a load, which is refused while a stage is "
            "unadopted"
        )
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report the local voice cascade's budget, licences and refusals."
    )
    parser.add_argument(
        "--report", action="store_true", help="Emit the cascade report as JSON."
    )
    parser.add_argument(
        "--measure",
        action="store_true",
        help="Also read nvidia-smi memory.used, tagged as the absolute reading it is.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.report and not args.measure:
        parser.print_help()
        return 0
    json.dump(report(measure=args.measure), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

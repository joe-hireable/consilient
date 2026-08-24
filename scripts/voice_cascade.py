"""B06 — the local voice cascade: utterance to a proposed action, local only.

The cascade is Silero VAD -> Smart Turn -> Parakeet TDT -> orchestrator -> Kokoro, as
specified in `docs/20-design/observability-steering-and-embodiment-2026-08-23.md`. This
module is the part that decides *whether the cascade may run and what an utterance is
allowed to become*. It is deliberately not an audio runtime: Pipecat (BSD-2) and LiveKit
Agents (Apache-2.0) already orchestrate this exact stage graph and are named in
`docs/20-design/supervision-escalation-and-sessions-2026-08-23.md` § 8 [cited]. Writing a
third one would be the second orchestrator this project forbids. The four stage backends
are injected; when none exists the cascade refuses rather than fabricating a transcript.

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
to the caller and written nowhere. `events.py` remains the sole writer and this module is
not one of its callers.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from consilient.capabilities import classify_reversibility  # noqa: E402
from consilient.local_fit import FRAMEWORK_FLOOR_BYTES  # noqa: E402

COMPONENT_RECORD = ROOT / "docs" / "legal" / "adopted-components.json"

# The unit's own criterion: "under 2 GB resident" for the cascade, leaving the rest of
# the card for the model that thinks. [cited] embodiment design, voice section.
BUDGET_BYTES = 2 * 1024**3

# The provider and protocol tokens below are the rule stating ADR-0102's prohibition.
# This literal is the only place in this module where one may be named, and
# `test_the_module_names_no_telephony_provider_outside_its_own_prohibition` fails if one
# appears anywhere else — the same shape as the private-repository name rule in AGENTS.md.
TELEPHONY_TOKENS: frozenset[str] = frozenset(
    {
        "twilio",
        "vonage",
        "plivo",
        "telnyx",
        "sinch",
        "signalwire",
        "pstn",
        "sip:",
        "sip trunk",
        "10dlc",
    }
)

# Share-alike and reciprocal licences the project will not carry. `piper1-gpl` is the
# case the design names; the existing component check denies "AGPL" by substring and so
# does not catch a bare "GPL-3.0", which is why this list exists here as well.
COPYLEFT_TOKENS: tuple[str, ...] = ("agpl", "gpl", "sspl", "cc-by-sa", "osl")

# Only a claim whose evidence has been checked may be spoken unhedged. Speech cues
# significantly raised perceived accuracy independent of correctness, N=2,165
# [cited, arXiv:2405.06079] — a measured effect this design amplifies on purpose, so the
# evidence tag becomes the spoken hedge.
SPEAKABLE_UNHEDGED: frozenset[str] = frozenset({"measured", "cited"})


@dataclass(frozen=True)
class Stage:
    """One cascade stage: what runs, under what licence, and how big it is declared to be."""

    role: str
    component: str
    licence: str
    declared_weight_bytes: int
    evidence: str


# Sizes are the design document's own figures, in decimal bytes as it states them. They
# are declared weights, not resident footprints, and this module never calls them measured.
CASCADE: tuple[Stage, ...] = (
    Stage(
        role="vad",
        component="snakers4/silero-vad",
        licence="MIT",
        declared_weight_bytes=2_000_000,
        evidence="[cited] embodiment design, voice section: MIT, 2 MB",
    ),
    Stage(
        role="endpoint",
        component="pipecat-ai/smart-turn",
        licence="BSD-2-Clause",
        declared_weight_bytes=8_000_000,
        evidence="[cited] embodiment design, voice section: BSD-2, 8 MB, ~10 ms CPU",
    ),
    Stage(
        role="asr",
        component="nvidia/parakeet-tdt-0.6b",
        licence="CC-BY-4.0",
        declared_weight_bytes=1_200_000_000,
        evidence="[cited] embodiment design, voice section: CC-BY-4.0, ~1.2 GB",
    ),
    Stage(
        role="tts",
        component="hexgrad/kokoro-82m",
        licence="Apache-2.0",
        declared_weight_bytes=400_000_000,
        evidence="[cited] embodiment design, voice section: Apache-2.0, ~0.4 GB",
    ),
)


@dataclass(frozen=True)
class Intent:
    """A phrase the cascade will act on, bound to the capability it would reach.

    `principal_authority` marks the V0-18 classes — approval, consent, verdict, gate lift,
    spend. They are refused whatever their reversibility class, because the objection is
    who authored the decision, not how hard it is to undo.
    """

    name: str
    trigger: str
    kind: str
    tool: str
    effect_classes: tuple[str, ...]
    principal_authority: bool = False


INTENTS: tuple[Intent, ...] = (
    Intent("read_file", "read the file", "tool", "read", ("data.read",)),
    Intent("run_tests", "run the tests", "tool", "bash", ("process.run",)),
    Intent("search_web", "search the web", "tool", "websearch", ()),
    Intent(
        "approve_dispatch",
        "approve the dispatch",
        "tool",
        "read",
        ("data.read",),
        principal_authority=True,
    ),
)


class Backends(Protocol):
    """The four stage models, injected. No default exists: a cascade with no models
    refuses, and a refusal is a truthful outcome where a fabricated transcript is not."""

    def speech(self, frames: bytes) -> bool: ...

    def endpointed(self, frames: bytes) -> bool: ...

    def transcribe(self, frames: bytes) -> str: ...


# --- the budget ---------------------------------------------------------------------


def projected_weight_bytes(stages: Sequence[Stage] = CASCADE) -> int:
    """Declared weights only — the marginal cost of the cascade on a card whose driver
    context is already resident because something else is running on it."""
    return sum(stage.declared_weight_bytes for stage in stages)


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


def nvidia_used_bytes() -> int | None:
    """GPU memory currently in use, or None when it cannot be read.

    Verified by artefact: the number is parsed, and an exit code alone is never taken as
    a reading. Text mode carries an explicit encoding because the Windows default is
    cp1252 and crashes on ordinary tool output.
    """
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            check=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines or not lines[0].isdigit():
        return None
    return int(lines[0]) * 1024 * 1024


def measured_footprint(before: int | None, after: int | None) -> dict[str, object]:
    """Decide the 2 GB criterion from a before/after delta around a cascade load.

    An absolute reading is refused as evidence. `local-model-fit-arithmetic.md` § 7 says
    of its own 29,442 MiB figure that it "is not the model's footprint" because a
    concurrent process could not be separated from it; the same objection applies here,
    and a delta is the cheapest way to answer it.
    """
    if before is None or after is None:
        return {
            "evidence": "unmeasured",
            "verdict": "unmeasured",
            "delta_bytes": None,
            "budget_bytes": BUDGET_BYTES,
            "reason": "nvidia-smi did not return a readable memory.used value",
        }
    delta = after - before
    if delta < 0:
        return {
            "evidence": "unmeasured",
            "verdict": "unmeasured",
            "delta_bytes": delta,
            "budget_bytes": BUDGET_BYTES,
            "reason": (
                "GPU memory fell across the load, so another process moved during the "
                "reading and no cascade footprint can be attributed from it"
            ),
        }
    return {
        "evidence": "measured",
        "verdict": "within" if delta <= BUDGET_BYTES else "exceeds",
        "delta_bytes": delta,
        "budget_bytes": BUDGET_BYTES,
        "reason": "nvidia-smi memory.used delta across the cascade load",
    }


# --- the refusals -------------------------------------------------------------------


def telephony_refusals(*texts: str) -> tuple[str, ...]:
    """Refuse any sink, configuration or route naming a telephony provider (ADR-0102)."""
    refusals: list[str] = []
    for text in texts:
        folded = text.casefold()
        for token in sorted(TELEPHONY_TOKENS):
            if token in folded:
                refusals.append(
                    f"ADR-0102: telephony is not in the open-source tree; "
                    f"{token!r} is refused"
                )
    return tuple(refusals)


def _normalise(name: str) -> str:
    return re.sub(r"[-_./]+", "-", name).casefold()


def load_components(path: Path = COMPONENT_RECORD) -> list[dict[str, object]]:
    """Read the adopted-component record. An unreadable record adopts nothing."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    components = payload.get("components") if isinstance(payload, dict) else None
    if not isinstance(components, list):
        return []
    return [entry for entry in components if isinstance(entry, dict)]


def _copyleft(licence: str) -> str | None:
    folded = licence.casefold()
    return next((token for token in COPYLEFT_TOKENS if token in folded), None)


def adoption_refusals(
    stages: Sequence[Stage], record: Sequence[dict[str, object]]
) -> tuple[str, ...]:
    """Refuse a stage that is unrecorded, recorded as refused, or copyleft.

    ADR-0065 makes adoption a recorded decision rather than a default. All four stages
    are unrecorded today, which is the honest reason live execution is refused — not a
    missing download.
    """
    index = {
        _normalise(str(entry.get("name", ""))): entry
        for entry in record
        if isinstance(entry.get("name"), str)
    }
    refusals: list[str] = []
    for stage in stages:
        entry = index.get(_normalise(stage.component))
        licences = [stage.licence]
        if entry is not None:
            licences.append(str(entry.get("licence", "")))
        copyleft = next(
            (token for token in (_copyleft(text) for text in licences) if token), None
        )
        if copyleft is not None:
            refusals.append(
                f"{stage.role}: {stage.component} is copyleft ({copyleft.upper()}); "
                f"the project does not carry it"
            )
            continue
        if entry is None:
            refusals.append(
                f"{stage.role}: {stage.component} is not recorded in "
                f"{COMPONENT_RECORD.name}; ADR-0065 makes adoption a decision, "
                f"not a default"
            )
            continue
        if str(entry.get("status", "")) != "supplied":
            refusals.append(
                f"{stage.role}: {stage.component} is recorded as "
                f"{entry.get('status')!r} and does not run"
            )
    return tuple(refusals)


# --- speech -------------------------------------------------------------------------


def spoken(text: str, evidence: str) -> str:
    """Hedge any claim whose evidence has not been checked, before it is voiced."""
    if evidence.casefold() in SPEAKABLE_UNHEDGED:
        return text
    return f"Unverified — {text}"


def truncate_to_played(generated: str, played_chars: int) -> str:
    """Truncate the assistant turn to what the human actually heard on barge-in.

    A turn record containing sentences they never received is the bug that desynchronises
    the agent's memory from the human's, and it is worst on the actions that matter.
    """
    return generated[: max(0, played_chars)].rstrip()


def _parse(transcript: str, intents: Sequence[Intent]) -> tuple[Intent, str] | None:
    folded = transcript.casefold().strip()
    for intent in intents:
        if folded.startswith(intent.trigger):
            return intent, transcript.strip()[len(intent.trigger) :].strip()
    return None


def _readback(intent: Intent, parameter: str) -> str:
    """Read the parsed action back with a distinguishing token, never a bare yes.

    A bare "say yes" prompt is a yes-bias magnet one ASR error from a wrong action, and
    the adversarial critic of this design showed a *fixed* spoken token is no better —
    an ASR error produces it or fails to. So the token is drawn from the parsed action
    itself, which makes the readback a check on the parse rather than an authorisation.
    """
    token = parameter or intent.name
    return f"Proposed: {intent.name.replace('_', ' ')} — {token}. Confirm on screen."


def _outcome(**fields: object) -> dict[str, object]:
    base: dict[str, object] = {
        "outcome": "refused",
        "transcript": None,
        "intent": None,
        "parameter": None,
        "reversibility_class": None,
        "gate": "voice_refused",
        "commit_channel": "non_voice",
        "executed": False,
        "readback": None,
        "speech": "",
        "refusals": (),
    }
    base.update(fields)
    return base


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

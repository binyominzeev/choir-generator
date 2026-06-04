from __future__ import annotations

from dataclasses import replace

from choirgen.generators.base import GenerationContext
from choirgen.models.score import NoteEvent, Part, note_name_to_midi
from choirgen.models.spec import VoiceSpec
from choirgen.rules.engine import WeightedConstraintEngine

_DYNAMIC_VELOCITY = {"pp": 38, "p": 50, "mp": 62, "mf": 74, "f": 88, "ff": 102}


class HarmonicVoiceStrategy:
    def generate(self, melody: Part, voice: VoiceSpec, context: GenerationContext) -> Part:
        if context.harmony is None:
            raise ValueError("Harmonic strategy requires harmonic analysis context")

        low = note_name_to_midi(voice.range.low) if voice.range and voice.range.low else None
        high = note_name_to_midi(voice.range.high) if voice.range and voice.range.high else None

        constraints = WeightedConstraintEngine(context.specification)
        max_leap = int(constraints.value_for("max_leap", 7))
        max_leap_weight = constraints.weight_for("max_leap", 0.7)
        stepwise_weight = constraints.weight_for(
            "stepwise_preference",
            constraints.preference_weight(context.specification.voice_leading.prefer.stepwise_motion, 0.8),
        )
        common_tone_weight = constraints.preference_weight(
            context.specification.voice_leading.prefer.common_tone_retention,
            0.5,
        )
        small_leap_weight = constraints.preference_weight(
            context.specification.voice_leading.prefer.small_leaps,
            0.5,
        )

        forbid_crossing = context.specification.voice_leading.forbid.voice_crossing
        forbid_parallel_fifths = context.specification.voice_leading.forbid.parallel_fifths
        forbid_parallel_octaves = context.specification.voice_leading.forbid.parallel_octaves

        notes = []
        previous_pitch: int | None = None
        previous_melody_pitch: int | None = None
        previous_chord: tuple[int, int, int] | None = None
        default_target_offset = _default_offset(voice.name)

        for index, melody_note in enumerate(melody.notes):
            harmonic_index = min(index, len(context.harmony.moments) - 1)
            moment = context.harmony.moments[harmonic_index]
            candidates = _build_candidates(
                chord_pcs=moment.chord_pcs,
                melody_pitch=melody_note.pitch,
                low=low,
                high=high,
                offset=default_target_offset,
            )
            scored = [
                (
                    candidate,
                    _score_candidate(
                        candidate=candidate,
                        melody_pitch=melody_note.pitch,
                        previous_pitch=previous_pitch,
                        previous_melody_pitch=previous_melody_pitch,
                        previous_chord=previous_chord,
                        max_leap=max_leap,
                        max_leap_weight=max_leap_weight,
                        stepwise_weight=stepwise_weight,
                        common_tone_weight=common_tone_weight,
                        small_leap_weight=small_leap_weight,
                        forbid_crossing=forbid_crossing,
                        forbid_parallel_fifths=forbid_parallel_fifths,
                        forbid_parallel_octaves=forbid_parallel_octaves,
                        root_motion_preference=voice.priority.root_motion if voice.priority.root_motion is not None else 0.0,
                        root_pc=moment.root_pc,
                    ),
                )
                for candidate in candidates
            ]

            scored.sort(key=lambda item: item[1], reverse=True)
            selected_pitch = _select_weighted_candidate(scored, context)

            notes.append(replace(melody_note, pitch=selected_pitch))
            previous_pitch = selected_pitch
            previous_melody_pitch = melody_note.pitch
            previous_chord = moment.chord_pcs

        shaped_notes = _apply_expression(notes, context)
        return melody.clone(name=voice.name, notes=shaped_notes)


def _default_offset(voice_name: str) -> int:
    lowered = voice_name.lower()
    if lowered == "alto":
        return -4
    if lowered == "tenor":
        return -12
    if lowered == "bass":
        return -19
    return -7


def _build_candidates(chord_pcs: tuple[int, int, int], melody_pitch: int, low: int | None, high: int | None, offset: int) -> list[int]:
    target = melody_pitch + offset
    start = low if low is not None else target - 24
    end = high if high is not None else target + 24
    if start > end:
        start, end = end, start

    candidates = [pitch for pitch in range(start, end + 1) if pitch % 12 in chord_pcs]
    if not candidates:
        clamped_target = target
        if low is not None:
            clamped_target = max(clamped_target, low)
        if high is not None:
            clamped_target = min(clamped_target, high)
        candidates = [clamped_target]
    return candidates


def _score_candidate(
    *,
    candidate: int,
    melody_pitch: int,
    previous_pitch: int | None,
    previous_melody_pitch: int | None,
    previous_chord: tuple[int, int, int] | None,
    max_leap: int,
    max_leap_weight: float,
    stepwise_weight: float,
    common_tone_weight: float,
    small_leap_weight: float,
    forbid_crossing: bool,
    forbid_parallel_fifths: bool,
    forbid_parallel_octaves: bool,
    root_motion_preference: float,
    root_pc: int,
) -> float:
    score = 0.0

    if forbid_crossing and candidate >= melody_pitch:
        score -= 1000.0

    score += root_motion_preference if candidate % 12 == root_pc else 0.0

    if previous_pitch is None or previous_melody_pitch is None:
        return score

    leap = abs(candidate - previous_pitch)
    score -= leap * stepwise_weight * 0.2

    if leap > max_leap:
        score -= (leap - max_leap) * max_leap_weight * 2.0

    if leap <= 4:
        score += small_leap_weight

    if previous_chord and candidate % 12 in previous_chord:
        score += common_tone_weight

    melody_motion = melody_pitch - previous_melody_pitch
    voice_motion = candidate - previous_pitch

    if forbid_parallel_fifths and _parallel_interval(previous_pitch, previous_melody_pitch, candidate, melody_pitch, 7):
        score -= 500.0
    if forbid_parallel_octaves and _parallel_interval(previous_pitch, previous_melody_pitch, candidate, melody_pitch, 0):
        score -= 500.0

    if melody_motion == 0 and voice_motion == 0:
        score += 0.2

    return score


def _parallel_interval(previous_voice: int, previous_melody: int, current_voice: int, current_melody: int, target_interval: int) -> bool:
    previous_interval = (previous_melody - previous_voice) % 12
    current_interval = (current_melody - current_voice) % 12
    same_direction = (current_voice - previous_voice) * (current_melody - previous_melody) > 0
    return previous_interval == target_interval and current_interval == target_interval and same_direction


def _select_weighted_candidate(scored: list[tuple[int, float]], context: GenerationContext) -> int:
    if not scored:
        raise ValueError("No candidates were generated")

    scored.sort(key=lambda item: item[1], reverse=True)
    best_pitch = scored[0][0]

    variation = context.specification.randomization.voice_variation
    legacy_probability = context.specification.randomization.variation.note_choice_probability
    enabled = variation.enabled or legacy_probability > 0.0
    intensity = variation.intensity if variation.enabled else legacy_probability

    if not enabled or intensity <= 0.0:
        return best_pitch

    pool = scored[: min(4, len(scored))]
    probabilities = []
    total = 0.0
    baseline = pool[0][1]
    for _, score in pool:
        weight = max(0.0001, 1.0 + (score - baseline + 1.0) * intensity)
        probabilities.append(weight)
        total += weight

    pick = context.random.random() * total
    cumulative = 0.0
    for (pitch, _), weight in zip(pool, probabilities):
        cumulative += weight
        if pick <= cumulative:
            return pitch
    # Floating-point rounding can leave a tiny uncovered tail; use last candidate deterministically.
    return pool[-1][0]


def _apply_expression(notes: list[NoteEvent], context: GenerationContext) -> list[NoteEvent]:
    if not notes:
        return notes

    expression = context.specification.expression
    dynamics = expression.dynamics
    if not dynamics.enabled:
        return notes

    phrase = context.phrase
    start_index = phrase.start_index if phrase else 0
    climax_index = phrase.climax_index if phrase else len(notes) // 2
    end_index = phrase.end_index if phrase else len(notes) - 1

    start_dyn = context.specification.phrases.behavior.start.dynamics or dynamics.base or "mp"
    climax_dyn = context.specification.phrases.behavior.climax.dynamics or "f"
    end_dyn = context.specification.phrases.behavior.end.dynamics or ("p" if expression.shaping.phrase_decay else start_dyn)

    start_velocity = _dynamic_to_velocity(start_dyn)
    climax_velocity = _dynamic_to_velocity(climax_dyn)
    end_velocity = _dynamic_to_velocity(end_dyn)

    shaped = []
    for index, note in enumerate(notes):
        velocity = start_velocity
        if expression.shaping.crescendo_towards_climax and climax_index > start_index and index <= climax_index:
            progress = (index - start_index) / max(1, climax_index - start_index)
            velocity = int(start_velocity + (climax_velocity - start_velocity) * progress)
        elif expression.shaping.phrase_decay and end_index > climax_index and index > climax_index:
            progress = (index - climax_index) / max(1, end_index - climax_index)
            velocity = int(climax_velocity + (end_velocity - climax_velocity) * progress)
        elif index >= climax_index:
            velocity = climax_velocity

        shaped.append(replace(note, velocity=max(1, min(127, velocity))))

    return shaped


def _dynamic_to_velocity(dynamic: str) -> int:
    lowered = dynamic.lower()
    if lowered == "decrescendo":
        return _DYNAMIC_VELOCITY["p"]
    return _DYNAMIC_VELOCITY.get(lowered, _DYNAMIC_VELOCITY["mp"])

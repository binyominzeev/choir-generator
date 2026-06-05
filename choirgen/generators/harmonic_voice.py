from __future__ import annotations

from dataclasses import dataclass, replace

from choirgen.generators.base import GenerationContext
from choirgen.harmony.scoring import cadence_strength_for_index, level_weight
from choirgen.models.score import NoteEvent, Part, note_name_to_midi
from choirgen.models.spec import VoiceSpec
from choirgen.rules.engine import WeightedConstraintEngine

_DYNAMIC_VELOCITY = {"pp": 38, "p": 50, "mp": 62, "mf": 74, "f": 88, "ff": 102}


@dataclass(slots=True)
class CandidateScore:
    harmony_score: float
    voice_leading_score: float
    cadence_score: float
    phrase_score: float
    voice_assignment_score: float

    @property
    def total(self) -> float:
        return (
            self.harmony_score
            * self.voice_leading_score
            * self.cadence_score
            * self.phrase_score
            * self.voice_assignment_score
        )


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
        previous_root_pc: int | None = None
        default_target_offset = _default_offset(voice.name)
        voice_breakdown: list[dict[str, float]] = []

        for index, melody_note in enumerate(melody.notes):
            harmonic_index = min(index, len(context.harmony.moments) - 1)
            moment = context.harmony.moments[harmonic_index]
            candidates = _build_candidates(
                chord_pcs=moment.chord_pcs,
                melody_pitch=melody_note.pitch,
                low=low,
                high=high,
                offset=default_target_offset,
                include_passing=(voice.priority.passing_tones or 0.0) > 0.0,
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
                        root_motion_preference=voice.priority.root_motion or 0.0,
                        melody_priority=voice.priority.melody or 0.0,
                        chord_tones_priority=voice.priority.chord_tones or 0.0,
                        passing_tones_priority=voice.priority.passing_tones or 0.0,
                        current_chord=moment.chord_pcs,
                        root_pc=moment.root_pc,
                        previous_root_pc=previous_root_pc,
                        index=index,
                        total_notes=len(melody.notes),
                        context=context,
                    ),
                )
                for candidate in candidates
            ]

            scored.sort(key=lambda item: item[1].total, reverse=True)
            selected_pitch, selected_score = _select_weighted_candidate(scored, context)

            notes.append(replace(melody_note, pitch=selected_pitch))
            voice_breakdown.append(
                {
                    "index": float(index),
                    "harmony_score": selected_score.harmony_score,
                    "voice_leading_score": selected_score.voice_leading_score,
                    "cadence_score": selected_score.cadence_score,
                    "phrase_score": selected_score.phrase_score,
                    "voice_assignment_score": selected_score.voice_assignment_score,
                    "score": selected_score.total,
                }
            )
            previous_pitch = selected_pitch
            previous_melody_pitch = melody_note.pitch
            previous_chord = moment.chord_pcs
            previous_root_pc = moment.root_pc

        shaped_notes = _apply_expression(notes, context)
        if context.explain:
            context.voice_score_breakdown[voice.name] = voice_breakdown
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


def _build_candidates(
    chord_pcs: tuple[int, int, int],
    melody_pitch: int,
    low: int | None,
    high: int | None,
    offset: int,
    include_passing: bool,
) -> list[int]:
    target = melody_pitch + offset
    start = low if low is not None else target - 24
    end = high if high is not None else target + 24
    if start > end:
        start, end = end, start

    candidate_pitches_set: set[int] = {pitch for pitch in range(start, end + 1) if pitch % 12 in chord_pcs}
    if include_passing:
        for pitch in range(max(start, target - 2), min(end, target + 2) + 1):
            if pitch % 12 not in chord_pcs:
                candidate_pitches_set.add(pitch)
    if not candidate_pitches_set:
        clamped_target = target
        if low is not None:
            clamped_target = max(clamped_target, low)
        if high is not None:
            clamped_target = min(clamped_target, high)
        return [clamped_target]
    return sorted(candidate_pitches_set)


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
    melody_priority: float,
    chord_tones_priority: float,
    passing_tones_priority: float,
    current_chord: tuple[int, int, int],
    root_pc: int,
    previous_root_pc: int | None,
    index: int,
    total_notes: int,
    context: GenerationContext,
) -> CandidateScore:
    harmony_score = 1.0 if candidate % 12 in current_chord else 0.7
    voice_leading_score = 1.0
    cadence_score = 1.0
    phrase_score = 1.0
    voice_assignment_score = 1.0

    if forbid_crossing and candidate >= melody_pitch:
        voice_leading_score *= 0.001

    if candidate % 12 == root_pc:
        harmony_score *= 1.0 + root_motion_preference * 0.2

    if previous_pitch is None or previous_melody_pitch is None:
        voice_assignment_score = _voice_assignment_score(
            candidate=candidate,
            melody_pitch=melody_pitch,
            root_pc=root_pc,
            melody_priority=melody_priority,
            chord_tones_priority=chord_tones_priority,
            passing_tones_priority=passing_tones_priority,
            root_motion_preference=root_motion_preference,
            is_chord_tone=candidate % 12 in current_chord,
        )
        cadence_score = _cadence_score(
            candidate=candidate,
            root_pc=root_pc,
            previous_root_pc=previous_root_pc,
            index=index,
            total_notes=total_notes,
            context=context,
        )
        phrase_score = _phrase_score(index=index, total_notes=total_notes, context=context, candidate=candidate, root_pc=root_pc)
        return CandidateScore(
            harmony_score=max(0.001, harmony_score),
            voice_leading_score=max(0.001, voice_leading_score),
            cadence_score=max(0.001, cadence_score),
            phrase_score=max(0.001, phrase_score),
            voice_assignment_score=max(0.001, voice_assignment_score),
        )

    leap = abs(candidate - previous_pitch)
    voice_leading_score *= max(0.2, 1.0 - leap * stepwise_weight * 0.04)

    if leap > max_leap:
        voice_leading_score *= max(0.05, 1.0 - (leap - max_leap) * max_leap_weight * 0.2)

    if leap <= 4:
        voice_leading_score *= 1.0 + small_leap_weight * 0.2

    if previous_chord and candidate % 12 in previous_chord:
        harmony_score *= 1.0 + common_tone_weight * 0.2

    melody_motion = melody_pitch - previous_melody_pitch
    voice_motion = candidate - previous_pitch

    if forbid_parallel_fifths and _parallel_interval(previous_pitch, previous_melody_pitch, candidate, melody_pitch, 7):
        voice_leading_score *= 0.05
    if forbid_parallel_octaves and _parallel_interval(previous_pitch, previous_melody_pitch, candidate, melody_pitch, 0):
        voice_leading_score *= 0.05

    if melody_motion == 0 and voice_motion == 0:
        voice_leading_score *= 1.05

    cadence_score = _cadence_score(
        candidate=candidate,
        root_pc=root_pc,
        previous_root_pc=previous_root_pc,
        index=index,
        total_notes=total_notes,
        context=context,
    )
    phrase_score = _phrase_score(index=index, total_notes=total_notes, context=context, candidate=candidate, root_pc=root_pc)
    voice_assignment_score = _voice_assignment_score(
        candidate=candidate,
        melody_pitch=melody_pitch,
        root_pc=root_pc,
        melody_priority=melody_priority,
        chord_tones_priority=chord_tones_priority,
        passing_tones_priority=passing_tones_priority,
        root_motion_preference=root_motion_preference,
        is_chord_tone=candidate % 12 in current_chord,
    )

    return CandidateScore(
        harmony_score=max(0.001, harmony_score),
        voice_leading_score=max(0.001, voice_leading_score),
        cadence_score=max(0.001, cadence_score),
        phrase_score=max(0.001, phrase_score),
        voice_assignment_score=max(0.001, voice_assignment_score),
    )


def _parallel_interval(previous_voice: int, previous_melody: int, current_voice: int, current_melody: int, target_interval: int) -> bool:
    previous_interval = (previous_melody - previous_voice) % 12
    current_interval = (current_melody - current_voice) % 12
    same_direction = (current_voice - previous_voice) * (current_melody - previous_melody) > 0
    return previous_interval == target_interval and current_interval == target_interval and same_direction


def _select_weighted_candidate(scored: list[tuple[int, CandidateScore]], context: GenerationContext) -> tuple[int, CandidateScore]:
    if not scored:
        raise ValueError("No candidates were generated")

    scored.sort(key=lambda item: item[1].total, reverse=True)
    best_pitch, best_score = scored[0]

    variation = context.specification.randomization.voice_variation
    legacy_probability = context.specification.randomization.variation.note_choice_probability
    enabled = variation.enabled or legacy_probability > 0.0
    intensity = variation.intensity if variation.enabled else legacy_probability

    if not enabled or intensity <= 0.0:
        return best_pitch, best_score

    pool = scored[: min(4, len(scored))]
    probabilities = []
    total = 0.0
    baseline = pool[0][1].total
    for _, score in pool:
        weight = max(0.0001, 1.0 + (score.total - baseline + 1.0) * intensity)
        probabilities.append(weight)
        total += weight

    pick = context.random.random() * total
    cumulative = 0.0
    for (pitch, score_data), weight in zip(pool, probabilities):
        cumulative += weight
        if pick <= cumulative:
            return pitch, score_data
    # Floating-point rounding can leave a tiny uncovered tail; use last candidate deterministically.
    return pool[-1]


def _voice_assignment_score(
    *,
    candidate: int,
    melody_pitch: int,
    root_pc: int,
    melody_priority: float,
    chord_tones_priority: float,
    passing_tones_priority: float,
    root_motion_preference: float,
    is_chord_tone: bool,
) -> float:
    distance = abs(melody_pitch - candidate)
    melody_fit = max(0.2, 1.0 - distance / 24.0)
    score = 1.0 + melody_priority * melody_fit
    if is_chord_tone:
        score += chord_tones_priority
    else:
        score += passing_tones_priority
    if candidate % 12 == root_pc:
        score += root_motion_preference
    return max(0.05, score)


def _cadence_score(
    *,
    candidate: int,
    root_pc: int,
    previous_root_pc: int | None,
    index: int,
    total_notes: int,
    context: GenerationContext,
) -> float:
    at_end = _at_phrase_end(index, total_notes, context)
    before_end = _one_before_end(index, total_notes, context)
    score = 1.0
    if not at_end and not before_end:
        return score

    tonic = context.harmony.tonic_pc if context.harmony is not None else root_pc
    authentic_weight = _level_value(context.specification.harmony.cadence_model.authentic, 0.0)
    plagal_weight = _level_value(context.specification.harmony.cadence_model.plagal, 0.0)

    if at_end:
        if previous_root_pc == (tonic + 7) % 12 and root_pc == tonic:
            score *= 1.0 + authentic_weight
        elif previous_root_pc == (tonic + 5) % 12 and root_pc == tonic:
            score *= 1.0 + plagal_weight
        elif root_pc == tonic:
            score *= 1.0 + max(authentic_weight, plagal_weight) * 0.5
    elif before_end:
        if root_pc == (tonic + 7) % 12:
            score *= 1.0 + authentic_weight * 0.5
        if root_pc == (tonic + 5) % 12:
            score *= 1.0 + plagal_weight * 0.5

    cadence_strength = _cadence_strength(index, total_notes, context)
    if at_end and cadence_strength > 1.0 and candidate % 12 == tonic:
        score *= cadence_strength
    return max(0.05, score)


def _phrase_score(*, index: int, total_notes: int, context: GenerationContext, candidate: int, root_pc: int) -> float:
    score = _cadence_strength(index, total_notes, context)
    if _at_phrase_end(index, total_notes, context) and candidate % 12 != root_pc and score > 1.0:
        score *= 0.85
    return max(0.05, score)


def _cadence_strength(index: int, total_notes: int, context: GenerationContext) -> float:
    return cadence_strength_for_index(index, total_notes, context.phrase, context.specification.phrases.behavior)


def _at_phrase_end(index: int, total_notes: int, context: GenerationContext) -> bool:
    if context.phrase is not None:
        return index >= context.phrase.end_index
    return index == total_notes - 1


def _one_before_end(index: int, total_notes: int, context: GenerationContext) -> bool:
    if context.phrase is not None:
        return index == max(0, context.phrase.end_index - 1)
    return index == max(0, total_notes - 2)


def _level_value(level: str | None, default: float) -> float:
    return level_weight(level, default)


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

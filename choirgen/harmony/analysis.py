from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from choirgen.models.score import Part
from choirgen.models.spec import ArrangementSpec

if TYPE_CHECKING:
    from choirgen.phrases.detector import PhraseProfile

_MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
_MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]
_MAJOR_QUALITY = ["maj", "min", "min", "maj", "maj", "min", "dim"]
_MINOR_QUALITY = ["min", "dim", "maj", "min", "min", "maj", "maj"]
_MAJOR_ROMANS = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
_MINOR_ROMANS = ["i", "ii°", "III", "iv", "v", "VI", "VII"]
_EMOTIONS = {
    "I": "stability",
    "ii": "preparation",
    "iii": "softness",
    "IV": "expansion",
    "V": "tension",
    "vi": "softness",
    "vii°": "instability",
    "i": "stability",
    "ii°": "instability",
    "III": "softness",
    "iv": "expansion",
    "v": "tension",
    "VI": "softness",
    "VII": "instability",
}
_LEVEL_WEIGHT = {"low": 0.3, "medium": 0.6, "high": 0.9, "strong": 1.0}


@dataclass(slots=True)
class ChordCandidate:
    root_pc: int
    chord_pcs: tuple[int, int, int]
    quality: str
    roman_numeral: str
    emotion: str
    degree: int | None
    is_diatonic: bool
    is_secondary_dominant: bool


@dataclass(slots=True)
class HarmonicMoment:
    melody_pitch: int
    degree: int
    root_pc: int
    chord_pcs: tuple[int, int, int]
    quality: str
    roman_numeral: str
    emotion: str
    candidates: list[ChordCandidate]
    score_breakdown: dict[str, float]
    total_score: float


@dataclass(slots=True)
class HarmonicContext:
    tonic_pc: int
    is_minor: bool
    moments: list[HarmonicMoment]
    progression: list[str]


def infer_harmony(melody: Part, specification: ArrangementSpec | None = None, phrase: PhraseProfile | None = None) -> HarmonicContext:
    tonic_pc, is_minor = _detect_key(melody)
    scale = _MINOR_SCALE if is_minor else _MAJOR_SCALE
    qualities = _MINOR_QUALITY if is_minor else _MAJOR_QUALITY
    romans = _MINOR_ROMANS if is_minor else _MAJOR_ROMANS

    diatonic_chords = [
        ChordCandidate(
            root_pc=(tonic_pc + scale[index]) % 12,
            chord_pcs=(
                (tonic_pc + scale[index]) % 12,
                (tonic_pc + scale[(index + 2) % 7]) % 12,
                (tonic_pc + scale[(index + 4) % 7]) % 12,
            ),
            quality=qualities[index],
            roman_numeral=romans[index],
            emotion=_EMOTIONS.get(romans[index], "neutral"),
            degree=index + 1,
            is_diatonic=True,
            is_secondary_dominant=False,
        )
        for index in range(7)
    ]
    secondary_chords = _build_secondary_dominants(diatonic_chords)
    total_notes = max(1, len(melody.notes))
    moments: list[HarmonicMoment] = []
    previous: ChordCandidate | None = None

    for index, note in enumerate(melody.notes):
        candidates = list(diatonic_chords)
        if specification and specification.harmony.chord_preference.secondary_dominants > 0:
            candidates.extend(secondary_chords)

        best_candidate = candidates[0]
        best_breakdown = {"harmony_score": 1.0, "cadence_score": 1.0, "phrase_score": 1.0}
        best_score = -1.0
        for candidate in candidates:
            breakdown = _score_harmony_candidate(
                candidate=candidate,
                melody_pitch=note.pitch,
                previous=previous,
                index=index,
                total_notes=total_notes,
                tonic_pc=tonic_pc,
                specification=specification,
                phrase=phrase,
            )
            score = breakdown["harmony_score"] * breakdown["cadence_score"] * breakdown["phrase_score"]
            if score > best_score:
                best_candidate = candidate
                best_breakdown = breakdown
                best_score = score

        moments.append(
            HarmonicMoment(
                melody_pitch=note.pitch,
                degree=best_candidate.degree or _closest_degree((best_candidate.root_pc - tonic_pc) % 12, scale) + 1,
                root_pc=best_candidate.root_pc,
                chord_pcs=best_candidate.chord_pcs,
                quality=best_candidate.quality,
                roman_numeral=best_candidate.roman_numeral,
                emotion=best_candidate.emotion,
                candidates=candidates,
                score_breakdown=best_breakdown,
                total_score=best_score,
            )
        )
        previous = best_candidate

    progression = _compress_progression([moment.roman_numeral for moment in moments])
    return HarmonicContext(tonic_pc=tonic_pc, is_minor=is_minor, moments=moments, progression=progression)


def _build_secondary_dominants(diatonic_chords: list[ChordCandidate]) -> list[ChordCandidate]:
    secondary: list[ChordCandidate] = []
    seen: set[tuple[int, tuple[int, int, int]]] = set()
    for target in diatonic_chords:
        if target.degree == 1:
            continue
        root_pc = (target.root_pc + 7) % 12
        chord_pcs = (root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12)
        key = (root_pc, chord_pcs)
        if key in seen:
            continue
        seen.add(key)
        secondary.append(
            ChordCandidate(
                root_pc=root_pc,
                chord_pcs=chord_pcs,
                quality="maj",
                roman_numeral=f"V/{target.roman_numeral}",
                emotion="tension",
                degree=None,
                is_diatonic=False,
                is_secondary_dominant=True,
            )
        )
    return secondary


def _score_harmony_candidate(
    *,
    candidate: ChordCandidate,
    melody_pitch: int,
    previous: ChordCandidate | None,
    index: int,
    total_notes: int,
    tonic_pc: int,
    specification: ArrangementSpec | None,
    phrase: PhraseProfile | None,
) -> dict[str, float]:
    melody_pc = melody_pitch % 12
    harmony_score = 1.0 if melody_pc in candidate.chord_pcs else 0.45
    cadence_score = 1.0
    phrase_score = 1.0

    if specification is not None:
        diatonic_preference = specification.harmony.chord_preference.diatonic
        secondary_preference = specification.harmony.chord_preference.secondary_dominants
        if candidate.is_diatonic:
            harmony_score *= max(0.1, diatonic_preference)
        if candidate.is_secondary_dominant:
            harmony_score *= 0.1 + max(0.0, secondary_preference)

        at_end = _is_phrase_end(index, total_notes, phrase)
        one_before_end = _is_one_before_phrase_end(index, total_notes, phrase)
        authentic = _level_value(specification.harmony.cadence_model.authentic, 0.0)
        plagal = _level_value(specification.harmony.cadence_model.plagal, 0.0)

        if at_end:
            if previous is not None and previous.root_pc == (tonic_pc + 7) % 12 and candidate.root_pc == tonic_pc:
                cadence_score *= 1.0 + authentic
            elif previous is not None and previous.root_pc == (tonic_pc + 5) % 12 and candidate.root_pc == tonic_pc:
                cadence_score *= 1.0 + plagal
            elif candidate.root_pc == tonic_pc:
                cadence_score *= 1.0 + max(authentic, plagal) * 0.5
            else:
                cadence_score *= 0.8
        elif one_before_end:
            if candidate.root_pc == (tonic_pc + 7) % 12:
                cadence_score *= 1.0 + authentic * 0.6
            if candidate.root_pc == (tonic_pc + 5) % 12:
                cadence_score *= 1.0 + plagal * 0.6

        cadence_strength = _cadence_strength_for_index(index, total_notes, phrase, specification)
        if cadence_strength > 1.0 and candidate.root_pc == tonic_pc and at_end:
            phrase_score *= cadence_strength
        elif cadence_strength > 1.0 and at_end and candidate.root_pc != tonic_pc:
            phrase_score *= 0.9

    return {
        "harmony_score": harmony_score,
        "cadence_score": cadence_score,
        "phrase_score": phrase_score,
    }


def _cadence_strength_for_index(index: int, total_notes: int, phrase: PhraseProfile | None, specification: ArrangementSpec) -> float:
    behavior = specification.phrases.behavior
    if phrase is None:
        if index == 0:
            return _level_value(behavior.start.cadence_strength, 1.0)
        if index == total_notes - 1:
            return _level_value(behavior.end.cadence_strength, 1.0)
        return _level_value(behavior.climax.cadence_strength, 1.0)
    if index <= phrase.start_index:
        return _level_value(behavior.start.cadence_strength, 1.0)
    if index >= phrase.end_index:
        return _level_value(behavior.end.cadence_strength, 1.0)
    return _level_value(behavior.climax.cadence_strength, 1.0)


def _is_phrase_end(index: int, total_notes: int, phrase: PhraseProfile | None) -> bool:
    if phrase is not None:
        return index >= phrase.end_index
    return index == total_notes - 1


def _is_one_before_phrase_end(index: int, total_notes: int, phrase: PhraseProfile | None) -> bool:
    if phrase is not None:
        return index == max(0, phrase.end_index - 1)
    return index == max(0, total_notes - 2)


def _level_value(level: str | None, default: float) -> float:
    if level is None:
        return default
    return _LEVEL_WEIGHT.get(level.lower(), default)


def _compress_progression(romans: list[str]) -> list[str]:
    progression: list[str] = []
    for roman in romans:
        if not progression or progression[-1] != roman:
            progression.append(roman)
    return progression


def _detect_key(melody: Part) -> tuple[int, bool]:
    pcs = [note.pitch % 12 for note in melody.notes]
    if not pcs:
        return 0, False

    best_score = -1.0
    best = (0, False)
    for tonic in range(12):
        major_score = _scale_fit_score(pcs, tonic, _MAJOR_SCALE)
        if major_score > best_score:
            best_score = major_score
            best = (tonic, False)
        minor_score = _scale_fit_score(pcs, tonic, _MINOR_SCALE)
        if minor_score > best_score:
            best_score = minor_score
            best = (tonic, True)
    return best


def _scale_fit_score(pitch_classes: list[int], tonic_pc: int, scale: list[int]) -> float:
    scale_pcs = {(tonic_pc + interval) % 12 for interval in scale}
    in_scale = sum(1 for pc in pitch_classes if pc in scale_pcs)
    tonic_hits = sum(1 for pc in pitch_classes if pc == tonic_pc)
    # Slight tonic bias helps break ties toward keys where melody resolves on tonic.
    return in_scale + tonic_hits * 0.15


def _closest_degree(relative_pc: int, scale: list[int]) -> int:
    best_degree = 0
    best_distance = 12
    for degree, scale_pc in enumerate(scale):
        distance = min((relative_pc - scale_pc) % 12, (scale_pc - relative_pc) % 12)
        if distance < best_distance:
            best_distance = distance
            best_degree = degree
    return best_degree

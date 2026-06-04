from __future__ import annotations

from dataclasses import dataclass

from choirgen.models.score import Part

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


@dataclass(slots=True)
class HarmonicMoment:
    degree: int
    root_pc: int
    chord_pcs: tuple[int, int, int]
    quality: str
    roman_numeral: str
    emotion: str


@dataclass(slots=True)
class HarmonicContext:
    tonic_pc: int
    is_minor: bool
    moments: list[HarmonicMoment]


def infer_harmony(melody: Part) -> HarmonicContext:
    tonic_pc, is_minor = _detect_key(melody)
    scale = _MINOR_SCALE if is_minor else _MAJOR_SCALE
    qualities = _MINOR_QUALITY if is_minor else _MAJOR_QUALITY
    romans = _MINOR_ROMANS if is_minor else _MAJOR_ROMANS

    moments: list[HarmonicMoment] = []
    for note in melody.notes:
        degree = _closest_degree((note.pitch - tonic_pc) % 12, scale)
        root_pc = (tonic_pc + scale[degree]) % 12
        third_pc = (tonic_pc + scale[(degree + 2) % 7]) % 12
        fifth_pc = (tonic_pc + scale[(degree + 4) % 7]) % 12
        roman = romans[degree]
        moments.append(
            HarmonicMoment(
                degree=degree + 1,
                root_pc=root_pc,
                chord_pcs=(root_pc, third_pc, fifth_pc),
                quality=qualities[degree],
                roman_numeral=roman,
                emotion=_EMOTIONS.get(roman, "neutral"),
            )
        )

    return HarmonicContext(tonic_pc=tonic_pc, is_minor=is_minor, moments=moments)


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

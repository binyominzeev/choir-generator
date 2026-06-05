from __future__ import annotations

from typing import TYPE_CHECKING

from choirgen.models.spec import PhraseBehaviorSpec

if TYPE_CHECKING:
    from choirgen.phrases.detector import PhraseProfile

_LEVEL_WEIGHT = {"low": 0.3, "medium": 0.6, "high": 0.9, "strong": 1.0}
_CADENCE_STRENGTH = {"low": 0.85, "medium": 1.0, "high": 1.2, "strong": 1.35}


def level_weight(level: str | None, default: float) -> float:
    if level is None:
        return default
    return _LEVEL_WEIGHT.get(level.lower(), default)


def cadence_strength(level: str | None, default: float) -> float:
    if level is None:
        return default
    return _CADENCE_STRENGTH.get(level.lower(), default)


def cadence_strength_for_index(index: int, total_notes: int, phrase: PhraseProfile | None, behavior: PhraseBehaviorSpec) -> float:
    if phrase is None:
        if total_notes == 1:
            return max(
                cadence_strength(behavior.start.cadence_strength, 1.0),
                cadence_strength(behavior.end.cadence_strength, 1.0),
            )
        if index == 0:
            return cadence_strength(behavior.start.cadence_strength, 1.0)
        if index == total_notes - 1:
            return cadence_strength(behavior.end.cadence_strength, 1.0)
        return cadence_strength(behavior.climax.cadence_strength, 1.0)
    if index <= phrase.start_index:
        return cadence_strength(behavior.start.cadence_strength, 1.0)
    if index >= phrase.end_index:
        return cadence_strength(behavior.end.cadence_strength, 1.0)
    return cadence_strength(behavior.climax.cadence_strength, 1.0)

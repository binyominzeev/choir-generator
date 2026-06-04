from __future__ import annotations

from collections.abc import Iterable

from choirgen.models.score import Part
from choirgen.models.spec import ArrangementSpec, VoiceSpec
from choirgen.rules.base import VoiceRule

_LEVEL_WEIGHT = {"low": 0.3, "medium": 0.6, "high": 0.9, "strong": 1.0}


class RuleEngine:
    def __init__(self, rules: Iterable[VoiceRule]):
        self._rules = list(rules)

    def apply(self, part: Part, melody: Part, voice: VoiceSpec) -> Part:
        current = part
        for rule in self._rules:
            current = rule.apply(current, melody, voice)
        return current


class WeightedConstraintEngine:
    def __init__(self, specification: ArrangementSpec):
        self._specification = specification

    def weight_for(self, name: str, default: float) -> float:
        weighted_rule = self._specification.rules.get(name)
        if weighted_rule is not None and weighted_rule.weight is not None:
            return weighted_rule.weight
        return default

    def value_for(self, name: str, default: int | float) -> int | float:
        weighted_rule = self._specification.rules.get(name)
        if weighted_rule is None or weighted_rule.value is None:
            return default
        value = weighted_rule.value
        if isinstance(default, int):
            return int(value)
        return float(value)

    def preference_weight(self, level: str | None, default: float) -> float:
        if level is None:
            return default
        return _LEVEL_WEIGHT.get(level.lower(), default)

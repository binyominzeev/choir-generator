from __future__ import annotations

from collections.abc import Iterable

from choirgen.models.score import Part
from choirgen.models.spec import VoiceSpec
from choirgen.rules.base import VoiceRule


class RuleEngine:
    def __init__(self, rules: Iterable[VoiceRule]):
        self._rules = list(rules)

    def apply(self, part: Part, melody: Part, voice: VoiceSpec) -> Part:
        current = part
        for rule in self._rules:
            current = rule.apply(current, melody, voice)
        return current

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Protocol

from choirgen.models.score import Part
from choirgen.models.spec import ArrangementSpec, VoiceSpec


@dataclass(slots=True)
class GenerationContext:
    specification: ArrangementSpec
    random: Random


class GenerationStrategy(Protocol):
    def generate(self, melody: Part, voice: VoiceSpec, context: GenerationContext) -> Part:
        ...

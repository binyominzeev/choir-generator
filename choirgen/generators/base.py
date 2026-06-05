from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Protocol

from choirgen.harmony.analysis import HarmonicContext
from choirgen.models.score import Part
from choirgen.models.spec import ArrangementSpec, VoiceSpec
from choirgen.phrases.detector import PhraseProfile


@dataclass(slots=True)
class GenerationContext:
    specification: ArrangementSpec
    random: Random
    harmony: HarmonicContext | None = None
    phrase: PhraseProfile | None = None
    explain: bool = False
    voice_score_breakdown: dict[str, list[dict[str, float]]] = field(default_factory=dict)


class GenerationStrategy(Protocol):
    def generate(self, melody: Part, voice: VoiceSpec, context: GenerationContext) -> Part:
        ...

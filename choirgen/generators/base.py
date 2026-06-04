from __future__ import annotations

from dataclasses import dataclass
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


class GenerationStrategy(Protocol):
    def generate(self, melody: Part, voice: VoiceSpec, context: GenerationContext) -> Part:
        ...

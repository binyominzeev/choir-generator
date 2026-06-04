from __future__ import annotations

from choirgen.generators.base import GenerationContext
from choirgen.models.score import Part
from choirgen.models.spec import VoiceSpec


class FixedIntervalStrategy:
    def generate(self, melody: Part, voice: VoiceSpec, context: GenerationContext) -> Part:
        if voice.strategy is None:
            raise ValueError(f"Voice '{voice.name}' is missing a generation strategy")
        semitones = voice.strategy.require_int("interval", "semitones")
        notes = [note.transpose(semitones) for note in melody.notes]
        return melody.clone(name=voice.name, notes=notes)

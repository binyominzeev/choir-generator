from __future__ import annotations

from pathlib import Path
from random import Random

from choirgen.exporters.factory import create_exporter
from choirgen.generators.base import GenerationContext
from choirgen.generators.factory import create_strategy
from choirgen.midi.reader import read_monophonic_midi
from choirgen.models.score import Arrangement
from choirgen.parser.casl import CaslParser
from choirgen.rules.engine import RuleEngine
from choirgen.rules.range import RangeRule


class ChoirGeneratorApp:
    def __init__(self, parser: CaslParser | None = None) -> None:
        self._parser = parser or CaslParser()
        self._rule_engine = RuleEngine([RangeRule()])

    def generate(self, melody_path: str, spec_path: str, output_path: str | None = None, output_format: str = "midi") -> Path:
        specification = self._parser.parse_file(spec_path)
        loaded_melody = read_monophonic_midi(melody_path)
        context = GenerationContext(
            specification=specification,
            random=Random(specification.randomization.seed),
        )

        parts = [loaded_melody.part.clone(name=specification.original_voice_name())]
        for voice in specification.generated_voices():
            if voice.strategy is None:
                raise ValueError(f"Generated voice '{voice.name}' is missing a strategy")
            strategy = create_strategy(voice.strategy.type)
            generated_part = strategy.generate(loaded_melody.part, voice, context)
            generated_part = self._rule_engine.apply(generated_part, loaded_melody.part, voice)
            parts.append(generated_part)

        arrangement = Arrangement(
            title=specification.project.name,
            parts=parts,
            ticks_per_beat=loaded_melody.ticks_per_beat,
            meta_messages=loaded_melody.meta_messages,
        )

        destination = Path(output_path) if output_path else self._default_output_path(melody_path, output_format)
        create_exporter(output_format).export(arrangement, str(destination))
        return destination

    @staticmethod
    def _default_output_path(melody_path: str, output_format: str) -> Path:
        suffix = ".mid" if output_format == "midi" else ".musicxml"
        return Path(melody_path).with_name(f"{Path(melody_path).stem}_choir{suffix}")

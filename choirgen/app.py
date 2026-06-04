from __future__ import annotations

from pathlib import Path
from random import Random

from choirgen.exporters.factory import create_exporter
from choirgen.generators.base import GenerationContext
from choirgen.generators.factory import create_strategy
from choirgen.harmony.analysis import infer_harmony
from choirgen.midi.reader import read_monophonic_midi
from choirgen.models.score import Arrangement
from choirgen.models.spec import VoiceSpec
from choirgen.parser.casl import CaslParser
from choirgen.phrases.detector import detect_phrase_profile
from choirgen.rules.engine import RuleEngine
from choirgen.rules.range import RangeRule


class ChoirGeneratorApp:
    def __init__(self, parser: CaslParser | None = None) -> None:
        self._parser = parser or CaslParser()
        self._rule_engine = RuleEngine([RangeRule()])

    def generate(
        self,
        melody_path: str,
        spec_path: str,
        output_path: str | None = None,
        output_format: str = "midi",
        expected_casl_version: str | None = None,
    ) -> Path:
        specification = self._parser.parse_file(spec_path)
        if expected_casl_version is not None and specification.casl_version != expected_casl_version:
            raise ValueError(
                f"CASL version mismatch: expected {expected_casl_version}, got {specification.casl_version}"
            )

        loaded_melody = read_monophonic_midi(melody_path)
        phrase = None
        if specification.analysis.phrase_detection or specification.phrases.detect:
            phrase = detect_phrase_profile(loaded_melody.part, loaded_melody.ticks_per_beat)

        harmony = None
        if specification.analysis.key_detection or specification.analysis.chord_inference or specification.harmony.mode:
            harmony = infer_harmony(loaded_melody.part)

        context = GenerationContext(
            specification=specification,
            random=Random(specification.randomization.seed),
            harmony=harmony,
            phrase=phrase,
        )

        parts = [loaded_melody.part.clone(name=specification.original_voice_name())]
        for voice in specification.generated_voices():
            strategy = create_strategy(self._resolve_strategy(voice, specification.casl_version))
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
    def _resolve_strategy(voice: VoiceSpec, casl_version: str) -> str:
        if voice.strategy is not None:
            return voice.strategy.type
        if casl_version == "2.0":
            return "harmonic_voice"
        raise ValueError(f"Generated voice '{voice.name}' is missing a strategy")

    @staticmethod
    def _default_output_path(melody_path: str, output_format: str) -> Path:
        suffix = ".mid" if output_format == "midi" else ".musicxml"
        return Path(melody_path).with_name(f"{Path(melody_path).stem}_choir{suffix}")

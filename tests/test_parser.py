from pathlib import Path

from choirgen.parser.casl import CaslParser


def test_parser_reads_extensible_casl_model_v1() -> None:
    parser = CaslParser()
    specification = parser.parse_file(Path("examples/example.casl"))

    assert specification.project.name == "Simple Alto Demo"
    assert specification.casl_version == "1.0"
    assert specification.melody.source == "input"
    assert specification.randomization.seed == 42
    assert specification.randomization.variation.note_choice_probability == 0.15
    assert specification.original_voice_name() == "melody"

    alto = specification.voices["alto"]
    assert alto.generate is True
    assert alto.range is not None
    assert alto.range.low == "G3"
    assert alto.range.high == "D5"
    assert alto.strategy is not None
    assert alto.strategy.type == "fixed_interval"
    assert alto.strategy.require_int("interval", "semitones") == -4


def test_parser_reads_casl_2_model() -> None:
    parser = CaslParser()
    specification = parser.parse_file(Path("examples/example_v2.casl"))

    assert specification.project.name == "Advanced SATB Demo"
    assert specification.casl_version == "2.0"
    assert specification.analysis.key_detection is True
    assert specification.analysis.chord_inference is True
    assert specification.analysis.phrase_detection is True
    assert specification.arrangement.type == "SATB"

    assert specification.harmony.mode == "functional"
    assert specification.harmony.roman_numerals.enabled is True
    assert specification.harmony.chord_preference.diatonic == 0.9
    assert specification.harmony.cadence_model.authentic == "strong"

    assert specification.original_voice_name() == "soprano"
    assert [voice.name for voice in specification.generated_voices()] == ["alto", "tenor", "bass"]
    assert specification.ranges["bass"].low == "E2"
    assert specification.rules["max_leap"].value == 7
    assert specification.rules["max_leap"].weight == 0.7
    assert specification.phrases.detect is True
    assert specification.randomization.voice_variation.enabled is True
    assert specification.randomization.voice_variation.intensity == 0.1
    assert specification.expression.shaping.phrase_decay is True
    assert [extension.name for extension in specification.extensions] == ["jazz_rules", "baroque_voice_leading"]

from pathlib import Path

from choirgen.parser.casl import CaslParser


def test_parser_reads_extensible_casl_model() -> None:
    parser = CaslParser()
    specification = parser.parse_file(Path("examples/example.casl"))

    assert specification.project.name == "Simple Alto Demo"
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

from pathlib import Path

from mido import Message, MidiFile, MidiTrack

from choirgen.app import ChoirGeneratorApp
from choirgen.harmony.analysis import infer_harmony
from choirgen.models.score import NoteEvent, Part
from choirgen.parser.casl import CaslParser


def _make_spec():
    return CaslParser().parse_file(Path("examples/example_v2.casl"))


def _write_input_midi(path: Path) -> None:
    midi = MidiFile(ticks_per_beat=480)
    melody_track = MidiTrack()
    midi.tracks.append(melody_track)
    melody_track.append(Message("note_on", note=72, velocity=90, time=0))
    melody_track.append(Message("note_off", note=72, velocity=0, time=480))
    melody_track.append(Message("note_on", note=74, velocity=90, time=0))
    melody_track.append(Message("note_off", note=74, velocity=0, time=480))
    melody_track.append(Message("note_on", note=76, velocity=90, time=0))
    melody_track.append(Message("note_off", note=76, velocity=0, time=480))
    melody_track.append(Message("note_on", note=77, velocity=90, time=0))
    melody_track.append(Message("note_off", note=77, velocity=0, time=480))
    midi.save(path)


def test_secondary_dominants_affect_selected_chords() -> None:
    spec = _make_spec()
    spec.harmony.chord_preference.diatonic = 0.9
    spec.harmony.chord_preference.secondary_dominants = 0.9
    melody = Part(
        name="melody",
        notes=[
            NoteEvent(pitch=60, start=0, end=480),
            NoteEvent(pitch=64, start=480, end=960),
            NoteEvent(pitch=67, start=960, end=1440),
            NoteEvent(pitch=66, start=1440, end=1920),
        ],
    )

    harmony = infer_harmony(melody, specification=spec, phrase=None)
    assert harmony.moments[-1].roman_numeral.startswith("V/")

    spec.harmony.chord_preference.secondary_dominants = 0.0
    harmony_without_secondary = infer_harmony(melody, specification=spec, phrase=None)
    assert not harmony_without_secondary.moments[-1].roman_numeral.startswith("V/")


def test_cadence_and_phrase_strength_influence_harmony_scoring() -> None:
    spec = _make_spec()
    spec.harmony.cadence_model.authentic = "strong"
    spec.harmony.cadence_model.plagal = "medium"
    spec.phrases.behavior.end.cadence_strength = "high"
    melody = Part(
        name="melody",
        notes=[
            NoteEvent(pitch=60, start=0, end=480),
        ],
    )

    harmony = infer_harmony(melody, specification=spec, phrase=None)
    last = harmony.moments[-1]
    assert last.score_breakdown["cadence_score"] > 1.0
    assert last.score_breakdown["phrase_score"] != 1.0


def test_app_explain_output_contains_required_sections(tmp_path: Path) -> None:
    input_midi = tmp_path / "melody.mid"
    output_midi = tmp_path / "arranged.mid"
    _write_input_midi(input_midi)

    app = ChoirGeneratorApp()
    app.generate(
        str(input_midi),
        "examples/example_v2.casl",
        str(output_midi),
        expected_casl_version="2.0",
        explain=True,
    )

    explanation = app.last_explanation
    assert explanation is not None
    assert explanation["detected_key"]
    assert explanation["detected_phrases"] is not None
    assert explanation["inferred_chords"]
    assert explanation["selected_chord_progression"]
    score_breakdown = explanation["score_breakdown"]
    assert score_breakdown["harmony"]
    assert "alto" in score_breakdown["voice_assignment"]

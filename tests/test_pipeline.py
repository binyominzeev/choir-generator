from pathlib import Path

from mido import Message, MidiFile, MidiTrack

from choirgen.app import ChoirGeneratorApp
from choirgen.models.score import note_name_to_midi


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


def _note_ons(track: MidiTrack) -> list[Message]:
    return [message for message in track if message.type == "note_on" and message.velocity > 0]


def test_generation_pipeline_writes_two_voice_midi(tmp_path: Path) -> None:
    input_midi = tmp_path / "melody.mid"
    output_midi = tmp_path / "arranged.mid"
    _write_input_midi(input_midi)

    app = ChoirGeneratorApp()
    result_path = app.generate(str(input_midi), "examples/example.casl", str(output_midi))

    assert result_path.exists()
    rendered = MidiFile(result_path)

    assert len(rendered.tracks) == 3
    melody_notes = [message.note for message in _note_ons(rendered.tracks[1])]
    alto_notes = [message.note for message in _note_ons(rendered.tracks[2])]

    assert melody_notes == [72, 74, 76, 77]
    assert alto_notes == [68, 70, 72, 73]


def test_generation_pipeline_writes_satb_midi(tmp_path: Path) -> None:
    input_midi = tmp_path / "melody.mid"
    output_midi = tmp_path / "arranged.mid"
    _write_input_midi(input_midi)

    app = ChoirGeneratorApp()
    result_path = app.generate(
        str(input_midi),
        "examples/example_v2.casl",
        str(output_midi),
        expected_casl_version="2.0",
    )

    assert result_path == output_midi
    assert output_midi.exists()

    rendered = MidiFile(output_midi)
    assert len(rendered.tracks) == 5

    soprano_notes = [message.note for message in _note_ons(rendered.tracks[1])]
    alto = _note_ons(rendered.tracks[2])
    tenor = _note_ons(rendered.tracks[3])
    bass = _note_ons(rendered.tracks[4])

    assert soprano_notes == [72, 74, 76, 77]
    assert len(alto) == len(tenor) == len(bass) == 4

    alto_low = note_name_to_midi("G3")
    alto_high = note_name_to_midi("D5")
    tenor_low = note_name_to_midi("C3")
    tenor_high = note_name_to_midi("G4")
    bass_low = note_name_to_midi("E2")
    bass_high = note_name_to_midi("C4")

    assert all(alto_low <= note.note <= alto_high for note in alto)
    assert all(tenor_low <= note.note <= tenor_high for note in tenor)
    assert all(bass_low <= note.note <= bass_high for note in bass)

    assert all(note.velocity > 0 for note in alto + tenor + bass)


def test_generation_rejects_version_mismatch(tmp_path: Path) -> None:
    input_midi = tmp_path / "melody.mid"
    _write_input_midi(input_midi)

    app = ChoirGeneratorApp()
    try:
        app.generate(str(input_midi), "examples/example_v2.casl", expected_casl_version="1.0")
    except ValueError as exc:
        assert "CASL version mismatch" in str(exc)
    else:
        raise AssertionError("Expected CASL version mismatch")

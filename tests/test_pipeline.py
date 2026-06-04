from pathlib import Path

from mido import Message, MidiFile, MidiTrack

from choirgen.app import ChoirGeneratorApp


def _write_input_midi(path: Path) -> None:
    midi = MidiFile(ticks_per_beat=480)
    melody_track = MidiTrack()
    midi.tracks.append(melody_track)
    melody_track.append(Message("note_on", note=72, velocity=90, time=0))
    melody_track.append(Message("note_off", note=72, velocity=0, time=480))
    melody_track.append(Message("note_on", note=74, velocity=90, time=0))
    melody_track.append(Message("note_off", note=74, velocity=0, time=480))
    midi.save(path)


def test_generation_pipeline_writes_two_voice_midi(tmp_path: Path) -> None:
    input_midi = tmp_path / "melody.mid"
    output_midi = tmp_path / "arranged.mid"
    _write_input_midi(input_midi)

    app = ChoirGeneratorApp()
    result_path = app.generate(str(input_midi), "examples/example.casl", str(output_midi))

    assert result_path == output_midi
    assert output_midi.exists()

    rendered = MidiFile(output_midi)
    assert len(rendered.tracks) == 3

    melody_notes = [message.note for message in rendered.tracks[1] if message.type == "note_on" and message.velocity > 0]
    alto_notes = [message.note for message in rendered.tracks[2] if message.type == "note_on" and message.velocity > 0]

    assert melody_notes == [72, 74]
    assert alto_notes == [68, 70]

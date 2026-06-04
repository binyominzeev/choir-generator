from __future__ import annotations

from mido import MidiFile

from choirgen.models.score import LoadedMelody, NoteEvent, Part

_ALLOWED_META_TYPES = {"set_tempo", "time_signature", "key_signature"}


def read_monophonic_midi(path: str) -> LoadedMelody:
    midi = MidiFile(path)
    active_notes: dict[int, tuple[int, int]] = {}
    notes: list[NoteEvent] = []
    meta_messages: list[tuple[int, object]] = []

    for track_index, track in enumerate(midi.tracks):
        absolute_time = 0
        for message in track:
            absolute_time += message.time
            if message.is_meta:
                if track_index == 0 and message.type in _ALLOWED_META_TYPES:
                    meta_messages.append((absolute_time, message.copy(time=0)))
                continue
            if message.type == "note_on" and message.velocity > 0:
                if active_notes:
                    raise ValueError("Input MIDI must be monophonic")
                active_notes[message.note] = (absolute_time, message.velocity)
                continue
            if message.type not in {"note_off", "note_on"}:
                continue
            note_state = active_notes.pop(message.note, None)
            if note_state is None:
                continue
            start_time, velocity = note_state
            if absolute_time > start_time:
                notes.append(
                    NoteEvent(
                        pitch=message.note,
                        start=start_time,
                        end=absolute_time,
                        velocity=velocity,
                    )
                )

    if active_notes:
        raise ValueError("Input MIDI contains notes without matching note-off events")
    if not notes:
        raise ValueError("Input MIDI does not contain any notes")

    notes.sort(key=lambda note: (note.start, note.pitch))
    return LoadedMelody(part=Part(name="melody", notes=notes), ticks_per_beat=midi.ticks_per_beat, meta_messages=meta_messages)

from __future__ import annotations

from mido import Message, MetaMessage, MidiFile, MidiTrack

from choirgen.models.score import Arrangement, Part


def _sorted_events(part: Part, channel: int) -> list[tuple[int, object]]:
    events: list[tuple[int, object]] = [
        (0, MetaMessage("track_name", name=part.name, time=0)),
        (0, Message("program_change", program=part.program, channel=channel, time=0)),
    ]
    for note in part.notes:
        events.append(
            (
                note.start,
                Message("note_on", note=note.pitch, velocity=max(1, note.velocity), channel=channel, time=0),
            )
        )
        events.append(
            (
                note.end,
                Message("note_off", note=note.pitch, velocity=0, channel=channel, time=0),
            )
        )
    return sorted(events, key=lambda item: (item[0], 0 if getattr(item[1], "type", "") == "note_off" else 1))


class MidiArrangementExporter:
    def export(self, arrangement: Arrangement, path: str) -> None:
        midi = MidiFile(ticks_per_beat=arrangement.ticks_per_beat)

        meta_track = MidiTrack()
        midi.tracks.append(meta_track)
        last_time = 0
        for absolute_time, message in sorted(arrangement.meta_messages, key=lambda item: item[0]):
            copied = message.copy(time=absolute_time - last_time)
            meta_track.append(copied)
            last_time = absolute_time
        meta_track.append(MetaMessage("end_of_track", time=0))

        for channel, part in enumerate(arrangement.parts):
            track = MidiTrack()
            midi.tracks.append(track)
            last_time = 0
            for absolute_time, message in _sorted_events(part, channel % 16):
                copied = message.copy(time=absolute_time - last_time)
                track.append(copied)
                last_time = absolute_time
            track.append(MetaMessage("end_of_track", time=0))

        midi.save(path)

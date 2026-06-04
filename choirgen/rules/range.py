from __future__ import annotations

from choirgen.models.score import fit_pitch_to_range, note_name_to_midi
from choirgen.models.score import Part
from choirgen.models.spec import VoiceSpec


class RangeRule:
    def apply(self, part: Part, melody: Part, voice: VoiceSpec) -> Part:
        if voice.range is None:
            return part
        low = note_name_to_midi(voice.range.low) if voice.range.low else None
        high = note_name_to_midi(voice.range.high) if voice.range.high else None
        notes = [
            note.__class__(
                pitch=fit_pitch_to_range(note.pitch, low, high),
                start=note.start,
                end=note.end,
                velocity=note.velocity,
            )
            for note in part.notes
        ]
        return part.clone(notes=notes)

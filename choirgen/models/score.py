from __future__ import annotations

from dataclasses import dataclass, field, replace
import re

NOTE_OFFSETS = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}
NOTE_NAME_RE = re.compile(r"^([A-Ga-g])([#b]?)(-?\d+)$")


@dataclass(slots=True)
class NoteEvent:
    pitch: int
    start: int
    end: int
    velocity: int = 64

    def transpose(self, semitones: int) -> "NoteEvent":
        return replace(self, pitch=self.pitch + semitones)


@dataclass(slots=True)
class Part:
    name: str
    notes: list[NoteEvent]
    program: int = 0

    def clone(self, *, name: str | None = None, notes: list[NoteEvent] | None = None) -> "Part":
        return Part(name=name or self.name, notes=notes or list(self.notes), program=self.program)


@dataclass(slots=True)
class LoadedMelody:
    part: Part
    ticks_per_beat: int
    meta_messages: list[tuple[int, object]] = field(default_factory=list)


@dataclass(slots=True)
class Arrangement:
    title: str
    parts: list[Part]
    ticks_per_beat: int = 480
    meta_messages: list[tuple[int, object]] = field(default_factory=list)


def note_name_to_midi(note_name: str) -> int:
    match = NOTE_NAME_RE.fullmatch(note_name.strip())
    if match is None:
        raise ValueError(f"Invalid note name: {note_name}")
    note, accidental, octave_text = match.groups()
    pitch_class = NOTE_OFFSETS[note.upper() + accidental]
    octave = int(octave_text)
    return (octave + 1) * 12 + pitch_class


def fit_pitch_to_range(pitch: int, low: int | None, high: int | None) -> int:
    if low is not None:
        while pitch < low:
            pitch += 12
    if high is not None:
        while pitch > high:
            pitch -= 12
    if low is not None and pitch < low:
        return low
    if high is not None and pitch > high:
        return high
    return pitch

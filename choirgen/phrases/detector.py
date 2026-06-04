from __future__ import annotations

from dataclasses import dataclass

from choirgen.models.score import Part


@dataclass(slots=True)
class PhraseProfile:
    start_index: int
    climax_index: int
    end_index: int


def detect_phrase_profile(melody: Part, ticks_per_beat: int) -> PhraseProfile:
    if not melody.notes:
        return PhraseProfile(start_index=0, climax_index=0, end_index=0)

    end_index = len(melody.notes) - 1
    climax_index = max(range(len(melody.notes)), key=lambda idx: melody.notes[idx].pitch)

    for index in range(1, len(melody.notes)):
        gap = melody.notes[index].start - melody.notes[index - 1].end
        if gap >= ticks_per_beat:
            end_index = index - 1
            break

    if climax_index > end_index:
        climax_index = end_index

    return PhraseProfile(start_index=0, climax_index=climax_index, end_index=end_index)

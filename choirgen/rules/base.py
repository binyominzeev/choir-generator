from __future__ import annotations

from typing import Protocol

from choirgen.models.score import Part
from choirgen.models.spec import VoiceSpec


class VoiceRule(Protocol):
    def apply(self, part: Part, melody: Part, voice: VoiceSpec) -> Part:
        ...

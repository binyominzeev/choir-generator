from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProjectSpec:
    name: str = "Untitled Project"


@dataclass(slots=True)
class MelodySpec:
    source: str = "input"


@dataclass(slots=True)
class RangeSpec:
    low: str | None = None
    high: str | None = None


@dataclass(slots=True)
class StrategySpec:
    type: str
    config: dict[str, Any] = field(default_factory=dict)

    def require_int(self, *path: str) -> int:
        value: Any = self.config
        for key in path:
            if not isinstance(value, dict) or key not in value:
                joined = ".".join(path)
                raise ValueError(f"Missing strategy configuration value: {joined}")
            value = value[key]
        if not isinstance(value, int):
            joined = ".".join(path)
            raise ValueError(f"Strategy configuration value must be an integer: {joined}")
        return value


@dataclass(slots=True)
class VoiceSpec:
    name: str
    source: str | None = None
    generate: bool = False
    range: RangeSpec | None = None
    strategy: StrategySpec | None = None
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VariationSpec:
    note_choice_probability: float = 0.0


@dataclass(slots=True)
class RandomizationSpec:
    seed: int | None = None
    variation: VariationSpec = field(default_factory=VariationSpec)


@dataclass(slots=True)
class ArrangementSpec:
    project: ProjectSpec = field(default_factory=ProjectSpec)
    melody: MelodySpec = field(default_factory=MelodySpec)
    voices: dict[str, VoiceSpec] = field(default_factory=dict)
    randomization: RandomizationSpec = field(default_factory=RandomizationSpec)

    def original_voice_name(self) -> str:
        for voice in self.voices.values():
            if voice.source == "original":
                return voice.name
        return "melody"

    def generated_voices(self) -> list[VoiceSpec]:
        return [voice for voice in self.voices.values() if voice.generate]

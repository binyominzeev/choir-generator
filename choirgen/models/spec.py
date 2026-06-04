from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProjectSpec:
    name: str = "Untitled Project"
    version: str = "1.0"


@dataclass(slots=True)
class MelodySpec:
    source: str = "input"
    file: str | None = None


@dataclass(slots=True)
class AnalysisSpec:
    key_detection: bool = False
    chord_inference: bool = False
    phrase_detection: bool = False


@dataclass(slots=True)
class ArrangementTypeSpec:
    type: str = "custom"


@dataclass(slots=True)
class HarmonyRomanNumeralsSpec:
    enabled: bool = False


@dataclass(slots=True)
class HarmonyChordPreferenceSpec:
    diatonic: float = 1.0
    secondary_dominants: float = 0.0


@dataclass(slots=True)
class HarmonyCadenceModelSpec:
    authentic: str | None = None
    plagal: str | None = None


@dataclass(slots=True)
class HarmonySpec:
    mode: str | None = None
    roman_numerals: HarmonyRomanNumeralsSpec = field(default_factory=HarmonyRomanNumeralsSpec)
    chord_preference: HarmonyChordPreferenceSpec = field(default_factory=HarmonyChordPreferenceSpec)
    cadence_model: HarmonyCadenceModelSpec = field(default_factory=HarmonyCadenceModelSpec)


@dataclass(slots=True)
class RangeSpec:
    low: str | None = None
    high: str | None = None
    strict: bool = False


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
class VoicePrioritySpec:
    melody: float | None = None
    chord_tones: float | None = None
    passing_tones: float | None = None
    root_motion: float | None = None


@dataclass(slots=True)
class VoiceSpec:
    name: str
    role: str | None = None
    source: str | None = None
    generate: bool = False
    range: RangeSpec | None = None
    strategy: StrategySpec | None = None
    priority: VoicePrioritySpec = field(default_factory=VoicePrioritySpec)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VariationSpec:
    note_choice_probability: float = 0.0


@dataclass(slots=True)
class RandomizationVariationSpec:
    enabled: bool = False
    intensity: float = 0.0


@dataclass(slots=True)
class RandomizationSpec:
    seed: int | None = None
    variation: VariationSpec = field(default_factory=VariationSpec)
    voice_variation: RandomizationVariationSpec = field(default_factory=RandomizationVariationSpec)
    rhythm_variation: RandomizationVariationSpec = field(default_factory=RandomizationVariationSpec)


@dataclass(slots=True)
class VoiceLeadingForbidSpec:
    parallel_fifths: bool = False
    parallel_octaves: bool = False
    voice_crossing: bool = False


@dataclass(slots=True)
class VoiceLeadingPreferSpec:
    stepwise_motion: str | None = None
    common_tone_retention: str | None = None
    small_leaps: str | None = None


@dataclass(slots=True)
class VoiceLeadingSpec:
    forbid: VoiceLeadingForbidSpec = field(default_factory=VoiceLeadingForbidSpec)
    prefer: VoiceLeadingPreferSpec = field(default_factory=VoiceLeadingPreferSpec)


@dataclass(slots=True)
class WeightedRuleSpec:
    value: int | float | str | bool | None = None
    weight: float | None = None


@dataclass(slots=True)
class PhraseRegionSpec:
    dynamics: str | None = None
    cadence_strength: str | None = None


@dataclass(slots=True)
class PhraseBehaviorSpec:
    start: PhraseRegionSpec = field(default_factory=PhraseRegionSpec)
    climax: PhraseRegionSpec = field(default_factory=PhraseRegionSpec)
    end: PhraseRegionSpec = field(default_factory=PhraseRegionSpec)


@dataclass(slots=True)
class PhrasesSpec:
    detect: bool = False
    behavior: PhraseBehaviorSpec = field(default_factory=PhraseBehaviorSpec)


@dataclass(slots=True)
class ExpressionDynamicsSpec:
    enabled: bool = False
    base: str | None = None


@dataclass(slots=True)
class ExpressionShapingSpec:
    crescendo_towards_climax: bool = False
    phrase_decay: bool = False


@dataclass(slots=True)
class ExpressionSpec:
    dynamics: ExpressionDynamicsSpec = field(default_factory=ExpressionDynamicsSpec)
    shaping: ExpressionShapingSpec = field(default_factory=ExpressionShapingSpec)


@dataclass(slots=True)
class ExtensionSpec:
    name: str


@dataclass(slots=True)
class ArrangementSpec:
    project: ProjectSpec = field(default_factory=ProjectSpec)
    melody: MelodySpec = field(default_factory=MelodySpec)
    analysis: AnalysisSpec = field(default_factory=AnalysisSpec)
    arrangement: ArrangementTypeSpec = field(default_factory=ArrangementTypeSpec)
    harmony: HarmonySpec = field(default_factory=HarmonySpec)
    voices: dict[str, VoiceSpec] = field(default_factory=dict)
    ranges: dict[str, RangeSpec] = field(default_factory=dict)
    randomization: RandomizationSpec = field(default_factory=RandomizationSpec)
    voice_leading: VoiceLeadingSpec = field(default_factory=VoiceLeadingSpec)
    rules: dict[str, WeightedRuleSpec] = field(default_factory=dict)
    phrases: PhrasesSpec = field(default_factory=PhrasesSpec)
    expression: ExpressionSpec = field(default_factory=ExpressionSpec)
    extensions: list[ExtensionSpec] = field(default_factory=list)

    @property
    def casl_version(self) -> str:
        return self.project.version or "1.0"

    def original_voice_name(self) -> str:
        for voice in self.voices.values():
            if voice.source == "original":
                return voice.name
        for voice in self.voices.values():
            if voice.role == "melody":
                return voice.name
        return "melody"

    def generated_voices(self) -> list[VoiceSpec]:
        return [
            voice
            for voice in self.voices.values()
            if voice.generate or voice.role == "generated"
        ]

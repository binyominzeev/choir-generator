from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from choirgen.models.spec import (
    AnalysisSpec,
    ArrangementSpec,
    ArrangementTypeSpec,
    ExpressionDynamicsSpec,
    ExpressionShapingSpec,
    ExpressionSpec,
    ExtensionSpec,
    HarmonyCadenceModelSpec,
    HarmonyChordPreferenceSpec,
    HarmonyRomanNumeralsSpec,
    HarmonySpec,
    MelodySpec,
    PhraseBehaviorSpec,
    PhraseRegionSpec,
    PhrasesSpec,
    ProjectSpec,
    RandomizationSpec,
    RandomizationVariationSpec,
    RangeSpec,
    StrategySpec,
    VariationSpec,
    VoiceLeadingForbidSpec,
    VoiceLeadingPreferSpec,
    VoiceLeadingSpec,
    VoicePrioritySpec,
    VoiceSpec,
    WeightedRuleSpec,
)


class CaslParser:
    def parse_file(self, path: str | Path) -> ArrangementSpec:
        with Path(path).open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return self.parse_data(data)

    def parse_data(self, data: dict[str, Any]) -> ArrangementSpec:
        if not isinstance(data, dict):
            raise ValueError("CASL root must be a mapping")

        project_data = self._mapping(data.get("project"))
        melody_data = self._mapping(data.get("melody"))
        analysis_data = self._mapping(data.get("analysis"))
        arrangement_data = self._mapping(data.get("arrangement"))
        harmony_data = self._mapping(data.get("harmony"))
        randomization_data = self._mapping(data.get("randomization"))
        voices_data = data.get("voices") or {}
        ranges_data = data.get("ranges") or {}
        voice_leading_data = self._mapping(data.get("voice_leading"))
        rules_data = data.get("rules") or {}
        phrases_data = self._mapping(data.get("phrases"))
        expression_data = self._mapping(data.get("expression"))

        if not isinstance(voices_data, dict):
            raise ValueError("CASL voices section must be a mapping")
        if not isinstance(ranges_data, dict):
            raise ValueError("CASL ranges section must be a mapping")
        if not isinstance(rules_data, dict):
            raise ValueError("CASL rules section must be a mapping")

        global_ranges = {
            name: self._parse_range(value, section=f"ranges.{name}")
            for name, value in ranges_data.items()
        }

        voice_assignment = self._mapping(data.get("voice_assignment"))
        voices = {
            name: self._parse_voice(
                name,
                voice_data,
                global_ranges.get(name),
                self._mapping(voice_assignment.get(name)).get("priority") if voice_assignment else None,
            )
            for name, voice_data in voices_data.items()
        }

        harmony_roman_data = self._mapping(harmony_data.get("roman_numerals"))
        harmony_chord_preference_data = self._mapping(harmony_data.get("chord_preference"))
        harmony_cadence_model_data = self._mapping(harmony_data.get("cadence_model"))

        variation_data = self._mapping(randomization_data.get("variation"))
        voice_variation_data = self._mapping(randomization_data.get("voice_variation"))
        rhythm_variation_data = self._mapping(randomization_data.get("rhythm_variation"))

        voice_leading_forbid = self._mapping(voice_leading_data.get("forbid"))
        voice_leading_prefer = self._mapping(voice_leading_data.get("prefer"))

        phrase_behavior = self._mapping(phrases_data.get("behavior"))

        expression_dynamics_data = self._mapping(expression_data.get("dynamics"))
        expression_shaping_data = self._mapping(expression_data.get("shaping"))

        return ArrangementSpec(
            project=ProjectSpec(
                name=project_data.get("name", "Untitled Project"),
                version=str(project_data.get("version", "1.0")),
            ),
            melody=MelodySpec(
                source=melody_data.get("source", "input"),
                file=melody_data.get("file"),
            ),
            analysis=AnalysisSpec(
                key_detection=bool(analysis_data.get("key_detection", False)),
                chord_inference=bool(analysis_data.get("chord_inference", False)),
                phrase_detection=bool(analysis_data.get("phrase_detection", False)),
            ),
            arrangement=ArrangementTypeSpec(
                type=str(arrangement_data.get("type", "custom")),
            ),
            harmony=HarmonySpec(
                mode=harmony_data.get("mode"),
                roman_numerals=HarmonyRomanNumeralsSpec(
                    enabled=bool(harmony_roman_data.get("enabled", False)),
                ),
                chord_preference=HarmonyChordPreferenceSpec(
                    diatonic=float(harmony_chord_preference_data.get("diatonic", 1.0)),
                    secondary_dominants=float(harmony_chord_preference_data.get("secondary_dominants", 0.0)),
                ),
                cadence_model=HarmonyCadenceModelSpec(
                    authentic=harmony_cadence_model_data.get("authentic"),
                    plagal=harmony_cadence_model_data.get("plagal"),
                ),
            ),
            voices=voices,
            ranges=global_ranges,
            randomization=RandomizationSpec(
                seed=randomization_data.get("seed"),
                variation=VariationSpec(
                    note_choice_probability=float(variation_data.get("note_choice_probability", 0.0)),
                ),
                voice_variation=RandomizationVariationSpec(
                    enabled=bool(voice_variation_data.get("enabled", False)),
                    intensity=float(voice_variation_data.get("intensity", variation_data.get("note_choice_probability", 0.0))),
                ),
                rhythm_variation=RandomizationVariationSpec(
                    enabled=bool(rhythm_variation_data.get("enabled", False)),
                    intensity=float(rhythm_variation_data.get("intensity", 0.0)),
                ),
            ),
            voice_leading=VoiceLeadingSpec(
                forbid=VoiceLeadingForbidSpec(
                    parallel_fifths=bool(voice_leading_forbid.get("parallel_fifths", False)),
                    parallel_octaves=bool(voice_leading_forbid.get("parallel_octaves", False)),
                    voice_crossing=bool(voice_leading_forbid.get("voice_crossing", False)),
                ),
                prefer=VoiceLeadingPreferSpec(
                    stepwise_motion=voice_leading_prefer.get("stepwise_motion"),
                    common_tone_retention=voice_leading_prefer.get("common_tone_retention"),
                    small_leaps=voice_leading_prefer.get("small_leaps"),
                ),
            ),
            rules={name: self._parse_weighted_rule(name, value) for name, value in rules_data.items()},
            phrases=PhrasesSpec(
                detect=bool(phrases_data.get("detect", False)),
                behavior=PhraseBehaviorSpec(
                    start=self._parse_phrase_region(phrase_behavior.get("start")),
                    climax=self._parse_phrase_region(phrase_behavior.get("climax")),
                    end=self._parse_phrase_region(phrase_behavior.get("end")),
                ),
            ),
            expression=ExpressionSpec(
                dynamics=ExpressionDynamicsSpec(
                    enabled=bool(expression_dynamics_data.get("enabled", False)),
                    base=expression_dynamics_data.get("base"),
                ),
                shaping=ExpressionShapingSpec(
                    crescendo_towards_climax=bool(expression_shaping_data.get("crescendo_towards_climax", False)),
                    phrase_decay=bool(expression_shaping_data.get("phrase_decay", False)),
                ),
            ),
            extensions=self._parse_extensions(data.get("extensions") or []),
        )

    @staticmethod
    def _mapping(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _parse_voice(self, name: str, voice_data: Any, default_range: RangeSpec | None, priority_data: Any) -> VoiceSpec:
        if not isinstance(voice_data, dict):
            raise ValueError(f"Voice '{name}' must be a mapping")

        strategy_data = voice_data.get("strategy")
        strategy = None
        if strategy_data is not None:
            if not isinstance(strategy_data, dict) or "type" not in strategy_data:
                raise ValueError(f"Voice '{name}' strategy must be a mapping with a type")
            strategy = StrategySpec(
                type=strategy_data["type"],
                config={key: value for key, value in strategy_data.items() if key != "type"},
            )

        range_spec = self._parse_range(voice_data.get("range"), section=f"voices.{name}.range") or default_range
        role = voice_data.get("role")
        generate = bool(voice_data.get("generate", role == "generated"))

        return VoiceSpec(
            name=name,
            role=role,
            source=voice_data.get("source"),
            generate=generate,
            range=range_spec,
            strategy=strategy,
            priority=self._parse_priority(priority_data),
            config={
                key: value
                for key, value in voice_data.items()
                if key not in {"role", "source", "generate", "range", "strategy"}
            },
        )

    def _parse_range(self, range_data: Any, section: str) -> RangeSpec | None:
        if range_data is None:
            return None
        if isinstance(range_data, list) and len(range_data) == 2:
            return RangeSpec(low=str(range_data[0]), high=str(range_data[1]))
        if isinstance(range_data, dict):
            return RangeSpec(
                low=range_data.get("low"),
                high=range_data.get("high"),
                strict=bool(range_data.get("strict", False)),
            )
        raise ValueError(f"{section} must be [low, high] or mapping")

    @staticmethod
    def _parse_priority(priority_data: Any) -> VoicePrioritySpec:
        if not isinstance(priority_data, dict):
            return VoicePrioritySpec()
        return VoicePrioritySpec(
            melody=_as_float_or_none(priority_data.get("melody")),
            chord_tones=_as_float_or_none(priority_data.get("chord_tones")),
            passing_tones=_as_float_or_none(priority_data.get("passing_tones")),
            root_motion=_as_float_or_none(priority_data.get("root_motion")),
        )

    @staticmethod
    def _parse_weighted_rule(name: str, data: Any) -> WeightedRuleSpec:
        if not isinstance(data, dict):
            return WeightedRuleSpec(value=data, weight=None)
        return WeightedRuleSpec(
            value=data.get("value"),
            weight=float(data["weight"]) if "weight" in data and data["weight"] is not None else None,
        )

    @staticmethod
    def _parse_phrase_region(region_data: Any) -> PhraseRegionSpec:
        if not isinstance(region_data, dict):
            return PhraseRegionSpec()
        return PhraseRegionSpec(
            dynamics=region_data.get("dynamics"),
            cadence_strength=region_data.get("cadence_strength"),
        )

    @staticmethod
    def _parse_extensions(extensions_data: Any) -> list[ExtensionSpec]:
        if not isinstance(extensions_data, list):
            return []
        parsed: list[ExtensionSpec] = []
        for item in extensions_data:
            if isinstance(item, str):
                parsed.append(ExtensionSpec(name=item))
                continue
            if isinstance(item, dict) and "name" in item:
                parsed.append(ExtensionSpec(name=str(item["name"])))
        return parsed


def _as_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)

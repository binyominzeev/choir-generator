from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from choirgen.models.spec import (
    ArrangementSpec,
    MelodySpec,
    ProjectSpec,
    RandomizationSpec,
    RangeSpec,
    StrategySpec,
    VariationSpec,
    VoiceSpec,
)


class CaslParser:
    def parse_file(self, path: str | Path) -> ArrangementSpec:
        with Path(path).open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return self.parse_data(data)

    def parse_data(self, data: dict[str, Any]) -> ArrangementSpec:
        if not isinstance(data, dict):
            raise ValueError("CASL root must be a mapping")

        project_data = data.get("project") or {}
        melody_data = data.get("melody") or {}
        randomization_data = data.get("randomization") or {}
        voices_data = data.get("voices") or {}

        if not isinstance(voices_data, dict):
            raise ValueError("CASL voices section must be a mapping")

        voices = {
            name: self._parse_voice(name, voice_data)
            for name, voice_data in voices_data.items()
        }

        return ArrangementSpec(
            project=ProjectSpec(name=project_data.get("name", "Untitled Project")),
            melody=MelodySpec(source=melody_data.get("source", "input")),
            voices=voices,
            randomization=RandomizationSpec(
                seed=randomization_data.get("seed"),
                variation=VariationSpec(
                    note_choice_probability=float(
                        (randomization_data.get("variation") or {}).get(
                            "note_choice_probability",
                            0.0,
                        )
                    ),
                ),
            ),
        )

    def _parse_voice(self, name: str, voice_data: Any) -> VoiceSpec:
        if not isinstance(voice_data, dict):
            raise ValueError(f"Voice '{name}' must be a mapping")

        range_data = voice_data.get("range") or {}
        strategy_data = voice_data.get("strategy")
        strategy = None
        if strategy_data is not None:
            if not isinstance(strategy_data, dict) or "type" not in strategy_data:
                raise ValueError(f"Voice '{name}' strategy must be a mapping with a type")
            strategy = StrategySpec(
                type=strategy_data["type"],
                config={key: value for key, value in strategy_data.items() if key != "type"},
            )

        return VoiceSpec(
            name=name,
            source=voice_data.get("source"),
            generate=bool(voice_data.get("generate", False)),
            range=RangeSpec(low=range_data.get("low"), high=range_data.get("high")) if range_data else None,
            strategy=strategy,
            config={
                key: value
                for key, value in voice_data.items()
                if key not in {"source", "generate", "range", "strategy"}
            },
        )

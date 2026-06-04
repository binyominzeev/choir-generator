from __future__ import annotations

from choirgen.generators.base import GenerationStrategy
from choirgen.generators.fixed_interval import FixedIntervalStrategy
from choirgen.generators.harmonic_voice import HarmonicVoiceStrategy


def create_strategy(strategy_type: str) -> GenerationStrategy:
    if strategy_type == "fixed_interval":
        return FixedIntervalStrategy()
    if strategy_type == "harmonic_voice":
        return HarmonicVoiceStrategy()
    raise ValueError(f"Unsupported generation strategy: {strategy_type}")

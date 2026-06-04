from __future__ import annotations

from typing import Protocol

from choirgen.models.score import Arrangement


class ArrangementExporter(Protocol):
    def export(self, arrangement: Arrangement, path: str) -> None:
        ...

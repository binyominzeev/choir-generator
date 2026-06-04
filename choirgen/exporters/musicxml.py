from __future__ import annotations

from choirgen.models.score import Arrangement


class MusicXmlArrangementExporter:
    def export(self, arrangement: Arrangement, path: str) -> None:
        raise NotImplementedError("MusicXML export is not implemented yet, but the exporter interface is ready for future work")

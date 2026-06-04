from __future__ import annotations

from choirgen.exporters.base import ArrangementExporter
from choirgen.exporters.midi import MidiArrangementExporter
from choirgen.exporters.musicxml import MusicXmlArrangementExporter


def create_exporter(output_format: str) -> ArrangementExporter:
    if output_format == "midi":
        return MidiArrangementExporter()
    if output_format == "musicxml":
        return MusicXmlArrangementExporter()
    raise ValueError(f"Unsupported output format: {output_format}")

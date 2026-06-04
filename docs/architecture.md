# Architecture

## System architecture

The prototype is organized around a small clean-architecture pipeline:

1. `choirgen.cli` parses command-line arguments.
2. `choirgen.parser.casl` loads the YAML-based CASL document into typed specification models.
3. `choirgen.midi.reader` loads a monophonic MIDI melody into internal note models.
4. `choirgen.generators` selects a strategy implementation for each generated voice.
5. `choirgen.rules.engine` applies post-generation rules such as range handling.
6. `choirgen.exporters` writes the final arrangement to MIDI and reserves a future MusicXML extension point.

## Module responsibilities

- `choirgen.models.spec`: typed CASL configuration objects.
- `choirgen.models.score`: internal note, part, arrangement, and pitch helpers.
- `choirgen.parser`: CASL parsing and validation.
- `choirgen.generators`: voice-generation strategies and factory selection.
- `choirgen.rules`: a rule-engine layer designed for future voice-leading constraints.
- `choirgen.midi`: MIDI import logic.
- `choirgen.exporters`: output adapters for MIDI and future MusicXML support.
- `choirgen.app`: orchestration service for the full pipeline.

## Processing pipeline

The current prototype reads one melody, keeps the original line as the source voice, generates one or more new voices from strategy definitions, applies rule-engine passes, and exports the combined arrangement. The separation between parser, strategies, rules, and exporters is intended to let future work add richer CASL syntax, many more rules, and multiple output backends without redesigning the core flow.

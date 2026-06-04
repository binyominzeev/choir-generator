# Architecture

## System architecture

The generator uses a layered pipeline aligned with CASL 2.0:

1. `choirgen.cli` parses command-line arguments and optional CASL version checks.
2. `choirgen.parser.casl` loads CASL 1.0/2.0 YAML into typed specification models.
3. `choirgen.midi.reader` loads a monophonic melody into internal note models.
4. `choirgen.harmony.analysis` infers key and per-note harmonic context.
5. `choirgen.phrases.detector` finds phrase shape points (start/climax/end).
6. `choirgen.generators` builds generated parts using strategy implementations (`fixed_interval` and harmony-aware generation).
7. `choirgen.rules.engine` applies post-generation rules and exposes weighted rule access.
8. `choirgen.exporters` writes final arrangements to MIDI (MusicXML stub retained for future work).

## Module responsibilities

- `choirgen.models.spec`: typed CASL configuration objects for both versions.
- `choirgen.models.score`: internal note/part/arrangement and pitch helpers.
- `choirgen.parser`: CASL parsing and validation.
- `choirgen.harmony`: harmonic abstraction and chord inference per melody note.
- `choirgen.phrases`: phrase detection profiles used by expression shaping.
- `choirgen.generators`: voice-generation strategies and factory resolution.
- `choirgen.rules`: deterministic post-rules plus weighted-constraint access helpers.
- `choirgen.midi`: MIDI import logic.
- `choirgen.exporters`: output adapters.
- `choirgen.app`: orchestration of the full CASL execution pipeline.

## Processing pipeline details

CASL 2.0 generated voices are harmony-driven by default, not fixed intervals. Candidate notes are chosen from inferred chord tones and scored by weighted constraints (stepwise preference, leap limits, common-tone retention, and hard forbids such as crossing/parallels). Phrase-aware expression shaping adjusts velocities toward climax and decay based on specification behavior.

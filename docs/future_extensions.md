# Future Extensions

CASL 2.0 is now implemented as a harmony-aware, SATB-ready baseline. The following remain natural next steps.

## Multi-phrase form handling

The current phrase detector identifies one phrase profile (start/climax/end). Future work can segment full pieces into multiple phrases and apply cadence/dynamics behavior per segment.

## Richer harmonic reasoning

The harmonic model is functional and diatonic-first. Extensions can add secondary dominants, modal interchange, and style-specific reinterpretation modules.

## Global SATB spacing constraints

Current hard constraints focus on voice crossing/parallels against melody context. Future optimization can evaluate all generated voices together (spacing, doublings, unresolved tendency tones).

## MusicXML expression export

Expression shaping currently affects MIDI velocities. Future work can serialize explicit dynamics, phrase marks, articulations, and slurs to MusicXML.

## Extension loading runtime

CASL already accepts extension declarations by name. Future work can wire these names to plugin loading so extension packages can contribute new rules and weighting profiles at runtime.

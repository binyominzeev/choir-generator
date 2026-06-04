# CASL Language

## Philosophy

CASL is treated as a first-class choir-arrangement DSL rather than a temporary settings file. The initial syntax is YAML so the prototype stays easy to read while still mapping cleanly to structured internal models.

## Current syntax

```yaml
project:
  name: Simple Alto Demo

melody:
  source: input

randomization:
  seed: 42
  variation:
    note_choice_probability: 0.15

voices:
  melody:
    source: original

  alto:
    generate: true
    range:
      low: G3
      high: D5
    strategy:
      type: fixed_interval
      interval:
        semitones: -4
```

## Extension strategy

Each voice strategy stores a `type` plus arbitrary strategy-specific configuration. Unknown strategy types can therefore be added by registering a new generator without redesigning the language shape. The same pattern can be extended to future sections such as harmony rules, style libraries, phrase shaping, dynamics, articulation, SATB templates, or AI-assisted controls.

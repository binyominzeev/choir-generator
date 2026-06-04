# choir-generator

A Python command-line prototype for generating polyphonic choir voices from a monophonic MIDI melody using a YAML-based Choir Arrangement Specification Language (CASL).

## Installation

```bash
python -m pip install .
```

For development:

```bash
python -m pip install -e '.[dev]'
```

## Usage

CASL 1.0 (fixed-interval strategy):

```bash
python -m choirgen.cli melody.mid examples/example.casl
```

CASL 2.0 SATB (harmonic strategy + phrase shaping):

```bash
python -m choirgen.cli melody.mid examples/example_v2.casl --casl-version 2.0
```

By default, output is MIDI next to the melody file. Use `--format musicxml` for future compatibility (MusicXML export is still a stub).

> Note: `choirgen` is a console entry point installed by the package.

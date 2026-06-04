# choir-generator

A Python command-line prototype for generating additional choir voices from a monophonic MIDI melody using a YAML-based Choir Arrangement Specification Language (CASL).

## Installation

Install the project and its dependencies with:

```bash
python -m pip install .
```

For development, you can install it in editable mode:

```bash
python -m pip install -e .
```

## Usage

After installation, run:

```bash
python -m choirgen.cli melody.mid examples/example.casl
```

This command writes a two-voice MIDI file next to the input melody by default.

> Note: `choirgen` is a command-line entry point installed by the package. It is not a standalone file in the repository root.

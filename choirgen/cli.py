from __future__ import annotations

import argparse
from pathlib import Path

from choirgen.app import ChoirGeneratorApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate additional choir voices from a monophonic MIDI melody")
    parser.add_argument("melody", help="Path to the monophonic input MIDI file")
    parser.add_argument("specification", help="Path to the CASL YAML specification file")
    parser.add_argument("-o", "--output", help="Path for the generated output file")
    parser.add_argument("--format", choices=["midi", "musicxml"], default="midi", help="Output format")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = ChoirGeneratorApp()
    output_path = app.generate(args.melody, args.specification, args.output, args.format)
    print(Path(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

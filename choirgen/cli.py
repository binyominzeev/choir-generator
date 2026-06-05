from __future__ import annotations

import argparse
import json
from pathlib import Path

from choirgen.app import ChoirGeneratorApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate additional choir voices from a monophonic MIDI melody")
    parser.add_argument("melody", help="Path to the monophonic input MIDI file")
    parser.add_argument("specification", help="Path to the CASL YAML specification file")
    parser.add_argument("-o", "--output", help="Path for the generated output file")
    parser.add_argument("--format", choices=["midi", "musicxml"], default="midi", help="Output format")
    parser.add_argument("--casl-version", choices=["1.0", "2.0"], help="Require a specific CASL version")
    parser.add_argument("--explain", action="store_true", help="Print harmonization analysis and score breakdown")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = ChoirGeneratorApp()
    output_path = app.generate(
        args.melody,
        args.specification,
        args.output,
        args.format,
        expected_casl_version=args.casl_version,
        explain=args.explain,
    )
    if args.explain and app.last_explanation is not None:
        print(json.dumps(app.last_explanation, indent=2, sort_keys=True))
    print(Path(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

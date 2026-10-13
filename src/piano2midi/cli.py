
"""Command-line interface for batch piano transcription."""

import argparse
from pathlib import Path

from piano2midi.transcription.transkun_backend import (
    TranskunError,
    transcribe,
)

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg"}


def parse_args():
    parser = argparse.ArgumentParser(
        prog="piano2midi",
        description="Transcribe piano audio to MIDI using Transkun.",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Audio files to transcribe.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Process supported audio files in this directory.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Include audio files in subdirectories.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("transcriptions"),
        help="Output directory (default: ./transcriptions).",
    )
    parser.add_argument(
        "--device",
        choices=("cuda", "cpu"),
        default="cuda",
        help="Inference device (default: cuda).",
    )
    parser.add_argument(
        "--transkun-executable",
        type=Path,
        help="Path to the Transkun executable in its own environment.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing MIDI outputs.",
    )
    return parser.parse_args()


def collect_inputs(args):
    files = [Path(item).expanduser() for item in args.inputs]

    if args.input_dir:
        directory = args.input_dir.expanduser()
        if not directory.is_dir():
            raise ValueError(f"Input directory not found: {directory}")

        iterator = directory.rglob("*") if args.recursive else directory.iterdir()
        files.extend(
            path for path in iterator
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    # Deduplicate paths while preserving order.
    unique_files = []
    seen = set()
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_files.append(resolved)

    if not unique_files:
        raise ValueError(
            "No input files found. Supply audio paths or use --input-dir."
        )

    return unique_files


def main():
    args = parse_args()

    try:
        inputs = collect_inputs(args)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)

    succeeded = 0
    skipped = 0
    failed = 0
    total = len(inputs)

    for index, audio in enumerate(inputs, start=1):
        print(f"\n[{index}/{total}] {audio.name}")

        if not audio.is_file():
            print(f"  FAILED: input file not found: {audio}")
            failed += 1
            continue

        if audio.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"  FAILED: unsupported audio format: {audio.suffix}")
            failed += 1
            continue

        output = args.output_dir / f"{audio.stem}.mid"

        if output.exists() and not args.overwrite:
            print(f"  SKIPPED: output already exists: {output}")
            skipped += 1
            continue

        try:
            result = transcribe(
                audio,
                output,
                device=args.device,
                executable=args.transkun_executable,
            )
            print(f"  OK: {result}")
            succeeded += 1
        except (TranskunError, OSError, ValueError) as exc:
            print(f"  FAILED: {exc}")
            failed += 1

    print("\n--- Batch summary ---")
    print(f"Total:     {total}")
    print(f"Succeeded: {succeeded}")
    print(f"Skipped:   {skipped}")
    print(f"Failed:    {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

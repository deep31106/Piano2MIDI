
"""Command-line interface for batch piano transcription."""

import argparse
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from piano2midi.transcription.transkun_backend import (
    TranskunError,
    transcribe,
)

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}
SUPPORTED_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


def parse_args():
    parser = argparse.ArgumentParser(
        prog="piano2midi",
        description="Transcribe piano audio or video to MIDI using Transkun.",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Audio or video files to transcribe.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Process supported files in this directory.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Include files in subdirectories when using --input-dir.",
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


@contextmanager
def prepare_audio(input_path: Path):
    """Yield an audio file, extracting audio from video when necessary."""
    if input_path.suffix.lower() not in VIDEO_EXTENSIONS:
        yield input_path
        return

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise ValueError(
            "FFmpeg was not found. Install FFmpeg and add it to PATH "
            "to transcribe video files."
        )

    with tempfile.TemporaryDirectory(prefix="piano2midi_") as temp_dir:
        extracted_audio = Path(temp_dir) / "extracted.wav"

        command = [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            str(extracted_audio),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0 or not extracted_audio.is_file():
            details = (result.stderr or "").strip()
            message = (
                f"FFmpeg could not extract audio from {input_path.name}."
            )
            if details:
                message += f" Details: {details[-1000:]}"
            raise ValueError(message)

        yield extracted_audio


def collect_inputs(args):
    files = [Path(item).expanduser() for item in args.inputs]

    if args.input_dir:
        directory = args.input_dir.expanduser()
        if not directory.is_dir():
            raise ValueError(f"Input directory not found: {directory}")

        iterator = (
            directory.rglob("*") if args.recursive else directory.iterdir()
        )
        files.extend(
            path
            for path in iterator
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
            "No input files found. Supply audio/video paths "
            "or use --input-dir."
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

    for index, source in enumerate(inputs, start=1):
        print(f"\n[{index}/{total}] {source.name}")

        if not source.is_file():
            print(f"  FAILED: input file not found: {source}")
            failed += 1
            continue

        if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"  FAILED: unsupported input format: {source.suffix}")
            failed += 1
            continue

        # Use the original filename, not the temporary extracted WAV name.
        output = args.output_dir / f"{source.stem}.mid"

        if output.exists() and not args.overwrite:
            print(f"  SKIPPED: output already exists: {output}")
            skipped += 1
            continue

        try:
            with prepare_audio(source) as audio_input:
                result = transcribe(
                    audio_input,
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

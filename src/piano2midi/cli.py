
"""Command-line interface for local and online piano transcription."""

import argparse
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from piano2midi.transcription.transkun_backend import (
    TranskunError,
    transcribe,
)

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}
SUPPORTED_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS

ALLOWED_URL_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "instagram.com",
    "www.instagram.com",
}


def parse_args():
    parser = argparse.ArgumentParser(
        prog="piano2midi",
        description=(
            "Transcribe piano audio/video files or accessible online "
            "media to MIDI using Transkun."
        ),
        epilog=(
            "Local files are processed locally. The --url option requires "
            "internet access and yt-dlp. Video inputs require FFmpeg."
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Local audio or video files to transcribe.",
    )
    parser.add_argument(
        "--url",
        action="append",
        default=[],
        metavar="URL",
        help=(
            "Download accessible media from YouTube or Instagram. "
            "Requires internet access; may be repeated."
        ),
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


def validate_url(url: str) -> None:
    """Allow only HTTPS URLs from the explicitly supported hostnames."""
    parsed = urlparse(url)

    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_URL_HOSTS:
        raise ValueError(
            "Unsupported URL. Supply an HTTPS YouTube or Instagram URL."
        )


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


@contextmanager
def download_url_audio(url: str):
    """Download accessible online media and yield its extracted WAV audio."""
    validate_url(url)

    # Check that yt-dlp is installed in the Python environment running this CLI.
    check = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if check.returncode != 0:
        raise ValueError(
            "Online URL support requires yt-dlp. Install it with: "
            "python -m pip install yt-dlp"
        )

    if shutil.which("ffmpeg") is None:
        raise ValueError(
            "FFmpeg was not found. Install FFmpeg and add it to PATH "
            "for online audio extraction."
        )

    with tempfile.TemporaryDirectory(prefix="piano2midi_url_") as temp_dir:
        temp_path = Path(temp_dir)
        output_template = str(temp_path / "%(id)s.%(ext)s")

        command = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--no-playlist",
            "--no-warnings",
            "--format",
            "bestaudio/best",
            "--extract-audio",
            "--audio-format",
            "wav",
            "--output",
            output_template,
            url,
        ]

        print("  Downloading audio (internet required)...")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            details = (result.stderr or result.stdout or "").strip()
            raise ValueError(
                "Could not download/extract audio from this URL. "
                "The media may be unavailable, require login, or be "
                "unsupported."
                + (f" Details: {details[-1200:]}" if details else "")
            )

        audio_files = list(temp_path.glob("*.wav"))
        if not audio_files:
            raise ValueError(
                "yt-dlp completed but did not produce a WAV audio file."
            )

        # The ID-based filename avoids relying on a video's title.
        yield audio_files[0]


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

    unique_files = []
    seen = set()

    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_files.append(resolved)

    if not unique_files and not args.url:
        raise ValueError(
            "No inputs found. Supply file paths, --input-dir, or --url."
        )

    return unique_files


def transcribe_one(audio_input, output, args):
    """Run the existing Transkun backend on a prepared audio file."""
    return transcribe(
        audio_input,
        output,
        device=args.device,
        executable=args.transkun_executable,
    )


def main():
    args = parse_args()

    try:
        inputs = collect_inputs(args)
        for url in args.url:
            validate_url(url)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)

    succeeded = 0
    skipped = 0
    failed = 0
    total = len(inputs) + len(args.url)

    # Process local files first.
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

        output = args.output_dir / f"{source.stem}.mid"

        if output.exists() and not args.overwrite:
            print(f"  SKIPPED: output already exists: {output}")
            skipped += 1
            continue

        try:
            with prepare_audio(source) as audio_input:
                result = transcribe_one(audio_input, output, args)

            print(f"  OK: {result}")
            succeeded += 1
        except (TranskunError, OSError, ValueError) as exc:
            print(f"  FAILED: {exc}")
            failed += 1

    # Online downloads use temporary directories that are cleaned up
    # automatically after each transcription attempt.
    for url_index, url in enumerate(args.url, start=len(inputs) + 1):
        print(f"\n[{url_index}/{total}] Online URL")

        try:
            with download_url_audio(url) as audio_input:
                output = args.output_dir / f"{audio_input.stem}.mid"

                if output.exists() and not args.overwrite:
                    print(f"  SKIPPED: output already exists: {output}")
                    skipped += 1
                    continue

                result = transcribe_one(audio_input, output, args)

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

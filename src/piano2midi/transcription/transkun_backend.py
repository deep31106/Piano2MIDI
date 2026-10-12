
"""Adapter for running Transkun as an external transcription backend."""

from pathlib import Path
import shutil
import subprocess


class TranskunError(RuntimeError):
    """Raised when Transkun cannot complete a transcription."""


def transcribe(
    audio_path: str | Path,
    output_path: str | Path,
    *,
    device: str = "cuda",
    executable: str | Path | None = None,
) -> Path:
    """Transcribe an audio file to MIDI using the installed Transkun CLI.

    Transkun runs in its own Python environment. This function invokes its
    command-line executable instead of importing its Python dependencies.
    """
    audio = Path(audio_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()

    if not audio.is_file():
        raise FileNotFoundError(f"Input audio not found: {audio}")

    if audio.suffix.lower() not in {".wav", ".mp3", ".flac", ".ogg"}:
        raise ValueError(f"Unsupported audio extension: {audio.suffix}")

    if executable is None:
        executable = shutil.which("transkun")

    if executable is None:
        raise TranskunError(
            "Transkun executable not found. Install Transkun in its own "
            "environment or pass its executable path explicitly."
        )

    executable = str(executable)

    output.parent.mkdir(parents=True, exist_ok=True)

    command = [
        executable,
        str(audio),
        str(output),
        "--device",
        device,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise TranskunError(f"Could not launch Transkun: {exc}") from exc

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise TranskunError(
            f"Transkun failed with exit code {result.returncode}."
            + (f"\n{details}" if details else "")
        )

    if not output.is_file() or output.stat().st_size == 0:
        raise TranskunError(
            f"Transkun reported success but produced no MIDI file: {output}"
        )

    return output

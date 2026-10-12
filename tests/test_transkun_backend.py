
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from piano2midi.transcription.transkun_backend import (
    TranskunError,
    transcribe,
)


def test_missing_audio_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        transcribe(
            tmp_path / "missing.wav",
            tmp_path / "output.mid",
            executable="/fake/transkun",
        )


def test_unsupported_extension_raises(tmp_path):
    audio = tmp_path / "song.mp4"
    audio.touch()

    with pytest.raises(ValueError, match="Unsupported audio extension"):
        transcribe(
            audio,
            tmp_path / "output.mid",
            executable="/fake/transkun",
        )


def test_missing_executable_raises(tmp_path):
    audio = tmp_path / "song.wav"
    audio.touch()

    with patch(
        "piano2midi.transcription.transkun_backend.shutil.which",
        return_value=None,
    ):
        with pytest.raises(TranskunError, match="not found"):
            transcribe(audio, tmp_path / "output.mid")


def test_successful_transcription(tmp_path):
    audio = tmp_path / "song.wav"
    audio.touch()
    output = tmp_path / "results" / "song.mid"

    def fake_run(command, **kwargs):
        # Simulate the external model writing its MIDI output.
        Path(command[2]).write_bytes(b"fake-midi-content")
        return Mock(returncode=0, stdout="", stderr="")

    with patch(
        "piano2midi.transcription.transkun_backend.subprocess.run",
        side_effect=fake_run,
    ) as run:
        result = transcribe(
            audio,
            output,
            executable="/fake/transkun",
        )

    assert result == output.resolve()
    assert result.read_bytes() == b"fake-midi-content"
    assert run.call_args.kwargs["check"] is False
    assert "--device" in run.call_args.args[0]


def test_failed_transcription_raises(tmp_path):
    audio = tmp_path / "song.wav"
    audio.touch()

    with patch(
        "piano2midi.transcription.transkun_backend.subprocess.run",
        return_value=Mock(
            returncode=1,
            stdout="",
            stderr="model crashed",
        ),
    ):
        with pytest.raises(TranskunError, match="model crashed"):
            transcribe(
                audio,
                tmp_path / "output.mid",
                executable="/fake/transkun",
            )


def test_success_without_output_raises(tmp_path):
    audio = tmp_path / "song.wav"
    audio.touch()

    with patch(
        "piano2midi.transcription.transkun_backend.subprocess.run",
        return_value=Mock(returncode=0, stdout="", stderr=""),
    ):
        with pytest.raises(TranskunError, match="produced no MIDI"):
            transcribe(
                audio,
                tmp_path / "output.mid",
                executable="/fake/transkun",
            )


from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from piano2midi.cli import prepare_audio


def test_audio_file_passes_through_unchanged(tmp_path):
    audio = tmp_path / "song.mp3"
    audio.touch()

    with prepare_audio(audio) as prepared:
        assert prepared == audio


def test_video_extracts_audio_and_cleans_temporary_file(tmp_path):
    video = tmp_path / "performance.mp4"
    video.touch()

    with patch(
        "piano2midi.cli.shutil.which",
        return_value="ffmpeg",
    ), patch("piano2midi.cli.subprocess.run") as run:

        def fake_ffmpeg(command, **kwargs):
            Path(command[-1]).write_bytes(b"fake-wav")
            return Mock(returncode=0, stderr="")

        run.side_effect = fake_ffmpeg

        with prepare_audio(video) as prepared:
            assert prepared.suffix == ".wav"
            assert prepared.read_bytes() == b"fake-wav"
            assert prepared != video

        assert not prepared.exists()

    command = run.call_args.args[0]
    assert command[0] == "ffmpeg"
    assert "-i" in command
    assert str(video) in command
    assert "-vn" in command


def test_video_fails_if_ffmpeg_is_missing(tmp_path):
    video = tmp_path / "performance.mov"
    video.touch()

    with patch("piano2midi.cli.shutil.which", return_value=None):
        with pytest.raises(ValueError, match="FFmpeg was not found"):
            with prepare_audio(video):
                pass


def test_video_fails_if_extraction_fails(tmp_path):
    video = tmp_path / "broken.mp4"
    video.touch()

    with patch(
        "piano2midi.cli.shutil.which",
        return_value="ffmpeg",
    ), patch(
        "piano2midi.cli.subprocess.run",
        return_value=Mock(returncode=1, stderr="Invalid input"),
    ):
        with pytest.raises(ValueError, match="could not extract audio"):
            with prepare_audio(video):
                pass

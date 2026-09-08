"""Round-trip tests for the ffmpeg wrappers; they shell out to the real binary."""
import subprocess

import pytest

import media

pytestmark = pytest.mark.skipif(
    not media.ffmpeg_available(), reason="ffmpeg/ffprobe not installed"
)


@pytest.fixture
def voice_note(tmp_path):
    """A two second OGG/Opus tone, the shape Telegram sends voice messages in."""
    path = tmp_path / "voice.ogg"
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-codec:a", "libopus", str(path),
        ],
        check=True,
    )
    return path


def test_probe_duration_reads_length(voice_note):
    assert media.probe_duration(voice_note) == pytest.approx(2.0, abs=0.2)


def test_to_mp3_produces_playable_audio(voice_note, tmp_path):
    converted = media.to_mp3(voice_note, tmp_path / "voice.mp3")

    assert converted.stat().st_size > 0
    assert media.probe_duration(converted) == pytest.approx(2.0, abs=0.2)


def test_to_mp3_rejects_non_media(tmp_path):
    junk = tmp_path / "junk.ogg"
    junk.write_bytes(b"definitely not audio")

    with pytest.raises(media.MediaError):
        media.to_mp3(junk, tmp_path / "out.mp3")


def test_probe_duration_rejects_non_media(tmp_path):
    junk = tmp_path / "junk.ogg"
    junk.write_bytes(b"definitely not audio")

    with pytest.raises(media.MediaError):
        media.probe_duration(junk)

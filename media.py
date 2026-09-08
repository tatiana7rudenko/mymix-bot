"""Thin ffmpeg/ffprobe wrappers used to handle Telegram voice and video notes.

Telegram delivers voice messages as OGG/Opus and video notes as MP4, neither of
which every client can replay comfortably, so the bot transcodes them to MP3.
Kept free of telebot imports so it can be tested without a bot token.
"""
import json
import shutil
import subprocess
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"


class MediaError(RuntimeError):
    """Raised when ffmpeg is missing or fails on a file."""


def ffmpeg_available() -> bool:
    """True when both ffmpeg and ffprobe are on PATH."""
    return shutil.which(FFMPEG) is not None and shutil.which(FFPROBE) is not None


def _run(args: list) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=True, check=True)
    except FileNotFoundError as exc:
        raise MediaError(f"{args[0]} is not installed") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", "replace").strip().splitlines()
        detail = stderr[-1] if stderr else f"exit code {exc.returncode}"
        raise MediaError(f"{args[0]} failed: {detail}") from exc


def probe_duration(src: PathLike) -> float:
    """Return the duration of a media file in seconds."""
    result = _run([
        FFPROBE, "-v", "error", "-show_entries", "format=duration",
        "-print_format", "json", str(src),
    ])
    payload = json.loads(result.stdout)
    try:
        return float(payload["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MediaError(f"no duration reported for {src}") from exc


def to_mp3(src: PathLike, dst: PathLike, bitrate: str = "128k") -> Path:
    """Transcode any input to MP3, dropping video so video notes work too."""
    dst = Path(dst)
    _run([
        FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(src), "-vn", "-codec:a", "libmp3lame", "-b:a", bitrate,
        str(dst),
    ])
    if not dst.exists() or dst.stat().st_size == 0:
        raise MediaError(f"ffmpeg produced no output for {src}")
    return dst

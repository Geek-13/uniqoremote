from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


@dataclass
class EncoderConfig:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    codec: str = "h264"
    bitrate: int = 5000
    preset: str = "fast"
    hardware: str = "auto"


class FfmpegEncoder:
    def __init__(self, config: EncoderConfig | None = None) -> None:
        self._config = config or EncoderConfig()
        self._proc: subprocess.Popen[bytes] | None = None
        self._available = bool(_find_ffmpeg())

    @property
    def is_available(self) -> bool:
        return self._available

    async def start(self, width: int, height: int, fps: int, codec: str) -> None:
        self._config.width = width
        self._config.height = height
        self._config.fps = fps
        self._config.codec = codec
        if not self._available:
            return
        exe = _find_ffmpeg()
        assert exe is not None
        encoder = _pick_encoder(self._config.hardware)
        cmd: list[str] = [
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgra",
            "-s",
            f"{width}x{height}",
            "-r",
            str(fps),
            "-i",
            "pipe:0",
            "-c:v",
            encoder,
            "-b:v",
            f"{self._config.bitrate}k",
            "-g",
            str(fps * 2),
            "-preset",
            self._config.preset,
            "-f",
            codec,
            "pipe:1",
        ]
        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    async def encode(self, frame_data: bytes) -> bytes:
        if self._proc is None or self._proc.stdin is None:
            return b""
        self._proc.stdin.write(frame_data)
        self._proc.stdin.flush()
        if self._proc.stdout is None:
            return b""
        return self._proc.stdout.read(65536)

    async def request_keyframe(self) -> None:
        if self._proc is not None:
            import signal as _signal

            self._proc.send_signal(int(_signal.SIGINT))

    async def stop(self) -> None:
        if self._proc is not None:
            if self._proc.stdin is not None:
                self._proc.stdin.close()
            self._proc.terminate()
            self._proc.wait(timeout=5)
            self._proc = None


class FfmpegDecoder:
    def __init__(self) -> None:
        self._proc: subprocess.Popen[bytes] | None = None
        self._available = bool(_find_ffmpeg())
        self._width = 0
        self._height = 0

    @property
    def is_available(self) -> bool:
        return self._available

    async def start(self, width: int, height: int, codec: str) -> None:
        self._width = width
        self._height = height
        if not self._available:
            return
        exe = _find_ffmpeg()
        assert exe is not None
        decoder_cmd: list[str] = [
            exe,
            "-f",
            codec,
            "-i",
            "pipe:0",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgra",
            "pipe:1",
        ]
        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    async def decode(self, data: bytes) -> bytes:
        if self._proc is None:
            return b""
        if self._proc.stdin is None:
            return b""
        self._proc.stdin.write(data)
        self._proc.stdin.flush()
        if self._proc.stdout is None:
            return b""
        return self._proc.stdout.read(self._width * self._height * 4)

    async def stop(self) -> None:
        if self._proc is not None:
            if self._proc.stdin is not None:
                self._proc.stdin.close()
            self._proc.terminate()
            self._proc.wait(timeout=5)
            self._proc = None


def _find_ffmpeg() -> str | None:
    for path in (
        "ffmpeg",
        os.path.join(os.environ.get("PROGRAMFILES", ""), "ffmpeg", "bin", "ffmpeg.exe"),
    ):
        try:
            if (
                subprocess.call(
                    [path, "-version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                )
                == 0
            ):
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
    return None


def _pick_encoder(hardware: str) -> str:
    hw_encoders = {
        "nvidia": "h264_nvenc",
        "amd": "h264_amf",
        "intel": "h264_qsv",
    }
    return hw_encoders.get(hardware, "libx264")

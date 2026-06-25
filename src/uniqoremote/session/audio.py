from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import StrEnum


class AudioCodec(StrEnum):
    OPUS = "opus"
    AAC = "aac"
    PCM = "pcm_s16le"


@dataclass
class AudioConfig:
    sample_rate: int = 48000
    channels: int = 2
    codec: AudioCodec = AudioCodec.OPUS
    bitrate: int = 128


@dataclass
class AudioFrame:
    data: bytes
    timestamp: float = 0.0
    sample_rate: int = 48000
    channels: int = 2


@dataclass
class AudioDevice:
    name: str
    device_id: int = 0
    is_input: bool = True
    is_default: bool = False


class AudioCapture:
    def __init__(self, config: AudioConfig | None = None) -> None:
        self._config = config or AudioConfig()
        self._proc: subprocess.Popen[bytes] | None = None

    async def start(self) -> None:
        pass

    async def read(self) -> AudioFrame:
        return AudioFrame(
            data=b"", sample_rate=self._config.sample_rate, channels=self._config.channels
        )

    async def stop(self) -> None:
        if self._proc is not None:
            self._proc.terminate()
            self._proc = None


class AudioPlayback:
    def __init__(self, config: AudioConfig | None = None) -> None:
        self._config = config or AudioConfig()

    async def start(self) -> None:
        pass

    async def play(self, frame: AudioFrame) -> None:
        pass

    async def stop(self) -> None:
        pass


def list_audio_devices() -> list[AudioDevice]:
    return [
        AudioDevice(name="Default Input", device_id=0, is_input=True, is_default=True),
        AudioDevice(name="Default Output", device_id=1, is_input=False, is_default=True),
    ]

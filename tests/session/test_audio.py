from __future__ import annotations

from uniqoremote.session.audio import (
    AudioCapture,
    AudioConfig,
    AudioPlayback,
    list_audio_devices,
)


class TestAudioConfig:
    def test_defaults(self) -> None:
        config = AudioConfig()
        assert config.sample_rate == 48000
        assert config.channels == 2
        assert config.bitrate == 128


class TestAudioCapture:
    async def test_start_stop(self) -> None:
        cap = AudioCapture()
        await cap.start()
        frame = await cap.read()
        assert frame.data == b""
        await cap.stop()


class TestAudioPlayback:
    async def test_start_stop(self) -> None:
        pb = AudioPlayback()
        await pb.start()
        await pb.stop()


class TestListDevices:
    def test_returns_defaults(self) -> None:
        devices = list_audio_devices()
        assert len(devices) == 2
        assert any(d.is_input for d in devices)
        assert any(not d.is_input for d in devices)

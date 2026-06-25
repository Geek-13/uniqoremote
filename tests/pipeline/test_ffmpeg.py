from __future__ import annotations

import pytest

from uniqoremote.pipeline.encoder.ffmpeg import EncoderConfig, FfmpegDecoder, FfmpegEncoder


class TestFfmpegEncoder:
    def test_availability_check(self) -> None:
        encoder = FfmpegEncoder()
        assert isinstance(encoder.is_available, bool)

    def test_encoder_config_defaults(self) -> None:
        config = EncoderConfig()
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 30
        assert config.codec == "h264"


class TestFfmpegDecoder:
    def test_availability_check(self) -> None:
        decoder = FfmpegDecoder()
        assert isinstance(decoder.is_available, bool)

    @pytest.mark.asyncio
    async def test_start_stop_safe_without_ffmpeg(self) -> None:
        decoder = FfmpegDecoder()
        await decoder.start(1920, 1080, "h264")
        result = await decoder.decode(b"")
        assert result == b""
        await decoder.stop()

from __future__ import annotations

import numpy as np
import pytest

from uniqoremote.pipeline.capturer.base import RawFrame
from uniqoremote.pipeline.decoder.base import Decoder
from uniqoremote.pipeline.encoder.base import EncodedPacket, Encoder
from uniqoremote.pipeline.pipeline import Pipeline


class QuickCapturer:
    def __init__(self) -> None:
        self._running = False

    async def start(self, monitor: int = 0) -> None:
        self._running = True

    async def capture(self) -> RawFrame:
        return RawFrame(data=np.zeros((240, 320, 3), dtype=np.uint8), width=320, height=240)

    async def stop(self) -> None:
        self._running = False

    @property
    def supported_resolutions(self) -> list[tuple[int, int]]:
        return [(320, 240)]


class QuickEncoder(Encoder):
    def __init__(self) -> None:
        self._started = False
        self.frame_count = 0

    async def start(self, width: int, height: int, fps: int, codec: str) -> None:
        self._started = True

    async def encode(self, frame) -> list[EncodedPacket]:
        self.frame_count += 1
        return [EncodedPacket(data=b"frame-" + str(self.frame_count).encode(), pts=frame.pts)]

    async def stop(self) -> None:
        self._started = False

    async def request_keyframe(self) -> None:
        pass


class QuickDecoder(Decoder):
    async def start(self, width: int, height: int, codec: str) -> None:
        pass

    async def decode(self, data: bytes) -> RawFrame:
        return RawFrame(data=np.zeros((240, 320, 3), dtype=np.uint8), width=320, height=240)

    async def stop(self) -> None:
        pass


@pytest.mark.asyncio
async def test_pipeline_produces_encoded_packets() -> None:
    capturer = QuickCapturer()
    encoder = QuickEncoder()
    pipeline = Pipeline(capturer, encoder)

    await pipeline.start(320, 240, 30)

    packets = await pipeline.read()
    assert len(packets) == 1
    assert packets[0].data == b"frame-1"

    await pipeline.stop()


@pytest.mark.asyncio
async def test_pipeline_multiple_frames() -> None:
    capturer = QuickCapturer()
    encoder = QuickEncoder()
    pipeline = Pipeline(capturer, encoder)

    await pipeline.start(320, 240, 30)

    for _ in range(3):
        packets = await pipeline.read()
        assert len(packets) == 1

    await pipeline.stop()
    assert encoder.frame_count >= 3


class TestDecoderIntegration:
    def test_decoder_abc_compliance(self) -> None:
        decoder = QuickDecoder()
        assert isinstance(decoder, Decoder)

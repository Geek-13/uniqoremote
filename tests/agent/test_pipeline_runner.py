from __future__ import annotations

import asyncio

import numpy as np
import pytest

from uniqoremote.agent.pipeline_runner import PipelineRunner
from uniqoremote.pipeline.capturer.base import Capturer, RawFrame
from uniqoremote.pipeline.encoder.base import EncodedPacket, Encoder


class _FakeCapturer(Capturer):
    def __init__(self) -> None:
        self._started = False
        self._count = 0

    async def start(self, monitor: int = 0) -> None:
        self._started = True

    async def capture(self) -> RawFrame:
        self._count += 1
        if self._count > 3:
            await asyncio.sleep(10)
        return RawFrame(
            data=np.zeros((100, 100, 4), dtype=np.uint8),
            width=100,
            height=100,
        )

    async def stop(self) -> None:
        self._started = False

    @property
    def supported_resolutions(self) -> list[tuple[int, int]]:
        return [(100, 100)]


class _FakeEncoder(Encoder):
    def __init__(self) -> None:
        self._started = False
        self.frames: list[RawFrame] = []

    async def start(self, width: int, height: int, fps: int, codec: str) -> None:
        self._started = True

    async def encode(self, frame: RawFrame) -> list[EncodedPacket]:
        self.frames.append(frame)
        return [EncodedPacket(data=b"encoded", is_keyframe=False, pts=0)]

    async def request_keyframe(self) -> None:
        pass

    async def stop(self) -> None:
        self._started = False


@pytest.mark.asyncio
async def test_pipeline_runner_start_stop() -> None:
    capturer = _FakeCapturer()
    encoder = _FakeEncoder()
    queue: asyncio.Queue[list[bytes]] = asyncio.Queue()
    runner = PipelineRunner(capturer, encoder, queue)
    await runner.start(1920, 1080, 30, "h264")
    assert runner.is_running
    await asyncio.sleep(0.2)
    assert not queue.empty()
    encoded_frames = await queue.get()
    assert len(encoded_frames) == 1
    assert encoded_frames[0] == b"encoded"
    await runner.stop()
    assert not runner.is_running

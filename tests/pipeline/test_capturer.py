from __future__ import annotations

import numpy as np
import pytest

from uniqoremote.pipeline.capturer.base import Capturer, RawFrame


class FakeCapturer(Capturer):
    def __init__(self) -> None:
        self._running = False
        self._monitor = 0
        self._counter = 0

    async def start(self, monitor: int = 0) -> None:
        self._monitor = monitor
        self._running = True

    async def capture(self) -> RawFrame:
        if not self._running:
            raise RuntimeError("Not started")
        self._counter += 1
        return RawFrame(data=np.zeros((720, 1280, 3), dtype=np.uint8), width=1280, height=720)

    async def stop(self) -> None:
        self._running = False

    @property
    def supported_resolutions(self) -> list[tuple[int, int]]:
        return [(1280, 720), (1920, 1080)]


class TestCapturerABC:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            Capturer()  # type: ignore[abstract]

    def test_fake_capturer_creates_frames(self) -> None:
        capturer = FakeCapturer()
        assert capturer.supported_resolutions == [(1280, 720), (1920, 1080)]


@pytest.mark.asyncio
async def test_fake_capturer_lifecycle() -> None:
    capturer = FakeCapturer()
    await capturer.start()
    frame = await capturer.capture()
    assert frame.width == 1280
    assert frame.height == 720
    assert frame.data.shape == (720, 1280, 3)
    await capturer.stop()

    with pytest.raises(RuntimeError, match="Not started"):
        await capturer.capture()

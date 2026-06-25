from __future__ import annotations

import numpy as np

from uniqoremote.pipeline.capturer.base import Capturer, RawFrame


class WgcCapturer(Capturer):
    """Windows Graphics Capture — requires Win10 1803+ and winrt."""

    def __init__(self) -> None:
        self._running = False
        self._monitor = 0

    async def start(self, monitor: int = 0) -> None:
        self._monitor = monitor
        self._running = True

    async def capture(self) -> RawFrame:
        return RawFrame(data=np.zeros((1080, 1920, 3), dtype=np.uint8), width=1920, height=1080)

    async def stop(self) -> None:
        self._running = False

    @property
    def supported_resolutions(self) -> list[tuple[int, int]]:
        return [(1920, 1080), (1280, 720)]

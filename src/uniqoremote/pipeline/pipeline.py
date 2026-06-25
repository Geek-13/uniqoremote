from __future__ import annotations

import asyncio
import contextlib

from uniqoremote.pipeline.capturer.base import Capturer
from uniqoremote.pipeline.encoder.base import EncodedPacket, Encoder


class Pipeline:
    def __init__(self, capturer: Capturer, encoder: Encoder) -> None:
        self._capturer = capturer
        self._encoder = encoder
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._queue: asyncio.Queue[list[EncodedPacket]] = asyncio.Queue(maxsize=30)

    async def start(self, width: int, height: int, fps: int, codec: str = "h264") -> None:
        await self._capturer.start()
        await self._encoder.start(width, height, fps, codec)
        self._running = True
        self._task = asyncio.create_task(self._capture_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        await self._encoder.stop()
        await self._capturer.stop()

    async def read(self) -> list[EncodedPacket]:
        return await self._queue.get()

    async def _capture_loop(self) -> None:
        while self._running:
            frame = await self._capturer.capture()
            packets = await self._encoder.encode(frame)
            await self._queue.put(packets)

from __future__ import annotations

import asyncio
import contextlib

from uniqoremote.pipeline.base import Pipeline as PipelineABC
from uniqoremote.pipeline.capturer.base import Capturer
from uniqoremote.pipeline.encoder.base import EncodedPacket, Encoder


class Pipeline(PipelineABC):
    def __init__(self, capturer: Capturer | None = None, encoder: Encoder | None = None) -> None:
        self._capturer = capturer
        self._encoder = encoder
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._queue: asyncio.Queue[list[EncodedPacket]] = asyncio.Queue(maxsize=30)

    def set_capturer(self, capturer: Capturer) -> None:
        self._capturer = capturer

    def set_encoder(self, encoder: Encoder) -> None:
        self._encoder = encoder

    async def start(self, width: int, height: int, fps: int, codec: str = "h264") -> None:
        if self._capturer is None or self._encoder is None:
            raise RuntimeError("Capturer and encoder must be set before starting")
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
        if self._encoder:
            await self._encoder.stop()
        if self._capturer:
            await self._capturer.stop()

    async def read(self) -> list[EncodedPacket]:
        return await self._queue.get()

    async def _capture_loop(self) -> None:
        if self._capturer is None or self._encoder is None:
            return
        while self._running:
            frame = await self._capturer.capture()
            packets = await self._encoder.encode(frame)
            await self._queue.put(packets)

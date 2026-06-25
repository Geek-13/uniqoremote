from __future__ import annotations

import asyncio
import contextlib

from uniqoremote.pipeline.capturer.base import Capturer
from uniqoremote.pipeline.encoder.base import Encoder


class PipelineRunner:
    def __init__(
        self,
        capturer: Capturer,
        encoder: Encoder,
        frame_queue: asyncio.Queue[list[bytes]],
    ) -> None:
        self._capturer = capturer
        self._encoder = encoder
        self._queue = frame_queue
        self._running = False
        self._task: asyncio.Task[None] | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self, width: int, height: int, fps: int, codec: str) -> None:
        await self._capturer.start()
        await self._encoder.start(width, height, fps, codec)
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        await self._encoder.stop()
        await self._capturer.stop()

    async def _loop(self) -> None:
        while self._running:
            try:
                frame = await asyncio.wait_for(self._capturer.capture(), timeout=1.0)
            except TimeoutError:
                continue
            packets = await self._encoder.encode(frame)
            data_list = [p.data for p in packets]
            await self._queue.put(data_list)

from __future__ import annotations

import asyncio
import time


class HeartbeatMonitor:
    def __init__(self, interval: float = 5.0, timeout: float = 30.0) -> None:
        self._interval = interval
        self._timeout = timeout
        self._last_beat: float = 0.0
        self._running = False
        self._task: asyncio.Task[None] | None = None

    @property
    def is_alive(self) -> bool:
        if self._last_beat == 0.0:
            return True
        return (time.time() - self._last_beat) < self._timeout

    def beat(self) -> None:
        self._last_beat = time.time()

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    async def _loop(self) -> None:
        while self._running:
            self.beat()
            await asyncio.sleep(self._interval)

from __future__ import annotations

import asyncio

from uniqoremote.core.events import MessageType
from uniqoremote.session.audio import AudioCapture, AudioFrame, AudioPlayback


class AudioSession:
    def __init__(self) -> None:
        self._capture = AudioCapture()
        self._playback = AudioPlayback()
        self._running = False
        self._send_queue: asyncio.Queue[AudioFrame] = asyncio.Queue(maxsize=50)

    async def start_capture(self) -> None:
        await self._capture.start()
        self._running = True
        asyncio.create_task(self._capture_loop())

    async def start_playback(self) -> None:
        await self._playback.start()

    async def stop(self) -> None:
        self._running = False
        await self._capture.stop()
        await self._playback.stop()

    async def on_audio_received(self, frame: AudioFrame) -> None:
        await self._playback.play(frame)

    async def get_audio_frame(self) -> AudioFrame:
        return await self._send_queue.get()

    async def _capture_loop(self) -> None:
        while self._running:
            frame = await self._capture.read()
            await self._send_queue.put(frame)


async def create_audio_pipeline() -> tuple[AudioSession, AudioSession]:
    local = AudioSession()
    remote = AudioSession()
    await local.start_capture()
    await remote.start_playback()
    return local, remote

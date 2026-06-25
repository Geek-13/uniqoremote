from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from uniqoremote.core.channel import EncryptedChannel
from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import DecodedMessage

MessageHandler = Callable[[DecodedMessage], Any]


class MessageRouter:
    def __init__(self, channel: EncryptedChannel) -> None:
        self._channel = channel
        self._handlers: dict[MessageType, list[MessageHandler]] = {}
        self._running = False
        self._task: asyncio.Task[None] | None = None

    def on(self, msg_type: MessageType, handler: MessageHandler) -> None:
        if msg_type not in self._handlers:
            self._handlers[msg_type] = []
        self._handlers[msg_type].append(handler)

    async def send(self, msg_type: MessageType, payload: bytes | dict[str, Any]) -> None:
        await self._channel.send(msg_type, payload)

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._receive_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()

    async def _receive_loop(self) -> None:
        while self._running:
            try:
                msg = await self._channel.recv()
            except Exception:
                continue
            handlers = self._handlers.get(msg.type, [])
            for handler in handlers:
                handler(msg)

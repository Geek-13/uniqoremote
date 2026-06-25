from __future__ import annotations

import asyncio
from typing import Any, Self

from uniqoremote.transport.base import Transport


class UdpTransport(Transport):
    def __init__(self) -> None:
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: _UdpProtocol | None = None
        self._remote_addr: tuple[str, int] | None = None

    @property
    def local_addr(self) -> tuple[str, int] | None:
        if self._transport is not None:
            sock = self._transport.get_extra_info("socket")
            if sock is not None:
                return sock.getsockname()[:2]
        return None

    async def bind(self, addr: tuple[str, int]) -> Self:
        loop = asyncio.get_running_loop()
        self._protocol = _UdpProtocol()
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: self._protocol,
            local_addr=addr,
        )
        return self

    async def connect(self, addr: tuple[str, int]) -> None:
        self._remote_addr = addr

    async def send(self, data: bytes) -> None:
        if self._transport is None or self._remote_addr is None:
            raise RuntimeError("Not connected")
        self._transport.sendto(data, self._remote_addr)

    async def recv(self) -> bytes:
        if self._protocol is None:
            raise RuntimeError("Not bound")
        return await self._protocol.recv()

    async def close(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None
        self._protocol = None
        self._remote_addr = None


class _UdpProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        self._queue.put_nowait(data)

    async def recv(self) -> bytes:
        return await self._queue.get()

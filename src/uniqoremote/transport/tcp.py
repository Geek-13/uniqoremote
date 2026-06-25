from __future__ import annotations

import asyncio

from uniqoremote.transport.base import Transport


class TcpTransport(Transport):
    def __init__(self) -> None:
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self, addr: tuple[str, int]) -> None:
        self._reader, self._writer = await asyncio.open_connection(addr[0], addr[1])

    async def send(self, data: bytes) -> None:
        if self._writer is None:
            raise RuntimeError("Not connected")
        self._writer.write(len(data).to_bytes(4, "big"))
        self._writer.write(data)
        await self._writer.drain()

    async def recv(self) -> bytes:
        if self._reader is None:
            raise RuntimeError("Not connected")
        header = await self._reader.readexactly(4)
        length = int.from_bytes(header, "big")
        return await self._reader.readexactly(length)

    async def recv_exactly(self, length: int) -> bytes:
        if self._reader is None:
            raise RuntimeError("Not connected")
        return await self._reader.readexactly(length)

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
        self._reader = None
        self._writer = None

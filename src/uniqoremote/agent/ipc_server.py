from __future__ import annotations

import asyncio
import struct
from typing import Any

import msgpack  # type: ignore[import-untyped]


class IpcServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        self._host = host
        self._port = port
        self._server: asyncio.Server | None = None
        self._pending: asyncio.Queue[IpcConnection] = asyncio.Queue()

    async def start(self) -> int:
        self._server = await asyncio.start_server(self._handler, self._host, self._port)
        assert self._server.sockets is not None
        sockname: tuple[str, int] = self._server.sockets[0].getsockname()[:2]
        return sockname[1]

    async def accept(self) -> IpcConnection:
        return await self._pending.get()

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await self._pending.put(IpcConnection(reader, writer))


class IpcClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        self._host = host
        self._port = port
        self._conn: IpcConnection | None = None

    async def connect(self) -> None:
        reader, writer = await asyncio.open_connection(self._host, self._port)
        self._conn = IpcConnection(reader, writer)

    async def send(self, msg_type: str, payload: dict[str, Any]) -> None:
        if self._conn is None:
            raise RuntimeError("Not connected")
        await self._conn.send(msg_type, payload)

    async def recv(self) -> tuple[str, dict[str, Any]]:
        if self._conn is None:
            raise RuntimeError("Not connected")
        return await self._conn.recv()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None


class IpcConnection:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self._reader = reader
        self._writer = writer

    async def send(self, msg_type: str, payload: dict[str, Any]) -> None:
        data = msgpack.packb({"type": msg_type, "payload": payload})
        self._writer.write(struct.pack(">I", len(data)) + data)
        await self._writer.drain()

    async def recv(self) -> tuple[str, dict[str, Any]]:
        header = await self._reader.readexactly(4)
        length = struct.unpack(">I", header)[0]
        data = await self._reader.readexactly(length)
        msg: dict[str, Any] = msgpack.unpackb(data)
        return msg["type"], msg["payload"]

    async def close(self) -> None:
        try:
            self._writer.close()
        except Exception:
            pass

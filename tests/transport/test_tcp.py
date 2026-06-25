from __future__ import annotations

import asyncio

import pytest

from uniqoremote.transport.tcp import TcpTransport


@pytest.mark.asyncio
async def test_tcp_echo_loopback() -> None:
    server = await asyncio.start_server(
        lambda r, w: asyncio.create_task(_echo_handler(r, w)),
        "127.0.0.1",
        0,
    )
    addr = server.sockets[0].getsockname()[:2]

    client = TcpTransport()
    await client.connect(addr)

    await client.send(b"ping")
    response = await asyncio.wait_for(client.recv(), timeout=2.0)
    assert response == b"pong"

    await client.close()
    server.close()
    await server.wait_closed()


async def _echo_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    header = await reader.readexactly(4)
    length = int.from_bytes(header, "big")
    data = await reader.readexactly(length)
    if data == b"ping":
        pong_data = b"pong"
        writer.write(len(pong_data).to_bytes(4, "big"))
        writer.write(pong_data)
        await writer.drain()
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_tcp_large_transfer() -> None:
    large_data = b"A" * 65536

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        header = await reader.readexactly(4)
        length = int.from_bytes(header, "big")
        data = await reader.readexactly(length)
        writer.write(len(data).to_bytes(4, "big"))
        writer.write(data)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(
        lambda r, w: asyncio.create_task(handler(r, w)), "127.0.0.1", 0
    )
    addr = server.sockets[0].getsockname()[:2]

    client = TcpTransport()
    await client.connect(addr)

    await client.send(large_data)
    response = await asyncio.wait_for(client.recv(), timeout=5.0)
    assert response == large_data

    await client.close()
    server.close()
    await server.wait_closed()

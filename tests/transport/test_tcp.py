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
    data = await reader.read(1024)
    if data == b"ping":
        writer.write(b"pong")
        await writer.drain()
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_tcp_large_transfer() -> None:
    large_data = b"A" * 65536

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        data = await reader.readexactly(len(large_data))
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
    response = await asyncio.wait_for(client.recv_exactly(len(large_data)), timeout=5.0)
    assert response == large_data

    await client.close()
    server.close()
    await server.wait_closed()

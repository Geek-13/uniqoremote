from __future__ import annotations

import asyncio

import pytest

from uniqoremote.transport.udp import UdpTransport


@pytest.mark.asyncio
async def test_udp_send_recv_loopback() -> None:
    server = UdpTransport()
    client = UdpTransport()

    await server.bind(("127.0.0.1", 0))
    await client.bind(("127.0.0.1", 0))

    server_addr = server.local_addr
    assert server_addr is not None

    await client.connect(server_addr)
    await server.connect(client.local_addr)  # type: ignore[arg-type]

    async def recv_and_verify() -> None:
        data = await server.recv()
        assert data == b"hello from client"

    recv_task = asyncio.create_task(recv_and_verify())
    await asyncio.sleep(0.01)
    await client.send(b"hello from client")
    await asyncio.wait_for(recv_task, timeout=2.0)

    await client.close()
    await server.close()


@pytest.mark.asyncio
async def test_udp_bind_auto_port() -> None:
    transport = UdpTransport()
    await transport.bind(("127.0.0.1", 0))
    addr = transport.local_addr
    assert addr is not None
    assert addr[0] == "127.0.0.1"
    assert addr[1] > 0
    await transport.close()

from __future__ import annotations

import asyncio

import pytest

from uniqoremote.agent.ipc_server import IpcServer
from uniqoremote.ui.ipc_client import IpcClient


@pytest.fixture
async def ipc_pair(unused_tcp_port: int):
    server = IpcServer(port=unused_tcp_port)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.05)

    client = IpcClient(port=unused_tcp_port)
    await client.connect()
    conn_server = await asyncio.wait_for(server.accept(), timeout=2.0)

    try:
        yield client, conn_server
    finally:
        try:
            await client.close()
        except Exception:
            pass
        try:
            await conn_server.close()
        except Exception:
            pass
        server_task.cancel()
        try:
            await server_task
        except (asyncio.CancelledError, Exception):
            pass
        try:
            await server.stop()
        except Exception:
            pass


@pytest.mark.asyncio
async def test_ipc_start_capture(ipc_pair) -> None:
    client, server = ipc_pair
    await client.send("START_CAPTURE", {"width": 1920, "height": 1080, "fps": 30, "codec": "h264"})
    msg_type, payload = await asyncio.wait_for(server.recv(), timeout=2.0)
    assert msg_type == "START_CAPTURE"
    assert payload["width"] == 1920
    assert payload["fps"] == 30


@pytest.mark.asyncio
async def test_ipc_inject_input(ipc_pair) -> None:
    client, server = ipc_pair
    await client.send("INJECT_INPUT", {"type": "KEY_DOWN", "key": 0x41})
    msg_type, payload = await asyncio.wait_for(server.recv(), timeout=2.0)
    assert msg_type == "INJECT_INPUT"
    assert payload["key"] == 0x41


@pytest.mark.asyncio
async def test_ipc_frame_push(ipc_pair) -> None:
    client, server = ipc_pair
    data = b"\x00" * 100
    await server.send("FRAME", {"data": data, "width": 1920, "height": 1080, "pts": 0.0})
    msg_type, payload = await asyncio.wait_for(client.recv(), timeout=2.0)
    assert msg_type == "FRAME"
    assert payload["width"] == 1920
    assert payload["data"] == data


@pytest.mark.asyncio
async def test_ipc_heartbeat(ipc_pair) -> None:
    client, server = ipc_pair
    await client.send("HEARTBEAT", {"ts": 12345})
    msg_type, payload = await asyncio.wait_for(server.recv(), timeout=2.0)
    assert msg_type == "HEARTBEAT"
    await server.send("HEARTBEAT", {"ts": 12346})
    msg_type2, payload2 = await asyncio.wait_for(client.recv(), timeout=2.0)
    assert msg_type2 == "HEARTBEAT"


@pytest.mark.asyncio
async def test_ipc_multiple_messages(ipc_pair) -> None:
    client, server = ipc_pair
    for i in range(5):
        await client.send("HEARTBEAT", {"seq": i})
    for i in range(5):
        msg_type, payload = await asyncio.wait_for(server.recv(), timeout=2.0)
        assert payload["seq"] == i

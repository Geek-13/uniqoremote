from __future__ import annotations

import pytest

from uniqoremote.core.crypto import generate_key_pair, public_key_to_bytes
from uniqoremote.server.protocol import ProtocolServer


@pytest.mark.asyncio
async def test_protocol_server_start_stop() -> None:
    server = ProtocolServer()
    port = await server.start("127.0.0.1", 0)
    assert port > 0
    await server.stop()


def test_hello_registration() -> None:
    sk_a, pk_a = generate_key_pair()
    server = ProtocolServer()
    server.register_device("test-device-1", public_key_to_bytes(pk_a), ("127.0.0.1", 12345))
    device = server.lookup_peer("test-device-1")
    assert device is not None
    assert device.public_key == public_key_to_bytes(pk_a)

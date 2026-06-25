"""UniqoRemote demo — protocol + encryption roundtrip on loopback."""
from __future__ import annotations

import asyncio

from uniqoremote.core.channel import EncryptedChannel
from uniqoremote.core.crypto import derive_session_key, generate_key_pair, generate_nonce
from uniqoremote.core.events import MessageType
from uniqoremote.transport.udp import UdpTransport


async def main() -> None:
    sk_a, pk_a = generate_key_pair()
    sk_b, pk_b = generate_key_pair()
    nonce_a = generate_nonce()
    nonce_b = generate_nonce()
    session_key = derive_session_key(sk_a, pk_b, nonce_a, nonce_b)

    transport_a = UdpTransport()
    transport_b = UdpTransport()
    await transport_a.bind(("127.0.0.1", 0))
    await transport_b.bind(("127.0.0.1", 0))

    addr_a = transport_a.local_addr
    addr_b = transport_b.local_addr
    assert addr_a is not None and addr_b is not None

    await transport_a.connect(addr_b)
    await transport_b.connect(addr_a)

    channel_a = EncryptedChannel(transport_a, session_key)
    channel_b = EncryptedChannel(transport_b, session_key)

    await channel_a.send(MessageType.CHAT, {"msg": "Hello UniqoRemote!"})
    received = await channel_b.recv()

    print(f"Type: {received.type.name}")
    print(f"Payload: {received.payload}")
    print("Encrypted roundtrip OK")

    await transport_a.close()
    await transport_b.close()


if __name__ == "__main__":
    asyncio.run(main())

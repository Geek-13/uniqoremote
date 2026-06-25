from __future__ import annotations

import asyncio

import pytest

from uniqoremote.core.channel import EncryptedChannel
from uniqoremote.core.crypto import derive_session_key, generate_key_pair, generate_nonce
from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import DecodedMessage
from uniqoremote.transport.udp import UdpTransport


@pytest.mark.asyncio
async def test_encrypted_channel_roundtrip() -> None:
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
    assert addr_a is not None
    assert addr_b is not None

    await transport_a.connect(addr_b)
    await transport_b.connect(addr_a)

    channel_a = EncryptedChannel(transport_a, session_key)
    channel_b = EncryptedChannel(transport_b, session_key)

    payload = {"msg": "encrypted hello"}
    await channel_a.send(MessageType.CHAT, payload)

    msg = await asyncio.wait_for(channel_b.recv(), timeout=2.0)
    assert isinstance(msg, DecodedMessage)
    assert msg.type == MessageType.CHAT
    assert isinstance(msg.payload, dict)
    assert msg.payload["msg"] == "encrypted hello"

    await transport_a.close()
    await transport_b.close()


@pytest.mark.asyncio
async def test_encrypted_channel_binary_payload() -> None:
    sk_a, pk_a = generate_key_pair()
    sk_b, pk_b = generate_key_pair()
    session_key = derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce())

    transport_a = UdpTransport()
    transport_b = UdpTransport()
    await transport_a.bind(("127.0.0.1", 0))
    await transport_b.bind(("127.0.0.1", 0))
    await transport_a.connect(transport_b.local_addr)  # type: ignore[arg-type]
    await transport_b.connect(transport_a.local_addr)  # type: ignore[arg-type]

    channel_a = EncryptedChannel(transport_a, session_key)
    channel_b = EncryptedChannel(transport_b, session_key)

    binary = b"\x00\x01\x02\x03" * 100
    await channel_a.send(MessageType.VIDEO, binary)

    msg = await asyncio.wait_for(channel_b.recv(), timeout=2.0)
    assert msg.type == MessageType.VIDEO
    assert msg.payload == binary

    await transport_a.close()
    await transport_b.close()


@pytest.mark.asyncio
async def test_channel_seq_num_monotonic() -> None:
    sk_a, pk_a = generate_key_pair()
    sk_b, pk_b = generate_key_pair()
    session_key = derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce())

    transport_a = UdpTransport()
    transport_b = UdpTransport()
    await transport_a.bind(("127.0.0.1", 0))
    await transport_b.bind(("127.0.0.1", 0))
    await transport_a.connect(transport_b.local_addr)  # type: ignore[arg-type]
    await transport_b.connect(transport_a.local_addr)  # type: ignore[arg-type]

    channel_a = EncryptedChannel(transport_a, session_key)
    channel_b = EncryptedChannel(transport_b, session_key)

    seqs: list[int] = []
    for i in range(5):
        await channel_a.send(MessageType.STREAM, {"msg": f"msg{i}"})
        msg = await asyncio.wait_for(channel_b.recv(), timeout=2.0)
        seqs.append(msg.seq_num)

    assert seqs == sorted(seqs)
    assert len(set(seqs)) == 5

    await transport_a.close()
    await transport_b.close()

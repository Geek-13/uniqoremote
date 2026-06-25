from __future__ import annotations

from uniqoremote.transport.p2p import P2PTransport, PunchResult, StunClient


class TestP2PTransport:
    async def test_bind_and_close(self) -> None:
        transport = P2PTransport()
        await transport.bind(("127.0.0.1", 0))
        assert transport.local_addr is not None
        await transport.close()

    async def test_punch_returns_result(self) -> None:
        transport = P2PTransport()
        await transport.bind(("127.0.0.1", 0))
        result = await transport.punch(("127.0.0.1", 9999), attempts=1, timeout=0.1)
        assert isinstance(result, PunchResult)
        await transport.close()


class TestStunClient:
    async def test_discover_returns_address(self) -> None:
        client = StunClient()
        addr = await client.discover()
        assert len(addr) == 2
        assert isinstance(addr[0], str)

    async def test_discover_returns_gracefully_on_failure(self) -> None:
        client = StunClient()
        client.STUN_SERVERS = [("10.255.255.1", 19302)]
        addr = await client.discover()
        assert addr == ("0.0.0.0", 0)

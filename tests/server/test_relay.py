from __future__ import annotations

import pytest

from uniqoremote.server.relay.relay import RelayServer, RelaySession


class TestRelayServer:
    async def test_create_and_lookup(self) -> None:
        server = RelayServer()
        server.create_session("s1")
        assert server.register_client("s1", ("1.1.1.1", 1000)) is True
        assert server.register_client("s1", ("2.2.2.2", 2000)) is True
        assert server.register_client("s1", ("3.3.3.3", 3000)) is False
        peer = server.get_peer("s1", ("1.1.1.1", 1000))
        assert peer == ("2.2.2.2", 2000)

    def test_relay_session_defaults(self) -> None:
        s = RelaySession(session_id="x")
        assert s.session_id == "x"
        assert s.client_a_addr is None
        assert s.client_b_addr is None

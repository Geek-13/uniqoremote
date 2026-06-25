from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass
class RelaySession:
    session_id: str
    client_a_addr: tuple[str, int] | None = None
    client_b_addr: tuple[str, int] | None = None
    created_at: float = field(default_factory=lambda: __import__("time").time())


class RelayServer:
    def __init__(self) -> None:
        self._sessions: dict[str, RelaySession] = {}
        self._server: asyncio.Server | None = None
        self._transport: asyncio.DatagramTransport | None = None

    async def start(self, host: str = "0.0.0.0", port: int = 21117) -> int:
        loop = asyncio.get_running_loop()
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: _RelayProtocol(self),
            local_addr=(host, port),
        )
        return self._transport.get_extra_info("socket").getsockname()[1]

    def create_session(self, session_id: str) -> RelaySession:
        session = RelaySession(session_id=session_id)
        self._sessions[session_id] = session
        return session

    def register_client(self, session_id: str, addr: tuple[str, int]) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False
        if session.client_a_addr is None:
            session.client_a_addr = addr
        elif session.client_b_addr is None:
            session.client_b_addr = addr
        else:
            return False
        return True

    def get_peer(self, session_id: str, addr: tuple[str, int]) -> tuple[str, int] | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if addr == session.client_a_addr:
            return session.client_b_addr
        return session.client_a_addr

    async def stop(self) -> None:
        if self._transport:
            self._transport.close()
            self._transport = None

    def _relay(self, data: bytes, from_addr: tuple[str, int], session_id: str) -> None:
        if self._transport is None:
            return
        peer = self.get_peer(session_id, from_addr)
        if peer:
            self._transport.sendto(data, peer)


class _RelayProtocol(asyncio.DatagramProtocol):
    def __init__(self, relay: RelayServer) -> None:
        self._relay = relay

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if len(data) < 12:
            return
        session_id = data[:12].decode("ascii", errors="replace")
        payload = data[12:]
        self._relay._relay(payload, addr, session_id)

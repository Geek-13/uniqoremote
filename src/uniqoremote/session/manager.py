from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from uniqoremote.core.channel import EncryptedChannel
from uniqoremote.core.crypto import (
    generate_key_pair,
    generate_nonce,
    public_key_from_bytes,
)
from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import decode_frame, encode_frame
from uniqoremote.session.handshake import (
    derive_shared_key,
    generate_hello_payload,
)
from uniqoremote.transport.base import Transport
from uniqoremote.transport.p2p import P2PTransport, StunClient
from uniqoremote.transport.tcp import TcpTransport
from uniqoremote.transport.udp import UdpTransport


class SessionState(StrEnum):
    IDLE = "idle"
    CONNECTING = "connecting"
    HANDSHAKING = "handshaking"
    ACTIVE = "active"
    CLOSING = "closing"
    ERROR = "error"


class SessionError(Exception):
    pass


@dataclass
class Session:
    session_id: str
    remote_device_id: str
    state: SessionState = SessionState.IDLE
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition(self, target: SessionState) -> None:
        valid = _TRANSITIONS.get(self.state, set())
        if target not in valid:
            raise SessionError(f"Invalid transition: {self.state} -> {target}")
        self.state = target


_TRANSITIONS: dict[SessionState, set[SessionState]] = {
    SessionState.IDLE: {SessionState.CONNECTING},
    SessionState.CONNECTING: {SessionState.HANDSHAKING, SessionState.ERROR},
    SessionState.HANDSHAKING: {SessionState.ACTIVE, SessionState.ERROR},
    SessionState.ACTIVE: {SessionState.CLOSING, SessionState.ERROR},
    SessionState.CLOSING: {SessionState.IDLE},
    SessionState.ERROR: {SessionState.IDLE, SessionState.CLOSING},
}


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._channel: EncryptedChannel | None = None
        self._transport: Transport | None = None
        self._frame_handlers: list[Callable[[bytes], None]] = []
        self._input_handlers: list[Callable[[dict[str, Any]], None]] = []
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._listen_task: asyncio.Task[None] | None = None
        self._listen_udp: UdpTransport | None = None

    def create(self, session_id: str, remote_device_id: str) -> Session:
        session = Session(session_id=session_id, remote_device_id=remote_device_id)
        session.transition(SessionState.CONNECTING)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def list_active(self) -> list[Session]:
        return [s for s in self._sessions.values() if s.state == SessionState.ACTIVE]

    def on_frame(self, handler: Callable[[bytes], None]) -> None:
        self._frame_handlers.append(handler)

    def on_input(self, handler: Callable[[dict[str, Any]], None]) -> None:
        self._input_handlers.append(handler)

    async def listen(self, config_device_id: str, server_addr: tuple[str, int]) -> None:
        sk, pk = generate_key_pair()
        nonce = generate_nonce()
        hello = generate_hello_payload(config_device_id, pk, "1.0.0", nonce)
        frame = encode_frame(MessageType.HELLO, hello)

        self._listen_udp = UdpTransport()
        await self._listen_udp.bind(("0.0.0.0", 0))
        await self._listen_udp.connect(server_addr)
        await self._listen_udp.send(frame)

        self._listen_task = asyncio.create_task(self._listen_loop(sk, b""))

    async def _listen_loop(self, sk: Any, nonce: bytes) -> None:
        if self._listen_udp is None:
            return
        while True:
            try:
                raw = await asyncio.wait_for(self._listen_udp.recv(), timeout=30.0)
            except TimeoutError:
                continue
            try:
                msg = decode_frame(raw)
            except Exception:
                continue
            if msg.type == MessageType.PUNCH:
                from_id = str(msg.payload.get("from_device_id", ""))
                peer_addr = msg.payload.get("peer_addr", [])
                if peer_addr and len(peer_addr) == 2:
                    p2p = P2PTransport()
                    await p2p.bind(("0.0.0.0", 0))
                    await p2p.connect((str(peer_addr[0]), int(peer_addr[1])))
                    await p2p.send(b"\x00" * 8)
                    session_key = derive_shared_key(sk, sk.public_key(), nonce, nonce)
                    self._transport = p2p
                    self._channel = EncryptedChannel(p2p, session_key)
                    session = self.create(from_id, from_id)
                    session.transition(SessionState.HANDSHAKING)
                    session.transition(SessionState.ACTIVE)

    async def connect(
        self,
        remote_device_id: str,
        server_addr: tuple[str, int],
        stun: StunClient,
        p2p: P2PTransport,
        relay: TcpTransport,
        config_device_id: str,
    ) -> Session:
        sk, pk = generate_key_pair()
        nonce = generate_nonce()
        hello = generate_hello_payload(config_device_id, pk, "1.0.0", nonce, remote_device_id)
        frame = encode_frame(MessageType.HELLO, hello)

        udp = UdpTransport()
        await udp.bind(("0.0.0.0", 0))
        await udp.connect(server_addr)
        await udp.send(frame)

        try:
            raw = await asyncio.wait_for(udp.recv(), timeout=5.0)
        except TimeoutError as e:
            raise SessionError("No response from server") from e

        msg = decode_frame(raw)
        if msg.type != MessageType.NOTIFY:
            raise SessionError(f"Expected NOTIFY, got {msg.type}")

        peer_info = msg.payload.get("peer", {})
        peer_pubkey = peer_info.get("public_key", b"")
        if not peer_pubkey:
            raise SessionError("Peer not online")

        session_key = derive_shared_key(sk, public_key_from_bytes(peer_pubkey), nonce, b"")

        peer_addr = peer_info.get("addr")
        if peer_addr and len(peer_addr) == 2:
            await p2p.bind(("0.0.0.0", 0))
            await p2p.connect((str(peer_addr[0]), int(peer_addr[1])))
            await p2p.send(b"\x00" * 8)

        self._transport = p2p
        self._channel = EncryptedChannel(p2p, session_key)

        session = self.create(remote_device_id, remote_device_id)
        session.transition(SessionState.HANDSHAKING)
        session.transition(SessionState.ACTIVE)

        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._start_receive_loop()
        return session

    def _start_receive_loop(self) -> None:
        import msgpack

        async def _loop() -> None:
            while self._channel is not None:
                try:
                    msg = await self._channel.recv()
                    if msg.type == MessageType.VIDEO:
                        data: bytes
                        if isinstance(msg.payload, bytes):
                            data = msg.payload
                        else:
                            data = msgpack.packb(msg.payload)
                        for h in self._frame_handlers:
                            h(data)
                    elif msg.type == MessageType.INPUT:
                        payload = msg.payload if isinstance(msg.payload, dict) else {}
                        for h in self._input_handlers:
                            h(payload)
                except Exception:
                    await asyncio.sleep(0.1)

        asyncio.create_task(_loop())

    async def _heartbeat_loop(self) -> None:
        while self._channel is not None:
            try:
                await self._channel.send(MessageType.PING, {})
                await asyncio.sleep(5)
            except Exception:
                self._channel = None
                for s in self._sessions.values():
                    if s.state == SessionState.ACTIVE:
                        s.transition(SessionState.ERROR)
                break

    async def send_frame(self, data: bytes) -> None:
        if self._channel is None:
            raise SessionError("Not connected")
        await self._channel.send(MessageType.VIDEO, data)

    async def send_input(self, payload: dict[str, Any]) -> None:
        if self._channel is None:
            raise SessionError("Not connected")
        await self._channel.send(MessageType.INPUT, payload)

    async def disconnect(self) -> None:
        if self._channel is not None:
            await self._channel.send(MessageType.BYE, {})
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        self._channel = None
        self._transport = None

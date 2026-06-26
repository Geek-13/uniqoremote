from __future__ import annotations

import asyncio
from typing import Any

from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import HEADER_SIZE, decode_frame, encode_frame
from uniqoremote.server.relay.relay import RelayServer
from uniqoremote.server.rendezvous.manager import RegisteredDevice, RendezvousManager


class ProtocolServer:
    def __init__(self) -> None:
        self._rendezvous = RendezvousManager()
        self._relay = RelayServer()
        self._transport: asyncio.DatagramTransport | None = None

    async def start(self, host: str = "0.0.0.0", port: int = 21116) -> int:
        loop = asyncio.get_running_loop()
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: _UdpProtocol(self),
            local_addr=(host, port),
        )
        sock = self._transport.get_extra_info("socket")
        assert sock is not None
        sockname: tuple[str, int] = sock.getsockname()
        return sockname[1]

    async def start_relay(self, host: str = "0.0.0.0", port: int = 21117) -> int:
        return await self._relay.start(host, port)

    def register_device(
        self, device_id: str, public_key: bytes, addr: tuple[str, int] | None
    ) -> RegisteredDevice:
        return self._rendezvous.register(device_id, public_key, addr)

    def lookup_peer(self, device_id: str) -> RegisteredDevice | None:
        return self._rendezvous.lookup_peer(device_id)

    async def stop(self) -> None:
        if self._transport:
            self._transport.close()
            self._transport = None
        await self._relay.stop()

    def handle_datagram(self, data: bytes, addr: tuple[str, int]) -> None:
        if len(data) < HEADER_SIZE:
            return
        try:
            msg = decode_frame(data)
        except Exception:
            return

        if msg.type == MessageType.HELLO:
            self._handle_hello(msg.payload, addr)
        elif msg.type == MessageType.PUNCH:
            self._handle_punch(msg.payload, addr)
        elif msg.type == MessageType.PING:
            self._rendezvous.update_heartbeat(str(msg.payload.get("device_id", "")))

    def _handle_hello(self, payload: Any, addr: tuple[str, int]) -> None:
        device_id = str(payload.get("device_id", ""))
        public_key = payload.get("public_key", b"")
        self._rendezvous.register(device_id, public_key, addr)

        target_id = str(payload.get("target_device_id", ""))
        peer_info: dict[str, Any] = {}
        if target_id:
            peer = self._rendezvous.lookup_peer(target_id)
            if peer:
                peer_info = {
                    "device_id": peer.device_id,
                    "public_key": peer.public_key,
                    "addr": list(peer.addr) if peer.addr else None,
                }
                if peer.addr and self._transport:
                    notify_peer = encode_frame(
                        MessageType.PUNCH,
                        {"from_device_id": device_id, "peer_addr": list(addr)},
                    )
                    self._transport.sendto(notify_peer, peer.addr)

        if self._transport:
            ack = encode_frame(
                MessageType.NOTIFY,
                {"status": "registered", "peer": peer_info},
            )
            self._transport.sendto(ack, addr)

    def _handle_punch(self, payload: Any, addr: tuple[str, int]) -> None:
        target_id = str(payload.get("target_device_id", ""))
        from_id = str(payload.get("from_device_id", ""))
        peer = self._rendezvous.lookup_peer(target_id)

        if peer and peer.addr and self._transport:
            punch_data = encode_frame(
                MessageType.PUNCH,
                {"from_device_id": from_id, "peer_addr": peer.addr},
            )
            self._transport.sendto(punch_data, addr)

            notify_peer = encode_frame(
                MessageType.PUNCH,
                {"from_device_id": from_id, "peer_addr": addr},
            )
            self._transport.sendto(notify_peer, peer.addr)


class _UdpProtocol(asyncio.DatagramProtocol):
    def __init__(self, server: ProtocolServer) -> None:
        self._server = server

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self._server.handle_datagram(data, addr)

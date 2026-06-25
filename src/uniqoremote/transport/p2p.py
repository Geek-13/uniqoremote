from __future__ import annotations

import asyncio
import contextlib
import socket
from dataclasses import dataclass
from typing import Self

from uniqoremote.transport.base import Transport
from uniqoremote.transport.udp import UdpTransport


@dataclass
class PunchResult:
    success: bool
    local_addr: tuple[str, int]
    peer_addr: tuple[str, int] | None = None
    nat_type: str = "unknown"


class StunClient:
    STUN_SERVERS = [
        ("stun.l.google.com", 19302),
        ("stun1.l.google.com", 19302),
    ]

    def __init__(self) -> None:
        self._transport: UdpTransport | None = None

    async def discover(self) -> tuple[str, int]:
        for host, port in self.STUN_SERVERS:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(3)
                sock.connect((host, port))
                addr = sock.getsockname()
                sock.close()
                return (addr[0], addr[1])
            except (TimeoutError, OSError):
                continue
        return ("0.0.0.0", 0)


class P2PTransport(Transport):
    def __init__(self) -> None:
        self._udp = UdpTransport()

    async def bind(self, addr: tuple[str, int]) -> Self:
        await self._udp.bind(addr)
        return self

    async def connect(self, addr: tuple[str, int]) -> None:
        await self._udp.connect(addr)

    async def send(self, data: bytes) -> None:
        await self._udp.send(data)

    async def recv(self) -> bytes:
        return await self._udp.recv()

    async def close(self) -> None:
        await self._udp.close()

    @property
    def local_addr(self) -> tuple[str, int] | None:
        return self._udp.local_addr

    async def punch(
        self,
        peer_addr: tuple[str, int],
        attempts: int = 5,
        timeout: float = 0.5,
    ) -> PunchResult:
        await self._udp.connect(peer_addr)
        for _i in range(attempts):
            with contextlib.suppress(OSError):
                await self._udp.send(b"\x00" * 8)
            try:
                data = await asyncio.wait_for(self._udp.recv(), timeout=timeout)
                if data:
                    return PunchResult(
                        success=True, local_addr=self.local_addr or ("", 0), peer_addr=peer_addr
                    )
            except TimeoutError:
                continue
        return PunchResult(success=False, local_addr=self.local_addr or ("", 0))

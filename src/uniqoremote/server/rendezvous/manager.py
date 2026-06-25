from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class RegisteredDevice:
    device_id: str
    public_key: bytes
    version: str = "1.0.0"
    addr: tuple[str, int] | None = None
    registered_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    _timeout: float = 60.0

    @property
    def is_online(self) -> bool:
        return time.time() - self.last_seen < self._timeout


class RendezvousManager:
    def __init__(self, session_timeout: float = 60.0) -> None:
        self._devices: dict[str, RegisteredDevice] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._timeout = session_timeout

    def register(
        self, device_id: str, public_key: bytes, addr: tuple[str, int] | None = None
    ) -> RegisteredDevice:
        device = RegisteredDevice(
            device_id=device_id,
            public_key=public_key,
            addr=addr,
            _timeout=self._timeout,
        )
        self._devices[device_id] = device
        return device

    def unregister(self, device_id: str) -> None:
        self._devices.pop(device_id, None)

    def get_device(self, device_id: str) -> RegisteredDevice | None:
        return self._devices.get(device_id)

    def lookup_peer(self, device_id: str) -> RegisteredDevice | None:
        device = self._devices.get(device_id)
        if device is None:
            return None
        if not device.is_online:
            return None
        return device

    def update_heartbeat(self, device_id: str) -> None:
        device = self._devices.get(device_id)
        if device:
            device.last_seen = time.time()

    def list_online_devices(self) -> list[RegisteredDevice]:
        return [d for d in self._devices.values() if d.is_online]

    def get_lock(self, device_id: str) -> asyncio.Lock:
        if device_id not in self._locks:
            self._locks[device_id] = asyncio.Lock()
        return self._locks[device_id]

from __future__ import annotations

from abc import ABC, abstractmethod


class Transport(ABC):
    @abstractmethod
    async def connect(self, addr: tuple[str, int]) -> None: ...

    @abstractmethod
    async def send(self, data: bytes) -> None: ...

    @abstractmethod
    async def recv(self) -> bytes: ...

    @abstractmethod
    async def close(self) -> None: ...

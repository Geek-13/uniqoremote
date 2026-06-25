from __future__ import annotations

from abc import ABC, abstractmethod

from uniqoremote.pipeline.capturer.base import RawFrame


class Decoder(ABC):
    @abstractmethod
    async def start(self, width: int, height: int, codec: str) -> None: ...

    @abstractmethod
    async def decode(self, data: bytes) -> RawFrame: ...

    @abstractmethod
    async def stop(self) -> None: ...

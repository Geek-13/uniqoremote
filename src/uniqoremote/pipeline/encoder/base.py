from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from uniqoremote.pipeline.capturer.base import RawFrame


@dataclass
class EncodedPacket:
    data: bytes
    pts: float = 0.0
    is_keyframe: bool = False


class Encoder(ABC):
    @abstractmethod
    async def start(self, width: int, height: int, fps: int, codec: str) -> None: ...

    @abstractmethod
    async def encode(self, frame: RawFrame) -> list[EncodedPacket]: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def request_keyframe(self) -> None: ...

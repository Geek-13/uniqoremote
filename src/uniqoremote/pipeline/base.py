from __future__ import annotations

from abc import ABC, abstractmethod

from uniqoremote.pipeline.capturer.base import Capturer
from uniqoremote.pipeline.encoder.base import EncodedPacket, Encoder


class Pipeline(ABC):
    @abstractmethod
    async def start(self, width: int, height: int, fps: int, codec: str = "h264") -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def read(self) -> list[EncodedPacket]: ...

    @abstractmethod
    def set_capturer(self, capturer: Capturer) -> None: ...

    @abstractmethod
    def set_encoder(self, encoder: Encoder) -> None: ...

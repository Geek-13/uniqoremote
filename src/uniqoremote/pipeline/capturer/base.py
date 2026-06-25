from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class RawFrame:
    data: np.ndarray[Any, Any]
    width: int
    height: int
    pts: float = 0.0


class Capturer(ABC):
    @abstractmethod
    async def start(self, monitor: int = 0) -> None: ...

    @abstractmethod
    async def capture(self) -> RawFrame: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @property
    @abstractmethod
    def supported_resolutions(self) -> list[tuple[int, int]]: ...

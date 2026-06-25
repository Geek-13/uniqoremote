from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto


class InputEventType(Enum):
    KEY_DOWN = auto()
    KEY_UP = auto()
    MOUSE_MOVE = auto()
    MOUSE_DOWN = auto()
    MOUSE_UP = auto()
    MOUSE_WHEEL = auto()


@dataclass
class InputEvent:
    type: InputEventType
    data: dict[str, int]


class InputController(ABC):
    @abstractmethod
    async def send_event(self, event: InputEvent) -> None: ...

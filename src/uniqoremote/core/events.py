from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from typing import Any


class ConnectionState(StrEnum):
    IDLE = "idle"
    CONNECTING = "connecting"
    HANDSHAKING = "handshaking"
    ACTIVE = "active"
    CLOSING = "closing"
    ERROR = "error"


class MessageType(Enum):
    HELLO = 0x01
    PUNCH = 0x02
    NOTIFY = 0x03
    RELAY = 0x04
    STREAM = 0x05
    CONTROL = 0x06
    CLIPBOARD = 0x07
    FILE = 0x08
    CHAT = 0x09
    AUDIO = 0x0A
    VIDEO = 0x0B
    INPUT = 0x0C
    ERROR = 0x0D
    PING = 0x0E
    PONG = 0x0F
    BYE = 0x10

    @classmethod
    def from_int(cls, value: int) -> MessageType:
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown message type: 0x{value:02X}")


class InputEventType(Enum):
    KEY_DOWN = auto()
    KEY_UP = auto()
    MOUSE_MOVE = auto()
    MOUSE_DOWN = auto()
    MOUSE_UP = auto()
    MOUSE_WHEEL = auto()


class ErrorCode(Enum):
    INVALID_FRAME = 0x01
    VERSION_MISMATCH = 0x02
    AUTH_FAILED = 0x03
    DEVICE_OFFLINE = 0x04
    RELAY_FULL = 0x05
    PUNCH_FAILED = 0x06
    TIMEOUT = 0x07
    INTERNAL = 0x08


@dataclass
class ConnectionEvent:
    state: ConnectionState
    device_id: str


@dataclass
class InputEvent:
    type: InputEventType
    data: dict[str, Any]


@dataclass
class FrameEvent:
    width: int
    height: int
    data: bytes
    pts: float = 0.0


@dataclass
class ErrorEvent:
    code: ErrorCode
    message: str
    device_id: str = ""

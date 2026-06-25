from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class PrivacyMode(StrEnum):
    OFF = "off"
    BLACK_SCREEN = "black_screen"
    WALLPAPER = "wallpaper"


@dataclass
class PrivacyScreen:
    mode: PrivacyMode = PrivacyMode.OFF

    def enable(self, mode: PrivacyMode = PrivacyMode.BLACK_SCREEN) -> None:
        self.mode = mode

    def disable(self) -> None:
        self.mode = PrivacyMode.OFF

    @property
    def is_active(self) -> bool:
        return self.mode != PrivacyMode.OFF

    def to_control_message(self) -> dict[str, Any]:
        return {"privacy_mode": str(self.mode), "enabled": self.is_active}

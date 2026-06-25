from __future__ import annotations

import ctypes
from dataclasses import dataclass


@dataclass
class MonitorInfo:
    index: int
    name: str
    width: int
    height: int
    is_primary: bool = False


class MonitorManager:
    def __init__(self) -> None:
        self._user32 = ctypes.windll.user32

    def list_monitors(self) -> list[MonitorInfo]:
        width = self._user32.GetSystemMetrics(0)
        height = self._user32.GetSystemMetrics(1)
        return [MonitorInfo(0, "Primary", width, height, True)]

    @property
    def primary_resolution(self) -> tuple[int, int]:
        return (
            self._user32.GetSystemMetrics(0),
            self._user32.GetSystemMetrics(1),
        )

from __future__ import annotations

import ctypes
import ctypes.wintypes

from uniqoremote.input.base import InputController, InputEvent, InputEventType

INPUT_KEYBOARD = 1
INPUT_MOUSE = 0
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120


class _MOUSEINPUT(ctypes.Structure):  # noqa: N801
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_uint32),
        ("dwFlags", ctypes.c_uint32),
        ("time", ctypes.c_uint32),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _KEYBDINPUT(ctypes.Structure):  # noqa: N801
    _fields_ = [
        ("wVk", ctypes.c_uint16),
        ("wScan", ctypes.c_uint16),
        ("dwFlags", ctypes.c_uint32),
        ("time", ctypes.c_uint32),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):  # noqa: N801
    _fields_ = [
        ("mi", _MOUSEINPUT),
        ("ki", _KEYBDINPUT),
    ]


class _WININPUT(ctypes.Structure):  # noqa: N801
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("union", _INPUT_UNION),
    ]


class WindowsInputController(InputController):
    async def send_event(self, event: InputEvent) -> None:
        inputs = self._build_input(event)
        ctypes.windll.user32.SendInput(len(inputs), inputs, ctypes.sizeof(_WININPUT))

    def _build_input(self, event: InputEvent) -> list[_WININPUT]:
        inp = _WININPUT()
        if event.type in (InputEventType.KEY_DOWN, InputEventType.KEY_UP):
            inp.type = INPUT_KEYBOARD
            inp.union.ki.wVk = event.data.get("key", 0)
            inp.union.ki.wScan = 0
            inp.union.ki.dwFlags = KEYEVENTF_KEYUP if event.type == InputEventType.KEY_UP else 0
            inp.union.ki.time = 0
            inp.union.ki.dwExtraInfo = None
        elif event.type == InputEventType.MOUSE_MOVE:
            inp.type = INPUT_MOUSE
            inp.union.mi.dx = event.data.get("x", 0)
            inp.union.mi.dy = event.data.get("y", 0)
            inp.union.mi.mouseData = 0
            inp.union.mi.dwFlags = MOUSEEVENTF_MOVE
            inp.union.mi.time = 0
            inp.union.mi.dwExtraInfo = None
        elif event.type == InputEventType.MOUSE_DOWN:
            inp.type = INPUT_MOUSE
            inp.union.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
        elif event.type == InputEventType.MOUSE_UP:
            inp.type = INPUT_MOUSE
            inp.union.mi.dwFlags = MOUSEEVENTF_LEFTUP
        elif event.type == InputEventType.MOUSE_WHEEL:
            inp.type = INPUT_MOUSE
            inp.union.mi.mouseData = event.data.get("delta", WHEEL_DELTA)
            inp.union.mi.dwFlags = MOUSEEVENTF_WHEEL
        return [inp]

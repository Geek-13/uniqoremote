from __future__ import annotations

import asyncio
import ctypes
from collections.abc import Callable


class ClipboardSync:
    def __init__(self, send_handler: Callable[[str], None]) -> None:
        self._send = send_handler
        self._last_text: str = ""
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    def on_remote_text(self, text: str) -> None:
        self._last_text = text
        self._set_clipboard(text)

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                current = self._get_clipboard()
                if current and current != self._last_text:
                    self._last_text = current
                    self._send(current)
            except Exception:
                pass
            await asyncio.sleep(0.5)

    @staticmethod
    def _get_clipboard() -> str:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_TEXT = 1  # noqa: N806
        if not user32.OpenClipboard(0):
            return ""
        try:
            h_data = user32.GetClipboardData(CF_TEXT)
            if not h_data:
                return ""
            lp = kernel32.GlobalLock(h_data)
            if not lp:
                return ""
            try:
                return ctypes.c_char_p(lp).value.decode("gbk", errors="replace")
            finally:
                kernel32.GlobalUnlock(h_data)
        finally:
            user32.CloseClipboard()

    @staticmethod
    def _set_clipboard(text: str) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_TEXT = 1  # noqa: N806
        data = text.encode("gbk") + b"\x00"
        if not user32.OpenClipboard(0):
            return
        try:
            user32.EmptyClipboard()
            h_mem = kernel32.GlobalAlloc(0x0002, len(data))
            if not h_mem:
                return
            lp = kernel32.GlobalLock(h_mem)
            if not lp:
                return
            ctypes.memmove(lp, data, len(data))
            kernel32.GlobalUnlock(h_mem)
            user32.SetClipboardData(CF_TEXT, h_mem)
        finally:
            user32.CloseClipboard()

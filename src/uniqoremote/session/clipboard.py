from __future__ import annotations

import ctypes
import ctypes.wintypes
from dataclasses import dataclass


@dataclass
class ClipboardData:
    text: str = ""
    format: str = "text/plain"


class ClipboardManager:
    CF_UNICODETEXT = 13

    def __init__(self) -> None:
        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32

    def get_text(self) -> ClipboardData:
        try:
            if not self._user32.OpenClipboard(0):
                return ClipboardData()
            try:
                hdata = self._user32.GetClipboardData(self.CF_UNICODETEXT)
                if hdata is None:
                    return ClipboardData()
                ptr = self._kernel32.GlobalLock(hdata)
                if ptr is None:
                    return ClipboardData()
                try:
                    text = ctypes.c_wchar_p(ptr).value
                    return ClipboardData(text=text or "")
                finally:
                    self._kernel32.GlobalUnlock(hdata)
            finally:
                self._user32.CloseClipboard()
        except (OSError, ValueError, ctypes.ArgumentError):
            return ClipboardData()

    def set_text(self, text: str) -> bool:
        try:
            if not self._user32.OpenClipboard(0):
                return False
            try:
                self._user32.EmptyClipboard()
                size = (len(text) + 1) * 2
                hmem = self._kernel32.GlobalAlloc(0x0042, size)
                ptr = self._kernel32.GlobalLock(hmem)
                encoded = text.encode("utf-16-le")
                ctypes.memmove(ptr, encoded, min(len(encoded), size))
                self._kernel32.GlobalUnlock(hmem)
                self._user32.SetClipboardData(self.CF_UNICODETEXT, hmem)
                return True
            finally:
                self._user32.CloseClipboard()
        except (OSError, ValueError, ctypes.ArgumentError):
            return False

    def sync(self, remote_data: ClipboardData) -> ClipboardData:
        local = self.get_text()
        if remote_data.text and remote_data.text != local.text:
            self.set_text(remote_data.text)
        return local

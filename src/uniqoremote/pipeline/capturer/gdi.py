from __future__ import annotations

import ctypes
import ctypes.wintypes

import numpy as np

from uniqoremote.pipeline.capturer.base import Capturer, RawFrame


class GdiCapturer(Capturer):
    def __init__(self) -> None:
        self._running = False
        self._monitor = 0

    async def start(self, monitor: int = 0) -> None:
        self._monitor = monitor
        self._running = True

    async def capture(self) -> RawFrame:
        if not self._running:
            raise RuntimeError("Capturer not started")

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        hwnd = user32.GetDesktopWindow()
        hdc_src = user32.GetWindowDC(hwnd)
        hdc_dst = gdi32.CreateCompatibleDC(hdc_src)

        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)

        hbitmap = gdi32.CreateCompatibleBitmap(hdc_src, width, height)
        gdi32.SelectObject(hdc_dst, hbitmap)
        gdi32.BitBlt(hdc_dst, 0, 0, width, height, hdc_src, 0, 0, 0x00CC0020)

        bmp_info = _BITMAPINFO()
        bmp_info.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmp_info.bmiHeader.biWidth = width
        bmp_info.bmiHeader.biHeight = -height
        bmp_info.bmiHeader.biPlanes = 1
        bmp_info.bmiHeader.biBitCount = 32
        bmp_info.bmiHeader.biCompression = 0

        buf_size = width * height * 4
        buf = (ctypes.c_ubyte * buf_size)()
        gdi32.GetDIBits(hdc_dst, hbitmap, 0, height, buf, ctypes.byref(bmp_info), 0)

        data = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 4)
        data = data[:, :, :3]
        data = np.ascontiguousarray(data[:, :, ::-1])

        gdi32.DeleteObject(hbitmap)
        gdi32.DeleteDC(hdc_dst)
        user32.ReleaseDC(hwnd, hdc_src)

        return RawFrame(data=data, width=width, height=height)

    async def stop(self) -> None:
        self._running = False

    @property
    def supported_resolutions(self) -> list[tuple[int, int]]:
        user32 = ctypes.windll.user32
        return [(user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))]


class _BITMAPINFOHEADER(ctypes.Structure):  # noqa: N801
    _fields_ = [
        ("biSize", ctypes.c_uint32),
        ("biWidth", ctypes.c_int32),
        ("biHeight", ctypes.c_int32),
        ("biPlanes", ctypes.c_uint16),
        ("biBitCount", ctypes.c_uint16),
        ("biCompression", ctypes.c_uint32),
        ("biSizeImage", ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed", ctypes.c_uint32),
        ("biClrImportant", ctypes.c_uint32),
    ]


class _BITMAPINFO(ctypes.Structure):  # noqa: N801
    _fields_ = [
        ("bmiHeader", _BITMAPINFOHEADER),
    ]

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QKeyEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from uniqoremote.pipeline.encoder.ffmpeg import FfmpegDecoder
    from uniqoremote.session.manager import SessionManager


class RemoteView(QWidget):
    def __init__(
        self,
        session_mgr: SessionManager | None = None,
        decoder: FfmpegDecoder | None = None,
    ) -> None:
        super().__init__()
        self._session_mgr = session_mgr
        self._decoder = decoder
        self._display = QLabel()
        self._display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._display.setStyleSheet("background-color: black;")
        self._display.setMinimumSize(640, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._display)

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        if self._session_mgr:
            self._session_mgr.on_frame(self._on_frame)

        self._timer = QTimer()
        self._timer.timeout.connect(self._process_frames)
        self._timer.start(16)
        self._frame_queue: list[bytes] = []

    def _on_frame(self, data: bytes) -> None:
        self._frame_queue.append(data)

    def _process_frames(self) -> None:
        if not self._frame_queue:
            return
        data = self._frame_queue.pop(0)
        if self._decoder:
            raw = self._decoder.decode(data)
            if raw and self._decoder._width > 0:
                img = QImage(
                    raw,
                    self._decoder._width,
                    self._decoder._height,
                    self._decoder._width * 4,
                    QImage.Format.Format_RGBA8888,
                )
                self._display.setPixmap(QPixmap.fromImage(img))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._session_mgr:
            asyncio.ensure_future(
                self._session_mgr.send_input(
                    {"type": "mouse_move", "x": event.position().x(), "y": event.position().y()}
                )
            )

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._session_mgr:
            btn_map = {
                Qt.MouseButton.LeftButton: "left",
                Qt.MouseButton.RightButton: "right",
                Qt.MouseButton.MiddleButton: "middle",
            }
            btn = btn_map.get(event.button(), "left")
            asyncio.ensure_future(
                self._session_mgr.send_input({"type": "mouse_press", "button": btn})
            )

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._session_mgr:
            btn_map = {
                Qt.MouseButton.LeftButton: "left",
                Qt.MouseButton.RightButton: "right",
                Qt.MouseButton.MiddleButton: "middle",
            }
            btn = btn_map.get(event.button(), "left")
            asyncio.ensure_future(
                self._session_mgr.send_input({"type": "mouse_release", "button": btn})
            )

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if self._session_mgr:
            asyncio.ensure_future(
                self._session_mgr.send_input(
                    {"type": "key_press", "key": event.key(), "modifiers": int(event.modifiers())}
                )
            )

    def keyReleaseEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if self._session_mgr:
            asyncio.ensure_future(
                self._session_mgr.send_input({"type": "key_release", "key": event.key()})
            )

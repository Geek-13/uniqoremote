from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class RemoteView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._display = QLabel()
        self._display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._display.setStyleSheet("background-color: #1a1a1a;")
        self._display.setText("等待连接...")
        self._layout.addWidget(self._display)

        self._current_frame: np.ndarray | None = None
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh)
        self._timer.start(33)

    def update_frame(self, data: np.ndarray, width: int, height: int) -> None:
        if data.shape[:2] != (height, width):
            data = data.reshape(height, width, 3)
        self._current_frame = data

    def _refresh(self) -> None:
        if self._current_frame is None:
            return
        h, w, _ = self._current_frame.shape
        qimage = QImage(self._current_frame.tobytes(), w, h, w * 3, QImage.Format.Format_BGR888)
        scaled = self._display.size()
        pixmap = QPixmap.fromImage(qimage).scaled(
            scaled, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self._display.setPixmap(pixmap)

    def set_placeholder(self, text: str) -> None:
        self._current_frame = None
        self._display.setText(text)

    def get_display_size(self) -> tuple[int, int]:
        s = self._display.size()
        return (s.width(), s.height())

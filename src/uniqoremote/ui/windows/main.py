from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QStatusBar, QVBoxLayout, QWidget

from uniqoremote.core.config import Config


class MainWindow(QMainWindow):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self.setWindowTitle("UniqoRemote")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self._device_label = QLabel(f"Device: {config.identity.device_id}")
        self._device_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._device_label)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage(f"UniqoRemote v0.1.0 - {config.identity.device_name}")

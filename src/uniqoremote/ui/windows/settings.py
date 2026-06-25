from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from uniqoremote.core.config import Config


class SettingsPage(QWidget):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)

        title = QLabel("设置")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #cdd6f4;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self._device_name = QLineEdit(config.identity.device_name)
        form.addRow("设备名称:", self._device_name)

        self._server_addr = QLineEdit(config.network.rendezvous_server)
        self._server_addr.setPlaceholderText("例如: 192.168.1.100:21116")
        form.addRow("服务器地址:", self._server_addr)

        self._bind_port = QLineEdit(str(config.network.bind_port))
        form.addRow("本地端口:", self._bind_port)

        self._max_fps = QLineEdit(str(config.display.max_fps))
        form.addRow("最大帧率:", self._max_fps)

        layout.addLayout(form)

        row = QHBoxLayout()
        save = QPushButton("保存")
        save.setStyleSheet(
            "QPushButton { background-color: #a6e3a1; color: #1e1e2e;"
            " font-weight: bold; padding: 10px 24px; }"
            "QPushButton:hover { background-color: #94e2d5; }"
        )
        save.clicked.connect(self._on_save)
        row.addStretch()
        row.addWidget(save)
        layout.addLayout(row)

        layout.addStretch()

    def _on_save(self) -> None:
        self._config.identity.device_name = self._device_name.text()
        self._config.network.rendezvous_server = self._server_addr.text()
        self._config.network.bind_port = int(self._bind_port.text())
        self._config.display.max_fps = int(self._max_fps.text())

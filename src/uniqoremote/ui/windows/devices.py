from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QListWidget, QVBoxLayout


class DeviceListDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("设备列表")
        self.resize(400, 500)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("在线设备"))
        self._list = QListWidget()
        self._list.addItem("暂无在线设备")
        layout.addWidget(self._list)

        label = QLabel("输入远程设备ID或从列表选择")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888;")
        layout.addWidget(label)

    def update_devices(self, devices: list[str]) -> None:
        self._list.clear()
        if not devices:
            self._list.addItem("暂无在线设备")
        else:
            for d in devices:
                self._list.addItem(d)

    def selected_device_id(self) -> str | None:
        item = self._list.currentItem()
        if item and item.text() != "暂无在线设备":
            return item.text()
        return None

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QTextEdit, QVBoxLayout, QWidget


class FileManagerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("远程文件管理")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("远程文件管理器 - 拖拽文件到此处传输"))
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("传输记录将显示在此处...")
        layout.addWidget(self._log)

    def log_transfer(self, filename: str, status: str) -> None:
        self._log.append(f"[{status}] {filename}")

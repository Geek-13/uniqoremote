from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from uniqoremote.session.chat import ChatManager


class ChatDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("聊天消息")
        self.resize(500, 450)

        self._mgr = ChatManager()

        layout = QVBoxLayout(self)
        self._display = QTextEdit()
        self._display.setReadOnly(True)
        self._display.setPlaceholderText("聊天记录将显示在此处...")
        layout.addWidget(self._display)

        row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("输入消息...")
        self._input.returnPressed.connect(self._send)
        row.addWidget(self._input)
        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self._send)
        row.addWidget(send_btn)
        layout.addLayout(row)

    def _send(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        msg = self._mgr.send("local", text)
        self._display.append(f"[{msg.timestamp[:19]}] local: {text}")
        self._input.clear()

    def add_remote_message(self, sender: str, content: str) -> None:
        self._mgr.send(sender, content)
        self._display.append(f"[remote] {sender}: {content}")

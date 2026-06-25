from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from uniqoremote.session.terminal import RemoteTerminal


class TerminalDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("远程终端 (CMD)")
        self.resize(700, 500)

        self._terminal = RemoteTerminal()

        layout = QVBoxLayout(self)
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("远程命令输出将显示在此处...")
        layout.addWidget(self._output)

        self._input = QLineEdit()
        self._input.setPlaceholderText("输入命令，按 Enter 执行 (如: dir, ipconfig)")
        self._input.returnPressed.connect(self._execute)
        layout.addWidget(self._input)

        self._send_btn = QPushButton("执行")
        self._send_btn.clicked.connect(self._execute)
        layout.addWidget(self._send_btn)

    def _execute(self) -> None:
        cmd = self._input.text().strip()
        if not cmd:
            return
        self._output.append(f"> {cmd}")
        self._input.clear()
        result = self._terminal.execute(cmd)
        if result.stdout:
            self._output.append(result.stdout.rstrip())
        if result.stderr:
            self._output.append(f"[stderr] {result.stderr.rstrip()}")
        if result.exit_code != 0:
            self._output.append(f"[exit code: {result.exit_code}]")

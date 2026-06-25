from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from uniqoremote.core.config import Config


class MainWindow(QMainWindow):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self.setWindowTitle("UniqoRemote")
        self.resize(420, 600)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        identity = QGroupBox("本机信息")
        id_layout = QVBoxLayout(identity)
        id_layout.addWidget(QLabel(f"设备名: {config.identity.device_name}"))
        self._id_label = QLabel(f"设备 ID: {config.identity.device_id}")
        self._id_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        self._id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        id_layout.addWidget(self._id_label)
        root.addWidget(identity)

        connect_group = QGroupBox("连接远程设备")
        connect_layout = QVBoxLayout(connect_group)
        input_row = QHBoxLayout()
        self._remote_input = QLineEdit()
        self._remote_input.setPlaceholderText("输入远程设备 ID")
        self._remote_input.setMaxLength(12)
        input_row.addWidget(self._remote_input)
        self._connect_btn = QPushButton("连接")
        self._connect_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 6px 20px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self._connect_btn.clicked.connect(self._on_connect)
        input_row.addWidget(self._connect_btn)
        connect_layout.addLayout(input_row)
        root.addWidget(connect_group)

        actions = QGroupBox("快捷操作")
        actions_layout = QVBoxLayout(actions)
        self._file_btn = QPushButton("远程文件管理")
        self._file_btn.clicked.connect(self._open_file_manager)
        self._terminal_btn = QPushButton("远程终端 (CMD)")
        self._terminal_btn.clicked.connect(self._open_terminal)
        self._privacy_btn = QPushButton("隐私屏")
        self._privacy_btn.setCheckable(True)
        self._privacy_btn.clicked.connect(self._on_toggle_privacy)
        self._settings_btn = QPushButton("设置")
        self._settings_btn.clicked.connect(self._open_settings)
        actions_layout.addWidget(self._file_btn)
        actions_layout.addWidget(self._terminal_btn)
        actions_layout.addWidget(self._privacy_btn)
        actions_layout.addWidget(self._settings_btn)
        root.addWidget(actions)

        recent = QGroupBox("最近连接")
        recent_layout = QVBoxLayout(recent)
        self._recent_label = QLabel("暂无记录")
        self._recent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._recent_label.setStyleSheet("color: #888;")
        recent_layout.addWidget(self._recent_label)
        root.addWidget(recent)

        root.addStretch()

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(line)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage(
            f"UniqoRemote v0.1.0 | {config.identity.device_name} | ID: {config.identity.device_id}"
        )

    def _on_connect(self) -> None:
        remote_id = self._remote_input.text().strip()
        if not remote_id:
            self._status.showMessage("请输入远程设备 ID", 3000)
            return
        self._status.showMessage(f"正在连接 {remote_id}...", 5000)

    def _on_toggle_privacy(self, checked: bool) -> None:
        if checked:
            self._status.showMessage("隐私屏已开启", 2000)
            self._privacy_btn.setText("关闭隐私屏")
            self._privacy_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; }"
            )
        else:
            self._status.showMessage("隐私屏已关闭", 2000)
            self._privacy_btn.setText("隐私屏")
            self._privacy_btn.setStyleSheet("")

    def _open_file_manager(self) -> None:
        from uniqoremote.ui.windows.file_manager import FileManagerDialog

        dlg = FileManagerDialog(self)
        dlg.exec()

    def _open_terminal(self) -> None:
        from uniqoremote.ui.windows.terminal import TerminalDialog

        dlg = TerminalDialog(self)
        dlg.exec()

    def _open_settings(self) -> None:
        from uniqoremote.ui.windows.settings import SettingsDialog

        dlg = SettingsDialog(self._config, self)
        if dlg.exec():
            self._status.showMessage("设置已保存", 2000)

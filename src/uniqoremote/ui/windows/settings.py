from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from uniqoremote.core.config import Config


class SettingsDialog(QDialog):
    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(450, 350)
        self._config = config

        tabs = QTabWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)

        tabs.addTab(self._build_general(), "通用")
        tabs.addTab(self._build_display(), "显示")
        tabs.addTab(self._build_network(), "网络")
        tabs.addTab(self._build_ai(), "AI")

        btn_row = QHBoxLayout()
        save = QPushButton("保存")
        save.clicked.connect(self.accept)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(save)
        btn_row.addWidget(cancel)
        layout.addLayout(btn_row)

    def _build_general(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self._name_edit = QLineEdit(self._config.identity.device_name)
        form.addRow("设备名称:", self._name_edit)
        self._lang_box = QComboBox()
        self._lang_box.addItems(["简体中文", "English"])
        form.addRow("语言:", self._lang_box)
        return w

    def _build_display(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self._fps_edit = QLineEdit(str(self._config.display.max_fps))
        form.addRow("最大帧率:", self._fps_edit)
        self._quality_box = QComboBox()
        self._quality_box.addItems(["高画质", "平衡", "流畅"])
        form.addRow("画质:", self._quality_box)
        return w

    def _build_network(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self._server_edit = QLineEdit(self._config.network.rendezvous_server)
        form.addRow("服务器地址:", self._server_edit)
        self._port_edit = QLineEdit(str(self._config.network.bind_port))
        form.addRow("绑定端口:", self._port_edit)
        return w

    def _build_ai(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self._ai_enabled = QCheckBox("启用 AI 功能")
        self._ai_enabled.setChecked(self._config.ai.enabled)
        form.addRow(self._ai_enabled)
        form.addRow(QLabel("需要配置环境变量 UNIQOREMOTE_AI_API_KEY"))
        return w

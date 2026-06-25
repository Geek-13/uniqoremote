from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from uniqoremote.ai.client import DeepSeekClient
    from uniqoremote.pipeline.encoder.ffmpeg import FfmpegDecoder
    from uniqoremote.session.manager import SessionManager
    from uniqoremote.session.router import MessageRouter
    from uniqoremote.ui.ipc_client import IpcClient

from uniqoremote.core.config import Config


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: Config,
        session_mgr: SessionManager | None = None,
        decoder: FfmpegDecoder | None = None,
        agent_client: IpcClient | None = None,
        ai_client: DeepSeekClient | None = None,
        router: MessageRouter | None = None,
    ) -> None:
        super().__init__()
        self._config = config
        self._session_mgr = session_mgr
        self._decoder = decoder
        self._agent_client = agent_client
        self._ai_client = ai_client
        self._router = router
        self._active_session_id: str | None = None
        self._privacy_active = False

        self.setWindowTitle("UniqoRemote")
        self.resize(420, 680)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        root.addWidget(self._build_identity())
        root.addWidget(self._build_connect())
        root.addWidget(self._build_actions())
        root.addWidget(self._build_session_tools())
        root.addWidget(self._build_ai_tools())
        root.addWidget(self._build_recent())
        root.addStretch()

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(line)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage(
            f"UniqoRemote v0.1.0 | {config.identity.device_name} | ID: {config.identity.device_id}"
        )

    def _build_identity(self) -> QGroupBox:
        g = QGroupBox("本机信息")
        layout = QVBoxLayout(g)
        layout.addWidget(QLabel(f"设备名: {self._config.identity.device_name}"))
        self._id_label = QLabel(f"设备 ID: {self._config.identity.device_id}")
        self._id_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        self._id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._id_label)
        return g

    def _build_connect(self) -> QGroupBox:
        g = QGroupBox("连接远程设备")
        layout = QVBoxLayout(g)
        row = QHBoxLayout()
        self._remote_input = QLineEdit()
        self._remote_input.setPlaceholderText("输入远程设备 ID")
        self._remote_input.setMaxLength(12)
        row.addWidget(self._remote_input)
        self._connect_btn = QPushButton("连接")
        self._connect_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 6px 20px; }"
        )
        self._connect_btn.clicked.connect(self._on_connect)
        row.addWidget(self._connect_btn)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        self._device_list_btn = QPushButton("设备列表")
        self._device_list_btn.clicked.connect(self._open_device_list)
        self._disconnect_btn = QPushButton("断开")
        self._disconnect_btn.setEnabled(False)
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        row2.addWidget(self._device_list_btn)
        row2.addWidget(self._disconnect_btn)
        layout.addLayout(row2)
        return g

    def _build_actions(self) -> QGroupBox:
        g = QGroupBox("远程会话")
        layout = QVBoxLayout(g)
        self._remote_btn = QPushButton("远程桌面")
        self._remote_btn.setEnabled(False)
        self._remote_btn.clicked.connect(self._open_remote_view)
        layout.addWidget(self._remote_btn)
        self._file_btn = QPushButton("远程文件管理")
        self._file_btn.clicked.connect(self._open_file_manager)
        layout.addWidget(self._file_btn)
        self._terminal_btn = QPushButton("远程终端 (CMD)")
        self._terminal_btn.clicked.connect(self._open_terminal)
        layout.addWidget(self._terminal_btn)
        return g

    def _build_session_tools(self) -> QGroupBox:
        g = QGroupBox("会话工具")
        layout = QVBoxLayout(g)
        self._chat_btn = QPushButton("聊天消息")
        self._chat_btn.clicked.connect(self._open_chat)
        layout.addWidget(self._chat_btn)
        self._clipboard_btn = QPushButton("同步剪贴板")
        self._clipboard_btn.clicked.connect(self._on_sync_clipboard)
        layout.addWidget(self._clipboard_btn)
        self._record_btn = QPushButton("开始录制")
        self._record_btn.setCheckable(True)
        self._record_btn.clicked.connect(self._on_toggle_recording)
        layout.addWidget(self._record_btn)
        self._privacy_btn = QPushButton("隐私屏")
        self._privacy_btn.setCheckable(True)
        self._privacy_btn.clicked.connect(self._on_toggle_privacy)
        layout.addWidget(self._privacy_btn)
        return g

    def _build_ai_tools(self) -> QGroupBox:
        g = QGroupBox("AI 助手")
        layout = QVBoxLayout(g)
        self._ai_ocr_btn = QPushButton("屏幕 OCR 识别")
        self._ai_ocr_btn.clicked.connect(self._on_ai_ocr)
        layout.addWidget(self._ai_ocr_btn)
        self._ai_ask_btn = QPushButton("AI 屏幕问答")
        self._ai_ask_btn.clicked.connect(self._on_ai_ask)
        layout.addWidget(self._ai_ask_btn)
        self._ai_translate_btn = QPushButton("AI 翻译")
        self._ai_translate_btn.clicked.connect(self._on_ai_translate)
        layout.addWidget(self._ai_translate_btn)
        self._settings_btn = QPushButton("设置")
        self._settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(self._settings_btn)
        return g

    def _build_recent(self) -> QGroupBox:
        g = QGroupBox("最近连接")
        layout = QVBoxLayout(g)
        self._recent_label = QLabel("暂无记录")
        self._recent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._recent_label.setStyleSheet("color: #888;")
        layout.addWidget(self._recent_label)
        return g

    def _on_connect(self) -> None:
        remote_id = self._remote_input.text().strip()
        if not remote_id:
            self._status.showMessage("请输入远程设备 ID", 3000)
            return
        self._active_session_id = remote_id
        prog = self._recent_label
        prog.setText(f"上次连接: {remote_id}")
        prog.setStyleSheet("color: #4CAF50;")
        self._remote_btn.setEnabled(True)
        self._disconnect_btn.setEnabled(True)
        self._status.showMessage(f"已连接到 {remote_id}", 5000)

    def _on_disconnect(self) -> None:
        self._active_session_id = None
        self._remote_btn.setEnabled(False)
        self._disconnect_btn.setEnabled(False)
        self._status.showMessage("已断开连接", 3000)

    def _open_device_list(self) -> None:
        from uniqoremote.ui.windows.devices import DeviceListDialog

        dlg = DeviceListDialog(self)
        if dlg.exec():
            selected = dlg.selected_device_id()
            if selected:
                self._remote_input.setText(selected)

    def _open_remote_view(self) -> None:
        from PySide6.QtWidgets import QDialog

        from uniqoremote.ui.windows.remote import RemoteView

        dlg = QDialog(self)
        dlg.setWindowTitle(f"远程桌面 - {self._active_session_id}")
        dlg.resize(1024, 768)
        view = RemoteView()
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)
        dlg.exec()

    def _open_file_manager(self) -> None:
        from uniqoremote.ui.windows.file_manager import FileManagerDialog

        FileManagerDialog(self).exec()

    def _open_terminal(self) -> None:
        from uniqoremote.ui.windows.terminal import TerminalDialog

        TerminalDialog(self).exec()

    def _open_chat(self) -> None:
        from uniqoremote.ui.windows.chat import ChatDialog

        ChatDialog(self).exec()

    def _on_sync_clipboard(self) -> None:
        try:
            from uniqoremote.session.clipboard import ClipboardManager

            mgr = ClipboardManager()
            local = mgr.get_text()
            mgr.sync(local)
            self._status.showMessage("剪贴板已同步", 2000)
        except Exception as e:
            self._status.showMessage(f"剪贴板同步失败: {e}", 3000)

    def _on_toggle_recording(self, checked: bool) -> None:
        if checked:
            self._record_btn.setText("停止录制")
            self._record_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; }"
            )
            self._status.showMessage("录制已开始", 2000)
        else:
            self._record_btn.setText("开始录制")
            self._record_btn.setStyleSheet("")
            self._status.showMessage("录制已停止", 2000)

    def _on_toggle_privacy(self, checked: bool) -> None:
        self._privacy_active = checked
        if checked:
            self._privacy_btn.setText("关闭隐私屏")
            self._privacy_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; }"
            )
            self._status.showMessage("隐私屏已开启", 2000)
        else:
            self._privacy_btn.setText("隐私屏")
            self._privacy_btn.setStyleSheet("")
            self._status.showMessage("隐私屏已关闭", 2000)

    def _open_settings(self) -> None:
        from uniqoremote.ui.windows.settings import SettingsDialog

        if SettingsDialog(self._config, self).exec():
            self._status.showMessage("设置已保存", 2000)

    def _on_ai_ocr(self) -> None:
        if self._ai_client is None:
            self._status.showMessage("AI功能未配置 (设置 UNIQOREMOTE_AI_API_KEY)", 3000)
            return
        self._status.showMessage("正在OCR识别...", 5000)

    def _on_ai_ask(self) -> None:
        if self._ai_client is None:
            self._status.showMessage("AI功能未配置 (设置 UNIQOREMOTE_AI_API_KEY)", 3000)
            return
        self._status.showMessage("正在AI分析...", 5000)

    def _on_ai_translate(self) -> None:
        if self._ai_client is None:
            self._status.showMessage("AI功能未配置 (设置 UNIQOREMOTE_AI_API_KEY)", 3000)
            return
        self._status.showMessage("正在翻译...", 5000)

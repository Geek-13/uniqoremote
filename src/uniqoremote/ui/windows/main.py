from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
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

SIDEBAR_WIDTH = 200
STYLE = """
QMainWindow {
    background-color: #1e1e2e;
}
QWidget {
    color: #cdd6f4;
    font-size: 14px;
}
QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #cdd6f4;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QLineEdit {
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: #313244;
    color: #cdd6f4;
}
QLineEdit:focus {
    border-color: #89b4fa;
}
QPushButton {
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    background-color: #45475a;
    color: #cdd6f4;
}
QPushButton:hover {
    background-color: #585b70;
}
QPushButton:pressed {
    background-color: #313244;
}
QPushButton:disabled {
    background-color: #313244;
    color: #6c7086;
}
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    border-top: 1px solid #313244;
}
QLabel#logo {
    font-size: 22px;
    font-weight: bold;
    color: #89b4fa;
}
QLabel#device_id {
    font-size: 15px;
    font-weight: bold;
    color: #a6e3a1;
    background-color: #313244;
    border-radius: 6px;
    padding: 8px 12px;
}
"""


class MainWindow(QMainWindow):
    def __init__(
        self,
        config: Config,
        session_mgr: SessionManager | None = None,
        decoder: FfmpegDecoder | None = None,
        agent_client: IpcClient | None = None,
        ai_client: DeepSeekClient | None = None,
        router: MessageRouter | None = None,
        stun_client: Any = None,
        p2p_transport: Any = None,
        relay_transport: Any = None,
    ) -> None:
        super().__init__()
        self._config = config
        self._session_mgr = session_mgr
        self._decoder = decoder
        self._agent_client = agent_client
        self._ai_client = ai_client
        self._router = router
        self._stun_client = stun_client
        self._p2p_transport = p2p_transport
        self._relay_transport = relay_transport
        self._active_session_id: str | None = None
        self.setStyleSheet(STYLE)

        self.setWindowTitle("UniqoRemote")
        self.resize(860, 600)

        self._register_with_server()

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_home_page())
        self._stack.addWidget(self._build_placeholder("远程文件管理"))
        self._stack.addWidget(self._build_placeholder("远程终端"))
        self._stack.addWidget(self._build_session_tools())
        self._stack.addWidget(self._build_ai_tools())
        from uniqoremote.ui.windows.settings import SettingsPage

        self._stack.addWidget(SettingsPage(config))
        root.addWidget(self._stack, 1)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage(
            f"设备名: {config.identity.device_name} | ID: {config.identity.device_id}"
        )

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setStyleSheet("background-color: #181825; border-right: 1px solid #313244;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        logo = QLabel("UniqoRemote")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        layout.addSpacing(16)

        nav_items = [
            ("🏠  远程协助", 0),
            ("📁  文件管理", 1),
            ("🖥  远程终端", 2),
            ("🔧  会话工具", 3),
            ("🤖  AI 助手", 4),
            ("⚙  设置", 5),
        ]
        self._nav_btns: list[QPushButton] = []
        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setStyleSheet(_nav_style(False))
            btn.clicked.connect(lambda checked, i=idx: self._stack.setCurrentIndex(i))
            layout.addWidget(btn)
            self._nav_btns.append(btn)

        _set_nav_active(self._nav_btns[0], self._nav_btns)

        layout.addStretch()

        ver = QLabel("v0.2.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("color: #6c7086; font-size: 12px;")
        layout.addWidget(ver)

        return sidebar

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        greeting = QLabel("欢迎使用 UniqoRemote")
        greeting.setStyleSheet("font-size: 20px; font-weight: bold; color: #cdd6f4;")
        layout.addWidget(greeting)

        id_card = QFrame()
        id_card.setStyleSheet(
            "QFrame { background-color: #313244; border-radius: 10px; padding: 16px; }"
        )
        id_layout = QVBoxLayout(id_card)
        id_layout.addWidget(QLabel("本机设备 ID"))
        device_id = QLabel(self._config.identity.device_id)
        device_id.setObjectName("device_id")
        device_id.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        id_layout.addWidget(device_id)
        id_layout.addWidget(QLabel(f"设备名: {self._config.identity.device_name}"))
        layout.addWidget(id_card)

        connect_card = QFrame()
        connect_card.setStyleSheet(
            "QFrame { background-color: #313244; border-radius: 10px; padding: 16px; }"
        )
        cl = QVBoxLayout(connect_card)
        cl.addWidget(QLabel("连接远程设备"))
        row = QHBoxLayout()
        self._remote_input = QLineEdit()
        self._remote_input.setPlaceholderText("输入对方设备 ID")
        self._remote_input.setMaxLength(12)
        row.addWidget(self._remote_input, 1)
        self._connect_btn = QPushButton("连接")
        self._connect_btn.setStyleSheet(
            "QPushButton { background-color: #a6e3a1; color: #1e1e2e;"
            " font-weight: bold; padding: 10px 24px; }"
            "QPushButton:hover { background-color: #94e2d5; }"
        )
        self._connect_btn.clicked.connect(self._on_connect)
        row.addWidget(self._connect_btn)
        cl.addLayout(row)
        self._disconnect_btn = QPushButton("断开连接")
        self._disconnect_btn.setEnabled(False)
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        cl.addWidget(self._disconnect_btn)
        layout.addWidget(connect_card)

        layout.addStretch()
        return page

    def _build_session_tools(self) -> QWidget:
        return self._build_tool_page(
            "会话工具",
            [
                ("远程桌面", self._open_remote_view, True),
                ("聊天消息", self._open_chat, False),
                ("同步剪贴板", self._on_sync_clipboard, False),
                ("开始录制", self._on_toggle_recording, False),
                ("隐私屏", self._on_toggle_privacy, False),
            ],
        )

    def _build_ai_tools(self) -> QWidget:
        return self._build_tool_page(
            "AI 助手",
            [
                ("屏幕 OCR 识别", self._on_ai_ocr, False),
                ("AI 屏幕问答", self._on_ai_ask, False),
                ("AI 翻译", self._on_ai_translate, False),
            ],
        )

    def _build_tool_page(self, title: str, items: list[tuple[str, callable, bool]]) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)
        header = QLabel(title)
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)
        for text, handler, enabled in items:
            btn = QPushButton(text)
            btn.setMinimumHeight(48)
            btn.setEnabled(enabled)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        layout.addStretch()
        return page

    def _build_placeholder(self, title: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        h = QLabel(title)
        h.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(h)
        p = QLabel("此功能将在连接远程设备后可用")
        p.setStyleSheet("color: #6c7086; font-size: 15px;")
        layout.addWidget(p)
        layout.addStretch()
        return page

    def _on_connect(self) -> None:
        rid = self._remote_input.text().strip()
        if not rid:
            self._status.showMessage("请输入远程设备 ID", 3000)
            return

        server_str = self._config.network.rendezvous_server
        if not server_str:
            self._status.showMessage("请先在设置中配置服务器地址", 5000)
            return

        host, port_str = server_str.rsplit(":", 1)
        server_addr = (host, int(port_str))

        import asyncio

        self._active_session_id = rid
        self._status.showMessage("正在连接...", 0)

        async def _do_connect() -> None:
            try:
                await self._session_mgr.connect(
                    remote_device_id=rid,
                    server_addr=server_addr,
                    stun=self._stun_client,
                    p2p=self._p2p_transport,
                    relay=self._relay_transport,
                    config_device_id=self._config.identity.device_id,
                )
                self._disconnect_btn.setEnabled(True)
                self._status.showMessage(f"已连接到 {rid}", 5000)
                for i in range(1, self._stack.count()):
                    w = self._stack.widget(i)
                    if w:
                        self._enable_buttons(w, True)
            except Exception as e:
                import traceback

                traceback.print_exc()
                self._status.showMessage(f"连接失败: {e}", 8000)

        asyncio.get_running_loop().create_task(_do_connect())

    def _on_disconnect(self) -> None:
        import asyncio
        import contextlib

        async def _do_disconnect() -> None:
            with contextlib.suppress(Exception):
                await self._session_mgr.disconnect()

        asyncio.get_running_loop().create_task(_do_disconnect())
        self._active_session_id = None
        self._disconnect_btn.setEnabled(False)
        self._status.showMessage("已断开连接", 3000)
        for i in range(1, self._stack.count()):
            w = self._stack.widget(i)
            if w:
                self._enable_buttons(w, False)

    def _enable_buttons(self, widget: QWidget, enabled: bool) -> None:
        for child in widget.findChildren(QPushButton):
            if child is not self._disconnect_btn:
                child.setEnabled(enabled)

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

    def _open_chat(self) -> None:
        from uniqoremote.ui.windows.chat import ChatDialog

        ChatDialog(self).exec()

    def _open_file_manager(self) -> None:
        from uniqoremote.ui.windows.file_manager import FileManagerDialog

        FileManagerDialog(self).exec()

    def _open_terminal(self) -> None:
        from uniqoremote.ui.windows.terminal import TerminalDialog

        TerminalDialog(self).exec()

    def _on_sync_clipboard(self) -> None:
        self._status.showMessage("剪贴板已同步", 2000)

    def _on_toggle_recording(self) -> None:
        self._status.showMessage("录制功能", 2000)

    def _on_toggle_privacy(self) -> None:
        self._status.showMessage("隐私屏已切换", 2000)

    def _on_ai_ocr(self) -> None:
        self._status.showMessage("OCR 识别功能", 3000)

    def _on_ai_ask(self) -> None:
        self._status.showMessage("AI 问答功能", 3000)

    def _on_ai_translate(self) -> None:
        self._status.showMessage("AI 翻译功能", 3000)

    def _register_with_server(self) -> None:
        server_str = self._config.network.rendezvous_server
        if not server_str:
            return

        import asyncio

        async def _do_register() -> None:
            from uniqoremote.core.crypto import generate_key_pair, generate_nonce
            from uniqoremote.core.events import MessageType
            from uniqoremote.core.protocol import encode_frame
            from uniqoremote.session.handshake import generate_hello_payload
            from uniqoremote.transport.udp import UdpTransport

            try:
                host, port_str = server_str.rsplit(":", 1)
                server_addr = (host, int(port_str))
                sk, pk = generate_key_pair()
                nonce = generate_nonce()
                hello = generate_hello_payload(self._config.identity.device_id, pk, "1.0.0", nonce)
                frame = encode_frame(MessageType.HELLO, hello)
                udp = UdpTransport()
                await udp.bind(("0.0.0.0", 0))
                await udp.connect(server_addr)
                await udp.send(frame)
            except Exception:
                pass

        asyncio.get_running_loop().create_task(_do_register())


def _nav_style(active: bool) -> str:
    if active:
        return (
            "QPushButton { background-color: #45475a; color: #89b4fa; font-weight: bold; "
            "text-align: left; padding: 10px 14px; border-radius: 6px; }"
        )
    return (
        "QPushButton { background-color: transparent; color: #a6adc8; "
        "text-align: left; padding: 10px 14px; border-radius: 6px; }"
        "QPushButton:hover { background-color: #313244; color: #cdd6f4; }"
    )


def _set_nav_active(active_btn: QPushButton, all_btns: list[QPushButton]) -> None:
    for btn in all_btns:
        btn.setStyleSheet(_nav_style(btn is active_btn))

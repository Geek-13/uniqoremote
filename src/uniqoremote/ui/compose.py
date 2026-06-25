from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from uniqoremote.core.config import Config, load_config

if TYPE_CHECKING:
    from uniqoremote.ui.windows.main import MainWindow


def create_app(config_path: Path | None = None) -> MainWindow:
    if config_path is None:
        config_path = Path("config.toml")
    config = load_config(config_path)
    _start_agent()

    from uniqoremote.pipeline.encoder.ffmpeg import FfmpegDecoder
    from uniqoremote.session.manager import SessionManager
    from uniqoremote.transport.p2p import P2PTransport, StunClient
    from uniqoremote.transport.tcp import TcpTransport
    from uniqoremote.ui.ipc_client import IpcClient
    from uniqoremote.ui.windows.main import MainWindow

    session_mgr = SessionManager()
    decoder = FfmpegDecoder()
    agent_client = IpcClient(port=9510)
    stun = StunClient()
    p2p_transport = P2PTransport()
    relay_transport = TcpTransport()
    ai_client = _create_ai_client(config)

    return MainWindow(
        config=config,
        session_mgr=session_mgr,
        decoder=decoder,
        agent_client=agent_client,
        ai_client=ai_client,
        stun_client=stun,
        p2p_transport=p2p_transport,
        relay_transport=relay_transport,
    )


def _create_ai_client(config: Config):
    if config.ai.enabled and config.ai.api_key:
        from uniqoremote.ai.client import DeepSeekClient

        return DeepSeekClient(model=config.ai.model)
    return None


def _start_agent() -> None:
    try:
        import ctypes

        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, "-m uniqoremote.agent", None, 1
        )
        if ret <= 32:
            subprocess.Popen(
                [sys.executable, "-m", "uniqoremote.agent"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        subprocess.Popen(
            [sys.executable, "-m", "uniqoremote.agent"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

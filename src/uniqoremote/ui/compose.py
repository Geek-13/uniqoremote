from __future__ import annotations

from pathlib import Path

from uniqoremote.core.config import Config, load_config

try:
    from uniqoremote.core.channel import EncryptedChannel
    from uniqoremote.core.crypto import generate_key_pair
    from uniqoremote.pipeline.encoder.ffmpeg import FfmpegDecoder, FfmpegEncoder
    from uniqoremote.session.manager import SessionManager
    from uniqoremote.session.router import MessageRouter
    from uniqoremote.transport.udp import UdpTransport
    from uniqoremote.ui.ipc_client import IpcClient
    from uniqoremote.ui.windows.main import MainWindow

    HAS_FULL_DEPS = True
except ImportError:
    HAS_FULL_DEPS = False


def create_app(config_path: Path | None = None) -> MainWindow:
    if config_path is None:
        config_path = Path("config.toml")
    config = load_config(config_path)

    if HAS_FULL_DEPS:
        key_pair = generate_key_pair()
        transport = UdpTransport()
        channel = EncryptedChannel(transport, derive_key(key_pair))
        router = MessageRouter(channel)
        session_mgr = SessionManager()
        decoder = FfmpegDecoder()
        agent_client = IpcClient(port=9510)
        ai_client = _create_ai_client(config)
        return MainWindow(config, session_mgr, decoder, agent_client, ai_client, router)

    return MainWindow(config)


def _create_ai_client(config: Config):
    if config.ai.enabled:
        from uniqoremote.ai.client import DeepSeekClient

        return DeepSeekClient(model=config.ai.model)
    return None


def derive_key(key_pair):
    from uniqoremote.core.crypto import derive_session_key, generate_nonce

    sk_a, pk_a = key_pair
    sk_b, pk_b = generate_key_pair()
    return derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce())

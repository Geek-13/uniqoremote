from __future__ import annotations

import tempfile
import time
from pathlib import Path

from uniqoremote.agent.ipc_server import IpcClient as _IpcClient

_PORT_FILE = Path(tempfile.gettempdir()) / "uniqoremote_agent.port"


class IpcClient(_IpcClient):
    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        discovered = port
        if port == 0:
            discovered = self._wait_port()
        super().__init__(host=host, port=discovered)

    @staticmethod
    def _wait_port() -> int:
        for _ in range(30):
            if _PORT_FILE.exists():
                try:
                    return int(_PORT_FILE.read_text().strip())
                except (ValueError, OSError):
                    pass
            time.sleep(0.5)
        return 9510

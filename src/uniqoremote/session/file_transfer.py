from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uniqoremote.session.manager import SessionManager

CHUNK_SIZE = 65536


class FileTransfer:
    def __init__(self, session_mgr: SessionManager) -> None:
        self._session_mgr = session_mgr

    async def send(self, filepath: str) -> None:
        path = Path(filepath)
        if not path.is_file():
            return
        name = path.name
        size = path.stat().st_size
        with path.open("rb") as f:
            offset = 0
            while offset < size:
                chunk = f.read(CHUNK_SIZE)
                await self._session_mgr.send_input(
                    {
                        "type": "file_chunk",
                        "filename": name,
                        "offset": offset,
                        "size": len(chunk),
                        "total_size": size,
                        "data": chunk,
                    }
                )
                offset += len(chunk)

    @staticmethod
    def on_chunk(payload: dict, save_dir: str) -> None:
        name = payload["filename"]
        data = payload.get("data", b"")
        path = Path(save_dir) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as f:
            f.write(data)

from __future__ import annotations

from typing import Any

import fastapi  # type: ignore[import-not-found]
import uvicorn  # type: ignore[import-not-found]

from uniqoremote.server.rendezvous.manager import RendezvousManager


class AdminWebPanel:
    def __init__(self, rendezvous: RendezvousManager) -> None:
        self._rendezvous = rendezvous

    def get_status(self) -> dict[str, Any]:
        online = self._rendezvous.list_online_devices()
        return {
            "online_devices": len(online),
            "total_devices": len(self._rendezvous._devices),
            "devices": [{"id": d.device_id, "version": d.version, "addr": d.addr} for d in online],
        }

    async def start(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        app = fastapi.FastAPI(title="UniqoRemote Admin")

        @app.get("/status")  # type: ignore[untyped-decorator]
        async def status() -> dict[str, Any]:
            return self.get_status()

        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

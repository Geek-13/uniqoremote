"""UniqoRemote admin web panel. Requires: pip install fastapi uvicorn"""

from __future__ import annotations

from uniqoremote.server.rendezvous.manager import RendezvousManager


class AdminWebPanel:
    def __init__(self, rendezvous: RendezvousManager) -> None:
        self._rendezvous = rendezvous

    def get_status(self) -> dict:
        online = self._rendezvous.list_online_devices()
        return {
            "online_devices": len(online),
            "total_devices": len(self._rendezvous._devices),
            "devices": [{"id": d.device_id, "version": d.version, "addr": d.addr} for d in online],
        }

    async def start(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        try:
            import uvicorn
            from fastapi import FastAPI

            app = FastAPI(title="UniqoRemote Admin")

            @app.get("/status")
            async def status():
                return self.get_status()

            config = uvicorn.Config(app, host=host, port=port, log_level="info")
            server = uvicorn.Server(config)
            await server.serve()
        except ImportError:
            pass

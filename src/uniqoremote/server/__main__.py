"""UniqoRemote Server — rendezvous and relay."""

from __future__ import annotations

import asyncio
import signal

from uniqoremote.core.logging import configure_logging
from uniqoremote.server.relay.relay import RelayServer
from uniqoremote.server.rendezvous.manager import RendezvousManager


async def main() -> None:
    logger = configure_logging(level="INFO")
    logger.info("server_starting")  # type: ignore[attr-defined]

    rendezvous = RendezvousManager()
    relay = RelayServer()

    relay_port = await relay.start("0.0.0.0", 21117)
    logger.info("relay_listening", port=relay_port)  # type: ignore[attr-defined]

    from uniqoremote.server.admin.web import AdminWebPanel

    admin = AdminWebPanel(rendezvous)

    stop = asyncio.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    logger.info("server_ready")  # type: ignore[attr-defined]
    await stop.wait()

    await relay.stop()
    logger.info("server_stopped")  # type: ignore[attr-defined]


if __name__ == "__main__":
    asyncio.run(main())

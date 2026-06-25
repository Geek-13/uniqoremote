from __future__ import annotations

import asyncio
import signal
from typing import Any

from uniqoremote.core.logging import configure_logging
from uniqoremote.server.protocol import ProtocolServer


async def main() -> None:
    logger: Any = configure_logging(level="INFO")
    logger.info("server_starting")

    server = ProtocolServer()
    rendezvous_port = await server.start("0.0.0.0", 21116)
    logger.info("rendezvous_listening", port=rendezvous_port)
    relay_port = await server.start_relay("0.0.0.0", 21117)
    logger.info("relay_listening", port=relay_port)

    logger.info("server_ready")

    stop = asyncio.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    await stop.wait()
    await server.stop()
    logger.info("server_stopped")


if __name__ == "__main__":
    asyncio.run(main())

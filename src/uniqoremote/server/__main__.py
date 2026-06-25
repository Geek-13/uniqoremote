"""UniqoRemote Server — rendezvous and relay."""

from __future__ import annotations

import asyncio
import signal

from uniqoremote.core.logging import configure_logging


async def main() -> None:
    logger = configure_logging(level="INFO")
    logger.info("server_starting")  # type: ignore[attr-defined]
    server = await asyncio.start_server(
        lambda r, w: asyncio.create_task(_handle(r, w, logger)),  # type: ignore[arg-type]
        "0.0.0.0",
        21116,
    )
    addr = server.sockets[0].getsockname()
    logger.info("server_listening", host=addr[0], port=addr[1])  # type: ignore[attr-defined]

    stop = asyncio.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    await stop.wait()
    server.close()
    await server.wait_closed()
    logger.info("server_stopped")


async def _handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, logger) -> None:
    import contextlib

    addr = writer.get_extra_info("peername")
    logger.info("server_connection", client=addr)
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception:
        logger.exception("server_connection_error")
    finally:
        with contextlib.suppress(Exception):
            writer.close()


if __name__ == "__main__":
    asyncio.run(main())

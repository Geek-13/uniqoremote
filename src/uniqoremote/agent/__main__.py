"""UniqoRemote Agent — screen capture and input injection service."""

from __future__ import annotations

import asyncio
import signal

from uniqoremote.agent.ipc_server import IpcServer
from uniqoremote.core.logging import configure_logging


async def main() -> None:
    logger = configure_logging(level="INFO")
    logger.info("agent_starting")  # type: ignore[attr-defined]
    server = IpcServer(port=9510)
    actual_port = await server.start()
    logger.info("agent_listening", port=actual_port)  # type: ignore[attr-defined]

    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, lambda *_: _signal_handler())
    signal.signal(signal.SIGTERM, lambda *_: _signal_handler())

    while not stop_event.is_set():
        try:
            conn = await asyncio.wait_for(server.accept(), timeout=1.0)
            logger.info("agent_client_connected")
            asyncio.create_task(_handle_client(conn, logger))
        except TimeoutError:
            continue

    await server.stop()
    logger.info("agent_stopped")


async def _handle_client(conn, logger) -> None:
    import contextlib

    try:
        while True:
            msg_type, payload = await conn.recv()
            logger.info("agent_msg_received", type=msg_type)  # type: ignore[attr-defined]
            if msg_type == "START_CAPTURE":
                logger.info("capture_started", params=payload)  # type: ignore[attr-defined]
                await conn.send("FRAME", {"status": "capture_started"})
            elif msg_type == "STOP_CAPTURE":
                logger.info("capture_stopped")
                await conn.send("FRAME", {"status": "capture_stopped"})
            elif msg_type == "INJECT_INPUT":
                logger.debug("input_injected", input=payload)
            elif msg_type == "HEARTBEAT":
                await conn.send("HEARTBEAT", {"ts": payload.get("ts", 0)})
    except Exception:
        logger.exception("agent_client_error")
    finally:
        with contextlib.suppress(Exception):
            await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

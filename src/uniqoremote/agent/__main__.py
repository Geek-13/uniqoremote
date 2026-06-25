from __future__ import annotations

import asyncio
import signal
import tempfile
from pathlib import Path
from typing import Any

from uniqoremote.agent.ipc_server import IpcConnection, IpcServer
from uniqoremote.core.logging import configure_logging

_PORT_FILE = Path(tempfile.gettempdir()) / "uniqoremote_agent.port"


async def main() -> None:
    logger: Any = configure_logging(level="INFO")
    logger.info("agent_starting")
    _PORT_FILE.unlink(missing_ok=True)
    actual_port = 0
    for port in (9510, 0):
        server = IpcServer(port=port)
        try:
            actual_port = await server.start()
            break
        except OSError:
            continue
    _PORT_FILE.write_text(str(actual_port))
    logger.info("agent_listening", port=actual_port)

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
    _PORT_FILE.unlink(missing_ok=True)
    logger.info("agent_stopped")


async def _handle_client(conn: IpcConnection, logger: Any) -> None:
    import contextlib

    from uniqoremote.agent.pipeline_runner import PipelineRunner
    from uniqoremote.input.controller import InputController
    from uniqoremote.pipeline.capturer.gdi import GdiCapturer
    from uniqoremote.pipeline.encoder.ffmpeg import FfmpegEncoder

    runner: PipelineRunner | None = None
    input_ctrl = InputController()
    frame_queue: asyncio.Queue[list[bytes]] = asyncio.Queue()

    async def _push_frames() -> None:
        while True:
            try:
                frames = await asyncio.wait_for(frame_queue.get(), timeout=1.0)
                for data in frames:
                    await conn.send("FRAME", {"data": data, "size": len(data)})
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    try:
        while True:
            msg_type, payload = await conn.recv()
            logger.info("agent_msg_received", type=msg_type)

            if msg_type == "START_CAPTURE":
                width = int(payload.get("width", 1920))
                height = int(payload.get("height", 1080))
                fps = int(payload.get("fps", 30))
                codec = str(payload.get("codec", "h264"))
                capturer = GdiCapturer()
                encoder = FfmpegEncoder()
                if not encoder.is_available:
                    await conn.send("ERROR", {"code": "FFMPEG_NOT_FOUND"})
                    continue
                runner = PipelineRunner(capturer, encoder, frame_queue)
                await runner.start(width, height, fps, codec)
                await conn.send("FRAME", {"status": "capture_started"})
                asyncio.create_task(_push_frames())

            elif msg_type == "STOP_CAPTURE":
                if runner:
                    await runner.stop()
                    runner = None
                await conn.send("FRAME", {"status": "capture_stopped"})

            elif msg_type == "INJECT_INPUT":
                await input_ctrl.handle(payload)

            elif msg_type == "HEARTBEAT":
                await conn.send("HEARTBEAT", {"ts": payload.get("ts", 0)})
    except Exception:
        logger.exception("agent_client_error")
    finally:
        if runner:
            with contextlib.suppress(Exception):
                await runner.stop()
        with contextlib.suppress(Exception):
            await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

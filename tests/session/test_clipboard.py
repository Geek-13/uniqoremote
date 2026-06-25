from __future__ import annotations

import pytest

from uniqoremote.session.clipboard import ClipboardSync


@pytest.mark.asyncio
async def test_clipboard_sync_start_stop() -> None:
    captured: list[str] = []

    def handler(text: str) -> None:
        captured.append(text)

    sync = ClipboardSync(handler)
    await sync.start()
    assert sync._running
    await sync.stop()
    assert not sync._running


def test_on_remote_text() -> None:
    sent: list[str] = []

    def handler(text: str) -> None:
        sent.append(text)

    sync = ClipboardSync(handler)
    sync.on_remote_text("hello")
    assert sync._last_text == "hello"

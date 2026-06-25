from __future__ import annotations

from uniqoremote.session.clipboard import ClipboardData


class TestClipboardData:
    def test_default_values(self) -> None:
        data = ClipboardData()
        assert data.text == ""
        assert data.format == "text/plain"

    def test_custom_text(self) -> None:
        data = ClipboardData(text="hello", format="text/html")
        assert data.text == "hello"
        assert data.format == "text/html"

    def test_sync_logic(self) -> None:
        local = ClipboardData(text="local_text")
        remote = ClipboardData(text="remote_text")
        assert local.text != remote.text
        assert remote.text == "remote_text"

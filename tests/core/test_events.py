from __future__ import annotations

from dataclasses import asdict

from uniqoremote.core.events import (
    ConnectionEvent,
    ConnectionState,
    FrameEvent,
    InputEvent,
    InputEventType,
)


class TestConnectionEvent:
    def test_creates_connection_event(self) -> None:
        event = ConnectionEvent(state=ConnectionState.CONNECTING, device_id="abc123")
        assert event.state == ConnectionState.CONNECTING
        assert event.device_id == "abc123"

    def test_serializes_roundtrip(self) -> None:
        import msgpack

        event = ConnectionEvent(state=ConnectionState.ACTIVE, device_id="xyz")
        packed = msgpack.packb(asdict(event))
        unpacked = msgpack.unpackb(packed)
        assert unpacked["state"] == "active"
        assert unpacked["device_id"] == "xyz"


class TestInputEvent:
    def test_creates_key_event(self) -> None:
        event = InputEvent(type=InputEventType.KEY_DOWN, data={"key": 0x41})
        assert event.type == InputEventType.KEY_DOWN
        assert event.data["key"] == 0x41

    def test_creates_mouse_event(self) -> None:
        event = InputEvent(type=InputEventType.MOUSE_MOVE, data={"x": 100, "y": 200})
        assert event.type == InputEventType.MOUSE_MOVE
        assert event.data["x"] == 100


class TestFrameEvent:
    def test_creates_frame_event(self) -> None:
        data = b"\x00" * 100
        event = FrameEvent(width=1920, height=1080, data=data, pts=0.0)
        assert event.width == 1920
        assert event.height == 1080
        assert event.data == data
        assert event.pts == 0.0

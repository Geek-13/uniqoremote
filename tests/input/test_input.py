from __future__ import annotations

from uniqoremote.input.base import InputController, InputEvent, InputEventType


class TestInputEvent:
    def test_key_event(self) -> None:
        event = InputEvent(type=InputEventType.KEY_DOWN, data={"key": 0x41})
        assert event.type == InputEventType.KEY_DOWN
        assert event.data["key"] == 0x41

    def test_mouse_event(self) -> None:
        event = InputEvent(type=InputEventType.MOUSE_MOVE, data={"x": 100, "y": 200})
        assert event.type == InputEventType.MOUSE_MOVE

    def test_abc_cannot_instantiate(self) -> None:
        import pytest

        with pytest.raises(TypeError):
            InputController()  # type: ignore[abstract]

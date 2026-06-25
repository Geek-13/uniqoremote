from __future__ import annotations

from uniqoremote.session.privacy import PrivacyMode, PrivacyScreen


class TestPrivacyScreen:
    def test_default_off(self) -> None:
        ps = PrivacyScreen()
        assert ps.mode == PrivacyMode.OFF
        assert ps.is_active is False

    def test_enable_black_screen(self) -> None:
        ps = PrivacyScreen()
        ps.enable(PrivacyMode.BLACK_SCREEN)
        assert ps.mode == PrivacyMode.BLACK_SCREEN
        assert ps.is_active is True

    def test_disable(self) -> None:
        ps = PrivacyScreen()
        ps.enable()
        ps.disable()
        assert ps.mode == PrivacyMode.OFF
        assert ps.is_active is False

    def test_to_control_message(self) -> None:
        ps = PrivacyScreen()
        ps.enable(PrivacyMode.BLACK_SCREEN)
        msg = ps.to_control_message()
        assert msg["privacy_mode"] == "black_screen"
        assert msg["enabled"] is True

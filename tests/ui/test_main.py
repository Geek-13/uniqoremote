from __future__ import annotations

from PySide6.QtWidgets import QLabel

from uniqoremote.core.config import Config
from uniqoremote.ui.windows.main import MainWindow


class TestMainWindow:
    def test_window_title(self, qtbot) -> None:
        config = Config()
        window = MainWindow(config)
        qtbot.addWidget(window)
        assert window.windowTitle() == "UniqoRemote"

    def test_device_id_displayed(self, qtbot) -> None:
        config = Config()
        expected_id = config.identity.device_id
        window = MainWindow(config)
        qtbot.addWidget(window)
        labels = window.findChildren(QLabel)
        found = any(expected_id in lbl.text() for lbl in labels if lbl.text())
        assert found

    def test_device_name_displayed(self, qtbot) -> None:
        config = Config()
        config.identity.device_name = "TestPC"
        window = MainWindow(config)
        qtbot.addWidget(window)
        assert "TestPC" in window._status.currentMessage()

    def test_connect_empty_id_shows_warning(self, qtbot) -> None:
        config = Config()
        window = MainWindow(config)
        qtbot.addWidget(window)
        window._remote_input.clear()
        window._on_connect()
        assert "请输入" in window._status.currentMessage()


class TestCompose:
    def test_create_app_returns_main_window(self) -> None:
        from uniqoremote.ui.compose import create_app

        window = create_app()
        assert isinstance(window, MainWindow)
        window.close()

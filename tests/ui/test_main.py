from __future__ import annotations

from uniqoremote.core.config import Config
from uniqoremote.ui.windows.main import MainWindow


class TestMainWindow:
    def test_window_title(self, qtbot) -> None:
        config = Config()
        window = MainWindow(config)
        qtbot.addWidget(window)
        assert window.windowTitle() == "UniqoRemote"

    def test_device_label_shows_id(self, qtbot) -> None:
        config = Config()
        expected_id = config.identity.device_id
        window = MainWindow(config)
        qtbot.addWidget(window)
        assert expected_id in window._device_label.text()

    def test_window_resize(self, qtbot) -> None:
        config = Config()
        window = MainWindow(config)
        qtbot.addWidget(window)
        assert window.width() == 800
        assert window.height() == 600


class TestCompose:
    def test_create_app_returns_main_window(self) -> None:
        from uniqoremote.ui.compose import create_app

        window = create_app()
        assert isinstance(window, MainWindow)
        window.close()

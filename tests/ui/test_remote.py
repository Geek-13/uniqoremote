from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QMainWindow

from uniqoremote.ui.windows.remote import RemoteView


class TestRemoteView:
    def test_placeholder_text(self, qtbot) -> None:
        window = QMainWindow()
        qtbot.addWidget(window)
        view = RemoteView()
        window.setCentralWidget(view)
        assert "等待连接" in view.findChild(type(view._display)).text()

    def test_update_frame_no_crash(self, qtbot) -> None:
        window = QMainWindow()
        qtbot.addWidget(window)
        view = RemoteView()
        window.setCentralWidget(view)
        data = np.zeros((240, 320, 3), dtype=np.uint8)
        view.update_frame(data, 320, 240)
        qtbot.wait(50)

    def test_set_placeholder(self, qtbot) -> None:
        window = QMainWindow()
        qtbot.addWidget(window)
        view = RemoteView()
        window.setCentralWidget(view)
        view.set_placeholder("disconnected")
        assert "disconnected" in view.findChild(type(view._display)).text()

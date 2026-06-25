from __future__ import annotations

from PySide6.QtWidgets import QMainWindow

from uniqoremote.ui.windows.remote import RemoteView


class TestRemoteView:
    def test_remote_view_creates_display(self, qtbot) -> None:
        window = QMainWindow()
        qtbot.addWidget(window)
        view = RemoteView()
        window.setCentralWidget(view)
        display = view.findChild(type(view._display))
        assert display is not None
        assert display.minimumWidth() == 640

    def test_remote_view_frame_queue(self, qtbot) -> None:
        window = QMainWindow()
        qtbot.addWidget(window)
        view = RemoteView()
        window.setCentralWidget(view)
        view._on_frame(b"\x00" * 100)
        assert len(view._frame_queue) == 1
        view._process_frames()
        assert len(view._frame_queue) == 0

    def test_remote_view_mouse_tracking_enabled(self, qtbot) -> None:
        window = QMainWindow()
        qtbot.addWidget(window)
        view = RemoteView()
        window.setCentralWidget(view)
        assert view.hasMouseTracking()

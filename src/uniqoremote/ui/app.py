from __future__ import annotations

from PySide6.QtWidgets import QApplication


def create_qapp() -> QApplication:
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName("UniqoRemote")
    app.setOrganizationName("UniqoRemote")
    return app

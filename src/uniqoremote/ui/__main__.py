from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from uniqoremote.ui.compose import create_app


def main() -> int:
    app = QApplication(sys.argv)
    window = create_app()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

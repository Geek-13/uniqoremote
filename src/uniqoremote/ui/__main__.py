from __future__ import annotations

import asyncio
import sys

import qasync
from PySide6.QtWidgets import QApplication

from uniqoremote.ui.compose import create_app


def main() -> int:
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = create_app()
    window.show()
    with loop:
        loop.run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())

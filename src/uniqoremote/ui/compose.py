from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMainWindow

from uniqoremote.core.config import load_config
from uniqoremote.ui.windows.main import MainWindow


def create_app(config_path: Path | None = None) -> QMainWindow:
    if config_path is None:
        config_path = Path("config.toml")
    config = load_config(config_path)
    return MainWindow(config)

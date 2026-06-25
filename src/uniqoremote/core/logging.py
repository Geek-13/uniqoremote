from __future__ import annotations

import logging
import os
from pathlib import Path

import structlog
from structlog.typing import BindableLogger


def configure_logging(level: str = "INFO") -> BindableLogger:
    log_dir = Path(os.environ.get("APPDATA", "")) / "UniqoRemote" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "uniqoremote.log"

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setLevel(getattr(logging, level.upper()))
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().setLevel(getattr(logging, level.upper()))

    return structlog.get_logger()  # type: ignore[no-any-return]

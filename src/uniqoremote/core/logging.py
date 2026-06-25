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

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=getattr(logging, level.upper()),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_file), encoding="utf-8"),
        ],
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()  # type: ignore[no-any-return]

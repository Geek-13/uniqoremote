from __future__ import annotations

import logging
import sys
from typing import IO

import structlog
from structlog.typing import BindableLogger


def configure_logging(
    level: str = "INFO",
    output: IO[str] | None = None,
) -> BindableLogger:
    if output is None:
        output = sys.stderr

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=output, level=log_level)

    return structlog.get_logger()  # type: ignore[no-any-return]

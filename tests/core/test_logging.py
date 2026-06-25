from __future__ import annotations

import structlog
from structlog.testing import capture_logs
from structlog.typing import BindableLogger

from uniqoremote.core.logging import configure_logging


class TestLogging:
    def setup_method(self) -> None:
        structlog.reset_defaults()

    def test_configure_logging_returns_bindable_logger(self) -> None:
        logger = configure_logging(level="INFO")
        assert isinstance(logger, BindableLogger)

    def test_log_messages_are_json_formatted(self) -> None:
        configure_logging(level="DEBUG")
        with capture_logs() as captured:
            logger = structlog.get_logger()
            logger.info("test_event", key="value")
        assert len(captured) == 1
        assert captured[0]["event"] == "test_event"
        assert captured[0]["key"] == "value"
        assert captured[0]["log_level"] == "info"

    def test_debug_messages_produced_at_debug_level(self) -> None:
        configure_logging(level="DEBUG")
        with capture_logs() as captured:
            logger = structlog.get_logger()
            logger.debug("debug_message")
        assert len(captured) == 1
        assert captured[0]["event"] == "debug_message"
        assert captured[0]["log_level"] == "debug"

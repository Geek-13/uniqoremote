from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from uniqoremote.core.config import Config


@dataclass
class AnomalyEvent:
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    event_type: str = ""
    severity: str = "info"
    description: str = ""


class AnomalyMonitor:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._events: list[AnomalyEvent] = []
        self._max_events = 100

    def check_connection(self, remote_ip: str, connections_per_minute: int) -> list[AnomalyEvent]:
        events: list[AnomalyEvent] = []
        if connections_per_minute > 10:
            events.append(
                AnomalyEvent(
                    event_type="rate_limit",
                    severity="warning",
                    description=(
                        f"High connection rate from {remote_ip}: "
                        f"{connections_per_minute}/min"
                    ),
                )
            )
        return events

    def check_large_transfer(
        self, transfer_size: int, threshold_mb: int = 100
    ) -> list[AnomalyEvent]:
        if transfer_size > threshold_mb * 1024 * 1024:
            return [
                AnomalyEvent(
                    event_type="large_transfer",
                    severity="warning",
                    description=f"Large file transfer detected: {transfer_size} bytes",
                )
            ]
        return []

    def add_event(self, event: AnomalyEvent) -> None:
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events.pop(0)

    def get_recent_events(self, count: int = 20) -> list[AnomalyEvent]:
        return self._events[-count:]

    def clear(self) -> None:
        self._events.clear()

from __future__ import annotations

from uniqoremote.ai.monitor import AnomalyEvent, AnomalyMonitor
from uniqoremote.core.config import Config


class TestAnomalyMonitor:
    def test_check_high_connection_rate(self) -> None:
        m = AnomalyMonitor(Config())
        events = m.check_connection("192.168.1.1", 50)
        assert len(events) == 1
        assert events[0].event_type == "rate_limit"
        assert events[0].severity == "warning"

    def test_check_normal_connection_rate(self) -> None:
        m = AnomalyMonitor(Config())
        events = m.check_connection("192.168.1.1", 3)
        assert len(events) == 0

    def test_check_large_transfer(self) -> None:
        m = AnomalyMonitor(Config())
        events = m.check_large_transfer(200 * 1024 * 1024, threshold_mb=100)
        assert len(events) == 1
        assert events[0].event_type == "large_transfer"

    def test_recent_events(self) -> None:
        m = AnomalyMonitor(Config())
        m.add_event(AnomalyEvent(event_type="test"))
        assert len(m.get_recent_events()) == 1

    def test_max_events(self) -> None:
        m = AnomalyMonitor(Config())
        for i in range(150):
            m.add_event(AnomalyEvent(event_type=f"test_{i}"))
        assert len(m.get_recent_events(150)) == 100

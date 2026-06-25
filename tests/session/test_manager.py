from __future__ import annotations

import pytest

from uniqoremote.session.manager import Session, SessionError, SessionManager, SessionState


class TestSessionStateMachine:
    def test_initial_state_is_idle(self) -> None:
        session = Session(session_id="test-1", remote_device_id="device-a")
        assert session.state == SessionState.IDLE

    def test_valid_transition_idle_to_connecting(self) -> None:
        session = Session(session_id="test-1", remote_device_id="device-a")
        session.transition(SessionState.CONNECTING)
        assert session.state == SessionState.CONNECTING

    def test_valid_full_lifecycle(self) -> None:
        session = Session(session_id="test-1", remote_device_id="device-a")
        session.transition(SessionState.CONNECTING)
        session.transition(SessionState.HANDSHAKING)
        session.transition(SessionState.ACTIVE)
        session.transition(SessionState.CLOSING)
        session.transition(SessionState.IDLE)
        assert session.state == SessionState.IDLE

    def test_invalid_transition_raises_error(self) -> None:
        session = Session(session_id="test-1", remote_device_id="device-a")
        with pytest.raises(SessionError, match="Invalid transition"):
            session.transition(SessionState.ACTIVE)

    def test_error_state_can_transition_to_idle(self) -> None:
        session = Session(session_id="test-1", remote_device_id="device-a")
        session.transition(SessionState.CONNECTING)
        session.transition(SessionState.ERROR)
        session.transition(SessionState.IDLE)
        assert session.state == SessionState.IDLE


class TestSessionManager:
    def test_create_session(self) -> None:
        mgr = SessionManager()
        session = mgr.create("s1", "dev-a")
        assert session.session_id == "s1"
        assert session.remote_device_id == "dev-a"
        assert session.state == SessionState.CONNECTING

    def test_get_session(self) -> None:
        mgr = SessionManager()
        mgr.create("s1", "dev-a")
        s = mgr.get("s1")
        assert s is not None
        assert s.remote_device_id == "dev-a"

    def test_remove_session(self) -> None:
        mgr = SessionManager()
        mgr.create("s1", "dev-a")
        mgr.remove("s1")
        assert mgr.get("s1") is None

    def test_list_active(self) -> None:
        mgr = SessionManager()
        s = mgr.create("s1", "dev-a")
        s.transition(SessionState.HANDSHAKING)
        s.transition(SessionState.ACTIVE)
        active = mgr.list_active()
        assert len(active) == 1
        assert active[0].session_id == "s1"

    def test_inactive_not_in_active_list(self) -> None:
        mgr = SessionManager()
        mgr.create("s1", "dev-a")
        assert len(mgr.list_active()) == 0

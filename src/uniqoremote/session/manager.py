from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SessionState(StrEnum):
    IDLE = "idle"
    CONNECTING = "connecting"
    HANDSHAKING = "handshaking"
    ACTIVE = "active"
    CLOSING = "closing"
    ERROR = "error"


class SessionError(Exception):
    pass


@dataclass
class Session:
    session_id: str
    remote_device_id: str
    state: SessionState = SessionState.IDLE
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition(self, target: SessionState) -> None:
        valid = _TRANSITIONS.get(self.state, set())
        if target not in valid:
            raise SessionError(f"Invalid transition: {self.state} -> {target}")
        self.state = target


_TRANSITIONS: dict[SessionState, set[SessionState]] = {
    SessionState.IDLE: {SessionState.CONNECTING},
    SessionState.CONNECTING: {SessionState.HANDSHAKING, SessionState.ERROR},
    SessionState.HANDSHAKING: {SessionState.ACTIVE, SessionState.ERROR},
    SessionState.ACTIVE: {SessionState.CLOSING, SessionState.ERROR},
    SessionState.CLOSING: {SessionState.IDLE},
    SessionState.ERROR: {SessionState.IDLE, SessionState.CLOSING},
}


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, session_id: str, remote_device_id: str) -> Session:
        session = Session(session_id=session_id, remote_device_id=remote_device_id)
        session.transition(SessionState.CONNECTING)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def list_active(self) -> list[Session]:
        return [s for s in self._sessions.values() if s.state == SessionState.ACTIVE]

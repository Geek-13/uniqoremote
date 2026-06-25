from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ChatMessage:
    sender: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    message_id: str = ""


class ChatManager:
    def __init__(self, max_history: int = 500) -> None:
        self._history: list[ChatMessage] = []
        self._max_history = max_history
        self._on_message_callbacks: list[Callable[[ChatMessage], None]] = []

    def send(self, sender: str, content: str) -> ChatMessage:
        msg = ChatMessage(sender=sender, content=content)
        self._history.append(msg)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        return msg

    def get_history(self) -> list[ChatMessage]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()

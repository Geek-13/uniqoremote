from __future__ import annotations

from uniqoremote.session.chat import ChatManager, ChatMessage


class TestChatManager:
    def test_send_message(self) -> None:
        mgr = ChatManager()
        msg = mgr.send("user1", "hello")
        assert msg.sender == "user1"
        assert msg.content == "hello"
        assert msg.timestamp != ""

    def test_history_ordering(self) -> None:
        mgr = ChatManager()
        mgr.send("user1", "first")
        mgr.send("user2", "second")
        history = mgr.get_history()
        assert len(history) == 2
        assert history[0].content == "first"
        assert history[1].content == "second"

    def test_max_history(self) -> None:
        mgr = ChatManager(max_history=3)
        for i in range(5):
            mgr.send("u", f"msg{i}")
        history = mgr.get_history()
        assert len(history) == 3
        assert history[0].content == "msg2"

    def test_clear(self) -> None:
        mgr = ChatManager()
        mgr.send("u", "test")
        mgr.clear()
        assert len(mgr.get_history()) == 0


class TestChatMessage:
    def test_dataclass_fields(self) -> None:
        msg = ChatMessage(sender="alice", content="hi", message_id="m1")
        assert msg.sender == "alice"
        assert msg.content == "hi"
        assert msg.message_id == "m1"

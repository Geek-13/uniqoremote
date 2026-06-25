from __future__ import annotations

from uniqoremote.server.rendezvous.manager import RegisteredDevice, RendezvousManager


class TestRendezvousManager:
    def test_register_device(self) -> None:
        mgr = RendezvousManager()
        device = mgr.register("dev-001", b"k" * 32)
        assert device.device_id == "dev-001"
        assert device.is_online is True

    def test_lookup_peer_online(self) -> None:
        mgr = RendezvousManager()
        mgr.register("peer-1", b"k" * 32)
        peer = mgr.lookup_peer("peer-1")
        assert peer is not None
        assert peer.public_key == b"k" * 32

    def test_lookup_peer_offline(self) -> None:
        mgr = RendezvousManager(session_timeout=-1)
        mgr.register("peer-2", b"k" * 32)
        peer = mgr.lookup_peer("peer-2")
        assert peer is None

    def test_unregister(self) -> None:
        mgr = RendezvousManager()
        mgr.register("dev-x", b"k" * 32)
        mgr.unregister("dev-x")
        assert mgr.get_device("dev-x") is None

    def test_list_online(self) -> None:
        mgr = RendezvousManager()
        mgr.register("a", b"k" * 32)
        mgr.register("b", b"k" * 32)
        assert len(mgr.list_online_devices()) == 2

    def test_heartbeat_keeps_alive(self) -> None:
        mgr = RendezvousManager(session_timeout=3600)
        mgr.register("dev", b"k" * 32)
        mgr.update_heartbeat("dev")
        assert mgr.lookup_peer("dev") is not None


class TestRegisteredDevice:
    def test_default_values(self) -> None:
        d = RegisteredDevice(device_id="d", public_key=b"k" * 32)
        assert d.version == "1.0.0"
        assert d.is_online is True

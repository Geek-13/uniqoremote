from __future__ import annotations

from uniqoremote.transport.base import Transport


class TestTransportABC:
    def test_cannot_instantiate_abc(self) -> None:
        try:
            Transport()  # type: ignore[abstract]
            assert False, "Should have raised TypeError"
        except TypeError:
            pass

    def test_subclass_must_implement_all_methods(self) -> None:
        class Incomplete(Transport):
            async def connect(self, addr: tuple[str, int]) -> None:
                pass

        try:
            Incomplete()  # type: ignore[abstract]
            assert False, "Should have raised TypeError"
        except TypeError:
            pass

    def test_valid_subclass_instantiates(self) -> None:
        class Complete(Transport):
            async def connect(self, addr: tuple[str, int]) -> None:
                pass

            async def send(self, data: bytes) -> None:
                pass

            async def recv(self) -> bytes:
                return b""

            async def close(self) -> None:
                pass

        t = Complete()
        assert isinstance(t, Transport)

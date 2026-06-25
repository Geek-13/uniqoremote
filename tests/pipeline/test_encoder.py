from __future__ import annotations

import pytest

from uniqoremote.pipeline.encoder.base import EncodedPacket, Encoder


class FakeEncoder(Encoder):
    def __init__(self) -> None:
        self._started = False
        self._keyframe_requested = False

    async def start(self, width: int, height: int, fps: int, codec: str) -> None:
        self._started = True

    async def encode(self, frame) -> list[EncodedPacket]:
        return [EncodedPacket(data=b"fake-encoded", pts=frame.pts, is_keyframe=False)]

    async def stop(self) -> None:
        self._started = False

    async def request_keyframe(self) -> None:
        self._keyframe_requested = True


class TestEncoderABC:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            Encoder()  # type: ignore[abstract]


class TestFakeEncoder:
    def test_encoder_lifecycle(self) -> None:
        encoder = FakeEncoder()
        assert encoder._started is False

    def test_encoded_packet_creation(self) -> None:
        packet = EncodedPacket(data=b"test", pts=0.5, is_keyframe=True)
        assert packet.data == b"test"
        assert packet.pts == 0.5
        assert packet.is_keyframe is True

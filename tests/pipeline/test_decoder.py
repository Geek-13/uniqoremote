from __future__ import annotations

import numpy as np
import pytest

from uniqoremote.pipeline.capturer.base import RawFrame
from uniqoremote.pipeline.decoder.base import Decoder


class FakeDecoder(Decoder):
    def __init__(self) -> None:
        self._started = False

    async def start(self, width: int, height: int, codec: str) -> None:
        self._started = True

    async def decode(self, data: bytes) -> RawFrame:
        h = w = 720
        return RawFrame(data=np.zeros((h, w, 3), dtype=np.uint8), width=w, height=h)

    async def stop(self) -> None:
        self._started = False


class TestDecoderABC:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            Decoder()  # type: ignore[abstract]


class TestFakeDecoder:
    def test_decoder_initial_state(self) -> None:
        decoder = FakeDecoder()
        assert decoder._started is False

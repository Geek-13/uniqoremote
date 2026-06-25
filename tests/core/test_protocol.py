from __future__ import annotations

import pytest

from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import (
    MAGIC,
    PROTOCOL_VERSION,
    ProtocolError,
    decode_frame,
    encode_frame,
    make_hello_payload,
)


def _pack_hello() -> bytes:
    payload = make_hello_payload(
        device_id="test-device",
        public_key=b"\x00" * 32,
        version="1.0.0",
        capabilities={"codec": ["h264"]},
        nonce=b"\x01" * 24,
    )
    return encode_frame(MessageType.HELLO, payload)


class TestEncodeDecode:
    def test_encode_hello_header_magic(self) -> None:
        frame = _pack_hello()
        assert frame[:4] == MAGIC

    def test_encode_hello_header_version(self) -> None:
        frame = _pack_hello()
        version_field = int.from_bytes(frame[4:6], "big")
        assert version_field == PROTOCOL_VERSION

    def test_encode_hello_header_type(self) -> None:
        frame = _pack_hello()
        type_field = int.from_bytes(frame[6:8], "big")
        assert type_field == MessageType.HELLO.value

    def test_encode_hello_total_length(self) -> None:
        frame = _pack_hello()
        length_field = int.from_bytes(frame[12:16], "big")
        assert length_field == len(frame) - 16

    def test_roundtrip_hello(self) -> None:
        original = _pack_hello()
        msg = decode_frame(original)
        assert msg.type == MessageType.HELLO
        assert msg.payload["device_id"] == "test-device"
        assert msg.payload["version"] == "1.0.0"
        assert len(msg.payload["public_key"]) == 32

    def test_decode_invalid_magic(self) -> None:
        bad = b"XXXX" + b"\x00" * 12
        with pytest.raises(ProtocolError, match="Invalid magic"):
            decode_frame(bad)

    def test_decode_version_mismatch(self) -> None:
        bad = MAGIC + b"\xff\xff" + b"\x00" * 10
        with pytest.raises(ProtocolError, match="Unsupported protocol version"):
            decode_frame(bad)

    def test_decode_truncated_header(self) -> None:
        with pytest.raises(ProtocolError, match="Frame too short"):
            decode_frame(MAGIC + b"\x00\x00\x00")

    def test_decode_truncated_payload(self) -> None:
        header = (
            MAGIC
            + (0x0001).to_bytes(2, "big")
            + (0x0001).to_bytes(2, "big")
            + (0).to_bytes(4, "big")
            + (100).to_bytes(4, "big")
        )
        with pytest.raises(ProtocolError, match="Payload too short"):
            decode_frame(header + b"\x00" * 50)

    def test_sequence_number_increments(self) -> None:
        payload = b"data"
        frame1 = encode_frame(MessageType.STREAM, payload)
        frame2 = encode_frame(MessageType.STREAM, payload)
        seq1 = int.from_bytes(frame1[8:12], "big")
        seq2 = int.from_bytes(frame2[8:12], "big")
        assert seq2 == seq1 + 1

    def test_decode_preserves_sequence_number(self) -> None:
        payload = b"test"
        frame = encode_frame(MessageType.RELAY, payload)
        msg = decode_frame(frame)
        assert msg.seq_num == int.from_bytes(frame[8:12], "big")

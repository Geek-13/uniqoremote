from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import msgpack  # type: ignore[import-untyped]

from uniqoremote.core.events import MessageType

MAGIC = b"UNIQ"
PROTOCOL_VERSION = 1
HEADER_SIZE = 16
_seq_counter = 0


def _next_seq() -> int:
    global _seq_counter
    _seq_counter += 1
    return _seq_counter


class ProtocolError(Exception):
    pass


@dataclass
class DecodedMessage:
    type: MessageType
    seq_num: int
    payload: bytes | dict[str, Any]


def encode_frame(msg_type: MessageType, payload: bytes | dict[str, Any]) -> bytes:
    payload_bytes: bytes
    payload_bytes = msgpack.packb(payload) if isinstance(payload, dict) else payload

    seq = _next_seq()
    header = bytearray(HEADER_SIZE)
    header[0:4] = MAGIC
    header[4:6] = PROTOCOL_VERSION.to_bytes(2, "big")
    header[6:8] = msg_type.value.to_bytes(2, "big")
    header[8:12] = seq.to_bytes(4, "big")
    header[12:16] = len(payload_bytes).to_bytes(4, "big")
    return bytes(header) + payload_bytes


def decode_frame(data: bytes) -> DecodedMessage:
    if len(data) < HEADER_SIZE:
        raise ProtocolError(f"Frame too short: {len(data)} bytes")

    magic = data[0:4]
    if magic != MAGIC:
        raise ProtocolError(f"Invalid magic: {magic!r}")

    version = int.from_bytes(data[4:6], "big")
    if version != PROTOCOL_VERSION:
        raise ProtocolError(f"Unsupported protocol version: {version}")

    msg_type = MessageType.from_int(int.from_bytes(data[6:8], "big"))
    seq_num = int.from_bytes(data[8:12], "big")
    payload_len = int.from_bytes(data[12:16], "big")

    if len(data) < HEADER_SIZE + payload_len:
        raise ProtocolError(
            f"Payload too short: expected {payload_len}, got {len(data) - HEADER_SIZE}"
        )

    payload_bytes = data[HEADER_SIZE : HEADER_SIZE + payload_len]
    try:
        payload: dict[str, Any] = msgpack.unpackb(payload_bytes)
    except (msgpack.exceptions.ExtraData, ValueError):
        payload = payload_bytes  # type: ignore[assignment]
    return DecodedMessage(type=msg_type, seq_num=seq_num, payload=payload)


def make_hello_payload(
    device_id: str,
    public_key: bytes,
    version: str,
    capabilities: dict[str, Any],
    nonce: bytes,
) -> dict[str, Any]:
    return {
        "device_id": device_id,
        "public_key": public_key,
        "version": version,
        "capabilities": capabilities,
        "nonce": nonce,
    }

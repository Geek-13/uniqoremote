from __future__ import annotations

from typing import Any

from uniqoremote.core.crypto import decrypt, encrypt
from uniqoremote.core.events import MessageType
from uniqoremote.core.protocol import DecodedMessage, decode_frame, encode_frame
from uniqoremote.transport.base import Transport


class EncryptedChannel:
    def __init__(self, transport: Transport, session_key: bytes) -> None:
        self._transport = transport
        self._session_key = session_key
        self._seq_counter = 0

    async def send(self, msg_type: MessageType, payload: bytes | dict[str, Any]) -> None:
        frame = encode_frame(msg_type, payload)
        self._seq_counter += 1
        encrypted = encrypt(self._session_key, frame, self._seq_counter)
        await self._transport.send(encrypted)

    async def recv(self) -> DecodedMessage:
        raw = await self._transport.recv()
        self._seq_counter += 1
        frame = decrypt(self._session_key, raw, self._seq_counter)
        return decode_frame(frame)

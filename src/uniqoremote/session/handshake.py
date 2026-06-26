from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey

from uniqoremote.core.crypto import derive_session_key, public_key_to_bytes


class HandshakeState(StrEnum):
    IDLE = "idle"
    HELLO_SENT = "hello_sent"
    NOTIFY_RECEIVED = "notify_received"
    KEY_DERIVED = "key_derived"
    FAILED = "failed"


@dataclass
class HandshakeContext:
    private_key: X25519PrivateKey
    public_key: X25519PublicKey
    nonce: bytes
    device_id: str
    version: str
    state: HandshakeState = HandshakeState.IDLE
    peer_public_key: bytes | None = None
    peer_nonce: bytes | None = None
    session_key: bytes | None = None


def generate_hello_payload(
    device_id: str,
    public_key: X25519PublicKey,
    version: str,
    nonce: bytes,
    target_device_id: str = "",
) -> dict:
    return {
        "device_id": device_id,
        "public_key": public_key_to_bytes(public_key),
        "version": version,
        "capabilities": {"codec": ["h264"], "max_res": "1920x1080"},
        "nonce": nonce,
        "target_device_id": target_device_id,
    }


def derive_shared_key(
    private_key: X25519PrivateKey,
    peer_public_key: X25519PublicKey,
    nonce_a: bytes,
    nonce_b: bytes,
) -> bytes:
    return derive_session_key(private_key, peer_public_key, nonce_a, nonce_b)

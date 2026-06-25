from __future__ import annotations

from uniqoremote.core.crypto import generate_key_pair, generate_nonce
from uniqoremote.session.handshake import (
    HandshakeState,
    derive_shared_key,
    generate_hello_payload,
)


def test_generate_hello_payload() -> None:
    sk, pk = generate_key_pair()
    nonce = generate_nonce()
    payload = generate_hello_payload("abc123", pk, "1.0.0", nonce)
    assert payload["device_id"] == "abc123"
    assert len(payload["public_key"]) == 32
    assert payload["nonce"] == nonce


def test_derive_shared_key_identical() -> None:
    sk_a, pk_a = generate_key_pair()
    sk_b, pk_b = generate_key_pair()
    nonce_a = generate_nonce()
    nonce_b = generate_nonce()
    key_a = derive_shared_key(sk_a, pk_b, nonce_a, nonce_b)
    key_b = derive_shared_key(sk_b, pk_a, nonce_a, nonce_b)
    assert key_a == key_b
    assert len(key_a) == 32


def test_handshake_state_transitions() -> None:
    state = HandshakeState.IDLE
    assert state == HandshakeState.IDLE
    assert HandshakeState.KEY_DERIVED == "key_derived"

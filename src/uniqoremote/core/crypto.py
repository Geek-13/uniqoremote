from __future__ import annotations

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

NONCE_SIZE = 12
KEY_SIZE = 32


def generate_key_pair() -> tuple[X25519PrivateKey, X25519PublicKey]:
    private = X25519PrivateKey.generate()
    return private, private.public_key()


def public_key_to_bytes(public_key: X25519PublicKey) -> bytes:
    return public_key.public_bytes_raw()


def public_key_from_bytes(data: bytes) -> X25519PublicKey:
    return X25519PublicKey.from_public_bytes(data)


def generate_nonce() -> bytes:
    return os.urandom(NONCE_SIZE)


def derive_session_key(
    private_key: X25519PrivateKey,
    peer_public_key: X25519PublicKey,
    nonce_a: bytes,
    nonce_b: bytes,
) -> bytes:
    shared_secret = private_key.exchange(peer_public_key)
    salt = nonce_a[:8] + nonce_b[:8]
    return HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        info=b"uniqoremote-session-key",
    ).derive(shared_secret)


def _make_nonce(seq_num: int) -> bytes:
    nonce = bytearray(NONCE_SIZE)
    nonce[0:4] = seq_num.to_bytes(4, "big")
    return bytes(nonce)


def encrypt(session_key: bytes, plaintext: bytes, seq_num: int) -> bytes:
    nonce = _make_nonce(seq_num)
    cipher = ChaCha20Poly1305(session_key)
    return cipher.encrypt(nonce, plaintext, None)


def decrypt(session_key: bytes, ciphertext: bytes, seq_num: int) -> bytes:
    nonce = _make_nonce(seq_num)
    cipher = ChaCha20Poly1305(session_key)
    return cipher.decrypt(nonce, ciphertext, None)

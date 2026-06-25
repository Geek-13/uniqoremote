from __future__ import annotations

import pytest
from cryptography.exceptions import InvalidTag

from uniqoremote.core.crypto import (
    decrypt,
    derive_session_key,
    encrypt,
    generate_key_pair,
    generate_nonce,
    public_key_to_bytes,
)


class TestKeyGeneration:
    def test_generates_valid_key_pair(self) -> None:
        private, public = generate_key_pair()
        raw_pub = public_key_to_bytes(public)
        assert len(raw_pub) == 32
        assert raw_pub != b"\x00" * 32

    def test_generates_unique_keys(self) -> None:
        pub1 = public_key_to_bytes(generate_key_pair()[1])
        pub2 = public_key_to_bytes(generate_key_pair()[1])
        assert pub1 != pub2

    def test_generate_nonce_length(self) -> None:
        nonce = generate_nonce()
        assert len(nonce) == 12


class TestSessionKey:
    def test_derives_same_key_both_sides(self) -> None:
        sk_a, pk_a = generate_key_pair()
        sk_b, pk_b = generate_key_pair()
        nonce_a = generate_nonce()
        nonce_b = generate_nonce()

        key_a = derive_session_key(sk_a, pk_b, nonce_a, nonce_b)
        key_b = derive_session_key(sk_b, pk_a, nonce_a, nonce_b)
        assert key_a == key_b
        assert len(key_a) == 32

    def test_different_nonces_produce_different_keys(self) -> None:
        sk_a, pk_a = generate_key_pair()
        sk_b, pk_b = generate_key_pair()

        key1 = derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce() + b"\x00" * 12)
        key2 = derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce() + b"\x00" * 12)
        assert key1 != key2


class TestEncryptDecrypt:
    @pytest.fixture
    def session_key(self) -> bytes:
        sk_a, pk_a = generate_key_pair()
        sk_b, pk_b = generate_key_pair()
        return derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce())

    def test_encrypt_decrypt_roundtrip(self, session_key: bytes) -> None:
        plaintext = b"Hello, UniqoRemote! This is a secret message."
        nonce_nonce = 0
        ciphertext = encrypt(session_key, plaintext, nonce_nonce)
        assert ciphertext != plaintext
        decrypted = decrypt(session_key, ciphertext, nonce_nonce)
        assert decrypted == plaintext

    def test_encrypt_produces_auth_tag(self, session_key: bytes) -> None:
        plaintext = b"short"
        ciphertext = encrypt(session_key, plaintext, 1)
        assert len(ciphertext) == len(plaintext) + 16

    def test_decrypt_detects_tampering(self, session_key: bytes) -> None:
        plaintext = b"tamper test"
        ciphertext = bytearray(encrypt(session_key, plaintext, 2))
        ciphertext[0] ^= 0xFF
        with pytest.raises(InvalidTag):
            decrypt(session_key, bytes(ciphertext), 2)

    def test_decrypt_detects_wrong_nonce(self, session_key: bytes) -> None:
        plaintext = b"nonce test"
        ciphertext = encrypt(session_key, plaintext, 3)
        with pytest.raises(InvalidTag):
            decrypt(session_key, ciphertext, 4)

    def test_different_keys_produce_different_ciphertext(self, session_key: bytes) -> None:
        sk_a, pk_a = generate_key_pair()
        sk_b, pk_b = generate_key_pair()
        other_key = derive_session_key(sk_a, pk_b, generate_nonce(), generate_nonce())

        ct1 = encrypt(session_key, b"same data", 5)
        ct2 = encrypt(other_key, b"same data", 5)
        assert ct1 != ct2

    def test_large_payload(self, session_key: bytes) -> None:
        plaintext = b"\xaa" * 65536
        ciphertext = encrypt(session_key, plaintext, 6)
        assert decrypt(session_key, ciphertext, 6) == plaintext
